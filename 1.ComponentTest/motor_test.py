import RPi.GPIO as GPIO
import time

# 모터 A (왼쪽 모터)
IN1 = 27
IN2 = 22
ENA = 13  # PWM

# 모터 B (오른쪽 모터)
IN3 = 23
IN4 = 24
ENB = 12   # PWM

# GPIO 설정
GPIO.setmode(GPIO.BCM)  # 혹은 GPIO.BOARD로 변경 가능
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)

GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)
GPIO.setup(ENB, GPIO.OUT)

# PWM 객체 생성 (주파수: 1000Hz)
pwmA = GPIO.PWM(ENA, 1000)
pwmB = GPIO.PWM(ENB, 1000)
pwmA.start(0)
pwmB.start(0)

try:
    while True:
        # 정방향 회전
        print("Forward")
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
        pwmA.ChangeDutyCycle(100)

        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
        pwmB.ChangeDutyCycle(100)

        time.sleep(3)

        # 정지 
        print("Stop")
        pwmA.ChangeDutyCycle(0)
        pwmB.ChangeDutyCycle(0)
        time.sleep(1)

        # 역방향 회전
        print("Backward")
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
        pwmA.ChangeDutyCycle(100)
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)
        pwmB.ChangeDutyCycle(100)

        time.sleep(3)

        # 정지
        print("Stop")
        pwmA.ChangeDutyCycle(0)
        pwmB.ChangeDutyCycle(0)
        time.sleep(1)

except KeyboardInterrupt:
    print("종료 중...")
    pass

finally:
    pwmA.stop()
    pwmB.stop()
    GPIO.cleanup()