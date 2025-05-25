"""
line_tracing_web.py - 웹 브라우저에서 라인 트레이싱 모니터링
Flask + OpenCV + PID 제어
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

# HTML 템플릿
html = """
<!doctype html>
<html>
<head>
    <title>패스파인더 라인 트레이싱</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            text-align: center; 
            background-color: #f0f0f0; 
            margin: 0; 
            padding: 20px; 
        }
        .container { 
            max-width: 1000px; 
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
            gap: 20px; 
            margin: 20px 0; 
            flex-wrap: wrap; 
        }
        .control-group { 
            background: white; 
            padding: 15px; 
            border-radius: 10px; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.1); 
        }
        button { 
            background: #007bff; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            border-radius: 5px; 
            cursor: pointer; 
            margin: 5px; 
        }
        button:hover { background: #0056b3; }
        button.stop { background: #dc3545; }
        button.stop:hover { background: #c82333; }
        input[type="range"] { 
            width: 150px; 
            margin: 0 10px; 
        }
        .status { 
            background: #e8f4fd; 
            padding: 15px; 
            border-radius: 10px; 
            margin: 20px 0; 
        }
        .status-item { 
            display: inline-block; 
            margin: 5px 15px; 
            padding: 5px 10px; 
            background: white; 
            border-radius: 5px; 
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 패스파인더 라인 트레이싱</h1>
        
        <div class="video-container">
            <img src="{{ url_for('video_feed') }}" width="640" height="480">
        </div>
        
        <div class="controls">
            <div class="control-group">
                <h3>라인 트레이싱 제어</h3>
                <button onclick="startTracing()">시작</button>
                <button onclick="stopTracing()" class="stop">정지</button>
                <button onclick="resetPID()">PID 리셋</button>
            </div>
            
            <div class="control-group">
                <h3>속도 조절</h3>
                <label>기본 속도: <span id="speedValue">40</span></label><br>
                <input type="range" id="speedSlider" min="20" max="80" value="40" 
                       onchange="updateSpeed(this.value)">
            </div>
            
            <div class="control-group">
                <h3>PID 파라미터</h3>
                <label>P: <input type="number" id="kp" value="0.8" step="0.1" style="width:60px;" onchange="updatePID()"></label><br>
                <label>I: <input type="number" id="ki" value="0.1" step="0.01" style="width:60px;" onchange="updatePID()"></label><br>
                <label>D: <input type="number" id="kd" value="0.3" step="0.1" style="width:60px;" onchange="updatePID()"></label>
            </div>
        </div>
        
        <div class="status">
            <h3>상태 정보</h3>
            <div class="status-item">라인 검출: <span id="lineDetected">-</span></div>
            <div class="status-item">조향 값: <span id="steering">-</span></div>
            <div class="status-item">속도: <span id="currentSpeed">-</span></div>
            <div class="status-item">FPS: <span id="fps">-</span></div>
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
        
        // 상태 정보 주기적 업데이트
        setInterval(() => {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('lineDetected').textContent = data.line_detected ? '✅' : '❌';
                    document.getElementById('steering').textContent = data.steering.toFixed(2);
                    document.getElementById('currentSpeed').textContent = data.speed;
                    document.getElementById('fps').textContent = data.fps;
                });
        }, 500);
    </script>
</body>
</html>
"""

class WebLineTracer:
    """웹 인터페이스용 라인 트레이서"""
    
    def __init__(self):
        # 카메라 초기화
        self.picam2 = Picamera2()
        self.picam2.preview_configuration.main.size = (640, 480)
        self.picam2.preview_configuration.main.format = "RGB888"
        self.picam2.configure("preview")
        self.picam2.start()
        
        # 모터 컨트롤러 초기화
        self.motor = MotorController()
        
        # PID 제어기 초기화
        self.kp = 0.8
        self.ki = 0.1
        self.kd = 0.3
        self.reset_pid()
        
        # 설정값들
        self.frame_width = 640
        self.frame_height = 480
        self.roi_height = 100
        self.roi_y = 350
        self.base_speed = 40
        self.max_turn_speed = 30
        self.line_threshold = 50
        self.min_line_area = 500
        
        # 상태 변수
        self.tracing_active = False
        self.line_detected = False
        self.current_steering = 0
        self.fps = 0
        self.fps_counter = 0
        self.fps_start_time = time.time()
        
        # PID 변수
        self.previous_error = 0
        self.integral = 0
        self.last_time = time.time()
        
        print("웹 라인 트레이서 초기화 완료")
    
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
    
    def process_frame(self, frame):
        """프레임 처리 및 라인 트레이싱"""
        # FPS 계산
        self.fps_counter += 1
        current_time = time.time()
        if current_time - self.fps_start_time >= 1.0:
            self.fps = self.fps_counter
            self.fps_counter = 0
            self.fps_start_time = current_time
        
        # ROI 추출
        roi = frame[self.roi_y:self.roi_y + self.roi_height, :]
        
        # 그레이스케일 변환 및 이진화
        gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, binary = cv2.threshold(blurred, self.line_threshold, 255, cv2.THRESH_BINARY_INV)
        
        # 라인 중심점 찾기
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        line_center = None
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest_contour) > self.min_line_area:
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    line_center = (cx, cy)
        
        # 라인 검출 상태 업데이트
        self.line_detected = line_center is not None
        
        # 조향 계산 및 모터 제어
        if self.tracing_active:
            if line_center:
                error = line_center[0] - (self.frame_width // 2)
                steering = self.calculate_pid(error)
                steering = max(-self.max_turn_speed, min(self.max_turn_speed, steering))
                self.current_steering = steering
                
                # 모터 제어
                left_speed = max(0, min(100, self.base_speed - steering))
                right_speed = max(0, min(100, self.base_speed + steering))
                self.motor.set_individual_speeds(int(right_speed), int(left_speed))
            else:
                self.motor.stop_motors()
                self.current_steering = 0
        else:
            self.motor.stop_motors()
            self.current_steering = 0
        
        # 디버그 정보 그리기
        self.draw_debug_info(frame, binary, line_center, contours)
        
        return frame
    
    def draw_debug_info(self, frame, binary, line_center, contours):
        """디버그 정보 그리기"""
        # ROI 영역 표시
        cv2.rectangle(frame, (0, self.roi_y), (self.frame_width, self.roi_y + self.roi_height), (0, 255, 0), 2)
        
        # 중심선 표시
        center_x = self.frame_width // 2
        cv2.line(frame, (center_x, 0), (center_x, self.frame_height), (255, 255, 255), 2)
        
        # 라인 중심점 표시
        if line_center:
            actual_x = line_center[0]
            actual_y = line_center[1] + self.roi_y
            cv2.circle(frame, (actual_x, actual_y), 10, (0, 0, 255), -1)
            cv2.line(frame, (center_x, actual_y), (actual_x, actual_y), (255, 0, 0), 3)
        
        # 윤곽선 표시
        if contours:
            roi_contours = []
            for contour in contours:
                adjusted_contour = contour.copy()
                adjusted_contour[:, :, 1] += self.roi_y
                roi_contours.append(adjusted_contour)
            cv2.drawContours(frame, roi_contours, -1, (0, 255, 255), 2)
        
        # 이진화 이미지 표시
        binary_colored = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
        binary_resized = cv2.resize(binary_colored, (200, 100))
        frame[10:110, 10:210] = binary_resized
        cv2.rectangle(frame, (10, 10), (210, 110), (255, 255, 255), 2)
        
        # 상태 정보 표시
        status_color = (0, 255, 0) if self.tracing_active else (0, 0, 255)
        status_text = "ACTIVE" if self.tracing_active else "STOPPED"
        cv2.putText(frame, f"Status: {status_text}", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        cv2.putText(frame, f"Line: {'YES' if self.line_detected else 'NO'}", (10, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Steering: {self.current_steering:.2f}", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Speed: {self.base_speed}", (10, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"FPS: {self.fps}", (10, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

# 전역 라인 트레이서 인스턴스
tracer = WebLineTracer()

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

@app.route('/status')
def get_status():
    return jsonify({
        'line_detected': tracer.line_detected,
        'steering': tracer.current_steering,
        'speed': tracer.base_speed,
        'fps': tracer.fps,
        'tracing_active': tracer.tracing_active
    })

if __name__ == '__main__':
    print("🤖 패스파인더 웹 라인 트레이싱 서버 시작!")
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