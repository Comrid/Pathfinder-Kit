"""
qlearning_web.py - Q-Learning 웹 인터페이스
실시간 훈련 모니터링 및 제어
"""

from flask import Flask, render_template_string, Response, request, jsonify
import json
import threading
import time
import os
from pathfinder_qlearning import PathfinderQLearning

app = Flask(__name__)

# HTML 템플릿
html = """
<!doctype html>
<html>
<head>
    <title>패스파인더 Q-Learning 제어판</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f0f0f0; 
        }
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
        }
        h1 { 
            color: #333; 
            text-align: center; 
        }
        .dashboard { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
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
        .status-panel { 
            background: #e8f4fd; 
        }
        .training-panel { 
            background: #f0f8e8; 
        }
        .chart-panel { 
            background: #fff8e8; 
        }
        .model-panel { 
            background: #f8e8f8; 
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
        .status-item { 
            display: inline-block; 
            margin: 5px 10px; 
            padding: 8px 12px; 
            background: white; 
            border-radius: 5px; 
            font-size: 14px;
            border-left: 4px solid #007bff;
        }
        .log-area {
            background: #000;
            color: #0f0;
            padding: 15px;
            border-radius: 5px;
            height: 200px;
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
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
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
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        .metric-label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <h1>🤖 패스파인더 Q-Learning 제어판</h1>
        
        <div class="dashboard">
            <!-- 제어 패널 -->
            <div class="panel control-panel">
                <h3>🎮 훈련 제어</h3>
                <button id="startBtn" onclick="startTraining()" class="success">훈련 시작</button>
                <button id="stopBtn" onclick="stopTraining()" class="danger" disabled>훈련 중단</button>
                <button onclick="resetAgent()">에이전트 리셋</button>
                <button onclick="saveModel()">모델 저장</button>
                <button onclick="loadModel()">모델 로드</button>
                
                <div style="margin: 20px 0;">
                    <label>에피소드 수: <input type="number" id="episodes" value="100" min="1" max="10000"></label>
                    <label>최대 스텝: <input type="number" id="maxSteps" value="500" min="10" max="2000"></label>
                </div>
            </div>
            
            <!-- 상태 패널 -->
            <div class="panel status-panel">
                <h3>📊 현재 상태</h3>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value" id="currentEpisode">0</div>
                        <div class="metric-label">현재 에피소드</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="currentStep">0</div>
                        <div class="metric-label">현재 스텝</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="currentReward">0</div>
                        <div class="metric-label">현재 보상</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="distance">0</div>
                        <div class="metric-label">거리 (cm)</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="exploration">100%</div>
                        <div class="metric-label">탐험률</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="qTableSize">0</div>
                        <div class="metric-label">Q-Table 크기</div>
                    </div>
                </div>
                
                <div style="margin: 15px 0;">
                    <strong>현재 액션:</strong> <span id="currentAction">-</span><br>
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
                    <label>학습률 (α): <span id="learningRateValue">0.1</span></label><br>
                    <input type="range" id="learningRate" min="0.01" max="1.0" step="0.01" value="0.1" 
                           onchange="updateParameter('learning_rate', this.value)">
                </div>
                
                <div style="margin: 10px 0;">
                    <label>할인 인수 (γ): <span id="discountValue">0.95</span></label><br>
                    <input type="range" id="discount" min="0.1" max="1.0" step="0.01" value="0.95" 
                           onchange="updateParameter('discount_factor', this.value)">
                </div>
                
                <div style="margin: 10px 0;">
                    <label>탐험률 감소: <span id="decayValue">0.995</span></label><br>
                    <input type="range" id="decay" min="0.9" max="0.999" step="0.001" value="0.995" 
                           onchange="updateParameter('exploration_decay', this.value)">
                </div>
                
                <div style="margin: 10px 0;">
                    <label>안전 거리: <span id="safeDistanceValue">20</span> cm</label><br>
                    <input type="range" id="safeDistance" min="10" max="50" step="1" value="20" 
                           onchange="updateParameter('safe_distance', this.value)">
                </div>
            </div>
            
            <!-- 차트 패널 -->
            <div class="panel chart-panel">
                <h3>📈 학습 진행 차트</h3>
                <canvas id="rewardChart" width="400" height="200"></canvas>
                <button onclick="resetChart()">차트 리셋</button>
            </div>
            
            <!-- 모델 관리 패널 -->
            <div class="panel model-panel">
                <h3>💾 모델 관리</h3>
                <div>
                    <label>모델 파일명: <input type="text" id="modelName" value="my_model.json"></label>
                    <button onclick="saveModelAs()">다른 이름으로 저장</button>
                </div>
                
                <div style="margin: 15px 0;">
                    <h4>저장된 모델 목록:</h4>
                    <div id="modelList" style="max-height: 150px; overflow-y: auto;">
                        로딩 중...
                    </div>
                </div>
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
                    addLog('🚀 훈련 시작!');
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
            } else if (param === 'safe_distance') {
                document.getElementById('safeDistanceValue').textContent = value;
            }
        }

        // 모델 저장
        function saveModel() {
            fetch('/save_model', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                addLog('💾 모델 저장: ' + data.filename);
                loadModelList();
            });
        }

        // 다른 이름으로 저장
        function saveModelAs() {
            const filename = document.getElementById('modelName').value;
            fetch('/save_model', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({filename: filename})
            })
            .then(response => response.json())
            .then(data => {
                addLog('💾 모델 저장: ' + data.filename);
                loadModelList();
            });
        }

        // 모델 로드
        function loadModel() {
            const filename = prompt('로드할 모델 파일명을 입력하세요:', 'final_model.json');
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
            if (confirm('에이전트를 리셋하시겠습니까? (Q-table이 초기화됩니다)')) {
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

        // 모델 목록 로드
        function loadModelList() {
            fetch('/get_models')
            .then(response => response.json())
            .then(data => {
                const modelList = document.getElementById('modelList');
                modelList.innerHTML = '';
                data.models.forEach(model => {
                    const div = document.createElement('div');
                    div.innerHTML = `
                        <span>${model}</span>
                        <button onclick="loadSpecificModel('${model}')" style="margin-left: 10px; padding: 2px 8px; font-size: 12px;">로드</button>
                    `;
                    div.style.margin = '5px 0';
                    modelList.appendChild(div);
                });
            });
        }

        // 특정 모델 로드
        function loadSpecificModel(filename) {
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

        // 상태 업데이트
        function updateStatus() {
            fetch('/status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('currentEpisode').textContent = data.episode;
                document.getElementById('currentStep').textContent = data.step;
                document.getElementById('currentReward').textContent = data.reward.toFixed(1);
                document.getElementById('distance').textContent = data.distance.toFixed(1);
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
            loadModelList();
            setInterval(updateStatus, 1000);  // 1초마다 상태 업데이트
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

@app.route('/start_training', methods=['POST'])
def start_training():
    global agent, training_thread, training_active
    
    data = request.get_json()
    episodes = data.get('episodes', 100)
    max_steps = data.get('max_steps', 500)
    
    if not training_active:
        if agent is None:
            agent = PathfinderQLearning()
        
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
        agent = PathfinderQLearning()
    
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

@app.route('/get_models')
def get_models():
    models_dir = '6.QLearning/models'
    if os.path.exists(models_dir):
        models = [f for f in os.listdir(models_dir) if f.endswith('.json')]
        return jsonify({'models': models})
    else:
        return jsonify({'models': []})

@app.route('/status')
def get_status():
    global agent, training_active
    
    if agent is None:
        return jsonify({
            'episode': 0,
            'step': 0,
            'reward': 0,
            'distance': 0,
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
    
    # 현재 거리 측정
    try:
        distance = agent.get_distance()
    except:
        distance = 0
    
    return jsonify({
        'episode': agent.episode,
        'step': agent.steps,
        'reward': agent.total_reward,
        'distance': distance,
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
    print("🌐 Q-Learning 웹 인터페이스 시작!")
    print("브라우저에서 http://라즈베리파이IP:5000 으로 접속하세요")
    
    # models 디렉토리 생성
    os.makedirs('6.QLearning/models', exist_ok=True)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n서버 종료 중...")
        if agent:
            agent.cleanup()
    finally:
        print("정리 완료!") 