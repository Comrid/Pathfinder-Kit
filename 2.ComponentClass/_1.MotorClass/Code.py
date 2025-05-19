from flask import Flask, render_template, request
import RPi.GPIO as GPIO
from MotorClass import DualMotor

app = Flask(__name__)
GPIO.setmode(GPIO.BCM)

motor = DualMotor(in1=22, in2=27, in3=23, in4=24, ena=13, enb=12)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/move', methods=['POST'])
def move():
    direction = request.form['direction']
    if direction == 'forward':
        motor.forward()
    elif direction == 'backward':
        motor.backward()
    elif direction == 'left':
        motor.left()
    elif direction == 'right':
        motor.right()
    elif direction == 'stop':
        motor.stop()
    return '', 204  # 응답 없음 (빠르게 처리)
    
@app.route('/cleanup')
def cleanup():
    motor.cleanup()
    GPIO.cleanup()
    return 'GPIO cleaned up.'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)