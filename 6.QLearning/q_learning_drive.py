"""
q_learning_drive.py - Autonomous driving using Q-learning
"""

import time
import random
import numpy as np
import json
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import sys

# Add parent directory to path to allow imports
sys.path.append(str(Path(__file__).parent.parent))

from ComponentClass.IntegratedClass import PathfinderKit, PathfinderConfig

class QLearningAgent:
    """
    Q-Learning agent for autonomous driving.
    """
    
    def __init__(self, kit: PathfinderKit, config: Optional[dict] = None):
        """
        Initialize the Q-learning agent.
        
        Args:
            kit: Instance of PathfinderKit with initialized components
            config: Configuration dictionary (optional)
        """
        self.kit = kit
        self.config = self._load_config(config)
        self.q_table: Dict[str, List[float]] = {}
        self.state = ""
        self.last_action = 0
        self.episode = 0
        self.steps = 0
        self.total_reward = 0
        self.running = False
        
        # Create models directory if it doesn't exist
        os.makedirs(self.config['models_dir'], exist_ok=True)
    
    def _load_config(self, config: Optional[dict]) -> dict:
        """Load and validate configuration"""
        default_config = {
            'learning_rate': 0.1,      # Learning rate (alpha)
            'discount_factor': 0.95,    # Discount factor (gamma)
            'exploration_rate': 1.0,    # Initial exploration rate (epsilon)
            'exploration_min': 0.01,    # Minimum exploration rate
            'exploration_decay': 0.995,  # Decay rate for exploration
            'models_dir': 'models',     # Directory to save Q-tables
            'model_prefix': 'qtable_',  # Prefix for saved models
            'state_bins': 5,            # Number of bins for discretizing state space
            'max_speed': 100,           # Maximum motor speed (0-100)
            'min_speed': 30,            # Minimum motor speed (0-100)
            'sensor_max': 200,          # Maximum sensor value (cm)
            'sensor_bins': 4,            # Number of bins for sensor values
            'actions': [
                # (left_speed, right_speed)
                (40, 40),    # Forward
                (60, 20),     # Slight right
                (20, 60),     # Slight left
                (70, 0),      # Hard right
                (0, 70),      # Hard left
                (-30, 30),    # Spin right
                (30, -30)     # Spin left
            ]
        }
        
        if config:
            default_config.update(config)
            
        return default_config
    
    def _discretize_value(self, value: float, min_val: float, max_val: float, bins: int) -> int:
        """Discretize a continuous value into bins"""
        if value <= min_val:
            return 0
        if value >= max_val:
            return bins - 1
        return int((value - min_val) / (max_val - min_val) * (bins - 1))
    
    def get_state(self) -> str:
        """
        Get the current state as a string key.
        
        Returns:
            String representing the current state
        """
        # Get sensor readings
        distance = self.kit.get_obstacle_distance()
        
        # Discretize sensor values
        distance_bin = self._discretize_value(
            distance, 0, self.config['sensor_max'], self.config['sensor_bins']
        )
        
        # Create state key (e.g., "2_1_3" for multiple sensors)
        state_key = f"{distance_bin}"
        
        return state_key
    
    def choose_action(self, state: str) -> int:
        """
        Choose an action using epsilon-greedy policy.
        
        Args:
            state: Current state
            
        Returns:
            Index of the chosen action
        """
        # Exploration: choose a random action
        if random.random() < self.config['exploration_rate']:
            return random.randint(0, len(self.config['actions']) - 1)
            
        # Exploitation: choose the best known action
        if state in self.q_table:
            return int(np.argmax(self.q_table[state]))
        else:
            # Initialize state if not in Q-table
            self.q_table[state] = [0.0] * len(self.config['actions'])
            return random.randint(0, len(self.config['actions']) - 1)
    
    def get_reward(self, state: str, action: int) -> float:
        """
        Calculate the reward for taking an action in a state.
        
        Args:
            state: Current state
            action: Action index
            
        Returns:
            Reward value
        """
        # Get sensor readings
        distance = self.kit.get_obstacle_distance()
        
        # Calculate reward based on distance to obstacle
        if distance < 10:  # Too close
            return -10.0
        elif distance < 30:  # Warning zone
            return -2.0
        elif distance > 50:  # Good distance
            return 1.0
        else:  # Normal distance
            return 0.1
    
    def update_q_value(self, state: str, action: int, reward: float, next_state: str) -> None:
        """
        Update Q-value using the Q-learning update rule.
        
        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
        """
        if state not in self.q_table:
            self.q_table[state] = [0.0] * len(self.config['actions'])
            
        if next_state not in self.q_table:
            self.q_table[next_state] = [0.0] * len(self.config['actions'])
        
        # Q-learning update rule
        best_next_action = np.argmax(self.q_table[next_state])
        td_target = reward + self.config['discount_factor'] * self.q_table[next_state][best_next_action]
        td_error = td_target - self.q_table[state][action]
        self.q_table[state][action] += self.config['learning_rate'] * td_error
    
    def decay_exploration(self) -> None:
        """Decay exploration rate"""
        self.config['exploration_rate'] = max(
            self.config['exploration_min'],
            self.config['exploration_rate'] * self.config['exploration_decay']
        )
    
    def save_model(self, filename: Optional[str] = None) -> str:
        """
        Save the Q-table to a file.
        
        Args:
            filename: Optional filename (will generate if None)
            
        Returns:
            Path to the saved file
        """
        if filename is None:
            filename = f"{self.config['model_prefix']}{self.episode:06d}.json"
        
        filepath = os.path.join(self.config['models_dir'], filename)
        
        # Convert numpy arrays to native Python types
        q_table_serializable = {
            state: [float(q) for q in q_values]
            for state, q_values in self.q_table.items()
        }
        
        # Save with metadata
        data = {
            'q_table': q_table_serializable,
            'episode': self.episode,
            'config': self.config,
            'timestamp': time.time()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"Model saved to {filepath}")
        return filepath
    
    def load_model(self, filepath: str) -> bool:
        """
        Load a Q-table from a file.
        
        Args:
            filepath: Path to the model file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            self.q_table = {
                state: np.array(q_values)
                for state, q_values in data['q_table'].items()
            }
            
            # Update config with saved values
            if 'config' in data:
                self.config.update(data['config'])
                
            if 'episode' in data:
                self.episode = data['episode']
                
            print(f"Model loaded from {filepath}")
            return True
            
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def train_episode(self, max_steps: int = 1000) -> float:
        """
        Train for one episode.
        
        Args:
            max_steps: Maximum number of steps per episode
            
        Returns:
            Total reward for the episode
        """
        self.episode += 1
        self.steps = 0
        self.total_reward = 0
        
        # Get initial state
        self.state = self.get_state()
        
        for _ in range(max_steps):
            if not self.running:
                break
                
            # Choose and perform an action
            action = self.choose_action(self.state)
            self.last_action = action
            left_speed, right_speed = self.config['actions'][action]
            self.kit.motors.set_speeds(left_speed, right_speed)
            
            # Observe the result
            next_state = self.get_state()
            reward = self.get_reward(self.state, action)
            
            # Update Q-value
            self.update_q_value(self.state, action, reward, next_state)
            
            # Update statistics
            self.total_reward += reward
            self.steps += 1
            
            # Move to the next state
            self.state = next_state
            
            # Print progress
            if self.steps % 10 == 0:
                print(f"Episode: {self.episode}, Step: {self.steps}, "
                      f"Reward: {self.total_reward:.1f}, "
                      f"Exploration: {self.config['exploration_rate']:.3f}")
            
            # Small delay to prevent overwhelming the robot
            time.sleep(0.1)
        
        # Stop the robot at the end of the episode
        self.kit.stop()
        
        # Decay exploration rate
        self.decay_exploration()
        
        # Save model periodically
        if self.episode % 10 == 0:
            self.save_model()
        
        return self.total_reward
    
    def start_training(self, episodes: int = 1000) -> None:
        """
        Start the training process.
        
        Args:
            episodes: Number of episodes to train for
        """
        print(f"Starting training for {episodes} episodes")
        self.running = True
        
        try:
            for _ in range(episodes):
                if not self.running:
                    break
                    
                total_reward = self.train_episode()
                print(f"Episode {self.episode} completed with total reward: {total_reward:.1f}")
                
                # Small delay between episodes
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("Training interrupted")
        finally:
            self.running = False
            self.kit.stop()
            
            # Save the final model
            self.save_model("final_model.json")
            print("Training completed")
    
    def stop_training(self) -> None:
        """Stop the training process"""
        self.running = False
        self.kit.stop()


def main():
    """Test the Q-learning agent"""
    try:
        # Initialize the kit
        config = PathfinderConfig()
        with PathfinderKit(config=config) as kit:
            if not kit.setup():
                print("Failed to initialize kit")
                return
                
            # Create and train Q-learning agent
            agent = QLearningAgent(kit)
            
            # Try to load existing model
            # agent.load_model("models/final_model.json")
            
            # Start training
            agent.start_training(episodes=1000)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Cleanup complete")


if __name__ == "__main__":
    main()