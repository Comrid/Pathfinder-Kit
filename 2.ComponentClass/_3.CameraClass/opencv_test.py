# flask_libcamera_stream.py

from flask import Flask, render_template_string, Response
import cv2
import numpy as np
from picamera2 import Picamera2

app = Flask(__name__)

# HTML 템플릿 - 더 예쁘게 만들기
html = """
<!doctype html>
<html>
<head>
    <title>Raspberry Pi Camera Stream with OpenCV</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            text-align: center; 
            background-color: #f0f0f0; 
        }
        h1 { color: #333; }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px; 
        }
        img { 
            border: 3px solid #333; 
            border-radius: 10px; 
            box-shadow: 0 4px 8px rgba(0,0,0,0.3); 
        }
        .info { 
            margin-top: 20px; 
            padding: 10px; 
            background-color: #e8f4fd; 
            border-radius: 5px; 
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 패스파인더 카메라 + OpenCV 테스트</h1>
        <img src="{{ url_for('video_feed') }}" width="640" height="480">
        <div class="info">
            <h3>적용된 OpenCV 기능들:</h3>
            <p>✅ 엣지 검출 (Canny Edge Detection)</p>
            <p>✅ 색상 검출 (빨간색 객체 찾기)</p>
            <p>✅ 얼굴 검출 (Face Detection)</p>
            <p>✅ 윤곽선 검출 (Contour Detection)</p>
            <p>✅ FPS 표시</p>
        </div>
    </div>
</body>
</html>
"""

# 카메라 초기화
picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 480)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()

# 얼굴 검출용 분류기 로드 (있으면)
try:
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    face_detection_enabled = True
except:
    face_detection_enabled = False
    print("얼굴 검출 분류기를 로드할 수 없습니다.")

# FPS 계산용
import time
fps_counter = 0
fps_start_time = time.time()
current_fps = 0

def process_frame(frame):
    """OpenCV로 프레임 처리"""
    global fps_counter, fps_start_time, current_fps
    
    # 원본 프레임 복사
    processed = frame.copy()
    height, width = processed.shape[:2]
    
    # 1. 엣지 검출 (왼쪽 상단)
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    
    # 엣지를 작은 창으로 표시
    small_edges = cv2.resize(edges_colored, (160, 120))
    processed[10:130, 10:170] = small_edges
    cv2.rectangle(processed, (10, 10), (170, 130), (0, 255, 0), 2)
    cv2.putText(processed, "Edges", (15, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # 2. 빨간색 검출 (오른쪽 상단)
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
    
    # 빨간색 범위 정의
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 50, 50])
    upper_red2 = np.array([180, 255, 255])
    
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = mask1 + mask2
    
    # 빨간색 영역을 작은 창으로 표시
    red_result = cv2.bitwise_and(frame, frame, mask=red_mask)
    small_red = cv2.resize(red_result, (160, 120))
    processed[10:130, width-170:width-10] = small_red
    cv2.rectangle(processed, (width-170, 10), (width-10, 130), (255, 0, 0), 2)
    cv2.putText(processed, "Red Detection", (width-165, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    
    # 3. 얼굴 검출 (가운데)
    if face_detection_enabled:
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        for (x, y, w, h) in faces:
            cv2.rectangle(processed, (x, y), (x+w, y+h), (255, 255, 0), 3)
            cv2.putText(processed, "Face", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    # 4. 윤곽선 검출
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 큰 윤곽선만 그리기
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 500:  # 면적이 500 이상인 윤곽선만
            cv2.drawContours(processed, [contour], -1, (0, 255, 255), 2)
    
    # 5. FPS 계산 및 표시
    fps_counter += 1
    current_time = time.time()
    if current_time - fps_start_time >= 1.0:
        current_fps = fps_counter
        fps_counter = 0
        fps_start_time = current_time
    
    # 정보 표시
    cv2.putText(processed, f"FPS: {current_fps}", (10, height-60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(processed, f"Contours: {len(contours)}", (10, height-30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(processed, "OpenCV Test", (width//2-70, height-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    
    # 6. 중앙에 십자선 그리기
    cv2.line(processed, (width//2-20, height//2), (width//2+20, height//2), (255, 255, 255), 2)
    cv2.line(processed, (width//2, height//2-20), (width//2, height//2+20), (255, 255, 255), 2)
    
    return processed

def gen_frames():
    while True:
        # 원본 프레임 캡처
        frame = picam2.capture_array()
        
        # OpenCV 처리 적용
        processed_frame = process_frame(frame)
        
        # JPEG로 인코딩
        ret, buffer = cv2.imencode('.jpg', processed_frame)
        if not ret:
            continue
        
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return render_template_string(html)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("🤖 패스파인더 카메라 + OpenCV 테스트 서버 시작!")
    print("브라우저에서 http://라즈베리파이IP:5000 으로 접속하세요")
    print("Ctrl+C로 종료")
    app.run(host='0.0.0.0', port=5000, debug=False)
