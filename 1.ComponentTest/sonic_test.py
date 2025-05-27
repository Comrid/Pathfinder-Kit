import RPi.GPIO as GPIO
import time

# 핀 번호 설정 (BCM 모드)
TRIG = 5  # GPIO5 → 초음파 송신
ECHO = 6  # GPIO6 → 초음파 수신

# 상수 정의
SOUND_SPEED = 34300  # 음속 (cm/s)
TRIGGER_PULSE = 0.00001  # 10µs 트리거 펄스
MEASUREMENT_INTERVAL = 0.1  # 측정 간격
TIMEOUT = 0.1  # 타임아웃 (100ms)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)  # 경고 메시지 비활성화
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# 초기 상태 설정
GPIO.output(TRIG, False)

def get_distance():
    """초음파 센서로 거리 측정"""
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

def main():
    """메인 실행 함수"""
    print("🤖 패스파인더 초음파 센서 테스트 시작!")
    print("📡 HC-SR04 초음파 센서로 거리를 측정합니다...")
    print("💡 Ctrl+C로 종료하세요")
    print("-" * 40)
    
    try:
        while True:
            distance = get_distance()
            if distance is not None:
                print(f"거리: {distance} cm")
            else:
                print("측정 실패 (범위 초과 또는 오류)")
            time.sleep(MEASUREMENT_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n측정 종료")
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()