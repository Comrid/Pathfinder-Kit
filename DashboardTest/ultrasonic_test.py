#!/usr/bin/env python3
"""
초음파 센서 시뮬레이션 - WebSocket 스트리밍 테스트용
실제 GPIO 없이도 동작하는 시뮬레이션 코드
"""

import time
import random
import sys

def simulate_ultrasonic_sensor():
    """초음파 센서 거리 측정 시뮬레이션"""
    print("🔄 초음파 센서 시뮬레이션 시작")
    print("📡 실시간 거리 측정 중... (중지 버튼으로 종료)")
    print("-" * 50)
    
    try:
        measurement_count = 0
        
        while True:
            # 랜덤한 거리 값 생성 (5cm ~ 200cm)
            distance = round(random.uniform(5.0, 200.0), 2)
            
            # 측정 횟수 증가
            measurement_count += 1
            
            # 거리에 따른 상태 표시
            if distance < 10:
                status = "🔴 매우 가까움"
            elif distance < 30:
                status = "🟡 가까움"
            elif distance < 100:
                status = "🟢 보통"
            else:
                status = "🔵 멀음"
            
            # 실시간 출력
            print(f"[{measurement_count:04d}] 거리: {distance:6.2f}cm | {status}")
            
            # 특별한 이벤트 시뮬레이션
            if measurement_count % 20 == 0:
                print(f"📊 {measurement_count}회 측정 완료!")
            
            if measurement_count % 50 == 0:
                print("🔄 센서 캘리브레이션 중...")
                time.sleep(0.5)
                print("✅ 캘리브레이션 완료")
            
            # 0.1초 대기 (실제 센서와 유사한 주기)
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("⏹️ 사용자에 의해 중지됨")
        print(f"📊 총 {measurement_count}회 측정 완료")
        print("👋 프로그램 종료")

def test_quick_output():
    """빠른 출력 테스트"""
    print("⚡ 빠른 출력 테스트 시작")
    
    for i in range(10):
        print(f"출력 {i+1}/10: 현재 시간 {time.strftime('%H:%M:%S')}")
        time.sleep(0.05)  # 50ms 간격
    
    print("✅ 빠른 출력 테스트 완료")

if __name__ == "__main__":
    print("🚀 WebSocket 스트리밍 테스트 프로그램")
    print("=" * 50)
    
    # 초음파 센서 시뮬레이션 실행
    simulate_ultrasonic_sensor() 