#!/usr/bin/env python3
"""
Pathfinder Web IDE v2 - Flask-SocketIO 기반 실시간 웹 IDE
라즈베리파이 원격 개발을 위한 안정적이고 보안이 강화된 IDE

주요 기능:
- 실시간 코드 편집 (Monaco Editor)
- WebSocket 기반 실시간 코드 실행
- 파일/폴더 관리
- 터미널 출력 스트리밍
- 무한루프 코드 실시간 실행 및 제어 지원
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
running_processes = {}  # 파일 기반 실행 중인 프로세스들
realtime_processes = {}  # 실시간 실행 중인 프로세스들

class RealTimeExecutor:
    """실시간 코드 실행 관리 클래스 (flask_socketio_fixed.py에서 가져옴)"""
    
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

class FileManager:
    """파일 시스템 관리 클래스 - 보안 강화"""
    
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
        """경로 안전성 검사 - 보안 강화"""
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

class CodeRunner:
    """WebSocket 기반 코드 실행 관리 클래스 - 보안 및 안정성 강화"""
    
    @staticmethod
    def start_execution(filepath, session_id):
        """Python 파일 WebSocket 스트리밍 실행 (파일 기반)"""
        try:
            # 기존 프로세스가 있으면 종료
            if filepath in running_processes:
                CodeRunner.stop_execution(filepath)
            
            # 파일 존재 및 확장자 확인
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {filepath}")
            
            if not filepath.endswith('.py'):
                raise ValueError("Python 파일만 실행할 수 있습니다")
            
            # 새 프로세스 시작 (보안 강화)
            python_cmd = 'python' if os.name == 'nt' else 'python3'
            
            # 작업 디렉토리 설정
            work_dir = os.path.dirname(filepath) if os.path.dirname(filepath) else CONFIG['project_dir']
            
            process = subprocess.Popen(
                [python_cmd, '-u', os.path.basename(filepath)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=0,
                cwd=work_dir,
                # 보안 강화: 환경 변수 제한
                env={
                    'PATH': os.environ.get('PATH', ''),
                    'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
                    'HOME': os.environ.get('HOME', ''),
                    'USER': os.environ.get('USER', ''),
                }
            )
            
            running_processes[filepath] = {
                'process': process,
                'session_id': session_id,
                'start_time': time.time(),
                'type': 'file'  # 파일 기반 실행 표시
            }
            
            # 출력 모니터링 스레드 시작
            monitor_thread = threading.Thread(
                target=CodeRunner._monitor_output,
                args=(filepath, process, session_id),
                daemon=True
            )
            monitor_thread.start()
            
            # 시작 메시지 전송
            socketio.emit('execution_started', {
                'filepath': filepath,
                'pid': process.pid,
                'message': f'🚀 프로세스 시작됨 (PID: {process.pid})',
                'type': 'file'
            }, room=session_id)
            
            logger.info(f"파일 실행 시작: {filepath} (PID: {process.pid})")
            return {'success': True, 'pid': process.pid}
            
        except Exception as e:
            error_msg = f'❌ 실행 오류: {str(e)}'
            logger.error(f"코드 실행 실패: {filepath} - {e}")
            
            socketio.emit('execution_error', {
                'filepath': filepath,
                'error': error_msg,
                'type': 'file'
            }, room=session_id)
            
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _monitor_output(filepath, process, session_id):
        """프로세스 출력을 실시간으로 모니터링 - 타임아웃 추가"""
        try:
            start_time = time.time()
            
            while True:
                # 실행 시간 제한 확인
                if time.time() - start_time > CONFIG['max_execution_time']:
                    logger.warning(f"실행 시간 초과: {filepath}")
                    process.terminate()
                    socketio.emit('execution_error', {
                        'filepath': filepath,
                        'error': f'❌ 실행 시간 초과 ({CONFIG["max_execution_time"]}초)',
                        'type': 'file'
                    }, room=session_id)
                    break
                
                # 프로세스 종료 확인
                if process.poll() is not None:
                    # 남은 출력 읽기
                    try:
                        remaining = process.stdout.read()
                        if remaining:
                            socketio.emit('execution_output', {
                                'filepath': filepath,
                                'output': remaining,
                                'type': 'file'
                            }, room=session_id)
                    except:
                        pass
                    
                    # 종료 메시지 전송
                    socketio.emit('execution_finished', {
                        'filepath': filepath,
                        'exit_code': process.returncode,
                        'message': f'✅ 프로세스 종료됨 (종료 코드: {process.returncode})',
                        'type': 'file'
                    }, room=session_id)
                    
                    logger.info(f"파일 실행 완료: {filepath} (종료 코드: {process.returncode})")
                    break
                
                # 새로운 출력 읽기
                try:
                    line = process.stdout.readline()
                    if line:
                        socketio.emit('execution_output', {
                            'filepath': filepath,
                            'output': line,
                            'type': 'file'
                        }, room=session_id)
                    else:
                        time.sleep(0.01)  # 10ms 대기
                        
                except Exception as e:
                    logger.error(f"출력 읽기 오류: {e}")
                    socketio.emit('execution_error', {
                        'filepath': filepath,
                        'error': f'❌ 출력 읽기 오류: {str(e)}',
                        'type': 'file'
                    }, room=session_id)
                    break
                    
        except Exception as e:
            logger.error(f"모니터링 오류: {e}")
            socketio.emit('execution_error', {
                'filepath': filepath,
                'error': f'❌ 모니터링 오류: {str(e)}',
                'type': 'file'
            }, room=session_id)
        finally:
            # 정리
            if filepath in running_processes:
                del running_processes[filepath]
    
    @staticmethod
    def stop_execution(filepath):
        """파일 실행 중지 - 강제 종료 개선"""
        try:
            if filepath in running_processes:
                process_info = running_processes[filepath]
                process = process_info['process']
                session_id = process_info['session_id']
                
                # 프로세스 종료 (단계적)
                process.terminate()
                try:
                    process.wait(timeout=5)  # 5초 대기
                except subprocess.TimeoutExpired:
                    logger.warning(f"프로세스 강제 종료: {filepath}")
                    process.kill()
                    process.wait()
                
                # 중지 메시지 전송
                socketio.emit('execution_stopped', {
                    'filepath': filepath,
                    'message': '⏹️ 실행이 중지되었습니다',
                    'type': 'file'
                }, room=session_id)
                
                logger.info(f"파일 실행 중지: {filepath}")
                
                # 정리
                del running_processes[filepath]
                
                return {'success': True}
            else:
                return {'success': False, 'error': '실행 중인 프로세스가 없습니다'}
                
        except Exception as e:
            logger.error(f"실행 중지 오류: {e}")
            return {'success': False, 'error': str(e)}

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
    """파일 내용 읽기 - 보안 강화"""
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
    """파일 저장 - 보안 강화"""
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
    """파일/폴더 생성 - 보안 강화"""
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
    """파일/폴더 삭제 - 보안 강화"""
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

@app.route('/api/rename', methods=['POST'])
def rename_item():
    """파일/폴더 이름 변경 - 보안 강화"""
    try:
        data = request.get_json()
        if not data or 'old_path' not in data or 'new_path' not in data:
            return jsonify({'success': False, 'error': '잘못된 요청 데이터'}), 400
        
        old_path = data.get('old_path', '')
        new_path = data.get('new_path', '')
        
        if not FileManager.is_safe_path(old_path) or not FileManager.is_safe_path(new_path):
            return jsonify({'success': False, 'error': '접근 권한이 없습니다'}), 403
        
        old_full_path = os.path.join(CONFIG['project_dir'], old_path)
        new_full_path = os.path.join(CONFIG['project_dir'], new_path)
        
        if not os.path.exists(old_full_path):
            return jsonify({'success': False, 'error': '원본 파일을 찾을 수 없습니다'}), 404
        
        if os.path.exists(new_full_path):
            return jsonify({'success': False, 'error': '대상 경로에 이미 파일이 존재합니다'}), 409
        
        # 파일인 경우 확장자 확인
        if os.path.isfile(old_full_path):
            ext = os.path.splitext(new_path)[1].lower()
            if ext and ext not in CONFIG['allowed_extensions']:
                return jsonify({'success': False, 'error': '지원하지 않는 파일 형식입니다'}), 400
        
        os.makedirs(os.path.dirname(new_full_path), exist_ok=True)
        os.rename(old_full_path, new_full_path)
        
        logger.info(f"이름 변경: {old_path} -> {new_path}")
        return jsonify({'success': True, 'message': '이름이 변경되었습니다'})
        
    except PermissionError:
        return jsonify({'success': False, 'error': '이름 변경 권한이 없습니다'}), 403
    except Exception as e:
        logger.error(f"이름 변경 오류: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/run/<path:filepath>', methods=['POST'])
def run_file(filepath):
    """파일 실행 - 보안 강화"""
    try:
        if not FileManager.is_safe_path(filepath):
            return jsonify({'success': False, 'error': '접근 권한이 없습니다'}), 403
        
        full_path = os.path.join(CONFIG['project_dir'], filepath)
        
        if not os.path.exists(full_path):
            return jsonify({'success': False, 'error': '파일을 찾을 수 없습니다'}), 404
        
        if not filepath.endswith('.py'):
            return jsonify({'success': False, 'error': 'Python 파일만 실행할 수 있습니다'}), 400
        
        data = request.get_json() or {}
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({'success': False, 'error': '세션 ID가 필요합니다'}), 400
        
        result = CodeRunner.start_execution(full_path, session_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"실행 오류: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stop/<path:filepath>', methods=['POST'])
def stop_execution(filepath):
    """실행 중지"""
    try:
        if not FileManager.is_safe_path(filepath):
            return jsonify({'success': False, 'error': '접근 권한이 없습니다'}), 403
        
        full_path = os.path.join(CONFIG['project_dir'], filepath)
        result = CodeRunner.stop_execution(full_path)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"중지 오류: {e}")
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
    
    # 해당 세션의 파일 기반 실행 중인 프로세스들 정리
    processes_to_stop = []
    for filepath, process_info in running_processes.items():
        if process_info['session_id'] == request.sid:
            processes_to_stop.append(filepath)
    
    for filepath in processes_to_stop:
        CodeRunner.stop_execution(filepath)
    
    # 해당 세션의 실시간 실행 중인 프로세스들 정리
    if request.sid in realtime_processes:
        realtime_processes[request.sid].stop_execution()
        del realtime_processes[request.sid]

@socketio.on('join_session')
def handle_join_session(data):
    """세션 참가"""
    session_id = data.get('session_id', request.sid)
    join_room(session_id)
    emit('session_joined', {'session_id': session_id})
    logger.info(f"세션 참가: {session_id}")

# ==================== 실시간 코드 실행 이벤트 핸들러 ====================

@socketio.on('execute_realtime')
def handle_execute_realtime(data):
    """실시간 코드 실행 (임시 파일 기반)"""
    session_id = request.sid
    code = data.get('code', '')
    
    logger.info(f"📝 실시간 코드 실행 요청: {len(code)} 문자 (세션: {session_id})")
    
    # 기존 실행 중인 프로세스가 있으면 중지
    if session_id in realtime_processes:
        realtime_processes[session_id].stop_execution()
        del realtime_processes[session_id]
    
    # 새 실행기 생성
    executor = RealTimeExecutor(session_id)
    realtime_processes[session_id] = executor
    
    emit('execution_started', {
        'message': '실시간 실행 시작...',
        'timestamp': datetime.now().isoformat(),
        'type': 'realtime'
    })
    
    # 코드 실행
    success = executor.execute_code(code)
    if not success:
        if session_id in realtime_processes:
            del realtime_processes[session_id]

@socketio.on('stop_realtime_execution')
def handle_stop_realtime_execution():
    """실시간 실행 중지"""
    session_id = request.sid
    
    if session_id in realtime_processes:
        success = realtime_processes[session_id].stop_execution()
        if success:
            del realtime_processes[session_id]
        return success
    else:
        emit('execution_error', {
            'error': '실행 중인 프로세스가 없습니다',
            'timestamp': datetime.now().isoformat(),
            'type': 'realtime'
        })
        return False

@socketio.on('execute_code')
def handle_execute_code(data):
    """일반 코드 실행 (기존 기능 유지 - 메모리 내 실행)"""
    code = data.get('code', '')
    logger.info(f"📝 일반 코드 실행 요청: {len(code)} 문자")
    
    emit('execution_start', {
        'message': '코드 실행 중...',
        'timestamp': datetime.now().isoformat(),
        'type': 'memory'
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
            'timestamp': datetime.now().isoformat(),
            'type': 'memory'
        })
        
        logger.info(f"✅ 일반 코드 실행 성공")
        
    except Exception as e:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        emit('execution_result', {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'timestamp': datetime.now().isoformat(),
            'type': 'memory'
        })
        
        logger.error(f"❌ 일반 코드 실행 오류: {e}")

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
    print("🚀 Pathfinder Web IDE v2 시작!")
    print(f"📁 프로젝트 디렉토리: {CONFIG['project_dir']}")
    print("🌐 브라우저에서 http://라즈베리파이IP:5000 으로 접속하세요")
    print("⚡ WebSocket 실시간 스트리밍 지원")
    print("🔄 무한루프 코드 실시간 실행 및 제어 지원")
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