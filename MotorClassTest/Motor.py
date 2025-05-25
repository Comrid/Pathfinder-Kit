import RPi.GPIO as GPIO
import time

# Config 파일에서 설정값들 import
import config

class MotorController:
    """
    패스파인더 키트용 모터 컨트롤러 클래스
    """
    
    def __init__(self):
        """모터 컨트롤러 초기화"""
        # PWM 객체들
        self.pwm_right = None
        self.pwm_left = None
        
        # 초기화
        self.setup()
    
    def setup(self):
        """GPIO 핀 및 PWM 초기화"""
        try:
            # GPIO 설정
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            
            # 핀 설정
            GPIO.setup(config.RIGHT_MOTOR_IN1, GPIO.OUT)
            GPIO.setup(config.RIGHT_MOTOR_IN2, GPIO.OUT)
            GPIO.setup(config.LEFT_MOTOR_IN3, GPIO.OUT)
            GPIO.setup(config.LEFT_MOTOR_IN4, GPIO.OUT)
            GPIO.setup(config.RIGHT_MOTOR_ENA, GPIO.OUT)
            GPIO.setup(config.LEFT_MOTOR_ENB, GPIO.OUT)
            
            # PWM 설정
            self.pwm_right = GPIO.PWM(config.RIGHT_MOTOR_ENA, config.PWM_FREQUENCY)
            self.pwm_left = GPIO.PWM(config.LEFT_MOTOR_ENB, config.PWM_FREQUENCY)
            self.pwm_right.start(0)
            self.pwm_left.start(0)
            
            # 초기 상태: 모터 정지
            self.stop_motors()
            
            self.debug_print("모터 컨트롤러 초기화 완료")
            
        except Exception as e:
            self.debug_print(f"모터 컨트롤러 초기화 오류: {e}")
            raise
    
    def debug_print(self, message):
        """디버그 메시지 출력"""
        if config.DEBUG:
            print(f"[MotorController] {message}")
    
    def stop_motors(self):
        """모든 모터 정지"""
        self.debug_print("모터 정지")
        GPIO.output(config.RIGHT_MOTOR_IN1, GPIO.LOW)
        GPIO.output(config.RIGHT_MOTOR_IN2, GPIO.LOW)
        GPIO.output(config.LEFT_MOTOR_IN3, GPIO.LOW)
        GPIO.output(config.LEFT_MOTOR_IN4, GPIO.LOW)
        
        if self.pwm_right and self.pwm_left:
            self.pwm_right.ChangeDutyCycle(0)
            self.pwm_left.ChangeDutyCycle(0)
    
    def set_motor_direction(self, right_forward, left_forward):
        """
        모터 방향 설정
        
        right_forward: 오른쪽 모터 전진 여부
        left_forward: 왼쪽 모터 전진 여부
        """
        # 오른쪽 모터 방향 설정
        if right_forward:
            GPIO.output(config.RIGHT_MOTOR_IN1, GPIO.HIGH)
            GPIO.output(config.RIGHT_MOTOR_IN2, GPIO.LOW)
        else:
            GPIO.output(config.RIGHT_MOTOR_IN1, GPIO.LOW)
            GPIO.output(config.RIGHT_MOTOR_IN2, GPIO.HIGH)
        
        # 왼쪽 모터 방향 설정
        if left_forward:
            GPIO.output(config.LEFT_MOTOR_IN3, GPIO.HIGH)
            GPIO.output(config.LEFT_MOTOR_IN4, GPIO.LOW)
        else:
            GPIO.output(config.LEFT_MOTOR_IN3, GPIO.LOW)
            GPIO.output(config.LEFT_MOTOR_IN4, GPIO.HIGH)
    
    def set_motor_speed(self, right_speed, left_speed):
        """
        모터 속도 설정
        
        right_speed: 오른쪽 모터 속도 (0-100)
        left_speed: 왼쪽 모터 속도 (0-100)
        """
        if self.pwm_right and self.pwm_left:
            # 속도 범위 제한
            right_speed = max(0, min(100, right_speed))
            left_speed = max(0, min(100, left_speed))
            
            self.pwm_right.ChangeDutyCycle(right_speed)
            self.pwm_left.ChangeDutyCycle(left_speed)
    
    # === 기본 이동 명령들 ===
    
    def move_forward(self, speed=None):
        """전진"""
        speed = speed or config.NORMAL_SPEED
        self.debug_print(f"전진 - 속도: {speed}")
        self.set_motor_direction(True, True)
        self.set_motor_speed(speed, speed)
    
    def move_backward(self, speed=None):
        """후진"""
        speed = speed or config.NORMAL_SPEED
        self.debug_print(f"후진 - 속도: {speed}")
        self.set_motor_direction(False, False)
        self.set_motor_speed(speed, speed)
    
    def turn_left(self, speed=None):
        """제자리 좌회전"""
        speed = speed or config.TURN_SPEED
        self.debug_print(f"좌회전 - 속도: {speed}")
        self.set_motor_direction(True, False)
        self.set_motor_speed(speed, speed)
    
    def turn_right(self, speed=None):
        """제자리 우회전"""
        speed = speed or config.TURN_SPEED
        self.debug_print(f"우회전 - 속도: {speed}")
        self.set_motor_direction(False, True)
        self.set_motor_speed(speed, speed)
    
    # === 대각선 이동 명령들 ===
    
    def move_forward_left(self, speed=None):
        """왼쪽 앞으로 (오른쪽 모터가 더 빠름)"""
        speed = speed or config.NORMAL_SPEED
        diagonal_speed = int(speed * config.DIAGONAL_SPEED / 100)
        self.debug_print(f"왼쪽 앞으로 - 오른쪽: {speed}, 왼쪽: {diagonal_speed}")
        self.set_motor_direction(True, True)
        self.set_motor_speed(speed, diagonal_speed)
    
    def move_forward_right(self, speed=None):
        """오른쪽 앞으로 (왼쪽 모터가 더 빠름)"""
        speed = speed or config.NORMAL_SPEED
        diagonal_speed = int(speed * config.DIAGONAL_SPEED / 100)
        self.debug_print(f"오른쪽 앞으로 - 오른쪽: {diagonal_speed}, 왼쪽: {speed}")
        self.set_motor_direction(True, True)
        self.set_motor_speed(diagonal_speed, speed)
    
    def move_backward_left(self, speed=None):
        """왼쪽 뒤로 (오른쪽 모터가 더 빠름)"""
        speed = speed or config.NORMAL_SPEED
        diagonal_speed = int(speed * config.DIAGONAL_SPEED / 100)
        self.debug_print(f"왼쪽 뒤로 - 오른쪽: {speed}, 왼쪽: {diagonal_speed}")
        self.set_motor_direction(False, False)
        self.set_motor_speed(speed, diagonal_speed)
    
    def move_backward_right(self, speed=None):
        """오른쪽 뒤로 (왼쪽 모터가 더 빠름)"""
        speed = speed or config.NORMAL_SPEED
        diagonal_speed = int(speed * config.DIAGONAL_SPEED / 100)
        self.debug_print(f"오른쪽 뒤로 - 오른쪽: {diagonal_speed}, 왼쪽: {speed}")
        self.set_motor_direction(False, False)
        self.set_motor_speed(diagonal_speed, speed)
    
    # === 고급 제어 메서드들 ===
    
    def set_individual_speeds(self, right_speed, left_speed):
        """
        각 모터의 속도를 개별적으로 설정 (음수는 후진)
        
        right_speed: 오른쪽 모터 속도 (-100 ~ 100)
        left_speed: 왼쪽 모터 속도 (-100 ~ 100)
        """
        # 오른쪽 모터
        if right_speed >= 0:
            GPIO.output(config.RIGHT_MOTOR_IN1, GPIO.HIGH)
            GPIO.output(config.RIGHT_MOTOR_IN2, GPIO.LOW)
        else:
            GPIO.output(config.RIGHT_MOTOR_IN1, GPIO.LOW)
            GPIO.output(config.RIGHT_MOTOR_IN2, GPIO.HIGH)
        
        # 왼쪽 모터
        if left_speed >= 0:
            GPIO.output(config.LEFT_MOTOR_IN3, GPIO.HIGH)
            GPIO.output(config.LEFT_MOTOR_IN4, GPIO.LOW)
        else:
            GPIO.output(config.LEFT_MOTOR_IN3, GPIO.LOW)
            GPIO.output(config.LEFT_MOTOR_IN4, GPIO.HIGH)
        
        # 속도 설정
        if self.pwm_right and self.pwm_left:
            self.pwm_right.ChangeDutyCycle(abs(right_speed))
            self.pwm_left.ChangeDutyCycle(abs(left_speed))
    
    def execute_command(self, command, speed=None):
        """
        문자열 명령 실행
        
        command: 실행할 명령
        speed: 속도 (None이면 기본값 사용)
        """
        try:
            speed = speed or config.NORMAL_SPEED
            
            if command == "forward":
                self.move_forward(speed)
            elif command == "backward":
                self.move_backward(speed)
            elif command == "left":
                self.turn_left(speed)
            elif command == "right":
                self.turn_right(speed)
            elif command == "forward-left":
                self.move_forward_left(speed)
            elif command == "forward-right":
                self.move_forward_right(speed)
            elif command == "backward-left":
                self.move_backward_left(speed)
            elif command == "backward-right":
                self.move_backward_right(speed)
            elif command == "stop":
                self.stop_motors()
            else:
                self.debug_print(f"알 수 없는 명령: {command}")
                return False
            
            return True
            
        except Exception as e:
            self.debug_print(f"명령 실행 오류: {e}")
            return False
    
    def test_motors(self):
        """모터 테스트 함수"""
        self.debug_print("모터 테스트 시작")
        
        try:
            # 오른쪽 모터 테스트
            self.debug_print("오른쪽 모터 전진 테스트")
            GPIO.output(config.RIGHT_MOTOR_IN1, GPIO.HIGH)
            GPIO.output(config.RIGHT_MOTOR_IN2, GPIO.LOW)
            if self.pwm_right:
                self.pwm_right.ChangeDutyCycle(100)
            time.sleep(1)
            if self.pwm_right:
                self.pwm_right.ChangeDutyCycle(0)
            
            # 왼쪽 모터 테스트
            self.debug_print("왼쪽 모터 전진 테스트")
            GPIO.output(config.LEFT_MOTOR_IN3, GPIO.HIGH)
            GPIO.output(config.LEFT_MOTOR_IN4, GPIO.LOW)
            if self.pwm_left:
                self.pwm_left.ChangeDutyCycle(100)
            time.sleep(1)
            if self.pwm_left:
                self.pwm_left.ChangeDutyCycle(0)
            
            self.debug_print("모터 테스트 완료")
            
        except Exception as e:
            self.debug_print(f"모터 테스트 오류: {e}")
        finally:
            self.stop_motors()
    
    def cleanup(self):
        """리소스 정리"""
        try:
            self.stop_motors()
            
            if self.pwm_right:
                self.pwm_right.stop()
            if self.pwm_left:
                self.pwm_left.stop()
            
            GPIO.cleanup()
            self.debug_print("모터 컨트롤러 정리 완료")
            
        except Exception as e:
            self.debug_print(f"정리 중 오류: {e}")
    
    def __enter__(self):
        """Context manager 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.cleanup()


# 사용 예제
if __name__ == "__main__":
    try:
        # 기본 설정으로 모터 컨트롤러 생성
        with MotorController() as motors:
            # 테스트 시퀀스
            print("=== 패스파인더 모터 컨트롤러 테스트 ===")
            
            # 개별 모터 테스트
            motors.test_motors()
            time.sleep(1)
            
            # 기본 이동 테스트
            print("\n기본 이동 테스트:")
            motors.move_forward(50)
            time.sleep(2)
            
            motors.turn_right(50)
            time.sleep(1)
            
            motors.move_backward(50)
            time.sleep(2)
            
            motors.turn_left(50)
            time.sleep(1)
            
            # 대각선 이동 테스트
            print("\n대각선 이동 테스트:")
            motors.move_forward_left(50)
            time.sleep(2)
            
            motors.move_forward_right(50)
            time.sleep(2)
            
            motors.move_backward_left(50)
            time.sleep(2)
            
            motors.move_backward_right(50)
            time.sleep(2)
            
            # 명령 문자열 테스트
            print("\n명령 문자열 테스트:")
            commands = ["forward", "right", "backward", "left", "stop"]
            for cmd in commands:
                print(f"명령 실행: {cmd}")
                motors.execute_command(cmd, 60)
                time.sleep(1)
            
            print("\n테스트 완료!")
            
    except KeyboardInterrupt:
        print("\n사용자에 의해 테스트 중단")
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
    finally:
        print("정리 완료")
