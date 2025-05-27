import RPi.GPIO as GPIO
import time
import logging
import sys
from typing import Optional

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 모터 A (왼쪽 모터)
IN1 = 22
IN2 = 27
ENA = 13  # PWM

# 모터 B (오른쪽 모터)
IN3 = 23
IN4 = 24
ENB = 12   # PWM

# 모터 속도 설정 (안전한 범위로 제한)
MIN_SPEED = 30
MAX_SPEED = 100
DEFAULT_SPEED = 70

class MotorTester:
    """안전한 모터 테스트를 위한 클래스"""
    
    def __init__(self, speed: int = DEFAULT_SPEED):
        self.speed = self._validate_speed(speed)
        self.pwmA: Optional[GPIO.PWM] = None
        self.pwmB: Optional[GPIO.PWM] = None
        self._setup_gpio()
    
    def _validate_speed(self, speed: int) -> int:
        """속도 값 검증 및 안전 범위로 제한"""
        if not isinstance(speed, int):
            logger.warning(f"속도는 정수여야 합니다. 기본값 {DEFAULT_SPEED} 사용")
            return DEFAULT_SPEED
        
        if speed < MIN_SPEED:
            logger.warning(f"속도가 너무 낮습니다. 최소값 {MIN_SPEED} 사용")
            return MIN_SPEED
        elif speed > MAX_SPEED:
            logger.warning(f"속도가 너무 높습니다. 최대값 {MAX_SPEED} 사용")
            return MAX_SPEED
        
        return speed
    
    def _setup_gpio(self):
        """GPIO 핀 설정"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # 모터 핀 설정
            pins = [IN1, IN2, ENA, IN3, IN4, ENB]
            for pin in pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)  # 초기 상태를 LOW로 설정
            
            # PWM 객체 생성 (주파수: 1000Hz)
            self.pwmA = GPIO.PWM(ENA, 1000)
            self.pwmB = GPIO.PWM(ENB, 1000)
            self.pwmA.start(0)
            self.pwmB.start(0)
            
            logger.info("GPIO 설정 완료")
            
        except Exception as e:
            logger.error(f"GPIO 설정 실패: {e}")
            self.cleanup()
            sys.exit(1)
    
    def stop_motors(self):
        """모터 즉시 정지"""
        if self.pwmA and self.pwmB:
            self.pwmA.ChangeDutyCycle(0)
            self.pwmB.ChangeDutyCycle(0)
            GPIO.output(IN1, GPIO.LOW)
            GPIO.output(IN2, GPIO.LOW)
            GPIO.output(IN3, GPIO.LOW)
            GPIO.output(IN4, GPIO.LOW)
    
    def move_forward(self, duration: float = 1.0):
        """전진"""
        logger.info(f"전진! (속도: {self.speed}%, 시간: {duration}초)")
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
        self.pwmA.ChangeDutyCycle(self.speed)
        self.pwmB.ChangeDutyCycle(self.speed)
        time.sleep(duration)
    
    def move_backward(self, duration: float = 1.0):
        """후진"""
        logger.info(f"후진! (속도: {self.speed}%, 시간: {duration}초)")
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)
        self.pwmA.ChangeDutyCycle(self.speed)
        self.pwmB.ChangeDutyCycle(self.speed)
        time.sleep(duration)
    
    def turn_left(self, duration: float = 0.5):
        """좌회전"""
        logger.info(f"좌회전! (속도: {self.speed}%, 시간: {duration}초)")
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
        GPIO.output(IN3, GPIO.HIGH)
        GPIO.output(IN4, GPIO.LOW)
        self.pwmA.ChangeDutyCycle(self.speed)
        self.pwmB.ChangeDutyCycle(self.speed)
        time.sleep(duration)
    
    def turn_right(self, duration: float = 0.5):
        """우회전"""
        logger.info(f"우회전! (속도: {self.speed}%, 시간: {duration}초)")
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)
        self.pwmA.ChangeDutyCycle(self.speed)
        self.pwmB.ChangeDutyCycle(self.speed)
        time.sleep(duration)
    
    def run_test_sequence(self):
        """종합 테스트 시퀀스 실행"""
        logger.info("🤖 패스파인더 모터 테스트 시작!")
        logger.info(f"⚡ 설정 속도: {self.speed}%")
        logger.info("🔄 전진 → 정지 → 후진 → 정지 → 좌회전 → 우회전 반복")
        logger.info("💡 Ctrl+C로 종료하세요")
        logger.info("-" * 50)
        
        try:
            while True:
                # 전진
                self.move_forward(1.0)
                self.stop_motors()
                logger.info("정지!")
                time.sleep(0.5)
                
                # 후진
                self.move_backward(1.0)
                self.stop_motors()
                logger.info("정지!")
                time.sleep(0.5)
                
                # 좌회전
                self.turn_left(0.5)
                self.stop_motors()
                logger.info("정지!")
                time.sleep(0.5)
                
                # 우회전
                self.turn_right(0.5)
                self.stop_motors()
                logger.info("정지!")
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            logger.info("사용자가 프로그램을 종료했습니다!")
        except Exception as e:
            logger.error(f"테스트 중 오류 발생: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """리소스 정리"""
        try:
            self.stop_motors()
            if self.pwmA:
                self.pwmA.stop()
            if self.pwmB:
                self.pwmB.stop()
            GPIO.cleanup()
            logger.info("GPIO 정리 완료")
        except Exception as e:
            logger.error(f"정리 중 오류 발생: {e}")

def main():
    """메인 함수"""
    try:
        # 사용자 입력으로 속도 설정 (선택사항)
        try:
            user_speed = input(f"모터 속도를 입력하세요 ({MIN_SPEED}-{MAX_SPEED}, 기본값: {DEFAULT_SPEED}): ").strip()
            if user_speed:
                speed = int(user_speed)
            else:
                speed = DEFAULT_SPEED
        except ValueError:
            logger.warning("잘못된 입력입니다. 기본 속도를 사용합니다.")
            speed = DEFAULT_SPEED
        
        # 모터 테스터 생성 및 실행
        motor_tester = MotorTester(speed)
        motor_tester.run_test_sequence()
        
    except Exception as e:
        logger.error(f"프로그램 실행 중 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()