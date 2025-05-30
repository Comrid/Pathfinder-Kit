#!/usr/bin/env python3
"""
🧪 Q-Learning LineTracing System Test Script
패스파인더 키트 Q-Learning 시스템 기본 기능 테스트

이 스크립트는 하드웨어 없이도 Q-Learning 알고리즘의 
기본 동작을 테스트할 수 있습니다.
"""

import numpy as np
import json
import time
from datetime import datetime

# 메인 애플리케이션에서 클래스 임포트
try:
    from app import QLearningConfig, QLearningAgent
    print("✅ 메인 모듈 임포트 성공")
except ImportError as e:
    print(f"❌ 메인 모듈 임포트 실패: {e}")
    exit(1)

def test_qlearning_config():
    """Q-Learning 설정 테스트"""
    print("\n🔧 Q-Learning 설정 테스트")
    print("-" * 40)
    
    config = QLearningConfig()
    
    # 기본 파라미터 확인
    assert config.learning_rate == 0.1, "학습률 오류"
    assert config.discount_factor == 0.95, "할인인수 오류"
    assert config.epsilon == 0.3, "탐험률 오류"
    assert config.num_states == 7, "상태 수 오류"
    assert config.num_actions == 5, "행동 수 오류"
    
    print(f"✅ 학습률: {config.learning_rate}")
    print(f"✅ 할인인수: {config.discount_factor}")
    print(f"✅ 탐험률: {config.epsilon}")
    print(f"✅ 상태 수: {config.num_states}")
    print(f"✅ 행동 수: {config.num_actions}")
    print(f"✅ 기본 속도: {config.base_speed}")
    print(f"✅ 회전 속도: {config.turn_speed}")

def test_qlearning_agent():
    """Q-Learning 에이전트 테스트"""
    print("\n🤖 Q-Learning 에이전트 테스트")
    print("-" * 40)
    
    config = QLearningConfig()
    agent = QLearningAgent(config)
    
    # Q-테이블 초기화 확인
    assert agent.q_table.shape == (7, 5), "Q-테이블 크기 오류"
    assert np.all(agent.q_table == 0), "Q-테이블 초기화 오류"
    
    print(f"✅ Q-테이블 크기: {agent.q_table.shape}")
    print(f"✅ Q-테이블 초기값: 모두 0")
    print(f"✅ 초기 에피소드: {agent.episode}")
    print(f"✅ 초기 총 스텝: {agent.total_steps}")

def test_state_conversion():
    """상태 변환 테스트"""
    print("\n🎯 상태 변환 테스트")
    print("-" * 40)
    
    config = QLearningConfig()
    agent = QLearningAgent(config)
    
    frame_width = 640
    test_cases = [
        (None, 3),      # 라인 없음 → 중앙 상태
        (0, 0),         # 왼쪽 끝
        (91, 1),        # 왼쪽
        (182, 2),       # 약간 왼쪽
        (320, 3),       # 중앙
        (457, 4),       # 약간 오른쪽
        (548, 5),       # 오른쪽
        (639, 6),       # 오른쪽 끝
    ]
    
    for line_x, expected_state in test_cases:
        state = agent.get_state_from_line_position(line_x, frame_width)
        assert state == expected_state, f"상태 변환 오류: {line_x} → {state} (예상: {expected_state})"
        print(f"✅ 라인 위치 {line_x} → 상태 {state}")

def test_action_selection():
    """행동 선택 테스트"""
    print("\n🎮 행동 선택 테스트")
    print("-" * 40)
    
    config = QLearningConfig()
    agent = QLearningAgent(config)
    
    # 탐험 모드 테스트 (랜덤 행동)
    actions_exploration = []
    for _ in range(100):
        action = agent.choose_action(3, training=True)  # 중앙 상태
        actions_exploration.append(action)
        assert 0 <= action <= 4, f"잘못된 행동: {action}"
    
    unique_actions = len(set(actions_exploration))
    print(f"✅ 탐험 모드: {unique_actions}개 서로 다른 행동 선택")
    
    # Q값 설정 후 활용 모드 테스트
    agent.q_table[3, 2] = 10.0  # 중앙 상태에서 직진 행동에 높은 Q값
    
    actions_exploitation = []
    for _ in range(10):
        action = agent.choose_action(3, training=False)  # 활용 모드
        actions_exploitation.append(action)
    
    # 모든 행동이 직진(2)이어야 함
    assert all(action == 2 for action in actions_exploitation), "활용 모드 오류"
    print(f"✅ 활용 모드: 최적 행동(직진) 일관성 있게 선택")

def test_q_table_update():
    """Q-테이블 업데이트 테스트"""
    print("\n📊 Q-테이블 업데이트 테스트")
    print("-" * 40)
    
    config = QLearningConfig()
    agent = QLearningAgent(config)
    
    # 초기 Q값
    initial_q = agent.q_table[3, 2]  # 중앙 상태, 직진 행동
    print(f"✅ 초기 Q값: {initial_q}")
    
    # Q-테이블 업데이트
    state, action, reward, next_state = 3, 2, 15, 3
    agent.update_q_table(state, action, reward, next_state)
    
    # 업데이트된 Q값
    updated_q = agent.q_table[3, 2]
    expected_q = initial_q + config.learning_rate * (reward + config.discount_factor * 0 - initial_q)
    
    assert abs(updated_q - expected_q) < 1e-6, f"Q값 업데이트 오류: {updated_q} != {expected_q}"
    print(f"✅ 업데이트된 Q값: {updated_q:.3f}")
    print(f"✅ 예상 Q값: {expected_q:.3f}")

def test_reward_calculation():
    """보상 계산 테스트"""
    print("\n🏆 보상 계산 테스트")
    print("-" * 40)
    
    config = QLearningConfig()
    agent = QLearningAgent(config)
    
    test_cases = [
        (3, True, config.reward_center),     # 중앙, 라인 검출됨
        (2, True, config.reward_on_line),    # 약간 왼쪽, 라인 검출됨
        (4, True, config.reward_on_line),    # 약간 오른쪽, 라인 검출됨
        (1, True, config.reward_on_line),    # 왼쪽, 라인 검출됨
        (5, True, config.reward_on_line),    # 오른쪽, 라인 검출됨
        (0, True, config.reward_on_line - 3), # 왼쪽 끝, 라인 검출됨
        (6, True, config.reward_on_line - 3), # 오른쪽 끝, 라인 검출됨
        (3, False, config.reward_off_line),  # 중앙, 라인 검출 안됨
    ]
    
    for state, line_detected, expected_reward in test_cases:
        reward = agent.calculate_reward(state, line_detected)
        assert reward == expected_reward, f"보상 계산 오류: 상태{state}, 검출{line_detected} → {reward} (예상: {expected_reward})"
        print(f"✅ 상태 {state}, 라인 검출 {line_detected} → 보상 {reward}")

def test_model_save_load():
    """모델 저장/로드 테스트"""
    print("\n💾 모델 저장/로드 테스트")
    print("-" * 40)
    
    config = QLearningConfig()
    agent1 = QLearningAgent(config)
    
    # 임의의 Q값 설정
    agent1.q_table[3, 2] = 10.5
    agent1.episode = 42
    agent1.total_steps = 1000
    agent1.successful_episodes = 20
    agent1.episode_rewards = [100, 150, 200]
    
    # 모델 저장
    test_filename = "test_model.json"
    agent1.save_model(test_filename)
    print(f"✅ 모델 저장: {test_filename}")
    
    # 새 에이전트로 모델 로드
    agent2 = QLearningAgent(config)
    success = agent2.load_model(test_filename)
    
    assert success, "모델 로드 실패"
    assert agent2.q_table[3, 2] == 10.5, "Q값 로드 오류"
    assert agent2.episode == 42, "에피소드 로드 오류"
    assert agent2.total_steps == 1000, "총 스텝 로드 오류"
    assert agent2.successful_episodes == 20, "성공 에피소드 로드 오류"
    assert agent2.episode_rewards == [100, 150, 200], "에피소드 보상 로드 오류"
    
    print(f"✅ 모델 로드 성공")
    print(f"✅ Q값 복원: {agent2.q_table[3, 2]}")
    print(f"✅ 에피소드 복원: {agent2.episode}")
    print(f"✅ 총 스텝 복원: {agent2.total_steps}")
    
    # 테스트 파일 정리
    import os
    try:
        os.remove(test_filename)
        print(f"✅ 테스트 파일 정리: {test_filename}")
    except:
        pass

def test_episode_management():
    """에피소드 관리 테스트"""
    print("\n📈 에피소드 관리 테스트")
    print("-" * 40)
    
    config = QLearningConfig()
    agent = QLearningAgent(config)
    
    # 초기 상태
    initial_episode = agent.episode
    initial_epsilon = agent.config.epsilon
    
    # 보상 설정
    agent.total_reward = 150
    
    # 에피소드 종료
    agent.end_episode()
    
    # 검증
    assert agent.episode == initial_episode + 1, "에피소드 증가 오류"
    assert agent.total_reward == 0, "보상 초기화 오류"
    assert len(agent.episode_rewards) == 1, "에피소드 보상 기록 오류"
    assert agent.episode_rewards[0] == 150, "에피소드 보상 값 오류"
    assert agent.config.epsilon < initial_epsilon, "탐험률 감소 오류"
    assert agent.successful_episodes == 1, "성공 에피소드 카운트 오류"
    
    print(f"✅ 에피소드 증가: {initial_episode} → {agent.episode}")
    print(f"✅ 보상 초기화: 150 → {agent.total_reward}")
    print(f"✅ 탐험률 감소: {initial_epsilon:.3f} → {agent.config.epsilon:.3f}")
    print(f"✅ 성공 에피소드: {agent.successful_episodes}")

def run_simulation():
    """간단한 학습 시뮬레이션"""
    print("\n🎮 학습 시뮬레이션")
    print("-" * 40)
    
    config = QLearningConfig()
    agent = QLearningAgent(config)
    
    # 시뮬레이션 파라미터
    num_episodes = 10
    steps_per_episode = 20
    
    print(f"📊 시뮬레이션 설정: {num_episodes} 에피소드, 에피소드당 {steps_per_episode} 스텝")
    
    for episode in range(num_episodes):
        agent.total_reward = 0
        
        for step in range(steps_per_episode):
            # 임의의 상태 (중앙 근처)
            state = np.random.choice([2, 3, 4])
            
            # 행동 선택
            action = agent.choose_action(state, training=True)
            
            # 보상 계산 (라인이 검출되었다고 가정)
            reward = agent.calculate_reward(state, True)
            agent.total_reward += reward
            
            # 다음 상태 (임의)
            next_state = np.random.choice([2, 3, 4])
            
            # Q-테이블 업데이트
            if step > 0:  # 첫 번째 스텝이 아닌 경우
                agent.update_q_table(prev_state, prev_action, reward, state)
            
            prev_state = state
            prev_action = action
        
        # 에피소드 종료
        agent.end_episode()
        
        print(f"  에피소드 {episode + 1}: 보상 {agent.episode_rewards[-1]:.1f}, ε={agent.config.epsilon:.3f}")
    
    # 최종 Q-테이블 상태
    print(f"\n📊 최종 Q-테이블 (중앙 상태):")
    for action in range(config.num_actions):
        action_names = ['좌회전', '약간좌', '직진', '약간우', '우회전']
        q_value = agent.q_table[3, action]
        print(f"  {action_names[action]}: {q_value:.3f}")

def main():
    """메인 테스트 함수"""
    print("🧪 Q-Learning LineTracing System 테스트 시작")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # 각 테스트 실행
        test_qlearning_config()
        test_qlearning_agent()
        test_state_conversion()
        test_action_selection()
        test_q_table_update()
        test_reward_calculation()
        test_model_save_load()
        test_episode_management()
        run_simulation()
        
        end_time = time.time()
        
        print("\n" + "=" * 60)
        print("🎉 모든 테스트 통과!")
        print(f"⏱️ 실행 시간: {end_time - start_time:.2f}초")
        print(f"📅 테스트 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        return False
    except Exception as e:
        print(f"\n💥 예상치 못한 오류: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 