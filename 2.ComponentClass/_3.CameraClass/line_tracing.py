"""
line_tracing.py - 패스파인더 키트용 라인 트레이싱
OpenCV + PID 제어로 흰색 바탕의 검은 선을 따라가는 자율주행
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

class LineTracer:
    """라인 트레이싱 메인 클래스"""
    
    def __init__(self):
        # 카메라 초기화
        self.picam2 = Picamera2()
        self.picam2.preview_configuration.main.size = (640, 480)
        self.picam2.preview_configuration.main.format = "RGB888"
        self.picam2.configure("preview")
        self.picam2.start()
        
        # 모터 컨트롤러 초기화
        self.motor = MotorController()
        
        # PID 제어기 초기화 (값은 실험을 통해 조정)
        self.pid = PIDController(kp=0.8, ki=0.1, kd=0.3)
        
        # 라인 트레이싱 설정
        self.frame_width = 640
        self.frame_height = 480
        self.roi_height = 100  # 관심 영역 높이
        self.roi_y = 350       # 관심 영역 시작 Y 좌표
        
        # 모터 속도 설정
        self.base_speed = 40   # 기본 속도
        self.max_turn_speed = 30  # 최대 회전 속도
        
        # 라인 검출 임계값
        self.line_threshold = 50  # 이진화 임계값
        self.min_line_area = 500  # 최소 라인 면적
        
        # 상태 변수
        self.line_detected = False
        self.center_x = self.frame_width // 2
        self.running = True
        
        print("🤖 패스파인더 라인 트레이싱 시작!")
        print("ESC 키를 눌러 종료")
    
    def preprocess_frame(self, frame):
        """프레임 전처리 - 라인 검출을 위한 이진화"""
        # 관심 영역(ROI) 추출
        roi = frame[self.roi_y:self.roi_y + self.roi_height, :]
        
        # 그레이스케일 변환
        gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        
        # 가우시안 블러로 노이즈 제거
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 이진화 (검은 선 검출)
        _, binary = cv2.threshold(blurred, self.line_threshold, 255, cv2.THRESH_BINARY_INV)
        
        return binary, roi
    
    def find_line_center(self, binary_image):
        """이진화된 이미지에서 라인의 중심점 찾기"""
        # 윤곽선 검출
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None, []
        
        # 가장 큰 윤곽선 찾기 (라인으로 가정)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # 면적이 너무 작으면 무시
        if cv2.contourArea(largest_contour) < self.min_line_area:
            return None, contours
        
        # 모멘트를 이용해 중심점 계산
        M = cv2.moments(largest_contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            return (cx, cy), contours
        
        return None, contours
    
    def calculate_steering(self, line_center):
        """라인 중심점을 기반으로 조향 계산"""
        if line_center is None:
            return 0
        
        # 화면 중심과 라인 중심의 차이 계산
        error = line_center[0] - (self.frame_width // 2)
        
        # PID 제어로 조향 값 계산
        steering = self.pid.update(error)
        
        # 조향 값 제한
        steering = max(-self.max_turn_speed, min(self.max_turn_speed, steering))
        
        return steering
    
    def control_motors(self, steering):
        """모터 제어"""
        if not self.line_detected:
            # 라인이 없으면 정지
            self.motor.stop_motors()
            return
        
        # 좌우 모터 속도 계산
        left_speed = self.base_speed - steering
        right_speed = self.base_speed + steering
        
        # 속도 제한 (0-100)
        left_speed = max(0, min(100, left_speed))
        right_speed = max(0, min(100, right_speed))
        
        # 모터 제어
        self.motor.set_individual_speeds(int(right_speed), int(left_speed))
    
    def draw_debug_info(self, frame, binary, line_center, steering, contours):
        """디버그 정보 화면에 표시"""
        # ROI 영역 표시
        cv2.rectangle(frame, (0, self.roi_y), (self.frame_width, self.roi_y + self.roi_height), (0, 255, 0), 2)
        
        # 중심선 표시
        center_x = self.frame_width // 2
        cv2.line(frame, (center_x, 0), (center_x, self.frame_height), (255, 255, 255), 2)
        
        # 라인 중심점 표시
        if line_center:
            # ROI 좌표를 전체 프레임 좌표로 변환
            actual_x = line_center[0]
            actual_y = line_center[1] + self.roi_y
            cv2.circle(frame, (actual_x, actual_y), 10, (0, 0, 255), -1)
            
            # 에러 라인 표시
            cv2.line(frame, (center_x, actual_y), (actual_x, actual_y), (255, 0, 0), 3)
        
        # 윤곽선 표시 (ROI 영역에)
        if contours:
            roi_contours = []
            for contour in contours:
                # ROI 좌표를 전체 프레임 좌표로 변환
                adjusted_contour = contour.copy()
                adjusted_contour[:, :, 1] += self.roi_y
                roi_contours.append(adjusted_contour)
            cv2.drawContours(frame, roi_contours, -1, (0, 255, 255), 2)
        
        # 이진화 이미지를 작은 창으로 표시
        binary_colored = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
        binary_resized = cv2.resize(binary_colored, (200, 100))
        frame[10:110, 10:210] = binary_resized
        cv2.rectangle(frame, (10, 10), (210, 110), (255, 255, 255), 2)
        
        # 텍스트 정보 표시
        info_y = 130
        cv2.putText(frame, f"Line Detected: {self.line_detected}", (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Steering: {steering:.2f}", (10, info_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Base Speed: {self.base_speed}", (10, info_y + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # PID 파라미터 표시
        cv2.putText(frame, f"PID: P={self.pid.kp} I={self.pid.ki} D={self.pid.kd}", (10, info_y + 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        return frame
    
    def run(self):
        """메인 실행 루프"""
        try:
            while self.running:
                # 프레임 캡처
                frame = self.picam2.capture_array()
                
                # 프레임 전처리
                binary, roi = self.preprocess_frame(frame)
                
                # 라인 중심점 찾기
                line_center, contours = self.find_line_center(binary)
                
                # 라인 검출 상태 업데이트
                self.line_detected = line_center is not None
                
                # 조향 계산
                steering = self.calculate_steering(line_center)
                
                # 모터 제어
                self.control_motors(steering)
                
                # 디버그 정보 표시
                debug_frame = self.draw_debug_info(frame, binary, line_center, steering, contours)
                
                # 화면 표시
                cv2.imshow('Line Tracing', debug_frame)
                
                # 키 입력 처리
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC 키
                    break
                elif key == ord('r'):  # R 키로 PID 리셋
                    self.pid.reset()
                    print("PID 제어기 리셋")
                elif key == ord('+'):  # 속도 증가
                    self.base_speed = min(80, self.base_speed + 5)
                    print(f"속도 증가: {self.base_speed}")
                elif key == ord('-'):  # 속도 감소
                    self.base_speed = max(20, self.base_speed - 5)
                    print(f"속도 감소: {self.base_speed}")
        
        except KeyboardInterrupt:
            print("\n사용자에 의해 중단됨")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """리소스 정리"""
        print("라인 트레이싱 종료 중...")
        self.motor.stop_motors()
        self.motor.cleanup()
        cv2.destroyAllWindows()
        self.picam2.stop()
        print("정리 완료!")

# 사용 예제
if __name__ == "__main__":
    print("🤖 패스파인더 라인 트레이싱 시작!")
    print("=" * 50)
    print("조작법:")
    print("ESC: 종료")
    print("R: PID 리셋")
    print("+: 속도 증가")
    print("-: 속도 감소")
    print("=" * 50)
    
    # 라인 트레이서 생성 및 실행
    tracer = LineTracer()
    tracer.run() 