#!/usr/bin/env python3
"""
Flask-SocketIO 보안 강화 실시간 코드 실행기
보안 표준을 준수한 안전한 코드 실행 환경
"""

import eventlet
eventlet.monkey_patch()

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
import re
import shlex
import logging
from datetime import datetime
from typing import List, Optional

# 보안 설정
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask-SocketIO 설정 (보안 강화)
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",  # 프로덕션에서는 특정 도메인으로 제한
    async_mode='eventlet',
    logger=False,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25,
    transports=['websocket', 'polling'],
    allow_upgrades=True,
    websocket_timeout=60,
    max_http_buffer_size=1024 * 1024  # 1MB 제한
)

class SecureCodeValidator:
    """
    보안 코드 검증 클래스
    위험한 코드 패턴을 사전에 차단
    """
    
    # 금지된 모듈 및 함수
    FORBIDDEN_IMPORTS = {
        'os', 'subprocess', 'sys', 'shutil', 'glob', 'socket', 
        'urllib', 'requests', 'ftplib', 'telnetlib', 'smtplib',
        'pickle', 'marshal', 'shelve', 'dbm'
    }
    
    # 금지된 함수 호출
    FORBIDDEN_FUNCTIONS = {
        'eval', 'exec', 'compile', 'open', '__import__',
        'getattr', 'setattr', 'delattr', 'hasattr', 'vars',
        'dir', 'globals', 'locals'
    }
    
    # 위험한 패턴
    DANGEROUS_PATTERNS = [
        r'__.*__',  # 매직 메서드
        r'\..*\(',  # 메서드 체이닝
        r'import\s+os',  # OS 모듈 import
        r'from\s+os',  # OS 모듈 from import
        r'subprocess',  # subprocess 사용
        r'system\(',  # 시스템 명령 실행
        r'popen\(',  # 프로세스 실행
        r'eval\(',  # eval 함수
        r'exec\(',  # exec 함수
    ]
    
    @classmethod
    def validate_code(cls, code: str) -> tuple[bool, str]:
        """
        코드 보안 검증
        
        Args:
            code (str): 검증할 Python 코드
            
        Returns:
            tuple[bool, str]: (유효성, 오류 메시지)
        """
        # 코드 길이 제한
        if len(code) > 10000:  # 10KB 제한
            return False, "코드가 너무 깁니다 (최대 10KB)"
        
        # 금지된 import 검사
        for forbidden in cls.FORBIDDEN_IMPORTS:
            if re.search(rf'\bimport\s+{forbidden}\b', code):
                return False, f"금지된 모듈: {forbidden}"
            if re.search(rf'\bfrom\s+{forbidden}\b', code):
                return False, f"금지된 모듈: {forbidden}"
        
        # 금지된 함수 검사
        for forbidden in cls.FORBIDDEN_FUNCTIONS:
            if re.search(rf'\b{forbidden}\s*\(', code):
                return False, f"금지된 함수: {forbidden}"
        
        # 위험한 패턴 검사
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, code):
                return False, f"위험한 패턴 감지: {pattern}"
        
        return True, ""

class SecureExecutor:
    """보안 강화된 코드 실행 클래스"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.process = None
        self.is_running = False
        self.temp_file = None
        self.start_time = None
        self.max_execution_time = 300  # 5분 제한
        
    def execute_code(self, code: str) -> bool:
        """
        보안 검증된 코드 실행
        
        Args:
            code (str): 실행할 Python 코드
            
        Returns:
            bool: 실행 성공 여부
        """
        try:
            # 1. 코드 보안 검증
            is_valid, error_msg = SecureCodeValidator.validate_code(code)
            if not is_valid:
                socketio.emit('execution_error', {
                    'error': f'보안 검증 실패: {error_msg}',
                    'timestamp': datetime.now().isoformat()
                }, room=self.session_id)
                return False
            
            # 2. 안전한 임시 파일 생성
            self.temp_file = tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.py', 
                delete=False,
                encoding='utf-8',
                dir=tempfile.gettempdir()  # 시스템 임시 디렉토리 사용
            )
            
            # 3. 제한된 실행 환경 코드 추가
            safe_code = self._create_safe_environment(code)
            self.temp_file.write(safe_code)
            self.temp_file.close()
            
            # 4. 보안 강화된 프로세스 실행
            self.process = subprocess.Popen(
                [sys.executable, '-u', self.temp_file.name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=0,
                shell=False,  # 보안: shell=False 사용
                cwd=tempfile.gettempdir(),  # 안전한 작업 디렉토리
                env={'PYTHONPATH': ''},  # 환경 변수 제한
                preexec_fn=None  # 보안: preexec_fn 사용 안함
            )
            
            self.is_running = True
            self.start_time = time.time()
            
            # 5. 실시간 모니터링 시작
            monitor_thread = threading.Thread(
                target=self._monitor_execution,
                daemon=True
            )
            monitor_thread.start()
            
            logger.info(f"코드 실행 시작: 세션 {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"코드 실행 오류: {e}")
            socketio.emit('execution_error', {
                'error': f'실행 오류: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
            return False
    
    def _create_safe_environment(self, user_code: str) -> str:
        """
        안전한 실행 환경 코드 생성
        
        Args:
            user_code (str): 사용자 코드
            
        Returns:
            str: 보안 강화된 실행 코드
        """
        safe_wrapper = f'''
import sys
import signal
import time
from datetime import datetime

# 실행 시간 제한 설정
def timeout_handler(signum, frame):
    print("\\n⏰ 실행 시간 초과 (최대 {self.max_execution_time}초)")
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm({self.max_execution_time})

# 안전한 print 함수 (출력 제한)
original_print = print
output_count = 0
MAX_OUTPUT_LINES = 1000

def safe_print(*args, **kwargs):
    global output_count
    if output_count < MAX_OUTPUT_LINES:
        original_print(*args, **kwargs)
        output_count += 1
    elif output_count == MAX_OUTPUT_LINES:
        original_print("\\n⚠️ 출력 라인 수 제한 도달 (최대 1000줄)")
        output_count += 1

# print 함수 교체
print = safe_print

try:
    # 사용자 코드 실행
{self._indent_code(user_code, 4)}
except KeyboardInterrupt:
    print("\\n⏹️ 사용자에 의해 중단됨")
except Exception as e:
    print(f"\\n❌ 오류 발생: {{e}}")
    print(f"오류 타입: {{type(e).__name__}}")
finally:
    signal.alarm(0)  # 타이머 해제
'''
        return safe_wrapper
    
    def _indent_code(self, code: str, spaces: int) -> str:
        """코드 들여쓰기"""
        indent = ' ' * spaces
        return '\n'.join(indent + line for line in code.split('\n'))
    
    def _monitor_execution(self):
        """실행 모니터링 및 출력 처리"""
        try:
            while self.is_running and self.process and self.process.poll() is None:
                # 실행 시간 체크
                if time.time() - self.start_time > self.max_execution_time:
                    self.stop_execution()
                    break
                
                try:
                    line = self.process.stdout.readline()
                    if line:
                        socketio.emit('realtime_output', {
                            'output': line.rstrip('\n\r'),
                            'timestamp': datetime.now().isoformat()
                        }, room=self.session_id)
                    else:
                        time.sleep(0.01)
                        
                except Exception as e:
                    logger.error(f"출력 읽기 오류: {e}")
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
            logger.error(f"모니터링 오류: {e}")
        finally:
            self.cleanup()
    
    def stop_execution(self) -> bool:
        """안전한 실행 중지"""
        try:
            self.is_running = False
            
            if self.process and self.process.poll() is None:
                # 1. 정상 종료 시도
                self.process.terminate()
                
                # 2. 3초 대기
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    # 3. 강제 종료
                    self.process.kill()
                    self.process.wait()
                
                socketio.emit('execution_stopped', {
                    'message': '실행이 안전하게 중지되었습니다',
                    'timestamp': datetime.now().isoformat()
                }, room=self.session_id)
                
            logger.info(f"코드 실행 중지: 세션 {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"실행 중지 오류: {e}")
            return False
    
    def cleanup(self):
        """리소스 안전 정리"""
        try:
            if self.temp_file and os.path.exists(self.temp_file.name):
                os.unlink(self.temp_file.name)
                logger.info(f"임시 파일 정리: {self.temp_file.name}")
        except Exception as e:
            logger.error(f"정리 오류: {e}")

# 전역 실행기 관리
running_executors = {}

@app.route('/')
def index():
    """메인 페이지"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>패스파인더 보안 코드 실행기</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 15px; 
            padding: 30px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        h1 { 
            color: #333; 
            text-align: center; 
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .security-notice {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .security-notice h3 {
            color: #856404;
            margin-top: 0;
        }
        .editor-container { 
            margin-bottom: 20px; 
        }
        #codeEditor { 
            width: 100%; 
            height: 300px; 
            font-family: 'Courier New', monospace; 
            font-size: 14px; 
            border: 2px solid #ddd; 
            border-radius: 8px; 
            padding: 15px;
            resize: vertical;
        }
        .controls { 
            text-align: center; 
            margin: 20px 0; 
        }
        button { 
            background: linear-gradient(45deg, #667eea, #764ba2); 
            color: white; 
            border: none; 
            padding: 12px 25px; 
            margin: 0 10px; 
            border-radius: 25px; 
            cursor: pointer; 
            font-size: 16px;
            transition: all 0.3s ease;
        }
        button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        button:disabled { 
            background: #ccc; 
            cursor: not-allowed; 
            transform: none;
        }
        .output-container { 
            display: flex; 
            gap: 20px; 
        }
        .output-panel { 
            flex: 1; 
            background: #f8f9fa; 
            border: 2px solid #dee2e6; 
            border-radius: 8px; 
            padding: 15px; 
            height: 400px; 
            overflow-y: auto;
        }
        .output-panel h3 { 
            margin-top: 0; 
            color: #495057;
        }
        .message { 
            margin: 5px 0; 
            padding: 8px; 
            border-radius: 4px; 
        }
        .message.output { 
            background: #e7f3ff; 
            border-left: 4px solid #007bff;
        }
        .message.error { 
            background: #f8d7da; 
            border-left: 4px solid #dc3545;
        }
        .message.success { 
            background: #d4edda; 
            border-left: 4px solid #28a745;
        }
        .message.info { 
            background: #fff3cd; 
            border-left: 4px solid #ffc107;
        }
        .status { 
            text-align: center; 
            padding: 10px; 
            margin: 10px 0; 
            border-radius: 8px; 
            font-weight: bold;
        }
        .status.connected { 
            background: #d4edda; 
            color: #155724; 
        }
        .status.disconnected { 
            background: #f8d7da; 
            color: #721c24; 
        }
        .status.running { 
            background: #fff3cd; 
            color: #856404; 
        }
        small { 
            color: #6c757d; 
            font-size: 0.8em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 패스파인더 보안 코드 실행기</h1>
        
        <div class="security-notice">
            <h3>🛡️ 보안 정책</h3>
            <ul>
                <li>위험한 모듈 및 함수 사용 금지 (os, subprocess, eval 등)</li>
                <li>최대 실행 시간: 5분</li>
                <li>최대 출력 라인: 1000줄</li>
                <li>코드 크기 제한: 10KB</li>
            </ul>
        </div>
        
        <div id="connectionStatus" class="status disconnected">
            🔌 서버 연결 중...
        </div>
        
        <div class="editor-container">
            <textarea id="codeEditor" placeholder="여기에 Python 코드를 입력하세요...">
# 패스파인더 보안 코드 실행기 예제
print("🤖 안전한 코드 실행 환경입니다!")

# 기본 연산
for i in range(5):
    print(f"카운트: {i}")

# 수학 연산
import math
print(f"원주율: {math.pi:.4f}")

# 시간 지연 (안전)
import time
print("잠시 대기...")
time.sleep(1)
print("완료!")
            </textarea>
        </div>
        
        <div class="controls">
            <button onclick="executeCode()" id="executeBtn">
                ▶️ 실행 (Ctrl+Enter)
            </button>
            <button onclick="executeRealtime()" id="realtimeBtn">
                ⚡ 실시간 실행 (Ctrl+Shift+Enter)
            </button>
            <button onclick="stopExecution()" id="stopBtn" disabled>
                ⏹️ 중지
            </button>
            <button onclick="clearOutput()">
                🗑️ 출력 지우기
            </button>
        </div>
        
        <div class="output-container">
            <div class="output-panel">
                <h3>📄 일반 실행 결과</h3>
                <div id="output"></div>
            </div>
            <div class="output-panel">
                <h3>⚡ 실시간 실행 결과</h3>
                <div id="realtimeOutput"></div>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let isExecuting = false;
        
        // 연결 상태 관리
        socket.on('connect', function() {
            document.getElementById('connectionStatus').className = 'status connected';
            document.getElementById('connectionStatus').textContent = '🟢 서버 연결됨';
        });
        
        socket.on('disconnect', function() {
            document.getElementById('connectionStatus').className = 'status disconnected';
            document.getElementById('connectionStatus').textContent = '🔴 서버 연결 끊김';
        });
        
        // 일반 실행 결과
        socket.on('execution_result', function(data) {
            const output = document.getElementById('output');
            const div = document.createElement('div');
            div.className = 'message ' + (data.success ? 'success' : 'error');
            
            if (data.success) {
                div.innerHTML = '<small>' + data.timestamp + '</small><br>' + 
                               (data.stdout || '').replace(/\\n/g, '<br>') +
                               (data.stderr ? '<br><span style="color:red;">' + data.stderr.replace(/\\n/g, '<br>') + '</span>' : '');
            } else {
                div.innerHTML = '<small>' + data.timestamp + '</small><br>' +
                               '<strong>오류:</strong> ' + data.error;
            }
            
            output.appendChild(div);
            output.scrollTop = output.scrollHeight;
        });
        
        // 실시간 실행 이벤트
        socket.on('execution_started', function(data) {
            isExecuting = true;
            updateButtons();
            addRealtimeMessage(data.message, 'info');
        });
        
        socket.on('realtime_output', function(data) {
            addRealtimeMessage(data.output, 'output');
        });
        
        socket.on('execution_finished', function(data) {
            isExecuting = false;
            updateButtons();
            addRealtimeMessage(data.message, 'success');
        });
        
        socket.on('execution_stopped', function(data) {
            isExecuting = false;
            updateButtons();
            addRealtimeMessage(data.message, 'info');
        });
        
        socket.on('execution_error', function(data) {
            isExecuting = false;
            updateButtons();
            addRealtimeMessage('오류: ' + data.error, 'error');
        });
        
        // 함수들
        function executeCode() {
            const code = document.getElementById('codeEditor').value;
            socket.emit('execute_code', {code: code});
            addMessage('코드 실행 요청됨...', 'info');
        }
        
        function executeRealtime() {
            const code = document.getElementById('codeEditor').value;
            socket.emit('execute_realtime', {code: code});
        }
        
        function stopExecution() {
            socket.emit('stop_execution');
        }
        
        function clearOutput() {
            document.getElementById('output').innerHTML = '';
            document.getElementById('realtimeOutput').innerHTML = '';
        }
        
        function updateButtons() {
            document.getElementById('executeBtn').disabled = isExecuting;
            document.getElementById('realtimeBtn').disabled = isExecuting;
            document.getElementById('stopBtn').disabled = !isExecuting;
            
            if (isExecuting) {
                document.getElementById('connectionStatus').className = 'status running';
                document.getElementById('connectionStatus').textContent = '⚡ 코드 실행 중...';
            } else {
                document.getElementById('connectionStatus').className = 'status connected';
                document.getElementById('connectionStatus').textContent = '🟢 서버 연결됨';
            }
        }
        
        function addMessage(message, type) {
            const output = document.getElementById('output');
            const div = document.createElement('div');
            div.className = 'message ' + type;
            div.innerHTML = '<small>' + new Date().toLocaleTimeString() + '</small> ' + 
                           message.replace(/\\n/g, '<br>');
            output.appendChild(div);
            output.scrollTop = output.scrollHeight;
        }
        
        function addRealtimeMessage(message, type) {
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
                if (e.shiftKey) {
                    executeRealtime();
                } else {
                    executeCode();
                }
                e.preventDefault();
            }
        });
    </script>
</body>
</html>
    ''')

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결"""
    session_id = request.sid
    logger.info(f"클라이언트 연결: {session_id}")

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제"""
    session_id = request.sid
    logger.info(f"클라이언트 연결 해제: {session_id}")
    
    # 실행 중인 프로세스 정리
    if session_id in running_executors:
        running_executors[session_id].stop_execution()
        del running_executors[session_id]

@socketio.on('execute_realtime')
def handle_execute_realtime(data):
    """보안 강화된 실시간 코드 실행"""
    session_id = request.sid
    code = data.get('code', '')
    
    logger.info(f"실시간 코드 실행 요청: 세션 {session_id}, 코드 길이 {len(code)}")
    
    # 기존 실행 중인 프로세스 정리
    if session_id in running_executors:
        running_executors[session_id].stop_execution()
        del running_executors[session_id]
    
    # 새 보안 실행기 생성
    executor = SecureExecutor(session_id)
    running_executors[session_id] = executor
    
    emit('execution_started', {
        'message': '보안 검증 후 실행 시작...',
        'timestamp': datetime.now().isoformat()
    })
    
    # 보안 검증 및 실행
    success = executor.execute_code(code)
    if not success:
        if session_id in running_executors:
            del running_executors[session_id]

@socketio.on('stop_execution')
def handle_stop_execution():
    """실행 중지"""
    session_id = request.sid
    
    if session_id in running_executors:
        success = running_executors[session_id].stop_execution()
        if success:
            del running_executors[session_id]
        return success
    else:
        emit('execution_error', {
            'error': '실행 중인 프로세스가 없습니다',
            'timestamp': datetime.now().isoformat()
        })
        return False

@socketio.on('execute_code')
def handle_execute_code(data):
    """일반 코드 실행 (제한된 환경)"""
    code = data.get('code', '')
    session_id = request.sid
    
    logger.info(f"일반 코드 실행 요청: 세션 {session_id}")
    
    # 보안 검증
    is_valid, error_msg = SecureCodeValidator.validate_code(code)
    if not is_valid:
        emit('execution_result', {
            'success': False,
            'error': f'보안 검증 실패: {error_msg}',
            'timestamp': datetime.now().isoformat()
        })
        return
    
    emit('execution_start', {
        'message': '코드 실행 중...',
        'timestamp': datetime.now().isoformat()
    })
    
    try:
        # 제한된 환경에서 실행
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        
        # 제한된 globals 환경
        safe_globals = {
            '__name__': '__main__',
            '__builtins__': {
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'sum': sum,
                'min': min,
                'max': max,
                'abs': abs,
                'round': round,
                'sorted': sorted,
                'reversed': reversed,
            }
        }
        
        exec(code, safe_globals)
        
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
        
        logger.info(f"일반 코드 실행 성공: 세션 {session_id}")
        
    except Exception as e:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        emit('execution_result', {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.error(f"일반 코드 실행 오류: 세션 {session_id}, 오류: {e}")

if __name__ == '__main__':
    print("🔒 패스파인더 보안 강화 코드 실행기 시작!")
    print("🛡️ 보안 정책:")
    print("   - 위험한 모듈/함수 차단")
    print("   - 실행 시간 제한 (5분)")
    print("   - 출력 라인 제한 (1000줄)")
    print("   - 코드 크기 제한 (10KB)")
    print("🌐 브라우저에서 http://라즈베리파이IP:5000 접속")
    print("⏹️  종료: Ctrl+C")
    print("-" * 60)
    
    try:
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=5000, 
            debug=False,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n⏹️ 서버 종료 중...")
        # 모든 실행 중인 프로세스 정리
        for executor in running_executors.values():
            executor.stop_execution()
        print("✅ 모든 프로세스 정리 완료")
    except Exception as e:
        logger.error(f"서버 오류: {e}")
    finally:
        logger.info("서버 종료됨") 