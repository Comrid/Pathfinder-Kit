#!/usr/bin/env python3
"""
Pathfinder Web IDE v3 - 스마트 실시간 코드 실행 시스템
라즈베리파이 원격 개발을 위한 직관적이고 강력한 IDE

주요 기능:
- 스마트 실시간 코드 실행 (단일 실행 버튼)
- 자동 프로세스 종료 감지
- 파일/폴더 관리
- Monaco Editor 통합
- WebSocket 기반 실시간 통신
"""

# eventlet으로 WebSocket 완전 지원
import eventlet
eventlet.monkey_patch()

from flask import Flask, request, render_template, jsonify
from flask_socketio import SocketIO, emit, join_room
import subprocess
import os
import shutil
import json
from datetime import datetime
import threading
import time
import secrets
import logging
import sys
import io
import tempfile

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# 전역 설정
CONFIG = {
    'project_dir': os.path.expanduser("~"),  # 홈 디렉토리
    'max_file_size': 5 * 1024 * 1024,  # 5MB
    'excluded_dirs': {'.git', '__pycache__', '.vscode', 'node_modules', '.DS_Store', '.pytest_cache'},
    'allowed_extensions': {'.py', '.txt', '.md', '.json', '.html', '.css', '.js', '.sh', '.cfg', '.yml', '.yaml', '.xml'},
    'max_execution_time': 300  # 5분
}

# 전역 변수
running_processes = {}  # 실행 중인 프로세스들

class SmartExecutor:
    """스마트 실시간 코드 실행 관리 클래스"""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.process = None
        self.is_running = False
        self.temp_file = None
        
    def execute_code(self, code):
        """코드를 별도 프로세스에서 스마트 실시간 실행"""
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
            python_cmd = 'python' if os.name == 'nt' else 'python3'
            self.process = subprocess.Popen(
                [python_cmd, '-u', self.temp_file.name],
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
        """프로세스 출력을 실시간으로 모니터링하고 자동 종료 감지"""
        try:
            while self.is_running and self.process and self.process.poll() is None:
                try:
                    # 실시간 출력 읽기
                    line = self.process.stdout.readline()
                    if line:
                        socketio.emit('code_output', {
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
            
            # 프로세스 종료 처리 (자동 감지)
            if self.process:
                exit_code = self.process.poll()
                if exit_code is not None:
                    if exit_code == 0:
                        # 정상 종료 - 일반 코드 완료
                        socketio.emit('execution_completed', {
                            'exit_code': exit_code,
                            'message': '✅ 프로그램이 완료되었습니다',
                            'timestamp': datetime.now().isoformat()
                        }, room=self.session_id)
                    else:
                        # 오류 종료
                        socketio.emit('execution_error', {
                            'error': f'프로그램이 오류로 종료되었습니다 (코드: {exit_code})',
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
                    'message': '⏹️ 실행이 중지되었습니다',
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

class FileManager:
    """파일 시스템 관리 클래스"""
    
    @staticmethod
    def get_file_tree(path):
        """파일 트리 구조 생성"""
        tree = []
        try:
            if not os.path.exists(path):
                return tree
                
            items = sorted(os.listdir(path))
            
            # 폴더 먼저 추가
            for item in items:
                if item.startswith('.') or item in CONFIG['excluded_dirs']:
                    continue
                    
                item_path = os.path.join(path, item)
                rel_path = os.path.relpath(item_path, CONFIG['project_dir']).replace('\\', '/')
                
                if os.path.isdir(item_path):
                    tree.append({
                        'name': item,
                        'type': 'folder',
                        'path': rel_path,
                        'children': FileManager.get_file_tree(item_path)
                    })
            
            # 파일 나중에 추가
            for item in items:
                if item.startswith('.') or item in CONFIG['excluded_dirs']:
                    continue
                    
                item_path = os.path.join(path, item)
                rel_path = os.path.relpath(item_path, CONFIG['project_dir']).replace('\\', '/')
                
                if os.path.isfile(item_path):
                    ext = os.path.splitext(item)[1].lower()
                    tree.append({
                        'name': item,
                        'type': 'file',
                        'path': rel_path,
                        'extension': ext,
                        'size': os.path.getsize(item_path),
                        'modified': datetime.fromtimestamp(os.path.getmtime(item_path)).isoformat()
                    })
                    
        except PermissionError:
            logger.warning(f"권한 없음: {path}")
        except Exception as e:
            logger.error(f"디렉토리 읽기 오류 {path}: {e}")
        
        return tree
    
    @staticmethod
    def is_safe_path(filepath):
        """경로 안전성 검사"""
        if not filepath:
            return False
            
        # 위험한 패턴 검사
        dangerous_patterns = ['..', '~', '$', '|', ';', '&', '`']
        for pattern in dangerous_patterns:
            if pattern in filepath:
                logger.warning(f"위험한 경로 패턴 감지: {filepath}")
                return False
        
        try:
            full_path = os.path.join(CONFIG['project_dir'], filepath)
            resolved_path = os.path.realpath(full_path)
            project_path = os.path.realpath(CONFIG['project_dir'])
            
            # 프로젝트 디렉토리 내부인지 확인
            return resolved_path.startswith(project_path)
        except Exception as e:
            logger.error(f"경로 검증 오류: {e}")
            return False

# ==================== 라우트 ====================

@app.route('/')
def index():
    """메인 페이지"""
    return render_template_string(HTML_TEMPLATE)
    #return render_template('index.html')

@app.route('/api/files')
def get_files():
    """파일 트리 API"""
    try:
        tree = FileManager.get_file_tree(CONFIG['project_dir'])
        return jsonify({'success': True, 'data': tree})
    except Exception as e:
        logger.error(f"파일 트리 로드 오류: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/file/<path:filepath>')
def get_file(filepath):
    """파일 내용 읽기"""
    try:
        if not FileManager.is_safe_path(filepath):
            return jsonify({'success': False, 'error': '접근 권한이 없습니다'}), 403
        
        full_path = os.path.join(CONFIG['project_dir'], filepath)
        
        if not os.path.exists(full_path):
            return jsonify({'success': False, 'error': '파일을 찾을 수 없습니다'}), 404
        
        if os.path.getsize(full_path) > CONFIG['max_file_size']:
            return jsonify({'success': False, 'error': '파일이 너무 큽니다 (5MB 제한)'}), 413
        
        # 파일 확장자 확인
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in CONFIG['allowed_extensions']:
            return jsonify({'success': False, 'error': '지원하지 않는 파일 형식입니다'}), 400
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'data': {
                'content': content,
                'size': os.path.getsize(full_path),
                'modified': datetime.fromtimestamp(os.path.getmtime(full_path)).isoformat()
            }
        })
        
    except UnicodeDecodeError:
        return jsonify({'success': False, 'error': '바이너리 파일은 편집할 수 없습니다'}), 400
    except PermissionError:
        return jsonify({'success': False, 'error': '파일 접근 권한이 없습니다'}), 403
    except Exception as e:
        logger.error(f"파일 읽기 오류: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/file/<path:filepath>', methods=['POST'])
def save_file(filepath):
    """파일 저장"""
    try:
        if not FileManager.is_safe_path(filepath):
            return jsonify({'success': False, 'error': '접근 권한이 없습니다'}), 403
        
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'success': False, 'error': '잘못된 요청 데이터'}), 400
        
        content = data.get('content', '')
        
        # 내용 크기 제한
        if len(content.encode('utf-8')) > CONFIG['max_file_size']:
            return jsonify({'success': False, 'error': '파일 내용이 너무 큽니다'}), 413
        
        full_path = os.path.join(CONFIG['project_dir'], filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"파일 저장: {filepath}")
        return jsonify({'success': True, 'message': '파일이 저장되었습니다'})
        
    except PermissionError:
        return jsonify({'success': False, 'error': '파일 저장 권한이 없습니다'}), 403
    except Exception as e:
        logger.error(f"파일 저장 오류: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/create', methods=['POST'])
def create_item():
    """파일/폴더 생성"""
    try:
        data = request.get_json()
        if not data or 'path' not in data:
            return jsonify({'success': False, 'error': '잘못된 요청 데이터'}), 400
        
        path = data.get('path', '').strip()
        is_folder = data.get('is_folder', False)
        
        if not path:
            return jsonify({'success': False, 'error': '경로를 입력하세요'}), 400
        
        if not FileManager.is_safe_path(path):
            return jsonify({'success': False, 'error': '접근 권한이 없습니다'}), 403
        
        full_path = os.path.join(CONFIG['project_dir'], path)
        
        if os.path.exists(full_path):
            return jsonify({'success': False, 'error': '이미 존재합니다'}), 409
        
        if is_folder:
            os.makedirs(full_path, exist_ok=True)
            message = f'폴더 "{os.path.basename(path)}"가 생성되었습니다'
            logger.info(f"폴더 생성: {path}")
        else:
            # 파일 확장자 확인
            ext = os.path.splitext(path)[1].lower()
            if ext and ext not in CONFIG['allowed_extensions']:
                return jsonify({'success': False, 'error': '지원하지 않는 파일 형식입니다'}), 400
            
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write('')
            message = f'파일 "{os.path.basename(path)}"가 생성되었습니다'
            logger.info(f"파일 생성: {path}")
        
        return jsonify({'success': True, 'message': message, 'path': path})
        
    except PermissionError:
        return jsonify({'success': False, 'error': '생성 권한이 없습니다'}), 403
    except Exception as e:
        logger.error(f"생성 오류: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/delete/<path:filepath>', methods=['DELETE'])
def delete_item(filepath):
    """파일/폴더 삭제"""
    try:
        if not FileManager.is_safe_path(filepath):
            return jsonify({'success': False, 'error': '접근 권한이 없습니다'}), 403
        
        full_path = os.path.join(CONFIG['project_dir'], filepath)
        
        if not os.path.exists(full_path):
            return jsonify({'success': False, 'error': '파일을 찾을 수 없습니다'}), 404
        
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
            message = '폴더가 삭제되었습니다'
            logger.info(f"폴더 삭제: {filepath}")
        else:
            os.remove(full_path)
            message = '파일이 삭제되었습니다'
            logger.info(f"파일 삭제: {filepath}")
        
        return jsonify({'success': True, 'message': message})
        
    except PermissionError:
        return jsonify({'success': False, 'error': '삭제 권한이 없습니다'}), 403
    except Exception as e:
        logger.error(f"삭제 오류: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== WebSocket 이벤트 ====================

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결"""
    logger.info(f"클라이언트 연결: {request.sid}")
    emit('connected', {'message': '서버에 연결되었습니다'})

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제"""
    logger.info(f"클라이언트 연결 해제: {request.sid}")
    
    # 해당 세션의 실행 중인 프로세스들 정리
    if request.sid in running_processes:
        running_processes[request.sid].stop_execution()
        del running_processes[request.sid]

@socketio.on('join_session')
def handle_join_session(data):
    """세션 참가"""
    session_id = data.get('session_id', request.sid)
    join_room(session_id)
    emit('session_joined', {'session_id': session_id})
    logger.info(f"세션 참가: {session_id}")

@socketio.on('execute_code')
def handle_execute_code(data):
    """스마트 실시간 코드 실행 (단일 실행 버튼)"""
    session_id = request.sid
    code = data.get('code', '')
    
    logger.info(f"📝 스마트 코드 실행 요청: {len(code)} 문자 (세션: {session_id})")
    
    # 기존 실행 중인 프로세스가 있으면 중지
    if session_id in running_processes:
        running_processes[session_id].stop_execution()
        del running_processes[session_id]
    
    # 새 실행기 생성
    executor = SmartExecutor(session_id)
    running_processes[session_id] = executor
    
    emit('execution_started', {
        'message': '🚀 코드 실행 시작...',
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

@socketio.on('ping')
def handle_ping():
    """핑 테스트"""
    emit('pong', {
        'timestamp': datetime.now().isoformat(),
        'server_time': datetime.now().strftime('%H:%M:%S')
    })

# ==================== 에러 핸들러 ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'API를 찾을 수 없습니다'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"서버 오류: {error}")
    return jsonify({'success': False, 'error': '서버 오류가 발생했습니다'}), 500

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pathfinder Web IDE v3</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🚀</text></svg>">
    
    <!-- Monaco Editor -->
    <script src="https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs/loader.js"></script>
    
    <!-- Socket.IO -->
    <script src="https://cdn.socket.io/4.8.1/socket.io.min.js"></script>
    
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1e1e1e;
            color: #cccccc;
            overflow: hidden;
        }

        .ide-container {
            display: flex;
            height: 100vh;
            flex-direction: column;
        }

        /* 상단 메뉴바 */
        .menubar {
            background: #2d2d30;
            height: 40px;
            display: flex;
            align-items: center;
            padding: 0 15px;
            border-bottom: 1px solid #3e3e42;
            user-select: none;
        }

        .logo {
            display: flex;
            align-items: center;
            margin-right: 30px;
            font-weight: bold;
            color: #ffffff;
            font-size: 16px;
        }

        .logo::before {
            content: '🚀';
            margin-right: 8px;
        }

        .menu-buttons {
            display: flex;
            gap: 10px;
        }

        .menu-btn {
            background: #007acc;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            transition: background 0.2s;
        }

        .menu-btn:hover {
            background: #005a9e;
        }

        .menu-btn:disabled {
            background: #555;
            cursor: not-allowed;
        }

        .menu-btn.danger {
            background: #dc3545;
        }

        .menu-btn.danger:hover {
            background: #c82333;
        }

        /* 메인 영역 */
        .main-area {
            display: flex;
            flex: 1;
            overflow: hidden;
        }

        /* 사이드바 */
        .sidebar {
            width: 280px;
            background: #252526;
            border-right: 1px solid #3e3e42;
            display: flex;
            flex-direction: column;
        }

        .sidebar-header {
            padding: 12px 15px;
            background: #2d2d30;
            border-bottom: 1px solid #3e3e42;
            font-weight: bold;
            font-size: 12px;
            text-transform: uppercase;
            color: #cccccc;
        }

        .file-tree {
            flex: 1;
            overflow-y: auto;
            padding: 8px 0;
        }

        .tree-item {
            display: flex;
            align-items: center;
            padding: 4px 15px;
            cursor: pointer;
            user-select: none;
            font-size: 13px;
            transition: background 0.2s;
        }

        .tree-item:hover {
            background: #2a2d2e;
        }

        .tree-item.selected {
            background: #094771;
            color: #ffffff;
        }

        .tree-item .icon {
            margin-right: 8px;
            width: 16px;
            text-align: center;
        }

        /* 에디터 영역 */
        .editor-area {
            flex: 1;
            display: flex;
            flex-direction: column;
        }

        .editor-container {
            flex: 1;
            position: relative;
        }

        #monaco-editor {
            width: 100%;
            height: 100%;
        }

        .welcome-screen {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            text-align: center;
            color: #8c8c8c;
        }

        .welcome-screen h2 {
            margin-bottom: 20px;
            color: #cccccc;
        }

        /* 하단 패널 */
        .bottom-panel {
            background: #252526;
            border-top: 1px solid #3e3e42;
            height: 200px;
            display: flex;
            flex-direction: column;
        }

        .bottom-panel.collapsed {
            height: 0;
            overflow: hidden;
        }

        .panel-header {
            background: #2d2d30;
            padding: 8px 15px;
            border-bottom: 1px solid #3e3e42;
            font-weight: bold;
            font-size: 12px;
            text-transform: uppercase;
        }

        .terminal {
            flex: 1;
            background: #000000;
            color: #ffffff;
            font-family: 'Consolas', 'Monaco', monospace;
            padding: 10px;
            overflow-y: auto;
            font-size: 13px;
            line-height: 1.4;
            white-space: pre-wrap;
        }

        /* 상태바 */
        .statusbar {
            background: #007acc;
            color: #ffffff;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 15px;
            font-size: 12px;
        }

        .statusbar-left, .statusbar-right {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .status-item {
            cursor: pointer;
            padding: 2px 6px;
            border-radius: 3px;
            transition: background 0.2s;
        }

        .status-item:hover {
            background: rgba(255, 255, 255, 0.1);
        }

        /* 알림 */
        .notification {
            position: fixed;
            top: 60px;
            right: 20px;
            background: #2d2d30;
            border: 1px solid #5a5a5a;
            border-radius: 6px;
            padding: 16px;
            max-width: 320px;
            z-index: 1500;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
            transform: translateX(100%);
            transition: transform 0.3s ease;
        }

        .notification.show {
            transform: translateX(0);
        }

        .notification.success {
            border-left: 4px solid #28a745;
        }

        .notification.error {
            border-left: 4px solid #dc3545;
        }

        .notification.warning {
            border-left: 4px solid #ffc107;
        }

        .notification.info {
            border-left: 4px solid #17a2b8;
        }

        /* 스크롤바 */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #2d2d30;
        }

        ::-webkit-scrollbar-thumb {
            background: #5a5a5a;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #6a6a6a;
        }
    </style>
</head>
<body>
    <div class="ide-container">
        <!-- 상단 메뉴바 -->
        <div class="menubar">
            <div class="logo">Pathfinder Web IDE v3</div>
            <div class="menu-buttons">
                <button class="menu-btn" onclick="saveCurrentFile()" id="saveBtn" disabled>💾 저장</button>
                <button class="menu-btn" onclick="runCode()" id="runBtn" disabled>▶️ 실행</button>
                <button class="menu-btn danger" onclick="stopExecution()" id="stopBtn" disabled>⏹️ 중지</button>
            </div>
        </div>

        <!-- 메인 영역 -->
        <div class="main-area">
            <!-- 사이드바 -->
            <div class="sidebar">
                <div class="sidebar-header">파일 탐색기</div>
                <div class="file-tree" id="fileTree">
                    <!-- 파일 트리가 여기에 로드됩니다 -->
                </div>
            </div>

            <!-- 에디터 영역 -->
            <div class="editor-area">
                <!-- 에디터 컨테이너 -->
                <div class="editor-container">
                    <div class="welcome-screen" id="welcomeScreen">
                        <h2>🚀 Pathfinder Web IDE v3</h2>
                        <p>파일을 선택하여 편집을 시작하세요</p>
                        <div style="margin-top: 30px; color: #666;">
                            <div>💡 <kbd>Ctrl+S</kbd> 파일 저장</div>
                            <div>⚡ <kbd>F5</kbd> 코드 실행</div>
                        </div>
                    </div>
                    <div id="monaco-editor" style="display: none;"></div>
                </div>
            </div>
        </div>

        <!-- 하단 패널 -->
        <div class="bottom-panel collapsed" id="bottomPanel">
            <div class="panel-header">터미널 출력</div>
            <div class="terminal" id="terminal"></div>
        </div>

        <!-- 상태바 -->
        <div class="statusbar">
            <div class="statusbar-left">
                <div class="status-item">🌿 main</div>
                <div class="status-item" id="statusFile">파일 없음</div>
            </div>
            <div class="statusbar-right">
                <div class="status-item" id="statusLanguage">-</div>
                <div class="status-item" id="statusPosition">Ln 1, Col 1</div>
                <div class="status-item" onclick="toggleBottomPanel()">📟 터미널</div>
            </div>
        </div>
    </div>

    <script>
        // 전역 변수
        let monaco;
        let editor;
        let socket;
        let sessionId = null;
        let currentFile = null;
        let isModified = false;
        let isRunning = false;

        // 초기화
        document.addEventListener('DOMContentLoaded', function() {
            initializeIDE();
        });

        async function initializeIDE() {
            try {
                console.log('🚀 IDE 초기화 시작...');
                
                // Monaco Editor 초기화
                await initializeMonaco();
                
                // Socket.IO 연결
                setTimeout(() => {
                    connectSocket();
                }, 1000);
                
                // 파일 트리 로드
                setTimeout(() => {
                    loadFileTree();
                }, 500);
                
                showNotification('IDE가 초기화되었습니다', 'success');
                
            } catch (error) {
                console.error('❌ IDE 초기화 오류:', error);
                showNotification(`IDE 초기화 실패: ${error.message}`, 'error');
            }
        }

        // Monaco Editor 초기화
        async function initializeMonaco() {
            return new Promise((resolve, reject) => {
                require.config({ 
                    paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs' }
                });
                
                require(['vs/editor/editor.main'], function() {
                    try {
                        monaco = window.monaco;
                        
                        // 다크 테마 설정
                        monaco.editor.defineTheme('pathfinder-dark', {
                            base: 'vs-dark',
                            inherit: true,
                            rules: [],
                            colors: {
                                'editor.background': '#1e1e1e',
                                'editor.foreground': '#cccccc'
                            }
                        });

                        // 에디터 생성
                        editor = monaco.editor.create(document.getElementById('monaco-editor'), {
                            value: '',
                            language: 'python',
                            theme: 'pathfinder-dark',
                            automaticLayout: true,
                            fontSize: 14,
                            lineNumbers: 'on',
                            minimap: { enabled: true },
                            scrollBeyondLastLine: false,
                            wordWrap: 'on',
                            tabSize: 4,
                            insertSpaces: true
                        });

                        // 에디터 이벤트
                        editor.onDidChangeModelContent(() => {
                            if (currentFile && !isModified) {
                                setModified(true);
                            }
                        });

                        editor.onDidChangeCursorPosition((e) => {
                            updateStatusPosition(e.position.lineNumber, e.position.column);
                        });
                        
                        // 키보드 단축키
                        editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
                            saveCurrentFile();
                        });
                        
                        editor.addCommand(monaco.KeyCode.F5, () => {
                            runCode();
                        });
                        
                        resolve();
                        
                    } catch (error) {
                        reject(error);
                    }
                });
            });
        }

        // WebSocket 연결
        function connectSocket() {
            try {
                if (typeof io === 'undefined') {
                    console.error('❌ Socket.IO 라이브러리가 로드되지 않았습니다');
                    showNotification('Socket.IO 라이브러리 로드 실패', 'error');
                    return;
                }
                
                socket = io({
                    transports: ['websocket', 'polling'],
                    timeout: 20000,
                    forceNew: true,
                    autoConnect: true,
                    reconnection: true,
                    reconnectionAttempts: 10,
                    reconnectionDelay: 1000,
                    reconnectionDelayMax: 5000,
                    maxReconnectionAttempts: 10,
                    pingTimeout: 60000,
                    pingInterval: 25000
                });
                
                sessionId = generateSessionId();

                socket.on('connect', function() {
                    console.log('🔗 WebSocket 연결됨 (ID: ' + socket.id + ')');
                    socket.emit('join_session', { session_id: sessionId });
                    showNotification('서버에 연결되었습니다', 'success');
                });

                socket.on('disconnect', function(reason) {
                    console.log('🔌 WebSocket 연결 해제됨:', reason);
                    showNotification('서버 연결이 끊어졌습니다', 'warning');
                });

                // 실행 관련 이벤트
                socket.on('execution_started', function(data) {
                    console.log('🚀 실행 시작:', data);
                    showBottomPanel();
                    appendToTerminal(`${data.message}\n`);
                    updateRunButtons(true);
                    isRunning = true;
                });

                socket.on('code_output', function(data) {
                    appendToTerminal(data.output + '\n');
                });

                socket.on('execution_completed', function(data) {
                    console.log('✅ 실행 완료:', data);
                    appendToTerminal(`\n${data.message}\n`);
                    updateRunButtons(false);
                    isRunning = false;
                });

                socket.on('execution_stopped', function(data) {
                    console.log('⏹️ 실행 중지:', data);
                    appendToTerminal(`\n${data.message}\n`);
                    updateRunButtons(false);
                    isRunning = false;
                });

                socket.on('execution_error', function(data) {
                    console.log('❌ 실행 에러:', data);
                    appendToTerminal(`\n❌ ${data.error}\n`);
                    updateRunButtons(false);
                    isRunning = false;
                });
                
            } catch (error) {
                console.error('❌ Socket 초기화 오류:', error);
                showNotification('WebSocket 초기화 실패: ' + error.message, 'error');
            }
        }

        function generateSessionId() {
            return 'session_' + Math.random().toString(36).substr(2, 9);
        }

        // 파일 트리 로드
        async function loadFileTree() {
            try {
                const response = await fetch('/api/files');
                const result = await response.json();
                
                if (result.success) {
                    renderFileTree(result.data);
                } else {
                    throw new Error(result.error);
                }
            } catch (error) {
                console.error('파일 트리 로드 오류:', error);
                showNotification('파일 트리를 로드할 수 없습니다', 'error');
            }
        }

        function renderFileTree(items) {
            const fileTreeEl = document.getElementById('fileTree');
            
            if (!items || items.length === 0) {
                fileTreeEl.innerHTML = '<div style="padding: 20px; text-align: center; color: #8c8c8c;">파일이 없습니다</div>';
                return;
            }
            
            fileTreeEl.innerHTML = renderTreeItems(items);
        }

        function renderTreeItems(items) {
            return items.map(item => {
                const icon = getFileIcon(item);
                
                return `
                    <div class="tree-item" 
                         data-path="${item.path}" 
                         data-type="${item.type}"
                         onclick="selectTreeItem('${item.path}', '${item.type}')"
                         ondblclick="openTreeItem('${item.path}', '${item.type}')">
                        <span class="icon">${icon}</span>
                        <span class="name">${item.name}</span>
                    </div>
                `;
            }).join('');
        }

        function getFileIcon(item) {
            if (item.type === 'folder') return '📁';
            
            const ext = item.extension || '';
            const iconMap = {
                '.py': '🐍',
                '.js': '📜',
                '.html': '🌐',
                '.css': '🎨',
                '.json': '📋',
                '.md': '📝',
                '.txt': '📄'
            };
            
            return iconMap[ext] || '📄';
        }

        function selectTreeItem(path, type) {
            document.querySelectorAll('.tree-item.selected').forEach(el => {
                el.classList.remove('selected');
            });
            
            const element = document.querySelector(`[data-path="${path}"]`);
            if (element) {
                element.classList.add('selected');
            }
        }

        function openTreeItem(path, type) {
            if (type === 'file') {
                openFile(path);
            }
        }

        // 파일 열기
        async function openFile(filepath) {
            try {
                const response = await fetch(`/api/file/${encodeURIComponent(filepath)}`);
                const result = await response.json();
                
                if (result.success) {
                    const fileData = result.data;
                    
                    // 에디터에 내용 설정
                    setEditorContent(fileData.content, filepath);
                    
                    // 현재 파일 설정
                    currentFile = filepath;
                    setModified(false);
                    
                    // UI 업데이트
                    updateStatusFile(filepath);
                    updateLanguage(filepath);
                    
                    showNotification(`파일 "${filepath}"를 열었습니다`, 'success');
                } else {
                    throw new Error(result.error);
                }
            } catch (error) {
                console.error('파일 열기 오류:', error);
                showNotification(`파일을 열 수 없습니다: ${error.message}`, 'error');
            }
        }

        function setEditorContent(content, filepath) {
            if (!editor) return;
            
            // 언어 설정
            const language = getLanguageFromPath(filepath);
            const model = monaco.editor.createModel(content, language);
            editor.setModel(model);
            
            // Welcome 화면 숨기기
            document.getElementById('welcomeScreen').style.display = 'none';
            document.getElementById('monaco-editor').style.display = 'block';
            
            // 실행 버튼 활성화 (Python 파일인 경우)
            document.getElementById('runBtn').disabled = !filepath.endsWith('.py') || isRunning;
        }

        function getLanguageFromPath(filepath) {
            const ext = filepath.split('.').pop().toLowerCase();
            const languageMap = {
                'py': 'python',
                'js': 'javascript',
                'html': 'html',
                'css': 'css',
                'json': 'json',
                'md': 'markdown'
            };
            return languageMap[ext] || 'plaintext';
        }

        // 파일 저장
        async function saveCurrentFile() {
            if (!currentFile || !editor) {
                showNotification('저장할 파일이 없습니다', 'warning');
                return;
            }

            try {
                const content = editor.getValue();
                
                const response = await fetch(`/api/file/${encodeURIComponent(currentFile)}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ content })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    setModified(false);
                    showNotification('파일이 저장되었습니다', 'success');
                } else {
                    throw new Error(result.error);
                }
            } catch (error) {
                console.error('파일 저장 오류:', error);
                showNotification(`파일 저장 실패: ${error.message}`, 'error');
            }
        }

        // 코드 실행 (스마트 실시간)
        function runCode() {
            if (!editor) {
                showNotification('에디터가 로드되지 않았습니다', 'warning');
                return;
            }
            
            const code = editor.getValue();
            if (!code.trim()) {
                showNotification('실행할 코드가 없습니다', 'warning');
                return;
            }
            
            console.log('🚀 스마트 코드 실행 시작:', code.length, '문자');
            
            if (socket && socket.connected) {
                clearTerminal();
                socket.emit('execute_code', { code: code });
                showNotification('코드 실행을 시작했습니다', 'info');
            } else {
                showNotification('서버에 연결되지 않았습니다', 'error');
            }
        }

        // 실행 중지
        function stopExecution() {
            if (socket && socket.connected) {
                socket.emit('stop_execution');
                showNotification('실행을 중지했습니다', 'info');
            } else {
                showNotification('서버에 연결되지 않았습니다', 'error');
            }
        }

        function updateRunButtons(isRunning) {
            document.getElementById('runBtn').disabled = isRunning || !currentFile || !currentFile.endsWith('.py');
            document.getElementById('stopBtn').disabled = !isRunning;
        }

        function setModified(modified) {
            isModified = modified;
            document.getElementById('saveBtn').disabled = !modified || !currentFile;
        }

        // 터미널 관리
        function showBottomPanel() {
            document.getElementById('bottomPanel').classList.remove('collapsed');
        }

        function toggleBottomPanel() {
            const panel = document.getElementById('bottomPanel');
            panel.classList.toggle('collapsed');
        }

        function clearTerminal() {
            document.getElementById('terminal').textContent = '';
        }

        function appendToTerminal(text) {
            const terminal = document.getElementById('terminal');
            terminal.textContent += text;
            terminal.scrollTop = terminal.scrollHeight;
        }

        // UI 업데이트
        function updateStatusFile(filename) {
            document.getElementById('statusFile').textContent = filename;
        }

        function updateLanguage(filepath) {
            const language = getLanguageFromPath(filepath);
            const languageNames = {
                'python': 'Python',
                'javascript': 'JavaScript',
                'html': 'HTML',
                'css': 'CSS',
                'json': 'JSON',
                'markdown': 'Markdown',
                'plaintext': 'Text'
            };
            
            document.getElementById('statusLanguage').textContent = languageNames[language] || 'Text';
        }

        function updateStatusPosition(line, column) {
            document.getElementById('statusPosition').textContent = `Ln ${line}, Col ${column}`;
        }

        // 알림 시스템
        function showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.classList.add('show');
            }, 100);
            
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }, 3000);
        }
    </script>
</body>
</html> 
'''


if __name__ == '__main__':
    print("🚀 Pathfinder Web IDE v3 시작!")
    print(f"📁 프로젝트 디렉토리: {CONFIG['project_dir']}")
    print("🌐 브라우저에서 http://라즈베리파이IP:5000 으로 접속하세요")
    print("⚡ 스마트 실시간 코드 실행 시스템")
    print("🔄 자동 프로세스 종료 감지")
    print(f"🔧 비동기 모드: eventlet")
    print(f"🌍 CORS: 모든 도메인 허용")
    print(f"📡 Ping 간격: 25초, 타임아웃: 60초")
    print(f"🔒 보안: 경로 검증, 파일 크기 제한, 실행 시간 제한")
    print("-" * 60)
    
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=5000, 
        debug=False,  # eventlet에서는 debug=False 권장
        use_reloader=False  # eventlet에서는 reloader 비활성화
    ) 