"""
config.py - 패스파인더 모터 컨트롤러 설정 파일
초심자를 위한 간단한 버전
"""

# GPIO 핀 설정 (실제 하드웨어 배치에 맞게)
RIGHT_MOTOR_IN1 = 23  # 오른쪽 모터 방향 1
RIGHT_MOTOR_IN2 = 24  # 오른쪽 모터 방향 2
LEFT_MOTOR_IN3 = 22   # 왼쪽 모터 방향 1
LEFT_MOTOR_IN4 = 27   # 왼쪽 모터 방향 2
RIGHT_MOTOR_ENA = 12  # 오른쪽 모터 PWM
LEFT_MOTOR_ENB = 13   # 왼쪽 모터 PWM

# 속도 설정
NORMAL_SPEED = 100    # 일반 이동 속도 (0-100)
TURN_SPEED = 80       # 회전 속도 (0-100)
DIAGONAL_SPEED = 60   # 대각선 이동 시 감속 비율 (0-100)

# PWM 설정
PWM_FREQUENCY = 1000  # PWM 주파수 (Hz)

# 디버그 설정
DEBUG = True          # 디버그 메시지 출력 여부

