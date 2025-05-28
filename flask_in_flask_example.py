#!/usr/bin/env python3
"""
Flask 안에서 다른 Flask 서버 실행하기 - subprocess 방식
메인 Flask 서버에서 opencv_test.py 같은 다른 Flask 앱을 제어
"""

from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit
import subprocess
import threading
import time
import os
import signal
import psutil
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'flask-in-flask-demo'
socketio = SocketIO(app, cors_allowed_origins="*")

# 실행 중인 Flask 서버들 관리
running_servers = {}

class FlaskServerManager:
    """다른 Flask 서버들을 관리하는 클래스"""
    
    @staticmethod
    def start_server(server_name, script_path, port):
        """새로운 Flask 서버 시작"""
        try:
            # 기존 서버가 있으면 중지
            if server_name in running_servers:
                FlaskServerManager.stop_server(server_name)
            
            # 스크립트 파일 존재 확인
            if not os.path.exists(script_path):
                return {'success': False, 'error': f'파일을 찾을 수 없습니다: {script_path}'}
            
            # 포트 사용 중인지 확인
            if FlaskServerManager.is_port_in_use(port):
                return {'success': False, 'error': f'포트 {port}가 이미 사용 중입니다'}
            
            # 새 Flask 서버 프로세스 시작
            process = subprocess.Popen(
                ['python3', script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(script_path) if os.path.dirname(script_path) else '.'
            )
            
            # 서버 정보 저장
            running_servers[server_name] = {
                'process': process,
                'script_path': script_path,
                'port': port,
                'start_time': datetime.now(),
                'pid': process.pid
            }
            
            # 서버 상태 모니터링 스레드 시작
            monitor_thread = threading.Thread(
                target=FlaskServerManager._monitor_server,
                args=(server_name, process),
                daemon=True
            )
            monitor_thread.start()
            
            # 잠시 대기 후 서버 상태 확인
            time.sleep(2)
            if process.poll() is None:  # 프로세스가 살아있으면
                socketio.emit('server_started', {
                    'server_name': server_name,
                    'port': port,
                    'pid': process.pid,
                    'url': f'http://localhost:{port}',
                    'message': f'✅ {server_name} 서버가 포트 {port}에서 시작되었습니다'
                })
                return {'success': True, 'pid': process.pid, 'port': port}
            else:
                # 프로세스가 죽었으면 오류 정보 수집
                stdout, stderr = process.communicate()
                error_msg = stderr if stderr else stdout
                return {'success': False, 'error': f'서버 시작 실패: {error_msg}'}
                
        except Exception as e:
            return {'success': False, 'error': f'서버 시작 오류: {str(e)}'}
    
    @staticmethod
    def stop_server(server_name):
        """Flask 서버 중지"""
        try:
            if server_name not in running_servers:
                return {'success': False, 'error': f'{server_name} 서버가 실행 중이 아닙니다'}
            
            server_info = running_servers[server_name]
            process = server_info['process']
            port = server_info['port']
            
            # 프로세스 종료
            if process.poll() is None:  # 프로세스가 살아있으면
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            
            # 서버 정보 삭제
            del running_servers[server_name]
            
            socketio.emit('server_stopped', {
                'server_name': server_name,
                'port': port,
                'message': f'⏹️ {server_name} 서버가 중지되었습니다'
            })
            
            return {'success': True, 'message': f'{server_name} 서버가 중지되었습니다'}
            
        except Exception as e:
            return {'success': False, 'error': f'서버 중지 오류: {str(e)}'}
    
    @staticmethod
    def _monitor_server(server_name, process):
        """서버 프로세스 모니터링"""
        try:
            while server_name in running_servers:
                if process.poll() is not None:  # 프로세스가 종료됨
                    stdout, stderr = process.communicate()
                    
                    socketio.emit('server_crashed', {
                        'server_name': server_name,
                        'exit_code': process.returncode,
                        'stdout': stdout,
                        'stderr': stderr,
                        'message': f'❌ {server_name} 서버가 예기치 않게 종료되었습니다'
                    })
                    
                    # 서버 정보 삭제
                    if server_name in running_servers:
                        del running_servers[server_name]
                    break
                
                time.sleep(1)
                
        except Exception as e:
            print(f"서버 모니터링 오류: {e}")
    
    @staticmethod
    def is_port_in_use(port):
        """포트 사용 여부 확인"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port:
                    return True
            return False
        except:
            return False
    
    @staticmethod
    def get_server_status():
        """모든 서버 상태 반환"""
        status = {}
        for name, info in running_servers.items():
            process = info['process']
            status[name] = {
                'running': process.poll() is None,
                'pid': info['pid'],
                'port': info['port'],
                'start_time': info['start_time'].isoformat(),
                'script_path': info['script_path']
            }
        return status

# HTML 템플릿
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Flask 서버 관리자</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #333; text-align: center; }
        .server-card { 
            background: white; 
            border-radius: 8px; 
            padding: 20px; 
            margin: 10px 0; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        }
        .server-controls { margin: 20px 0; }
        .btn { 
            padding: 10px 20px; 
            margin: 5px; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 14px;
        }
        .btn-start { background-color: #28a745; color: white; }
        .btn-stop { background-color: #dc3545; color: white; }
        .btn-refresh { background-color: #007bff; color: white; }
        .status { padding: 10px; border-radius: 4px; margin: 10px 0; }
        .status-running { background-color: #d4edda; color: #155724; }
        .status-stopped { background-color: #f8d7da; color: #721c24; }
        .log { 
            background-color: #f8f9fa; 
            border: 1px solid #dee2e6; 
            border-radius: 4px; 
            padding: 10px; 
            height: 200px; 
            overflow-y: auto; 
            font-family: monospace; 
            font-size: 12px;
        }
        input[type="text"], input[type="number"] { 
            padding: 8px; 
            border: 1px solid #ddd; 
            border-radius: 4px; 
            margin: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Flask 서버 관리자</h1>
        
        <!-- 새 서버 시작 -->
        <div class="server-card">
            <h3>새 Flask 서버 시작</h3>
            <div>
                <input type="text" id="serverName" placeholder="서버 이름" value="opencv_camera">
                <input type="text" id="scriptPath" placeholder="스크립트 경로" value="2.ComponentClass/_3.CameraClass/opencv_test.py">
                <input type="number" id="serverPort" placeholder="포트" value="5001">
                <button class="btn btn-start" onclick="startServer()">서버 시작</button>
            </div>
        </div>
        
        <!-- 서버 상태 -->
        <div class="server-card">
            <h3>실행 중인 서버들</h3>
            <button class="btn btn-refresh" onclick="refreshStatus()">상태 새로고침</button>
            <div id="serverStatus"></div>
        </div>
        
        <!-- 로그 -->
        <div class="server-card">
            <h3>실시간 로그</h3>
            <div id="log" class="log"></div>
            <button class="btn btn-refresh" onclick="clearLog()">로그 지우기</button>
        </div>
    </div>

    <script>
        const socket = io();
        
        function addLog(message) {
            const log = document.getElementById('log');
            const timestamp = new Date().toLocaleTimeString();
            log.innerHTML += `[${timestamp}] ${message}<br>`;
            log.scrollTop = log.scrollHeight;
        }
        
        function startServer() {
            const name = document.getElementById('serverName').value;
            const path = document.getElementById('scriptPath').value;
            const port = document.getElementById('serverPort').value;
            
            if (!name || !path || !port) {
                alert('모든 필드를 입력해주세요');
                return;
            }
            
            fetch('/start_server', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    server_name: name,
                    script_path: path,
                    port: parseInt(port)
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog(`✅ ${name} 서버 시작 요청 성공`);
                    refreshStatus();
                } else {
                    addLog(`❌ ${name} 서버 시작 실패: ${data.error}`);
                }
            });
        }
        
        function stopServer(serverName) {
            fetch('/stop_server', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({server_name: serverName})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog(`⏹️ ${serverName} 서버 중지 성공`);
                    refreshStatus();
                } else {
                    addLog(`❌ ${serverName} 서버 중지 실패: ${data.error}`);
                }
            });
        }
        
        function refreshStatus() {
            fetch('/server_status')
            .then(response => response.json())
            .then(data => {
                const statusDiv = document.getElementById('serverStatus');
                statusDiv.innerHTML = '';
                
                if (Object.keys(data).length === 0) {
                    statusDiv.innerHTML = '<p>실행 중인 서버가 없습니다</p>';
                    return;
                }
                
                for (const [name, info] of Object.entries(data)) {
                    const statusClass = info.running ? 'status-running' : 'status-stopped';
                    const statusText = info.running ? '실행 중' : '중지됨';
                    
                    statusDiv.innerHTML += `
                        <div class="status ${statusClass}">
                            <strong>${name}</strong> - ${statusText} 
                            (PID: ${info.pid}, 포트: ${info.port})
                            <br>스크립트: ${info.script_path}
                            <br>시작 시간: ${new Date(info.start_time).toLocaleString()}
                            ${info.running ? `
                                <br><a href="http://localhost:${info.port}" target="_blank">서버 열기</a>
                                <button class="btn btn-stop" onclick="stopServer('${name}')">중지</button>
                            ` : ''}
                        </div>
                    `;
                }
            });
        }
        
        function clearLog() {
            document.getElementById('log').innerHTML = '';
        }
        
        // Socket.IO 이벤트 리스너
        socket.on('server_started', function(data) {
            addLog(`🚀 ${data.message}`);
            refreshStatus();
        });
        
        socket.on('server_stopped', function(data) {
            addLog(`⏹️ ${data.message}`);
            refreshStatus();
        });
        
        socket.on('server_crashed', function(data) {
            addLog(`💥 ${data.message} (종료 코드: ${data.exit_code})`);
            if (data.stderr) {
                addLog(`오류: ${data.stderr}`);
            }
            refreshStatus();
        });
        
        // 페이지 로드 시 상태 새로고침
        window.onload = function() {
            refreshStatus();
            addLog('Flask 서버 관리자가 시작되었습니다');
        };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/start_server', methods=['POST'])
def start_server():
    data = request.get_json()
    server_name = data.get('server_name')
    script_path = data.get('script_path')
    port = data.get('port')
    
    result = FlaskServerManager.start_server(server_name, script_path, port)
    return jsonify(result)

@app.route('/stop_server', methods=['POST'])
def stop_server():
    data = request.get_json()
    server_name = data.get('server_name')
    
    result = FlaskServerManager.stop_server(server_name)
    return jsonify(result)

@app.route('/server_status')
def server_status():
    return jsonify(FlaskServerManager.get_server_status())

@socketio.on('connect')
def handle_connect():
    print(f"클라이언트 연결됨: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"클라이언트 연결 해제됨: {request.sid}")

if __name__ == '__main__':
    print("🚀 Flask 서버 관리자 시작!")
    print("브라우저에서 http://localhost:5000 으로 접속하세요")
    print("다른 Flask 서버들을 시작/중지할 수 있습니다")
    
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 서버 종료 중...")
        # 모든 실행 중인 서버 중지
        for server_name in list(running_servers.keys()):
            FlaskServerManager.stop_server(server_name)
        print("✅ 모든 서버가 정리되었습니다") 