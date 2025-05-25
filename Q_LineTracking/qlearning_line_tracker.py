"""
qlearning_line_tracker.py - Q-Learning 기반 라인 트레이싱
카메라를 이용한 라인 추적 학습 시스템
"""

import time
import random
import numpy as np
import json
import os
import cv2
from typing import List, Dict, Tuple, Optional
import sys
from pathlib import Path

# 모터 컨트롤러 import
sys.path.append(str(Path(__file__).parent.parent))
from MotorClassTest.Motor import MotorController

class LineTrackingQLearning:
    """Q-Learning 기반 라인 트레이싱 에이전트"""
    
    def __init__(self, config: Optional[dict] = None):
        """
        Q-Learning 라인 트레이싱 에이전트 초기화
        
        Args:
            config: 설정 딕셔너리 (선택사항)
        """
        # 하드웨어 초기화
        self.motor = MotorController()
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        
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
        
        # 라인 트레이싱 변수
        self.line_center = 160  # 화면 중앙 (320/2)
        self.last_line_position = self.line_center
        self.line_lost_count = 0
        
        # 모델 저장 디렉토리 생성
        os.makedirs(self.config['models_dir'], exist_ok=True)
        
        print("🤖 Q-Learning 라인 트레이싱 에이전트 초기화 완료!")
        print(f"액션 수: {len(self.config['actions'])}")
        print(f"상태 공간: {self.config['line_bins']} bins")
    
    def _load_config(self, config: Optional[dict]) -> dict:
        """설정 로드 및 검증"""
        default_config = {
            # Q-Learning 파라미터
            'learning_rate': 0.15,       # 학습률 (alpha)
            'discount_factor': 0.9,      # 할인 인수 (gamma)
            'exploration_rate': 1.0,     # 초기 탐험률 (epsilon)
            'exploration_min': 0.05,     # 최소 탐험률
            'exploration_decay': 0.998,  # 탐험률 감소율
            
            # 라인 트레이싱 설정
            'line_bins': 7,              # 라인 위치 구간 수
            'line_threshold': 50,        # 라인 검출 임계값
            'roi_height': 80,            # ROI 높이
            'roi_y_offset': 160,         # ROI Y 시작점
            'min_line_area': 100,        # 최소 라인 면적
            
            # 모터 설정
            'base_speed': 35,            # 기본 속도
            'turn_speed': 50,            # 회전 속도
            'slow_speed': 20,            # 느린 속도
            
            # 액션 정의 (left_speed, right_speed)
            'actions': [
                (35, 35),    # 0: 직진
                (20, 35),    # 1: 약간 좌회전
                (35, 20),    # 2: 약간 우회전
                (10, 50),    # 3: 강한 좌회전
                (50, 10),    # 4: 강한 우회전
                (0, 35),     # 5: 제자리 좌회전
                (35, 0),     # 6: 제자리 우회전
                (15, 15),    # 7: 느린 직진
            ],
            
            # 보상 설정
            'rewards': {
                'on_line': 10,           # 라인 위에 있을 때
                'near_line': 5,          # 라인 근처에 있을 때
                'off_line': -5,          # 라인에서 벗어났을 때
                'line_lost': -20,        # 라인을 완전히 놓쳤을 때
                'center_bonus': 15,      # 중앙에 있을 때 보너스
                'step_penalty': -0.5,    # 스텝 페널티
            },
            
            # 파일 설정
            'models_dir': 'Q_LineTracking/models',
            'model_prefix': 'line_qtable_',
            'save_interval': 25,         # 모델 저장 간격
        }
        
        if config:
            default_config.update(config)
        
        return default_config
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """카메라에서 프레임 캡처"""
        try:
            ret, frame = self.camera.read()
            if ret:
                return frame
            return None
        except Exception as e:
            print(f"카메라 캡처 오류: {e}")
            return None
    
    def process_frame(self, frame: np.ndarray) -> Tuple[int, bool]:
        """
        프레임 처리하여 라인 위치 검출
        
        Args:
            frame: 입력 프레임
            
        Returns:
            Tuple[int, bool]: (라인 위치, 라인 검출 여부)
        """
        try:
            # ROI 설정
            height, width = frame.shape[:2]
            roi_y = self.config['roi_y_offset']
            roi_height = self.config['roi_height']
            roi = frame[roi_y:roi_y + roi_height, :]
            
            # 그레이스케일 변환
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # 가우시안 블러
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # 이진화 (검은색 라인 검출)
            _, binary = cv2.threshold(blurred, self.config['line_threshold'], 255, cv2.THRESH_BINARY_INV)
            
            # 모폴로지 연산으로 노이즈 제거
            kernel = np.ones((3, 3), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            # 윤곽선 검출
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # 가장 큰 윤곽선 선택
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)
                
                if area > self.config['min_line_area']:
                    # 윤곽선의 중심점 계산
                    M = cv2.moments(largest_contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        self.last_line_position = cx
                        return cx, True
            
            # 라인을 찾지 못한 경우
            return self.last_line_position, False
            
        except Exception as e:
            print(f"프레임 처리 오류: {e}")
            return self.last_line_position, False
    
    def discretize_line_position(self, line_x: int, line_detected: bool) -> int:
        """라인 위치를 이산화된 상태로 변환"""
        if not line_detected:
            return self.config['line_bins']  # 라인 없음 상태
        
        # 화면을 구간으로 나누기
        width = 320  # 카메라 해상도
        bin_size = width / self.config['line_bins']
        
        bin_index = min(int(line_x / bin_size), self.config['line_bins'] - 1)
        return bin_index
    
    def get_state(self) -> str:
        """현재 상태 가져오기"""
        frame = self.capture_frame()
        if frame is None:
            return f"line{self.config['line_bins']}"  # 카메라 오류 상태
        
        line_x, line_detected = self.process_frame(frame)
        line_bin = self.discretize_line_position(line_x, line_detected)
        
        # 라인 손실 카운트 추가
        if not line_detected:
            self.line_lost_count += 1
        else:
            self.line_lost_count = 0
        
        # 상태를 문자열로 표현
        state = f"line{line_bin}"
        if self.line_lost_count > 5:
            state += "_lost"
        
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
            self.motor.set_individual_speeds(right_speed, left_speed)
        except Exception as e:
            print(f"액션 실행 오류: {e}")
            self.motor.stop_motors()
    
    def get_reward(self, line_x: int, line_detected: bool, action_idx: int) -> float:
        """보상 계산"""
        rewards = self.config['rewards']
        
        if not line_detected:
            return rewards['line_lost']
        
        # 라인 중앙으로부터의 거리 계산
        center_distance = abs(line_x - self.line_center)
        
        # 거리 기반 보상
        if center_distance < 20:  # 중앙 근처
            reward = rewards['center_bonus']
        elif center_distance < 50:  # 라인 위
            reward = rewards['on_line']
        elif center_distance < 80:  # 라인 근처
            reward = rewards['near_line']
        else:  # 라인에서 멀리
            reward = rewards['off_line']
        
        # 스텝 페널티 추가
        reward += rewards['step_penalty']
        
        return reward
    
    def update_q_value(self, state: str, action: int, reward: float, next_state: str) -> None:
        """Q-value 업데이트 (Q-learning 공식)"""
        # 상태가 Q-table에 없으면 초기화
        if state not in self.q_table:
            self.q_table[state] = [0.0] * len(self.config['actions'])
        if next_state not in self.q_table:
            self.q_table[next_state] = [0.0] * len(self.config['actions'])
        
        # Q-learning 업데이트 공식
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
    
    def train_episode(self, max_steps: int = 1000) -> float:
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
            time.sleep(0.1)
            
            # 다음 상태 및 보상 관찰
            frame = self.capture_frame()
            if frame is not None:
                line_x, line_detected = self.process_frame(frame)
                next_state = self.get_state()
                reward = self.get_reward(line_x, line_detected, action)
                
                # Q-value 업데이트
                self.update_q_value(self.current_state, action, reward, next_state)
                
                # 통계 업데이트
                episode_reward += reward
                self.steps += 1
                
                # 진행 상황 출력
                if step % 50 == 0:
                    action_name = self._get_action_name(action)
                    print(f"  스텝 {step}: 라인위치={line_x}, 검출={line_detected}, "
                          f"액션={action_name}, 보상={reward:.1f}, ε={self.config['exploration_rate']:.3f}")
                
                # 상태 업데이트
                self.current_state = next_state
            else:
                # 카메라 오류 시 에피소드 종료
                print("  ⚠️ 카메라 오류! 에피소드 종료")
                break
        
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
            "직진", "약간좌", "약간우", "강한좌", "강한우", "제자리좌", "제자리우", "느린직진"
        ]
        return action_names[action_idx] if action_idx < len(action_names) else f"액션{action_idx}"
    
    def start_training(self, episodes: int = 500) -> None:
        """훈련 시작"""
        print(f"🚀 Q-Learning 라인 트레이싱 훈련 시작! ({episodes} 에피소드)")
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
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n⏹️ 사용자에 의해 훈련 중단")
        
        finally:
            self.stop_training()
    
    def stop_training(self) -> None:
        """훈련 중단"""
        self.running = False
        self.motor.stop_motors()
        
        # 최종 모델 저장
        final_path = self.save_model("final_line_model.json")
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
    
    def run_trained_model(self, max_steps: int = 2000) -> None:
        """훈련된 모델로 실행 (탐험 없이)"""
        print("🎮 훈련된 모델로 라인 트레이싱 시작!")
        print("Ctrl+C로 중단")
        
        # 탐험률을 0으로 설정 (순수 활용)
        original_exploration = self.config['exploration_rate']
        self.config['exploration_rate'] = 0.0
        
        try:
            step = 0
            while step < max_steps:
                # 현재 상태 가져오기
                state = self.get_state()
                frame = self.capture_frame()
                
                if frame is not None:
                    line_x, line_detected = self.process_frame(frame)
                    
                    # 최적 액션 선택
                    action = self.choose_action(state)
                    action_name = self._get_action_name(action)
                    
                    # 액션 실행
                    self.execute_action(action)
                    
                    # 상태 출력
                    if step % 20 == 0:
                        print(f"스텝 {step}: 라인위치={line_x}, 검출={line_detected}, 액션={action_name}")
                    
                    step += 1
                    time.sleep(0.1)
                else:
                    print("카메라 오류!")
                    break
                
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
        if self.camera.isOpened():
            self.camera.release()
        print("🧹 리소스 정리 완료")


def main():
    """메인 함수"""
    print("🤖 Q-Learning 라인 트레이싱 시스템")
    print("=" * 50)
    
    # Q-Learning 에이전트 생성
    agent = LineTrackingQLearning()
    
    try:
        while True:
            print("\n메뉴:")
            print("1. 새로운 훈련 시작")
            print("2. 기존 모델 로드 후 훈련 계속")
            print("3. 훈련된 모델로 라인 트레이싱")
            print("4. 종료")
            
            choice = input("선택하세요 (1-4): ").strip()
            
            if choice == '1':
                episodes = int(input("훈련할 에피소드 수 (기본 200): ") or "200")
                agent.start_training(episodes)
                
            elif choice == '2':
                model_path = input("모델 파일 경로: ").strip()
                if agent.load_model(model_path):
                    episodes = int(input("추가 훈련할 에피소드 수 (기본 100): ") or "100")
                    agent.start_training(episodes)
                
            elif choice == '3':
                model_path = input("모델 파일 경로 (기본: Q_LineTracking/models/final_line_model.json): ").strip()
                if not model_path:
                    model_path = "Q_LineTracking/models/final_line_model.json"
                
                if agent.load_model(model_path):
                    max_steps = int(input("최대 실행 스텝 수 (기본 2000): ") or "2000")
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