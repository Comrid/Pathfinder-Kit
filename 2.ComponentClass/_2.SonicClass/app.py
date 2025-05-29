#!/usr/bin/env python3
"""
Pathfinder Ultrasonic Sensor Real-time Flask Application
실시간 초음파 센서 측정 및 데이터 시각화 시스템
"""

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import RPi.GPIO as GPIO
import time
import threading
import json
from datetime import datetime
from collections import deque
import statistics

# Flask 앱 설정
app = Flask(__name__)
app.config['SECRET_KEY'] = 'pathfinder_ultrasonic_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# 초음파 센서 설정
TRIG = 5  # GPIO5 → 초음파 송신
ECHO = 6  # GPIO6 → 초음파 수신

# 상수 정의
SOUND_SPEED = 34300  # 음속 (cm/s)
TRIGGER_PULSE = 0.00001  # 10µs 트리거 펄스
MEASUREMENT_INTERVAL = 0.1  # 측정 간격 (100ms)
TIMEOUT = 0.1  # 타임아웃 (100ms)

# 데이터 저장용 변수
measurement_data = deque(maxlen=100)  # 최근 100개 측정값
is_measuring = False
measurement_thread = None

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
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, False)
    print("🔧 GPIO 설정 완료")

def get_distance():
    """초음파 센서로 거리 측정"""
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

def measurement_worker():
    """백그라운드 측정 스레드"""
    global is_measuring
    
    print("📡 측정 스레드 시작")
    
    while is_measuring:
        try:
            # 거리 측정
            distance = get_distance()
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            
            # 데이터 저장
            measurement_data.append({
                'timestamp': timestamp,
                'distance': distance,
                'datetime': datetime.now().isoformat()
            })
            
            # 통계 업데이트
            update_statistics(distance)
            
            # 클라이언트에 실시간 데이터 전송
            socketio.emit('measurement_data', {
                'distance': distance,
                'timestamp': timestamp,
                'stats': stats.copy(),
                'chart_data': list(measurement_data)[-20:]  # 최근 20개 데이터
            })
            
            time.sleep(MEASUREMENT_INTERVAL)
            
        except Exception as e:
            print(f"측정 스레드 오류: {e}")
            socketio.emit('error_message', {'message': f'측정 오류: {str(e)}'})
            time.sleep(1)
    
    print("📡 측정 스레드 종료")

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결"""
    print(f"🔗 클라이언트 연결: {request.sid}")
    emit('connection_status', {'status': 'connected'})
    
    # 현재 상태 전송
    emit('measurement_status', {'is_measuring': is_measuring})
    if measurement_data:
        emit('measurement_data', {
            'distance': measurement_data[-1]['distance'] if measurement_data else None,
            'timestamp': measurement_data[-1]['timestamp'] if measurement_data else None,
            'stats': stats.copy(),
            'chart_data': list(measurement_data)[-20:]
        })

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제"""
    print(f"🔌 클라이언트 연결 해제: {request.sid}")

@socketio.on('start_measurement')
def handle_start_measurement():
    """측정 시작"""
    global is_measuring, measurement_thread
    
    if not is_measuring:
        is_measuring = True
        measurement_thread = threading.Thread(target=measurement_worker)
        measurement_thread.daemon = True
        measurement_thread.start()
        
        emit('measurement_status', {'is_measuring': True})
        emit('debug_message', {'message': '측정 시작됨'})
        print("▶️ 측정 시작")

@socketio.on('stop_measurement')
def handle_stop_measurement():
    """측정 중지"""
    global is_measuring
    
    if is_measuring:
        is_measuring = False
        emit('measurement_status', {'is_measuring': False})
        emit('debug_message', {'message': '측정 중지됨'})
        print("⏹️ 측정 중지")

@socketio.on('clear_data')
def handle_clear_data():
    """데이터 초기화"""
    global stats
    
    measurement_data.clear()
    stats = {
        'min_distance': None,
        'max_distance': None,
        'avg_distance': None,
        'total_measurements': 0,
        'error_count': 0
    }
    
    emit('measurement_data', {
        'distance': None,
        'timestamp': None,
        'stats': stats.copy(),
        'chart_data': []
    })
    emit('debug_message', {'message': '데이터 초기화됨'})
    print("🧹 데이터 초기화")

@socketio.on('get_history')
def handle_get_history():
    """전체 측정 기록 요청"""
    emit('history_data', {
        'data': list(measurement_data),
        'total_count': len(measurement_data)
    })

@socketio.on('test_sensor')
def handle_test_sensor():
    """센서 테스트"""
    emit('debug_message', {'message': '센서 테스트 시작...'})
    
    try:
        # 5회 연속 측정
        test_results = []
        for i in range(5):
            distance = get_distance()
            test_results.append(distance)
            time.sleep(0.2)
        
        # 테스트 결과 분석
        valid_results = [d for d in test_results if d is not None]
        success_rate = len(valid_results) / len(test_results) * 100
        
        emit('test_result', {
            'results': test_results,
            'success_rate': success_rate,
            'avg_distance': round(statistics.mean(valid_results), 1) if valid_results else None
        })
        
        if success_rate >= 80:
            emit('debug_message', {'message': f'✅ 센서 테스트 성공 (성공률: {success_rate:.0f}%)'})
        else:
            emit('debug_message', {'message': f'⚠️ 센서 테스트 불안정 (성공률: {success_rate:.0f}%)'})
            
    except Exception as e:
        emit('debug_message', {'message': f'❌ 센서 테스트 실패: {str(e)}'})

def cleanup():
    """정리 작업"""
    global is_measuring
    is_measuring = False
    try:
        GPIO.cleanup()
        print("🧹 GPIO 정리 완료")
    except:
        pass

if __name__ == '__main__':
    try:
        setup_gpio()
        print("🚀 패스파인더 초음파 센서 서버 시작")
        print("📡 실시간 거리 측정 및 데이터 시각화 시스템")
        print("🌐 웹 브라우저에서 http://라즈베리파이IP:5000 접속")
        print("-" * 50)
        
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\n⏹️ 서버 종료 중...")
    except Exception as e:
        print(f"❌ 서버 오류: {e}")
    finally:
        cleanup() 