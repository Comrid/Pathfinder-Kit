#!/usr/bin/env python3
"""
Flask-SocketIO 연결 문제 해결 버전
더 안정적인 설정과 디버깅 기능 포함
"""

from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit
import sys
import io
import secrets
from datetime import datetime

app = Flask(__name__)

# 보안 키 설정 - Flask 세션 및 SocketIO 보안용
# 실제 운영환경에서는 환경변수나 별도 설정파일 사용 권장
app.config['SECRET_KEY'] = secrets.token_hex(32)  # 안전한 랜덤 키 생성

# 더 호환성 높은 설정
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='threading',
    logger=True,  # 디버깅용
    engineio_logger=True,  # 디버깅용
    ping_timeout=120,
    ping_interval=60
)

@app.route('/')
def index():
    """메인 페이지"""
    return render_template_string(HTML_TEMPLATE)

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결 시"""
    print(f"🔗 클라이언트 연결됨: {datetime.now()}")
    emit('status', {
        'type': 'connected',
        'message': '서버에 연결되었습니다!',
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제 시"""
    print(f"🔌 클라이언트 연결 해제됨: {datetime.now()}")

@socketio.on('execute_code')
def handle_execute_code(data):
    """Python 코드 실행"""
    code = data.get('code', '')
    print(f"📝 코드 실행 요청: {len(code)} 문자")
    
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
        
        print(f"✅ 코드 실행 성공")
        
    except Exception as e:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        emit('execution_result', {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"❌ 코드 실행 오류: {e}")

@socketio.on('ping')
def handle_ping():
    """핑 테스트"""
    emit('pong', {
        'timestamp': datetime.now().isoformat(),
        'server_time': datetime.now().strftime('%H:%M:%S')
    })

@socketio.on('test_message')
def handle_test_message(data):
    """테스트 메시지"""
    print(f"📨 테스트 메시지 수신: {data}")
    emit('test_response', {
        'original': data,
        'response': f"서버에서 받은 메시지: {data.get('message', '')}",
        'timestamp': datetime.now().isoformat()
    })

# HTML 템플릿 - 더 호환성 높은 Socket.IO 설정
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flask-SocketIO 웹 IDE (수정됨)</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; font-weight: bold; }
        .connected { background: #d4edda; color: #155724; }
        .disconnected { background: #f8d7da; color: #721c24; }
        .executing { background: #fff3cd; color: #856404; }
        .connecting { background: #cce5ff; color: #004085; }
        
        .editor-section { margin: 20px 0; }
        .code-editor { width: 100%; height: 200px; font-family: 'Courier New', monospace; 
                      padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        
        .controls { margin: 10px 0; }
        .btn { padding: 10px 20px; margin: 5px; background: #007bff; color: white; 
               border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #0056b3; }
        .btn-success { background: #28a745; }
        .btn-warning { background: #ffc107; color: #212529; }
        .btn-danger { background: #dc3545; }
        
        .output-section { margin: 20px 0; }
        .output { height: 300px; overflow-y: auto; border: 1px solid #ddd; 
                 padding: 10px; background: #f8f9fa; font-family: 'Courier New', monospace; }
        
        .message { margin: 5px 0; padding: 5px; border-radius: 3px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .info { background: #d1ecf1; color: #0c5460; }
        .debug { background: #fff3cd; color: #856404; }
        
        .stats { background: #e9ecef; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .debug-info { background: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Flask-SocketIO 웹 IDE (수정됨)</h1>
        
        <div id="status" class="status disconnected">연결 시도 중...</div>
        
        <div class="stats">
            <div>연결 상태: <span id="connectionStatus">연결 시도 중</span></div>
            <div>실행된 코드: <span id="executionCount">0</span>개</div>
            <div>마지막 실행: <span id="lastExecution">없음</span></div>
        </div>
        
        <div class="debug-info">
            <strong>디버그 정보:</strong><br>
            현재 URL: <span id="currentUrl"></span><br>
            Socket.IO 상태: <span id="socketStatus">초기화 중</span><br>
            연결 시도: <span id="connectionAttempts">0</span>회
        </div>
        
        <div class="editor-section">
            <h3>Python 코드 에디터</h3>
            <textarea id="codeEditor" class="code-editor" placeholder="Python 코드를 입력하세요...">
# 예제 코드
print("Hello, Flask-SocketIO!")
print("현재 시간:", "2024-01-01")

# 간단한 계산
result = 10 + 20
print(f"10 + 20 = {result}")

# 리스트 처리
numbers = [1, 2, 3, 4, 5]
print("숫자들:", numbers)
print("합계:", sum(numbers))
            </textarea>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="executeCode()">▶️ 코드 실행</button>
            <button class="btn btn-success" onclick="sendPing()">📡 Ping 테스트</button>
            <button class="btn btn-warning" onclick="clearOutput()">🗑️ 출력 지우기</button>
            <button class="btn" onclick="testConnection()">🔧 연결 테스트</button>
            <button class="btn btn-danger" onclick="reconnect()">🔄 재연결</button>
        </div>
        
        <div class="output-section">
            <h3>실행 결과</h3>
            <div id="output" class="output"></div>
        </div>
    </div>

    <!-- 여러 Socket.IO 버전 시도 -->
    <script>
        let socket = null;
        let executionCount = 0;
        let connectionAttempts = 0;
        
        // 현재 URL 표시
        document.getElementById('currentUrl').textContent = window.location.href;
        
        // 페이지 로드 시 연결
        document.addEventListener('DOMContentLoaded', function() {
            loadSocketIO();
        });
        
        function loadSocketIO() {
            // 여러 Socket.IO 버전을 순차적으로 시도
            const versions = [
                'https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js',
                'https://cdnjs.cloudflare.com/ajax/libs/socket.io/3.1.3/socket.io.js',
                'https://cdnjs.cloudflare.com/ajax/libs/socket.io/2.4.1/socket.io.js'
            ];
            
            let versionIndex = 0;
            
            function tryNextVersion() {
                if (versionIndex >= versions.length) {
                    addOutput('❌ 모든 Socket.IO 버전 로드 실패', 'error');
                    document.getElementById('socketStatus').textContent = '로드 실패';
                    return;
                }
                
                const script = document.createElement('script');
                script.src = versions[versionIndex];
                script.onload = function() {
                    addOutput(`✅ Socket.IO 로드 성공: 버전 ${versionIndex + 1}`, 'success');
                    document.getElementById('socketStatus').textContent = '로드됨';
                    connectToServer();
                };
                script.onerror = function() {
                    addOutput(`❌ Socket.IO 버전 ${versionIndex + 1} 로드 실패`, 'error');
                    versionIndex++;
                    tryNextVersion();
                };
                document.head.appendChild(script);
            }
            
            tryNextVersion();
        }
        
        function connectToServer() {
            connectionAttempts++;
            document.getElementById('connectionAttempts').textContent = connectionAttempts;
            
            updateStatus('connecting', '서버에 연결 중...');
            addOutput('🔄 서버 연결 시도 중...', 'info');
            
            try {
                // 다양한 설정으로 연결 시도
                socket = io({
                    transports: ['polling', 'websocket'],  // polling 우선
                    upgrade: true,
                    rememberUpgrade: false,
                    timeout: 20000,
                    forceNew: true
                });
                
                socket.on('connect', function() {
                    updateStatus('connected', '서버에 연결됨');
                    addOutput('✅ 서버에 연결되었습니다!', 'success');
                    document.getElementById('connectionStatus').textContent = '연결됨';
                    document.getElementById('socketStatus').textContent = '연결됨';
                });
                
                socket.on('connect_error', function(error) {
                    addOutput('❌ 연결 오류: ' + error, 'error');
                    document.getElementById('socketStatus').textContent = '연결 오류';
                });
                
                socket.on('disconnect', function(reason) {
                    updateStatus('disconnected', '서버 연결 해제됨');
                    addOutput('❌ 서버 연결이 해제되었습니다: ' + reason, 'error');
                    document.getElementById('connectionStatus').textContent = '연결 안됨';
                    document.getElementById('socketStatus').textContent = '연결 해제됨';
                });
                
                socket.on('status', function(data) {
                    addOutput('📡 ' + data.message, 'info');
                });
                
                socket.on('execution_start', function(data) {
                    updateStatus('executing', '코드 실행 중...');
                    addOutput('⏳ ' + data.message, 'info');
                });
                
                socket.on('execution_result', function(data) {
                    updateStatus('connected', '실행 완료');
                    executionCount++;
                    document.getElementById('executionCount').textContent = executionCount;
                    document.getElementById('lastExecution').textContent = new Date().toLocaleTimeString();
                    
                    if (data.success) {
                        if (data.stdout) {
                            addOutput('📤 출력:\\n' + data.stdout, 'success');
                        }
                        if (data.stderr) {
                            addOutput('⚠️ 경고:\\n' + data.stderr, 'error');
                        }
                        if (!data.stdout && !data.stderr) {
                            addOutput('✅ 코드가 성공적으로 실행되었습니다 (출력 없음)', 'success');
                        }
                    } else {
                        addOutput('❌ 오류: ' + data.error_type + '\\n' + data.error, 'error');
                    }
                });
                
                socket.on('pong', function(data) {
                    addOutput('🏓 Pong 응답 - 서버 시간: ' + data.server_time, 'info');
                });
                
                socket.on('test_response', function(data) {
                    addOutput('🔧 테스트 응답: ' + data.response, 'info');
                });
                
            } catch (error) {
                addOutput('❌ Socket.IO 초기화 오류: ' + error, 'error');
                document.getElementById('socketStatus').textContent = '초기화 오류';
            }
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
        
        function sendPing() {
            if (socket && socket.connected) {
                socket.emit('ping');
            } else {
                addOutput('❌ 서버에 연결되지 않았습니다', 'error');
            }
        }
        
        function testConnection() {
            if (socket && socket.connected) {
                socket.emit('test_message', { 
                    message: 'Hello from client!',
                    timestamp: new Date().toISOString()
                });
            } else {
                addOutput('❌ 서버에 연결되지 않았습니다', 'error');
            }
        }
        
        function reconnect() {
            if (socket) {
                socket.disconnect();
            }
            setTimeout(function() {
                addOutput('🔄 재연결 시도...', 'info');
                connectToServer();
            }, 1000);
        }
        
        function clearOutput() {
            document.getElementById('output').innerHTML = '';
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
        
        // Enter 키로 코드 실행 (Ctrl+Enter)
        document.getElementById('codeEditor').addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                executeCode();
            }
        });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("🚀 Flask-SocketIO 웹 IDE 시작! (수정된 버전)")
    print("🌐 브라우저에서 http://라즈베리파이IP:5000 접속")
    print("🔧 디버깅 모드 활성화")
    print("⏹️  종료: Ctrl+C")
    print("-" * 50)
    
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=5000, 
        debug=True,
        allow_unsafe_werkzeug=True
    ) 