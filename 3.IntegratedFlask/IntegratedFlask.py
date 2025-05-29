#!/usr/bin/env python3
"""
Pathfinder Integrated Control System
모터, 초음파 센서, 카메라를 통합한 Flask 기반 제어 시스템
"""

from flask import Flask, render_template, jsonify, Response
from flask_socketio import SocketIO, emit
import time
import json
import threading
import atexit
from datetime import datetime
from collections import deque
import statistics
import random
import subprocess

# GPIO 및 카메라 모듈 가용성 확인
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
    print("🔧 RPi.GPIO 모듈 로드됨")
except ImportError:
    GPIO_AVAILABLE = False
    print("⚠️ RPi.GPIO 모듈 없음 - 시뮬레이션 모드로 실행")

try:
    import cv2
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
    print("📷 카메라 모듈 로드됨")
except ImportError:
    CAMERA_AVAILABLE = False
    print("⚠️ 카메라 모듈 없음 - 카메라 기능 비활성화")

# Flask 앱 설정
app = Flask(__name__)
app.config['SECRET_KEY'] = 'pathfinder_integrated_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# =============================================================================
# 모터 제어 설정
# =============================================================================

# 모터 상태 관리
current_command = "stop"
motor_speed = 100
motor_running = True
command_lock = threading.Lock()

# 모터 드라이버 핀 설정
IN1 = 23  # 오른쪽 모터 방향 1
IN2 = 24  # 오른쪽 모터 방향 2
IN3 = 22  # 왼쪽 모터 방향 1
IN4 = 27  # 왼쪽 모터 방향 2
ENA = 12  # 오른쪽 모터 PWM
ENB = 13  # 왼쪽 모터 PWM

# 모터 속도 설정
MOTOR_SPEED_NORMAL = 100
MOTOR_SPEED_TURN = 80
MOTOR_SPEED_DIAGONAL = 60

# =============================================================================
# 초음파 센서 설정
# =============================================================================

# 초음파 센서 핀 설정
TRIG = 5  # GPIO5 → 초음파 송신
ECHO = 6  # GPIO6 → 초음파 수신

# 초음파 센서 상수
SOUND_SPEED = 34300  # 음속 (cm/s)
TRIGGER_PULSE = 0.00001  # 10µs 트리거 펄스
TIMEOUT = 0.1  # 타임아웃 (100ms)

# 초음파 센서 데이터
measurement_data = deque(maxlen=50)  # 최근 50개 측정값
measurement_count = 0
ultrasonic_stats = {
    'min_distance': None,
    'max_distance': None,
    'avg_distance': None,
    'total_measurements': 0,
    'error_count': 0
}

# =============================================================================
# 카메라 설정
# =============================================================================

picam2 = None
# 카메라 초기화는 GPIO 설정 후에 실행

# =============================================================================
# GPIO 초기화
# =============================================================================

def setup_gpio():
    """GPIO 초기 설정"""
    global picam2
    
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
            
        except Exception as e:
            print(f"❌ GPIO 설정 실패: {e}")
            return False
    else:
        print("🔧 시뮬레이션 모드 - GPIO 설정 건너뜀")
    
    # GPIO 설정 후 카메라 초기화
    if CAMERA_AVAILABLE:
        try:
            picam2 = Picamera2()
            picam2.preview_configuration.main.size = (640, 480)
            picam2.preview_configuration.main.format = "RGB888"
            picam2.configure("preview")
            picam2.start()
            print("📷 카메라 초기화 완료")
        except Exception as e:
            print(f"❌ 카메라 초기화 실패: {e}")
            global CAMERA_AVAILABLE
            CAMERA_AVAILABLE = False
    
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
        except RuntimeError as e:
            if "pin numbering mode" not in str(e):
                raise e
    else:
        print("🎮 시뮬레이션: 모터 정지")

def set_motor_direction(right_forward, left_forward):
    """모터 방향 설정"""
    if GPIO_AVAILABLE:
        if right_forward:
            GPIO.output(IN1, GPIO.HIGH)
            GPIO.output(IN2, GPIO.LOW)
        else:
            GPIO.output(IN1, GPIO.LOW)
            GPIO.output(IN2, GPIO.HIGH)
        
        if left_forward:
            GPIO.output(IN3, GPIO.HIGH)
            GPIO.output(IN4, GPIO.LOW)
        else:
            GPIO.output(IN3, GPIO.LOW)
            GPIO.output(IN4, GPIO.HIGH)
    else:
        right_dir = "전진" if right_forward else "후진"
        left_dir = "전진" if left_forward else "후진"
        print(f"🎮 시뮬레이션: 모터 방향 - 오른쪽: {right_dir}, 왼쪽: {left_dir}")

def set_motor_speed(right_speed, left_speed):
    """모터 속도 설정"""
    if GPIO_AVAILABLE:
        pwm_right.ChangeDutyCycle(right_speed)
        pwm_left.ChangeDutyCycle(left_speed)
    else:
        print(f"🎮 시뮬레이션: 모터 속도 - 오른쪽: {right_speed}%, 왼쪽: {left_speed}%")

def move_forward(speed=MOTOR_SPEED_NORMAL):
    set_motor_direction(True, True)
    set_motor_speed(speed, speed)

def move_backward(speed=MOTOR_SPEED_NORMAL):
    set_motor_direction(False, False)
    set_motor_speed(speed, speed)

def turn_left(speed=MOTOR_SPEED_TURN):
    set_motor_direction(True, False)
    set_motor_speed(speed, speed)

def turn_right(speed=MOTOR_SPEED_TURN):
    set_motor_direction(False, True)
    set_motor_speed(speed, speed)

def move_forward_left(speed=MOTOR_SPEED_NORMAL):
    set_motor_direction(True, True)
    set_motor_speed(speed, speed * MOTOR_SPEED_DIAGONAL / 100)

def move_forward_right(speed=MOTOR_SPEED_NORMAL):
    set_motor_direction(True, True)
    set_motor_speed(speed * MOTOR_SPEED_DIAGONAL / 100, speed)

def move_backward_left(speed=MOTOR_SPEED_NORMAL):
    set_motor_direction(False, False)
    set_motor_speed(speed, speed * MOTOR_SPEED_DIAGONAL / 100)

def move_backward_right(speed=MOTOR_SPEED_NORMAL):
    set_motor_direction(False, False)
    set_motor_speed(speed * MOTOR_SPEED_DIAGONAL / 100, speed)

# =============================================================================
# 초음파 센서 함수들
# =============================================================================

def get_distance():
    """초음파 센서로 거리 측정"""
    if not GPIO_AVAILABLE:
        # 시뮬레이션 모드: 랜덤 거리 생성
        if random.random() < 0.05:  # 5% 확률로 측정 실패
            return None
        return round(random.uniform(5.0, 200.0), 1)
    
    try:
        # TRIG 신호 발생
        GPIO.output(TRIG, True)
        time.sleep(TRIGGER_PULSE)
        GPIO.output(TRIG, False)

        # ECHO 신호 대기 (타임아웃 적용)
        start_time = time.time()
        timeout_start = start_time
        
        # ECHO 신호 시작 대기
        while GPIO.input(ECHO) == 0:
            start_time = time.time()
            if start_time - timeout_start > TIMEOUT:
                return None  # 타임아웃 발생
        
        # ECHO 신호 종료 대기
        while GPIO.input(ECHO) == 1:
            end_time = time.time()
            if end_time - start_time > TIMEOUT:
                return None  # 타임아웃 발생

        # 거리 계산 (음속 * 시간 / 2)
        duration = end_time - start_time
        distance = (duration * SOUND_SPEED) / 2

        # 유효 범위 체크 (2cm ~ 400cm)
        if 2 <= distance <= 400:
            return round(distance, 1)
        return None
        
    except Exception as e:
        print(f"거리 측정 오류: {e}")
        return None

def update_ultrasonic_statistics(distance):
    """초음파 센서 통계 데이터 업데이트"""
    global ultrasonic_stats
    
    if distance is not None:
        ultrasonic_stats['total_measurements'] += 1
        
        # 최소/최대값 업데이트
        if ultrasonic_stats['min_distance'] is None or distance < ultrasonic_stats['min_distance']:
            ultrasonic_stats['min_distance'] = distance
        if ultrasonic_stats['max_distance'] is None or distance > ultrasonic_stats['max_distance']:
            ultrasonic_stats['max_distance'] = distance
        
        # 평균값 계산 (최근 측정값들 기준)
        valid_distances = [d['distance'] for d in measurement_data if d['distance'] is not None]
        if valid_distances:
            ultrasonic_stats['avg_distance'] = round(statistics.mean(valid_distances), 1)
    else:
        ultrasonic_stats['error_count'] += 1

# =============================================================================
# 카메라 함수들
# =============================================================================

def gen_frames():
    """카메라 프레임 생성"""
    if not CAMERA_AVAILABLE or picam2 is None:
        # 카메라가 없을 때 더미 이미지 생성
        import numpy as np
        while True:
            # 640x480 크기의 더미 이미지 생성
            dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            dummy_frame[:] = (50, 50, 50)  # 어두운 회색
            
            # 텍스트 추가
            cv2.putText(dummy_frame, "Camera Not Available", (150, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            ret, buffer = cv2.imencode('.jpg', dummy_frame)
            if ret:
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.1)
    else:
        while True:
            try:
                frame = picam2.capture_array()
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    continue
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                print(f"카메라 프레임 생성 오류: {e}")
                time.sleep(0.1)

# =============================================================================
# 모터 제어 스레드
# =============================================================================

def motor_control_thread():
    """모터 제어 백그라운드 스레드"""
    last_command = "stop"
    last_speed = 100
    
    print("🚗 모터 제어 스레드 시작")
    
    while motor_running:
        with command_lock:
            cmd = current_command
            spd = motor_speed
        
        if cmd != last_command or spd != last_speed:
            print(f"🚗 모터 명령 실행: {cmd}, 속도: {spd}%")
            
            # 실시간 상태 업데이트
            socketio.emit('motor_status', {
                'command': cmd,
                'speed': spd,
                'timestamp': time.time()
            })
            
            if cmd == "forward":
                move_forward(spd)
            elif cmd == "backward":
                move_backward(spd)
            elif cmd == "left":
                turn_left(spd)
            elif cmd == "right":
                turn_right(spd)
            elif cmd == "forward-left":
                move_forward_left(spd)
            elif cmd == "forward-right":
                move_forward_right(spd)
            elif cmd == "backward-left":
                move_backward_left(spd)
            elif cmd == "backward-right":
                move_backward_right(spd)
            elif cmd == "stop":
                stop_motors()
            else:
                print(f"⚠️ 알 수 없는 모터 명령: {cmd}")
            
            last_command = cmd
            last_speed = spd
        
        time.sleep(0.01)
    
    print("🚗 모터 제어 스레드 종료")

# =============================================================================
# Flask 라우트
# =============================================================================

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """카메라 스트리밍"""
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/distance')
def get_distance_api():
    """거리 측정 API (폴링용)"""
    global measurement_count
    
    try:
        # 거리 측정
        distance = get_distance()
        timestamp = datetime.now().strftime('%H:%M:%S')
        measurement_count += 1
        
        # 데이터 저장
        measurement_data.append({
            'timestamp': timestamp,
            'distance': distance,
            'datetime': datetime.now().isoformat(),
            'count': measurement_count
        })
        
        # 통계 업데이트
        update_ultrasonic_statistics(distance)
        
        # 응답 데이터 구성
        response_data = {
            'success': True,
            'distance': distance,
            'timestamp': timestamp,
            'count': measurement_count,
            'stats': ultrasonic_stats.copy(),
            'chart_data': list(measurement_data)[-20:]  # 최근 20개 데이터
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ 거리 측정 오류: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })

@app.route('/api/ultrasonic/clear')
def clear_ultrasonic_data():
    """초음파 센서 데이터 초기화 API"""
    global ultrasonic_stats, measurement_count
    
    measurement_data.clear()
    measurement_count = 0
    ultrasonic_stats = {
        'min_distance': None,
        'max_distance': None,
        'avg_distance': None,
        'total_measurements': 0,
        'error_count': 0
    }
    
    return jsonify({
        'success': True,
        'message': '초음파 센서 데이터가 초기화되었습니다.',
        'timestamp': datetime.now().strftime('%H:%M:%S')
    })

@app.route('/api/system/status')
def get_system_status():
    """시스템 상태 API"""
    return jsonify({
        'success': True,
        'gpio_available': GPIO_AVAILABLE,
        'camera_available': CAMERA_AVAILABLE,
        'motor_running': motor_running,
        'current_command': current_command,
        'motor_speed': motor_speed,
        'ultrasonic_measurements': len(measurement_data),
        'timestamp': datetime.now().strftime('%H:%M:%S')
    })

# =============================================================================
# SocketIO 이벤트 핸들러
# =============================================================================

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결"""
    print(f"🔗 클라이언트 연결: {request.sid}")
    emit('connection_status', {'status': 'connected'})
    emit('system_status', {
        'gpio_available': GPIO_AVAILABLE,
        'camera_available': CAMERA_AVAILABLE,
        'motor_running': motor_running
    })
    print(f"📊 시스템 상태 전송: GPIO={GPIO_AVAILABLE}, Camera={CAMERA_AVAILABLE}, Motor={motor_running}")

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제"""
    print(f"🔌 클라이언트 연결 해제: {request.sid}")

@socketio.on('motor_command')
def handle_motor_command(data):
    """모터 명령 처리"""
    global current_command
    
    command = data.get('command', 'stop')
    print(f"🎮 모터 명령 수신: {command} (클라이언트: {request.sid})")
    
    with command_lock:
        current_command = command
    
    emit('motor_command_received', {
        'command': command,
        'timestamp': time.time()
    })
    print(f"✅ 모터 명령 확인 응답 전송: {command}")

@socketio.on('speed_change')
def handle_speed_change(data):
    """모터 속도 변경"""
    global motor_speed
    
    speed = data.get('speed', 100)
    speed = max(0, min(100, speed))  # 0-100 범위로 제한
    
    with command_lock:
        motor_speed = speed
    
    print(f"⚡ 모터 속도 변경: {speed}% (클라이언트: {request.sid})")
    emit('speed_changed', {
        'speed': speed,
        'timestamp': time.time()
    })

@socketio.on('emergency_stop')
def handle_emergency_stop():
    """비상 정지"""
    global current_command
    
    print(f"🚨 비상 정지 명령 수신 (클라이언트: {request.sid})")
    
    with command_lock:
        current_command = "stop"
    
    stop_motors()
    
    emit('emergency_stop_executed', {
        'timestamp': time.time()
    })
    print("🚨 비상 정지 실행 완료")

# =============================================================================
# 정리 및 시작
# =============================================================================

def cleanup():
    """정리 작업"""
    global motor_running
    motor_running = False
    
    if GPIO_AVAILABLE:
        try:
            stop_motors()
            pwm_right.stop()
            pwm_left.stop()
            GPIO.cleanup()
            print("🧹 GPIO 정리 완료")
        except:
            pass
    
    if CAMERA_AVAILABLE and picam2:
        try:
            picam2.stop()
            print("📷 카메라 정리 완료")
        except:
            pass

# 프로그램 종료 시 정리 작업 등록
atexit.register(cleanup)

if __name__ == '__main__':
    try:
        if setup_gpio():
            # 모터 제어 스레드 시작
            motor_thread = threading.Thread(target=motor_control_thread)
            motor_thread.daemon = True
            motor_thread.start()
            
            print("🚀 패스파인더 통합 제어 시스템 시작")
            print("🤖 모터 제어, 📡 초음파 센서, 📷 카메라 통합")
            
            if GPIO_AVAILABLE:
                print("🔧 하드웨어 모드: 실제 센서 및 모터 사용")
            else:
                print("🎮 시뮬레이션 모드: 가상 데이터 생성")
            
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
