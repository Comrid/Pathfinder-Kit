"""
line_tracing_thin.py - 얇은 검은색 선 인식에 최적화된 라인 트레이싱
OpenCV + PID 제어로 얇은 선을 정확하게 따라가는 자율주행
"""

import cv2
import numpy as np
import time
from picamera2 import Picamera2
import sys
import os

# 모터 컨트롤러 import (상위 폴더에서)
sys.path.append(os.path.join(os.path.dirname(__file__), '../../MotorClassTest'))
from Motor import MotorController

class PIDController:
    """PID 제어기 클래스"""
    
    def __init__(self, kp=1.0, ki=0.0, kd=0.0):
        self.kp = kp  # 비례 게인
        self.ki = ki  # 적분 게인
        self.kd = kd  # 미분 게인
        
        self.previous_error = 0
        self.integral = 0
        self.last_time = time.time()
    
    def update(self, error):
        """PID 제어 값 계산"""
        current_time = time.time()
        dt = current_time - self.last_time
        
        if dt <= 0.0:
            dt = 0.01
        
        # 비례항
        proportional = self.kp * error
        
        # 적분항
        self.integral += error * dt
        integral_term = self.ki * self.integral
        
        # 미분항
        derivative = (error - self.previous_error) / dt
        derivative_term = self.kd * derivative
        
        # PID 출력
        output = proportional + integral_term + derivative_term
        
        # 다음 계산을 위해 저장
        self.previous_error = error
        self.last_time = current_time
        
        return output
    
    def reset(self):
        """PID 제어기 리셋"""
        self.previous_error = 0
        self.integral = 0
        self.last_time = time.time()

class ThinLineTracer:
    """얇은 라인 트레이싱에 최적화된 메인 클래스"""
    
    def __init__(self):
        # 카메라 초기화
        self.picam2 = Picamera2()
        self.picam2.preview_configuration.main.size = (640, 480)
        self.picam2.preview_configuration.main.format = "RGB888"
        self.picam2.configure("preview")
        self.picam2.start()
        
        # 모터 컨트롤러 초기화
        self.motor = MotorController()
        
        # PID 제어기 초기화 (얇은 선용으로 조정)
        self.pid = PIDController(kp=1.2, ki=0.05, kd=0.4)
        
        # 라인 트레이싱 설정
        self.frame_width = 640
        self.frame_height = 480
        self.roi_height = 120  # 얇은 선을 위해 ROI 높이 증가
        self.roi_y = 330       # ROI 위치 조정
        self.roi_margin = 100  # 중앙 기준 좌우 여백 (양쪽에서 잘라낼 크기)
        self.roi_x = self.roi_margin
        self.roi_width = self.frame_width - (2 * self.roi_margin)
        
        # 모터 속도 설정 (얇은 선은 더 신중하게)
        self.base_speed = 35   # 기본 속도 약간 낮춤
        self.max_turn_speed = 25  # 최대 회전 속도 낮춤
        
        # 얇은 라인 검출을 위한 특별 설정
        self.line_threshold = 60  # 임계값 높임 (더 확실한 검은색만)
        self.min_line_area = 50   # 최소 면적 대폭 감소 (얇은 선용)
        self.max_line_area = 5000 # 최대 면적 제한 (노이즈 방지)
        
        # 얇은 선 검출을 위한 고급 설정
        self.use_morphology = True  # 모폴로지 연산 사용
        self.use_skeleton = True    # 스켈레톤화 사용
        self.line_width_threshold = 50  # 예상 라인 폭 (픽셀)
        
        # 상태 변수
        self.line_detected = False
        self.center_x = self.frame_width // 2
        self.running = True
        self.detection_history = []  # 검출 히스토리 (안정성 향상)
        
        print("🤖 패스파인더 얇은 라인 트레이싱 시작!")
        print("얇은 선 검출에 최적화된 설정 적용")
        print("ESC 키를 눌러 종료")
    
    def preprocess_frame(self, frame):
        """얇은 선 검출을 위한 고급 전처리"""
        # 관심 영역(ROI) 추출 (좌우도 잘라내기)
        roi = frame[self.roi_y:self.roi_y + self.roi_height, self.roi_x:self.roi_x + self.roi_width]
        
        # 그레이스케일 변환
        gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        
        # 얇은 선을 위한 특별 전처리
        # 1. 약간의 블러 (너무 강하면 얇은 선이 사라짐)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # 2. 적응적 임계값 또는 일반 임계값
        if self.use_morphology:
            # 적응적 임계값 (조명 변화에 강함)
            binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                         cv2.THRESH_BINARY_INV, 11, 2)
        else:
            # 일반 임계값
            _, binary = cv2.threshold(blurred, self.line_threshold, 255, cv2.THRESH_BINARY_INV)
        
        # 3. 모폴로지 연산으로 노이즈 제거 및 선 연결
        if self.use_morphology:
            # 작은 노이즈 제거
            kernel_noise = np.ones((2, 2), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_noise)
            
            # 끊어진 선 연결
            kernel_connect = np.ones((3, 1), np.uint8)  # 세로로 긴 커널
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_connect)
        
        # 4. 스켈레톤화 (선을 1픽셀 두께로)
        if self.use_skeleton:
            binary = self.skeletonize(binary)
        
        return binary, roi
    
    def skeletonize(self, binary_image):
        """이미지 스켈레톤화 (Zhang-Suen 알고리즘)"""
        # OpenCV의 morphologyEx를 사용한 간단한 스켈레톤화
        skeleton = np.zeros(binary_image.shape, np.uint8)
        eroded = np.copy(binary_image)
        temp = np.zeros(binary_image.shape, np.uint8)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        
        while True:
            cv2.erode(eroded, kernel, eroded)
            cv2.dilate(eroded, kernel, temp)
            cv2.subtract(binary_image, temp, temp)
            cv2.bitwise_or(skeleton, temp, skeleton)
            eroded, binary_image = binary_image, eroded
            if cv2.countNonZero(binary_image) == 0:
                break
                
        return skeleton
    
    def find_line_center_advanced(self, binary_image):
        """얇은 선을 위한 고급 중심점 검출"""
        # 방법 1: 윤곽선 기반 검출
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # 면적과 형태를 고려한 라인 선택
            valid_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if self.min_line_area <= area <= self.max_line_area:
                    # 라인의 길이 대 폭 비율 확인 (얇고 긴 형태)
                    rect = cv2.minAreaRect(contour)
                    width, height = rect[1]
                    if width > 0 and height > 0:
                        aspect_ratio = max(width, height) / min(width, height)
                        if aspect_ratio > 2:  # 길이가 폭의 2배 이상
                            valid_contours.append(contour)
            
            if valid_contours:
                # 가장 큰 유효한 윤곽선 선택
                largest_contour = max(valid_contours, key=cv2.contourArea)
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    return (cx, cy), contours
        
        # 방법 2: 픽셀 기반 중심점 검출 (윤곽선이 실패할 경우)
        return self.find_line_center_pixel_based(binary_image), contours if 'contours' in locals() else []
    
    def find_line_center_pixel_based(self, binary_image):
        """픽셀 기반 라인 중심점 검출"""
        height, width = binary_image.shape
        
        # 각 행에서 라인 픽셀의 중심 계산
        line_centers = []
        for y in range(height):
            row = binary_image[y, :]
            white_pixels = np.where(row == 255)[0]
            
            if len(white_pixels) > 0:
                # 연속된 픽셀 그룹 찾기
                groups = []
                current_group = [white_pixels[0]]
                
                for i in range(1, len(white_pixels)):
                    if white_pixels[i] - white_pixels[i-1] <= 3:  # 3픽셀 이내면 같은 그룹
                        current_group.append(white_pixels[i])
                    else:
                        groups.append(current_group)
                        current_group = [white_pixels[i]]
                groups.append(current_group)
                
                # 가장 긴 그룹을 라인으로 선택
                if groups:
                    longest_group = max(groups, key=len)
                    if len(longest_group) >= 2:  # 최소 2픽셀 이상
                        center_x = int(np.mean(longest_group))
                        line_centers.append((center_x, y))
        
        if line_centers:
            # 모든 중심점의 평균 계산
            avg_x = int(np.mean([center[0] for center in line_centers]))
            avg_y = int(np.mean([center[1] for center in line_centers]))
            return (avg_x, avg_y)
        
        return None
    
    def calculate_steering_with_history(self, line_center):
        """히스토리를 고려한 안정적인 조향 계산"""
        if line_center is None:
            # 최근 검출 히스토리 확인
            if len(self.detection_history) > 0:
                # 최근 3프레임의 평균 사용
                recent_centers = self.detection_history[-3:]
                if recent_centers:
                    avg_x = np.mean([center[0] for center in recent_centers if center])
                    line_center = (int(avg_x), 0)
        
        if line_center is not None:
            # 히스토리에 추가
            self.detection_history.append(line_center)
            if len(self.detection_history) > 10:  # 최대 10프레임 유지
                self.detection_history.pop(0)
            
            # ROI 중심과 라인 중심의 차이 계산
            error = line_center[0] - (self.roi_width // 2)
            
            # PID 제어로 조향 값 계산
            steering = self.pid.update(error)
            
            # 조향 값 제한
            steering = max(-self.max_turn_speed, min(self.max_turn_speed, steering))
            
            return steering
        else:
            # 히스토리에 None 추가
            self.detection_history.append(None)
            if len(self.detection_history) > 10:
                self.detection_history.pop(0)
            
            return 0
    
    def control_motors(self, steering):
        """모터 제어"""
        if not self.line_detected:
            # 라인이 없으면 천천히 정지
            self.motor.stop_motors()
            return
        
        # 좌우 모터 속도 계산 (조향 방향 수정)
        left_speed = self.base_speed + steering
        right_speed = self.base_speed - steering
        
        # 속도 제한 (0-100)
        left_speed = max(0, min(100, left_speed))
        right_speed = max(0, min(100, right_speed))
        
        # 모터 제어
        self.motor.set_individual_speeds(int(right_speed), int(left_speed))
    
    def draw_debug_info(self, frame, binary, line_center, steering, contours):
        """디버그 정보 화면에 표시"""
        # ROI 영역 표시 (좌우 잘린 영역)
        cv2.rectangle(frame, (self.roi_x, self.roi_y), (self.roi_x + self.roi_width, self.roi_y + self.roi_height), (0, 255, 0), 2)
        
        # 중심선 표시 (ROI 영역 기준)
        center_x = self.roi_x + (self.roi_width // 2)
        cv2.line(frame, (center_x, 0), (center_x, self.frame_height), (255, 255, 255), 2)
        
        # 라인 중심점 표시
        if line_center:
            # ROI 좌표를 전체 프레임 좌표로 변환
            actual_x = line_center[0] + self.roi_x
            actual_y = line_center[1] + self.roi_y
            cv2.circle(frame, (actual_x, actual_y), 8, (0, 0, 255), -1)
            
            # 에러 라인 표시
            cv2.line(frame, (center_x, actual_y), (actual_x, actual_y), (255, 0, 0), 2)
        
        # 검출 히스토리 표시
        if len(self.detection_history) > 1:
            for i, hist_center in enumerate(self.detection_history[-5:]):  # 최근 5개
                if hist_center:
                    alpha = 0.3 + (i * 0.15)  # 최근일수록 진하게
                    hist_x = hist_center[0] + self.roi_x  # ROI 좌표 변환
                    hist_y = hist_center[1] + self.roi_y
                    cv2.circle(frame, (hist_x, hist_y), 4, (255, 255, 0), -1)
        
        # 윤곽선 표시 (ROI 영역에)
        if contours:
            roi_contours = []
            for contour in contours:
                # ROI 좌표를 전체 프레임 좌표로 변환
                adjusted_contour = contour.copy()
                adjusted_contour[:, :, 0] += self.roi_x  # X 좌표 변환
                adjusted_contour[:, :, 1] += self.roi_y  # Y 좌표 변환
                roi_contours.append(adjusted_contour)
            cv2.drawContours(frame, roi_contours, -1, (0, 255, 255), 1)
        
        # 이진화 이미지를 작은 창으로 표시 (ROI 비율에 맞게)
        binary_colored = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
        # ROI 비율에 맞게 리사이즈
        display_width = 200
        display_height = int(display_width * self.roi_height / self.roi_width)
        binary_resized = cv2.resize(binary_colored, (display_width, display_height))
        frame[10:10+display_height, 10:10+display_width] = binary_resized
        cv2.rectangle(frame, (10, 10), (10+display_width, 10+display_height), (255, 255, 255), 2)
        
        # 텍스트 정보 표시
        info_y = 140
        cv2.putText(frame, f"Thin Line Mode", (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f"Line Detected: {self.line_detected}", (10, info_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Steering: {steering:.2f}", (10, info_y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Speed: {self.base_speed}", (10, info_y + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"History: {len([h for h in self.detection_history if h])}/10", (10, info_y + 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # 설정 정보 표시
        cv2.putText(frame, f"Morphology: {'ON' if self.use_morphology else 'OFF'}", (220, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        cv2.putText(frame, f"Skeleton: {'ON' if self.use_skeleton else 'OFF'}", (220, info_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        cv2.putText(frame, f"Min Area: {self.min_line_area}", (220, info_y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        
        return frame
    
    def run(self):
        """메인 실행 루프"""
        try:
            while self.running:
                # 프레임 캡처
                frame = self.picam2.capture_array()
                
                # 프레임 전처리
                binary, roi = self.preprocess_frame(frame)
                
                # 라인 중심점 찾기 (고급 알고리즘)
                line_center, contours = self.find_line_center_advanced(binary)
                
                # 라인 검출 상태 업데이트
                self.line_detected = line_center is not None
                
                # 조향 계산 (히스토리 고려)
                steering = self.calculate_steering_with_history(line_center)
                
                # 모터 제어
                self.control_motors(steering)
                
                # 디버그 정보 표시
                debug_frame = self.draw_debug_info(frame, binary, line_center, steering, contours)
                
                # 화면 표시
                cv2.imshow('Thin Line Tracing', debug_frame)
                
                # 키 입력 처리
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC 키
                    break
                elif key == ord('r'):  # R 키로 PID 리셋
                    self.pid.reset()
                    self.detection_history.clear()
                    print("PID 제어기 및 히스토리 리셋")
                elif key == ord('+'):  # 속도 증가
                    self.base_speed = min(60, self.base_speed + 5)
                    print(f"속도 증가: {self.base_speed}")
                elif key == ord('-'):  # 속도 감소
                    self.base_speed = max(15, self.base_speed - 5)
                    print(f"속도 감소: {self.base_speed}")
                elif key == ord('m'):  # 모폴로지 토글
                    self.use_morphology = not self.use_morphology
                    print(f"모폴로지 연산: {'ON' if self.use_morphology else 'OFF'}")
                elif key == ord('s'):  # 스켈레톤 토글
                    self.use_skeleton = not self.use_skeleton
                    print(f"스켈레톤화: {'ON' if self.use_skeleton else 'OFF'}")
                elif key == ord('t'):  # 임계값 조정
                    self.line_threshold = (self.line_threshold + 10) % 100 + 30
                    print(f"임계값: {self.line_threshold}")
                elif key == ord('a'):  # 좌우 여백 감소 (ROI 확장)
                    self.roi_margin = max(0, self.roi_margin - 10)
                    self.roi_x = self.roi_margin
                    self.roi_width = self.frame_width - (2 * self.roi_margin)
                    print(f"좌우 여백: {self.roi_margin}, ROI 폭: {self.roi_width}")
                elif key == ord('d'):  # 좌우 여백 증가 (ROI 축소)
                    self.roi_margin = min(200, self.roi_margin + 10)
                    self.roi_x = self.roi_margin
                    self.roi_width = self.frame_width - (2 * self.roi_margin)
                    print(f"좌우 여백: {self.roi_margin}, ROI 폭: {self.roi_width}")
        
        except KeyboardInterrupt:
            print("\n사용자에 의해 중단됨")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """리소스 정리"""
        print("얇은 라인 트레이싱 종료 중...")
        self.motor.stop_motors()
        self.motor.cleanup()
        cv2.destroyAllWindows()
        self.picam2.stop()
        print("정리 완료!")

# 사용 예제
if __name__ == "__main__":
    print("🤖 패스파인더 얇은 라인 트레이싱 시작!")
    print("=" * 60)
    print("얇은 검은색 선 인식에 최적화된 설정:")
    print("- 적응적 임계값 처리")
    print("- 모폴로지 연산으로 노이즈 제거")
    print("- 스켈레톤화로 선 정규화")
    print("- 검출 히스토리 기반 안정화")
    print("=" * 60)
    print("조작법:")
    print("ESC: 종료")
    print("R: PID 및 히스토리 리셋")
    print("+/-: 속도 조절")
    print("M: 모폴로지 연산 ON/OFF")
    print("S: 스켈레톤화 ON/OFF")
    print("T: 임계값 순환 조정")
    print("A/D: 좌우 여백 조정 (중앙 기준)")
    print("=" * 60)
    
    # 얇은 라인 트레이서 생성 및 실행
    tracer = ThinLineTracer()
    tracer.run() 