#!/usr/bin/env python3
"""
패스파인더 통합 시스템 테스트 스크립트
"""

import sys
import time

# 모듈 가용성 테스트
print("🔍 모듈 가용성 테스트")
print("-" * 40)

try:
    import flask
    print(f"✅ Flask: {flask.__version__}")
except ImportError as e:
    print(f"❌ Flask: {e}")

try:
    import flask_socketio
    print(f"✅ Flask-SocketIO: {flask_socketio.__version__}")
except ImportError as e:
    print(f"❌ Flask-SocketIO: {e}")

try:
    import RPi.GPIO as GPIO
    print("✅ RPi.GPIO: 사용 가능")
    GPIO_AVAILABLE = True
except ImportError as e:
    print(f"❌ RPi.GPIO: {e}")
    GPIO_AVAILABLE = False

try:
    import cv2
    print(f"✅ OpenCV: {cv2.__version__}")
except ImportError as e:
    print(f"❌ OpenCV: {e}")

try:
    from picamera2 import Picamera2
    print("✅ Picamera2: 사용 가능")
except ImportError as e:
    print(f"❌ Picamera2: {e}")

print("\n🧪 기본 기능 테스트")
print("-" * 40)

# GPIO 테스트
if GPIO_AVAILABLE:
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(18, GPIO.OUT)  # 테스트용 핀
        GPIO.output(18, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(18, GPIO.LOW)
        GPIO.cleanup()
        print("✅ GPIO 기본 동작: 정상")
    except Exception as e:
        print(f"❌ GPIO 기본 동작: {e}")
else:
    print("⚠️ GPIO: 시뮬레이션 모드")

# 네트워크 테스트
try:
    import subprocess
    ip = subprocess.check_output(['hostname', '-I'], shell=False).decode().split()[0]
    print(f"✅ 네트워크: {ip}")
except Exception as e:
    print(f"❌ 네트워크: {e}")

print("\n📋 시스템 정보")
print("-" * 40)
print(f"Python 버전: {sys.version}")
print(f"플랫폼: {sys.platform}")

print("\n🚀 통합 시스템 시작 준비 완료!")
print("IntegratedFlask.py를 실행하세요.") 