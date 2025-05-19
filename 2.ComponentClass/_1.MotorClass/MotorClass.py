import RPi.GPIO as GPIO
import time

class DualMotor:
    def __init__(self, in1, in2, in3, in4, ena, enb, freq=1000):
        GPIO.setmode(GPIO.BCM)
        # 왼쪽 모터
        self.IN1 = in1
        self.IN2 = in2
        self.ENA = ena
        # 오른쪽 모터
        self.IN3 = in3
        self.IN4 = in4
        self.ENB = enb

        # GPIO 설정
        GPIO.setup(self.IN1, GPIO.OUT)
        GPIO.setup(self.IN2, GPIO.OUT)
        GPIO.setup(self.ENA, GPIO.OUT)
        GPIO.setup(self.IN3, GPIO.OUT)
        GPIO.setup(self.IN4, GPIO.OUT)
        GPIO.setup(self.ENB, GPIO.OUT)
        
        # PWM 객체 생성
        self.pwmA = GPIO.PWM(self.ENA, freq)
        self.pwmB = GPIO.PWM(self.ENB, freq)
        self.pwmA.start(0)
        self.pwmB.start(0)

    def forward(self, speed=100):
        GPIO.output(self.IN1, GPIO.HIGH)
        GPIO.output(self.IN2, GPIO.LOW)
        GPIO.output(self.IN3, GPIO.HIGH)
        GPIO.output(self.IN4, GPIO.LOW)
        self.pwmA.ChangeDutyCycle(speed)
        self.pwmB.ChangeDutyCycle(speed)
        
    def backward(self, speed=100):
        GPIO.output(self.IN1, GPIO.LOW)
        GPIO.output(self.IN2, GPIO.HIGH)
        GPIO.output(self.IN3, GPIO.LOW)
        GPIO.output(self.IN4, GPIO.HIGH)
        self.pwmA.ChangeDutyCycle(speed)
        self.pwmB.ChangeDutyCycle(speed)

    def left(self, speed=100):
        # 왼쪽 모터 뒤로, 오른쪽 모터 앞으로
        GPIO.output(self.IN1, GPIO.LOW)
        GPIO.output(self.IN2, GPIO.HIGH)
        GPIO.output(self.IN3, GPIO.HIGH)
        GPIO.output(self.IN4, GPIO.LOW)
        self.pwmA.ChangeDutyCycle(speed)
        self.pwmB.ChangeDutyCycle(speed)
        
    def right(self, speed=100):
        # 왼쪽 모터 앞으로, 오른쪽 모터 뒤로
        GPIO.output(self.IN1, GPIO.HIGH)
        GPIO.output(self.IN2, GPIO.LOW)
        GPIO.output(self.IN3, GPIO.LOW)
        GPIO.output(self.IN4, GPIO.HIGH)
        self.pwmA.ChangeDutyCycle(speed)
        self.pwmB.ChangeDutyCycle(speed)

    def stop(self):
        self.pwmA.ChangeDutyCycle(0)
        self.pwmB.ChangeDutyCycle(0)

    def cleanup(self):
        self.pwmA.stop()
        self.pwmB.stop()