#!/usr/bin/env python3
"""
Flask 안에서 Threading으로 다른 Flask 앱 실행하기
같은 프로세스 내에서 여러 Flask 앱을 다른 포트에서 실행
"""

from flask import Flask, render_template_string, jsonify
import threading
import time
from datetime import datetime
import cv2
import numpy as np

# 메인 Flask 앱
main_app = Flask(__name__)

# 카메라 Flask 앱 (opencv_test.py와 유사)
camera_app = Flask(__name__)

# 센서 Flask 앱
sensor_app = Flask(__name__)

# 전역 변수
running_apps = {}
app_threads = {}

class MultiFlaskManager:
    """여러 Flask 앱을 관리하는 클래스"""
    
    @staticmethod
    def start_camera_app(port=5001):
        """카메라 앱 시작"""
        try:
            @camera_app.route('/')
            def camera_index():
                return """
                <!DOCTYPE html>
                <html>
                <head><title>카메라 서버</title></head>
                <body>
                    <h1>🎥 카메라 서버</h1>
                    <p>포트 {port}에서 실행 중</p>
                    <img src="/video_feed" width="640" height="480">
                </body>
                </html>
                """.format(port=port)
            
            @camera_app.route('/video_feed')
            def video_feed():
                from flask import Response
                
                def generate_frames():
                    # 가상 카메라 데이터 생성
                    while True:
                        # 가상 프레임 생성 (실제로는 카메라에서 읽어옴)
                        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                        
                        # 현재 시간 표시
                        cv2.putText(frame, datetime.now().strftime("%H:%M:%S"), 
                                  (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                        
                        # JPEG 인코딩
                        ret, buffer = cv2.imencode('.jpg', frame)
                        frame_bytes = buffer.tobytes()
                        
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                        
                        time.sleep(0.1)  # 10 FPS
                
                return Response(generate_frames(), 
                              mimetype='multipart/x-mixed-replace; boundary=frame')
            
            # 별도 스레드에서 카메라 앱 실행
            def run_camera():
                camera_app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
            
            camera_thread = threading.Thread(target=run_camera, daemon=True)
            camera_thread.start()
            
            running_apps['camera'] = {
                'port': port,
                'status': 'running',
                'start_time': datetime.now(),
                'thread': camera_thread
            }
            
            return {'success': True, 'port': port, 'message': f'카메라 서버가 포트 {port}에서 시작되었습니다'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def start_sensor_app(port=5002):
        """센서 앱 시작"""
        try:
            @sensor_app.route('/')
            def sensor_index():
                return """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>센서 서버</title>
                    <script>
                        function updateSensors() {
                            fetch('/sensor_data')
                            .then(response => response.json())
                            .then(data => {
                                document.getElementById('distance').textContent = data.distance;
                                document.getElementById('temperature').textContent = data.temperature;
                                document.getElementById('timestamp').textContent = data.timestamp;
                            });
                        }
                        setInterval(updateSensors, 1000);
                        window.onload = updateSensors;
                    </script>
                </head>
                <body>
                    <h1>📡 센서 서버</h1>
                    <p>포트 {port}에서 실행 중</p>
                    <div>
                        <h3>실시간 센서 데이터</h3>
                        <p>거리: <span id="distance">-</span> cm</p>
                        <p>온도: <span id="temperature">-</span> °C</p>
                        <p>업데이트: <span id="timestamp">-</span></p>
                    </div>
                </body>
                </html>
                """.format(port=port)
            
            @sensor_app.route('/sensor_data')
            def sensor_data():
                # 가상 센서 데이터 생성
                import random
                return jsonify({
                    'distance': round(random.uniform(5, 200), 1),
                    'temperature': round(random.uniform(20, 35), 1),
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                })
            
            # 별도 스레드에서 센서 앱 실행
            def run_sensor():
                sensor_app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
            
            sensor_thread = threading.Thread(target=run_sensor, daemon=True)
            sensor_thread.start()
            
            running_apps['sensor'] = {
                'port': port,
                'status': 'running',
                'start_time': datetime.now(),
                'thread': sensor_thread
            }
            
            return {'success': True, 'port': port, 'message': f'센서 서버가 포트 {port}에서 시작되었습니다'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_app_status():
        """앱 상태 반환"""
        status = {}
        for name, info in running_apps.items():
            status[name] = {
                'port': info['port'],
                'status': info['status'],
                'start_time': info['start_time'].isoformat(),
                'running': info['thread'].is_alive() if info['thread'] else False
            }
        return status

# 메인 앱 라우트
@main_app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flask 멀티 앱 관리자</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .app-card { 
                border: 1px solid #ddd; 
                border-radius: 8px; 
                padding: 20px; 
                margin: 10px 0; 
                background-color: #f9f9f9;
            }
            .btn { 
                padding: 10px 20px; 
                margin: 5px; 
                border: none; 
                border-radius: 4px; 
                cursor: pointer; 
            }
            .btn-start { background-color: #28a745; color: white; }
            .btn-stop { background-color: #dc3545; color: white; }
            .btn-refresh { background-color: #007bff; color: white; }
            .status { margin: 10px 0; padding: 10px; border-radius: 4px; }
            .status-running { background-color: #d4edda; color: #155724; }
            .status-stopped { background-color: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <h1>🚀 Flask 멀티 앱 관리자 (Threading 방식)</h1>
        
        <div class="app-card">
            <h3>🎥 카메라 앱</h3>
            <p>OpenCV 기반 실시간 카메라 스트리밍</p>
            <button class="btn btn-start" onclick="startApp('camera')">카메라 앱 시작</button>
            <a href="http://localhost:5001" target="_blank">카메라 앱 열기</a>
        </div>
        
        <div class="app-card">
            <h3>📡 센서 앱</h3>
            <p>실시간 센서 데이터 모니터링</p>
            <button class="btn btn-start" onclick="startApp('sensor')">센서 앱 시작</button>
            <a href="http://localhost:5002" target="_blank">센서 앱 열기</a>
        </div>
        
        <div class="app-card">
            <h3>📊 앱 상태</h3>
            <button class="btn btn-refresh" onclick="refreshStatus()">상태 새로고침</button>
            <div id="appStatus"></div>
        </div>
        
        <script>
            function startApp(appName) {
                fetch(`/start_${appName}`, {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(`✅ ${data.message}`);
                        refreshStatus();
                    } else {
                        alert(`❌ 오류: ${data.error}`);
                    }
                });
            }
            
            function refreshStatus() {
                fetch('/app_status')
                .then(response => response.json())
                .then(data => {
                    const statusDiv = document.getElementById('appStatus');
                    statusDiv.innerHTML = '';
                    
                    if (Object.keys(data).length === 0) {
                        statusDiv.innerHTML = '<p>실행 중인 앱이 없습니다</p>';
                        return;
                    }
                    
                    for (const [name, info] of Object.entries(data)) {
                        const statusClass = info.running ? 'status-running' : 'status-stopped';
                        const statusText = info.running ? '실행 중' : '중지됨';
                        
                        statusDiv.innerHTML += `
                            <div class="status ${statusClass}">
                                <strong>${name}</strong> - ${statusText} (포트: ${info.port})
                                <br>시작 시간: ${new Date(info.start_time).toLocaleString()}
                            </div>
                        `;
                    }
                });
            }
            
            // 페이지 로드 시 상태 확인
            window.onload = refreshStatus;
        </script>
    </body>
    </html>
    """)

@main_app.route('/start_camera', methods=['POST'])
def start_camera():
    result = MultiFlaskManager.start_camera_app()
    return jsonify(result)

@main_app.route('/start_sensor', methods=['POST'])
def start_sensor():
    result = MultiFlaskManager.start_sensor_app()
    return jsonify(result)

@main_app.route('/app_status')
def app_status():
    return jsonify(MultiFlaskManager.get_app_status())

if __name__ == '__main__':
    print("🚀 Flask 멀티 앱 관리자 시작!")
    print("메인 서버: http://localhost:5000")
    print("카메라 앱: http://localhost:5001 (시작 후)")
    print("센서 앱: http://localhost:5002 (시작 후)")
    
    try:
        main_app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 모든 앱 종료 중...")
        print("✅ 정리 완료!") 