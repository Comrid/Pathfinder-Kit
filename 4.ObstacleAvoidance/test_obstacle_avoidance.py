#!/usr/bin/env python3
"""
패스파인더 장애물 회피 시스템 테스트 스크립트
"""

import sys
import time
import requests
import json

def test_modules():
    """모듈 가용성 테스트"""
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
    
    return GPIO_AVAILABLE

def test_gpio_basic(gpio_available):
    """GPIO 기본 테스트"""
    if not gpio_available:
        print("⚠️ GPIO: 시뮬레이션 모드")
        return
    
    print("\n🧪 GPIO 기본 테스트")
    print("-" * 40)
    
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        
        # 테스트용 핀 설정
        test_pin = 18
        GPIO.setup(test_pin, GPIO.OUT)
        GPIO.output(test_pin, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(test_pin, GPIO.LOW)
        GPIO.cleanup()
        
        print("✅ GPIO 기본 동작: 정상")
    except Exception as e:
        print(f"❌ GPIO 기본 동작: {e}")

def test_distance_sensor_simulation():
    """거리 센서 시뮬레이션 테스트"""
    print("\n📡 거리 센서 시뮬레이션 테스트")
    print("-" * 40)
    
    import random
    
    for i in range(5):
        # 시뮬레이션 거리 생성
        if random.random() < 0.2:  # 20% 확률로 장애물
            distance = round(random.uniform(5.0, 15.0), 1)
            status = "🚧 장애물 감지"
        else:
            distance = round(random.uniform(30.0, 100.0), 1)
            status = "✅ 안전"
        
        print(f"측정 {i+1}: {distance}cm - {status}")
        time.sleep(0.5)

def test_motor_simulation():
    """모터 제어 시뮬레이션 테스트"""
    print("\n🚗 모터 제어 시뮬레이션 테스트")
    print("-" * 40)
    
    commands = [
        ("전진", "move_forward"),
        ("좌회전", "turn_left"),
        ("우회전", "turn_right"),
        ("후진", "move_backward"),
        ("정지", "stop_motors")
    ]
    
    for name, command in commands:
        print(f"🎮 시뮬레이션: {name}")
        time.sleep(0.5)

def test_api_endpoints(base_url="http://localhost:5000"):
    """API 엔드포인트 테스트"""
    print(f"\n🌐 API 엔드포인트 테스트 ({base_url})")
    print("-" * 40)
    
    endpoints = [
        ("/api/status", "상태 조회"),
        ("/api/settings", "설정 조회"),
        ("/api/logs", "로그 조회")
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {description}: 정상")
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {description}: 연결 실패 - {e}")

def test_obstacle_avoidance_logic():
    """장애물 회피 로직 테스트"""
    print("\n🧠 장애물 회피 로직 테스트")
    print("-" * 40)
    
    # 거리 임계값
    OBSTACLE_DISTANCE = 20
    SAFE_DISTANCE = 30
    CRITICAL_DISTANCE = 10
    
    test_distances = [5, 15, 25, 35, 50]
    
    for distance in test_distances:
        if distance <= CRITICAL_DISTANCE:
            action = "🚨 위험! 후진 + 회전"
        elif distance <= OBSTACLE_DISTANCE:
            action = "🚧 장애물 감지! 회전"
        elif distance <= SAFE_DISTANCE:
            action = "⚠️ 주의! 저속 전진"
        else:
            action = "✅ 안전! 정상 전진"
        
        print(f"거리 {distance}cm → {action}")

def test_web_interface():
    """웹 인터페이스 기본 테스트"""
    print("\n🖥️ 웹 인터페이스 테스트")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code == 200:
            print("✅ 메인 페이지: 정상")
            
            # HTML 내용 간단 검증
            if "패스파인더 장애물 회피 시스템" in response.text:
                print("✅ 페이지 내용: 정상")
            else:
                print("❌ 페이지 내용: 비정상")
        else:
            print(f"❌ 메인 페이지: HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 웹 서버: 연결 실패 - {e}")

def run_comprehensive_test():
    """종합 테스트 실행"""
    print("🚧 패스파인더 장애물 회피 시스템 테스트")
    print("=" * 60)
    
    # 1. 모듈 테스트
    gpio_available = test_modules()
    
    # 2. GPIO 테스트
    test_gpio_basic(gpio_available)
    
    # 3. 센서 시뮬레이션 테스트
    test_distance_sensor_simulation()
    
    # 4. 모터 시뮬레이션 테스트
    test_motor_simulation()
    
    # 5. 로직 테스트
    test_obstacle_avoidance_logic()
    
    # 6. 웹 인터페이스 테스트 (서버가 실행 중인 경우)
    test_web_interface()
    
    # 7. API 테스트 (서버가 실행 중인 경우)
    test_api_endpoints()
    
    print("\n" + "=" * 60)
    print("🎯 테스트 완료!")
    print("\n📋 다음 단계:")
    print("1. python app.py 실행")
    print("2. 브라우저에서 http://라즈베리파이IP:5000 접속")
    print("3. 🚀 시작 버튼으로 장애물 회피 시작")
    print("4. 실시간 로그와 차트로 동작 확인")

def test_algorithm_scenarios():
    """다양한 시나리오 테스트"""
    print("\n🎭 시나리오 테스트")
    print("-" * 40)
    
    scenarios = [
        {
            "name": "정상 주행",
            "distances": [50, 45, 40, 35, 32],
            "expected": "전진 유지"
        },
        {
            "name": "장애물 접근",
            "distances": [30, 25, 20, 15, 10],
            "expected": "점진적 감속 → 회전"
        },
        {
            "name": "급작스런 장애물",
            "distances": [50, 45, 8, 5, 3],
            "expected": "즉시 후진 + 회전"
        },
        {
            "name": "좁은 통로",
            "distances": [25, 22, 18, 15, 12],
            "expected": "저속 주행 → 회전"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📖 시나리오: {scenario['name']}")
        print(f"예상 결과: {scenario['expected']}")
        
        for i, distance in enumerate(scenario['distances']):
            if distance <= 10:
                action = "후진+회전"
            elif distance <= 20:
                action = "회전"
            elif distance <= 30:
                action = "저속전진"
            else:
                action = "정상전진"
            
            print(f"  단계 {i+1}: {distance}cm → {action}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--scenarios":
        test_algorithm_scenarios()
    else:
        run_comprehensive_test() 