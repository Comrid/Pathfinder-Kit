# 🤖 패스파인더 AI 파이썬 자율주행 키트
## 차세대 AI 교육을 위한 혁신적인 로보틱스 플랫폼

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.0+-red.svg)](https://opencv.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Security](https://img.shields.io/badge/Security-Enhanced-brightgreen.svg)](SECURITY_IMPROVEMENTS.md)

> **"Learn by Building, Build by Learning"**  
> 만들면서 배우고, 배우면서 만드는 혁신적인 학습 경험

---

## 🎯 프로젝트 비전

**패스파인더 AI 파이썬 자율주행 키트**는 단순한 로봇 조립 키트를 넘어선, **차세대 AI 교육을 위한 종합적인 학습 플랫폼**입니다. 하드웨어 조립부터 고급 AI 알고리즘까지 체계적으로 학습할 수 있는 완전한 교육 생태계를 구축했습니다.

### 🌟 핵심 혁신 포인트

- **🎓 점진적 학습 설계**: 7단계 커리큘럼으로 초보자도 AI 전문가로 성장
- **🏗️ 실무 중심 아키텍처**: 산업 표준 패턴과 구조 적용
- **🌐 하이브리드 환경**: 하드웨어 + 시뮬레이션 모드로 접근성 극대화
- **🔒 보안 강화**: 엔터프라이즈급 보안 표준 적용
- **⚡ 실시간 제어**: WebSocket 기반 즉시 반응 시스템

---

## 🚀 7단계 혁신 커리큘럼

### 📊 학습 로드맵

```
🔧 1단계: ComponentTest     →  🌐 2단계: ComponentFlask
    (하드웨어 기초)              (웹 기반 IoT 제어)
           ↓                            ↓
⚙️ 3단계: IntegratedFlask   →  🚧 4단계: ObstacleAvoidance
    (통합 시스템)                (자율 행동 구현)
           ↓                            ↓
👁️ 5단계: LineTracing_PID   →  🧠 6단계: Q-Learning AI
    (컴퓨터 비전 + 제어)          (강화학습 AI)
           ↓                            ↓
💻 7단계: WebCodeExecuter   →  🎯 최종: 자율주행 완성
    (실시간 개발 환경)            (AI 로보틱스 마스터)
```

### 🔧 **1단계: ComponentTest** - 하드웨어 기초 마스터
```python
# 🎯 학습 목표: GPIO 제어 및 센서 기초
📁 1.ComponentTest/
├── motor_test.py      # L298N 모터 드라이버 제어
├── sonic_test.py      # HC-SR04 초음파 센서 거리 측정
└── camera_test.py     # 카메라 모듈 기본 동작
```
**핵심 기술**: GPIO 제어, PWM, 센서 인터페이싱

### 🌐 **2단계: ComponentFlask** - 웹 기반 IoT 제어
```python
# 🎯 학습 목표: Flask 웹 프레임워크 및 IoT 제어
📁 2.ComponentFlask/
├── 1.MotorFlask/      # 웹 기반 모터 제어
├── 2.SonicFlask/      # 실시간 센서 모니터링
└── 3.CameraFlask/     # 라이브 카메라 스트리밍
```
**핵심 기술**: Flask, HTML/CSS/JavaScript, 실시간 통신

### ⚙️ **3단계: IntegratedFlask** - 통합 시스템 아키텍처
```python
# 🎯 학습 목표: 시스템 통합 및 멀티스레딩
📁 3.IntegratedFlask/
├── IntegratedFlask.py # 모든 컴포넌트 통합 제어
├── templates/         # 반응형 웹 인터페이스
└── test_integrated.py # 통합 테스트 시스템
```
**핵심 기술**: SocketIO, 멀티스레딩, 시스템 아키텍처

### 🚧 **4단계: ObstacleAvoidance** - 자율 행동 구현
```python
# 🎯 학습 목표: 센서 기반 의사결정 및 자율 행동
📁 4.ObstacleAvoidance/
├── app.py                    # 장애물 회피 알고리즘
└── test_obstacle_avoidance.py # 자율 행동 테스트
```
**핵심 기술**: 센서 융합, 상태 머신, 자율 알고리즘

### 👁️ **5단계: LineTracing_PID** - 컴퓨터 비전 + 제어 이론
```python
# 🎯 학습 목표: OpenCV 영상 처리 및 PID 제어
📁 5.LineTracing_PID/
├── LineTracker.py     # PID 제어 라인 트레이싱
├── Motor.py          # 고급 모터 제어 클래스
└── config.py         # 설정 관리 시스템
```
**핵심 기술**: OpenCV, PID 제어, 실시간 영상 처리

### 🧠 **6단계: Q-Learning** - 강화학습 AI (예정)
```python
# 🎯 학습 목표: 강화학습 및 AI 의사결정
📁 6.QLearning/
├── q_learning_drive.py    # Q-Learning 자율주행
├── q_table.npy           # 학습된 지식 저장
└── training_env.py       # 학습 환경 구축
```
**핵심 기술**: 강화학습, 상태-행동 매핑, AI 의사결정

### 💻 **7단계: WebCodeExecuter** - 실시간 개발 환경
```python
# 🎯 학습 목표: 보안 강화 및 실시간 코드 실행
📁 7.WebCodeExecuter/
├── WebCodeExcuter_Secure.py  # 보안 강화 코드 실행기
└── README.md                 # 상세 사용 가이드
```
**핵심 기술**: 보안 프로그래밍, 프로세스 관리, 웹 IDE

---

## 🔧 하드웨어 구성

### 🎛️ 메인 컨트롤러
- **Raspberry Pi Zero 2 W** × 1개 (ARM Cortex-A53 쿼드코어)

### 📡 센서 & 비전 시스템
- **160도 광각 카메라 모듈** × 1개 (고급 컴퓨터 비전)
- **HC-SR04 초음파 센서** × 1개 (정밀 거리 측정)
- **22-to-15 FPC 카메라 케이블** × 1개

### ⚙️ 구동 시스템
- **L298N 모터 드라이버** × 1개 (안정적인 모터 제어)
- **기어 DC 모터** × 2개 (고토크 구동)
- **바퀴** × 2개 + **볼 캐스터** × 1개

### 🔋 전원 & 연결
- **5V 전압 강하 모듈** × 1개 (안전한 전원 관리)
- **점퍼선** 세트 (유연한 연결)

### 🏗️ 구조 프레임
- **2층 구조 프레임** (확장 가능한 모듈형 설계)

---

## 💡 기술적 혁신 특징

### 🏗️ **모듈화된 아키텍처**
```python
🔧 컴포넌트 기반 설계
├── 모터 컨트롤러 클래스 (PathfinderMotorController)
├── 센서 시스템 모듈 (실시간 데이터 처리)
├── 카메라 비전 엔진 (OpenCV 기반)
└── AI 학습 시스템 (Q-Learning, 딥러닝 준비)

⚙️ 설정 관리 시스템
├── JSON 기반 동적 설정
├── 프로파일별 최적화 (기본/고성능/안전/디버그)
└── 실시간 설정 변경 지원

🌐 웹 기반 제어 인터페이스
├── Flask + SocketIO 실시간 통신
├── 반응형 모바일 지원
└── 데이터 시각화 및 모니터링
```

### 🔒 **엔터프라이즈급 보안**
```python
🛡️ 보안 강화 시스템
├── subprocess shell=False 강제 적용
├── 입력 검증 및 새니타이제이션
├── 화이트리스트 기반 명령어 제한
├── 실행 시간 및 리소스 제한
└── 종합 보안 모니터링 시스템
```

### ⚡ **하이브리드 실행 환경**
- **하드웨어 모드**: 실제 Raspberry Pi와 센서 활용
- **시뮬레이션 모드**: GPIO 없는 환경에서도 완전 학습 가능
- **웹 인터페이스**: 어디서나 접근 가능한 원격 제어

---

## 🎓 교육적 가치

### 📚 **실전 프로그래밍 스킬**
- **객체지향 프로그래밍**: 클래스 기반 모듈 설계
- **비동기 프로그래밍**: 멀티스레딩과 실시간 통신
- **웹 개발**: Flask, SocketIO, HTML/CSS/JavaScript
- **AI/ML**: OpenCV, 강화학습, 컴퓨터 비전
- **보안 프로그래밍**: 안전한 코드 작성 및 시스템 보안

### 🏭 **산업 표준 도구**
- **버전 관리**: Git을 통한 협업 및 코드 관리
- **문서화**: 체계적인 README와 API 문서
- **테스팅**: 단위 테스트와 통합 테스트
- **배포**: 실제 하드웨어 환경 배포 경험
- **모니터링**: 실시간 시스템 모니터링

### 🎯 **학습 목표별 성취**

#### 🥉 **초급 단계** (1-3주)
- [ ] 하드웨어 조립 및 기본 프로그래밍
- [ ] GPIO 제어 및 센서 활용
- [ ] 웹 인터페이스 개발 기초

#### 🥈 **중급 단계** (4-6주)
- [ ] 컴퓨터 비전 및 이미지 처리
- [ ] 실시간 데이터 처리 및 통신
- [ ] 시스템 통합 및 아키텍처 설계

#### 🥇 **고급 단계** (7-8주)
- [ ] 강화학습 구현 및 AI 의사결정
- [ ] 자율주행 알고리즘 개발
- [ ] 보안 프로그래밍 및 시스템 최적화

---

## 🚀 빠른 시작 가이드

### 📋 **시스템 요구사항**
- **하드웨어**: Raspberry Pi Zero 2 W, 16GB+ microSD
- **OS**: Raspberry Pi OS Lite (32-bit) 또는 Desktop
- **Python**: 3.7 이상
- **네트워크**: Wi-Fi (2.4GHz 802.11 b/g/n)

### ⚡ **1분 설치**
```bash
# 1. 저장소 클론
git clone https://github.com/your-repo/pathfinder-kit.git
cd pathfinder-kit

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경 설정
cp .env.example .env
nano .env  # 필요시 설정 수정

# 4. 첫 번째 테스트 실행
cd 1.ComponentTest
python motor_test.py
```

### 🌐 **웹 인터페이스 접속**
```bash
# 통합 시스템 실행
cd 3.IntegratedFlask
python IntegratedFlask.py

# 브라우저에서 접속
# http://라즈베리파이IP:5000
```

---

## 📦 의존성 패키지

### 🔧 **핵심 라이브러리**
```txt
RPi.GPIO>=0.7.0          # GPIO 제어
numpy>=1.19.5            # 수치 연산
opencv-python-headless   # 컴퓨터 비전
picamera2>=0.3.12        # 카메라 제어
```

### 🌐 **웹 프레임워크**
```txt
flask>=2.0.1             # 웹 프레임워크
flask-socketio>=5.1.1    # 실시간 통신
eventlet>=0.33.0         # 비동기 처리
```

### 🔒 **보안 & 유틸리티**
```txt
python-dotenv>=0.19.0    # 환경 변수 관리
cryptography>=3.4.8     # 암호화 및 보안
pytest>=6.2.5           # 테스트 프레임워크
```

---

## 🎯 활용 분야

### 🏫 **교육 기관**
- **대학교**: 로보틱스/AI 교육 과정
- **코딩 부트캠프**: 실습 프로젝트
- **STEM 교육**: 창의적 문제 해결

### 👨‍💻 **개발자 교육**
- **신입 개발자**: 온보딩 프로그램
- **팀 빌딩**: 협업 프로젝트
- **스킬 업그레이드**: 최신 기술 학습

### 🏢 **기업 활용**
- **프로토타이핑**: 빠른 아이디어 검증
- **교육 프로그램**: 직원 역량 강화
- **R&D**: 로보틱스 연구 개발

---

## 🌟 확장 프로젝트 아이디어

### 🔰 **초급 확장**
- **음성 제어**: 음성 인식으로 로봇 명령
- **LED 매트릭스**: 감정 표현 디스플레이
- **블루투스 조종**: 스마트폰 앱 연동
- **IoT 센서**: 온도, 습도, 조도 센서 추가

### 🔥 **중급 확장**
- **SLAM**: 동시 위치 추정 및 지도 작성
- **객체 인식**: YOLO를 이용한 실시간 객체 탐지
- **군집 로봇**: 여러 로봇 협업 시스템
- **클라우드 연동**: AWS/Azure IoT 통합

### 🚀 **고급 확장**
- **딥러닝**: CNN을 이용한 고급 영상 처리
- **ROS 연동**: Robot Operating System 활용
- **시뮬레이션**: Gazebo 가상 환경 연동
- **상용화**: 제품 수준의 UI/UX 개발

---

## 🏆 성취 배지 시스템

### 🥉 **브론즈 배지**
- [ ] **🔧 첫 걸음**: 하드웨어 조립 완료
- [ ] **🤖 Hello Robot**: 첫 번째 모터 제어 성공
- [ ] **📡 센서 마스터**: 모든 센서 데이터 읽기 성공
- [ ] **🌐 웹 개발자**: 웹 인터페이스 실행 성공

### 🥈 **실버 배지**
- [ ] **⚙️ 통합자**: 모든 컴포넌트 통합 성공
- [ ] **🚧 장애물 회피**: 자율 장애물 회피 구현
- [ ] **👁️ 라인 트레이서**: PID 라인 트레이싱 성공
- [ ] **🔍 문제 해결사**: 독립적으로 버그 수정

### 🥇 **골드 배지**
- [ ] **🧠 AI 엔지니어**: Q-Learning 자율주행 완성
- [ ] **🎨 창작자**: 독창적인 확장 기능 개발
- [ ] **👨‍🏫 멘토**: 다른 학습자 도움 제공
- [ ] **🏆 마스터**: 모든 커리큘럼 완주

---

## 🔒 보안 및 안전성

### 🛡️ **보안 강화 기능**
- **입력 검증**: 모든 사용자 입력 엄격 검증
- **명령어 제한**: 화이트리스트 기반 안전한 명령 실행
- **프로세스 격리**: 안전한 코드 실행 환경
- **실시간 모니터링**: 보안 이벤트 실시간 감지

### 📋 **보안 체크리스트**
- [x] `subprocess shell=False` 적용
- [x] 입력 새니타이제이션 구현
- [x] 실행 시간 제한 설정
- [x] 리소스 사용량 제한
- [x] 보안 로깅 시스템

자세한 보안 가이드: [SECURITY_IMPROVEMENTS.md](SECURITY_IMPROVEMENTS.md)

---

## 🤝 기여하기

### 💡 **기여 방법**
1. **Fork** 저장소
2. **Feature 브랜치** 생성 (`git checkout -b feature/amazing-feature`)
3. **변경사항 커밋** (`git commit -m 'Add amazing feature'`)
4. **브랜치 푸시** (`git push origin feature/amazing-feature`)
5. **Pull Request** 생성

### 📝 **기여 가이드라인**
- 코드 스타일: PEP 8 준수
- 테스트: 새 기능에 대한 테스트 코드 포함
- 문서화: 변경사항에 대한 문서 업데이트
- 보안: 보안 가이드라인 준수

---

## 📄 라이선스

이 프로젝트는 **MIT 라이선스** 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

## 🙏 감사의 말

### 🔧 **오픈소스 커뮤니티**
- **Flask**: 강력한 웹 프레임워크
- **OpenCV**: 컴퓨터 비전 라이브러리
- **Raspberry Pi Foundation**: 혁신적인 하드웨어 플랫폼
- **Python Community**: 풍부한 생태계

### 👥 **기여자들**
모든 기여자분들께 진심으로 감사드립니다!

---

## 📞 지원 및 문의

### 💬 **커뮤니티**
- **GitHub Issues**: 버그 리포트 및 기능 요청
- **Discussions**: 질문 및 아이디어 공유
- **Wiki**: 상세 문서 및 튜토리얼

### 📧 **연락처**
- **이메일**: pathfinder-support@example.com
- **웹사이트**: https://pathfinder-kit.github.io

---

<div align="center">

## 🚀 **패스파인더와 함께 AI 로보틱스의 미래를 만들어보세요!**

[![GitHub stars](https://img.shields.io/github/stars/pathfinder-kit/pathfinder-kit.svg?style=social&label=Star)](https://github.com/pathfinder-kit/pathfinder-kit)
[![GitHub forks](https://img.shields.io/github/forks/pathfinder-kit/pathfinder-kit.svg?style=social&label=Fork)](https://github.com/pathfinder-kit/pathfinder-kit/fork)
[![GitHub watchers](https://img.shields.io/github/watchers/pathfinder-kit/pathfinder-kit.svg?style=social&label=Watch)](https://github.com/pathfinder-kit/pathfinder-kit)

**"혁신은 학습에서 시작되고, 학습은 실습에서 완성됩니다"**

</div>
