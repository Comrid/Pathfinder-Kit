#!/usr/bin/env python3
"""
Pathfinder Ultrasonic Sensor Server Test
서버 동작 테스트 스크립트
"""

import requests
import time
import socketio

def test_http_connection():
    """HTTP 연결 테스트"""
    try:
        response = requests.get('http://localhost:5000', timeout=5)
        if response.status_code == 200:
            print("✅ HTTP 연결 성공")
            return True
        else:
            print(f"❌ HTTP 연결 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ HTTP 연결 오류: {e}")
        return False

def test_websocket_connection():
    """WebSocket 연결 테스트"""
    try:
        sio = socketio.Client()
        
        @sio.event
        def connect():
            print("✅ WebSocket 연결 성공")
        
        @sio.event
        def disconnect():
            print("🔌 WebSocket 연결 해제")
        
        @sio.event
        def measurement_data(data):
            print(f"📊 측정 데이터 수신: {data['distance']} cm")
        
        @sio.event
        def debug_message(data):
            print(f"🐛 디버그: {data['message']}")
        
        sio.connect('http://localhost:5000')
        
        # 측정 시작 테스트
        print("🚀 측정 시작 테스트...")
        sio.emit('start_measurement')
        time.sleep(3)
        
        # 측정 중지 테스트
        print("⏹️ 측정 중지 테스트...")
        sio.emit('stop_measurement')
        time.sleep(1)
        
        # 센서 테스트
        print("🔧 센서 테스트...")
        sio.emit('test_sensor')
        time.sleep(2)
        
        sio.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ WebSocket 연결 오류: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🧪 패스파인더 초음파 센서 서버 테스트")
    print("=" * 40)
    
    # HTTP 연결 테스트
    print("1. HTTP 연결 테스트")
    http_ok = test_http_connection()
    
    if http_ok:
        print("\n2. WebSocket 연결 테스트")
        websocket_ok = test_websocket_connection()
        
        if websocket_ok:
            print("\n✅ 모든 테스트 통과!")
        else:
            print("\n❌ WebSocket 테스트 실패")
    else:
        print("\n❌ HTTP 연결 실패로 추가 테스트 불가")

if __name__ == "__main__":
    main() 