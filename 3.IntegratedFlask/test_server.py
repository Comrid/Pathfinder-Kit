#!/usr/bin/env python3
"""
서버 연결 테스트 스크립트
"""

import requests
import time
import socketio

def test_http_connection():
    """HTTP 연결 테스트"""
    try:
        print("🔍 HTTP 연결 테스트 중...")
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

def test_socketio_connection():
    """SocketIO 연결 테스트"""
    try:
        print("🔍 SocketIO 연결 테스트 중...")
        sio = socketio.SimpleClient()
        
        # 연결 시도
        sio.connect('http://localhost:5000', wait_timeout=10)
        print("✅ SocketIO 연결 성공")
        
        # 시스템 상태 이벤트 대기
        event = sio.receive(timeout=5)
        print(f"📡 이벤트 수신: {event}")
        
        # 테스트 명령 전송
        sio.emit('motor_command', {'command': 'stop', 'speed': 0})
        print("📤 테스트 명령 전송")
        
        # 응답 대기
        try:
            response = sio.receive(timeout=3)
            print(f"📥 응답 수신: {response}")
        except:
            print("⚠️ 응답 타임아웃 (정상일 수 있음)")
        
        sio.disconnect()
        print("✅ SocketIO 테스트 완료")
        return True
        
    except Exception as e:
        print(f"❌ SocketIO 연결 오류: {e}")
        return False

def main():
    print("🧪 패스파인더 서버 연결 테스트")
    print("=" * 50)
    
    # HTTP 테스트
    http_ok = test_http_connection()
    time.sleep(1)
    
    # SocketIO 테스트
    socketio_ok = test_socketio_connection()
    
    print("=" * 50)
    if http_ok and socketio_ok:
        print("✅ 모든 테스트 통과!")
        print("🌐 브라우저에서 http://localhost:5000 접속 가능")
    else:
        print("❌ 일부 테스트 실패")
        print("🔧 서버가 실행 중인지 확인하세요: python app.py")

if __name__ == '__main__':
    main() 