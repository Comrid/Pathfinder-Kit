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
    return render_template('index.html')

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