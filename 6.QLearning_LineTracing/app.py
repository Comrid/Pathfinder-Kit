#!/usr/bin/env python3
"""
🧠 Q-Learning LineTracing System
패스파인더 키트용 강화학습 기반 라인 트레이싱 자율주행 시스템

Features:
- 실시간 카메라 스트리밍
- Q-Learning 알고리즘 기반 학습
- 웹 인터페이스를 통한 학습 과정 모니터링
- 자율주행 모드 및 수동 제어 모드
"""

import os
import sys
import time
import json
import threading
import numpy as np
import cv2
from datetime import datetime
from flask import Flask, render_template, Response, request, jsonify
from flask_socketio import SocketIO, emit
import base64

# GPIO 모듈 가용성 확인
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
    print("✅ GPIO 모듈 사용 가능 - 하드웨어 모드")
except ImportError:
    GPIO_AVAILABLE = False
    print("⚠️ GPIO 모듈 없음 - 시뮬레이션 모드")

# 카메라 모듈 가용성 확인
try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
    print("✅ PiCamera2 모듈 사용 가능")
except ImportError:
    try:
        import cv2
        CAMERA_AVAILABLE = True
        print("⚠️ PiCamera2 없음 - OpenCV 카메라 사용")
    except ImportError:
        CAMERA_AVAILABLE = False
        print("❌ 카메라 모듈 없음 - 시뮬레이션 모드")

# Flask 앱 설정
app = Flask(__name__)
app.config['SECRET_KEY'] = 'pathfinder-qlearning-linetracing'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# =============================================================================
# 전역 변수 및 설정
# =============================================================================

# 모터 제어 핀 설정
IN1, IN2, IN3, IN4 = 23, 24, 22, 27  # 모터 방향 제어
ENA, ENB = 12, 13  # PWM 핀

# 시스템 상태
system_running = True
learning_active = False
autonomous_mode = False
manual_control = False

# 스레드 동기화
state_lock = threading.Lock()
camera_lock = threading.Lock()

# 카메라 설정
camera = None
current_frame = None
processed_frame = None

# Q-Learning 파라미터
class QLearningConfig:
    """Q-Learning 설정 클래스"""
    def __init__(self):
        # 학습 파라미터
        self.learning_rate = 0.1      # 학습률
        self.discount_factor = 0.95   # 할인 인수
        self.epsilon = 0.3            # 탐험률 (초기값)
        self.epsilon_min = 0.01       # 최소 탐험률
        self.epsilon_decay = 0.995    # 탐험률 감소율
        
        # 상태 및 행동 공간
        self.num_states = 7           # 라인 위치 상태 (0: 왼쪽 끝 ~ 6: 오른쪽 끝)
        self.num_actions = 5          # 행동 (0: 좌회전, 1: 약간좌, 2: 직진, 3: 약간우, 4: 우회전)
        
        # 보상 설정
        self.reward_on_line = 10      # 라인 위에 있을 때 보상
        self.reward_off_line = -5     # 라인에서 벗어났을 때 페널티
        self.reward_center = 15       # 중앙에 있을 때 추가 보상
        
        # 모터 속도 설정
        self.base_speed = 60          # 기본 속도
        self.turn_speed = 40          # 회전 속도

# Q-Learning 에이전트
class QLearningAgent:
    """Q-Learning 기반 라인 트레이싱 에이전트"""
    
    def __init__(self, config):
        self.config = config
        self.q_table = np.zeros((config.num_states, config.num_actions))
        self.current_state = 3  # 중앙 상태로 초기화
        self.current_action = 2  # 직진으로 초기화
        self.episode = 0
        self.total_reward = 0
        self.episode_rewards = []
        self.learning_history = []
        
        # 통계
        self.successful_episodes = 0
        self.total_steps = 0
        
    def get_state_from_line_position(self, line_center_x, frame_width):
        """라인 중심 위치를 상태로 변환"""
        if line_center_x is None:
            return 3  # 라인이 없으면 중앙 상태
        
        # 프레임을 7개 구역으로 나누어 상태 결정
        section_width = frame_width / self.config.num_states
        state = int(line_center_x / section_width)
        return max(0, min(self.config.num_states - 1, state))
    
    def choose_action(self, state, training=True):
        """ε-greedy 정책으로 행동 선택"""
        if training and np.random.random() < self.config.epsilon:
            # 탐험: 랜덤 행동
            action = np.random.randint(self.config.num_actions)
        else:
            # 활용: 최적 행동
            action = np.argmax(self.q_table[state])
        
        return action
    
    def update_q_table(self, state, action, reward, next_state):
        """Q-테이블 업데이트"""
        current_q = self.q_table[state, action]
        max_next_q = np.max(self.q_table[next_state])
        
        # Q-Learning 업데이트 공식
        new_q = current_q + self.config.learning_rate * (
            reward + self.config.discount_factor * max_next_q - current_q
        )
        
        self.q_table[state, action] = new_q
        
        # 학습 기록
        self.learning_history.append({
            'episode': self.episode,
            'state': state,
            'action': action,
            'reward': reward,
            'q_value': new_q,
            'epsilon': self.config.epsilon
        })
    
    def calculate_reward(self, state, line_detected):
        """보상 계산"""
        if not line_detected:
            return self.config.reward_off_line
        
        # 중앙에 가까울수록 높은 보상
        center_state = self.config.num_states // 2
        distance_from_center = abs(state - center_state)
        
        if distance_from_center == 0:
            return self.config.reward_center
        elif distance_from_center <= 1:
            return self.config.reward_on_line
        else:
            return self.config.reward_on_line - distance_from_center
    
    def end_episode(self):
        """에피소드 종료 처리"""
        self.episode_rewards.append(self.total_reward)
        
        # 성공적인 에피소드 판정 (임계값 이상의 보상)
        if self.total_reward > 100:
            self.successful_episodes += 1
        
        # ε 감소
        if self.config.epsilon > self.config.epsilon_min:
            self.config.epsilon *= self.config.epsilon_decay
        
        self.episode += 1
        self.total_reward = 0
    
    def save_model(self, filepath):
        """Q-테이블 저장"""
        model_data = {
            'q_table': self.q_table.tolist(),
            'episode': self.episode,
            'epsilon': self.config.epsilon,
            'episode_rewards': self.episode_rewards,
            'successful_episodes': self.successful_episodes,
            'total_steps': self.total_steps
        }
        
        with open(filepath, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        print(f"💾 모델 저장 완료: {filepath}")
    
    def load_model(self, filepath):
        """Q-테이블 로드"""
        try:
            with open(filepath, 'r') as f:
                model_data = json.load(f)
            
            self.q_table = np.array(model_data['q_table'])
            self.episode = model_data.get('episode', 0)
            self.config.epsilon = model_data.get('epsilon', self.config.epsilon)
            self.episode_rewards = model_data.get('episode_rewards', [])
            self.successful_episodes = model_data.get('successful_episodes', 0)
            self.total_steps = model_data.get('total_steps', 0)
            
            print(f"📂 모델 로드 완료: {filepath}")
            return True
        except Exception as e:
            print(f"❌ 모델 로드 실패: {e}")
            return False

# 전역 Q-Learning 에이전트
config = QLearningConfig()
agent = QLearningAgent(config)

# =============================================================================
# GPIO 및 모터 제어
# =============================================================================

def setup_gpio():
    """GPIO 초기화"""
    if GPIO_AVAILABLE:
        try:
            GPIO.setwarnings(False)
            GPIO.cleanup()
            GPIO.setmode(GPIO.BCM)
            
            # 모터 핀 설정
            GPIO.setup(IN1, GPIO.OUT)
            GPIO.setup(IN2, GPIO.OUT)
            GPIO.setup(IN3, GPIO.OUT)
            GPIO.setup(IN4, GPIO.OUT)
            GPIO.setup(ENA, GPIO.OUT)
            GPIO.setup(ENB, GPIO.OUT)
            
            # PWM 설정
            global pwm_right, pwm_left
            pwm_right = GPIO.PWM(ENA, 1000)
            pwm_left = GPIO.PWM(ENB, 1000)
            pwm_right.start(0)
            pwm_left.start(0)
            
            print("🔧 GPIO 설정 완료")
            return True
        except Exception as e:
            print(f"❌ GPIO 설정 실패: {e}")
            return False
    else:
        print("🔧 시뮬레이션 모드 - GPIO 설정 건너뜀")
        return True

def stop_motors():
    """모터 정지"""
    if GPIO_AVAILABLE:
        try:
            GPIO.output(IN1, GPIO.LOW)
            GPIO.output(IN2, GPIO.LOW)
            GPIO.output(IN3, GPIO.LOW)
            GPIO.output(IN4, GPIO.LOW)
            pwm_right.ChangeDutyCycle(0)
            pwm_left.ChangeDutyCycle(0)
        except:
            pass
    else:
        print("🎮 시뮬레이션: 모터 정지")

def execute_action(action):
    """Q-Learning 행동을 모터 명령으로 변환 및 실행"""
    actions = {
        0: "turn_left",      # 좌회전
        1: "slight_left",    # 약간 좌회전
        2: "forward",        # 직진
        3: "slight_right",   # 약간 우회전
        4: "turn_right"      # 우회전
    }
    
    action_name = actions.get(action, "forward")
    
    if GPIO_AVAILABLE:
        try:
            if action == 0:  # 좌회전
                GPIO.output(IN1, GPIO.HIGH)
                GPIO.output(IN2, GPIO.LOW)
                GPIO.output(IN3, GPIO.LOW)
                GPIO.output(IN4, GPIO.HIGH)
                pwm_right.ChangeDutyCycle(config.turn_speed)
                pwm_left.ChangeDutyCycle(config.turn_speed)
            elif action == 1:  # 약간 좌회전
                GPIO.output(IN1, GPIO.HIGH)
                GPIO.output(IN2, GPIO.LOW)
                GPIO.output(IN3, GPIO.HIGH)
                GPIO.output(IN4, GPIO.LOW)
                pwm_right.ChangeDutyCycle(config.base_speed)
                pwm_left.ChangeDutyCycle(config.base_speed * 0.5)
            elif action == 2:  # 직진
                GPIO.output(IN1, GPIO.HIGH)
                GPIO.output(IN2, GPIO.LOW)
                GPIO.output(IN3, GPIO.HIGH)
                GPIO.output(IN4, GPIO.LOW)
                pwm_right.ChangeDutyCycle(config.base_speed)
                pwm_left.ChangeDutyCycle(config.base_speed)
            elif action == 3:  # 약간 우회전
                GPIO.output(IN1, GPIO.HIGH)
                GPIO.output(IN2, GPIO.LOW)
                GPIO.output(IN3, GPIO.HIGH)
                GPIO.output(IN4, GPIO.LOW)
                pwm_right.ChangeDutyCycle(config.base_speed * 0.5)
                pwm_left.ChangeDutyCycle(config.base_speed)
            elif action == 4:  # 우회전
                GPIO.output(IN1, GPIO.LOW)
                GPIO.output(IN2, GPIO.HIGH)
                GPIO.output(IN3, GPIO.HIGH)
                GPIO.output(IN4, GPIO.LOW)
                pwm_right.ChangeDutyCycle(config.turn_speed)
                pwm_left.ChangeDutyCycle(config.turn_speed)
        except Exception as e:
            print(f"❌ 모터 제어 오류: {e}")
    else:
        print(f"🎮 시뮬레이션: {action_name} 실행")
    
    return action_name

# =============================================================================
# 컴퓨터 비전 - 라인 검출
# =============================================================================

def detect_line(frame):
    """라인 검출 및 중심점 계산"""
    try:
        # 그레이스케일 변환
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 가우시안 블러 적용
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 이진화 (검은 라인 검출)
        _, binary = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY_INV)
        
        # 관심 영역 설정 (하단 1/3 영역)
        height, width = binary.shape
        roi_height = height // 3
        roi = binary[height - roi_height:height, :]
        
        # 컨투어 찾기
        contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        line_center_x = None
        line_detected = False
        
        if contours:
            # 가장 큰 컨투어를 라인으로 간주
            largest_contour = max(contours, key=cv2.contourArea)
            
            if cv2.contourArea(largest_contour) > 100:  # 최소 면적 필터
                # 컨투어의 중심점 계산
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    line_center_x = int(M["m10"] / M["m00"])
                    line_detected = True
                    
                    # 시각화를 위해 컨투어 그리기
                    cv2.drawContours(roi, [largest_contour], -1, (255, 255, 255), 2)
                    cv2.circle(roi, (line_center_x, int(M["m01"] / M["m00"])), 5, (255, 255, 255), -1)
        
        # 처리된 프레임 생성 (시각화용)
        processed = cv2.cvtColor(roi, cv2.COLOR_GRAY2BGR)
        
        # 상태 구역 표시
        section_width = width / config.num_states
        for i in range(config.num_states + 1):
            x = int(i * section_width)
            cv2.line(processed, (x, 0), (x, roi_height), (0, 255, 0), 1)
        
        # 라인 중심점 표시
        if line_center_x is not None:
            cv2.line(processed, (line_center_x, 0), (line_center_x, roi_height), (0, 0, 255), 2)
        
        return line_center_x, line_detected, processed
        
    except Exception as e:
        print(f"❌ 라인 검출 오류: {e}")
        return None, False, frame

# =============================================================================
# 카메라 관리
# =============================================================================

def setup_camera():
    """카메라 초기화"""
    global camera
    
    if not CAMERA_AVAILABLE:
        print("⚠️ 카메라 없음 - 시뮬레이션 모드")
        return False
    
    try:
        if GPIO_AVAILABLE:
            # Raspberry Pi 카메라 사용
            camera = Picamera2()
            camera.configure(camera.create_preview_configuration(main={"size": (640, 480)}))
            camera.start()
            time.sleep(2)  # 카메라 안정화 대기
            print("📷 PiCamera2 초기화 완료")
        else:
            # USB 카메라 사용
            camera = cv2.VideoCapture(0)
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            print("📷 USB 카메라 초기화 완료")
        
        return True
    except Exception as e:
        print(f"❌ 카메라 초기화 실패: {e}")
        return False

def capture_frame():
    """프레임 캡처"""
    global current_frame
    
    if not CAMERA_AVAILABLE or camera is None:
        # 시뮬레이션용 더미 프레임 생성
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(dummy_frame, "SIMULATION MODE", (200, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return dummy_frame
    
    try:
        if GPIO_AVAILABLE and hasattr(camera, 'capture_array'):
            # PiCamera2
            frame = camera.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        else:
            # USB 카메라
            ret, frame = camera.read()
            if not ret:
                return None
        
        with camera_lock:
            current_frame = frame.copy()
        
        return frame
    except Exception as e:
        print(f"❌ 프레임 캡처 오류: {e}")
        return None

def generate_frames():
    """비디오 스트리밍용 프레임 생성기"""
    while system_running:
        frame = capture_frame()
        if frame is not None:
            try:
                # JPEG 인코딩
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            except Exception as e:
                print(f"❌ 프레임 인코딩 오류: {e}")
        
        time.sleep(0.033)  # ~30 FPS

# =============================================================================
# Q-Learning 학습 스레드
# =============================================================================

def learning_thread():
    """Q-Learning 학습 메인 스레드"""
    global learning_active, autonomous_mode
    
    print("🧠 Q-Learning 학습 스레드 시작")
    
    step_count = 0
    episode_start_time = time.time()
    
    while system_running:
        if not learning_active:
            time.sleep(0.1)
            continue
        
        try:
            # 현재 프레임 획득
            frame = capture_frame()
            if frame is None:
                time.sleep(0.1)
                continue
            
            # 라인 검출
            line_center_x, line_detected, processed_frame = detect_line(frame)
            
            # 현재 상태 계산
            current_state = agent.get_state_from_line_position(line_center_x, frame.shape[1])
            
            # 행동 선택
            action = agent.choose_action(current_state, training=True)
            
            # 행동 실행
            action_name = execute_action(action)
            
            # 보상 계산
            reward = agent.calculate_reward(current_state, line_detected)
            agent.total_reward += reward
            
            # Q-테이블 업데이트 (이전 상태가 있는 경우)
            if hasattr(agent, 'prev_state') and hasattr(agent, 'prev_action'):
                agent.update_q_table(agent.prev_state, agent.prev_action, reward, current_state)
            
            # 현재 상태 저장
            agent.prev_state = current_state
            agent.prev_action = action
            agent.total_steps += 1
            step_count += 1
            
            # 실시간 학습 정보 전송
            learning_info = {
                'episode': agent.episode,
                'step': step_count,
                'state': current_state,
                'action': action,
                'action_name': action_name,
                'reward': reward,
                'total_reward': agent.total_reward,
                'epsilon': agent.config.epsilon,
                'line_detected': line_detected,
                'line_center_x': line_center_x,
                'q_values': agent.q_table[current_state].tolist(),
                'timestamp': time.time()
            }
            
            socketio.emit('learning_update', learning_info)
            
            # 처리된 프레임 전송
            if processed_frame is not None:
                _, buffer = cv2.imencode('.jpg', processed_frame)
                processed_b64 = base64.b64encode(buffer).decode('utf-8')
                socketio.emit('processed_frame', {'image': processed_b64})
            
            # 에피소드 종료 조건 확인
            episode_duration = time.time() - episode_start_time
            if step_count >= 1000 or episode_duration > 60:  # 1000스텝 또는 60초
                agent.end_episode()
                
                # 에피소드 완료 정보 전송
                episode_info = {
                    'episode': agent.episode,
                    'total_reward': agent.episode_rewards[-1] if agent.episode_rewards else 0,
                    'steps': step_count,
                    'duration': episode_duration,
                    'success_rate': agent.successful_episodes / max(agent.episode, 1) * 100,
                    'epsilon': agent.config.epsilon
                }
                
                socketio.emit('episode_complete', episode_info)
                
                # 다음 에피소드 준비
                step_count = 0
                episode_start_time = time.time()
                
                # 주기적으로 모델 저장
                if agent.episode % 10 == 0:
                    agent.save_model('q_learning_model.json')
            
            time.sleep(0.1)  # 10 FPS로 학습
            
        except Exception as e:
            print(f"❌ 학습 스레드 오류: {e}")
            time.sleep(1)
    
    print("🧠 Q-Learning 학습 스레드 종료")

# =============================================================================
# 자율주행 스레드
# =============================================================================

def autonomous_thread():
    """자율주행 모드 스레드"""
    global autonomous_mode
    
    print("🚗 자율주행 스레드 시작")
    
    while system_running:
        if not autonomous_mode:
            time.sleep(0.1)
            continue
        
        try:
            # 현재 프레임 획득
            frame = capture_frame()
            if frame is None:
                time.sleep(0.1)
                continue
            
            # 라인 검출
            line_center_x, line_detected, processed_frame = detect_line(frame)
            
            # 현재 상태 계산
            current_state = agent.get_state_from_line_position(line_center_x, frame.shape[1])
            
            # 최적 행동 선택 (탐험 없음)
            action = agent.choose_action(current_state, training=False)
            
            # 행동 실행
            action_name = execute_action(action)
            
            # 자율주행 정보 전송
            autonomous_info = {
                'state': current_state,
                'action': action,
                'action_name': action_name,
                'line_detected': line_detected,
                'line_center_x': line_center_x,
                'confidence': np.max(agent.q_table[current_state]),
                'timestamp': time.time()
            }
            
            socketio.emit('autonomous_update', autonomous_info)
            
            time.sleep(0.1)  # 10 FPS로 자율주행
            
        except Exception as e:
            print(f"❌ 자율주행 스레드 오류: {e}")
            time.sleep(1)
    
    print("🚗 자율주행 스레드 종료")

# =============================================================================
# Flask 라우트
# =============================================================================

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """비디오 스트리밍"""
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def get_status():
    """시스템 상태 조회"""
    return jsonify({
        'learning_active': learning_active,
        'autonomous_mode': autonomous_mode,
        'manual_control': manual_control,
        'episode': agent.episode,
        'total_steps': agent.total_steps,
        'success_rate': agent.successful_episodes / max(agent.episode, 1) * 100,
        'epsilon': agent.config.epsilon,
        'gpio_available': GPIO_AVAILABLE,
        'camera_available': CAMERA_AVAILABLE
    })

@app.route('/api/q_table')
def get_q_table():
    """Q-테이블 조회"""
    return jsonify({
        'q_table': agent.q_table.tolist(),
        'states': config.num_states,
        'actions': config.num_actions,
        'action_names': ['좌회전', '약간좌', '직진', '약간우', '우회전']
    })

@app.route('/api/statistics')
def get_statistics():
    """학습 통계 조회"""
    return jsonify({
        'episode_rewards': agent.episode_rewards[-50:],  # 최근 50 에피소드
        'learning_history': agent.learning_history[-100:],  # 최근 100 스텝
        'total_episodes': agent.episode,
        'successful_episodes': agent.successful_episodes,
        'total_steps': agent.total_steps,
        'current_epsilon': agent.config.epsilon
    })

# =============================================================================
# SocketIO 이벤트 핸들러
# =============================================================================

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결"""
    print(f"🔗 클라이언트 연결: {request.sid}")
    emit('system_status', {
        'gpio_available': GPIO_AVAILABLE,
        'camera_available': CAMERA_AVAILABLE,
        'learning_active': learning_active,
        'autonomous_mode': autonomous_mode
    })

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제"""
    print(f"🔌 클라이언트 연결 해제: {request.sid}")

@socketio.on('start_learning')
def handle_start_learning():
    """학습 시작"""
    global learning_active, autonomous_mode, manual_control
    
    with state_lock:
        learning_active = True
        autonomous_mode = False
        manual_control = False
    
    print("🧠 Q-Learning 학습 시작")
    emit('learning_started', {'message': 'Q-Learning 학습이 시작되었습니다.'})

@socketio.on('stop_learning')
def handle_stop_learning():
    """학습 중지"""
    global learning_active
    
    with state_lock:
        learning_active = False
    
    stop_motors()
    print("🧠 Q-Learning 학습 중지")
    emit('learning_stopped', {'message': 'Q-Learning 학습이 중지되었습니다.'})

@socketio.on('start_autonomous')
def handle_start_autonomous():
    """자율주행 시작"""
    global autonomous_mode, learning_active, manual_control
    
    with state_lock:
        autonomous_mode = True
        learning_active = False
        manual_control = False
    
    print("🚗 자율주행 모드 시작")
    emit('autonomous_started', {'message': '자율주행 모드가 시작되었습니다.'})

@socketio.on('stop_autonomous')
def handle_stop_autonomous():
    """자율주행 중지"""
    global autonomous_mode
    
    with state_lock:
        autonomous_mode = False
    
    stop_motors()
    print("🚗 자율주행 모드 중지")
    emit('autonomous_stopped', {'message': '자율주행 모드가 중지되었습니다.'})

@socketio.on('manual_control')
def handle_manual_control(data):
    """수동 제어"""
    global manual_control, learning_active, autonomous_mode
    
    if learning_active or autonomous_mode:
        emit('error', {'message': '학습 또는 자율주행 모드에서는 수동 제어할 수 없습니다.'})
        return
    
    manual_control = True
    command = data.get('command', 'stop')
    
    # 수동 제어 명령 실행
    if command == 'forward':
        execute_action(2)  # 직진
    elif command == 'left':
        execute_action(0)  # 좌회전
    elif command == 'right':
        execute_action(4)  # 우회전
    elif command == 'stop':
        stop_motors()
    
    emit('manual_executed', {'command': command})

@socketio.on('save_model')
def handle_save_model():
    """모델 저장"""
    try:
        filename = f"q_learning_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        agent.save_model(filename)
        emit('model_saved', {'message': f'모델이 저장되었습니다: {filename}'})
    except Exception as e:
        emit('error', {'message': f'모델 저장 실패: {str(e)}'})

@socketio.on('load_model')
def handle_load_model(data):
    """모델 로드"""
    try:
        filename = data.get('filename', 'q_learning_model.json')
        if agent.load_model(filename):
            emit('model_loaded', {'message': f'모델이 로드되었습니다: {filename}'})
        else:
            emit('error', {'message': f'모델 로드 실패: {filename}'})
    except Exception as e:
        emit('error', {'message': f'모델 로드 오류: {str(e)}'})

@socketio.on('reset_learning')
def handle_reset_learning():
    """학습 초기화"""
    global agent
    
    # 학습 중지
    with state_lock:
        learning_active = False
        autonomous_mode = False
    
    stop_motors()
    
    # 에이전트 초기화
    agent = QLearningAgent(config)
    
    print("🔄 Q-Learning 에이전트 초기화 완료")
    emit('learning_reset', {'message': 'Q-Learning이 초기화되었습니다.'})

# =============================================================================
# 메인 실행
# =============================================================================

def cleanup():
    """시스템 정리"""
    global system_running, camera
    
    print("🧹 시스템 정리 중...")
    
    system_running = False
    
    # 모터 정지
    stop_motors()
    
    # 카메라 정리
    if camera is not None:
        try:
            if hasattr(camera, 'stop'):
                camera.stop()
            elif hasattr(camera, 'release'):
                camera.release()
        except:
            pass
    
    # GPIO 정리
    if GPIO_AVAILABLE:
        try:
            if 'pwm_right' in globals():
                pwm_right.stop()
            if 'pwm_left' in globals():
                pwm_left.stop()
            GPIO.cleanup()
        except:
            pass
    
    print("✅ 시스템 정리 완료")

if __name__ == '__main__':
    try:
        print("🚀 패스파인더 Q-Learning LineTracing 시스템 시작")
        print("=" * 60)
        
        # 시스템 초기화
        if not setup_gpio():
            print("⚠️ GPIO 설정 실패 - 시뮬레이션 모드로 계속")
        
        if not setup_camera():
            print("⚠️ 카메라 설정 실패 - 시뮬레이션 모드로 계속")
        
        # 기존 모델 로드 시도
        if os.path.exists('q_learning_model.json'):
            agent.load_model('q_learning_model.json')
        
        # 백그라운드 스레드 시작
        learning_thread_obj = threading.Thread(target=learning_thread, daemon=True)
        autonomous_thread_obj = threading.Thread(target=autonomous_thread, daemon=True)
        
        learning_thread_obj.start()
        autonomous_thread_obj.start()
        
        print("🌐 웹 서버 시작: http://0.0.0.0:5000")
        print("📱 모바일에서 접속: http://라즈베리파이IP:5000")
        print("🛑 Ctrl+C로 종료")
        
        # Flask-SocketIO 서버 실행
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의한 종료")
    except Exception as e:
        print(f"❌ 시스템 오류: {e}")
    finally:
        cleanup()
