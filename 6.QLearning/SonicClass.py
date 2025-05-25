"""
SonicClass.py - HC-SR04 초음파 센서 클래스
sonic_test.py 코드를 기반으로 한 간단한 초음파 센서 컨트롤러
"""

import RPi.GPIO as GPIO
import time
from typing import Optional

class UltrasonicSensor:
    """
    HC-SR04 초음파 센서 컨트롤러 클래스
    
    간단한 거리 측정 기능을 제공합니다.
    """
    
    def __init__(self, trigger_pin: int = 5, echo_pin: int = 6):
        """
        초음파 센서 초기화
        
        Args:
            trigger_pin (int): TRIG 핀 번호 (기본값: 5)
            echo_pin (int): ECHO 핀 번호 (기본값: 6)
        """
        self.trig_pin = trigger_pin
        self.echo_pin = echo_pin
        
        # GPIO 설정
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.trig_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        
        # 초기화 대기
        time.sleep(0.1)
        print(f"초음파 센서 초기화 완료 (TRIG: GPIO{self.trig_pin}, ECHO: GPIO{self.echo_pin})")
    
    def get_distance(self) -> Optional[float]:
        """
        거리 측정
        
        Returns:
            Optional[float]: 측정된 거리(cm), 실패 시 None
        """
        try:
            # TRIG 신호 짧게 발생
            GPIO.output(self.trig_pin, True)
            time.sleep(0.00001)  # 10µs
            GPIO.output(self.trig_pin, False)
            
            # ECHO 신호의 시작 시간 대기 (타임아웃 추가)
            timeout_start = time.time()
            while GPIO.input(self.echo_pin) == 0:
                start_time = time.time()
                if time.time() - timeout_start > 0.1:  # 100ms 타임아웃
                    return None
            
            # ECHO 신호의 끝 시간 대기 (타임아웃 추가)
            timeout_start = time.time()
            while GPIO.input(self.echo_pin) == 1:
                end_time = time.time()
                if time.time() - timeout_start > 0.1:  # 100ms 타임아웃
                    return None
            
            # 거리 계산
            duration = end_time - start_time
            distance = (duration * 34300) / 2  # cm 단위
            
            # 유효 범위 확인 (HC-SR04 측정 범위: 2-400cm)
            if 2 <= distance <= 400:
                return round(distance, 2)
            else:
                return None
                
        except Exception as e:
            print(f"거리 측정 오류: {e}")
            return None
    
    def get_distance_average(self, samples: int = 3) -> Optional[float]:
        """
        여러 번 측정하여 평균값 반환
        
        Args:
            samples (int): 측정 횟수 (기본값: 3)
            
        Returns:
            Optional[float]: 평균 거리(cm), 실패 시 None
        """
        distances = []
        
        for _ in range(samples):
            distance = self.get_distance()
            if distance is not None:
                distances.append(distance)
            time.sleep(0.01)  # 측정 간격
        
        if distances:
            return round(sum(distances) / len(distances), 2)
        else:
            return None
    
    def is_obstacle_detected(self, threshold: float = 30.0) -> bool:
        """
        장애물 감지 여부 확인
        
        Args:
            threshold (float): 감지 임계값(cm) (기본값: 30.0)
            
        Returns:
            bool: 장애물 감지 시 True, 아니면 False
        """
        distance = self.get_distance()
        if distance is not None:
            return distance <= threshold
        return False
    
    def cleanup(self):
        """GPIO 정리"""
        # 다른 컴포넌트가 GPIO를 사용할 수 있으므로 cleanup은 신중하게
        pass
    
    def test_sensor(self, duration: int = 10):
        """
        센서 테스트 (지정된 시간 동안 거리 측정)
        
        Args:
            duration (int): 테스트 시간(초) (기본값: 10)
        """
        print(f"초음파 센서 테스트 시작 ({duration}초)")
        print("Ctrl+C로 중단 가능")
        
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                distance = self.get_distance()
                if distance is not None:
                    print(f"거리: {distance} cm")
                else:
                    print("측정 실패")
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n테스트 중단")
        
        print("테스트 완료")


# 테스트 함수
def test_ultrasonic():
    """초음파 센서 테스트"""
    sensor = UltrasonicSensor()
    
    try:
        sensor.test_sensor(10)
    finally:
        sensor.cleanup()


if __name__ == "__main__":
    test_ultrasonic()
