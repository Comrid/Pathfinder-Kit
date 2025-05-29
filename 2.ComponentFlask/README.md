# 🧩 패스파인더 컴포넌트 Flask 시스템

패스파인더 로봇의 각 하드웨어 컴포넌트를 개별적으로 제어하고 테스트할 수 있는 Flask 기반 웹 인터페이스 모음입니다.

## 📋 목차
- [시스템 개요](#시스템-개요)
- [폴더 구조](#폴더-구조)
- [공통 설정](#공통-설정)
- [컴포넌트별 사용법](#컴포넌트별-사용법)
- [통합 테스트](#통합-테스트)
- [문제 해결](#문제-해결)

## 🎯 시스템 개요

### 목적
- **모듈화 개발**: 각 하드웨어 컴포넌트를 독립적으로 개발 및 테스트
- **단계별 학습**: 로봇 시스템을 점진적으로 이해
- **디버깅 용이성**: 개별 컴포넌트 문제 격리 및 해결
- **재사용성**: 다른 프로젝트에서 컴포넌트 재활용

### 학습 목표
- Flask 웹 프레임워크 활용
- 하드웨어 제어 기초 학습
- 웹 기반 IoT 인터페이스 구현
- 모듈화 프로그래밍 원리 이해

## 📁 폴더 구조

```
2.ComponentFlask/
├── 1.MotorFlask/          # 모터 제어 시스템
│   ├── app.py             # Flask 애플리케이션
│   ├── templates/         # 웹 인터페이스
│   └── README.md          # 모터 제어 가이드
├── 2.SonicFlask/          # 초음파 센서 시스템
│   ├── app.py             # Flask 애플리케이션
│   ├── templates/         # 웹 인터페이스
│   └── README.md          # 센서 사용 가이드
├── 3.CameraFlask/         # 카메라 시스템
│   ├── app.py             # Flask 애플리케이션
│   ├── templates/         # 웹 인터페이스
│   └── README.md          # 카메라 가이드
└── README.md              # 전체 시스템 가이드 (이 파일)
```

## ⚙️ 공통 설정

### 하드웨어 요구사항
- **Raspberry Pi Zero 2 W**: 메인 컨트롤러
- **L298N 모터 드라이버**: 모터 제어용
- **HC-SR04 초음파 센서**: 거리 측정용
- **Pi Camera 모듈**: 영상 처리용
- **점퍼 와이어**: 연결용

### GPIO 핀 배치 (공통)
```
모터 드라이버 (L298N):
- IN1: GPIO23 (오른쪽 모터 방향 1)
- IN2: GPIO24 (오른쪽 모터 방향 2)
- IN3: GPIO22 (왼쪽 모터 방향 1)
- IN4: GPIO27 (왼쪽 모터 방향 2)
- ENA: GPIO12 (오른쪽 모터 PWM)
- ENB: GPIO13 (왼쪽 모터 PWM)

초음파 센서 (HC-SR04):
- TRIG: GPIO5 (송신)
- ECHO: GPIO6 (수신)

카메라:
- CSI 포트 연결 (15핀 FPC 케이블)
```

### 공통 의존성
```bash
# 모든 컴포넌트에서 공통으로 사용
pip install flask>=2.0.1
pip install flask-socketio>=5.1.1
pip install eventlet>=0.33.0
pip install RPi.GPIO>=0.7.1

# 카메라 컴포넌트 추가 의존성
pip install opencv-python-headless>=4.5.0
pip install picamera2>=0.3.12
pip install numpy>=1.19.5
```

## 🧩 컴포넌트별 사용법

### 1️⃣ MotorFlask - 모터 제어 시스템

#### 기능
- **8방향 이동**: 전진, 후진, 좌회전, 우회전, 대각선 이동
- **속도 제어**: 0-100% PWM 속도 조절
- **실시간 제어**: 웹 인터페이스 및 키보드 제어
- **안전 기능**: 비상 정지, 자동 타임아웃

#### 실행 방법
```bash
cd 2.ComponentFlask/1.MotorFlask
python app.py
```

#### 웹 접속
```
http://라즈베리파이IP:5000
```

#### 주요 기능
- **방향 버튼**: 8방향 이동 제어
- **속도 슬라이더**: 모터 속도 조절 (0-100%)
- **키보드 제어**: WASD 또는 화살표 키
- **상태 모니터링**: 현재 명령 및 속도 표시

### 2️⃣ SonicFlask - 초음파 센서 시스템

#### 기능
- **거리 측정**: HC-SR04 센서로 정밀 거리 측정
- **실시간 차트**: 거리 데이터 시각화
- **통계 분석**: 최소/최대/평균 거리 계산
- **폴링 방식**: 안정적인 HTTP 기반 데이터 수집

#### 실행 방법
```bash
cd 2.ComponentFlask/2.SonicFlask
python app.py
```

#### 주요 기능
- **실시간 측정**: 100ms~10초 간격 조절 가능
- **데이터 차트**: Chart.js 기반 실시간 그래프
- **측정 통계**: 총 측정 횟수, 오류율, 평균값
- **데이터 내보내기**: CSV 형태로 측정 데이터 저장

### 3️⃣ CameraFlask - 카메라 시스템

#### 기능
- **실시간 스트리밍**: 640x480 해상도 영상 스트리밍
- **이미지 캡처**: 정지 이미지 저장
- **설정 조절**: 밝기, 대비, 해상도 조절
- **영상 처리**: 기본적인 필터 및 효과

#### 실행 방법
```bash
cd 2.ComponentFlask/3.CameraFlask
python app.py
```

#### 주요 기능
- **라이브 스트림**: MJPEG 형태 실시간 영상
- **캡처 기능**: 클릭으로 이미지 저장
- **카메라 설정**: 해상도, 프레임레이트 조절
- **영상 효과**: 그레이스케일, 엣지 검출 등

## 🔗 통합 테스트

### 개별 테스트 순서
1. **모터 테스트**: 기본 이동 및 속도 제어 확인
2. **센서 테스트**: 거리 측정 정확도 검증
3. **카메라 테스트**: 영상 스트리밍 및 캡처 확인
4. **통합 테스트**: 모든 컴포넌트 동시 동작 확인

### 테스트 스크립트
```bash
# 각 폴더에서 개별 테스트
cd 1.MotorFlask && python test_motor.py
cd ../2.SonicFlask && python test_sonic.py
cd ../3.CameraFlask && python test_camera.py
```

### 성능 벤치마크
- **모터 응답시간**: < 50ms
- **센서 측정 주기**: 100ms (조절 가능)
- **카메라 프레임레이트**: 15-30 FPS
- **웹 인터페이스 지연**: < 100ms

## 🔧 개발 가이드

### 새 컴포넌트 추가
1. **폴더 생성**: `4.NewComponent/`
2. **Flask 앱 작성**: `app.py`
3. **웹 인터페이스**: `templates/index.html`
4. **README 작성**: 사용법 및 API 문서
5. **테스트 스크립트**: `test_component.py`

### 코딩 규칙
- **GPIO 핀 설정**: 공통 핀 배치 준수
- **포트 번호**: 각 컴포넌트별 고유 포트 사용
- **에러 처리**: GPIO 없는 환경에서 시뮬레이션 모드 지원
- **로깅**: 상세한 디버그 정보 제공

### API 설계 원칙
```python
# 공통 API 패턴
@app.route('/api/status')          # 상태 조회
@app.route('/api/control', methods=['POST'])  # 제어 명령
@app.route('/api/settings')        # 설정 조회
@app.route('/api/test')           # 테스트 기능
```

## 🔍 문제 해결

### 일반적인 문제

#### 1. GPIO 권한 오류
```bash
# 해결책: sudo 권한으로 실행
sudo python app.py
```

#### 2. 포트 충돌
```bash
# 해결책: 다른 포트 사용
python app.py --port 5001
```

#### 3. 모듈 import 오류
```bash
# 해결책: 의존성 재설치
pip install -r requirements.txt
```

#### 4. 카메라 인식 안됨
```bash
# 해결책: 카메라 인터페이스 활성화
sudo raspi-config
# Interface Options > Camera > Enable
```

### 디버깅 팁

#### 로그 레벨 조정
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### GPIO 상태 확인
```bash
# GPIO 핀 상태 확인
gpio readall
```

#### 네트워크 연결 테스트
```bash
# 웹 서버 접근 테스트
curl http://localhost:5000/api/status
```

## 📈 성능 최적화

### 메모리 사용량 최적화
- **이미지 버퍼링**: 적절한 버퍼 크기 설정
- **가비지 컬렉션**: 주기적인 메모리 정리
- **스레드 관리**: 불필요한 스레드 종료

### CPU 사용률 최적화
- **폴링 주기**: 적절한 측정 간격 설정
- **비동기 처리**: 블로킹 작업 최소화
- **캐싱**: 반복 계산 결과 저장

### 네트워크 최적화
- **압축**: 이미지 및 데이터 압축 전송
- **캐싱**: 정적 리소스 브라우저 캐싱
- **연결 풀링**: 데이터베이스 연결 재사용

## 🎓 학습 로드맵

### 초급 (1-2주)
1. **Flask 기초**: 웹 프레임워크 이해
2. **GPIO 제어**: 기본 하드웨어 제어
3. **웹 인터페이스**: HTML/CSS/JavaScript 기초

### 중급 (3-4주)
1. **실시간 통신**: SocketIO 활용
2. **데이터 시각화**: Chart.js 사용
3. **API 설계**: RESTful API 구현

### 고급 (5-8주)
1. **시스템 통합**: 여러 컴포넌트 연동
2. **성능 최적화**: 메모리 및 CPU 최적화
3. **확장 기능**: 새로운 센서 및 액추에이터 추가

## 📚 참고 자료

### 관련 문서
- [0.Guide/](../0.Guide/): 하드웨어 설정 가이드
- [3.IntegratedFlask/](../3.IntegratedFlask/): 통합 시스템
- [4.ObstacleAvoidance/](../4.ObstacleAvoidance/): 장애물 회피 시스템

### 외부 자료
- [Flask 공식 문서](https://flask.palletsprojects.com/)
- [Raspberry Pi GPIO 가이드](https://www.raspberrypi.org/documentation/usage/gpio/)
- [SocketIO 문서](https://socket.io/docs/)
- [Chart.js 가이드](https://www.chartjs.org/docs/)

### 추천 학습 순서
1. **1.MotorFlask**: 기본 하드웨어 제어 학습
2. **2.SonicFlask**: 센서 데이터 처리 및 시각화
3. **3.CameraFlask**: 영상 처리 및 스트리밍
4. **통합 프로젝트**: 모든 컴포넌트 결합

---

**🎯 학습 목표 달성도 체크리스트**
- [ ] Flask 웹 프레임워크 이해
- [ ] GPIO 하드웨어 제어 구현
- [ ] 실시간 웹 인터페이스 개발
- [ ] 모듈화 프로그래밍 적용
- [ ] 개별 컴포넌트 테스트 완료
- [ ] 통합 시스템으로 발전 준비

**다음 단계**: [3.IntegratedFlask](../3.IntegratedFlask/) - 모든 컴포넌트를 하나로 통합! 