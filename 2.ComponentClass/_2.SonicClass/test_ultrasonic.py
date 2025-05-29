#!/usr/bin/env python3
"""
Pathfinder Ultrasonic Sensor Test Script
초음파 센서 기본 동작 테스트
"""

import RPi.GPIO as GPIO
import time
import statistics

# 핀 번호 설정 (BCM 모드)
TRIG = 5  # GPIO5 → 초음파 송신
ECHO = 6  # GPIO6 → 초음파 수신

# 상수 정의
SOUND_SPEED = 34300  # 음속 (cm/s)
TRIGGER_PULSE = 0.00001  # 10µs 트리거 펄스
TIMEOUT = 0.1  # 타임아웃 (100ms)

def setup_gpio():
    """GPIO 초기 설정"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, False)
    print("🔧 GPIO 설정 완료")

def get_distance():
    """초음파 센서로 거리 측정"""
    try:
        # TRIG 신호 발생
        GPIO.output(TRIG, True)
        time.sleep(TRIGGER_PULSE)
        GPIO.output(TRIG, False)

        # ECHO 신호 대기 (타임아웃 적용)
        start_time = time.time()
        timeout_start = start_time
        
        # ECHO 신호 시작 대기
        while GPIO.input(ECHO) == 0:
            start_time = time.time()
            if start_time - timeout_start > TIMEOUT:
                return None  # 타임아웃 발생
        
        # ECHO 신호 종료 대기
        while GPIO.input(ECHO) == 1:
            end_time = time.time()
            if end_time - start_time > TIMEOUT:
                return None  # 타임아웃 발생

        # 거리 계산 (음속 * 시간 / 2)
        duration = end_time - start_time
        distance = (duration * SOUND_SPEED) / 2

        # 유효 범위 체크 (2cm ~ 400cm)
        if 2 <= distance <= 400:
            return round(distance, 1)
        return None
        
    except Exception as e:
        print(f"거리 측정 오류: {e}")
        return None

def test_sensor_basic():
    """기본 센서 테스트"""
    print("📡 기본 센서 테스트 시작...")
    
    for i in range(5):
        distance = get_distance()
        if distance is not None:
            print(f"측정 {i+1}: {distance} cm")
        else:
            print(f"측정 {i+1}: 실패")
        time.sleep(0.5)

def test_sensor_statistics():
    """통계 기반 센서 테스트"""
    print("\n📊 통계 기반 센서 테스트 시작...")
    
    measurements = []
    errors = 0
    
    for i in range(20):
        distance = get_distance()
        if distance is not None:
            measurements.append(distance)
            print(f"측정 {i+1:2d}: {distance:6.1f} cm")
        else:
            errors += 1
            print(f"측정 {i+1:2d}: 실패")
        time.sleep(0.2)
    
    # 통계 계산
    if measurements:
        min_dist = min(measurements)
        max_dist = max(measurements)
        avg_dist = statistics.mean(measurements)
        std_dist = statistics.stdev(measurements) if len(measurements) > 1 else 0
        success_rate = len(measurements) / (len(measurements) + errors) * 100
        
        print("\n" + "="*40)
        print("📈 측정 결과 통계")
        print("="*40)
        print(f"총 측정 횟수: {len(measurements) + errors}")
        print(f"성공 횟수:   {len(measurements)}")
        print(f"실패 횟수:   {errors}")
        print(f"성공률:     {success_rate:.1f}%")
        print(f"최소 거리:   {min_dist:.1f} cm")
        print(f"최대 거리:   {max_dist:.1f} cm")
        print(f"평균 거리:   {avg_dist:.1f} cm")
        print(f"표준편차:   {std_dist:.1f} cm")
        
        # 센서 상태 평가
        if success_rate >= 90:
            print("✅ 센서 상태: 우수")
        elif success_rate >= 70:
            print("⚠️ 센서 상태: 보통")
        else:
            print("❌ 센서 상태: 불량")
    else:
        print("❌ 모든 측정 실패")

def test_sensor_continuous():
    """연속 측정 테스트"""
    print("\n🔄 연속 측정 테스트 시작 (10초간)")
    print("Ctrl+C로 중지하세요...")
    
    start_time = time.time()
    count = 0
    
    try:
        while time.time() - start_time < 10:
            distance = get_distance()
            count += 1
            
            if distance is not None:
                # 거리에 따른 시각적 표시
                bar_length = int(distance / 10)  # 10cm당 1칸
                bar = "█" * min(bar_length, 40)
                print(f"{count:3d}: {distance:6.1f} cm |{bar}")
            else:
                print(f"{count:3d}: 측정 실패")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n측정 중지됨")
    
    print(f"총 {count}회 측정 완료")

def main():
    """메인 실행 함수"""
    print("🤖 패스파인더 초음파 센서 테스트")
    print("=" * 40)
    
    try:
        setup_gpio()
        
        # 1. 기본 테스트
        test_sensor_basic()
        
        # 2. 통계 테스트
        test_sensor_statistics()
        
        # 3. 연속 측정 테스트
        test_sensor_continuous()
        
    except KeyboardInterrupt:
        print("\n테스트 중단됨")
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        GPIO.cleanup()
        print("🧹 GPIO 정리 완료")

if __name__ == "__main__":
    main() 