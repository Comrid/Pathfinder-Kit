# 🎥 패스파인더 OpenCV 테스트 시스템

Raspberry Pi 카메라와 OpenCV를 활용한 실시간 영상 처리 실험 환경입니다. 다양한 컴퓨터 비전 기법을 테스트하고 학습할 수 있습니다.

## 📋 목차
- [시스템 개요](#시스템-개요)
- [주요 기능](#주요-기능)
- [설치 및 실행](#설치-및-실행)
- [OpenCV 기능 설명](#opencv-기능-설명)
- [영상 처리 기법](#영상-처리-기법)
- [커스터마이징](#커스터마이징)
- [성능 최적화](#성능-최적화)
- [확장 기능](#확장-기능)

## 🎯 시스템 개요

### 목적
- **OpenCV 학습**: 컴퓨터 비전 기법 실습 및 이해
- **실시간 처리**: 라이브 카메라 영상에 다양한 필터 적용
- **시각적 피드백**: 처리 결과를 실시간으로 확인
- **실험 환경**: 새로운 영상 처리 알고리즘 테스트

### 학습 목표
- OpenCV 라이브러리 활용법 습득
- 컴퓨터 비전 기초 이론 이해
- 실시간 영상 처리 시스템 구현
- 로봇 비전 시스템 개발 기초

### 기술 스택
- **영상 처리**: OpenCV, NumPy
- **카메라**: Picamera2 (Raspberry Pi Camera)
- **웹 프레임워크**: Flask
- **스트리밍**: MJPEG over HTTP

## 🔧 주요 기능

### 1. 실시간 영상 처리
- **엣지 검출**: Canny Edge Detection으로 윤곽선 추출
- **색상 검출**: HSV 색공간에서 특정 색상 객체 찾기
- **얼굴 검출**: Haar Cascade 분류기로 얼굴 인식
- **윤곽선 검출**: 객체의 외곽선 추출 및 표시

### 2. 성능 모니터링
- **FPS 표시**: 실시간 프레임 처리 속도 측정
- **윤곽선 개수**: 검출된 윤곽선 수량 표시
- **처리 시간**: 각 프레임 처리 소요 시간

### 3. 시각적 인터페이스
- **멀티 뷰**: 원본과 처리된 영상 동시 표시
- **정보 오버레이**: 처리 결과 정보 실시간 표시
- **십자선**: 중앙 기준점 표시

### 4. 웹 기반 스트리밍
- **실시간 스트림**: MJPEG 형태로 웹 브라우저에 전송
- **반응형 디자인**: 다양한 화면 크기 지원
- **원격 접속**: 네트워크를 통한 원격 모니터링

## 🚀 설치 및 실행

### 1. 의존성 설치
```bash
cd 8.ExtraCode/OpenCV_Test
pip install opencv-python-headless>=4.5.0
pip install numpy>=1.19.5
pip install flask>=2.0.1
pip install picamera2>=0.3.12
```

### 2. 카메라 설정 확인
```bash
# 카메라 연결 상태 확인
vcgencmd get_camera

# 카메라 인터페이스 활성화 (필요시)
sudo raspi-config
# Interface Options > Camera > Enable
```

### 3. 시스템 실행
```bash
python opencv_test.py
```

### 4. 웹 접속
```
브라우저에서 http://라즈베리파이IP:5000 접속
```

### 5. 테스트 확인
- 카메라 영상이 정상적으로 표시되는지 확인
- 각종 OpenCV 효과가 적용되는지 확인
- FPS가 안정적으로 표시되는지 확인

## 🖼️ OpenCV 기능 설명

### 1. 엣지 검출 (Canny Edge Detection)

#### 원리
```python
# 그레이스케일 변환
gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

# Canny 엣지 검출
edges = cv2.Canny(gray, 50, 150)
```

#### 특징
- **저임계값 (50)**: 약한 엣지 검출 기준
- **고임계값 (150)**: 강한 엣지 검출 기준
- **용도**: 객체 윤곽선, 라인 검출 등

#### 활용 예시
- 라인 트레이싱에서 선 검출
- 장애물의 경계 인식
- 도형 인식 및 분석

### 2. 색상 검출 (Color Detection)

#### HSV 색공간 활용
```python
# RGB를 HSV로 변환
hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

# 빨간색 범위 정의
lower_red = np.array([0, 50, 50])
upper_red = np.array([10, 255, 255])

# 색상 마스크 생성
mask = cv2.inRange(hsv, lower_red, upper_red)
```

#### HSV 색공간 장점
- **조명 변화에 강함**: 밝기와 색상 분리
- **직관적**: 사람이 인식하는 색상과 유사
- **정확한 색상 분리**: RGB보다 색상 구분 용이

#### 색상별 HSV 범위
```python
# 빨간색 (Red)
lower_red = np.array([0, 50, 50])
upper_red = np.array([10, 255, 255])

# 파란색 (Blue)
lower_blue = np.array([100, 50, 50])
upper_blue = np.array([130, 255, 255])

# 녹색 (Green)
lower_green = np.array([40, 50, 50])
upper_green = np.array([80, 255, 255])

# 노란색 (Yellow)
lower_yellow = np.array([20, 50, 50])
upper_yellow = np.array([30, 255, 255])
```

### 3. 얼굴 검출 (Face Detection)

#### Haar Cascade 분류기
```python
# 분류기 로드
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# 얼굴 검출
faces = face_cascade.detectMultiScale(gray, 1.1, 4)
```

#### 파라미터 설명
- **scaleFactor (1.1)**: 이미지 크기 축소 비율
- **minNeighbors (4)**: 검출 신뢰도 기준
- **minSize**: 최소 검출 크기
- **maxSize**: 최대 검출 크기

#### 다른 검출 가능한 객체
```python
# 눈 검출
eye_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_eye.xml'
)

# 미소 검출
smile_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_smile.xml'
)

# 전신 검출
body_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_fullbody.xml'
)
```

### 4. 윤곽선 검출 (Contour Detection)

#### 윤곽선 찾기
```python
# 윤곽선 검출
contours, hierarchy = cv2.findContours(
    edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
)

# 윤곽선 그리기
cv2.drawContours(frame, contours, -1, (0, 255, 0), 2)
```

#### 검색 모드 (Retrieval Mode)
- **RETR_EXTERNAL**: 가장 바깥쪽 윤곽선만
- **RETR_LIST**: 모든 윤곽선을 리스트로
- **RETR_TREE**: 계층 구조로 모든 윤곽선
- **RETR_CCOMP**: 2단계 계층 구조

#### 근사 방법 (Approximation Method)
- **CHAIN_APPROX_NONE**: 모든 윤곽선 점 저장
- **CHAIN_APPROX_SIMPLE**: 끝점만 저장하여 압축

## 🎛️ 영상 처리 기법

### 1. 전처리 기법

#### 노이즈 제거
```python
# 가우시안 블러
blurred = cv2.GaussianBlur(frame, (5, 5), 0)

# 미디언 필터
median = cv2.medianBlur(frame, 5)

# 양방향 필터 (엣지 보존)
bilateral = cv2.bilateralFilter(frame, 9, 75, 75)
```

#### 히스토그램 평활화
```python
# 그레이스케일 히스토그램 평활화
equalized = cv2.equalizeHist(gray)

# 컬러 이미지 CLAHE
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
lab = cv2.cvtColor(frame, cv2.COLOR_RGB2LAB)
lab[:,:,0] = clahe.apply(lab[:,:,0])
enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
```

### 2. 형태학적 연산

#### 기본 연산
```python
# 커널 정의
kernel = np.ones((5,5), np.uint8)

# 침식 (Erosion)
erosion = cv2.erode(binary, kernel, iterations=1)

# 팽창 (Dilation)
dilation = cv2.dilate(binary, kernel, iterations=1)

# 열림 (Opening) = 침식 + 팽창
opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

# 닫힘 (Closing) = 팽창 + 침식
closing = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
```

### 3. 특징점 검출

#### 코너 검출
```python
# Harris 코너 검출
corners = cv2.cornerHarris(gray, 2, 3, 0.04)

# Shi-Tomasi 코너 검출
corners = cv2.goodFeaturesToTrack(gray, 100, 0.01, 10)
```

#### SIFT/ORB 특징점
```python
# ORB 특징점 검출기
orb = cv2.ORB_create()
keypoints, descriptors = orb.detectAndCompute(gray, None)

# 특징점 그리기
img_with_keypoints = cv2.drawKeypoints(frame, keypoints, None)
```

## ⚙️ 커스터마이징

### 1. 새로운 색상 검출 추가

#### 파란색 검출 예시
```python
def detect_blue_objects(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
    
    # 파란색 범위
    lower_blue = np.array([100, 50, 50])
    upper_blue = np.array([130, 255, 255])
    
    # 마스크 생성
    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
    
    # 결과 적용
    blue_result = cv2.bitwise_and(frame, frame, mask=blue_mask)
    
    return blue_result, blue_mask
```

### 2. 모션 검출 추가

#### 배경 차분법
```python
# 배경 모델 초기화
background_subtractor = cv2.createBackgroundSubtractorMOG2()

def detect_motion(frame):
    # 전경 마스크 생성
    fg_mask = background_subtractor.apply(frame)
    
    # 노이즈 제거
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
    
    # 윤곽선 검출
    contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 움직이는 객체 표시
    for contour in contours:
        if cv2.contourArea(contour) > 500:
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
    
    return frame
```

### 3. 객체 추적 추가

#### 단일 객체 추적
```python
# 추적기 초기화
tracker = cv2.TrackerCSRT_create()

def initialize_tracking(frame, bbox):
    """추적 초기화"""
    success = tracker.init(frame, bbox)
    return success

def update_tracking(frame):
    """추적 업데이트"""
    success, bbox = tracker.update(frame)
    
    if success:
        x, y, w, h = [int(i) for i in bbox]
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
        cv2.putText(frame, "Tracking", (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    
    return frame, success
```

## 📈 성능 최적화

### 1. 해상도 최적화
```python
# 처리 속도 향상을 위한 해상도 조정
def optimize_resolution(frame, target_width=320):
    height, width = frame.shape[:2]
    scale = target_width / width
    new_height = int(height * scale)
    
    # 크기 조정
    resized = cv2.resize(frame, (target_width, new_height))
    return resized, scale
```

### 2. ROI (관심 영역) 처리
```python
def process_roi_only(frame):
    height, width = frame.shape[:2]
    
    # 하단 1/3 영역만 처리 (라인 트레이싱용)
    roi_y_start = height * 2 // 3
    roi = frame[roi_y_start:height, :]
    
    # ROI에서만 처리 수행
    processed_roi = apply_processing(roi)
    
    # 원본에 결과 적용
    result = frame.copy()
    result[roi_y_start:height, :] = processed_roi
    
    return result
```

### 3. 멀티스레딩 활용
```python
import threading
import queue

class FrameProcessor:
    def __init__(self):
        self.frame_queue = queue.Queue(maxsize=2)
        self.result_queue = queue.Queue(maxsize=2)
        self.processing_thread = threading.Thread(target=self._process_frames)
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def _process_frames(self):
        while True:
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                processed = self.apply_opencv_processing(frame)
                
                if not self.result_queue.full():
                    self.result_queue.put(processed)
    
    def add_frame(self, frame):
        if not self.frame_queue.full():
            self.frame_queue.put(frame)
    
    def get_result(self):
        if not self.result_queue.empty():
            return self.result_queue.get()
        return None
```

## 🎓 확장 기능

### 1. 머신러닝 통합

#### TensorFlow Lite 모델 사용
```python
import tflite_runtime.interpreter as tflite

# 모델 로드
interpreter = tflite.Interpreter(model_path="model.tflite")
interpreter.allocate_tensors()

def run_inference(frame):
    # 입력 데이터 준비
    input_data = preprocess_frame(frame)
    
    # 추론 실행
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    
    # 결과 가져오기
    output_data = interpreter.get_tensor(output_details[0]['index'])
    
    return postprocess_output(output_data)
```

### 2. 데이터 로깅

#### 처리 결과 저장
```python
import json
from datetime import datetime

class DataLogger:
    def __init__(self):
        self.log_data = []
    
    def log_detection(self, detection_type, count, confidence=None):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': detection_type,
            'count': count,
            'confidence': confidence
        }
        self.log_data.append(entry)
    
    def save_log(self, filename='detection_log.json'):
        with open(filename, 'w') as f:
            json.dump(self.log_data, f, indent=2)
```

### 3. 실시간 분석

#### 통계 수집
```python
class PerformanceAnalyzer:
    def __init__(self):
        self.frame_times = []
        self.detection_counts = {'faces': 0, 'objects': 0}
    
    def update_frame_time(self, processing_time):
        self.frame_times.append(processing_time)
        if len(self.frame_times) > 100:
            self.frame_times.pop(0)
    
    def get_average_fps(self):
        if self.frame_times:
            avg_time = sum(self.frame_times) / len(self.frame_times)
            return 1.0 / avg_time if avg_time > 0 else 0
        return 0
    
    def update_detection_count(self, detection_type):
        if detection_type in self.detection_counts:
            self.detection_counts[detection_type] += 1
```

## 📚 참고 자료

### 관련 문서
- [5.LineTracing_PID/](../5.LineTracing_PID/): 라인 트레이싱에서 OpenCV 활용
- [3.IntegratedFlask/](../3.IntegratedFlask/): 통합 시스템에서 카메라 사용
- [2.ComponentFlask/3.CameraFlask/](../2.ComponentFlask/3.CameraFlask/): 기본 카메라 제어

### 기술 문서
- [OpenCV 공식 문서](https://docs.opencv.org/)
- [Picamera2 가이드](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)
- [NumPy 문서](https://numpy.org/doc/)

### 학습 자료
- [OpenCV 튜토리얼](https://docs.opencv.org/4.x/d9/df8/tutorial_root.html)
- [컴퓨터 비전 기초](https://opencv-python-tutroals.readthedocs.io/)
- [이미지 처리 이론](https://homepages.inf.ed.ac.uk/rbf/HIPR2/)

### 예제 코드
```python
# 사용자 정의 필터 예시
def custom_filter(frame):
    # 세피아 효과
    kernel = np.array([[0.272, 0.534, 0.131],
                       [0.349, 0.686, 0.168],
                       [0.393, 0.769, 0.189]])
    
    sepia = cv2.transform(frame, kernel)
    return np.clip(sepia, 0, 255).astype(np.uint8)

# 엠보싱 효과
def emboss_effect(frame):
    kernel = np.array([[-2, -1, 0],
                       [-1,  1, 1],
                       [ 0,  1, 2]])
    
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    embossed = cv2.filter2D(gray, -1, kernel)
    return cv2.cvtColor(embossed, cv2.COLOR_GRAY2RGB)
```

---

**🎯 학습 목표 달성도 체크리스트**
- [ ] OpenCV 기본 기능 이해 및 활용
- [ ] 실시간 영상 처리 시스템 구현
- [ ] 다양한 컴퓨터 비전 기법 실습
- [ ] 성능 최적화 기법 적용
- [ ] 커스텀 영상 처리 알고리즘 개발
- [ ] 로봇 비전 시스템 기초 구축

**활용 분야**: 라인 트레이싱, 객체 인식, 장애물 감지, 자율 주행 등 다양한 로봇 비전 프로젝트에 응용 가능! 