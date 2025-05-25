"""
pathfinder_qlearning.py - 패스파인더 키트용 Q-Learning 자율주행
초음파 센서를 이용한 장애물 회피 학습
"""

import time
import random
import numpy as np
import json
import os
from typing import List, Dict, Tuple, Optional
import sys
from pathlib import Path

# 모터 컨트롤러와 초음파 센서 import
sys.path.append(str(Path(__file__).parent.parent))
from MotorClassTest.Motor import MotorController
from ComponentClass._2.UltrasonicClass.Ultrasonic import UltrasonicSensor

class PathfinderQLearning:
    """패스파인더 키트용 Q-Learning 에이전트"""
    
    def __init__(self, config: Optional[dict] = None):
        """
        Q-Learning 에이전트 초기화
        
        Args:
            config: 설정 딕셔너리 (선택사항)
        """
        # 하드웨어 초기화
        self.motor = MotorController()
        self.ultrasonic = UltrasonicSensor()
        
        # 설정 로드
        self.config = self._load_config(config)
        
        # Q-Learning 변수
        self.q_table: Dict[str, List[float]] = {}
        self.current_state = ""
        self.last_action = 0
        self.episode = 0
        self.steps = 0
        self.total_reward = 0
        self.running = False
        
        # 통계 변수
        self.episode_rewards = []
        self.episode_steps = []
        
        # 모델 저장 디렉토리 생성
        os.makedirs(self.config['models_dir'], exist_ok=True)
        
        print("🤖 패스파인더 Q-Learning 에이전트 초기화 완료!")
        print(f"액션 수: {len(self.config['actions'])}")
        print(f"상태 공간: {self.config['sensor_bins']} bins")
    
    def _load_config(self, config: Optional[dict]) -> dict:
        """설정 로드 및 검증"""
        default_config = {
            # Q-Learning 파라미터
            'learning_rate': 0.1,        # 학습률 (alpha)
            'discount_factor': 0.95,     # 할인 인수 (gamma)
            'exploration_rate': 1.0,     # 초기 탐험률 (epsilon)
            'exploration_min': 0.01,     # 최소 탐험률
            'exploration_decay': 0.995,  # 탐험률 감소율
            
            # 환경 설정
            'sensor_max': 100,           # 최대 센서 값 (cm)
            'sensor_bins': 5,            # 센서 값 구간 수
            'safe_distance': 20,         # 안전 거리 (cm)
            'warning_distance': 30,      # 경고 거리 (cm)
            'good_distance': 50,         # 좋은 거리 (cm)
            
            # 모터 설정
            'base_speed': 40,            # 기본 속도
            'turn_speed': 60,            # 회전 속도
            'slow_speed': 25,            # 느린 속도
            
            # 액션 정의 (left_speed, right_speed)
            'actions': [
                (40, 40),    # 0: 직진
                (25, 40),    # 1: 약간 좌회전
                (40, 25),    # 2: 약간 우회전
                (0, 60),     # 3: 강한 좌회전
                (60, 0),     # 4: 강한 우회전
                (-30, 30),   # 5: 제자리 우회전
                (30, -30),   # 6: 제자리 좌회전
                (0, 0),      # 7: 정지
            ],
            
            # 보상 설정
            'rewards': {
                'collision': -100,       # 충돌 (매우 가까움)
                'danger': -10,           # 위험 (가까움)
                'warning': -2,           # 경고 (조금 가까움)
                'normal': 1,             # 정상 (적당한 거리)
                'good': 5,               # 좋음 (충분한 거리)
                'step_penalty': -0.1,    # 스텝 페널티
            },
            
            # 파일 설정
            'models_dir': '6.QLearning/models',
            'model_prefix': 'pathfinder_qtable_',
            'save_interval': 50,         # 모델 저장 간격
        }
        
        if config:
            default_config.update(config)
        
        return default_config
    
    def get_distance(self) -> float:
        """초음파 센서로 거리 측정"""
        try:
            distance = self.ultrasonic.get_distance()
            # 센서 값 제한
            return min(distance, self.config['sensor_max'])
        except Exception as e:
            print(f"센서 읽기 오류: {e}")
            return self.config['sensor_max']  # 안전한 기본값
    
    def discretize_distance(self, distance: float) -> int:
        """거리를 이산화된 상태로 변환"""
        if distance <= 0:
            return 0
        elif distance >= self.config['sensor_max']:
            return self.config['sensor_bins'] - 1
        else:
            # 거리를 구간으로 나누기
            bin_size = self.config['sensor_max'] / self.config['sensor_bins']
            return min(int(distance / bin_size), self.config['sensor_bins'] - 1)
    
    def get_state(self) -> str:
        """현재 상태 가져오기"""
        distance = self.get_distance()
        distance_bin = self.discretize_distance(distance)
        
        # 상태를 문자열로 표현
        state = f"d{distance_bin}"
        return state
    
    def choose_action(self, state: str) -> int:
        """ε-greedy 정책으로 액션 선택"""
        # 상태가 Q-table에 없으면 초기화
        if state not in self.q_table:
            self.q_table[state] = [0.0] * len(self.config['actions'])
        
        # 탐험 vs 활용
        if random.random() < self.config['exploration_rate']:
            # 탐험: 랜덤 액션
            return random.randint(0, len(self.config['actions']) - 1)
        else:
            # 활용: 최고 Q값 액션
            return int(np.argmax(self.q_table[state]))
    
    def execute_action(self, action_idx: int) -> None:
        """액션 실행"""
        left_speed, right_speed = self.config['actions'][action_idx]
        
        try:
            if left_speed == 0 and right_speed == 0:
                self.motor.stop_motors()
            else:
                self.motor.set_individual_speeds(abs(right_speed), abs(left_speed))
                
                # 후진이 필요한 경우 방향 설정
                if left_speed < 0 and right_speed < 0:
                    self.motor.set_motor_direction("left", "backward")
                    self.motor.set_motor_direction("right", "backward")
                elif left_speed < 0:
                    self.motor.set_motor_direction("left", "backward")
                    self.motor.set_motor_direction("right", "forward")
                elif right_speed < 0:
                    self.motor.set_motor_direction("left", "forward")
                    self.motor.set_motor_direction("right", "backward")
                else:
                    self.motor.set_motor_direction("left", "forward")
                    self.motor.set_motor_direction("right", "forward")
                    
        except Exception as e:
            print(f"액션 실행 오류: {e}")
            self.motor.stop_motors()
    
    def get_reward(self, distance: float, action_idx: int) -> float:
        """보상 계산"""
        rewards = self.config['rewards']
        
        # 거리 기반 보상
        if distance < 10:  # 충돌 위험
            return rewards['collision']
        elif distance < self.config['safe_distance']:  # 위험
            return rewards['danger']
        elif distance < self.config['warning_distance']:  # 경고
            return rewards['warning']
        elif distance > self.config['good_distance']:  # 좋음
            return rewards['good']
        else:  # 정상
            return rewards['normal']
    
    def update_q_value(self, state: str, action: int, reward: float, next_state: str) -> None:
        """Q-value 업데이트 (Q-learning 공식)"""
        # 상태가 Q-table에 없으면 초기화
        if state not in self.q_table:
            self.q_table[state] = [0.0] * len(self.config['actions'])
        if next_state not in self.q_table:
            self.q_table[next_state] = [0.0] * len(self.config['actions'])
        
        # Q-learning 업데이트 공식
        # Q(s,a) = Q(s,a) + α[r + γ*max(Q(s',a')) - Q(s,a)]
        best_next_action = np.argmax(self.q_table[next_state])
        td_target = reward + self.config['discount_factor'] * self.q_table[next_state][best_next_action]
        td_error = td_target - self.q_table[state][action]
        self.q_table[state][action] += self.config['learning_rate'] * td_error
    
    def decay_exploration(self) -> None:
        """탐험률 감소"""
        self.config['exploration_rate'] = max(
            self.config['exploration_min'],
            self.config['exploration_rate'] * self.config['exploration_decay']
        )
    
    def train_episode(self, max_steps: int = 500) -> float:
        """한 에피소드 훈련"""
        self.episode += 1
        self.steps = 0
        episode_reward = 0
        
        print(f"\n🎯 에피소드 {self.episode} 시작")
        
        # 초기 상태
        self.current_state = self.get_state()
        
        for step in range(max_steps):
            if not self.running:
                break
            
            # 액션 선택 및 실행
            action = self.choose_action(self.current_state)
            self.execute_action(action)
            
            # 잠시 대기 (액션 실행 시간)
            time.sleep(0.2)
            
            # 다음 상태 및 보상 관찰
            distance = self.get_distance()
            next_state = self.get_state()
            reward = self.get_reward(distance, action)
            
            # Q-value 업데이트
            self.update_q_value(self.current_state, action, reward, next_state)
            
            # 통계 업데이트
            episode_reward += reward
            self.steps += 1
            
            # 진행 상황 출력
            if step % 20 == 0:
                action_name = self._get_action_name(action)
                print(f"  스텝 {step}: 거리={distance:.1f}cm, 액션={action_name}, "
                      f"보상={reward:.1f}, ε={self.config['exploration_rate']:.3f}")
            
            # 충돌 감지 (에피소드 종료)
            if distance < 10:
                print(f"  ⚠️ 충돌 위험! 에피소드 종료 (거리: {distance:.1f}cm)")
                break
            
            # 상태 업데이트
            self.current_state = next_state
        
        # 에피소드 종료
        self.motor.stop_motors()
        self.decay_exploration()
        
        # 통계 저장
        self.episode_rewards.append(episode_reward)
        self.episode_steps.append(self.steps)
        
        print(f"✅ 에피소드 {self.episode} 완료: 보상={episode_reward:.1f}, 스텝={self.steps}")
        
        return episode_reward
    
    def _get_action_name(self, action_idx: int) -> str:
        """액션 인덱스를 이름으로 변환"""
        action_names = [
            "직진", "약간좌", "약간우", "강한좌", "강한우", "제자리우", "제자리좌", "정지"
        ]
        return action_names[action_idx] if action_idx < len(action_names) else f"액션{action_idx}"
    
    def start_training(self, episodes: int = 1000) -> None:
        """훈련 시작"""
        print(f"🚀 Q-Learning 훈련 시작! ({episodes} 에피소드)")
        print("Ctrl+C로 중단 가능")
        
        self.running = True
        
        try:
            for episode in range(episodes):
                if not self.running:
                    break
                
                # 에피소드 훈련
                episode_reward = self.train_episode()
                
                # 주기적으로 모델 저장
                if episode % self.config['save_interval'] == 0:
                    self.save_model()
                
                # 통계 출력
                if episode % 10 == 0:
                    avg_reward = np.mean(self.episode_rewards[-10:])
                    avg_steps = np.mean(self.episode_steps[-10:])
                    print(f"\n📊 최근 10 에피소드 평균: 보상={avg_reward:.1f}, 스텝={avg_steps:.1f}")
                    print(f"Q-table 크기: {len(self.q_table)} 상태")
                
                # 에피소드 간 휴식
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n⏹️ 사용자에 의해 훈련 중단")
        
        finally:
            self.stop_training()
    
    def stop_training(self) -> None:
        """훈련 중단"""
        self.running = False
        self.motor.stop_motors()
        
        # 최종 모델 저장
        final_path = self.save_model("final_model.json")
        print(f"🎉 훈련 완료! 최종 모델 저장: {final_path}")
        
        # 통계 출력
        if self.episode_rewards:
            print(f"\n📈 훈련 통계:")
            print(f"  총 에피소드: {len(self.episode_rewards)}")
            print(f"  평균 보상: {np.mean(self.episode_rewards):.2f}")
            print(f"  최고 보상: {np.max(self.episode_rewards):.2f}")
            print(f"  평균 스텝: {np.mean(self.episode_steps):.1f}")
            print(f"  Q-table 크기: {len(self.q_table)} 상태")
    
    def save_model(self, filename: Optional[str] = None) -> str:
        """모델 저장"""
        if filename is None:
            filename = f"{self.config['model_prefix']}{self.episode:06d}.json"
        
        filepath = os.path.join(self.config['models_dir'], filename)
        
        # 저장할 데이터 준비
        data = {
            'q_table': {state: q_values for state, q_values in self.q_table.items()},
            'episode': self.episode,
            'config': self.config,
            'statistics': {
                'episode_rewards': self.episode_rewards,
                'episode_steps': self.episode_steps,
            },
            'timestamp': time.time()
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 모델 저장: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ 모델 저장 실패: {e}")
            return ""
    
    def load_model(self, filepath: str) -> bool:
        """모델 로드"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Q-table 로드
            self.q_table = data['q_table']
            
            # 설정 업데이트
            if 'config' in data:
                self.config.update(data['config'])
            
            # 통계 로드
            if 'statistics' in data:
                self.episode_rewards = data['statistics'].get('episode_rewards', [])
                self.episode_steps = data['statistics'].get('episode_steps', [])
            
            if 'episode' in data:
                self.episode = data['episode']
            
            print(f"📂 모델 로드 완료: {filepath}")
            print(f"  Q-table 크기: {len(self.q_table)} 상태")
            print(f"  에피소드: {self.episode}")
            return True
            
        except Exception as e:
            print(f"❌ 모델 로드 실패: {e}")
            return False
    
    def run_trained_model(self, max_steps: int = 1000) -> None:
        """훈련된 모델로 실행 (탐험 없이)"""
        print("🎮 훈련된 모델로 실행 시작!")
        print("Ctrl+C로 중단")
        
        # 탐험률을 0으로 설정 (순수 활용)
        original_exploration = self.config['exploration_rate']
        self.config['exploration_rate'] = 0.0
        
        try:
            step = 0
            while step < max_steps:
                # 현재 상태 가져오기
                state = self.get_state()
                distance = self.get_distance()
                
                # 최적 액션 선택
                action = self.choose_action(state)
                action_name = self._get_action_name(action)
                
                # 액션 실행
                self.execute_action(action)
                
                # 상태 출력
                if step % 10 == 0:
                    print(f"스텝 {step}: 거리={distance:.1f}cm, 액션={action_name}")
                
                # 충돌 감지
                if distance < 15:
                    print(f"⚠️ 장애물 감지! 거리: {distance:.1f}cm")
                
                step += 1
                time.sleep(0.2)
                
        except KeyboardInterrupt:
            print("\n⏹️ 실행 중단")
        
        finally:
            self.motor.stop_motors()
            self.config['exploration_rate'] = original_exploration
            print("🏁 실행 완료")
    
    def cleanup(self) -> None:
        """리소스 정리"""
        self.motor.stop_motors()
        self.motor.cleanup()
        print("🧹 리소스 정리 완료")


def main():
    """메인 함수"""
    print("🤖 패스파인더 Q-Learning 자율주행")
    print("=" * 50)
    
    # Q-Learning 에이전트 생성
    agent = PathfinderQLearning()
    
    try:
        while True:
            print("\n메뉴:")
            print("1. 새로운 훈련 시작")
            print("2. 기존 모델 로드 후 훈련 계속")
            print("3. 훈련된 모델로 실행")
            print("4. 종료")
            
            choice = input("선택하세요 (1-4): ").strip()
            
            if choice == '1':
                episodes = int(input("훈련할 에피소드 수 (기본 100): ") or "100")
                agent.start_training(episodes)
                
            elif choice == '2':
                model_path = input("모델 파일 경로: ").strip()
                if agent.load_model(model_path):
                    episodes = int(input("추가 훈련할 에피소드 수 (기본 100): ") or "100")
                    agent.start_training(episodes)
                
            elif choice == '3':
                model_path = input("모델 파일 경로 (기본: 6.QLearning/models/final_model.json): ").strip()
                if not model_path:
                    model_path = "6.QLearning/models/final_model.json"
                
                if agent.load_model(model_path):
                    max_steps = int(input("최대 실행 스텝 수 (기본 1000): ") or "1000")
                    agent.run_trained_model(max_steps)
                
            elif choice == '4':
                break
                
            else:
                print("잘못된 선택입니다.")
    
    except KeyboardInterrupt:
        print("\n프로그램 중단")
    
    finally:
        agent.cleanup()


if __name__ == "__main__":
    main() 