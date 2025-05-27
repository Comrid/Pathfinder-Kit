#!/usr/bin/env python3
"""
test_camera.py - 카메라 연결 테스트 스크립트
Q-Learning 웹 인터페이스에서 카메라가 안 보일 때 사용
"""

import cv2
import time
import sys

def test_camera():
    """카메라 연결 및 기본 기능 테스트"""
    print("🔍 카메라 연결 테스트 시작...")
    
    # 카메라 장치 확인
    print("\n1. 카메라 장치 확인")
    for i in range(3):  # 0, 1, 2 번 장치 확인
        print(f"  장치 {i} 테스트 중...")
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                height, width = frame.shape[:2]
                print(f"  ✅ 장치 {i}: 연결됨 ({width}x{height})")
                cap.release()
                return i
            else:
                print(f"  ❌ 장치 {i}: 프레임 읽기 실패")
        else:
            print(f"  ❌ 장치 {i}: 연결 실패")
        cap.release()
    
    print("  ⚠️ 사용 가능한 카메라 장치를 찾을 수 없습니다.")
    return None

def test_camera_settings(device_id):
    """카메라 설정 테스트"""
    print(f"\n2. 카메라 {device_id} 설정 테스트")
    
    cap = cv2.VideoCapture(device_id)
    if not cap.isOpened():
        print("  ❌ 카메라 열기 실패")
        return False
    
    # 기본 설정 적용
    settings = [
        (cv2.CAP_PROP_FRAME_WIDTH, 320),
        (cv2.CAP_PROP_FRAME_HEIGHT, 240),
        (cv2.CAP_PROP_FPS, 30)
    ]
    
    for prop, value in settings:
        cap.set(prop, value)
        actual_value = cap.get(prop)
        print(f"  설정 {prop}: 요청={value}, 실제={actual_value}")
    
    # 프레임 캡처 테스트
    print("\n3. 프레임 캡처 테스트")
    success_count = 0
    for i in range(10):
        ret, frame = cap.read()
        if ret and frame is not None:
            success_count += 1
        time.sleep(0.1)
    
    print(f"  성공률: {success_count}/10 ({success_count*10}%)")
    
    cap.release()
    return success_count >= 7  # 70% 이상 성공

def test_opencv_version():
    """OpenCV 버전 확인"""
    print(f"\n4. OpenCV 정보")
    print(f"  버전: {cv2.__version__}")
    
    # 백엔드 정보
    backends = []
    for backend in [cv2.CAP_V4L2, cv2.CAP_GSTREAMER, cv2.CAP_FFMPEG]:
        try:
            cap = cv2.VideoCapture(0, backend)
            if cap.isOpened():
                backends.append(backend)
            cap.release()
        except:
            pass
    
    print(f"  사용 가능한 백엔드: {len(backends)}개")

def test_permissions():
    """권한 확인"""
    print(f"\n5. 권한 확인")
    
    import os
    import subprocess
    
    # 현재 사용자 확인
    user = os.getenv('USER', 'unknown')
    print(f"  현재 사용자: {user}")
    
    # video 그룹 확인
    try:
        result = subprocess.run(['groups'], capture_output=True, text=True)
        groups = result.stdout.strip()
        if 'video' in groups:
            print(f"  ✅ video 그룹 멤버십: 있음")
        else:
            print(f"  ⚠️ video 그룹 멤버십: 없음")
            print(f"    해결: sudo usermod -a -G video {user}")
    except:
        print(f"  ❓ 그룹 확인 실패")
    
    # 장치 파일 확인
    video_devices = [f"/dev/video{i}" for i in range(3)]
    for device in video_devices:
        if os.path.exists(device):
            stat = os.stat(device)
            print(f"  장치 {device}: 존재함 (권한: {oct(stat.st_mode)[-3:]})")
        else:
            print(f"  장치 {device}: 없음")

def main():
    """메인 함수"""
    print("🤖 패스파인더 카메라 진단 도구")
    print("=" * 50)
    
    try:
        # OpenCV 버전 확인
        test_opencv_version()
        
        # 권한 확인
        test_permissions()
        
        # 카메라 장치 찾기
        device_id = test_camera()
        
        if device_id is not None:
            # 카메라 설정 테스트
            if test_camera_settings(device_id):
                print(f"\n🎉 카메라 테스트 성공!")
                print(f"   사용할 장치: /dev/video{device_id}")
                print(f"   웹 인터페이스에서 '카메라 초기화' 버튼을 클릭하세요.")
            else:
                print(f"\n⚠️ 카메라 연결은 되지만 불안정합니다.")
                print(f"   해결 방법:")
                print(f"   1. 카메라 케이블 연결 확인")
                print(f"   2. 라즈베리파이 재부팅")
                print(f"   3. 다른 카메라 모듈 시도")
        else:
            print(f"\n❌ 카메라를 찾을 수 없습니다.")
            print(f"   해결 방법:")
            print(f"   1. 카메라 모듈이 제대로 연결되었는지 확인")
            print(f"   2. 'sudo raspi-config'에서 카메라 활성화")
            print(f"   3. 'lsusb' 명령으로 USB 카메라 확인")
            print(f"   4. 'dmesg | grep video' 명령으로 커널 메시지 확인")
    
    except KeyboardInterrupt:
        print(f"\n⏹️ 테스트 중단")
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
    
    print(f"\n테스트 완료!")

if __name__ == "__main__":
    main() 