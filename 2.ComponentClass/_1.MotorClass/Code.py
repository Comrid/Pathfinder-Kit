from MotorClass import *
import RPi.GPIO as GPIO
import time

# 핀 연결
motor = DualMotor(
    in1=22, in2=27,  # 왼쪽 모터
    in3=23, in4=24,  # 오른쪽 모터
    ena=13, enb=12   # PWM 핀
)


try:
    while True:
        print("전진")
        motor.forward()
        time.sleep(2)

        print("좌회전")
        motor.left()
        time.sleep(1)

        print("우회전")
        motor.right()
        time.sleep(1)

        print("후진")
        motor.backward()
        time.sleep(2)

        print("정지")
        motor.stop()
        time.sleep(1)

except KeyboardInterrupt:
    print("종료 중...")

finally:
    motor.cleanup()
    GPIO.cleanup()