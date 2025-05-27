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
import traceback

app = Flask(__name__)

# 설정
CONFIG = {
    'project_dir': os.path.expanduser("~"),
    'max_file_size': 5 * 1024 * 1024,  # 5MB
    'excluded_dirs': {'.git', '__pycache__', '.vscode', 'node_modules', '.DS_Store'},
    'allowed_extensions': {'.py', '.txt', '.md', '.json', '.html', '.css', '.js', '.sh', '.cfg'}
}

class FileManager:
    """파일 시스템 관리"""
    
    @staticmethod
    def get_file_tree(path):
        """파일 트리 구조 생성"""
        tree = []
        try:
            if not os.path.exists(path):
                return tree
                
            items = sorted(os.listdir(path))
            
            # 폴더 먼저
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
            
            # 파일 나중에
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
                    
        except Exception as e:
            print(f"Error reading directory {path}: {e}")
        
        return tree
    
    @staticmethod
    def is_safe_path(filepath):
        """경로 안전성 검사"""
        try:
            full_path = os.path.join(CONFIG['project_dir'], filepath)
            return os.path.commonpath([full_path, CONFIG['project_dir']]) == CONFIG['project_dir']
        except:
            return False

class CodeRunner:
    """코드 실행 관리"""
    
    @staticmethod
    def run_python_file(filepath):
        """Python 파일 실행"""
        try:
            result = subprocess.run(
                ['python3', filepath],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.path.dirname(filepath)
            )
            
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr
                
            return {
                'success': result.returncode == 0,
                'output': output,
                'exit_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '⏰ 실행 시간 초과 (30초)',
                'exit_code': -1
            }
        except Exception as e:
            return {
                'success': False,
                'output': f'❌ 실행 오류: {str(e)}',
                'exit_code': -1
            }

# 라우트
@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/api/files')
def get_files():
    """파일 트리 API"""
    try:
        tree = FileManager.get_file_tree(CONFIG['project_dir'])
        return jsonify({
            'success': True,
            'data': tree
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
            return jsonify({'success': False, 'error': '파일이 너무 큽니다'}), 413
        
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
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/file/<path:filepath>', methods=['POST'])
def save_file(filepath):
    """파일 저장"""
    try:
        if not FileManager.is_safe_path(filepath):
            return jsonify({'success': False, 'error': '접근 권한이 없습니다'}), 403
        
        data = request.get_json()
        content = data.get('content', '')
        
        full_path = os.path.join(CONFIG['project_dir'], filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            'success': True,
            'message': '파일이 저장되었습니다'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/run/<path:filepath>', methods=['POST'])
def run_file(filepath):
    """파일 실행"""
    try:
        if not FileManager.is_safe_path(filepath):
            return jsonify({'success': False, 'error': '접근 권한이 없습니다'}), 403
        
        full_path = os.path.join(CONFIG['project_dir'], filepath)
        
        if not os.path.exists(full_path):
            return jsonify({'success': False, 'error': '파일을 찾을 수 없습니다'}), 404
        
        if not filepath.endswith('.py'):
            return jsonify({'success': False, 'error': 'Python 파일만 실행할 수 있습니다'}), 400
        
        result = CodeRunner.run_python_file(full_path)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/create', methods=['POST'])
def create_item():
    """파일/폴더 생성"""
    try:
        data = request.get_json()
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
        else:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write('')
            message = f'파일 "{os.path.basename(path)}"가 생성되었습니다'
        
        return jsonify({
            'success': True,
            'message': message,
            'path': path
        })
        
    except Exception as e:
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
        else:
            os.remove(full_path)
            message = '파일이 삭제되었습니다'
        
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rename', methods=['POST'])
def rename_item():
    """파일/폴더 이름 변경"""
    try:
        data = request.get_json()
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
        
        os.makedirs(os.path.dirname(new_full_path), exist_ok=True)
        os.rename(old_full_path, new_full_path)
        
        return jsonify({
            'success': True,
            'message': '이름이 변경되었습니다'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 에러 핸들러
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'API를 찾을 수 없습니다'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': '서버 오류가 발생했습니다'}), 500

if __name__ == '__main__':
    print("🚀 Pathfinder Web IDE 시작!")
    print(f"📁 프로젝트 디렉토리: {CONFIG['project_dir']}")
    print("🌐 브라우저에서 http://라즈베리파이IP:5000 으로 접속하세요")
    
    app.run(host='0.0.0.0', port=5000, debug=True) 