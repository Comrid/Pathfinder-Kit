#!/usr/bin/env python3
"""
Pathfinder Obstacle Avoidance System
초음파 센서 기반 자율 장애물 회피 시스템 + 실시간 카메라 피드
"""

from flask import Flask, render_template, jsonify, Response
from flask_socketio import SocketIO, emit
import time
import threading
import random
import subprocess
import cv2
import numpy as np
from datetime import datetime
from collections import deque

# GPIO 모듈 가용성 확인
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
    print("🔧 RPi.GPIO 모듈 로드됨")
except ImportError:
    GPIO_AVAILABLE = False
    print("⚠️ RPi.GPIO 모듈 없음 - 시뮬레이션 모드로 실행")

# 카메라 모듈 가용성 확인
try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
    CAMERA_TYPE = "PiCamera"
    print("📷 PiCamera2 모듈 로드됨")
except ImportError:
    try:
        import cv2
        CAMERA_AVAILABLE = True
        CAMERA_TYPE = "USB"
        print("📷 USB 카메라 사용 가능")
    except ImportError:
        CAMERA_AVAILABLE = False
        CAMERA_TYPE = "None"
        print("⚠️ 카메라 모듈 없음 - 시뮬레이션 모드")

# Flask 앱 설정
app = Flask(__name__)
app.config['SECRET_KEY'] = 'pathfinder_obstacle_avoidance_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# =============================================================================
# 카메라 설정
# =============================================================================

camera = None
camera_lock = threading.Lock()
current_frame = None

def setup_camera():
    """카메라 초기화"""
    global camera
    
    if not CAMERA_AVAILABLE:
        print("⚠️ 카메라 없음 - 시뮬레이션 모드")
        return False
    
    try:
        if CAMERA_TYPE == "PiCamera" and GPIO_AVAILABLE:
            # Raspberry Pi 카메라 사용
            camera = Picamera2()
            camera.configure(camera.create_preview_configuration(main={"size": (640, 480)}))
            camera.start()
            time.sleep(2)  # 카메라 안정화 대기
            print("📷 PiCamera2 초기화 완료")
        else:
            # USB 카메라 사용
            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                print("❌ USB 카메라 열기 실패")
                return False
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            camera.set(cv2.CAP_PROP_FPS, 30)
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
        
        # 현재 시간 표시
        current_time = datetime.now().strftime("%H:%M:%S")
        cv2.putText(dummy_frame, "SIMULATION MODE", (180, 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(dummy_frame, f"Time: {current_time}", (220, 250), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(dummy_frame, "Camera Feed", (230, 300), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # 시뮬레이션 장애물 표시
        cv2.rectangle(dummy_frame, (100, 350), (200, 450), (0, 0, 255), 2)
        cv2.putText(dummy_frame, "Obstacle", (110, 340), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        return dummy_frame
    
    try:
        if CAMERA_TYPE == "PiCamera" and hasattr(camera, 'capture_array'):
            # PiCamera2
            frame = camera.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        else:
            # USB 카메라
            ret, frame = camera.read()
            if not ret:
                return None
        
        # 프레임에 정보 오버레이 추가
        current_time = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, f"Obstacle Avoidance - {current_time}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # 거리 정보 표시 (전역 변수에서 가져오기)
        if 'current_distance' in globals():
            distance_text = f"Distance: {current_distance:.1f}cm"
            cv2.putText(frame, distance_text, (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # 현재 상태 표시
        if 'current_state' in globals():
            state_text = f"State: {current_state}"
            cv2.putText(frame, state_text, (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
        
        with camera_lock:
            current_frame = frame.copy()
        
        return frame
    except Exception as e:
        print(f"❌ 프레임 캡처 오류: {e}")
        return None

def generate_frames():
    """비디오 스트리밍용 프레임 생성기"""
    while True:
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
# 하드웨어 설정
# =============================================================================

# 모터 드라이버 핀 설정
IN1 = 23  # 오른쪽 모터 방향 1
IN2 = 24  # 오른쪽 모터 방향 2
IN3 = 22  # 왼쪽 모터 방향 1
IN4 = 27  # 왼쪽 모터 방향 2
ENA = 12  # 오른쪽 모터 PWM
ENB = 13  # 왼쪽 모터 PWM

# 초음파 센서 핀 설정
TRIG = 5  # GPIO5 → 초음파 송신
ECHO = 6  # GPIO6 → 초음파 수신

# =============================================================================
# 장애물 회피 설정
# =============================================================================

# 거리 임계값 (cm)
OBSTACLE_DISTANCE = 20  # 장애물 감지 거리
SAFE_DISTANCE = 30      # 안전 거리
CRITICAL_DISTANCE = 10  # 위험 거리

# 모터 속도 설정
SPEED_NORMAL = 80       # 일반 주행 속도
SPEED_SLOW = 50         # 저속 주행
SPEED_TURN = 70         # 회전 속도

# 행동 시간 설정 (초)
FORWARD_TIME = 2.0      # 전진 시간
TURN_TIME = 1.0         # 회전 시간
BACKUP_TIME = 0.5       # 후진 시간

# 초음파 센서 상수
SOUND_SPEED = 34300     # 음속 (cm/s)
TRIGGER_PULSE = 0.00001 # 10µs 트리거 펄스
TIMEOUT = 0.1           # 타임아웃 (100ms)

# =============================================================================
# 전역 변수
# =============================================================================

# 시스템 상태
avoidance_active = False
avoidance_thread = None
system_running = True

# 현재 상태
current_state = "stopped"  # stopped, forward, turning_left, turning_right, backing_up
current_distance = 0
last_distances = deque(maxlen=5)  # 최근 5개 거리 측정값

# 통계
stats = {
    'total_obstacles': 0,
    'left_turns': 0,
    'right_turns': 0,
    'backups': 0,
    'distance_traveled': 0,
    'runtime': 0,
    'start_time': None
}

# 로그
action_log = deque(maxlen=50)

# =============================================================================
# GPIO 초기화
# =============================================================================

def setup_gpio():
    """GPIO 초기 설정"""
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
            
            # 초음파 센서 핀 설정
            GPIO.setup(TRIG, GPIO.OUT)
            GPIO.setup(ECHO, GPIO.IN)
            GPIO.output(TRIG, False)
            
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

# =============================================================================
# 모터 제어 함수들
# =============================================================================

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

def move_forward(speed=SPEED_NORMAL):
    """전진"""
    if GPIO_AVAILABLE:
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
        pwm_right.ChangeDutyCycle(speed)
        pwm_left.ChangeDutyCycle(speed)
    else:
        print(f"🎮 시뮬레이션: 전진 (속도: {speed}%)")

def move_backward(speed=SPEED_SLOW):
    """후진"""
    if GPIO_AVAILABLE:
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)
        pwm_right.ChangeDutyCycle(speed)
        pwm_left.ChangeDutyCycle(speed)
    else:
        print(f"🎮 시뮬레이션: 후진 (속도: {speed}%)")

def turn_left(speed=SPEED_TURN):
    """좌회전 (제자리)"""
    if GPIO_AVAILABLE:
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)
        pwm_right.ChangeDutyCycle(speed)
        pwm_left.ChangeDutyCycle(speed)
    else:
        print(f"🎮 시뮬레이션: 좌회전 (속도: {speed}%)")

def turn_right(speed=SPEED_TURN):
    """우회전 (제자리)"""
    if GPIO_AVAILABLE:
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
        pwm_right.ChangeDutyCycle(speed)
        pwm_left.ChangeDutyCycle(speed)
    else:
        print(f"🎮 시뮬레이션: 우회전 (속도: {speed}%)")

# =============================================================================
# 초음파 센서 함수들
# =============================================================================

def get_distance():
    """초음파 센서로 거리 측정"""
    if not GPIO_AVAILABLE:
        # 시뮬레이션 모드: 장애물 회피 시나리오 생성
        if random.random() < 0.1:  # 10% 확률로 장애물 생성
            return round(random.uniform(5.0, 15.0), 1)  # 가까운 장애물
        else:
            return round(random.uniform(30.0, 100.0), 1)  # 안전한 거리
    
    try:
        # TRIG 신호 발생
        GPIO.output(TRIG, True)
        time.sleep(TRIGGER_PULSE)
        GPIO.output(TRIG, False)

        # ECHO 신호 대기
        start_time = time.time()
        timeout_start = start_time
        
        while GPIO.input(ECHO) == 0:
            start_time = time.time()
            if start_time - timeout_start > TIMEOUT:
                return None
        
        while GPIO.input(ECHO) == 1:
            end_time = time.time()
            if end_time - start_time > TIMEOUT:
                return None

        # 거리 계산
        duration = end_time - start_time
        distance = (duration * SOUND_SPEED) / 2

        if 2 <= distance <= 400:
            return round(distance, 1)
        return None
        
    except Exception as e:
        print(f"거리 측정 오류: {e}")
        return None

def get_average_distance(samples=3):
    """여러 번 측정하여 평균 거리 계산"""
    distances = []
    for _ in range(samples):
        dist = get_distance()
        if dist is not None:
            distances.append(dist)
        time.sleep(0.05)  # 50ms 간격
    
    if distances:
        return round(sum(distances) / len(distances), 1)
    return None

# =============================================================================
# 장애물 회피 로직
# =============================================================================

def add_log(message, action_type="info"):
    """로그 추가"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = {
        'timestamp': timestamp,
        'message': message,
        'type': action_type,
        'distance': current_distance
    }
    action_log.append(log_entry)
    print(f"[{timestamp}] {message}")
    
    # 웹 클라이언트에 로그 전송
    socketio.emit('log_update', log_entry)

def decide_turn_direction():
    """회전 방향 결정 (랜덤 또는 패턴 기반)"""
    # 간단한 랜덤 선택
    return random.choice(['left', 'right'])

def obstacle_avoidance_loop():
    """장애물 회피 메인 루프"""
    global current_state, current_distance, avoidance_active, stats
    
    add_log("🚀 장애물 회피 시스템 시작", "start")
    stats['start_time'] = time.time()
    
    while avoidance_active and system_running:
        try:
            # 거리 측정
            distance = get_average_distance()
            
            if distance is not None:
                current_distance = distance
                last_distances.append(distance)
                
                # 상태 업데이트 전송
                socketio.emit('status_update', {
                    'state': current_state,
                    'distance': current_distance,
                    'stats': stats.copy()
                })
                
                # 장애물 회피 로직
                if distance <= CRITICAL_DISTANCE:
                    # 위험! 즉시 후진
                    if current_state != "backing_up":
                        current_state = "backing_up"
                        stats['backups'] += 1
                        add_log(f"🚨 위험! 후진 시작 (거리: {distance}cm)", "critical")
                        
                        stop_motors()
                        time.sleep(0.1)
                        move_backward(SPEED_SLOW)
                        time.sleep(BACKUP_TIME)
                        stop_motors()
                        
                        # 후진 후 회전
                        direction = decide_turn_direction()
                        current_state = f"turning_{direction}"
                        
                        if direction == "left":
                            stats['left_turns'] += 1
                            add_log("↺ 좌회전 시작", "turn")
                            turn_left()
                        else:
                            stats['right_turns'] += 1
                            add_log("↻ 우회전 시작", "turn")
                            turn_right()
                        
                        time.sleep(TURN_TIME)
                        stop_motors()
                
                elif distance <= OBSTACLE_DISTANCE:
                    # 장애물 감지! 회전
                    if current_state == "forward":
                        stats['total_obstacles'] += 1
                        direction = decide_turn_direction()
                        current_state = f"turning_{direction}"
                        
                        add_log(f"🚧 장애물 감지! (거리: {distance}cm)", "obstacle")
                        stop_motors()
                        time.sleep(0.1)
                        
                        if direction == "left":
                            stats['left_turns'] += 1
                            add_log("↺ 좌회전으로 회피", "turn")
                            turn_left()
                        else:
                            stats['right_turns'] += 1
                            add_log("↻ 우회전으로 회피", "turn")
                            turn_right()
                        
                        time.sleep(TURN_TIME)
                        stop_motors()
                
                elif distance >= SAFE_DISTANCE:
                    # 안전! 전진
                    if current_state != "forward":
                        current_state = "forward"
                        add_log(f"✅ 전진 시작 (거리: {distance}cm)", "forward")
                        move_forward(SPEED_NORMAL)
                        stats['distance_traveled'] += 0.1  # 대략적인 거리
                
                else:
                    # 중간 거리: 저속 전진
                    if current_state != "forward":
                        current_state = "forward"
                        add_log(f"⚠️ 저속 전진 (거리: {distance}cm)", "caution")
                        move_forward(SPEED_SLOW)
                        stats['distance_traveled'] += 0.05
            
            else:
                # 측정 실패
                if current_state == "forward":
                    stop_motors()
                    current_state = "stopped"
                    add_log("❌ 거리 측정 실패 - 정지", "error")
            
            # 통계 업데이트
            if stats['start_time']:
                stats['runtime'] = round(time.time() - stats['start_time'], 1)
            
            time.sleep(0.1)  # 100ms 주기
            
        except Exception as e:
            add_log(f"❌ 회피 루프 오류: {e}", "error")
            stop_motors()
            time.sleep(1)
    
    # 종료 시 정리
    stop_motors()
    current_state = "stopped"
    add_log("⏹️ 장애물 회피 시스템 종료", "stop")

# =============================================================================
# Flask 라우트
# =============================================================================

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """실시간 비디오 스트리밍"""
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/start')
def start_avoidance():
    """장애물 회피 시작"""
    global avoidance_active, avoidance_thread, stats
    
    if not avoidance_active:
        avoidance_active = True
        
        # 통계 초기화
        stats = {
            'total_obstacles': 0,
            'left_turns': 0,
            'right_turns': 0,
            'backups': 0,
            'distance_traveled': 0,
            'runtime': 0,
            'start_time': time.time()
        }
        
        # 스레드 시작
        avoidance_thread = threading.Thread(target=obstacle_avoidance_loop)
        avoidance_thread.daemon = True
        avoidance_thread.start()
        
        return jsonify({'success': True, 'message': '장애물 회피 시작됨'})
    else:
        return jsonify({'success': False, 'message': '이미 실행 중입니다'})

@app.route('/api/stop')
def stop_avoidance():
    """장애물 회피 중지"""
    global avoidance_active, current_state
    
    if avoidance_active:
        avoidance_active = False
        stop_motors()
        current_state = "stopped"
        return jsonify({'success': True, 'message': '장애물 회피 중지됨'})
    else:
        return jsonify({'success': False, 'message': '실행 중이 아닙니다'})

@app.route('/api/status')
def get_status():
    """현재 상태 조회"""
    return jsonify({
        'success': True,
        'active': avoidance_active,
        'state': current_state,
        'distance': current_distance,
        'stats': stats.copy(),
        'gpio_available': GPIO_AVAILABLE
    })

@app.route('/api/logs')
def get_logs():
    """로그 조회"""
    return jsonify({
        'success': True,
        'logs': list(action_log)
    })

@app.route('/api/settings')
def get_settings():
    """설정 조회"""
    return jsonify({
        'success': True,
        'settings': {
            'obstacle_distance': OBSTACLE_DISTANCE,
            'safe_distance': SAFE_DISTANCE,
            'critical_distance': CRITICAL_DISTANCE,
            'speed_normal': SPEED_NORMAL,
            'speed_slow': SPEED_SLOW,
            'speed_turn': SPEED_TURN
        }
    })

# =============================================================================
# SocketIO 이벤트 핸들러
# =============================================================================

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결"""
    print(f"🔗 클라이언트 연결: {request.sid}")
    emit('connection_status', {'status': 'connected'})
    
    # 현재 상태 전송
    emit('status_update', {
        'state': current_state,
        'distance': current_distance,
        'stats': stats.copy(),
        'active': avoidance_active
    })

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제"""
    print(f"🔌 클라이언트 연결 해제: {request.sid}")

@socketio.on('emergency_stop')
def handle_emergency_stop():
    """비상 정지"""
    global avoidance_active, current_state
    
    print("🚨 비상 정지 명령 수신")
    avoidance_active = False
    stop_motors()
    current_state = "stopped"
    
    add_log("🚨 비상 정지 실행", "emergency")
    emit('emergency_stop_executed', {'timestamp': time.time()})

# =============================================================================
# 정리 및 시작
# =============================================================================

def cleanup():
    """정리 작업"""
    global avoidance_active, system_running
    
    avoidance_active = False
    system_running = False
    
    if GPIO_AVAILABLE:
        try:
            stop_motors()
            if 'pwm_right' in globals():
                pwm_right.stop()
            if 'pwm_left' in globals():
                pwm_left.stop()
            GPIO.cleanup()
            print("🧹 GPIO 정리 완료")
        except:
            pass

if __name__ == '__main__':
    try:
        if setup_gpio():
            print("🚀 패스파인더 장애물 회피 시스템 시작")
            print("🚧 자율 장애물 회피 및 탐색 시스템")
            
            if GPIO_AVAILABLE:
                print("🔧 하드웨어 모드: 실제 센서 및 모터 사용")
            else:
                print("🎮 시뮬레이션 모드: 가상 장애물 생성")
            
            # 카메라 초기화
            if setup_camera():
                print("📷 카메라 초기화 완료")
            else:
                print("⚠️ 카메라 초기화 실패 - 시뮬레이션 모드로 계속")
            
            # IP 주소 자동 감지 및 출력
            try:
                ip = subprocess.check_output(['hostname', '-I'], shell=False).decode().split()[0]
                print(f"🌐 브라우저에서 http://{ip}:5000 으로 접속하세요")
            except:
                print("🌐 웹 브라우저에서 http://라즈베리파이IP:5000 접속")
            
            print("-" * 60)
            
            socketio.run(app, host='0.0.0.0', port=5000, debug=False)
        else:
            print("❌ GPIO 설정 실패로 서버를 시작할 수 없습니다")
        
    except KeyboardInterrupt:
        print("\n⏹️ 서버 종료 중...")
    except Exception as e:
        print(f"❌ 서버 오류: {e}")
    finally:
        cleanup()
