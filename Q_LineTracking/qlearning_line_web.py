"""
qlearning_line_web.py - Q-Learning 라인 트레이싱 웹 인터페이스
실시간 훈련 모니터링 및 제어
"""

from flask import Flask, render_template_string, Response, request, jsonify
import json
import threading
import time
import os
import cv2
import base64
import numpy as np
from picamera2 import Picamera2
from qlearning_line_tracker import LineTrackingQLearning

app = Flask(__name__)

# HTML 템플릿
html = """
<!doctype html>
<html>
<head>
    <title>Q-Learning 라인 트레이싱 제어판</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f0f0f0; 
        }
        .container { 
            max-width: 1600px; 
            margin: 0 auto; 
        }
        h1 { 
            color: #333; 
            text-align: center; 
        }
        .dashboard { 
            display: grid; 
            grid-template-columns: 1fr 1fr 1fr; 
            gap: 20px; 
            margin: 20px 0; 
        }
        .panel { 
            background: white; 
            padding: 20px; 
            border-radius: 10px; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.1); 
        }
        .control-panel { 
            grid-column: 1 / -1; 
        }
        .camera-panel {
            background: #e8f4fd;
            text-align: center;
        }
        .status-panel { 
            background: #f0f8e8; 
        }
        .training-panel { 
            background: #fff8e8; 
        }
        .chart-panel { 
            background: #f8e8f8; 
            grid-column: 1 / -1;
        }
        button { 
            background: #007bff; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            border-radius: 5px; 
            cursor: pointer; 
            margin: 5px; 
            font-size: 14px;
        }
        button:hover { background: #0056b3; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        button.danger { background: #dc3545; }
        button.danger:hover { background: #c82333; }
        button.success { background: #28a745; }
        button.success:hover { background: #218838; }
        input[type="range"] { 
            width: 200px; 
            margin: 0 10px; 
        }
        input[type="number"], input[type="text"] {
            padding: 5px;
            border: 1px solid #ddd;
            border-radius: 3px;
            margin: 5px;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin: 15px 0;
        }
        .metric-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #007bff;
        }
        .metric-value {
            font-size: 20px;
            font-weight: bold;
            color: #333;
        }
        .metric-label {
            font-size: 11px;
            color: #666;
            margin-top: 5px;
        }
        .camera-feed {
            max-width: 100%;
            border: 2px solid #ddd;
            border-radius: 8px;
        }
        .log-area {
            background: #000;
            color: #0f0;
            padding: 15px;
            border-radius: 5px;
            height: 150px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 12px;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #ddd;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #45a049);
            width: 0%;
            transition: width 0.3s ease;
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <h1>🤖 Q-Learning 라인 트레이싱 제어판</h1>
        
        <div class="dashboard">
            <!-- 제어 패널 -->
            <div class="panel control-panel">
                <h3>🎮 훈련 제어</h3>
                <button id="startBtn" onclick="startTraining()" class="success">훈련 시작</button>
                <button id="stopBtn" onclick="stopTraining()" class="danger" disabled>훈련 중단</button>
                <button onclick="resetAgent()">에이전트 리셋</button>
                <button onclick="saveModel()">모델 저장</button>
                <button onclick="loadModel()">모델 로드</button>
                <button onclick="runTrained()">훈련된 모델 실행</button>
                
                <div style="margin: 20px 0;">
                    <label>에피소드 수: <input type="number" id="episodes" value="200" min="1" max="5000"></label>
                    <label>최대 스텝: <input type="number" id="maxSteps" value="1000" min="10" max="3000"></label>
                </div>
            </div>
            
            <!-- 카메라 피드 -->
            <div class="panel camera-panel">
                <h3>📹 카메라 피드</h3>
                <div style="margin-bottom: 10px;">
                    <span>상태: </span><span id="cameraStatus" style="font-weight: bold;">확인 중...</span>
                </div>
                <img id="cameraFeed" class="camera-feed" src="" alt="카메라 피드">
                <div style="margin-top: 10px;">
                    <button onclick="initCamera()" class="success">카메라 초기화</button>
                    <button onclick="toggleCamera()">카메라 토글</button>
                    <button onclick="captureFrame()">프레임 캡처</button>
                </div>
            </div>
            
            <!-- 상태 패널 -->
            <div class="panel status-panel">
                <h3>📊 현재 상태</h3>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value" id="currentEpisode">0</div>
                        <div class="metric-label">에피소드</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="currentStep">0</div>
                        <div class="metric-label">스텝</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="currentReward">0</div>
                        <div class="metric-label">보상</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="linePosition">160</div>
                        <div class="metric-label">라인 위치</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="lineDetected">❌</div>
                        <div class="metric-label">라인 검출</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="exploration">100%</div>
                        <div class="metric-label">탐험률</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="qTableSize">0</div>
                        <div class="metric-label">Q-Table</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="currentAction">-</div>
                        <div class="metric-label">현재 액션</div>
                    </div>
                </div>
                
                <div style="margin: 15px 0;">
                    <strong>현재 상태:</strong> <span id="currentState">-</span><br>
                    <strong>훈련 상태:</strong> <span id="trainingStatus">대기 중</span>
                </div>
                
                <div class="progress-bar">
                    <div class="progress-fill" id="episodeProgress"></div>
                </div>
                <div style="text-align: center; font-size: 12px; margin-top: 5px;">
                    에피소드 진행률
                </div>
            </div>
            
            <!-- 파라미터 조정 패널 -->
            <div class="panel training-panel">
                <h3>⚙️ Q-Learning 파라미터</h3>
                
                <div style="margin: 10px 0;">
                    <label>학습률 (α): <span id="learningRateValue">0.15</span></label><br>
                    <input type="range" id="learningRate" min="0.01" max="0.5" step="0.01" value="0.15" 
                           onchange="updateParameter('learning_rate', this.value)">
                </div>
                
                <div style="margin: 10px 0;">
                    <label>할인 인수 (γ): <span id="discountValue">0.9</span></label><br>
                    <input type="range" id="discount" min="0.1" max="1.0" step="0.01" value="0.9" 
                           onchange="updateParameter('discount_factor', this.value)">
                </div>
                
                <div style="margin: 10px 0;">
                    <label>탐험률 감소: <span id="decayValue">0.998</span></label><br>
                    <input type="range" id="decay" min="0.99" max="0.999" step="0.001" value="0.998" 
                           onchange="updateParameter('exploration_decay', this.value)">
                </div>
                
                <div style="margin: 10px 0;">
                    <label>라인 임계값: <span id="thresholdValue">50</span></label><br>
                    <input type="range" id="threshold" min="20" max="100" step="5" value="50" 
                           onchange="updateParameter('line_threshold', this.value)">
                </div>
                
                <div style="margin: 10px 0;">
                    <label>기본 속도: <span id="baseSpeedValue">35</span></label><br>
                    <input type="range" id="baseSpeed" min="20" max="60" step="5" value="35" 
                           onchange="updateParameter('base_speed', this.value)">
                </div>
            </div>
            
            <!-- 차트 패널 -->
            <div class="panel chart-panel">
                <h3>📈 학습 진행 차트</h3>
                <canvas id="rewardChart" width="800" height="300"></canvas>
                <button onclick="resetChart()">차트 리셋</button>
            </div>
        </div>
        
        <!-- 로그 패널 -->
        <div class="panel">
            <h3>📝 실시간 로그</h3>
            <div class="log-area" id="logArea"></div>
            <button onclick="clearLog()">로그 지우기</button>
        </div>
    </div>

    <script>
        // 차트 초기화
        const ctx = document.getElementById('rewardChart').getContext('2d');
        const rewardChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '에피소드 보상',
                    data: [],
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.1
                }, {
                    label: '평균 보상 (10에피소드)',
                    data: [],
                    borderColor: '#FF9800',
                    backgroundColor: 'rgba(255, 152, 0, 0.1)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });

        let isTraining = false;
        let totalEpisodes = 0;
        let cameraEnabled = true;

        // 훈련 시작
        function startTraining() {
            const episodes = document.getElementById('episodes').value;
            const maxSteps = document.getElementById('maxSteps').value;
            
            fetch('/start_training', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({episodes: parseInt(episodes), max_steps: parseInt(maxSteps)})
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'started') {
                    isTraining = true;
                    totalEpisodes = parseInt(episodes);
                    document.getElementById('startBtn').disabled = true;
                    document.getElementById('stopBtn').disabled = false;
                    document.getElementById('trainingStatus').textContent = '훈련 중';
                    addLog('🚀 라인 트레이싱 훈련 시작!');
                }
            });
        }

        // 훈련 중단
        function stopTraining() {
            fetch('/stop_training', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                isTraining = false;
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                document.getElementById('trainingStatus').textContent = '중단됨';
                addLog('⏹️ 훈련 중단');
            });
        }

        // 훈련된 모델 실행
        function runTrained() {
            const maxSteps = prompt('최대 실행 스텝 수:', '2000');
            if (maxSteps) {
                fetch('/run_trained', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({max_steps: parseInt(maxSteps)})
                })
                .then(response => response.json())
                .then(data => {
                    addLog('🎮 훈련된 모델 실행 시작');
                });
            }
        }

        // 파라미터 업데이트
        function updateParameter(param, value) {
            fetch('/update_parameter', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({parameter: param, value: parseFloat(value)})
            });
            
            // UI 업데이트
            if (param === 'learning_rate') {
                document.getElementById('learningRateValue').textContent = value;
            } else if (param === 'discount_factor') {
                document.getElementById('discountValue').textContent = value;
            } else if (param === 'exploration_decay') {
                document.getElementById('decayValue').textContent = value;
            } else if (param === 'line_threshold') {
                document.getElementById('thresholdValue').textContent = value;
            } else if (param === 'base_speed') {
                document.getElementById('baseSpeedValue').textContent = value;
            }
        }

        // 카메라 초기화
        function initCamera() {
            fetch('/init_camera', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    addLog('📹 ' + data.message);
                    updateCameraStatus();
                    // 카메라 초기화 후 피드 시작
                    setTimeout(updateCamera, 1000);
                } else {
                    addLog('❌ ' + data.message);
                }
            })
            .catch(error => {
                addLog('❌ 카메라 초기화 요청 실패: ' + error);
            });
        }

        // 카메라 토글
        function toggleCamera() {
            cameraEnabled = !cameraEnabled;
            if (!cameraEnabled) {
                document.getElementById('cameraFeed').src = '';
                addLog('📹 카메라 피드 비활성화');
            } else {
                addLog('📹 카메라 피드 활성화');
                updateCamera();
            }
        }

        // 카메라 상태 업데이트
        function updateCameraStatus() {
            fetch('/camera_status')
            .then(response => response.json())
            .then(data => {
                const statusElement = document.getElementById('cameraStatus');
                if (data.status === 'connected') {
                    statusElement.textContent = '연결됨 ✅';
                    statusElement.style.color = 'green';
                } else if (data.status === 'disconnected') {
                    statusElement.textContent = '연결 끊김 ❌';
                    statusElement.style.color = 'red';
                } else {
                    statusElement.textContent = '초기화 필요 ⚠️';
                    statusElement.style.color = 'orange';
                }
            })
            .catch(error => {
                document.getElementById('cameraStatus').textContent = '상태 확인 실패 ❌';
                document.getElementById('cameraStatus').style.color = 'red';
            });
        }

        // 프레임 캡처
        function captureFrame() {
            fetch('/capture_frame')
            .then(response => response.json())
            .then(data => {
                addLog('📸 프레임 캡처 완료');
            });
        }

        // 모델 저장
        function saveModel() {
            fetch('/save_model', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                addLog('💾 모델 저장: ' + data.filename);
            });
        }

        // 모델 로드
        function loadModel() {
            const filename = prompt('로드할 모델 파일명:', 'final_line_model.json');
            if (filename) {
                fetch('/load_model', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({filename: filename})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        addLog('📂 모델 로드 성공: ' + filename);
                    } else {
                        addLog('❌ 모델 로드 실패: ' + data.message);
                    }
                });
            }
        }

        // 에이전트 리셋
        function resetAgent() {
            if (confirm('에이전트를 리셋하시겠습니까?')) {
                fetch('/reset_agent', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    addLog('🔄 에이전트 리셋 완료');
                    resetChart();
                });
            }
        }

        // 차트 리셋
        function resetChart() {
            rewardChart.data.labels = [];
            rewardChart.data.datasets[0].data = [];
            rewardChart.data.datasets[1].data = [];
            rewardChart.update();
        }

        // 로그 추가
        function addLog(message) {
            const logArea = document.getElementById('logArea');
            const timestamp = new Date().toLocaleTimeString();
            logArea.innerHTML += `[${timestamp}] ${message}\n`;
            logArea.scrollTop = logArea.scrollHeight;
        }

        // 로그 지우기
        function clearLog() {
            document.getElementById('logArea').innerHTML = '';
        }

        // 상태 업데이트
        function updateStatus() {
            fetch('/status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('currentEpisode').textContent = data.episode;
                document.getElementById('currentStep').textContent = data.step;
                document.getElementById('currentReward').textContent = data.reward.toFixed(1);
                document.getElementById('linePosition').textContent = data.line_position;
                document.getElementById('lineDetected').textContent = data.line_detected ? '✅' : '❌';
                document.getElementById('exploration').textContent = (data.exploration * 100).toFixed(1) + '%';
                document.getElementById('qTableSize').textContent = data.q_table_size;
                document.getElementById('currentAction').textContent = data.action;
                document.getElementById('currentState').textContent = data.state;
                
                // 진행률 업데이트
                if (totalEpisodes > 0) {
                    const progress = (data.episode / totalEpisodes) * 100;
                    document.getElementById('episodeProgress').style.width = progress + '%';
                }
                
                // 차트 업데이트
                if (data.new_episode_reward !== null) {
                    updateChart(data.episode, data.new_episode_reward, data.avg_reward);
                }
                
                // 훈련 완료 체크
                if (data.training_complete && isTraining) {
                    isTraining = false;
                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('stopBtn').disabled = true;
                    document.getElementById('trainingStatus').textContent = '완료';
                    addLog('🎉 훈련 완료!');
                }
            });
        }

        // 카메라 피드 업데이트
        function updateCamera() {
            if (cameraEnabled) {
                const img = document.getElementById('cameraFeed');
                const timestamp = new Date().getTime();
                
                // 이미지 로드 에러 처리
                img.onerror = function() {
                    console.log('카메라 피드 로드 실패, 재시도...');
                    setTimeout(() => {
                        if (cameraEnabled) {
                            img.src = '/video_feed?' + new Date().getTime();
                        }
                    }, 2000);
                };
                
                // 이미지 로드 성공 처리
                img.onload = function() {
                    console.log('카메라 피드 로드 성공');
                };
                
                img.src = '/video_feed?' + timestamp;
            }
        }

        // 차트 업데이트
        function updateChart(episode, reward, avgReward) {
            rewardChart.data.labels.push(episode);
            rewardChart.data.datasets[0].data.push(reward);
            rewardChart.data.datasets[1].data.push(avgReward);
            
            // 최대 100개 포인트 유지
            if (rewardChart.data.labels.length > 100) {
                rewardChart.data.labels.shift();
                rewardChart.data.datasets[0].data.shift();
                rewardChart.data.datasets[1].data.shift();
            }
            
            rewardChart.update('none');
        }

        // 초기화
        document.addEventListener('DOMContentLoaded', function() {
            setInterval(updateStatus, 1000);  // 1초마다 상태 업데이트
            setInterval(updateCamera, 2000);  // 2초마다 카메라 업데이트
            setInterval(updateCameraStatus, 5000);  // 5초마다 카메라 상태 확인
            
            // 페이지 로드 시 즉시 카메라 상태 확인
            updateCameraStatus();
            setTimeout(updateCamera, 1000);  // 1초 후 카메라 피드 시작
        });
    </script>
</body>
</html>
"""

# 전역 Q-Learning 에이전트
agent = None
training_thread = None
training_active = False

@app.route('/')
def index():
    return render_template_string(html)

@app.route('/video_feed')
def video_feed():
    """비디오 스트림"""
    def generate():
        global agent
        
        # 에이전트가 없으면 초기화
        if agent is None:
            try:
                agent = LineTrackingQLearning()
                print("📹 카메라 에이전트 초기화 완료")
            except Exception as e:
                print(f"❌ 에이전트 초기화 실패: {e}")
                # 에러 이미지 생성
                error_frame = create_error_frame("에이전트 초기화 실패")
                while True:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + error_frame + b'\r\n')
                    time.sleep(1)
        
        # 카메라 상태 확인 및 재시도
        camera_retry_count = 0
        max_retries = 3
        
        while True:
            try:
                if agent and agent.camera:
                    frame = agent.capture_frame()
                    if frame is not None:
                        # 프레임 처리하여 라인 검출 시각화
                        line_x, line_detected = agent.process_frame(frame)
                        
                        # ROI 표시
                        roi_y = agent.config['roi_y_offset']
                        roi_height = agent.config['roi_height']
                        cv2.rectangle(frame, (0, roi_y), (320, roi_y + roi_height), (0, 255, 0), 2)
                        
                        # 라인 위치 표시
                        if line_detected:
                            cv2.circle(frame, (line_x, roi_y + roi_height//2), 10, (0, 0, 255), -1)
                            cv2.putText(frame, f'Line: {line_x}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        else:
                            cv2.putText(frame, 'No Line', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                        # 중앙선 표시
                        cv2.line(frame, (160, 0), (160, 240), (255, 255, 0), 1)
                        
                        # 상태 정보 추가
                        cv2.putText(frame, f'Picamera2 OK', (10, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                        
                        # JPEG 인코딩
                        _, buffer = cv2.imencode('.jpg', frame)
                        frame_bytes = buffer.tobytes()
                        
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                        
                        camera_retry_count = 0  # 성공 시 재시도 카운트 리셋
                    else:
                        # 프레임 읽기 실패
                        camera_retry_count += 1
                        if camera_retry_count <= max_retries:
                            print(f"⚠️ 프레임 읽기 실패, 재시도 {camera_retry_count}/{max_retries}")
                            time.sleep(0.5)
                            continue
                        else:
                            # 에러 프레임 생성
                            error_frame = create_error_frame("프레임 읽기 실패")
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + error_frame + b'\r\n')
                else:
                    # 카메라가 없음
                    camera_retry_count += 1
                    if camera_retry_count <= max_retries:
                        print(f"⚠️ 카메라 연결 실패, 재시도 {camera_retry_count}/{max_retries}")
                        # 카메라 재초기화 시도
                        try:
                            if agent:
                                agent.camera.stop()
                                agent.camera.close()
                                time.sleep(1)
                                
                                # Picamera2 재초기화
                                agent.camera = Picamera2()
                                agent.camera.preview_configuration.main.size = (320, 240)
                                agent.camera.preview_configuration.main.format = "RGB888"
                                agent.camera.configure("preview")
                                agent.camera.start()
                                time.sleep(2)
                                continue
                        except Exception as e:
                            print(f"카메라 재초기화 실패: {e}")
                    
                    # 에러 프레임 생성
                    error_frame = create_error_frame("카메라 연결 실패")
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + error_frame + b'\r\n')
                
            except Exception as e:
                print(f"비디오 스트림 오류: {e}")
                error_frame = create_error_frame(f"스트림 오류: {str(e)[:30]}")
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + error_frame + b'\r\n')
            
            time.sleep(0.1)  # CPU 사용률 조절
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

def create_error_frame(message):
    """에러 메시지가 포함된 프레임 생성"""
    # 320x240 검은 이미지 생성
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    
    # 에러 메시지 텍스트 추가
    cv2.putText(frame, "Camera Error", (80, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    cv2.putText(frame, message, (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(frame, "Check camera connection", (40, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    
    # JPEG 인코딩
    _, buffer = cv2.imencode('.jpg', frame)
    return buffer.tobytes()

@app.route('/start_training', methods=['POST'])
def start_training():
    global agent, training_thread, training_active
    
    data = request.get_json()
    episodes = data.get('episodes', 200)
    max_steps = data.get('max_steps', 1000)
    
    if not training_active:
        if agent is None:
            agent = LineTrackingQLearning()
        
        training_active = True
        training_thread = threading.Thread(target=run_training, args=(episodes, max_steps))
        training_thread.start()
        
        return jsonify({'status': 'started'})
    else:
        return jsonify({'status': 'already_running'})

def run_training(episodes, max_steps):
    global training_active
    try:
        agent.start_training(episodes)
    except Exception as e:
        print(f"Training error: {e}")
    finally:
        training_active = False

@app.route('/stop_training', methods=['POST'])
def stop_training():
    global training_active
    if agent:
        agent.running = False
    training_active = False
    return jsonify({'status': 'stopped'})

@app.route('/run_trained', methods=['POST'])
def run_trained():
    global agent
    if agent:
        data = request.get_json()
        max_steps = data.get('max_steps', 2000)
        
        # 별도 스레드에서 실행
        thread = threading.Thread(target=agent.run_trained_model, args=(max_steps,))
        thread.start()
        
        return jsonify({'status': 'started'})
    return jsonify({'status': 'error'})

@app.route('/update_parameter', methods=['POST'])
def update_parameter():
    global agent
    if agent:
        data = request.get_json()
        param = data.get('parameter')
        value = data.get('value')
        
        if param in agent.config:
            agent.config[param] = value
            return jsonify({'status': 'updated'})
    
    return jsonify({'status': 'error'})

@app.route('/save_model', methods=['POST'])
def save_model():
    global agent
    if agent:
        data = request.get_json() or {}
        filename = data.get('filename')
        filepath = agent.save_model(filename)
        return jsonify({'status': 'saved', 'filename': os.path.basename(filepath)})
    
    return jsonify({'status': 'error', 'message': 'No agent available'})

@app.route('/load_model', methods=['POST'])
def load_model():
    global agent
    
    data = request.get_json()
    filename = data.get('filename')
    
    if agent is None:
        agent = LineTrackingQLearning()
    
    filepath = os.path.join(agent.config['models_dir'], filename)
    if agent.load_model(filepath):
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to load model'})

@app.route('/reset_agent', methods=['POST'])
def reset_agent():
    global agent
    if agent:
        agent.q_table = {}
        agent.episode = 0
        agent.episode_rewards = []
        agent.episode_steps = []
        return jsonify({'status': 'reset'})
    
    return jsonify({'status': 'error'})

@app.route('/capture_frame', methods=['GET'])
def capture_frame():
    global agent
    if agent:
        frame = agent.capture_frame()
        if frame is not None:
            return jsonify({'status': 'captured'})
    return jsonify({'status': 'error'})

@app.route('/init_camera', methods=['POST'])
def init_camera():
    """카메라 초기화"""
    global agent
    try:
        if agent is None:
            agent = LineTrackingQLearning()
        else:
            # 기존 카메라 해제 후 재초기화
            if hasattr(agent, 'camera') and agent.camera:
                try:
                    agent.camera.stop()
                    agent.camera.close()
                except:
                    pass
            
            # Picamera2 재초기화
            agent.camera = Picamera2()
            agent.camera.preview_configuration.main.size = (320, 240)
            agent.camera.preview_configuration.main.format = "RGB888"
            agent.camera.configure("preview")
            agent.camera.start()
            
            # 카메라 워밍업
            time.sleep(2)
            for _ in range(5):
                frame = agent.capture_frame()
                if frame is not None:
                    break
                time.sleep(0.1)
        
        if agent.camera:
            return jsonify({'status': 'success', 'message': 'Picamera2 초기화 성공'})
        else:
            return jsonify({'status': 'error', 'message': 'Picamera2 초기화 실패'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'카메라 초기화 실패: {str(e)}'})

@app.route('/camera_status', methods=['GET'])
def camera_status():
    """카메라 상태 확인"""
    global agent
    if agent and hasattr(agent, 'camera') and agent.camera:
        try:
            # 테스트 프레임 캡처로 상태 확인
            test_frame = agent.capture_frame()
            is_working = test_frame is not None
            return jsonify({
                'status': 'connected' if is_working else 'disconnected',
                'is_opened': is_working
            })
        except:
            return jsonify({
                'status': 'disconnected',
                'is_opened': False
            })
    else:
        return jsonify({
            'status': 'not_initialized',
            'is_opened': False
        })

@app.route('/status')
def get_status():
    global agent, training_active
    
    if agent is None:
        return jsonify({
            'episode': 0,
            'step': 0,
            'reward': 0,
            'line_position': 160,
            'line_detected': False,
            'exploration': 1.0,
            'q_table_size': 0,
            'action': '-',
            'state': '-',
            'training_active': False,
            'training_complete': False,
            'new_episode_reward': None,
            'avg_reward': 0
        })
    
    # 새 에피소드 보상 확인
    new_episode_reward = None
    avg_reward = 0
    if len(agent.episode_rewards) > 0:
        if hasattr(agent, '_last_reported_episode'):
            if agent.episode > agent._last_reported_episode:
                new_episode_reward = agent.episode_rewards[-1]
                agent._last_reported_episode = agent.episode
        else:
            agent._last_reported_episode = agent.episode
            if len(agent.episode_rewards) > 0:
                new_episode_reward = agent.episode_rewards[-1]
        
        # 최근 10 에피소드 평균
        recent_rewards = agent.episode_rewards[-10:]
        avg_reward = sum(recent_rewards) / len(recent_rewards)
    
    # 현재 라인 위치 측정 (안전하게 처리)
    line_position = 160
    line_detected = False
    try:
        if hasattr(agent, 'camera') and agent.camera:
            frame = agent.capture_frame()
            if frame is not None:
                line_position, line_detected = agent.process_frame(frame)
    except Exception as e:
        # 카메라 오류 시 기본값 유지
        print(f"Status 카메라 오류 (무시됨): {e}")
        pass
    
    return jsonify({
        'episode': agent.episode,
        'step': agent.steps,
        'reward': agent.total_reward,
        'line_position': line_position,
        'line_detected': line_detected,
        'exploration': agent.config['exploration_rate'],
        'q_table_size': len(agent.q_table),
        'action': agent._get_action_name(agent.last_action) if hasattr(agent, 'last_action') else '-',
        'state': agent.current_state,
        'training_active': training_active,
        'training_complete': not training_active and agent.episode > 0,
        'new_episode_reward': new_episode_reward,
        'avg_reward': avg_reward
    })

if __name__ == '__main__':
    print("🌐 Q-Learning 라인 트레이싱 웹 인터페이스 시작!")
    print("브라우저에서 http://라즈베리파이IP:5001 으로 접속하세요")
    
    # models 디렉토리 생성
    os.makedirs('Q_LineTracking/models', exist_ok=True)
    
    try:
        app.run(host='0.0.0.0', port=5001, debug=False)
    except KeyboardInterrupt:
        print("\n서버 종료 중...")
        if agent:
            agent.cleanup()
    finally:
        print("정리 완료!") 