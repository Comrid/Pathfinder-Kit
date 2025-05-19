import RPi.GPIO as GPIO
import time

# 핀 번호 설정 (BCM 모드)
TRIG = 5  # GPIO17 → 초음파 송신
ECHO = 6  # GPIO18 → 초음파 수신

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def get_distance():
    # TRIG 신호 짧게 발생
    GPIO.output(TRIG, True)
    time.sleep(0.00001)  # 10µs
    GPIO.output(TRIG, False)

    # ECHO 신호의 시작 시간
    while GPIO.input(ECHO) == 0:
        start_time = time.time()
    
    # ECHO 신호의 끝 시간
    while GPIO.input(ECHO) == 1:
        end_time = time.time()

    # 거리 계산
    duration = end_time - start_time
    distance = (duration * 34300) / 2  # cm 단위

    return round(distance, 2)

try:
    while True:
        dist = get_distance()
        print("거리: {} cm".format(dist))
        time.sleep(0.1) # 측정 주기

# Ctrl + C 로 종료 시 실행하는 부분
except KeyboardInterrupt:
    print("측정 종료")

finally:
    GPIO.cleanup() # GPIO 사용 종료