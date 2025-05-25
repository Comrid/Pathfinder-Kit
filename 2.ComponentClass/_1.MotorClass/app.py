from flask import Flask, render_template, jsonify, request
import RPi.GPIO as GPIO
import time
import threading
import atexit

app = Flask(__name__)

# 전역 변수 - 모터 상태 관리
current_command = "stop"
motor_speed = 100
motor_running = True
command_lock = threading.Lock()

# GPIO 설정
GPIO.setwarnings(False)
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)

# 모터 드라이버 핀 설정 (사용자 제공 핀 번호)
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
pwm_right = GPIO.PWM(ENA, 1000)  # 오른쪽 모터 PWM (ENA = GPIO 12)
pwm_left = GPIO.PWM(ENB, 1000)   # 왼쪽 모터 PWM (ENB = GPIO 13)
pwm_right.start(0)
pwm_left.start(0)

# 모터 속도 설정 (0-100)
MOTOR_SPEED_NORMAL = 100
MOTOR_SPEED_TURN = 80
MOTOR_SPEED_DIAGONAL = 60

# 디버그 모드
DEBUG = True

def debug_print(message):
    if DEBUG:
        print(f"[DEBUG] {message}")

def stop_motors():
    debug_print("모터 정지")
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    pwm_right.ChangeDutyCycle(0)
    pwm_left.ChangeDutyCycle(0)

def set_motor_direction(right_forward, left_forward):
    # 오른쪽 모터 방향 설정
    if right_forward:
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
    else:
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
    
    # 왼쪽 모터 방향 설정
    if left_forward:
        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
    else:
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)

def set_motor_speed(right_speed, left_speed):
    pwm_right.ChangeDutyCycle(right_speed)
    pwm_left.ChangeDutyCycle(left_speed)

# 모터 제어 함수
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

# 모터 제어 스레드 함수
def motor_control_thread():
    last_command = "stop"
    last_speed = 100
    
    while motor_running:
        with command_lock:
            cmd = current_command
            spd = motor_speed
        
        # 명령이 변경되었거나 속도가 변경된 경우에만 모터 제어
        if cmd != last_command or spd != last_speed:
            debug_print(f"명령 실행: {cmd}, 속도: {spd}")
            
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
        
        # 짧은 대기 시간으로 CPU 사용량 감소
        time.sleep(0.01)

# Flask 라우트
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test-motors', methods=['POST'])
def test_motors_route():
    test_motors()
    return jsonify({"status": "success", "message": "모터 테스트 완료"})

@app.route('/command', methods=['POST'])
def command():
    global current_command, motor_speed
    
    data = request.get_json(silent=True) or {}
    cmd = data.get('command', 'stop')
    spd = data.get('speed', 100)
    
    with command_lock:
        current_command = cmd
        motor_speed = spd
    
    return jsonify({"status": "success", "command": cmd, "speed": spd})

@app.route('/speed', methods=['POST'])
def speed():
    global motor_speed
    
    data = request.get_json(silent=True) or {}
    spd = data.get('speed', 100)
    
    with command_lock:
        motor_speed = spd
    
    return jsonify({"status": "success", "speed": spd})

# 프로그램 종료 시 정리 함수
def cleanup():
    global motor_running
    motor_running = False
    time.sleep(0.2)  # 스레드가 종료될 시간을 줌
    stop_motors()
    GPIO.cleanup()
    print("GPIO 정리 완료")

# 종료 시 cleanup 함수 실행
atexit.register(cleanup)

if __name__ == '__main__':
    try:
        # 시작 시 모터 정지
        stop_motors()
        
        # 모터 제어 스레드 시작
        motor_thread = threading.Thread(target=motor_control_thread)
        motor_thread.daemon = True
        motor_thread.start()
        
        # 외부에서 접속 가능하도록 호스트를 0.0.0.0으로 설정
        print("웹 서버를 시작합니다...")
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        cleanup()
