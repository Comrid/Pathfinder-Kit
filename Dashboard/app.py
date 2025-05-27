"""
Pathfinder Web IDE - 간단하고 안정적인 웹 기반 코드 편집기
라즈베리파이 원격 개발을 위한 최소 기능 IDE
"""

from flask import Flask, request, render_template, jsonify
import subprocess
import os
import shutil
import json
from datetime import datetime

app = Flask(__name__)

# 설정
CONFIG = {
    'project_dir': os.path.expanduser("~"),
    'max_file_size': 5 * 1024 * 1024,  # 5MB
    'allowed_extensions': {
        '.py', '.txt', '.md', '.json', '.yaml', '.yml', 
        '.html', '.css', '.js', '.sh', '.cfg', '.ini'
    },
    'excluded_dirs': {'.git', '__pycache__', '.vscode', 'node_modules', '.DS_Store'}
}

# 전역 변수
running_processes = {}

class FileManager:
    """파일 시스템 관리 클래스"""
    
    @staticmethod
    def get_file_tree(path, max_depth=2, current_depth=0):
        """파일 트리 구조 생성"""
        if current_depth > max_depth:
            return []
        
        tree = []
        try:
            if not os.path.exists(path):
                return tree
                
            items = sorted(os.listdir(path))
            
            # 폴더 먼저, 파일 나중에
            folders = []
            files = []
            
            for item in items:
                if item.startswith('.'):
                    continue
                    
                item_path = os.path.join(path, item)
                
                # 상대 경로 계산
                try:
                    rel_path = os.path.relpath(item_path, CONFIG['project_dir'])
                    rel_path = rel_path.replace('\\', '/')
                    if rel_path == '.':
                        rel_path = item
                except ValueError:
                    rel_path = item_path.replace('\\', '/')
                
                if os.path.isdir(item_path):
                    if item not in CONFIG['excluded_dirs']:
                        folder_data = {
                            'name': item,
                            'type': 'folder',
                            'path': rel_path,
                            'children': []
                        }
                        
                        # 첫 번째 레벨만 자동 로드
                        if current_depth == 0:
                            folder_data['children'] = FileManager.get_file_tree(
                                item_path, max_depth, current_depth + 1
                            )
                        
                        folders.append(folder_data)
                else:
                    try:
                        file_ext = os.path.splitext(item)[1].lower()
                        file_size = os.path.getsize(item_path)
                        
                        files.append({
                            'name': item,
                            'type': 'file',
                            'path': rel_path,
                            'extension': file_ext,
                            'size': file_size,
                            'modified': datetime.fromtimestamp(os.path.getmtime(item_path)).isoformat(),
                            'language': FileManager.get_language(file_ext)
                        })
                    except (OSError, PermissionError):
                        continue
            
            tree.extend(folders)
            tree.extend(files)
            
        except PermissionError:
            print(f"Permission denied: {path}")
        except Exception as e:
            print(f"Error reading directory {path}: {e}")
        
        return tree
    
    @staticmethod
    def get_language(extension):
        """파일 확장자로 언어 감지"""
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.md': 'markdown',
            '.sh': 'bash',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.txt': 'plaintext'
        }
        return lang_map.get(extension, 'plaintext')

class CodeRunner:
    """코드 실행 관리 클래스"""
    
    @staticmethod
    def run_python_file(filepath, timeout=30):
        """Python 파일 실행"""
        try:
            process = subprocess.Popen(
                ['python3', filepath],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=os.path.dirname(filepath)
            )
            
            try:
                output, _ = process.communicate(timeout=timeout)
                return {
                    'success': True,
                    'output': output,
                    'exit_code': process.returncode
                }
            except subprocess.TimeoutExpired:
                process.kill()
                return {
                    'success': False,
                    'output': f"⏰ 실행 시간 초과 ({timeout}초)",
                    'exit_code': -1
                }
                
        except Exception as e:
            return {
                'success': False,
                'output': f"❌ 실행 오류: {str(e)}",
                'exit_code': -1
            }

# 라우트 정의
@app.route('/')
def index():
    """메인 페이지"""
    return render_template('ide.html')

@app.route('/api/files')
def get_files():
    """파일 트리 API"""
    try:
        tree = FileManager.get_file_tree(CONFIG['project_dir'])
        return jsonify({
            'success': True,
            'data': tree,
            'root': CONFIG['project_dir']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/file/<path:filepath>')
def get_file_content(filepath):
    """파일 내용 읽기"""
    try:
        full_path = os.path.join(CONFIG['project_dir'], filepath)
        
        # 보안 검사
        if not os.path.commonpath([full_path, CONFIG['project_dir']]) == CONFIG['project_dir']:
            return jsonify({'success': False, 'error': '접근 권한이 없습니다'}), 403
        
        if not os.path.exists(full_path):
            return jsonify({'success': False, 'error': '파일을 찾을 수 없습니다'}), 404
        
        # 파일 크기 검사
        if os.path.getsize(full_path) > CONFIG['max_file_size']:
            return jsonify({'success': False, 'error': '파일이 너무 큽니다'}), 413
        
        # 파일 읽기
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            return jsonify({'success': False, 'error': '바이너리 파일은 편집할 수 없습니다'}), 400
        
        file_info = {
            'content': content,
            'size': os.path.getsize(full_path),
            'modified': datetime.fromtimestamp(os.path.getmtime(full_path)).isoformat(),
            'language': FileManager.get_language(os.path.splitext(filepath)[1]),
            'readonly': not os.access(full_path, os.W_OK)
        }
        
        return jsonify({
            'success': True,
            'data': file_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/file/<path:filepath>', methods=['POST'])
def save_file_content(filepath):
    """파일 저장"""
    try:
        full_path = os.path.join(CONFIG['project_dir'], filepath)
        
        # 보안 검사
        if not os.path.commonpath([full_path, CONFIG['project_dir']]) == CONFIG['project_dir']:
            return jsonify({'success': False, 'error': '접근 권한이 없습니다'}), 403
        
        data = request.get_json()
        content = data.get('content', '')
        
        # 디렉토리 생성
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # 파일 저장
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            'success': True,
            'message': '파일이 저장되었습니다'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/run/<path:filepath>', methods=['POST'])
def run_file(filepath):
    """파일 실행"""
    try:
        full_path = os.path.join(CONFIG['project_dir'], filepath)
        
        # 보안 검사
        if not os.path.commonpath([full_path, CONFIG['project_dir']]) == CONFIG['project_dir']:
            return jsonify({'success': False, 'error': '접근 권한이 없습니다'}), 403
        
        if not os.path.exists(full_path):
            return jsonify({'success': False, 'error': '파일을 찾을 수 없습니다'}), 404
        
        # 파일 확장자 확인
        ext = os.path.splitext(filepath)[1].lower()
        if ext != '.py':
            return jsonify({'success': False, 'error': 'Python 파일만 실행할 수 있습니다'}), 400
        
        # 실행
        result = CodeRunner.run_python_file(full_path)
        
        return jsonify({
            'success': result['success'],
            'output': result['output'],
            'exit_code': result['exit_code']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/create', methods=['POST'])
def create_file_or_folder():
    """파일/폴더 생성"""
    try:
        data = request.get_json()
        path = data.get('path', '').strip()
        is_folder = data.get('is_folder', False)
        
        if not path:
            return jsonify({'success': False, 'error': '경로를 입력하세요'}), 400
        
        # 경로 정규화
        path = path.replace('\\', '/')
        if path.startswith('/'):
            path = path[1:]
        
        full_path = os.path.join(CONFIG['project_dir'], path)
        
        # 보안 검사
        try:
            if not os.path.commonpath([full_path, CONFIG['project_dir']]) == CONFIG['project_dir']:
                return jsonify({'success': False, 'error': '접근 권한이 없습니다'}), 403
        except ValueError:
            return jsonify({'success': False, 'error': '잘못된 경로입니다'}), 400
        
        if os.path.exists(full_path):
            return jsonify({'success': False, 'error': '이미 존재합니다'}), 409
        
        try:
            if is_folder:
                os.makedirs(full_path, exist_ok=True)
                message = f'폴더 "{os.path.basename(path)}"가 생성되었습니다'
            else:
                # 상위 디렉토리 생성
                parent_dir = os.path.dirname(full_path)
                if parent_dir and parent_dir != CONFIG['project_dir']:
                    os.makedirs(parent_dir, exist_ok=True)
                
                # 파일 생성
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write('')
                message = f'파일 "{os.path.basename(path)}"가 생성되었습니다'
            
            return jsonify({
                'success': True,
                'message': message,
                'path': path
            })
            
        except PermissionError:
            return jsonify({'success': False, 'error': '권한이 없습니다'}), 403
        except OSError as e:
            return jsonify({'success': False, 'error': f'생성 실패: {str(e)}'}), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/delete/<path:filepath>', methods=['DELETE'])
def delete_file_or_folder(filepath):
    """파일/폴더 삭제"""
    try:
        full_path = os.path.join(CONFIG['project_dir'], filepath)
        
        # 보안 검사
        if not os.path.commonpath([full_path, CONFIG['project_dir']]) == CONFIG['project_dir']:
            return jsonify({'success': False, 'error': '접근 권한이 없습니다'}), 403
        
        if not os.path.exists(full_path):
            return jsonify({'success': False, 'error': '파일을 찾을 수 없습니다'}), 404
        
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
            message = '폴더가 삭제되었습니다'
        else:
            os.remove(full_path)
            message = '파일이 삭제되었습니다'
        
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/rename', methods=['POST'])
def rename_file_or_folder():
    """파일/폴더 이름 변경"""
    try:
        data = request.get_json()
        old_path = data.get('old_path', '')
        new_path = data.get('new_path', '')
        
        old_full_path = os.path.join(CONFIG['project_dir'], old_path)
        new_full_path = os.path.join(CONFIG['project_dir'], new_path)
        
        # 보안 검사
        if not (os.path.commonpath([old_full_path, CONFIG['project_dir']]) == CONFIG['project_dir'] and
                os.path.commonpath([new_full_path, CONFIG['project_dir']]) == CONFIG['project_dir']):
            return jsonify({'success': False, 'error': '접근 권한이 없습니다'}), 403
        
        if not os.path.exists(old_full_path):
            return jsonify({'success': False, 'error': '원본 파일을 찾을 수 없습니다'}), 404
        
        if os.path.exists(new_full_path):
            return jsonify({'success': False, 'error': '대상 경로에 이미 파일이 존재합니다'}), 409
        
        # 새 경로의 디렉토리 생성
        os.makedirs(os.path.dirname(new_full_path), exist_ok=True)
        
        # 이름 변경
        os.rename(old_full_path, new_full_path)
        
        return jsonify({
            'success': True,
            'message': '이름이 변경되었습니다'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 에러 핸들러
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'API 엔드포인트를 찾을 수 없습니다'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': '서버 내부 오류가 발생했습니다'}), 500

if __name__ == '__main__':
    print("🚀 Pathfinder Web IDE 시작!")
    print(f"📁 프로젝트 디렉토리: {CONFIG['project_dir']}")
    print("🌐 브라우저에서 http://라즈베리파이IP:5000 으로 접속하세요")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 서버 종료 중...")
    finally:
        print("✅ 정리 완료!")