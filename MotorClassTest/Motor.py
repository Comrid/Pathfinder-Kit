"""
Motor.py - 패스파인더 키트용 간단한 모터 컨트롤러
라인 트레이싱에 최적화된 모터 제어 클래스
"""

import RPi.GPIO as GPIO
import time

# 모터 핀 설정 (실제 하드웨어에 맞게 설정)
RIGHT_MOTOR_IN1 = 23
RIGHT_MOTOR_IN2 = 24
LEFT_MOTOR_IN1 = 22
LEFT_MOTOR_IN2 = 27
RIGHT_MOTOR_PWM = 12
LEFT_MOTOR_PWM = 13

# 기본 속도 설정
NORMAL_SPEED = 100
TURN_SPEED = 80

class MotorController:
    """간단한 모터 컨트롤러 클래스"""
    
    def __init__(self):
        # GPIO 설정
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # 모터 핀 설정
        self.right_in1 = RIGHT_MOTOR_IN1
        self.right_in2 = RIGHT_MOTOR_IN2
        self.left_in1 = LEFT_MOTOR_IN1
        self.left_in2 = LEFT_MOTOR_IN2
        self.right_pwm_pin = RIGHT_MOTOR_PWM
        self.left_pwm_pin = LEFT_MOTOR_PWM
        
        # GPIO 핀 모드 설정
        GPIO.setup(self.right_in1, GPIO.OUT)
        GPIO.setup(self.right_in2, GPIO.OUT)
        GPIO.setup(self.left_in1, GPIO.OUT)
        GPIO.setup(self.left_in2, GPIO.OUT)
        GPIO.setup(self.right_pwm_pin, GPIO.OUT)
        GPIO.setup(self.left_pwm_pin, GPIO.OUT)
            
        # PWM 객체 생성
        self.right_pwm = GPIO.PWM(self.right_pwm_pin, 1000)
        self.left_pwm = GPIO.PWM(self.left_pwm_pin, 1000)
        
        # PWM 시작
        self.right_pwm.start(0)
        self.left_pwm.start(0)
            
        print("모터 컨트롤러 초기화 완료")
            
    def set_motor_direction(self, motor, direction):
        """모터 방향 설정"""
        if motor == "right":
            if direction == "forward":
                GPIO.output(self.right_in1, GPIO.HIGH)
                GPIO.output(self.right_in2, GPIO.LOW)
            elif direction == "backward":
                GPIO.output(self.right_in1, GPIO.LOW)
                GPIO.output(self.right_in2, GPIO.HIGH)
            else:  # stop
                GPIO.output(self.right_in1, GPIO.LOW)
                GPIO.output(self.right_in2, GPIO.LOW)
        
        elif motor == "left":
            if direction == "forward":
                GPIO.output(self.left_in1, GPIO.HIGH)
                GPIO.output(self.left_in2, GPIO.LOW)
            elif direction == "backward":
                GPIO.output(self.left_in1, GPIO.LOW)
                GPIO.output(self.left_in2, GPIO.HIGH)
            else:  # stop
                GPIO.output(self.left_in1, GPIO.LOW)
                GPIO.output(self.left_in2, GPIO.LOW)
        
    def set_motor_speed(self, motor, speed):
        """모터 속도 설정 (0-100)"""
        speed = max(0, min(100, speed))  # 0-100 범위로 제한
        
        if motor == "right":
            self.right_pwm.ChangeDutyCycle(speed)
        elif motor == "left":
            self.left_pwm.ChangeDutyCycle(speed)
    
    def set_individual_speeds(self, right_speed, left_speed):
        """좌우 모터 개별 속도 설정 (라인 트레이싱용)"""
        # 속도가 0이면 정지
        if right_speed == 0:
            self.set_motor_direction("right", "stop")
            self.set_motor_speed("right", 0)
        else:
            self.set_motor_direction("right", "forward")
            self.set_motor_speed("right", right_speed)
        
        if left_speed == 0:
            self.set_motor_direction("left", "stop")
            self.set_motor_speed("left", 0)
        else:
            self.set_motor_direction("left", "forward")
            self.set_motor_speed("left", left_speed)
    
    def move_forward(self, speed=NORMAL_SPEED):
        """전진"""
        self.set_motor_direction("right", "forward")
        self.set_motor_direction("left", "forward")
        self.set_motor_speed("right", speed)
        self.set_motor_speed("left", speed)
    
    def move_backward(self, speed=NORMAL_SPEED):
        """후진"""
        self.set_motor_direction("right", "backward")
        self.set_motor_direction("left", "backward")
        self.set_motor_speed("right", speed)
        self.set_motor_speed("left", speed)
    
    def turn_left(self, speed=TURN_SPEED):
        """좌회전"""
        self.set_motor_direction("right", "forward")
        self.set_motor_direction("left", "backward")
        self.set_motor_speed("right", speed)
        self.set_motor_speed("left", speed)
    
    def turn_right(self, speed=TURN_SPEED):
        """우회전"""
        self.set_motor_direction("right", "backward")
        self.set_motor_direction("left", "forward")
        self.set_motor_speed("right", speed)
        self.set_motor_speed("left", speed)
    
    def stop_motors(self):
        """모터 정지"""
        self.set_motor_direction("right", "stop")
        self.set_motor_direction("left", "stop")
        self.set_motor_speed("right", 0)
        self.set_motor_speed("left", 0)
    
    def cleanup(self):
        """GPIO 정리"""
                self.stop_motors()
        self.right_pwm.stop()
        self.left_pwm.stop()
            GPIO.cleanup()
        print("모터 컨트롤러 정리 완료")
            
# 간단한 테스트 함수
def test_motor():
    """모터 테스트"""
    motor = MotorController()
    
    try:
        print("전진 테스트...")
        motor.move_forward(50)
            time.sleep(2)
            
        print("좌회전 테스트...")
        motor.turn_left(50)
            time.sleep(1)
            
        print("우회전 테스트...")
        motor.turn_right(50)
            time.sleep(1)
            
        print("정지")
        motor.stop_motors()
            
    except KeyboardInterrupt:
        print("테스트 중단")
    
    finally:
        motor.cleanup()

if __name__ == "__main__":
    test_motor() 