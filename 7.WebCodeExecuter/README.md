# 💻 패스파인더 웹 코드 실행기

실시간 Python 코드 실행 및 디버깅을 위한 웹 기반 IDE 환경입니다. 무한루프 코드도 안전하게 실행하고 제어할 수 있습니다.

## 📋 목차
- [시스템 개요](#시스템-개요)
- [주요 기능](#주요-기능)
- [설치 및 실행](#설치-및-실행)
- [웹 인터페이스 사용법](#웹-인터페이스-사용법)
- [실시간 실행 시스템](#실시간-실행-시스템)
- [보안 및 안전성](#보안-및-안전성)
- [고급 기능](#고급-기능)
- [문제 해결](#문제-해결)

## 🎯 시스템 개요

### 목적
- **실시간 코드 실행**: Python 코드를 웹에서 즉시 실행
- **무한루프 지원**: 장시간 실행되는 코드 안전 관리
- **실시간 출력**: 코드 실행 결과를 실시간으로 확인
- **원격 개발**: 웹 브라우저만으로 로봇 프로그래밍

### 학습 목표
- 웹 기반 IDE 개발 및 활용
- 실시간 프로세스 관리 기법
- WebSocket 통신 구현
- 안전한 코드 실행 환경 구축

### 기술 스택
- **백엔드**: Flask, Flask-SocketIO, Eventlet
- **프론트엔드**: HTML5, CSS3, JavaScript, CodeMirror
- **통신**: WebSocket (실시간 양방향 통신)
- **프로세스 관리**: subprocess, threading

## 🔧 주요 기능

### 1. 실시간 코드 실행
- **즉시 실행**: 코드 작성 후 바로 실행
- **실시간 출력**: print() 결과 즉시 표시
- **무한루프 지원**: 센서 모니터링, 모터 제어 등
- **프로세스 격리**: 안전한 별도 프로세스 실행

### 2. 고급 코드 에디터
- **구문 강조**: Python 문법 하이라이팅
- **자동 완성**: 기본 Python 키워드 지원
- **라인 번호**: 코드 라인 표시
- **들여쓰기**: 자동 들여쓰기 및 정렬

### 3. 실시간 모니터링
- **실행 상태**: 코드 실행/중지 상태 표시
- **출력 스트림**: 실시간 출력 및 오류 메시지
- **성능 모니터링**: 실행 시간 및 리소스 사용량
- **연결 상태**: WebSocket 연결 상태 표시

### 4. 프로세스 제어
- **안전한 중지**: 실행 중인 코드 안전 종료
- **강제 종료**: 응답하지 않는 프로세스 강제 종료
- **리소스 정리**: 임시 파일 및 메모리 자동 정리
- **다중 세션**: 여러 사용자 동시 지원

## 🚀 설치 및 실행

### 1. 의존성 설치
```bash
cd 7.WebCodeExecuter
pip install flask>=2.0.1
pip install flask-socketio>=5.1.1
pip install eventlet>=0.33.0
```

### 2. 시스템 실행
```bash
python WebCodeExcuter.py
```

### 3. 웹 접속
```
브라우저에서 http://라즈베리파이IP:5000 접속
```

### 4. 연결 확인
- 페이지 로드 시 "서버에 연결되었습니다!" 메시지 확인
- 상단 연결 상태 표시등이 녹색인지 확인

## 📱 웹 인터페이스 사용법

### 메인 화면 구성

#### 1. 코드 에디터 (왼쪽)
- **구문 강조**: Python 코드 자동 하이라이팅
- **라인 번호**: 코드 라인 번호 표시
- **자동 완성**: Tab 키로 기본 키워드 완성
- **들여쓰기**: 자동 들여쓰기 지원

#### 2. 제어 패널 (상단)
```
🚀 실행: 코드 실행 시작
⏹️ 중지: 실행 중인 코드 중지
🗑️ 지우기: 출력 창 내용 지우기
📋 예제: 샘플 코드 로드
```

#### 3. 출력 창 (오른쪽)
- **실시간 출력**: print() 결과 즉시 표시
- **오류 메시지**: 예외 및 오류 정보 표시
- **타임스탬프**: 각 출력의 시간 정보
- **상태 메시지**: 실행 시작/종료 알림

#### 4. 상태 표시
- **연결 상태**: WebSocket 연결 상태 (녹색/빨간색)
- **실행 상태**: 코드 실행 여부 표시
- **세션 ID**: 현재 세션 식별자

### 기본 사용법

#### 1. 간단한 코드 실행
```python
print("Hello, Pathfinder!")
for i in range(5):
    print(f"카운트: {i}")
```

#### 2. 센서 모니터링 예제
```python
import time
import random

print("센서 모니터링 시작...")
for i in range(10):
    distance = random.uniform(10, 100)
    print(f"거리: {distance:.1f}cm")
    time.sleep(1)
print("모니터링 완료")
```

#### 3. 무한루프 예제
```python
import time
import random

print("무한루프 센서 모니터링 시작...")
print("중지 버튼으로 언제든 중단 가능")

count = 0
while True:
    count += 1
    distance = random.uniform(5, 150)
    temperature = random.uniform(20, 30)
    
    print(f"[{count}] 거리: {distance:.1f}cm, 온도: {temperature:.1f}°C")
    time.sleep(2)
```

## ⚡ 실시간 실행 시스템

### 아키텍처 구조

#### 1. 프로세스 격리
```python
# 별도 Python 프로세스에서 실행
process = subprocess.Popen(
    [sys.executable, '-u', temp_file.name],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=0  # 실시간 출력
)
```

#### 2. 실시간 출력 모니터링
```python
def _monitor_output(self):
    while self.is_running and self.process.poll() is None:
        line = self.process.stdout.readline()
        if line:
            # WebSocket으로 실시간 전송
            socketio.emit('realtime_output', {
                'output': line.rstrip(),
                'timestamp': datetime.now().isoformat()
            })
```

#### 3. 안전한 프로세스 종료
```python
def stop_execution(self):
    # 1. 정상 종료 시도
    self.process.terminate()
    
    # 2. 3초 대기
    try:
        self.process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        # 3. 강제 종료
        self.process.kill()
```

### WebSocket 통신 프로토콜

#### 클라이언트 → 서버
```javascript
// 코드 실행 요청
socket.emit('execute_realtime', {
    code: python_code
});

// 실행 중지 요청
socket.emit('stop_execution');

// 연결 상태 확인
socket.emit('ping');
```

#### 서버 → 클라이언트
```javascript
// 실시간 출력
socket.on('realtime_output', function(data) {
    console.log(data.output);
});

// 실행 완료
socket.on('execution_finished', function(data) {
    console.log('종료 코드:', data.exit_code);
});

// 오류 발생
socket.on('execution_error', function(data) {
    console.error('오류:', data.error);
});
```

## 🔒 보안 및 안전성

### 보안 기능

#### 1. 프로세스 격리
- **별도 프로세스**: 메인 서버와 분리된 실행 환경
- **리소스 제한**: 메모리 및 CPU 사용량 제한 가능
- **권한 분리**: 제한된 권한으로 코드 실행

#### 2. 임시 파일 관리
```python
# 안전한 임시 파일 생성
temp_file = tempfile.NamedTemporaryFile(
    mode='w', 
    suffix='.py', 
    delete=False,
    encoding='utf-8'
)

# 자동 정리
def cleanup(self):
    if os.path.exists(self.temp_file.name):
        os.unlink(self.temp_file.name)
```

#### 3. 세션 관리
- **고유 세션 ID**: 각 클라이언트 고유 식별
- **자동 정리**: 연결 해제 시 리소스 자동 정리
- **타임아웃**: 장시간 비활성 세션 자동 종료

### 안전 가이드라인

#### 1. 권장 사항
```python
# ✅ 안전한 코드 예시
import time
print("안전한 센서 읽기")
for i in range(100):  # 제한된 반복
    print(f"값: {i}")
    time.sleep(0.1)
```

#### 2. 주의 사항
```python
# ⚠️ 주의가 필요한 코드
import os
os.system("rm -rf /")  # 시스템 명령 실행 주의

# 🚫 피해야 할 코드
while True:
    pass  # CPU 100% 사용하는 무한루프
```

## 🎛️ 고급 기능

### 1. 예제 코드 템플릿

#### GPIO 제어 예제
```python
# GPIO 제어 템플릿
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.OUT)
    
    for i in range(10):
        GPIO.output(18, GPIO.HIGH)
        print("LED ON")
        time.sleep(0.5)
        GPIO.output(18, GPIO.LOW)
        print("LED OFF")
        time.sleep(0.5)
        
finally:
    GPIO.cleanup()
```

#### 센서 데이터 수집
```python
# 센서 데이터 수집 템플릿
import time
import random

data_log = []
print("데이터 수집 시작...")

for i in range(20):
    # 가상 센서 데이터
    temperature = random.uniform(20, 30)
    humidity = random.uniform(40, 80)
    
    data_log.append({
        'time': time.time(),
        'temp': temperature,
        'humidity': humidity
    })
    
    print(f"[{i+1}] 온도: {temperature:.1f}°C, 습도: {humidity:.1f}%")
    time.sleep(1)

print(f"수집 완료: {len(data_log)}개 데이터")
```

### 2. 디버깅 도구

#### 실행 시간 측정
```python
import time

start_time = time.time()
print("작업 시작...")

# 여기에 측정할 코드 작성
time.sleep(2)  # 예시 작업

end_time = time.time()
print(f"실행 시간: {end_time - start_time:.2f}초")
```

#### 메모리 사용량 확인
```python
import sys
import gc

print(f"Python 버전: {sys.version}")
print(f"참조 카운트: {sys.getrefcount(None)}")

# 가비지 컬렉션 실행
collected = gc.collect()
print(f"정리된 객체: {collected}개")
```

### 3. 성능 최적화

#### 출력 버퍼링 제어
```python
import sys

# 즉시 출력 (버퍼링 비활성화)
print("즉시 출력", flush=True)

# 표준 출력 플러시
sys.stdout.flush()
```

#### 효율적인 반복문
```python
# 효율적인 대용량 데이터 처리
def process_data():
    for i in range(1000):
        if i % 100 == 0:  # 주기적 상태 출력
            print(f"진행률: {i/10:.1f}%")
        # 실제 처리 로직
        result = i ** 2
    print("처리 완료!")

process_data()
```

## 🔍 문제 해결

### 일반적인 문제

#### 1. WebSocket 연결 실패
**증상**: "연결 중..." 상태에서 멈춤
**해결책**:
```bash
# 방화벽 확인
sudo ufw allow 5000

# 포트 사용 확인
netstat -tulpn | grep :5000

# 서버 재시작
python WebCodeExcuter.py
```

#### 2. 코드 실행이 안됨
**증상**: 실행 버튼을 눌러도 반응 없음
**해결책**:
```javascript
// 브라우저 콘솔에서 확인
console.log("WebSocket 상태:", socket.connected);

// 페이지 새로고침 후 재시도
location.reload();
```

#### 3. 출력이 나오지 않음
**증상**: print() 결과가 표시되지 않음
**해결책**:
```python
# 즉시 출력 강제
print("테스트", flush=True)

# 표준 출력 플러시
import sys
sys.stdout.flush()
```

#### 4. 프로세스가 종료되지 않음
**증상**: 중지 버튼을 눌러도 계속 실행
**해결책**:
```bash
# 프로세스 강제 종료
sudo pkill -f WebCodeExcuter.py

# 시스템 재시작
sudo reboot
```

### 디버깅 도구

#### 1. 브라우저 개발자 도구
```javascript
// 콘솔에서 WebSocket 상태 확인
console.log("Socket connected:", socket.connected);
console.log("Socket ID:", socket.id);

// 이벤트 리스너 확인
socket.onAny((event, ...args) => {
    console.log("Socket event:", event, args);
});
```

#### 2. 서버 로그 확인
```bash
# 실시간 로그 확인
tail -f /var/log/pathfinder.log

# 오류 로그 검색
grep -i error /var/log/pathfinder.log
```

#### 3. 네트워크 연결 테스트
```bash
# WebSocket 연결 테스트
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: test" \
     -H "Sec-WebSocket-Version: 13" \
     http://localhost:5000/socket.io/
```

## 📈 성능 최적화

### 1. 서버 최적화
```python
# eventlet 워커 수 조정
socketio.run(app, host='0.0.0.0', port=5000, 
            debug=False, workers=4)

# 메모리 사용량 제한
import resource
resource.setrlimit(resource.RLIMIT_AS, (512*1024*1024, -1))  # 512MB
```

### 2. 클라이언트 최적화
```javascript
// 출력 버퍼링으로 성능 향상
let outputBuffer = [];
let bufferTimer;

socket.on('realtime_output', function(data) {
    outputBuffer.push(data.output);
    
    clearTimeout(bufferTimer);
    bufferTimer = setTimeout(() => {
        displayOutput(outputBuffer.join('\n'));
        outputBuffer = [];
    }, 100);  // 100ms 버퍼링
});
```

### 3. 메모리 관리
```python
# 주기적 가비지 컬렉션
import gc
import threading

def periodic_cleanup():
    while True:
        time.sleep(60)  # 1분마다
        gc.collect()
        print("메모리 정리 완료")

cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()
```

## 📚 참고 자료

### 관련 문서
- [2.ComponentFlask/](../2.ComponentFlask/): 개별 컴포넌트 시스템
- [3.IntegratedFlask/](../3.IntegratedFlask/): 통합 제어 시스템
- [5.LineTracing_PID/](../5.LineTracing_PID/): 라인 트레이싱 시스템

### 기술 문서
- [Flask-SocketIO 문서](https://flask-socketio.readthedocs.io/)
- [Eventlet 가이드](https://eventlet.net/)
- [WebSocket 프로토콜](https://tools.ietf.org/html/rfc6455)
- [CodeMirror 에디터](https://codemirror.net/)

### 보안 가이드
- [Python 보안 모범 사례](https://python.org/dev/security/)
- [웹 애플리케이션 보안](https://owasp.org/www-project-top-ten/)

---

**🎯 학습 목표 달성도 체크리스트**
- [ ] 웹 기반 IDE 환경 구축
- [ ] 실시간 코드 실행 시스템 구현
- [ ] WebSocket 통신 프로토콜 이해
- [ ] 프로세스 관리 및 제어 기법 습득
- [ ] 보안 및 안전성 고려사항 적용
- [ ] 성능 최적화 기법 구현

**다음 단계**: [8.ExtraCode/OpenCV_Test](../8.ExtraCode/OpenCV_Test/) - OpenCV 영상 처리 실험! 