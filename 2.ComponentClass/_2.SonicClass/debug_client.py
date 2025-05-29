#!/usr/bin/env python3
"""
Pathfinder Ultrasonic Sensor Debug Client
실시간 데이터 수신 테스트 클라이언트
"""

import socketio
import time
import threading

class UltrasonicDebugClient:
    def __init__(self, server_url='http://localhost:5000'):
        self.server_url = server_url
        self.sio = socketio.Client()
        self.data_count = 0
        self.last_data_time = 0
        
        # 이벤트 핸들러 등록
        self.setup_events()
    
    def setup_events(self):
        """WebSocket 이벤트 핸들러 설정"""
        
        @self.sio.event
        def connect():
            print("✅ 서버에 연결됨")
            print("📋 현재 상태 요청 중...")
            self.sio.emit('get_status')
        
        @self.sio.event
        def disconnect():
            print("🔌 서버 연결 해제됨")
        
        @self.sio.event
        def connect_error(data):
            print(f"❌ 연결 오류: {data}")
        
        @self.sio.event
        def measurement_status(data):
            status = "측정 중" if data['is_measuring'] else "대기 중"
            print(f"📊 측정 상태: {status}")
        
        @self.sio.event
        def measurement_data(data):
            self.data_count += 1
            current_time = time.time()
            interval = current_time - self.last_data_time if self.last_data_time > 0 else 0
            
            print(f"📏 데이터 #{self.data_count}: {data['distance']} cm (간격: {interval:.2f}초)")
            print(f"   📈 통계: 최소={data['stats']['min_distance']}, 최대={data['stats']['max_distance']}, 평균={data['stats']['avg_distance']}")
            print(f"   📊 차트 데이터: {len(data['chart_data'])}개")
            
            self.last_data_time = current_time
        
        @self.sio.event
        def debug_message(data):
            print(f"🐛 서버 디버그: {data['message']}")
        
        @self.sio.event
        def test_result(data):
            print(f"🧪 테스트 결과: {data['results']}")
            print(f"   성공률: {data['success_rate']:.1f}%, 평균: {data['avg_distance']} cm")
        
        @self.sio.event
        def error_message(data):
            print(f"❌ 서버 오류: {data['message']}")
    
    def connect(self):
        """서버에 연결"""
        try:
            print(f"🔗 서버 연결 시도: {self.server_url}")
            self.sio.connect(self.server_url)
            return True
        except Exception as e:
            print(f"❌ 연결 실패: {e}")
            return False
    
    def start_measurement(self):
        """측정 시작"""
        print("🚀 측정 시작 요청...")
        self.sio.emit('start_measurement')
    
    def stop_measurement(self):
        """측정 중지"""
        print("⏹️ 측정 중지 요청...")
        self.sio.emit('stop_measurement')
    
    def test_sensor(self):
        """센서 테스트"""
        print("🔧 센서 테스트 요청...")
        self.sio.emit('test_sensor')
    
    def clear_data(self):
        """데이터 초기화"""
        print("🧹 데이터 초기화 요청...")
        self.sio.emit('clear_data')
    
    def disconnect(self):
        """연결 해제"""
        self.sio.disconnect()
        print("🔌 연결 해제됨")

def main():
    """메인 테스트 함수"""
    print("🧪 패스파인더 초음파 센서 디버그 클라이언트")
    print("=" * 50)
    
    client = UltrasonicDebugClient()
    
    if not client.connect():
        return
    
    try:
        # 메뉴 루프
        while True:
            print("\n" + "="*30)
            print("📋 명령어 메뉴:")
            print("1. 측정 시작 (start)")
            print("2. 측정 중지 (stop)")
            print("3. 센서 테스트 (test)")
            print("4. 데이터 초기화 (clear)")
            print("5. 상태 확인 (status)")
            print("6. 종료 (quit)")
            print("="*30)
            
            command = input("명령어 입력: ").strip().lower()
            
            if command in ['1', 'start']:
                client.start_measurement()
            elif command in ['2', 'stop']:
                client.stop_measurement()
            elif command in ['3', 'test']:
                client.test_sensor()
            elif command in ['4', 'clear']:
                client.clear_data()
            elif command in ['5', 'status']:
                client.sio.emit('get_status')
            elif command in ['6', 'quit', 'exit']:
                break
            else:
                print("❌ 잘못된 명령어입니다.")
            
            time.sleep(0.5)  # 명령어 간 간격
    
    except KeyboardInterrupt:
        print("\n⏹️ 사용자 중단")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main() 