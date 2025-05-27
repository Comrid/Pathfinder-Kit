import RPi.GPIO as GPIO
import time

# 모터 A (왼쪽 모터)
IN1 = 22
IN2 = 27
ENA = 13  # PWM

# 모터 B (오른쪽 모터)
IN3 = 23
IN4 = 24
ENB = 12   # PWM

# 모터 속도(50~100)
SPEED = 100

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
    print("🤖 패스파인더 모터 테스트 시작!")
    print(f"⚡ 설정 속도: {SPEED}%")
    print("🔄 전진(1초) → 정지(1초) → 후진(1초) → 정지(1초) 반복")
    print("💡 Ctrl+C로 종료하세요")
    print("-" * 40)
    while True:
        # 정방향 회전
        print("전진!", end="\t")
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
        pwmA.ChangeDutyCycle(SPEED)
        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
        pwmB.ChangeDutyCycle(SPEED)
        time.sleep(1)

        # 정지 
        print("정지!", end="\t")
        pwmA.ChangeDutyCycle(0)
        pwmB.ChangeDutyCycle(0)
        time.sleep(1)

        # 역방향 회전
        print("후진!", end="\t")
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
        pwmA.ChangeDutyCycle(SPEED)
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)
        pwmB.ChangeDutyCycle(SPEED)
        time.sleep(1)

        # 정지
        print("정지!", end="\n")
        pwmA.ChangeDutyCycle(0)
        pwmB.ChangeDutyCycle(0)
        time.sleep(1)

except KeyboardInterrupt:
    print("프로그램을 종료합니다!")

finally:
    pwmA.stop()
    pwmB.stop()
    GPIO.cleanup()