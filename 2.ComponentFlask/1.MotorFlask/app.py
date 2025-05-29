#!/usr/bin/env python3
"""
Pathfinder Motor Control with Flask-SocketIO
실시간 모터 제어를 위한 WebSocket 기반 통합 시스템
"""

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import RPi.GPIO as GPIO
import time
import threading
import atexit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pathfinder-motor-control'
socketio = SocketIO(app, cors_allowed_origins="*")

# 전역 변수 - 모터 상태 관리
current_command = "stop"
motor_speed = 100
motor_running = True
command_lock = threading.Lock()

# GPIO 설정
GPIO.setwarnings(False)
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)

# 모터 드라이버 핀 설정
IN1 = 23  # 오른쪽 모터 방향 1
IN2 = 24  # 오른쪽 모터 방향 2
IN3 = 22  # 왼쪽 모터 방향 1
IN4 = 27  # 왼쪽 모터 방향 2
ENA = 12  # 오른쪽 모터 PWM
ENB = 13  # 왼쪽 모터 PWM

# GPIO 핀 설정
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(ENB, GPIO.OUT)

# PWM 설정
pwm_right = GPIO.PWM(ENA, 1000)
pwm_left = GPIO.PWM(ENB, 1000)
pwm_right.start(0)
pwm_left.start(0)

# 모터 속도 설정
MOTOR_SPEED_NORMAL = 100
MOTOR_SPEED_TURN = 80
MOTOR_SPEED_DIAGONAL = 60

DEBUG = True

def debug_print(message):
    if DEBUG:
        print(f"[DEBUG] {message}")
        # WebSocket으로 디버그 메시지 전송
        socketio.emit('debug_message', {'message': message})

def stop_motors():
    debug_print("모터 정지")
    try:
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.LOW)
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.LOW)
        pwm_right.ChangeDutyCycle(0)
        pwm_left.ChangeDutyCycle(0)
    except RuntimeError as e:
        # GPIO가 이미 정리된 경우 무시
        if "pin numbering mode" in str(e):
            print("⚠️ GPIO 이미 정리됨 - 모터 정지 건너뜀")
        else:
            raise e

def set_motor_direction(right_forward, left_forward):
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

def set_motor_speed(right_speed, left_speed):
    pwm_right.ChangeDutyCycle(right_speed)
    pwm_left.ChangeDutyCycle(left_speed)

# 모터 제어 함수들
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

def test_motors():
    """모터 테스트 함수"""
    debug_print("모터 테스트 시작")
    socketio.emit('motor_test_status', {'status': 'testing', 'message': '모터 테스트 중...'})
    
    # 오른쪽 모터 테스트
    debug_print("오른쪽 모터 전진 테스트")
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    pwm_right.ChangeDutyCycle(100)
    time.sleep(1)
    pwm_right.ChangeDutyCycle(0)
    
    # 왼쪽 모터 테스트
    debug_print("왼쪽 모터 전진 테스트")
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_left.ChangeDutyCycle(100)
    time.sleep(1)
    pwm_left.ChangeDutyCycle(0)
    
    debug_print("모터 테스트 완료")
    stop_motors()
    socketio.emit('motor_test_status', {'status': 'completed', 'message': '모터 테스트 완료'})

# 모터 제어 스레드
def motor_control_thread():
    last_command = "stop"
    last_speed = 100
    
    while motor_running:
        with command_lock:
            cmd = current_command
            spd = motor_speed
        
        if cmd != last_command or spd != last_speed:
            debug_print(f"명령 실행: {cmd}, 속도: {spd}")
            
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

# Flask 라우트
@app.route('/')
def index():
    return render_template('index.html')

# SocketIO 이벤트 핸들러
@socketio.on('connect')
def handle_connect():
    print(f"🔗 클라이언트 연결: {request.sid}")
    emit('debug_message', {'message': '클라이언트 연결됨'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"🔌 클라이언트 연결 해제: {request.sid}")

@socketio.on('motor_command')
def handle_motor_command(data):
    global current_command, motor_speed
    
    command = data.get('command', 'stop')
    speed = data.get('speed', 100)
    
    with command_lock:
        current_command = command
        motor_speed = speed
    
    print(f"📡 명령 수신: {command} (속도: {speed}%)")

@socketio.on('speed_change')
def handle_speed_change(data):
    global motor_speed
    
    speed = data.get('speed', 100)
    
    with command_lock:
        motor_speed = speed
    
    print(f"🎛️ 속도 변경: {speed}%")

@socketio.on('test_motors')
def handle_test_motors():
    print("🧪 모터 테스트 요청")
    # 별도 스레드에서 테스트 실행 (블로킹 방지)
    test_thread = threading.Thread(target=test_motors)
    test_thread.daemon = True
    test_thread.start()

# 정리 함수
def cleanup():
    global motor_running
    motor_running = False
    time.sleep(0.2)
    
    # GPIO 정리 전에 먼저 모터 정지
    try:
        stop_motors()
    except:
        pass  # GPIO 오류 무시
    
    # GPIO 정리
    try:
        GPIO.cleanup()
        print("🧹 GPIO 정리 완료")
    except:
        print("🧹 GPIO 정리 중 오류 (무시됨)")

atexit.register(cleanup)

if __name__ == '__main__':
    try:
        # 시작 시 모터 정지
        stop_motors()
        
        # 모터 제어 스레드 시작
        motor_thread = threading.Thread(target=motor_control_thread)
        motor_thread.daemon = True
        motor_thread.start()
        
        print("🚀 Pathfinder Motor Control with SocketIO 시작!")
        import subprocess
        ip = subprocess.check_output(['hostname', '-I'], shell=False).decode().split()[0]
        print(f"🌐 브라우저에서 http://{ip}:5000 으로 접속하세요")
        print("⚡ 실시간 WebSocket 통신 지원")
        
        # SocketIO 서버 실행
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        cleanup()
