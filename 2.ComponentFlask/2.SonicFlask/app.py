#!/usr/bin/env python3
"""
Pathfinder Ultrasonic Sensor Flask Application (Polling Version)
폴링 방식 초음파 센서 측정 및 데이터 시각화 시스템
"""

from flask import Flask, render_template, jsonify
import time
import json
from datetime import datetime
from collections import deque
import statistics
import random

# GPIO 모듈 가용성 확인
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
    print("🔧 RPi.GPIO 모듈 로드됨")
except ImportError:
    GPIO_AVAILABLE = False
    print("⚠️ RPi.GPIO 모듈 없음 - 시뮬레이션 모드로 실행")

# Flask 앱 설정
app = Flask(__name__)

# 초음파 센서 설정
TRIG = 5  # GPIO5 → 초음파 송신
ECHO = 6  # GPIO6 → 초음파 수신

# 상수 정의
SOUND_SPEED = 34300  # 음속 (cm/s)
TRIGGER_PULSE = 0.00001  # 10µs 트리거 펄스
TIMEOUT = 0.1  # 타임아웃 (100ms)

# 데이터 저장용 변수
measurement_data = deque(maxlen=50)  # 최근 50개 측정값
measurement_count = 0

# 통계 데이터
stats = {
    'min_distance': None,
    'max_distance': None,
    'avg_distance': None,
    'total_measurements': 0,
    'error_count': 0
}

def setup_gpio():
    """GPIO 초기 설정"""
    if GPIO_AVAILABLE:
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(TRIG, GPIO.OUT)
            GPIO.setup(ECHO, GPIO.IN)
            GPIO.output(TRIG, False)
            print("🔧 GPIO 설정 완료")
            return True
        except Exception as e:
            print(f"❌ GPIO 설정 실패: {e}")
            return False
    else:
        print("🔧 시뮬레이션 모드 - GPIO 설정 건너뜀")
        return True

def get_distance():
    """초음파 센서로 거리 측정"""
    if not GPIO_AVAILABLE:
        # 시뮬레이션 모드: 랜덤 거리 생성
        if random.random() < 0.05:  # 5% 확률로 측정 실패
            return None
        return round(random.uniform(5.0, 200.0), 1)
    
    try:
        # TRIG 신호 발생
        GPIO.output(TRIG, True)
        time.sleep(TRIGGER_PULSE)
        GPIO.output(TRIG, False)

        # ECHO 신호 대기 (타임아웃 적용)
        start_time = time.time()
        timeout_start = start_time
        
        # ECHO 신호 시작 대기
        while GPIO.input(ECHO) == 0:
            start_time = time.time()
            if start_time - timeout_start > TIMEOUT:
                return None  # 타임아웃 발생
        
        # ECHO 신호 종료 대기
        while GPIO.input(ECHO) == 1:
            end_time = time.time()
            if end_time - start_time > TIMEOUT:
                return None  # 타임아웃 발생

        # 거리 계산 (음속 * 시간 / 2)
        duration = end_time - start_time
        distance = (duration * SOUND_SPEED) / 2

        # 유효 범위 체크 (2cm ~ 400cm)
        if 2 <= distance <= 400:
            return round(distance, 1)
        return None
        
    except Exception as e:
        print(f"거리 측정 오류: {e}")
        return None

def update_statistics(distance):
    """통계 데이터 업데이트"""
    global stats
    
    if distance is not None:
        stats['total_measurements'] += 1
        
        # 최소/최대값 업데이트
        if stats['min_distance'] is None or distance < stats['min_distance']:
            stats['min_distance'] = distance
        if stats['max_distance'] is None or distance > stats['max_distance']:
            stats['max_distance'] = distance
        
        # 평균값 계산 (최근 측정값들 기준)
        valid_distances = [d['distance'] for d in measurement_data if d['distance'] is not None]
        if valid_distances:
            stats['avg_distance'] = round(statistics.mean(valid_distances), 1)
    else:
        stats['error_count'] += 1

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/api/distance')
def get_distance_api():
    """거리 측정 API (폴링용)"""
    global measurement_count
    
    try:
        # 거리 측정
        distance = get_distance()
        timestamp = datetime.now().strftime('%H:%M:%S')
        measurement_count += 1
        
        # 데이터 저장
        measurement_data.append({
            'timestamp': timestamp,
            'distance': distance,
            'datetime': datetime.now().isoformat(),
            'count': measurement_count
        })
        
        # 통계 업데이트
        update_statistics(distance)
        
        # 응답 데이터 구성
        response_data = {
            'success': True,
            'distance': distance,
            'timestamp': timestamp,
            'count': measurement_count,
            'stats': stats.copy(),
            'chart_data': list(measurement_data)[-20:]  # 최근 20개 데이터
        }
        
        print(f"📏 측정 #{measurement_count}: {distance} cm")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ 측정 오류: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })

@app.route('/api/stats')
def get_stats():
    """통계 데이터 API"""
    return jsonify({
        'success': True,
        'stats': stats.copy(),
        'data_count': len(measurement_data),
        'recent_data': list(measurement_data)[-10:]  # 최근 10개
    })

@app.route('/api/history')
def get_history():
    """전체 측정 기록 API"""
    return jsonify({
        'success': True,
        'data': list(measurement_data),
        'total_count': len(measurement_data)
    })

@app.route('/api/clear')
def clear_data():
    """데이터 초기화 API"""
    global stats, measurement_count
    
    measurement_data.clear()
    measurement_count = 0
    stats = {
        'min_distance': None,
        'max_distance': None,
        'avg_distance': None,
        'total_measurements': 0,
        'error_count': 0
    }
    
    print("🧹 데이터 초기화")
    return jsonify({
        'success': True,
        'message': '데이터가 초기화되었습니다.',
        'timestamp': datetime.now().strftime('%H:%M:%S')
    })

@app.route('/api/test')
def test_sensor():
    """센서 테스트 API"""
    try:
        # 5회 연속 측정
        test_results = []
        for i in range(5):
            distance = get_distance()
            test_results.append(distance)
            print(f"테스트 {i+1}: {distance} cm")
            time.sleep(0.2)
        
        # 테스트 결과 분석
        valid_results = [d for d in test_results if d is not None]
        success_rate = len(valid_results) / len(test_results) * 100
        
        return jsonify({
            'success': True,
            'test_results': test_results,
            'success_rate': success_rate,
            'avg_distance': round(statistics.mean(valid_results), 1) if valid_results else None,
            'message': f'센서 테스트 완료 (성공률: {success_rate:.0f}%)'
        })
        
    except Exception as e:
        print(f"❌ 센서 테스트 오류: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '센서 테스트 실패'
        })

def cleanup():
    """정리 작업"""
    if GPIO_AVAILABLE:
        try:
            GPIO.cleanup()
            print("🧹 GPIO 정리 완료")
        except:
            pass

if __name__ == '__main__':
    try:
        if setup_gpio():
            print("🚀 패스파인더 초음파 센서 서버 시작 (폴링 모드)")
            print("📡 HTTP 폴링 방식 거리 측정 시스템")
            if GPIO_AVAILABLE:
                print("🔧 하드웨어 모드: 실제 센서 사용")
            else:
                print("🎮 시뮬레이션 모드: 가상 데이터 생성")
            import subprocess
            ip = subprocess.check_output(['hostname', '-I'], shell=False).decode().split()[0]
            print(f"🌐 브라우저에서 http://{ip}:5000 으로 접속하세요")
            print("-" * 50)
            
            app.run(host='0.0.0.0', port=5000, debug=True)
        else:
            print("❌ GPIO 설정 실패로 서버를 시작할 수 없습니다")
        
    except KeyboardInterrupt:
        print("\n⏹️ 서버 종료 중...")
    except Exception as e:
        print(f"❌ 서버 오류: {e}")
    finally:
        cleanup()
