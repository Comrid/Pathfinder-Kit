# flask_libcamera_stream.py

from flask import Flask, render_template, Response
import cv2
import subprocess
import os

app = Flask(__name__)

# 카메라 모듈 감지 및 초기화
def setup_camera():
    """카메라 모듈을 자동으로 감지하고 초기화합니다."""
    try:
        # PiCamera2 시도
        from picamera2 import Picamera2
        picam2 = Picamera2()
        picam2.preview_configuration.main.size = (640, 480)
        picam2.preview_configuration.main.format = "RGB888"
        picam2.configure("preview")
        picam2.start()
        print("✅ PiCamera2 모듈이 성공적으로 초기화되었습니다.")
        return picam2, 'picamera2'
    except Exception as e:
        print(f"⚠️ PiCamera2 초기화 실패: {e}")
        
        try:
            # USB 카메라 시도
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                print("✅ USB 카메라가 성공적으로 초기화되었습니다.")
                return cap, 'usb'
            else:
                raise Exception("USB 카메라를 열 수 없습니다.")
        except Exception as e:
            print(f"⚠️ USB 카메라 초기화 실패: {e}")
            print("🔄 시뮬레이션 모드로 전환합니다.")
            return None, 'simulation'

# 카메라 초기화
camera, camera_type = setup_camera()

def generate_dummy_frame():
    """시뮬레이션용 더미 프레임을 생성합니다."""
    import numpy as np
    import time
    
    # 640x480 크기의 그라디언트 이미지 생성
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # 시간에 따라 변하는 색상 효과
    t = int(time.time() * 10) % 255
    frame[:, :, 0] = t  # Red channel
    frame[:, :, 1] = (t + 85) % 255  # Green channel  
    frame[:, :, 2] = (t + 170) % 255  # Blue channel
    
    # 텍스트 오버레이
    cv2.putText(frame, "SIMULATION MODE", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, f"Time: {time.strftime('%H:%M:%S')}", (50, 100), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, "Pathfinder Camera Test", (50, 150), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    
    return frame

def gen_frames():
    """프레임 생성기 - 카메라 타입에 따라 다른 방식으로 프레임을 생성합니다."""
    global camera, camera_type
    
    while True:
        try:
            if camera_type == 'picamera2':
                frame = camera.capture_array()
            elif camera_type == 'usb':
                ret, frame = camera.read()
                if not ret:
                    continue
                # BGR to RGB 변환 (OpenCV는 BGR 사용)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:  # simulation
                frame = generate_dummy_frame()
            
            # JPEG 인코딩
            ret, buffer = cv2.imencode('.jpg', frame, 
                                     [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ret:
                continue
                
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                   
        except Exception as e:
            print(f"❌ 프레임 생성 오류: {e}")
            # 오류 발생 시 더미 프레임으로 대체
            frame = generate_dummy_frame()
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    """메인 페이지를 렌더링합니다."""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """비디오 스트림을 제공합니다."""
    return Response(gen_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/camera_info')
def camera_info():
    """카메라 정보를 JSON으로 반환합니다."""
    from flask import jsonify
    
    info = {
        'camera_type': camera_type,
        'resolution': '640x480',
        'fps': 30,
        'format': 'MJPEG',
        'status': 'online' if camera else 'simulation'
    }
    return jsonify(info)

def get_server_ip():
    """서버 IP 주소를 안전하게 가져옵니다."""
    try:
        # subprocess.check_output 사용 시 shell=False로 보안 강화
        result = subprocess.check_output(['hostname', '-I'], 
                                       shell=False, 
                                       timeout=5,
                                       text=True)
        return result.strip().split()[0]
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, IndexError):
        # 실패 시 기본값 반환
        return '127.0.0.1'

if __name__ == '__main__':
    print("🤖 패스파인더 카메라 스트리밍 서버 시작!")
    print(f"📹 카메라 모드: {camera_type.upper()}")
    
    # 서버 IP 주소 가져오기
    server_ip = get_server_ip()
    print(f"🌐 브라우저에서 http://{server_ip}:5000 으로 접속하세요")
    print("📱 모바일에서도 접속 가능합니다!")
    print("Ctrl+C로 종료")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 서버를 종료합니다...")
        # 카메라 리소스 정리
        if camera and camera_type == 'picamera2':
            camera.stop()
        elif camera and camera_type == 'usb':
            camera.release()
        print("✅ 리소스가 정리되었습니다.")
