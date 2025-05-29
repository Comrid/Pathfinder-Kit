"""
line_tracing_thin_web.py - 얇은 검은색 선용 웹 라인 트레이싱
Flask + OpenCV + PID 제어로 얇은 선을 정확하게 인식
"""

from flask import Flask, render_template_string, Response, request, jsonify
import cv2
import numpy as np
import time
from picamera2 import Picamera2
import sys
import os
import threading

# 모터 컨트롤러 import
sys.path.append(os.path.join(os.path.dirname(__file__), '../../MotorClassTest'))
from Motor import MotorController

app = Flask(__name__)

# HTML 템플릿 (얇은 선용 설정 추가)
html = """
<!doctype html>
<html>
<head>
    <title>패스파인더 얇은 라인 트레이싱</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            text-align: center; 
            background-color: #f0f0f0; 
            margin: 0; 
            padding: 20px; 
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
        }
        h1 { color: #333; }
        .video-container { 
            margin: 20px 0; 
        }
        img { 
            border: 3px solid #333; 
            border-radius: 10px; 
            box-shadow: 0 4px 8px rgba(0,0,0,0.3); 
        }
        .controls { 
            display: flex; 
            justify-content: center; 
            gap: 15px; 
            margin: 20px 0; 
            flex-wrap: wrap; 
        }
        .control-group { 
            background: white; 
            padding: 15px; 
            border-radius: 10px; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.1); 
            min-width: 200px;
        }
        .thin-line-group {
            background: #e8f5e8;
            border: 2px solid #4CAF50;
        }
        button { 
            background: #007bff; 
            color: white; 
            border: none; 
            padding: 8px 16px; 
            border-radius: 5px; 
            cursor: pointer; 
            margin: 3px; 
            font-size: 12px;
        }
        button:hover { background: #0056b3; }
        button.stop { background: #dc3545; }
        button.stop:hover { background: #c82333; }
        button.thin-mode { background: #28a745; }
        button.thin-mode:hover { background: #218838; }
        input[type="range"] { 
            width: 120px; 
            margin: 0 5px; 
        }
        input[type="number"] {
            width: 60px;
            padding: 2px;
        }
        .status { 
            background: #e8f4fd; 
            padding: 15px; 
            border-radius: 10px; 
            margin: 20px 0; 
        }
        .status-item { 
            display: inline-block; 
            margin: 5px 10px; 
            padding: 5px 8px; 
            background: white; 
            border-radius: 5px; 
            font-size: 12px;
        }
        .toggle-switch {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 24px;
            margin: 5px;
        }
        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 24px;
        }
        .slider:before {
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        input:checked + .slider {
            background-color: #2196F3;
        }
        input:checked + .slider:before {
            transform: translateX(26px);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 패스파인더 얇은 라인 트레이싱</h1>
        <p style="color: #666;">얇은 검은색 선 인식에 최적화된 고급 알고리즘</p>
        
        <div class="video-container">
            <img src="{{ url_for('video_feed') }}" width="640" height="480">
        </div>
        
        <div class="controls">
            <div class="control-group">
                <h3>라인 트레이싱 제어</h3>
                <button onclick="startTracing()" class="thin-mode">시작</button>
                <button onclick="stopTracing()" class="stop">정지</button>
                <button onclick="resetPID()">PID 리셋</button>
                <button onclick="resetHistory()">히스토리 리셋</button>
            </div>
            
            <div class="control-group">
                <h3>속도 조절</h3>
                <label>기본 속도: <span id="speedValue">35</span></label><br>
                <input type="range" id="speedSlider" min="15" max="60" value="35" 
                       onchange="updateSpeed(this.value)">
            </div>
            
            <div class="control-group">
                <h3>PID 파라미터</h3>
                <label>P: <input type="number" id="kp" value="1.2" step="0.1" onchange="updatePID()"></label><br>
                <label>I: <input type="number" id="ki" value="0.05" step="0.01" onchange="updatePID()"></label><br>
                <label>D: <input type="number" id="kd" value="0.4" step="0.1" onchange="updatePID()"></label>
            </div>
            
            <div class="control-group thin-line-group">
                <h3>얇은 선 설정</h3>
                <label>모폴로지 연산:
                    <label class="toggle-switch">
                        <input type="checkbox" id="morphology" checked onchange="toggleMorphology()">
                        <span class="slider"></span>
                    </label>
                </label><br>
                <label>스켈레톤화:
                    <label class="toggle-switch">
                        <input type="checkbox" id="skeleton" checked onchange="toggleSkeleton()">
                        <span class="slider"></span>
                    </label>
                </label><br>
                <label>최소 면적: <input type="number" id="minArea" value="50" min="10" max="500" onchange="updateMinArea()"></label><br>
                <label>임계값: <span id="thresholdValue">60</span></label><br>
                <input type="range" id="thresholdSlider" min="30" max="100" value="60" 
                       onchange="updateThreshold(this.value)">
            </div>
            
            <div class="control-group">
                <h3>ROI 설정</h3>
                <label>ROI 높이: <span id="roiHeightValue">120</span></label><br>
                <input type="range" id="roiHeightSlider" min="80" max="200" value="120" 
                       onchange="updateROIHeight(this.value)"><br>
                <label>ROI Y 위치: <span id="roiYValue">330</span></label><br>
                <input type="range" id="roiYSlider" min="250" max="400" value="330" 
                       onchange="updateROIY(this.value)"><br>
                <label>좌우 여백: <span id="roiMarginValue">100</span></label><br>
                <input type="range" id="roiMarginSlider" min="0" max="200" value="100" 
                       onchange="updateROIMargin(this.value)">
                <p style="font-size: 12px; color: #666;">중앙 기준으로 양쪽에서 잘라낼 크기</p>
            </div>
        </div>
        
        <div class="status">
            <h3>상태 정보</h3>
            <div class="status-item">라인 검출: <span id="lineDetected">-</span></div>
            <div class="status-item">조향 값: <span id="steering">-</span></div>
            <div class="status-item">속도: <span id="currentSpeed">-</span></div>
            <div class="status-item">FPS: <span id="fps">-</span></div>
            <div class="status-item">히스토리: <span id="history">-</span></div>
            <div class="status-item">검출 방법: <span id="detectionMethod">-</span></div>
        </div>
    </div>

    <script>
        function startTracing() {
            fetch('/start_tracing', {method: 'POST'})
                .then(response => response.json())
                .then(data => console.log(data));
        }
        
        function stopTracing() {
            fetch('/stop_tracing', {method: 'POST'})
                .then(response => response.json())
                .then(data => console.log(data));
        }
        
        function resetPID() {
            fetch('/reset_pid', {method: 'POST'})
                .then(response => response.json())
                .then(data => console.log(data));
        }
        
        function resetHistory() {
            fetch('/reset_history', {method: 'POST'})
                .then(response => response.json())
                .then(data => console.log(data));
        }
        
        function updateSpeed(value) {
            document.getElementById('speedValue').textContent = value;
            fetch('/update_speed', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({speed: parseInt(value)})
            });
        }
        
        function updatePID() {
            const kp = parseFloat(document.getElementById('kp').value);
            const ki = parseFloat(document.getElementById('ki').value);
            const kd = parseFloat(document.getElementById('kd').value);
            
            fetch('/update_pid', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({kp: kp, ki: ki, kd: kd})
            });
        }
        
        function toggleMorphology() {
            const enabled = document.getElementById('morphology').checked;
            fetch('/toggle_morphology', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({enabled: enabled})
            });
        }
        
        function toggleSkeleton() {
            const enabled = document.getElementById('skeleton').checked;
            fetch('/toggle_skeleton', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({enabled: enabled})
            });
        }
        
        function updateMinArea() {
            const value = parseInt(document.getElementById('minArea').value);
            fetch('/update_min_area', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({min_area: value})
            });
        }
        
        function updateThreshold(value) {
            document.getElementById('thresholdValue').textContent = value;
            fetch('/update_threshold', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({threshold: parseInt(value)})
            });
        }
        
        function updateROIHeight(value) {
            document.getElementById('roiHeightValue').textContent = value;
            fetch('/update_roi', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({roi_height: parseInt(value)})
            });
        }
        
        function updateROIY(value) {
            document.getElementById('roiYValue').textContent = value;
            fetch('/update_roi', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({roi_y: parseInt(value)})
            });
        }
        
        function updateROIMargin(value) {
            document.getElementById('roiMarginValue').textContent = value;
            fetch('/update_roi', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({roi_margin: parseInt(value)})
            });
        }
        
        // 상태 정보 주기적 업데이트
        setInterval(() => {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('lineDetected').textContent = data.line_detected ? '✅' : '❌';
                    document.getElementById('steering').textContent = data.steering.toFixed(2);
                    document.getElementById('currentSpeed').textContent = data.speed;
                    document.getElementById('fps').textContent = data.fps;
                    document.getElementById('history').textContent = data.history_count + '/10';
                    document.getElementById('detectionMethod').textContent = data.detection_method;
                });
        }, 500);
    </script>
</body>
</html>
"""

class WebThinLineTracer:
    """웹 인터페이스용 얇은 라인 트레이서"""
    
    def __init__(self):
        # 카메라 초기화
        self.picam2 = Picamera2()
        self.picam2.preview_configuration.main.size = (640, 480)
        self.picam2.preview_configuration.main.format = "RGB888"
        self.picam2.configure("preview")
        self.picam2.start()
        
        # 모터 컨트롤러 초기화
        self.motor = MotorController()
        
        # PID 제어기 초기화 (얇은 선용)
        self.kp = 1.2
        self.ki = 0.05
        self.kd = 0.4
        self.reset_pid()
        
        # 설정값들
        self.frame_width = 640
        self.frame_height = 480
        self.roi_height = 120
        self.roi_y = 330
        self.roi_margin = 100   # 중앙 기준 좌우 여백 (양쪽에서 잘라낼 크기)
        self.roi_x = self.roi_margin
        self.roi_width = self.frame_width - (2 * self.roi_margin)
        self.base_speed = 35
        self.max_turn_speed = 25
        self.line_threshold = 60
        self.min_line_area = 50
        self.max_line_area = 5000
        
        # 얇은 선 검출 설정
        self.use_morphology = True
        self.use_skeleton = True
        
        # 상태 변수
        self.tracing_active = False
        self.line_detected = False
        self.current_steering = 0
        self.fps = 0
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.detection_history = []
        self.detection_method = "None"
        
        # PID 변수
        self.previous_error = 0
        self.integral = 0
        self.last_time = time.time()
        
        print("웹 얇은 라인 트레이서 초기화 완료")
    
    def reset_pid(self):
        """PID 제어기 리셋"""
        self.previous_error = 0
        self.integral = 0
        self.last_time = time.time()
    
    def update_pid_params(self, kp, ki, kd):
        """PID 파라미터 업데이트"""
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.reset_pid()
    
    def calculate_pid(self, error):
        """PID 제어 값 계산"""
        current_time = time.time()
        dt = current_time - self.last_time
        
        if dt <= 0.0:
            dt = 0.01
        
        # 비례항
        proportional = self.kp * error
        
        # 적분항
        self.integral += error * dt
        integral_term = self.ki * self.integral
        
        # 미분항
        derivative = (error - self.previous_error) / dt
        derivative_term = self.kd * derivative
        
        # PID 출력
        output = proportional + integral_term + derivative_term
        
        # 다음 계산을 위해 저장
        self.previous_error = error
        self.last_time = current_time
        
        return output
    
    def skeletonize(self, binary_image):
        """이미지 스켈레톤화"""
        skeleton = np.zeros(binary_image.shape, np.uint8)
        eroded = np.copy(binary_image)
        temp = np.zeros(binary_image.shape, np.uint8)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        
        iterations = 0
        while iterations < 10:  # 최대 반복 제한
            cv2.erode(eroded, kernel, eroded)
            cv2.dilate(eroded, kernel, temp)
            cv2.subtract(binary_image, temp, temp)
            cv2.bitwise_or(skeleton, temp, skeleton)
            eroded, binary_image = binary_image, eroded
            if cv2.countNonZero(binary_image) == 0:
                break
            iterations += 1
                
        return skeleton
    
    def process_frame(self, frame):
        """프레임 처리 및 얇은 라인 트레이싱"""
        # FPS 계산
        self.fps_counter += 1
        current_time = time.time()
        if current_time - self.fps_start_time >= 1.0:
            self.fps = self.fps_counter
            self.fps_counter = 0
            self.fps_start_time = current_time
        
        # ROI 추출 (좌우도 잘라내기)
        roi = frame[self.roi_y:self.roi_y + self.roi_height, self.roi_x:self.roi_x + self.roi_width]
        
        # 그레이스케일 변환
        gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        
        # 얇은 선을 위한 전처리
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # 적응적 임계값 또는 일반 임계값
        if self.use_morphology:
            binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                         cv2.THRESH_BINARY_INV, 11, 2)
        else:
            _, binary = cv2.threshold(blurred, self.line_threshold, 255, cv2.THRESH_BINARY_INV)
        
        # 모폴로지 연산
        if self.use_morphology:
            kernel_noise = np.ones((2, 2), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_noise)
            
            kernel_connect = np.ones((3, 1), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_connect)
        
        # 스켈레톤화
        if self.use_skeleton:
            binary = self.skeletonize(binary)
        
        # 라인 중심점 찾기
        line_center, contours = self.find_line_center_advanced(binary)
        
        # 라인 검출 상태 업데이트
        self.line_detected = line_center is not None
        
        # 조향 계산 및 모터 제어
        if self.tracing_active:
            steering = self.calculate_steering_with_history(line_center)
            self.current_steering = steering
            
            if self.line_detected:
                # 조향 방향 수정: 라인이 왼쪽에 있으면 왼쪽으로 가야 함
                left_speed = max(0, min(100, self.base_speed + steering))
                right_speed = max(0, min(100, self.base_speed - steering))
                self.motor.set_individual_speeds(int(right_speed), int(left_speed))
            else:
                self.motor.stop_motors()
        else:
            self.motor.stop_motors()
            self.current_steering = 0
        
        # 디버그 정보 그리기
        self.draw_debug_info(frame, binary, line_center, contours)
        
        return frame
    
    def find_line_center_advanced(self, binary_image):
        """얇은 선을 위한 고급 중심점 검출"""
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            valid_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if self.min_line_area <= area <= self.max_line_area:
                    rect = cv2.minAreaRect(contour)
                    width, height = rect[1]
                    if width > 0 and height > 0:
                        aspect_ratio = max(width, height) / min(width, height)
                        if aspect_ratio > 2:
                            valid_contours.append(contour)
            
            if valid_contours:
                largest_contour = max(valid_contours, key=cv2.contourArea)
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    self.detection_method = "Contour"
                    return (cx, cy), contours
        
        # 픽셀 기반 검출
        pixel_center = self.find_line_center_pixel_based(binary_image)
        if pixel_center:
            self.detection_method = "Pixel"
        else:
            self.detection_method = "None"
        
        return pixel_center, contours if 'contours' in locals() else []
    
    def find_line_center_pixel_based(self, binary_image):
        """픽셀 기반 라인 중심점 검출"""
        height, width = binary_image.shape
        line_centers = []
        
        for y in range(height):
            row = binary_image[y, :]
            white_pixels = np.where(row == 255)[0]
            
            if len(white_pixels) > 0:
                groups = []
                current_group = [white_pixels[0]]
                
                for i in range(1, len(white_pixels)):
                    if white_pixels[i] - white_pixels[i-1] <= 3:
                        current_group.append(white_pixels[i])
                    else:
                        groups.append(current_group)
                        current_group = [white_pixels[i]]
                groups.append(current_group)
                
                if groups:
                    longest_group = max(groups, key=len)
                    if len(longest_group) >= 2:
                        center_x = int(np.mean(longest_group))
                        line_centers.append((center_x, y))
        
        if line_centers:
            avg_x = int(np.mean([center[0] for center in line_centers]))
            avg_y = int(np.mean([center[1] for center in line_centers]))
            return (avg_x, avg_y)
        
        return None
    
    def calculate_steering_with_history(self, line_center):
        """히스토리를 고려한 조향 계산"""
        if line_center is None:
            if len(self.detection_history) > 0:
                recent_centers = self.detection_history[-3:]
                valid_centers = [center for center in recent_centers if center]
                if valid_centers:
                    avg_x = np.mean([center[0] for center in valid_centers])
                    line_center = (int(avg_x), 0)
        
        if line_center is not None:
            self.detection_history.append(line_center)
            if len(self.detection_history) > 10:
                self.detection_history.pop(0)
            
            error = line_center[0] - (self.roi_width // 2)
            steering = self.calculate_pid(error)
            steering = max(-self.max_turn_speed, min(self.max_turn_speed, steering))
            
            return steering
        else:
            self.detection_history.append(None)
            if len(self.detection_history) > 10:
                self.detection_history.pop(0)
            
            return 0
    
    def draw_debug_info(self, frame, binary, line_center, contours):
        """디버그 정보 그리기"""
        # ROI 영역 표시 (좌우 잘린 영역)
        cv2.rectangle(frame, (self.roi_x, self.roi_y), (self.roi_x + self.roi_width, self.roi_y + self.roi_height), (0, 255, 0), 2)
        
        # 중심선 표시 (ROI 영역 기준)
        center_x = self.roi_x + (self.roi_width // 2)
        cv2.line(frame, (center_x, 0), (center_x, self.frame_height), (255, 255, 255), 2)
        
        # 라인 중심점 표시
        if line_center:
            actual_x = line_center[0] + self.roi_x  # ROI 좌표를 전체 프레임 좌표로 변환
            actual_y = line_center[1] + self.roi_y
            cv2.circle(frame, (actual_x, actual_y), 8, (0, 0, 255), -1)
            cv2.line(frame, (center_x, actual_y), (actual_x, actual_y), (255, 0, 0), 2)
        
        # 검출 히스토리 표시
        if len(self.detection_history) > 1:
            for i, hist_center in enumerate(self.detection_history[-5:]):
                if hist_center:
                    hist_x = hist_center[0] + self.roi_x  # ROI 좌표 변환
                    hist_y = hist_center[1] + self.roi_y
                    cv2.circle(frame, (hist_x, hist_y), 4, (255, 255, 0), -1)
        
        # 윤곽선 표시
        if contours:
            roi_contours = []
            for contour in contours:
                adjusted_contour = contour.copy()
                adjusted_contour[:, :, 0] += self.roi_x  # X 좌표 변환
                adjusted_contour[:, :, 1] += self.roi_y  # Y 좌표 변환
                roi_contours.append(adjusted_contour)
            cv2.drawContours(frame, roi_contours, -1, (0, 255, 255), 1)
        
        # 이진화 이미지 표시 (ROI 크기에 맞게 조정)
        binary_colored = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
        # ROI 비율에 맞게 리사이즈
        display_width = 200
        display_height = int(display_width * self.roi_height / self.roi_width)
        binary_resized = cv2.resize(binary_colored, (display_width, display_height))
        frame[10:10+display_height, 10:10+display_width] = binary_resized
        cv2.rectangle(frame, (10, 10), (10+display_width, 10+display_height), (255, 255, 255), 2)
        
        # 상태 정보 표시
        status_color = (0, 255, 0) if self.tracing_active else (0, 0, 255)
        status_text = "THIN LINE ACTIVE" if self.tracing_active else "STOPPED"
        cv2.putText(frame, status_text, (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)

# 전역 얇은 라인 트레이서 인스턴스
tracer = WebThinLineTracer()

def gen_frames():
    """프레임 생성기"""
    while True:
        frame = tracer.picam2.capture_array()
        processed_frame = tracer.process_frame(frame)
        
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

@app.route('/start_tracing', methods=['POST'])
def start_tracing():
    tracer.tracing_active = True
    return jsonify({'status': 'started'})

@app.route('/stop_tracing', methods=['POST'])
def stop_tracing():
    tracer.tracing_active = False
    tracer.motor.stop_motors()
    return jsonify({'status': 'stopped'})

@app.route('/reset_pid', methods=['POST'])
def reset_pid():
    tracer.reset_pid()
    return jsonify({'status': 'pid_reset'})

@app.route('/reset_history', methods=['POST'])
def reset_history():
    tracer.detection_history.clear()
    return jsonify({'status': 'history_reset'})

@app.route('/update_speed', methods=['POST'])
def update_speed():
    data = request.get_json()
    tracer.base_speed = data['speed']
    return jsonify({'status': 'speed_updated', 'speed': tracer.base_speed})

@app.route('/update_pid', methods=['POST'])
def update_pid():
    data = request.get_json()
    tracer.update_pid_params(data['kp'], data['ki'], data['kd'])
    return jsonify({'status': 'pid_updated'})

@app.route('/toggle_morphology', methods=['POST'])
def toggle_morphology():
    data = request.get_json()
    tracer.use_morphology = data['enabled']
    return jsonify({'status': 'morphology_updated', 'enabled': tracer.use_morphology})

@app.route('/toggle_skeleton', methods=['POST'])
def toggle_skeleton():
    data = request.get_json()
    tracer.use_skeleton = data['enabled']
    return jsonify({'status': 'skeleton_updated', 'enabled': tracer.use_skeleton})

@app.route('/update_min_area', methods=['POST'])
def update_min_area():
    data = request.get_json()
    tracer.min_line_area = data['min_area']
    return jsonify({'status': 'min_area_updated', 'min_area': tracer.min_line_area})

@app.route('/update_threshold', methods=['POST'])
def update_threshold():
    data = request.get_json()
    tracer.line_threshold = data['threshold']
    return jsonify({'status': 'threshold_updated', 'threshold': tracer.line_threshold})

@app.route('/update_roi', methods=['POST'])
def update_roi():
    data = request.get_json()
    if 'roi_height' in data:
        tracer.roi_height = data['roi_height']
    if 'roi_y' in data:
        tracer.roi_y = data['roi_y']
    if 'roi_margin' in data:
        tracer.roi_margin = data['roi_margin']
        # ROI X와 폭을 자동으로 계산
        tracer.roi_x = tracer.roi_margin
        tracer.roi_width = tracer.frame_width - (2 * tracer.roi_margin)
        # ROI 폭이 변경되면 최대 면적도 조정
        tracer.max_line_area = int(tracer.roi_width * tracer.roi_height * 0.1)
    return jsonify({'status': 'roi_updated'})

@app.route('/status')
def get_status():
    history_count = len([h for h in tracer.detection_history if h])
    return jsonify({
        'line_detected': tracer.line_detected,
        'steering': tracer.current_steering,
        'speed': tracer.base_speed,
        'fps': tracer.fps,
        'tracing_active': tracer.tracing_active,
        'history_count': history_count,
        'detection_method': tracer.detection_method
    })

if __name__ == '__main__':
    print("🤖 패스파인더 웹 얇은 라인 트레이싱 서버 시작!")
    print("얇은 검은색 선 인식에 최적화된 고급 알고리즘 적용")
    print("브라우저에서 http://라즈베리파이IP:5000 으로 접속하세요")
    print("Ctrl+C로 종료")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n서버 종료 중...")
    finally:
        tracer.motor.stop_motors()
        tracer.motor.cleanup()
        print("정리 완료!") 