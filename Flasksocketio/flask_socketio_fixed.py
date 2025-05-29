#!/usr/bin/env python3
"""
Flask-SocketIO 실시간 코드 실행기 v2
무한루프 코드 실시간 실행 및 제어 지원 - WebSocket 완전 지원
"""

import eventlet
eventlet.monkey_patch()  # eventlet으로 WebSocket 완전 지원

from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit
import sys
import io
import secrets
import threading
import time
import queue
import subprocess
import os
import tempfile
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)

# Flask-SocketIO 설정 (WebSocket 완전 지원)
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='eventlet',  # eventlet으로 WebSocket 완전 지원
    logger=False,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25,
    # WebSocket 우선 설정
    transports=['websocket', 'polling'],  # WebSocket 우선
    allow_upgrades=True,  # WebSocket 업그레이드 허용
    # WebSocket 최적화
    websocket_timeout=60,
    max_http_buffer_size=1024 * 1024  # 1MB 버퍼
)

# 전역 변수
running_processes = {}  # 실행 중인 프로세스들
execution_threads = {}  # 실행 스레드들

class RealTimeExecutor:
    """실시간 코드 실행 관리 클래스"""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.process = None
        self.is_running = False
        self.temp_file = None
        
    def execute_code(self, code):
        """코드를 별도 프로세스에서 실시간 실행"""
        try:
            # 임시 파일 생성
            self.temp_file = tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.py', 
                delete=False,
                encoding='utf-8'
            )
            self.temp_file.write(code)
            self.temp_file.close()
            
            # Python 프로세스 시작
            self.process = subprocess.Popen(
                [sys.executable, '-u', self.temp_file.name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=0,  # 실시간 출력을 위해 버퍼링 비활성화
                universal_newlines=True
            )
            
            self.is_running = True
            
            # 실시간 출력 모니터링 스레드 시작
            monitor_thread = threading.Thread(
                target=self._monitor_output,
                daemon=True
            )
            monitor_thread.start()
            
            return True
            
        except Exception as e:
            socketio.emit('execution_error', {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
            return False
    
    def _monitor_output(self):
        """프로세스 출력을 실시간으로 모니터링"""
        try:
            while self.is_running and self.process and self.process.poll() is None:
                try:
                    # 실시간 출력 읽기
                    line = self.process.stdout.readline()
                    if line:
                        socketio.emit('realtime_output', {
                            'output': line.rstrip('\n\r'),
                            'timestamp': datetime.now().isoformat()
                        }, room=self.session_id)
                    else:
                        time.sleep(0.01)  # CPU 사용량 조절
                        
                except Exception as e:
                    socketio.emit('execution_error', {
                        'error': f'출력 읽기 오류: {str(e)}',
                        'timestamp': datetime.now().isoformat()
                    }, room=self.session_id)
                    break
            
            # 프로세스 종료 처리
            if self.process:
                exit_code = self.process.poll()
                if exit_code is not None:
                    socketio.emit('execution_finished', {
                        'exit_code': exit_code,
                        'message': f'프로세스 종료됨 (코드: {exit_code})',
                        'timestamp': datetime.now().isoformat()
                    }, room=self.session_id)
                    
        except Exception as e:
            socketio.emit('execution_error', {
                'error': f'모니터링 오류: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
        finally:
            self.cleanup()
    
    def stop_execution(self):
        """실행 중지"""
        try:
            self.is_running = False
            
            if self.process and self.process.poll() is None:
                # 프로세스 종료 시도
                self.process.terminate()
                
                # 3초 대기 후 강제 종료
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
                
                socketio.emit('execution_stopped', {
                    'message': '실행이 중지되었습니다',
                    'timestamp': datetime.now().isoformat()
                }, room=self.session_id)
                
            return True
            
        except Exception as e:
            socketio.emit('execution_error', {
                'error': f'중지 오류: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
            return False
    
    def cleanup(self):
        """리소스 정리"""
        try:
            if self.temp_file and os.path.exists(self.temp_file.name):
                os.unlink(self.temp_file.name)
        except:
            pass

@app.route('/')
def index():
    """메인 페이지"""
    return render_template_string(HTML_TEMPLATE)

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결 시"""
    session_id = request.sid
    print(f"🔗 클라이언트 연결됨: {session_id}")
    emit('status', {
        'type': 'connected',
        'message': '서버에 연결되었습니다!',
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제 시"""
    session_id = request.sid
    print(f"🔌 클라이언트 연결 해제됨: {session_id}")
    
    # 실행 중인 프로세스 정리
    if session_id in running_processes:
        running_processes[session_id].stop_execution()
        del running_processes[session_id]

@socketio.on('execute_realtime')
def handle_execute_realtime(data):
    """실시간 코드 실행"""
    session_id = request.sid
    code = data.get('code', '')
    
    print(f"📝 실시간 코드 실행 요청: {len(code)} 문자")
    
    # 기존 실행 중인 프로세스가 있으면 중지
    if session_id in running_processes:
        running_processes[session_id].stop_execution()
        del running_processes[session_id]
    
    # 새 실행기 생성
    executor = RealTimeExecutor(session_id)
    running_processes[session_id] = executor
    
    emit('execution_started', {
        'message': '실시간 실행 시작...',
        'timestamp': datetime.now().isoformat()
    })
    
    # 코드 실행
    success = executor.execute_code(code)
    if not success:
        if session_id in running_processes:
            del running_processes[session_id]

@socketio.on('stop_execution')
def handle_stop_execution():
    """실행 중지"""
    session_id = request.sid
    
    if session_id in running_processes:
        success = running_processes[session_id].stop_execution()
        if success:
            del running_processes[session_id]
        return success
    else:
        emit('execution_error', {
            'error': '실행 중인 프로세스가 없습니다',
            'timestamp': datetime.now().isoformat()
        })
        return False

@socketio.on('execute_code')
def handle_execute_code(data):
    """일반 코드 실행 (기존 기능 유지)"""
    code = data.get('code', '')
    print(f"📝 일반 코드 실행 요청: {len(code)} 문자")
    
    emit('execution_start', {
        'message': '코드 실행 중...',
        'timestamp': datetime.now().isoformat()
    })
    
    try:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        
        exec_globals = {'__name__': '__main__'}
        exec(code, exec_globals)
        
        stdout_result = stdout_capture.getvalue()
        stderr_result = stderr_capture.getvalue()
        
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        emit('execution_result', {
            'success': True,
            'stdout': stdout_result,
            'stderr': stderr_result,
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"✅ 일반 코드 실행 성공")
        
    except Exception as e:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        emit('execution_result', {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"❌ 일반 코드 실행 오류: {e}")

@socketio.on('ping')
def handle_ping():
    """핑 테스트"""
    emit('pong', {
        'timestamp': datetime.now().isoformat(),
        'server_time': datetime.now().strftime('%H:%M:%S')
    })

# HTML 템플릿 - 실시간 실행 기능 추가
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flask-SocketIO 실시간 코드 실행기 v2</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; font-weight: bold; }
        .connected { background: #d4edda; color: #155724; }
        .disconnected { background: #f8d7da; color: #721c24; }
        .executing { background: #fff3cd; color: #856404; }
        .realtime-executing { background: #cce5ff; color: #004085; }
        
        .main-content { display: flex; gap: 20px; }
        .left-panel { flex: 1; }
        .right-panel { flex: 1; }
        
        .editor-section { margin: 20px 0; }
        .code-editor { width: 100%; height: 300px; font-family: 'Courier New', monospace; 
                      padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }
        
        .controls { margin: 10px 0; display: flex; gap: 10px; flex-wrap: wrap; }
        .btn { padding: 10px 20px; background: #007bff; color: white; 
               border: none; border-radius: 5px; cursor: pointer; font-size: 14px; }
        .btn:hover { background: #0056b3; }
        .btn:disabled { background: #6c757d; cursor: not-allowed; }
        .btn-success { background: #28a745; }
        .btn-warning { background: #ffc107; color: #212529; }
        .btn-danger { background: #dc3545; }
        .btn-realtime { background: #17a2b8; }
        .btn-realtime:hover { background: #138496; }
        
        .output-section { margin: 20px 0; }
        .output { height: 400px; overflow-y: auto; border: 1px solid #ddd; 
                 padding: 10px; background: #f8f9fa; font-family: 'Courier New', monospace; 
                 font-size: 13px; line-height: 1.4; }
        
        .realtime-output { height: 300px; overflow-y: auto; border: 1px solid #17a2b8; 
                          padding: 10px; background: #f0f8ff; font-family: 'Courier New', monospace; 
                          font-size: 13px; line-height: 1.4; }
        
        .message { margin: 2px 0; padding: 3px 5px; border-radius: 3px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .info { background: #d1ecf1; color: #0c5460; }
        .realtime { background: #e7f3ff; color: #004085; }
        .warning { background: #fff3cd; color: #856404; }
        
        .stats { background: #e9ecef; padding: 10px; border-radius: 5px; margin: 10px 0; 
                display: flex; justify-content: space-between; flex-wrap: wrap; }
        .stat-item { margin: 5px; }
        
        .example-codes { margin: 20px 0; }
        .example-btn { padding: 5px 10px; margin: 2px; background: #6c757d; color: white; 
                      border: none; border-radius: 3px; cursor: pointer; font-size: 12px; }
        .example-btn:hover { background: #5a6268; }
        
        .section-title { color: #495057; border-bottom: 2px solid #dee2e6; padding-bottom: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Flask-SocketIO 실시간 코드 실행기 v2</h1>
        
        <div id="status" class="status disconnected">연결 시도 중...</div>
        
        <div class="stats">
            <div class="stat-item">연결 상태: <span id="connectionStatus">연결 시도 중</span></div>
            <div class="stat-item">일반 실행: <span id="executionCount">0</span>회</div>
            <div class="stat-item">실시간 실행: <span id="realtimeCount">0</span>회</div>
            <div class="stat-item">실시간 상태: <span id="realtimeStatus">대기 중</span></div>
        </div>
        
        <div class="main-content">
            <div class="left-panel">
                <div class="editor-section">
                    <h3 class="section-title">Python 코드 에디터</h3>
                    
                    <div class="example-codes">
                        <strong>예제 코드:</strong><br>
                        <button class="example-btn" onclick="loadExample('basic')">기본 출력</button>
                        <button class="example-btn" onclick="loadExample('loop')">무한 루프</button>
                        <button class="example-btn" onclick="loadExample('sensor')">센서 시뮬레이션</button>
                        <button class="example-btn" onclick="loadExample('counter')">카운터</button>
                        <button class="example-btn" onclick="loadExample('time')">시간 출력</button>
        </div>
        
            <textarea id="codeEditor" class="code-editor" placeholder="Python 코드를 입력하세요...">
# 실시간 무한루프 예제
import time

count = 0
while True:
    count += 1
    print(f"카운트: {count}")
    print(f"현재 시간: {time.strftime('%H:%M:%S')}")
    time.sleep(1)  # 1초 대기
            </textarea>
        </div>
        
        <div class="controls">
                    <button class="btn" onclick="executeCode()">▶️ 일반 실행</button>
                    <button class="btn btn-realtime" onclick="executeRealtime()" id="realtimeBtn">🔄 실시간 실행</button>
                    <button class="btn btn-danger" onclick="stopExecution()" id="stopBtn" disabled>⏹️ 중지</button>
                    <button class="btn btn-success" onclick="sendPing()">📡 Ping</button>
                    <button class="btn btn-warning" onclick="clearOutput()">🗑️ 지우기</button>
        </div>
        
        <div class="output-section">
                    <h3 class="section-title">일반 실행 결과</h3>
            <div id="output" class="output"></div>
                </div>
            </div>
            
            <div class="right-panel">
                <div class="output-section">
                    <h3 class="section-title">실시간 출력</h3>
                    <div id="realtimeOutput" class="realtime-output"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let socket = null;
        let executionCount = 0;
        let realtimeCount = 0;
        let isRealtimeRunning = false;
        
        // 예제 코드들
        const examples = {
            basic: `# 기본 출력 예제
print("Hello, Flask-SocketIO!")
print("현재 시간:", "2024-01-01")
result = 10 + 20
print(f"10 + 20 = {result}")`,
            
            loop: `# 무한 루프 예제
import time

count = 0
while True:
    count += 1
    print(f"카운트: {count}")
    print(f"현재 시간: {time.strftime('%H:%M:%S')}")
    time.sleep(1)  # 1초 대기`,
            
            sensor: `# 센서 시뮬레이션 예제
import time
import random

print("🤖 가상 센서 데이터 시뮬레이션 시작!")
print("💡 Ctrl+C로 종료하세요")
print("-" * 40)

while True:
    # 가상 센서 데이터 생성
    distance = round(random.uniform(5.0, 50.0), 1)
    temperature = round(random.uniform(20.0, 30.0), 1)
    
    print(f"거리: {distance} cm")
    print(f"온도: {temperature} °C")
    print("-" * 20)
    
    time.sleep(2)  # 2초 간격`,
            
            counter: `# 카운터 예제
import time

print("카운터 시작!")
for i in range(1, 101):
    print(f"카운트: {i}/100")
    time.sleep(0.5)
print("카운터 완료!")`,
            
            time: `# 시간 출력 예제
import time
from datetime import datetime

print("실시간 시계 시작!")
while True:
    now = datetime.now()
    print(f"현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"타임스탬프: {time.time()}")
    time.sleep(1)`
        };
        
        // 페이지 로드 시 연결
        document.addEventListener('DOMContentLoaded', function() {
            loadSocketIO();
        });
        
        function loadSocketIO() {
            const versions = [
                'https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js',
                'https://cdnjs.cloudflare.com/ajax/libs/socket.io/3.1.3/socket.io.js'
            ];
            
            let versionIndex = 0;
            
            function tryNextVersion() {
                if (versionIndex >= versions.length) {
                    addOutput('❌ Socket.IO 로드 실패', 'error');
                    return;
                }
                
                const script = document.createElement('script');
                script.src = versions[versionIndex];
                script.onload = function() {
                    addOutput(`✅ Socket.IO 로드 성공`, 'success');
                    connectToServer();
                };
                script.onerror = function() {
                    versionIndex++;
                    tryNextVersion();
                };
                document.head.appendChild(script);
            }
            
            tryNextVersion();
        }
        
        function connectToServer() {
            updateStatus('connecting', '서버에 연결 중...');
            
                socket = io({
                transports: ['polling', 'websocket'],
                    timeout: 20000,
                    forceNew: true
                });
                
                socket.on('connect', function() {
                    updateStatus('connected', '서버에 연결됨');
                    addOutput('✅ 서버에 연결되었습니다!', 'success');
                    document.getElementById('connectionStatus').textContent = '연결됨';
                });
                
                socket.on('disconnect', function(reason) {
                    updateStatus('disconnected', '서버 연결 해제됨');
                    addOutput('❌ 서버 연결이 해제되었습니다: ' + reason, 'error');
                    document.getElementById('connectionStatus').textContent = '연결 안됨';
                setRealtimeRunning(false);
                });
                
            socket.on('connect_error', function(error) {
                addOutput('❌ 연결 오류: ' + error, 'error');
                });
                
            // 일반 실행 이벤트
                socket.on('execution_start', function(data) {
                    updateStatus('executing', '코드 실행 중...');
                    addOutput('⏳ ' + data.message, 'info');
                });
                
                socket.on('execution_result', function(data) {
                    updateStatus('connected', '실행 완료');
                    executionCount++;
                    document.getElementById('executionCount').textContent = executionCount;
                    
                    if (data.success) {
                        if (data.stdout) {
                            addOutput('📤 출력:\\n' + data.stdout, 'success');
                        }
                        if (data.stderr) {
                        addOutput('⚠️ 경고:\\n' + data.stderr, 'warning');
                        }
                        if (!data.stdout && !data.stderr) {
                        addOutput('✅ 코드가 성공적으로 실행되었습니다', 'success');
                        }
                    } else {
                    addOutput('❌ 오류: ' + data.error, 'error');
                }
            });
            
            // 실시간 실행 이벤트
            socket.on('execution_started', function(data) {
                updateStatus('realtime-executing', '실시간 실행 중...');
                addRealtimeOutput('🚀 ' + data.message, 'info');
                setRealtimeRunning(true);
                realtimeCount++;
                document.getElementById('realtimeCount').textContent = realtimeCount;
                });
                
            socket.on('realtime_output', function(data) {
                addRealtimeOutput(data.output, 'realtime');
            });
            
            socket.on('execution_finished', function(data) {
                updateStatus('connected', '실행 완료');
                addRealtimeOutput('✅ ' + data.message, 'success');
                setRealtimeRunning(false);
                });
                
            socket.on('execution_stopped', function(data) {
                updateStatus('connected', '실행 중지됨');
                addRealtimeOutput('⏹️ ' + data.message, 'warning');
                setRealtimeRunning(false);
                });
                
            socket.on('execution_error', function(data) {
                addRealtimeOutput('❌ ' + data.error, 'error');
                setRealtimeRunning(false);
            });
            
            socket.on('pong', function(data) {
                addOutput('🏓 Pong - 서버 시간: ' + data.server_time, 'info');
            });
        }
        
        function executeCode() {
            const code = document.getElementById('codeEditor').value;
            if (!code.trim()) {
                addOutput('❌ 실행할 코드가 없습니다', 'error');
                return;
            }
            
            if (socket && socket.connected) {
                socket.emit('execute_code', { code: code });
            } else {
                addOutput('❌ 서버에 연결되지 않았습니다', 'error');
            }
        }
        
        function executeRealtime() {
            const code = document.getElementById('codeEditor').value;
            if (!code.trim()) {
                addRealtimeOutput('❌ 실행할 코드가 없습니다', 'error');
                return;
            }
            
            if (socket && socket.connected) {
                clearRealtimeOutput();
                socket.emit('execute_realtime', { code: code });
            } else {
                addRealtimeOutput('❌ 서버에 연결되지 않았습니다', 'error');
            }
        }
        
        function stopExecution() {
            if (socket && socket.connected) {
                socket.emit('stop_execution');
            } else {
                addRealtimeOutput('❌ 서버에 연결되지 않았습니다', 'error');
            }
        }
        
        function sendPing() {
            if (socket && socket.connected) {
                socket.emit('ping');
            } else {
                addOutput('❌ 서버에 연결되지 않았습니다', 'error');
            }
        }
        
        function clearOutput() {
            document.getElementById('output').innerHTML = '';
        }
        
        function clearRealtimeOutput() {
            document.getElementById('realtimeOutput').innerHTML = '';
        }
        
        function loadExample(type) {
            if (examples[type]) {
                document.getElementById('codeEditor').value = examples[type];
            }
        }
        
        function setRealtimeRunning(running) {
            isRealtimeRunning = running;
            document.getElementById('realtimeBtn').disabled = running;
            document.getElementById('stopBtn').disabled = !running;
            document.getElementById('realtimeStatus').textContent = running ? '실행 중' : '대기 중';
        }
        
        function updateStatus(type, message) {
            const statusEl = document.getElementById('status');
            statusEl.className = 'status ' + type;
            statusEl.textContent = message;
        }
        
        function addOutput(message, type) {
            const output = document.getElementById('output');
            const div = document.createElement('div');
            div.className = 'message ' + type;
            div.innerHTML = '<small>' + new Date().toLocaleTimeString() + '</small> ' + 
                           message.replace(/\\n/g, '<br>');
            output.appendChild(div);
            output.scrollTop = output.scrollHeight;
        }
        
        function addRealtimeOutput(message, type) {
            const output = document.getElementById('realtimeOutput');
            const div = document.createElement('div');
            div.className = 'message ' + type;
            div.innerHTML = '<small>' + new Date().toLocaleTimeString() + '</small> ' + 
                           message.replace(/\\n/g, '<br>');
            output.appendChild(div);
            output.scrollTop = output.scrollHeight;
        }
        
        // 키보드 단축키
        document.getElementById('codeEditor').addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                executeCode();
            } else if (e.ctrlKey && e.shiftKey && e.key === 'Enter') {
                executeRealtime();
            }
        });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("🚀 Flask-SocketIO 실시간 코드 실행기 v2 시작!")
    print("🌐 브라우저에서 http://라즈베리파이IP:5000 접속")
    print("🔄 실시간 무한루프 코드 실행 지원")
    print("⚡ WebSocket 완전 지원 (eventlet)")
    print("⏹️  종료: Ctrl+C")
    print("-" * 50)
    
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=5000, 
        debug=False,  # eventlet에서는 debug=False 권장
        use_reloader=False  # eventlet에서는 reloader 비활성화
    ) 