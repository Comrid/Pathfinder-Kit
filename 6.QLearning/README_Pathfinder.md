# 🤖 패스파인더 Q-Learning 자율주행

패스파인더 키트를 위한 강화학습 기반 자율주행 시스템입니다. Q-Learning 알고리즘을 사용하여 초음파 센서로 장애물을 회피하는 방법을 학습합니다.

## 📋 목차
- [Q-Learning이란?](#q-learning이란)
- [시스템 구성](#시스템-구성)
- [사용법](#사용법)
- [웹 인터페이스](#웹-인터페이스)
- [파라미터 설정](#파라미터-설정)
- [문제 해결](#문제-해결)

## 🧠 Q-Learning이란?

### 강화학습의 기본 개념
- **에이전트(Agent)**: 학습하는 주체 (패스파인더 로봇)
- **환경(Environment)**: 로봇이 움직이는 공간
- **상태(State)**: 현재 상황 (초음파 센서 거리)
- **액션(Action)**: 취할 수 있는 행동 (직진, 좌회전, 우회전 등)
- **보상(Reward)**: 행동에 대한 피드백 (좋음/나쁨)

### Q-Learning 공식
```
Q(s,a) = Q(s,a) + α[r + γ*max(Q(s',a')) - Q(s,a)]
```
- **Q(s,a)**: 상태 s에서 액션 a의 가치
- **α**: 학습률 (0.1)
- **γ**: 할인 인수 (0.95)
- **r**: 즉시 보상
- **s'**: 다음 상태

## 🔧 시스템 구성

### 하드웨어 요구사항
- Raspberry Pi Zero 2 W
- 초음파 센서 HC-SR04
- 모터 드라이버 L298N
- DC 기어 모터 2개

### 소프트웨어 구성
```
6.QLearning/
├── pathfinder_qlearning.py    # 메인 Q-Learning 구현
├── qlearning_web.py           # 웹 인터페이스
├── models/                    # 저장된 모델들
└── README_Pathfinder.md       # 이 파일
```

## 🚀 사용법

### 1. 터미널 모드 (기본)

```bash
cd 6.QLearning
python pathfinder_qlearning.py
```

**메뉴 옵션:**
1. **새로운 훈련 시작**: 처음부터 학습 시작
2. **기존 모델 로드 후 훈련 계속**: 저장된 모델에서 이어서 학습
3. **훈련된 모델로 실행**: 학습 완료된 모델로 자율주행
4. **종료**: 프로그램 종료

### 2. 웹 인터페이스 모드 (추천)

```bash
cd 6.QLearning
python qlearning_web.py
```

브라우저에서 `http://라즈베리파이IP:5000` 접속

## 🌐 웹 인터페이스

### 주요 기능

#### 🎮 훈련 제어 패널
- **훈련 시작/중단**: 실시간 훈련 제어
- **에피소드 수 설정**: 학습할 에피소드 개수
- **최대 스텝 설정**: 에피소드당 최대 행동 수

#### 📊 실시간 모니터링
- **현재 에피소드/스텝**: 학습 진행 상황
- **현재 보상**: 실시간 보상 값
- **거리**: 초음파 센서 측정값
- **탐험률**: 현재 ε(epsilon) 값
- **Q-Table 크기**: 학습된 상태 수

#### ⚙️ 파라미터 조정
- **학습률 (α)**: 얼마나 빨리 학습할지
- **할인 인수 (γ)**: 미래 보상의 중요도
- **탐험률 감소**: ε 값 감소 속도
- **안전 거리**: 장애물 회피 기준 거리

#### 📈 학습 진행 차트
- **에피소드별 보상**: 실시간 학습 성과
- **평균 보상**: 최근 10 에피소드 평균
- **학습 곡선**: 시간에 따른 성능 향상

#### 💾 모델 관리
- **모델 저장/로드**: 학습 결과 저장 및 불러오기
- **모델 목록**: 저장된 모델 파일 관리
- **자동 저장**: 50 에피소드마다 자동 저장

## ⚙️ 파라미터 설정

### Q-Learning 파라미터

#### 학습률 (Learning Rate, α)
```python
learning_rate = 0.1  # 기본값
```
- **높음 (0.5-1.0)**: 빠른 학습, 불안정할 수 있음
- **중간 (0.1-0.3)**: 균형잡힌 학습 (권장)
- **낮음 (0.01-0.1)**: 안정적이지만 느린 학습

#### 할인 인수 (Discount Factor, γ)
```python
discount_factor = 0.95  # 기본값
```
- **높음 (0.9-0.99)**: 장기적 보상 중시
- **낮음 (0.1-0.5)**: 즉시 보상 중시

#### 탐험률 (Exploration Rate, ε)
```python
exploration_rate = 1.0      # 초기값 (100% 탐험)
exploration_min = 0.01      # 최소값 (1% 탐험)
exploration_decay = 0.995   # 감소율
```

### 환경 설정

#### 거리 기준
```python
safe_distance = 20      # 안전 거리 (cm)
warning_distance = 30   # 경고 거리 (cm)
good_distance = 50      # 좋은 거리 (cm)
```

#### 보상 시스템
```python
rewards = {
    'collision': -100,    # 충돌 위험 (10cm 미만)
    'danger': -10,        # 위험 (20cm 미만)
    'warning': -2,        # 경고 (30cm 미만)
    'normal': 1,          # 정상 (30-50cm)
    'good': 5,            # 좋음 (50cm 이상)
}
```

### 액션 정의
```python
actions = [
    (40, 40),    # 0: 직진
    (25, 40),    # 1: 약간 좌회전
    (40, 25),    # 2: 약간 우회전
    (0, 60),     # 3: 강한 좌회전
    (60, 0),     # 4: 강한 우회전
    (-30, 30),   # 5: 제자리 우회전
    (30, -30),   # 6: 제자리 좌회전
    (0, 0),      # 7: 정지
]
```

## 📊 학습 과정 이해

### 학습 단계

#### 1단계: 탐험 (Exploration)
- **특징**: 랜덤한 행동, 높은 ε 값
- **목적**: 환경 탐색, 다양한 경험 수집
- **기간**: 초기 100-200 에피소드

#### 2단계: 학습 (Learning)
- **특징**: 점진적 ε 감소, Q-table 구축
- **목적**: 상태-액션 가치 학습
- **기간**: 200-500 에피소드

#### 3단계: 활용 (Exploitation)
- **특징**: 낮은 ε 값, 학습된 정책 사용
- **목적**: 최적 행동 수행
- **기간**: 500+ 에피소드

### 성능 지표

#### 에피소드 보상
- **초기**: -50 ~ -20 (많은 충돌)
- **중기**: -10 ~ 10 (점진적 개선)
- **후기**: 10 ~ 50 (안정적 회피)

#### Q-Table 크기
- **초기**: 1-5 상태
- **중기**: 5-15 상태
- **후기**: 10-20 상태 (수렴)

## 🔧 고급 설정

### 상태 공간 확장
```python
# 현재: 거리만 사용
state = f"d{distance_bin}"

# 확장 예시: 속도 추가
state = f"d{distance_bin}_v{velocity_bin}"

# 확장 예시: 방향 추가
state = f"d{distance_bin}_dir{direction_bin}"
```

### 보상 함수 커스터마이징
```python
def custom_reward(self, distance, action_idx):
    """사용자 정의 보상 함수"""
    base_reward = self.get_reward(distance, action_idx)
    
    # 직진 보너스
    if action_idx == 0 and distance > 30:
        base_reward += 2
    
    # 급회전 페널티
    if action_idx in [3, 4, 5, 6]:
        base_reward -= 1
    
    return base_reward
```

### 다중 센서 지원
```python
def get_multi_sensor_state(self):
    """다중 센서 상태"""
    front_distance = self.ultrasonic_front.get_distance()
    left_distance = self.ultrasonic_left.get_distance()
    right_distance = self.ultrasonic_right.get_distance()
    
    front_bin = self.discretize_distance(front_distance)
    left_bin = self.discretize_distance(left_distance)
    right_bin = self.discretize_distance(right_distance)
    
    return f"f{front_bin}_l{left_bin}_r{right_bin}"
```

## 🐛 문제 해결

### 학습이 안 될 때

#### 증상: 보상이 계속 음수
**원인**: 학습률이 너무 낮거나 탐험이 부족
**해결책**:
```python
learning_rate = 0.2        # 증가
exploration_decay = 0.99   # 느린 감소
```

#### 증상: 같은 행동만 반복
**원인**: 탐험률이 너무 빨리 감소
**해결책**:
```python
exploration_min = 0.1      # 최소값 증가
exploration_decay = 0.999  # 더 느린 감소
```

### 하드웨어 문제

#### 센서 읽기 오류
```python
# 센서 안정화
def get_stable_distance(self, samples=3):
    distances = []
    for _ in range(samples):
        distances.append(self.ultrasonic.get_distance())
        time.sleep(0.01)
    return np.median(distances)
```

#### 모터 제어 불안정
```python
# 부드러운 속도 변화
def smooth_speed_change(self, target_left, target_right):
    current_left = self.current_left_speed
    current_right = self.current_right_speed
    
    # 점진적 속도 변화
    for step in range(5):
        left = current_left + (target_left - current_left) * (step + 1) / 5
        right = current_right + (target_right - current_right) * (step + 1) / 5
        self.motor.set_individual_speeds(int(right), int(left))
        time.sleep(0.02)
```

### 성능 최적화

#### 메모리 사용량 줄이기
```python
# Q-table 크기 제한
if len(self.q_table) > 1000:
    # 오래된 상태 제거
    old_states = list(self.q_table.keys())[:100]
    for state in old_states:
        del self.q_table[state]
```

#### 학습 속도 향상
```python
# 배치 업데이트
def batch_update(self, experiences):
    for state, action, reward, next_state in experiences:
        self.update_q_value(state, action, reward, next_state)
```

## 📚 추가 학습 자료

### 강화학습 이론
- [Sutton & Barto - Reinforcement Learning: An Introduction](http://incompleteideas.net/book/the-book.html)
- [OpenAI Spinning Up](https://spinningup.openai.com/)

### 실습 예제
- [Q-Learning 시각화](https://cs.stanford.edu/people/karpathy/reinforcejs/)
- [GridWorld 예제](https://github.com/dennybritz/reinforcement-learning)

### 고급 알고리즘
- **Deep Q-Network (DQN)**: 신경망 기반 Q-Learning
- **Policy Gradient**: 정책 기반 학습
- **Actor-Critic**: 가치 + 정책 결합

## 🎯 프로젝트 확장 아이디어

### 1. 다중 목표 학습
- 장애물 회피 + 목표 지점 도달
- 에너지 효율성 최적화
- 시간 최소화 경로 탐색

### 2. 환경 복잡도 증가
- 동적 장애물 (움직이는 물체)
- 다양한 지형 (카펫, 타일 등)
- 조명 변화 대응

### 3. 센서 융합
- 카메라 + 초음파 센서
- IMU 센서 추가
- 라이다 센서 연동

### 4. 협력 학습
- 다중 로봇 협력
- 통신 기반 정보 공유
- 집단 지능 구현

---

🎉 **Q-Learning으로 똑똑한 자율주행 로봇을 만들어보세요!** 