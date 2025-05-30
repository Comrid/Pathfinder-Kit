# 🚀 패스파인더 통합 Flask 시스템

모터, 초음파 센서, 카메라를 하나의 웹 인터페이스로 통합한 종합 제어 시스템입니다. 패스파인더 로봇의 모든 기능을 한 곳에서 제어하고 모니터링할 수 있습니다.

## 📋 목차
- [시스템 개요](#시스템-개요)
- [주요 기능](#주요-기능)
- [설치 및 실행](#설치-및-실행)
- [웹 인터페이스 사용법](#웹-인터페이스-사용법)
- [API 문서](#api-문서)
- [설정 및 커스터마이징](#설정-및-커스터마이징)
- [문제 해결](#문제-해결)

## 🎯 시스템 개요

### 목적
- **통합 제어**: 모든 하드웨어 컴포넌트를 하나의 인터페이스로 제어
- **실시간 모니터링**: 로봇의 모든 상태를 실시간으로 확인
- **사용자 친화적**: 직관적이고 반응형 웹 인터페이스
- **확장 가능성**: 새로운 센서나 액추에이터 쉽게 추가

### 학습 목표
- 시스템 통합 및 아키텍처 설계
- 실시간 웹 애플리케이션 개발
- 멀티스레딩 및 비동기 프로그래밍
- 하드웨어-소프트웨어 통합 시스템 구현

### 기술 스택
- **백엔드**: Flask, Flask-SocketIO, Python
- **프론트엔드**: HTML5, CSS3, JavaScript, Chart.js
- **하드웨어**: Raspberry Pi, GPIO, 카메라, 센서
- **통신**: WebSocket, HTTP REST API

## 🔧 주요 기능

### 1. 모터 제어 시스템
- **8방향 이동**: 전진, 후진, 좌우 회전, 대각선 이동
- **실시간 제어**: SocketIO 기반 즉시 응답
- **속도 조절**: 0-100% PWM 속도 제어
- **키보드 제어**: WASD/화살표 키 지원

### 2. 초음파 센서 모니터링
- **실시간 거리 측정**: HTTP 폴링 방식으로 안정적 데이터 수집
- **통계 분석**: 최소/최대/평균 거리 계산
- **시각화**: 실시간 차트로 거리 변화 표시
- **데이터 로깅**: 측정 데이터 저장 및 분석

### 3. 카메라 스트리밍
- **실시간 영상**: 640x480 해상도 MJPEG 스트리밍
- **자동 감지**: 카메라 연결 상태 자동 확인
- **오류 처리**: 카메라 없을 시 더미 이미지 표시
- **성능 최적화**: 효율적인 프레임 처리

### 4. 시스템 상태 모니터링
- **하드웨어 상태**: GPIO, 카메라, 모터 상태 실시간 확인
- **연결 상태**: 웹소켓 연결 상태 표시
- **시뮬레이션 모드**: GPIO 없는 환경에서도 테스트 가능
- **로그 시스템**: 상세한 디버그 정보 제공

## 🚀 설치 및 실행

### 1. 의존성 설치
```bash
cd 3.IntegratedFlask
pip install -r requirements.txt
```

### 2. 하드웨어 연결 확인
```bash
# GPIO 핀 상태 확인
gpio readall

# 카메라 연결 확인
vcgencmd get_camera
```

### 3. 시스템 실행
```bash
python IntegratedFlask.py
```

### 4. 웹 접속
```
브라우저에서 http://라즈베리파이IP:5000 접속
```

### 5. 테스트 실행
```bash
# 시스템 테스트
python test_integrated.py
```

## 📱 웹 인터페이스 사용법

### 메인 화면 구성

#### 왼쪽 패널: 카메라 & 모터 제어
- **실시간 카메라**: 로봇의 시야 확인
- **방향 제어 버튼**: 8방향 이동 제어
- **속도 슬라이더**: 모터 속도 조절 (0-100%)
- **비상 정지**: 즉시 모든 동작 중단

#### 오른쪽 패널: 센서 & 상태
- **거리 측정**: 초음파 센서 실시간 데이터
- **거리 차트**: 시간별 거리 변화 그래프
- **시스템 상태**: 하드웨어 및 연결 상태
- **실시간 로그**: 시스템 동작 로그

### 제어 방법

#### 1. 마우스/터치 제어
- **방향 버튼**: 클릭으로 이동 방향 선택
- **속도 조절**: 슬라이더로 속도 설정
- **비상 정지**: 빨간 버튼으로 즉시 정지

#### 2. 키보드 제어
```
이동 제어:
- W/↑: 전진
- S/↓: 후진  
- A/←: 좌회전
- D/→: 우회전
- Q: 전진+좌회전
- E: 전진+우회전
- Z: 후진+좌회전
- C: 후진+우회전

기타:
- Space: 정지
- Esc: 비상 정지
```

#### 3. 모바일 지원
- **반응형 디자인**: 스마트폰/태블릿 최적화
- **터치 제어**: 터치 친화적 버튼 크기
- **세로/가로 모드**: 화면 회전 지원

### 실시간 모니터링

#### 거리 센서 데이터
- **현재 거리**: 실시간 거리 표시 (cm)
- **측정 통계**: 최소/최대/평균 거리
- **측정 횟수**: 총 측정 횟수 및 오류율
- **차트**: 최근 50개 데이터 포인트 시각화

#### 시스템 상태
- **GPIO 상태**: 하드웨어 모드/시뮬레이션 모드
- **카메라 상태**: 연결됨/연결 안됨
- **모터 상태**: 현재 명령 및 속도
- **네트워크**: WebSocket 연결 상태

## 📡 API 문서

### HTTP REST API

#### 거리 측정 API
```http
GET /api/distance
```
**응답 예시:**
```json
{
  "success": true,
  "distance": 25.3,
  "timestamp": "14:30:25",
  "count": 1234,
  "stats": {
    "min_distance": 5.2,
    "max_distance": 150.8,
    "avg_distance": 32.1,
    "total_measurements": 1234,
    "error_count": 5
  }
}
```

#### 시스템 상태 API
```http
GET /api/system/status
```
**응답 예시:**
```json
{
  "success": true,
  "gpio_available": true,
  "camera_available": true,
  "motor_running": true,
  "current_command": "forward",
  "motor_speed": 80,
  "timestamp": "14:30:25"
}
```

#### 데이터 초기화 API
```http
GET /api/ultrasonic/clear
```

### WebSocket 이벤트

#### 클라이언트 → 서버

##### 모터 제어
```javascript
socket.emit('motor_command', {
  command: 'forward'  // forward, backward, left, right, stop 등
});
```

##### 속도 변경
```javascript
socket.emit('speed_change', {
  speed: 80  // 0-100
});
```

##### 비상 정지
```javascript
socket.emit('emergency_stop');
```

#### 서버 → 클라이언트

##### 연결 상태
```javascript
socket.on('connection_status', function(data) {
  // data.status: 'connected'
});
```

##### 시스템 상태
```javascript
socket.on('system_status', function(data) {
  // data.gpio_available, data.camera_available 등
});
```

##### 모터 상태
```javascript
socket.on('motor_status', function(data) {
  // data.command, data.speed, data.timestamp
});
```

## ⚙️ 설정 및 커스터마이징

### GPIO 핀 설정 변경
```python
# IntegratedFlask.py 파일에서 수정
IN1 = 23  # 오른쪽 모터 방향 1
IN2 = 24  # 오른쪽 모터 방향 2
IN3 = 22  # 왼쪽 모터 방향 1
IN4 = 27  # 왼쪽 모터 방향 2
ENA = 12  # 오른쪽 모터 PWM
ENB = 13  # 왼쪽 모터 PWM
TRIG = 5  # 초음파 송신
ECHO = 6  # 초음파 수신
```

### 모터 속도 설정
```python
MOTOR_SPEED_NORMAL = 100    # 기본 속도
MOTOR_SPEED_TURN = 80       # 회전 속도
MOTOR_SPEED_DIAGONAL = 60   # 대각선 이동 속도
```

### 카메라 설정
```python
# 카메라 해상도 변경
picam2.preview_configuration.main.size = (640, 480)
# 다른 해상도: (320, 240), (800, 600), (1024, 768)
```

### 웹 인터페이스 커스터마이징

#### CSS 스타일 변경
```css
/* templates/index.html 내 <style> 섹션에서 수정 */
.control-panel {
  background: #your-color;
}
```

#### 차트 설정 변경
```javascript
// 차트 업데이트 주기 변경
const updateInterval = 1000; // 1초 (기본값)

// 차트 데이터 포인트 수 변경
const maxDataPoints = 100; // 기본값: 50
```

## 🔍 문제 해결

### 일반적인 문제

#### 1. 카메라만 나오고 모터/센서가 작동하지 않는 경우
**원인**: GPIO 초기화 순서 문제
**해결책**:
```bash
# 1. 프로그램 완전 종료
sudo pkill -f IntegratedFlask.py

# 2. GPIO 상태 초기화
sudo python -c "import RPi.GPIO as GPIO; GPIO.cleanup()"

# 3. 프로그램 재시작
python IntegratedFlask.py
```

#### 2. WebSocket 연결 실패
**원인**: 방화벽 또는 네트워크 설정
**해결책**:
```bash
# 포트 5000 개방 확인
sudo ufw allow 5000

# 네트워크 인터페이스 확인
ip addr show
```

#### 3. 모터가 한 방향으로만 회전
**원인**: 모터 드라이버 연결 문제
**해결책**:
- L298N 모터 드라이버 전원 확인
- GPIO 핀 연결 상태 점검
- 모터 전원 공급 확인

#### 4. 거리 센서 측정값이 불안정
**원인**: 전원 노이즈 또는 연결 불량
**해결책**:
```python
# 측정 샘플 수 증가
def get_average_distance(samples=5):  # 기본값: 3
```

### 디버깅 모드

#### 상세 로그 활성화
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 시뮬레이션 모드 강제 활성화
```python
# IntegratedFlask.py 상단에 추가
GPIO_AVAILABLE = False
CAMERA_AVAILABLE = False
```

#### 개별 컴포넌트 테스트
```bash
# 모터만 테스트
cd ../2.ComponentFlask/1.MotorFlask
python app.py

# 센서만 테스트  
cd ../2.SonicFlask
python app.py

# 카메라만 테스트
cd ../3.CameraFlask
python app.py
```

## 📈 성능 최적화

### 메모리 사용량 최적화
```python
# 카메라 프레임 버퍼 크기 조절
import gc
gc.collect()  # 주기적 가비지 컬렉션

# 측정 데이터 크기 제한
measurement_data = deque(maxlen=50)  # 기본값
```

### CPU 사용률 최적화
```python
# 폴링 주기 조절
time.sleep(0.01)  # 10ms (기본값)
# 더 느린 시스템의 경우: time.sleep(0.05)  # 50ms
```

### 네트워크 최적화
```python
# 이미지 품질 조절 (카메라 프레임 생성 시)
ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
```

## 🎓 확장 가이드

### 새로운 센서 추가
1. **GPIO 핀 정의**: 새 센서용 핀 설정
2. **데이터 수집 함수**: 센서 읽기 함수 구현
3. **API 엔드포인트**: REST API 추가
4. **웹 인터페이스**: HTML/JavaScript 업데이트
5. **실시간 업데이트**: SocketIO 이벤트 추가

### 새로운 액추에이터 추가
1. **제어 함수**: 액추에이터 제어 함수 구현
2. **WebSocket 이벤트**: 제어 명령 처리
3. **웹 UI**: 제어 버튼/슬라이더 추가
4. **상태 모니터링**: 현재 상태 표시

### 데이터 저장 기능 추가
```python
import sqlite3
import json
from datetime import datetime

def save_sensor_data(distance, timestamp):
    conn = sqlite3.connect('sensor_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO measurements (distance, timestamp)
        VALUES (?, ?)
    ''', (distance, timestamp))
    conn.commit()
    conn.close()
```

## 📚 참고 자료

### 관련 문서
- [2.ComponentFlask/](../2.ComponentFlask/): 개별 컴포넌트 시스템
- [4.ObstacleAvoidance/](../4.ObstacleAvoidance/): 장애물 회피 시스템
- [5.LineTracing_PID/](../5.LineTracing_PID/): 라인 트레이싱 시스템

### 기술 문서
- [Flask-SocketIO 문서](https://flask-socketio.readthedocs.io/)
- [Chart.js 가이드](https://www.chartjs.org/docs/)
- [Raspberry Pi Camera 가이드](https://picamera.readthedocs.io/)

### 예제 코드
```python
# 사용자 정의 센서 추가 예시
@app.route('/api/custom_sensor')
def get_custom_sensor():
    try:
        # 센서 데이터 읽기
        value = read_custom_sensor()
        return jsonify({
            'success': True,
            'value': value,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
```

---

**🎯 학습 목표 달성도 체크리스트**
- [ ] 통합 시스템 아키텍처 이해
- [ ] 실시간 웹 애플리케이션 구현
- [ ] 멀티스레딩 및 비동기 처리
- [ ] WebSocket 통신 구현
- [ ] 하드웨어-소프트웨어 통합
- [ ] 사용자 인터페이스 설계
- [ ] 시스템 모니터링 및 디버깅

**다음 단계**: [4.ObstacleAvoidance](../4.ObstacleAvoidance/) - 자율 주행 장애물 회피 시스템! 

### 웹에서 "무한 연결 중" 문제

1. **서버 상태 확인**
   ```bash
   # 서버가 정상 실행되는지 확인
   python app.py
   ```

2. **연결 테스트 실행**
   ```bash
   # 별도 터미널에서 테스트
   python test_server.py
   ```

3. **브라우저 개발자 도구 확인**
   - F12 키를 눌러 개발자 도구 열기
   - Console 탭에서 오류 메시지 확인
   - Network 탭에서 WebSocket 연결 상태 확인

4. **일반적인 해결 방법**
   ```bash
   # 포트 충돌 확인
   netstat -an | grep :5000
   
   # 방화벽 설정 확인 (라즈베리파이)
   sudo ufw status
   
   # 브라우저 캐시 삭제
   Ctrl+Shift+R (강력 새로고침)
   ```

### 초음파 센서 데이터가 웹에 표시되지 않는 문제

1. **서버 로그 확인**
   - 터미널에서 "📏 거리 측정" 메시지가 출력되는지 확인
   - "📡 초음파 데이터 전송" 메시지 확인

2. **WebSocket 연결 확인**
   - 브라우저 콘솔에서 "초음파 데이터:" 로그 확인
   - 연결 상태가 "연결됨"인지 확인

3. **하드웨어 연결 확인** (실제 하드웨어 사용 시)
   ```bash
   # GPIO 상태 확인
   gpio readall
   
   # 초음파 센서 연결 확인
   # TRIG: GPIO5, ECHO: GPIO6
   ```

### 모터 제어가 작동하지 않는 문제

1. **연결 상태 확인**
   - 웹 페이지 상단의 연결 상태가 "연결됨"인지 확인

2. **명령 전송 확인**
   - 브라우저 콘솔에서 "모터 명령 전송:" 로그 확인
   - 서버에서 "📡 모터 명령 수신:" 로그 확인

3. **하드웨어 연결 확인** (실제 하드웨어 사용 시)
   ```bash
   # 모터 드라이버 연결 확인
   # IN1: GPIO23, IN2: GPIO24, IN3: GPIO22, IN4: GPIO27
   # ENA: GPIO12, ENB: GPIO13
   ```

### 네트워크 연결 문제

1. **IP 주소 확인**
   ```bash
   hostname -I
   ifconfig
   ```

2. **포트 접근 확인**
   ```bash
   # 다른 기기에서 접근 테스트
   telnet [라즈베리파이IP] 5000
   ```

3. **방화벽 설정** (필요시)
   ```bash
   sudo ufw allow 5000
   ```

## 🎮 사용법

### 키보드 제어
- `W`: 전진
- `X`: 후진  
- `A`: 좌회전
- `D`: 우회전
- `Q`: 왼쪽 앞으로
- `E`: 오른쪽 앞으로
- `Z`: 왼쪽 뒤로
- `C`: 오른쪽 뒤로
- `S`: 정지

### 웹 인터페이스
- **카메라 패널**: 실시간 영상 스트리밍
- **모터 제어**: 방향 버튼 + 속도 슬라이더
- **센서 패널**: 거리 측정값 + 통계 + 차트
- **시스템 로그**: 실시간 상태 메시지

## 📋 시스템 요구사항

### 하드웨어
- Raspberry Pi (Zero 2 W 이상 권장)
- 카메라 모듈 또는 USB 카메라
- HC-SR04 초음파 센서
- L298N 모터 드라이버
- DC 기어 모터 2개

### 소프트웨어
- Python 3.7+
- Flask 2.3.0+
- Flask-SocketIO 5.3.0+
- OpenCV 4.5.0+
- PiCamera2 (라즈베리파이 카메라 사용 시)

## 🔍 디버깅 팁

1. **서버 로그 모니터링**
   ```bash
   python app.py | tee server.log
   ```

2. **브라우저 개발자 도구 활용**
   - Console: JavaScript 오류 및 로그 확인
   - Network: HTTP/WebSocket 요청 상태 확인
   - Application: 로컬 스토리지 및 쿠키 확인

3. **연결 테스트 스크립트 활용**
   ```bash
   python test_server.py
   ```

## 📞 지원

문제가 지속되면 다음 정보와 함께 문의하세요:
- 운영체제 및 Python 버전
- 서버 실행 로그
- 브라우저 콘솔 오류 메시지
- 네트워크 환경 (로컬/원격) 