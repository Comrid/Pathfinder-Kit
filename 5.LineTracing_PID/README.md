# 🛤️ 패스파인더 라인 트레이싱 PID 시스템

OpenCV와 PID 제어를 활용한 고급 라인 트레이싱 시스템입니다. 얇은 검은색 선을 정밀하게 인식하고 추적하여 자율 주행을 구현합니다.

## 📋 목차
- [시스템 개요](#시스템-개요)
- [주요 기능](#주요-기능)
- [설치 및 실행](#설치-및-실행)
- [웹 인터페이스 사용법](#웹-인터페이스-사용법)
- [PID 제어 이론](#pid-제어-이론)
- [영상 처리 알고리즘](#영상-처리-알고리즘)
- [설정 및 튜닝](#설정-및-튜닝)
- [문제 해결](#문제-해결)

## 🎯 시스템 개요

### 목적
- **정밀 라인 추적**: 얇은 검은색 선을 정확하게 인식 및 추적
- **PID 제어**: 안정적이고 부드러운 주행 제어
- **실시간 처리**: 고속 영상 처리 및 즉시 응답
- **적응형 알고리즘**: 다양한 환경 조건에 대응

### 학습 목표
- PID 제어 이론 및 실제 적용
- OpenCV 영상 처리 기법 습득
- 실시간 시스템 설계 및 구현
- 자율 주행 로봇 제어 시스템 개발

### 기술 스택
- **영상 처리**: OpenCV, NumPy
- **제어 시스템**: PID Controller
- **웹 프레임워크**: Flask
- **하드웨어**: Raspberry Pi Camera, 모터 드라이버

## 🔧 주요 기능

### 1. 고급 영상 처리
- **적응형 임계값**: 조명 변화에 자동 대응
- **모폴로지 연산**: 노이즈 제거 및 선 연결
- **스켈레톤화**: 얇은 선의 중심선 추출
- **컨투어 분석**: 가장 적합한 라인 선택

### 2. PID 제어 시스템
- **비례 제어 (P)**: 현재 오차에 비례한 제어
- **적분 제어 (I)**: 누적 오차 보정
- **미분 제어 (D)**: 오차 변화율 기반 예측 제어
- **실시간 튜닝**: 웹에서 PID 파라미터 조절

### 3. 지능형 주행 제어
- **히스토리 기반 예측**: 과거 경로 데이터 활용
- **적응형 속도 제어**: 커브 구간 자동 감속
- **라인 손실 복구**: 라인을 놓쳤을 때 복구 알고리즘
- **안전 기능**: 비상 정지 및 오류 처리

### 4. 실시간 모니터링
- **라이브 영상**: 처리된 영상 실시간 스트리밍
- **디버그 정보**: ROI, 중심선, PID 값 표시
- **상태 모니터링**: 추적 상태 및 성능 지표
- **파라미터 조절**: 실시간 설정 변경

## 🚀 설치 및 실행

### 1. 의존성 설치
```bash
cd 5.LineTracing_PID
pip install opencv-python-headless>=4.5.0
pip install numpy>=1.19.5
pip install flask>=2.0.1
pip install picamera2>=0.3.12
```

### 2. 모터 컨트롤러 설정
```bash
# Motor.py와 config.py가 올바른 위치에 있는지 확인
ls Motor.py config.py
```

### 3. 카메라 설정 확인
```bash
# 카메라 연결 상태 확인
vcgencmd get_camera

# 카메라 인터페이스 활성화 (필요시)
sudo raspi-config
# Interface Options > Camera > Enable
```

### 4. 시스템 실행
```bash
python LineTracker.py
```

### 5. 웹 접속
```
브라우저에서 http://라즈베리파이IP:5000 접속
```

## 📱 웹 인터페이스 사용법

### 메인 화면 구성

#### 1. 실시간 영상 스트림
- **원본 영상**: 카메라에서 받은 실시간 영상
- **처리된 영상**: 이진화 및 ROI 표시
- **디버그 정보**: 중심선, PID 값, 상태 정보 오버레이

#### 2. 라인 트레이싱 제어
```
🚀 시작: 라인 트레이싱 시작
⏹️ 정지: 트레이싱 중지
🔄 PID 리셋: PID 제어기 초기화
📊 히스토리 리셋: 경로 히스토리 초기화
```

#### 3. 속도 조절
- **기본 속도**: 15-60 범위에서 조절 (기본값: 35)
- **실시간 변경**: 주행 중에도 속도 조절 가능
- **커브 감속**: 급격한 방향 변화 시 자동 감속

#### 4. PID 파라미터 튜닝
```
P (비례): 1.2 (기본값) - 현재 오차 반응 강도
I (적분): 0.05 (기본값) - 누적 오차 보정 강도  
D (미분): 0.4 (기본값) - 오차 변화 예측 강도
```

#### 5. 얇은 선 전용 설정
- **모폴로지 연산**: 노이즈 제거 및 선 연결 (기본: ON)
- **스켈레톤화**: 중심선 추출 (기본: ON)
- **최소 면적**: 유효 컨투어 최소 크기 (기본: 50)
- **임계값**: 이진화 임계값 (기본: 60)

#### 6. ROI (관심 영역) 설정
- **ROI 높이**: 80-200 픽셀 (기본: 120)
- **ROI 오프셋**: 화면 하단에서의 거리 (기본: 50)

## 🎛️ PID 제어 이론

### PID 제어기 구성 요소

#### 1. 비례 제어 (Proportional - P)
```python
P_output = Kp * error
```
- **역할**: 현재 오차에 비례하여 제어 신호 생성
- **특성**: 빠른 응답, 정상상태 오차 존재
- **튜닝**: 값이 클수록 빠른 응답, 너무 크면 진동

#### 2. 적분 제어 (Integral - I)
```python
I_output = Ki * sum(errors) * dt
```
- **역할**: 누적된 오차를 제거하여 정상상태 오차 해결
- **특성**: 느린 응답, 정상상태 오차 제거
- **튜닝**: 값이 클수록 빠른 정정, 너무 크면 오버슈트

#### 3. 미분 제어 (Derivative - D)
```python
D_output = Kd * (error - previous_error) / dt
```
- **역할**: 오차 변화율을 예측하여 안정성 향상
- **특성**: 오버슈트 감소, 노이즈에 민감
- **튜닝**: 값이 클수록 안정적, 너무 크면 노이즈 증폭

### PID 튜닝 가이드

#### 1. 단계별 튜닝 방법
```
1단계: P만 사용 (I=0, D=0)
- P 값을 점진적으로 증가
- 진동이 시작되는 지점 확인

2단계: D 추가
- D 값을 조금씩 증가
- 진동 감소 및 안정성 향상 확인

3단계: I 추가
- I 값을 작게 시작
- 정상상태 오차 제거 확인
```

#### 2. 실제 튜닝 예시
```python
# 보수적 설정 (안정적, 느림)
Kp = 0.8, Ki = 0.02, Kd = 0.3

# 기본 설정 (균형)
Kp = 1.2, Ki = 0.05, Kd = 0.4

# 공격적 설정 (빠름, 불안정할 수 있음)
Kp = 1.8, Ki = 0.1, Kd = 0.6
```

## 🖼️ 영상 처리 알고리즘

### 1. 전처리 단계

#### 그레이스케일 변환
```python
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
```

#### 가우시안 블러
```python
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
```

#### 적응형 임계값
```python
binary = cv2.adaptiveThreshold(blurred, 255, 
                              cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                              cv2.THRESH_BINARY_INV, 11, 2)
```

### 2. 얇은 선 특화 처리

#### 모폴로지 연산
```python
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
morphed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
```

#### 스켈레톤화 (Zhang-Suen 알고리즘)
```python
def skeletonize(binary_image):
    skeleton = np.zeros(binary_image.shape, np.uint8)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    
    while True:
        opened = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, element)
        temp = cv2.subtract(binary_image, opened)
        eroded = cv2.erode(binary_image, element)
        skeleton = cv2.bitwise_or(skeleton, temp)
        binary_image = eroded.copy()
        
        if cv2.countNonZero(binary_image) == 0:
            break
    
    return skeleton
```

### 3. 라인 중심 검출

#### 컨투어 기반 방법
```python
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
largest_contour = max(contours, key=cv2.contourArea)
M = cv2.moments(largest_contour)
center_x = int(M["m10"] / M["m00"])
```

#### 픽셀 기반 방법
```python
white_pixels = np.where(binary == 255)
if len(white_pixels[1]) > 0:
    center_x = int(np.mean(white_pixels[1]))
```

### 4. ROI (관심 영역) 처리
```python
roi_height = 120
roi_offset = 50
roi_y_start = frame.shape[0] - roi_height - roi_offset
roi_y_end = frame.shape[0] - roi_offset
roi = binary[roi_y_start:roi_y_end, :]
```

## ⚙️ 설정 및 튜닝

### 환경별 최적 설정

#### 1. 실내 환경 (형광등 조명)
```python
threshold = 60
morphology_enabled = True
skeleton_enabled = True
min_area = 50
```

#### 2. 실외 환경 (자연광)
```python
threshold = 80
morphology_enabled = True
skeleton_enabled = False
min_area = 100
```

#### 3. 어두운 환경
```python
threshold = 40
morphology_enabled = True
skeleton_enabled = True
min_area = 30
```

### 라인 종류별 설정

#### 1. 매우 얇은 선 (1-2mm)
```python
Kp = 1.5, Ki = 0.08, Kd = 0.5
skeleton_enabled = True
min_area = 20
```

#### 2. 보통 선 (3-5mm)
```python
Kp = 1.2, Ki = 0.05, Kd = 0.4
skeleton_enabled = False
min_area = 50
```

#### 3. 두꺼운 선 (6mm 이상)
```python
Kp = 1.0, Ki = 0.03, Kd = 0.3
skeleton_enabled = False
min_area = 100
```

### 성능 최적화 설정

#### 1. 고속 주행용
```python
base_speed = 50
roi_height = 100  # 작은 ROI로 처리 속도 향상
```

#### 2. 정밀 주행용
```python
base_speed = 25
roi_height = 150  # 큰 ROI로 정확도 향상
```

## 🔍 문제 해결

### 일반적인 문제

#### 1. 라인을 인식하지 못하는 경우
**원인**: 조명 조건 또는 임계값 문제
**해결책**:
```python
# 임계값 조정
threshold = 40-80 범위에서 조절

# 적응형 임계값 사용
cv2.adaptiveThreshold() 파라미터 조정
```

#### 2. 진동하며 주행하는 경우
**원인**: PID 파라미터 부적절
**해결책**:
```python
# P 값 감소
Kp = 0.8  # 기본값 1.2에서 감소

# D 값 증가
Kd = 0.6  # 기본값 0.4에서 증가
```

#### 3. 커브에서 라인을 놓치는 경우
**원인**: ROI 설정 또는 속도 문제
**해결책**:
```python
# ROI 높이 증가
roi_height = 150

# 기본 속도 감소
base_speed = 30
```

#### 4. 노이즈가 많은 경우
**원인**: 조명 불균일 또는 바닥 패턴
**해결책**:
```python
# 모폴로지 연산 활성화
morphology_enabled = True

# 최소 면적 증가
min_area = 100
```

### 디버깅 도구

#### 1. 영상 처리 단계별 확인
```python
# 각 처리 단계 이미지 저장
cv2.imwrite('debug_gray.jpg', gray)
cv2.imwrite('debug_binary.jpg', binary)
cv2.imwrite('debug_morphed.jpg', morphed)
```

#### 2. PID 값 로깅
```python
print(f"Error: {error}, P: {p_output}, I: {i_output}, D: {d_output}")
```

#### 3. 성능 측정
```python
import time
start_time = time.time()
# 영상 처리 코드
processing_time = time.time() - start_time
print(f"Processing time: {processing_time:.3f}s")
```

## 📈 성능 최적화

### 1. 영상 처리 최적화
```python
# 해상도 조정
frame = cv2.resize(frame, (320, 240))  # 처리 속도 향상

# ROI만 처리
roi = frame[roi_y_start:roi_y_end, :]  # 필요한 영역만 처리
```

### 2. 알고리즘 최적화
```python
# 스켈레톤화 조건부 사용
if line_thickness < 3:
    binary = skeletonize(binary)
```

### 3. 메모리 최적화
```python
# 불필요한 변수 정리
del temp_image
gc.collect()
```

## 🎓 확장 기능

### 1. 다중 라인 추적
```python
def detect_multiple_lines(binary):
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    valid_lines = []
    for contour in contours:
        if cv2.contourArea(contour) > min_area:
            valid_lines.append(contour)
    return valid_lines
```

### 2. 교차점 감지
```python
def detect_intersection(binary):
    # 허프 변환으로 직선 검출
    lines = cv2.HoughLinesP(binary, 1, np.pi/180, threshold=50)
    # 교차점 계산 로직
    return intersection_points
```

### 3. 색상 라인 추적
```python
def detect_colored_line(frame, color_range):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, color_range[0], color_range[1])
    return mask
```

## 📚 참고 자료

### 관련 문서
- [3.IntegratedFlask/](../3.IntegratedFlask/): 통합 제어 시스템
- [4.ObstacleAvoidance/](../4.ObstacleAvoidance/): 장애물 회피 시스템
- [Motor.py](./Motor.py): 모터 제어 클래스

### 기술 문서
- [OpenCV 공식 문서](https://docs.opencv.org/)
- [PID 제어 이론](https://en.wikipedia.org/wiki/PID_controller)
- [Raspberry Pi Camera 가이드](https://picamera.readthedocs.io/)

### 알고리즘 참고
- Zhang-Suen Skeletonization Algorithm
- Adaptive Thresholding Techniques
- Morphological Image Processing

---

**🎯 학습 목표 달성도 체크리스트**
- [ ] PID 제어 이론 이해 및 구현
- [ ] OpenCV 영상 처리 기법 습득
- [ ] 실시간 라인 트레이싱 시스템 구현
- [ ] 웹 기반 모니터링 및 튜닝 시스템 개발
- [ ] 다양한 환경 조건에 대한 적응 능력 확보
- [ ] 성능 최적화 및 디버깅 기법 습득

**다음 단계**: [7.WebCodeExecuter](../7.WebCodeExecuter/) - 웹 기반 코드 실행 환경! 