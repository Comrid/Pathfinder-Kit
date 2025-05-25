#!/usr/bin/env python3
"""
import 테스트 스크립트
"""

import sys
from pathlib import Path

# 경로 추가
sys.path.append(str(Path(__file__).parent.parent))

print("경로 테스트 시작...")

try:
    print("1. MotorController import 테스트...")
    from MotorClassTest.Motor import MotorController
    print("   ✅ MotorController import 성공!")
except Exception as e:
    print(f"   ❌ MotorController import 실패: {e}")

try:
    print("2. UltrasonicSensor import 테스트...")
    from _2.ComponentClass._2.SonicClass.UltrasonicSensor import UltrasonicSensor
    print("   ✅ UltrasonicSensor import 성공!")
except Exception as e:
    print(f"   ❌ UltrasonicSensor import 실패: {e}")

try:
    print("3. pathfinder_qlearning import 테스트...")
    from pathfinder_qlearning import PathfinderQLearning
    print("   ✅ pathfinder_qlearning import 성공!")
except Exception as e:
    print(f"   ❌ pathfinder_qlearning import 실패: {e}")

print("테스트 완료!") 