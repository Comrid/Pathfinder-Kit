#!/usr/bin/env python3
"""
Pathfinder Integrated Control System
카메라, 초음파 센서, 모터를 통합한 실시간 제어 시스템
"""

from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO, emit
import cv2
import time
import threading
import subprocess
import os
import numpy as np
from datetime import datetime
from collections import deque
import json
import atexit

# Flask 앱 설정
app = Flask(__name__)
app.config['SECRET_KEY'] = 'pathfinder-integrated-system'
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='threading',
                   logger=True,
                   engineio_logger=True)

# GPIO 모듈 가용성 확인
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
    print("🔧 RPi.GPIO 모듈 로드됨")
except ImportError:
    GPIO_AVAILABLE = False
    print("⚠️ RPi.GPIO 모듈 없음 - 시뮬레이션 모드로 실행")

# =============================================================================
# 전역 변수 및 설정
# =============================================================================

# 시스템 상태
system_running = True
camera = None
camera_type = 'simulation'

# 모터 제어 변수
current_command = "stop"
motor_speed = 100
motor_running = True
command_lock = threading.Lock()

# 초음파 센서 변수
ultrasonic_data = deque(maxlen=50)
ultrasonic_stats = {
    'min_distance': None,
    'max_distance': None,
    'avg_distance': None,
    'total_measurements': 0,
    'error_count': 0
}

# =============================================================================
# GPIO 및 하드웨어 설정
# =============================================================================

# 모터 드라이버 핀 설정
MOTOR_IN1 = 23  # 오른쪽 모터 방향 1
MOTOR_IN2 = 24  # 오른쪽 모터 방향 2
MOTOR_IN3 = 22  # 왼쪽 모터 방향 1
MOTOR_IN4 = 27  # 왼쪽 모터 방향 2
MOTOR_ENA = 12  # 오른쪽 모터 PWM
MOTOR_ENB = 13  # 왼쪽 모터 PWM

# 초음파 센서 핀 설정
ULTRASONIC_TRIG = 5  # GPIO5 → 초음파 송신
ULTRASONIC_ECHO = 6  # GPIO6 → 초음파 수신

# 상수 정의
SOUND_SPEED = 34300  # 음속 (cm/s)
TRIGGER_PULSE = 0.00001  # 10µs 트리거 펄스
ULTRASONIC_TIMEOUT = 0.1  # 타임아웃 (100ms)

# 모터 속도 설정
MOTOR_SPEED_NORMAL = 100
MOTOR_SPEED_TURN = 80
MOTOR_SPEED_DIAGONAL = 60

# PWM 객체
pwm_right = None
pwm_left = None

def setup_gpio():
    """GPIO 초기 설정"""
    global pwm_right, pwm_left
    
    if not GPIO_AVAILABLE:
        print("🔧 시뮬레이션 모드 - GPIO 설정 건너뜀")
        return True
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # 모터 핀 설정
        GPIO.setup(MOTOR_IN1, GPIO.OUT)
        GPIO.setup(MOTOR_IN2, GPIO.OUT)
        GPIO.setup(MOTOR_IN3, GPIO.OUT)
        GPIO.setup(MOTOR_IN4, GPIO.OUT)
        GPIO.setup(MOTOR_ENA, GPIO.OUT)
        GPIO.setup(MOTOR_ENB, GPIO.OUT)
        
        # 초음파 센서 핀 설정
        GPIO.setup(ULTRASONIC_TRIG, GPIO.OUT)
        GPIO.setup(ULTRASONIC_ECHO, GPIO.IN)
        GPIO.output(ULTRASONIC_TRIG, False)
        
        # PWM 설정
        pwm_right = GPIO.PWM(MOTOR_ENA, 1000)
        pwm_left = GPIO.PWM(MOTOR_ENB, 1000)
        pwm_right.start(0)
        pwm_left.start(0)
        
        print("🔧 GPIO 설정 완료")
        return True
        
    except Exception as e:
        print(f"❌ GPIO 설정 실패: {e}")
        return False

# =============================================================================
# 카메라 시스템
# =============================================================================

def setup_camera():
    """카메라 모듈을 자동으로 감지하고 초기화합니다."""
    global camera, camera_type
    
    try:
        # PiCamera2 시도
        from picamera2 import Picamera2
        picam2 = Picamera2()
        picam2.preview_configuration.main.size = (640, 480)
        picam2.preview_configuration.main.format = "RGB888"
        picam2.configure("preview")
        picam2.start()
        camera = picam2
        camera_type = 'picamera2'
        print("✅ PiCamera2 모듈이 성공적으로 초기화되었습니다.")
        return True
    except Exception as e:
        print(f"⚠️ PiCamera2 초기화 실패: {e}")
        
        try:
            # USB 카메라 시도
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                camera = cap
                camera_type = 'usb'
                print("✅ USB 카메라가 성공적으로 초기화되었습니다.")
                return True
            else:
                raise Exception("USB 카메라를 열 수 없습니다.")
        except Exception as e:
            print(f"⚠️ USB 카메라 초기화 실패: {e}")
            print("🔄 시뮬레이션 모드로 전환합니다.")
            camera = None
            camera_type = 'simulation'
            return True

def generate_dummy_frame():
    """시뮬레이션용 더미 프레임을 생성합니다."""
    # 640x480 크기의 그라디언트 이미지 생성
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # 시간에 따라 변하는 색상 효과
    t = int(time.time() * 10) % 255
    frame[:, :, 0] = t  # Red channel
    frame[:, :, 1] = (t + 85) % 255  # Green channel  
    frame[:, :, 2] = (t + 170) % 255  # Blue channel
    
    # 시스템 정보 오버레이
    cv2.putText(frame, "PATHFINDER INTEGRATED SYSTEM", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(frame, f"Time: {time.strftime('%H:%M:%S')}", (50, 100), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Motor: {current_command.upper()}", (50, 150), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    # 최근 초음파 거리 표시
    if ultrasonic_data:
        latest_distance = ultrasonic_data[-1]['distance']
        if latest_distance is not None:
            cv2.putText(frame, f"Distance: {latest_distance} cm", (50, 200), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "Distance: ERROR", (50, 200), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    return frame

def generate_frames():
    """프레임 생성기 - 카메라 타입에 따라 다른 방식으로 프레임을 생성합니다."""
    global camera, camera_type
    
    while system_running:
        try:
            if camera_type == 'picamera2' and camera:
                frame = camera.capture_array()
            elif camera_type == 'usb' and camera:
                ret, frame = camera.read()
                if not ret:
                    continue
                # BGR to RGB 변환 (OpenCV는 BGR 사용)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:  # simulation
                frame = generate_dummy_frame()
            
            # 정보 오버레이 추가 (실제 카메라인 경우)
            if camera_type != 'simulation':
                # 현재 시간
                cv2.putText(frame, f"Time: {time.strftime('%H:%M:%S')}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # 모터 상태
                cv2.putText(frame, f"Motor: {current_command.upper()}", (10, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                # 초음파 거리
                if ultrasonic_data:
                    latest_distance = ultrasonic_data[-1]['distance']
                    if latest_distance is not None:
                        cv2.putText(frame, f"Distance: {latest_distance} cm", (10, 90), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    else:
                        cv2.putText(frame, "Distance: ERROR", (10, 90), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # JPEG 인코딩
            ret, buffer = cv2.imencode('.jpg', frame, 
                                     [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ret:
                continue
                
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                   
        except Exception as e:
            print(f"❌ 프레임 생성 오류: {e}")
            # 오류 발생 시 더미 프레임으로 대체
            frame = generate_dummy_frame()
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(0.033)  # ~30 FPS

# =============================================================================
# 모터 제어 시스템
# =============================================================================

def set_motor_direction(right_forward, left_forward):
    """모터 방향 설정"""
    if not GPIO_AVAILABLE:
        return
    
    if right_forward:
        GPIO.output(MOTOR_IN1, GPIO.HIGH)
        GPIO.output(MOTOR_IN2, GPIO.LOW)
    else:
        GPIO.output(MOTOR_IN1, GPIO.LOW)
        GPIO.output(MOTOR_IN2, GPIO.HIGH)
    
    if left_forward:
        GPIO.output(MOTOR_IN3, GPIO.HIGH)
        GPIO.output(MOTOR_IN4, GPIO.LOW)
    else:
        GPIO.output(MOTOR_IN3, GPIO.LOW)
        GPIO.output(MOTOR_IN4, GPIO.HIGH)

def set_motor_speed(right_speed, left_speed):
    """모터 속도 설정"""
    if not GPIO_AVAILABLE or not pwm_right or not pwm_left:
        return
    
    pwm_right.ChangeDutyCycle(right_speed)
    pwm_left.ChangeDutyCycle(left_speed)

def stop_motors():
    """모터 정지"""
    set_motor_speed(0, 0)

def move_forward(speed=MOTOR_SPEED_NORMAL):
    """전진"""
    set_motor_direction(True, True)
    set_motor_speed(speed, speed)

def move_backward(speed=MOTOR_SPEED_NORMAL):
    """후진"""
    set_motor_direction(False, False)
    set_motor_speed(speed, speed)

def turn_left(speed=MOTOR_SPEED_TURN):
    """좌회전"""
    set_motor_direction(True, False)
    set_motor_speed(speed, speed)

def turn_right(speed=MOTOR_SPEED_TURN):
    """우회전"""
    set_motor_direction(False, True)
    set_motor_speed(speed, speed)

def move_forward_left(speed=MOTOR_SPEED_NORMAL):
    """왼쪽 앞으로"""
    set_motor_direction(True, True)
    set_motor_speed(speed, speed * MOTOR_SPEED_DIAGONAL / 100)

def move_forward_right(speed=MOTOR_SPEED_NORMAL):
    """오른쪽 앞으로"""
    set_motor_direction(True, True)
    set_motor_speed(speed * MOTOR_SPEED_DIAGONAL / 100, speed)

def move_backward_left(speed=MOTOR_SPEED_NORMAL):
    """왼쪽 뒤로"""
    set_motor_direction(False, False)
    set_motor_speed(speed, speed * MOTOR_SPEED_DIAGONAL / 100)

def move_backward_right(speed=MOTOR_SPEED_NORMAL):
    """오른쪽 뒤로"""
    set_motor_direction(False, False)
    set_motor_speed(speed * MOTOR_SPEED_DIAGONAL / 100, speed)

def motor_control_thread():
    """모터 제어 스레드"""
    last_command = "stop"
    last_speed = 100
    
    while motor_running and system_running:
        with command_lock:
            cmd = current_command
            spd = motor_speed
        
        if cmd != last_command or spd != last_speed:
            print(f"🚗 모터 명령: {cmd}, 속도: {spd}")
            
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
            
            last_command = cmd
            last_speed = spd
        
        time.sleep(0.01)

# =============================================================================
# 초음파 센서 시스템
# =============================================================================

def get_ultrasonic_distance():
    """초음파 센서로 거리 측정"""
    if not GPIO_AVAILABLE:
        # 시뮬레이션 모드: 랜덤 거리 생성
        import random
        if random.random() < 0.05:  # 5% 확률로 측정 실패
            return None
        return round(random.uniform(5.0, 200.0), 1)
    
    try:
        # TRIG 신호 발생
        GPIO.output(ULTRASONIC_TRIG, True)
        time.sleep(TRIGGER_PULSE)
        GPIO.output(ULTRASONIC_TRIG, False)

        # ECHO 신호 대기 (타임아웃 적용)
        start_time = time.time()
        timeout_start = start_time
        
        # ECHO 신호 시작 대기
        while GPIO.input(ULTRASONIC_ECHO) == 0:
            start_time = time.time()
            if start_time - timeout_start > ULTRASONIC_TIMEOUT:
                return None  # 타임아웃 발생
        
        # ECHO 신호 종료 대기
        while GPIO.input(ULTRASONIC_ECHO) == 1:
            end_time = time.time()
            if end_time - start_time > ULTRASONIC_TIMEOUT:
                return None  # 타임아웃 발생

        # 거리 계산 (음속 * 시간 / 2)
        duration = end_time - start_time
        distance = (duration * SOUND_SPEED) / 2

        # 유효 범위 체크 (2cm ~ 400cm)
        if 2 <= distance <= 400:
            return round(distance, 1)
        return None
        
    except Exception as e:
        print(f"초음파 센서 오류: {e}")
        return None

def update_ultrasonic_stats(distance):
    """초음파 센서 통계 업데이트"""
    global ultrasonic_stats
    
    if distance is not None:
        ultrasonic_stats['total_measurements'] += 1
        
        # 최소/최대값 업데이트
        if ultrasonic_stats['min_distance'] is None or distance < ultrasonic_stats['min_distance']:
            ultrasonic_stats['min_distance'] = distance
        if ultrasonic_stats['max_distance'] is None or distance > ultrasonic_stats['max_distance']:
            ultrasonic_stats['max_distance'] = distance
        
        # 평균값 계산 (최근 측정값들 기준)
        valid_distances = [d['distance'] for d in ultrasonic_data if d['distance'] is not None]
        if valid_distances:
            ultrasonic_stats['avg_distance'] = round(sum(valid_distances) / len(valid_distances), 1)
    else:
        ultrasonic_stats['error_count'] += 1

def ultrasonic_sensor_thread():
    """초음파 센서 측정 스레드"""
    measurement_count = 0
    
    while system_running:
        try:
            # 거리 측정
            distance = get_ultrasonic_distance()
            timestamp = datetime.now().strftime('%H:%M:%S')
            measurement_count += 1
            
            # 데이터 저장
            ultrasonic_data.append({
                'timestamp': timestamp,
                'distance': distance,
                'datetime': datetime.now().isoformat(),
                'count': measurement_count
            })
            
            # 통계 업데이트
            update_ultrasonic_stats(distance)
            
            # 실시간 데이터 전송
            socketio.emit('ultrasonic_data', {
                'distance': distance,
                'timestamp': timestamp,
                'count': measurement_count,
                'stats': ultrasonic_stats.copy()
            })
            
            if distance is not None:
                print(f"📏 거리 측정 #{measurement_count}: {distance} cm")
            else:
                print(f"📏 거리 측정 #{measurement_count}: 실패")
                
        except Exception as e:
            print(f"❌ 초음파 센서 스레드 오류: {e}")
        
        time.sleep(0.5)  # 0.5초마다 측정

# =============================================================================
# Flask 라우트
# =============================================================================

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """비디오 스트림 제공"""
    return Response(generate_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/system_status')
def system_status():
    """시스템 상태 API"""
    return jsonify({
        'camera_type': camera_type,
        'gpio_available': GPIO_AVAILABLE,
        'motor_command': current_command,
        'motor_speed': motor_speed,
        'ultrasonic_stats': ultrasonic_stats.copy(),
        'system_running': system_running
    })

# =============================================================================
# SocketIO 이벤트 핸들러
# =============================================================================

@socketio.on('connect')
def handle_connect():
    print(f"🔗 클라이언트 연결: {request.sid}")
    print(f"🔗 연결 정보: {request.environ.get('REMOTE_ADDR', 'Unknown')}")
    emit('system_status', {
        'camera_type': camera_type,
        'gpio_available': GPIO_AVAILABLE,
        'message': '통합 시스템에 연결되었습니다.'
    })

@socketio.on('disconnect')
def handle_disconnect():
    print(f"🔌 클라이언트 연결 해제: {request.sid}")

@socketio.on('motor_command')
def handle_motor_command(data):
    """모터 명령 처리"""
    global current_command, motor_speed
    
    command = data.get('command', 'stop')
    speed = data.get('speed', 100)
    
    print(f"📡 모터 명령 수신: {command} (속도: {speed}%) from {request.sid}")
    
    with command_lock:
        current_command = command
        motor_speed = speed
    
    # 명령 수신 확인 응답
    emit('motor_command_received', {
        'command': command,
        'speed': speed,
        'timestamp': time.time()
    })

@socketio.on('speed_change')
def handle_speed_change(data):
    """속도 변경 처리"""
    global motor_speed
    
    speed = data.get('speed', 100)
    
    print(f"🎛️ 속도 변경 수신: {speed}% from {request.sid}")
    
    with command_lock:
        motor_speed = speed
    
    # 속도 변경 확인 응답
    emit('speed_change_received', {
        'speed': speed,
        'timestamp': time.time()
    })

@socketio.on('clear_ultrasonic_data')
def handle_clear_ultrasonic_data():
    """초음파 데이터 초기화"""
    global ultrasonic_stats
    
    print(f"🧹 초음파 데이터 초기화 요청 from {request.sid}")
    
    ultrasonic_data.clear()
    ultrasonic_stats = {
        'min_distance': None,
        'max_distance': None,
        'avg_distance': None,
        'total_measurements': 0,
        'error_count': 0
    }
    
    emit('ultrasonic_data_cleared', {'message': '초음파 데이터가 초기화되었습니다.'})
    print("🧹 초음파 데이터 초기화 완료")

# =============================================================================
# 시스템 정리 및 메인 함수
# =============================================================================

def cleanup():
    """시스템 정리"""
    global system_running, motor_running
    
    print("🧹 시스템 정리 중...")
    system_running = False
    motor_running = False
    
    # 모터 정지
    stop_motors()
    
    # 카메라 정리
    if camera and camera_type == 'picamera2':
        try:
            camera.stop()
        except:
            pass
    elif camera and camera_type == 'usb':
        try:
            camera.release()
        except:
            pass
    
    # GPIO 정리
    if GPIO_AVAILABLE:
        try:
            if pwm_right:
                pwm_right.stop()
            if pwm_left:
                pwm_left.stop()
            GPIO.cleanup()
            print("🧹 GPIO 정리 완료")
        except:
            pass

def get_server_ip():
    """서버 IP 주소를 안전하게 가져옵니다."""
    try:
        result = subprocess.check_output(['hostname', '-I'], 
                                       shell=False, 
                                       timeout=5,
                                       text=True)
        return result.strip().split()[0]
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, IndexError):
        return '127.0.0.1'

# 정리 함수 등록
atexit.register(cleanup)

if __name__ == '__main__':
    try:
        print("🚀 패스파인더 통합 제어 시스템 시작!")
        print("=" * 60)
        
        # 하드웨어 초기화
        if setup_gpio():
            print("✅ GPIO 초기화 완료")
        else:
            print("⚠️ GPIO 초기화 실패 - 시뮬레이션 모드")
        
        if setup_camera():
            print(f"✅ 카메라 초기화 완료 ({camera_type})")
        else:
            print("⚠️ 카메라 초기화 실패")
        
        # 시작 시 모터 정지
        stop_motors()
        
        # 백그라운드 스레드 시작
        motor_thread = threading.Thread(target=motor_control_thread)
        motor_thread.daemon = True
        motor_thread.start()
        print("✅ 모터 제어 스레드 시작")
        
        ultrasonic_thread = threading.Thread(target=ultrasonic_sensor_thread)
        ultrasonic_thread.daemon = True
        ultrasonic_thread.start()
        print("✅ 초음파 센서 스레드 시작")
        
        # 서버 정보 출력
        server_ip = get_server_ip()
        print("=" * 60)
        print(f"🌐 브라우저에서 http://{server_ip}:5000 으로 접속하세요")
        print(f"🌐 로컬에서는 http://localhost:5000 으로도 접속 가능")
        print("📱 모바일에서도 접속 가능합니다!")
        print("⚡ 실시간 WebSocket 통신 지원")
        print("🎮 키보드 제어: WASD + QE + ZC")
        print("📹 실시간 카메라 스트리밍")
        print("📏 자동 초음파 센서 측정")
        print("🔧 디버깅: 브라우저 개발자 도구(F12) 콘솔 확인")
        print("Ctrl+C로 종료")
        print("=" * 60)
        
        # SocketIO 서버 실행
        print("🚀 Flask-SocketIO 서버 시작 중...")
        socketio.run(app, 
                    host='0.0.0.0', 
                    port=5000, 
                    debug=False,
                    allow_unsafe_werkzeug=True)
        
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 종료됨")
    except Exception as e:
        print(f"❌ 시스템 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup()
        print("✅ 시스템 종료 완료") 