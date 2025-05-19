from flask import Flask, render_template, request
from motor import DualMotor  # motor.py에 DualMotor 클래스 정의되어 있어야 함
import RPi.GPIO as GPIO

app = Flask(__name__)

# 모터 핀 번호 설정 (예: L298N 기준)
motor = DualMotor(in1=17, in2=27, in3=23, in4=24, ena=18, enb=25)  # BCM 기준 핀 번호 설정

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<command>', methods=['POST'])
def control_motor(command):
    try:
        if command == 'forward':
            motor.forward()
        elif command == 'backward':
            motor.backward()
        elif command == 'left':
            motor.left()
        elif command == 'right':
            motor.right()
        elif command == 'forward-left':
            motor.left()
        elif command == 'forward-right':
            motor.right()
        elif command == 'backward-left':
            motor.left()
        elif command == 'backward-right':
            motor.right()
        elif command == 'stop':
            motor.stop()
    except Exception as e:
        print(f"[ERROR] {e}")
        motor.stop()
    return ('', 204)  # 응답 없음

@app.route('/cleanup')
def cleanup():
    motor.cleanup()
    GPIO.cleanup()
    return "Cleaned up"

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        motor.cleanup()
        GPIO.cleanup()
