# 🤖 Q-Learning 라인 트레이싱 시스템

패스파인더 키트를 위한 강화학습 기반 라인 트레이싱 시스템입니다. Q-Learning 알고리즘을 사용하여 카메라로 검은색 라인을 따라가는 방법을 학습합니다.

## 📋 목차
- [시스템 개요](#시스템-개요)
- [설치 및 설정](#설치-및-설정)
- [사용법](#사용법)
- [웹 인터페이스](#웹-인터페이스)
- [Q-Learning 파라미터](#q-learning-파라미터)
- [학습 과정](#학습-과정)
- [문제 해결](#문제-해결)

## 🎯 시스템 개요

### 기존 PID vs Q-Learning 비교

| 특징 | PID 제어 | Q-Learning |
|------|----------|------------|
| **학습 방식** | 수동 튜닝 | 자동 학습 |
| **적응성** | 고정된 파라미터 | 환경에 적응 |
| **복잡한 상황** | 제한적 대응 | 유연한 대응 |
| **설정 난이도** | 높음 (전문 지식 필요) | 낮음 (자동 최적화) |
| **성능** | 즉시 최적 | 점진적 향상 |

### Q-Learning 라인 트레이싱의 장점

1. **자동 최적화**: 환경에 맞게 스스로 학습
2. **복잡한 상황 대응**: 곡선, 교차점, 끊어진 라인 등
3. **노이즈 내성**: 조명 변화, 그림자에 강함
4. **확장성**: 다양한 센서 정보 통합 가능

## 🔧 설치 및 설정

### 필요 라이브러리
```bash
pip install opencv-python numpy flask
```

### 하드웨어 요구사항
- Raspberry Pi Zero 2 W
- 160도 광각 카메라 모듈
- L298N 모터 드라이버
- DC 기어 모터 2개

### 파일 구조
```
Q_LineTracking/
├── qlearning_line_tracker.py    # 메인 Q-Learning 구현
├── qlearning_line_web.py        # 웹 인터페이스
├── models/                      # 저장된 모델들
└── README.md                    # 이 파일
```

## 🚀 사용법

### 1. 터미널 모드

```bash
cd Q_LineTracking
python qlearning_line_tracker.py
```

**메뉴 옵션:**
1. **새로운 훈련 시작**: 처음부터 학습
2. **기존 모델 로드 후 훈련 계속**: 저장된 모델에서 이어서 학습
3. **훈련된 모델로 라인 트레이싱**: 학습 완료된 모델로 실행
4. **종료**: 프로그램 종료

### 2. 웹 인터페이스 모드 (추천)

```bash
cd Q_LineTracking
python qlearning_line_web.py
```

브라우저에서 `http://라즈베리파이IP:5001` 접속

## 🌐 웹 인터페이스

### 주요 기능

#### 🎮 훈련 제어
- **훈련 시작/중단**: 실시간 학습 제어
- **에피소드 수 설정**: 학습할 에피소드 개수 (기본: 200)
- **최대 스텝 설정**: 에피소드당 최대 행동 수 (기본: 1000)
- **훈련된 모델 실행**: 학습 완료 후 실제 라인 트레이싱

#### 📹 실시간 카메라 피드
- **라이브 영상**: 실시간 카메라 화면
- **라인 검출 시각화**: 검출된 라인과 ROI 표시
- **중앙선 가이드**: 목표 위치 표시
- **프레임 캡처**: 특정 순간 저장

#### 📊 실시간 모니터링
- **현재 에피소드/스텝**: 학습 진행 상황
- **현재 보상**: 실시간 보상 값
- **라인 위치**: 검출된 라인의 X 좌표
- **라인 검출 상태**: ✅/❌ 표시
- **탐험률**: 현재 ε(epsilon) 값
- **Q-Table 크기**: 학습된 상태 수

#### ⚙️ 실시간 파라미터 조정
- **학습률 (α)**: 0.01 ~ 0.5 (기본: 0.15)
- **할인 인수 (γ)**: 0.1 ~ 1.0 (기본: 0.9)
- **탐험률 감소**: 0.99 ~ 0.999 (기본: 0.998)
- **라인 임계값**: 20 ~ 100 (기본: 50)
- **기본 속도**: 20 ~ 60 (기본: 35)

#### 📈 학습 진행 차트
- **에피소드별 보상**: 실시간 학습 성과
- **평균 보상**: 최근 10 에피소드 평균
- **학습 곡선**: 시간에 따른 성능 향상

## ⚙️ Q-Learning 파라미터

### 핵심 파라미터

#### 학습률 (Learning Rate, α)
```python
learning_rate = 0.15  # 기본값
```
- **높음 (0.3-0.5)**: 빠른 학습, 불안정할 수 있음
- **중간 (0.1-0.2)**: 균형잡힌 학습 (권장)
- **낮음 (0.01-0.1)**: 안정적이지만 느린 학습

#### 할인 인수 (Discount Factor, γ)
```python
discount_factor = 0.9  # 기본값
```
- **높음 (0.9-0.99)**: 장기적 보상 중시 (라인 트레이싱에 적합)
- **낮음 (0.1-0.5)**: 즉시 보상 중시

#### 탐험률 (Exploration Rate, ε)
```python
exploration_rate = 1.0      # 초기값 (100% 탐험)
exploration_min = 0.05      # 최소값 (5% 탐험)
exploration_decay = 0.998   # 감소율
```

### 라인 트레이싱 설정

#### 상태 공간
```python
line_bins = 7              # 라인 위치 구간 수
```
화면을 7개 구간으로 나누어 라인 위치를 이산화:
- 구간 0: 왼쪽 끝 (0-45px)
- 구간 1: 왼쪽 (46-91px)
- 구간 2: 왼쪽 중앙 (92-137px)
- 구간 3: 중앙 (138-183px) ← 목표
- 구간 4: 오른쪽 중앙 (184-229px)
- 구간 5: 오른쪽 (230-275px)
- 구간 6: 오른쪽 끝 (276-320px)

#### 액션 공간
```python
actions = [
    (35, 35),    # 0: 직진
    (20, 35),    # 1: 약간 좌회전
    (35, 20),    # 2: 약간 우회전
    (10, 50),    # 3: 강한 좌회전
    (50, 10),    # 4: 강한 우회전
    (0, 35),     # 5: 제자리 좌회전
    (35, 0),     # 6: 제자리 우회전
    (15, 15),    # 7: 느린 직진
]
```

#### 보상 시스템
```python
rewards = {
    'center_bonus': 15,      # 중앙에 있을 때 (최고 보상)
    'on_line': 10,           # 라인 위에 있을 때
    'near_line': 5,          # 라인 근처에 있을 때
    'off_line': -5,          # 라인에서 벗어났을 때
    'line_lost': -20,        # 라인을 완전히 놓쳤을 때 (페널티)
    'step_penalty': -0.5,    # 스텝 페널티 (효율성 유도)
}
```

## 📊 학습 과정

### 학습 단계별 특징

#### 1단계: 초기 탐험 (0-50 에피소드)
- **특징**: 랜덤한 움직임, 높은 ε 값 (1.0 → 0.6)
- **목적**: 다양한 상황 경험, 기본 상태-액션 매핑
- **예상 보상**: -50 ~ -10 (많은 실수)

#### 2단계: 기본 학습 (50-100 에피소드)
- **특징**: 점진적 개선, 중간 ε 값 (0.6 → 0.3)
- **목적**: 기본적인 라인 추적 능력 습득
- **예상 보상**: -10 ~ 20 (가끔 성공)

#### 3단계: 안정화 (100-150 에피소드)
- **특징**: 일관된 성능, 낮은 ε 값 (0.3 → 0.15)
- **목적**: 안정적인 라인 트레이싱
- **예상 보상**: 20 ~ 60 (대부분 성공)

#### 4단계: 최적화 (150+ 에피소드)
- **특징**: 최적 경로 탐색, 최소 ε 값 (0.15 → 0.05)
- **목적**: 부드럽고 효율적인 움직임
- **예상 보상**: 60 ~ 100+ (최적 성능)

### 성능 지표

#### Q-Table 크기 변화
- **초기**: 5-10 상태
- **중기**: 15-25 상태
- **후기**: 20-30 상태 (수렴)

#### 에피소드 길이
- **초기**: 50-200 스텝 (빨리 실패)
- **중기**: 200-500 스텝 (점진적 개선)
- **후기**: 800-1000 스텝 (최대 길이 달성)

## 🔧 고급 설정

### 환경별 최적화

#### 실내 형광등 환경
```python
config = {
    'line_threshold': 60,        # 높은 임계값
    'roi_height': 100,           # 넓은 ROI
    'min_line_area': 150,        # 큰 최소 면적
}
```

#### 자연광 환경
```python
config = {
    'line_threshold': 40,        # 낮은 임계값
    'roi_height': 80,            # 기본 ROI
    'min_line_area': 100,        # 기본 최소 면적
}
```

#### 어두운 환경
```python
config = {
    'line_threshold': 30,        # 매우 낮은 임계값
    'roi_height': 120,           # 넓은 ROI
    'min_line_area': 80,         # 작은 최소 면적
}
```

### 상태 공간 확장

#### 기본 상태 (현재)
```python
state = f"line{line_bin}"
```

#### 확장 상태 예시
```python
# 라인 위치 + 방향 정보
state = f"line{line_bin}_dir{direction_bin}"

# 라인 위치 + 속도 정보
state = f"line{line_bin}_speed{speed_bin}"

# 라인 위치 + 이전 액션
state = f"line{line_bin}_prev{prev_action}"
```

### 보상 함수 커스터마이징

#### 부드러운 움직임 장려
```python
def smooth_reward(self, line_x, line_detected, action_idx, prev_action):
    base_reward = self.get_reward(line_x, line_detected, action_idx)
    
    # 급격한 방향 전환 페널티
    if abs(action_idx - prev_action) > 2:
        base_reward -= 5
    
    # 직진 보너스 (라인이 중앙에 있을 때)
    if action_idx == 0 and abs(line_x - 160) < 30:
        base_reward += 3
    
    return base_reward
```

#### 속도 기반 보상
```python
def speed_reward(self, line_x, line_detected, action_idx):
    base_reward = self.get_reward(line_x, line_detected, action_idx)
    
    # 빠른 속도 보너스 (직선 구간)
    if action_idx in [0, 7] and abs(line_x - 160) < 20:
        base_reward += 2
    
    # 느린 속도 보너스 (곡선 구간)
    elif action_idx == 7 and abs(line_x - 160) > 50:
        base_reward += 1
    
    return base_reward
```

## 🐛 문제 해결

### 학습 관련 문제

#### 학습이 안 되는 경우
**증상**: 보상이 계속 음수, 성능 개선 없음
**원인**: 
- 학습률이 너무 낮음
- 탐험률이 너무 빨리 감소
- 보상 설계 문제

**해결책**:
```python
# 학습률 증가
learning_rate = 0.2

# 탐험률 감소 속도 조정
exploration_decay = 0.999
exploration_min = 0.1

# 보상 재조정
rewards['center_bonus'] = 20
rewards['step_penalty'] = -0.1
```

#### 과학습 (Overfitting)
**증상**: 특정 환경에서만 동작, 일반화 부족
**해결책**:
- 다양한 조명 조건에서 훈련
- 탐험률 최소값 증가 (0.1 이상)
- 정규화 기법 적용

#### 불안정한 학습
**증상**: 보상이 크게 요동침
**해결책**:
```python
# 할인 인수 증가 (장기적 관점)
discount_factor = 0.95

# 학습률 감소
learning_rate = 0.1

# 보상 평활화
def smoothed_reward(self, rewards_history):
    return np.mean(rewards_history[-5:])  # 최근 5개 평균
```

### 하드웨어 관련 문제

#### 카메라 인식 불량
**증상**: 라인 검출 실패, "No Line" 지속
**해결책**:
```python
# 임계값 조정
line_threshold = 30  # 더 낮게

# ROI 확장
roi_height = 120
roi_y_offset = 140

# 최소 면적 감소
min_line_area = 50
```

#### 모터 반응 지연
**증상**: 액션과 실제 움직임 불일치
**해결책**:
```python
# 액션 실행 후 대기 시간 증가
time.sleep(0.15)  # 0.1에서 0.15로

# 속도 조정
base_speed = 30  # 더 느리게
turn_speed = 45
```

#### 전원 부족
**증상**: 갑작스런 정지, 성능 저하
**해결책**:
- 배터리 충전 상태 확인
- 전압 강하 모듈 출력 확인
- 모터 속도 감소로 전력 소모 줄이기

### 성능 최적화

#### 메모리 사용량 최적화
```python
# Q-table 크기 제한
MAX_STATES = 100

def cleanup_qtable(self):
    if len(self.q_table) > MAX_STATES:
        # 사용 빈도가 낮은 상태 제거
        sorted_states = sorted(self.q_table.items(), 
                              key=lambda x: max(x[1]))
        for state, _ in sorted_states[:20]:
            del self.q_table[state]
```

#### 학습 속도 향상
```python
# 경험 재생 (Experience Replay)
class ExperienceBuffer:
    def __init__(self, size=1000):
        self.buffer = []
        self.size = size
    
    def add(self, experience):
        if len(self.buffer) >= self.size:
            self.buffer.pop(0)
        self.buffer.append(experience)
    
    def sample(self, batch_size=32):
        return random.sample(self.buffer, 
                           min(batch_size, len(self.buffer)))
```

## 📚 추가 학습 자료

### 강화학습 이론
- [Q-Learning 기초](https://en.wikipedia.org/wiki/Q-learning)
- [Temporal Difference Learning](https://web.stanford.edu/class/psych209/Readings/SuttonBartoIPRLBook2ndEd.pdf)

### 컴퓨터 비전
- [OpenCV 라인 검출](https://docs.opencv.org/4.x/d9/db0/tutorial_hough_lines.html)
- [이미지 전처리 기법](https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_table_of_contents_imgproc/py_table_of_contents_imgproc.html)

### 실습 예제
- [Q-Learning 시각화](https://cs.stanford.edu/people/karpathy/reinforcejs/)
- [라인 트레이싱 알고리즘](https://github.com/topics/line-following-robot)

## 🎯 프로젝트 확장 아이디어

### 1. 고급 상태 표현
- **다중 프레임**: 연속된 프레임으로 움직임 정보 추가
- **라인 곡률**: 라인의 굽은 정도 측정
- **교차점 감지**: T자, 십자 교차점 인식

### 2. 다중 목표 학습
- **속도 최적화**: 빠르면서도 안정적인 주행
- **에너지 효율**: 최소 전력으로 목표 달성
- **부드러운 움직임**: 급격한 방향 전환 최소화

### 3. 환경 적응
- **조명 변화**: 자동 임계값 조정
- **다양한 라인**: 색상, 두께 변화 대응
- **장애물 회피**: 라인 트레이싱 + 장애물 감지

### 4. 고급 알고리즘
- **Deep Q-Network (DQN)**: 신경망 기반 Q-Learning
- **Double DQN**: 과추정 문제 해결
- **Dueling DQN**: 상태 가치와 액션 이점 분리

---

🎉 **Q-Learning으로 똑똑한 라인 트레이싱 로봇을 만들어보세요!** 