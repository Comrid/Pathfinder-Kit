# Q-Learning for Autonomous Driving

This module implements Q-learning, a reinforcement learning algorithm, to enable autonomous navigation and obstacle avoidance for the Pathfinder Kit.

## Features

- **Reinforcement Learning**: Implements Q-learning algorithm for autonomous decision making
- **Obstacle Avoidance**: Learns to navigate while avoiding obstacles
- **Customizable Rewards**: Configurable reward function for different behaviors
- **Model Persistence**: Save and load trained models
- **Progressive Learning**: Epsilon-greedy exploration strategy with decay

## Prerequisites

- Python 3.7+
- NumPy
- Pathfinder Kit with ultrasonic sensor and motors
- RPi.GPIO (for Raspberry Pi)

## Usage

1. **Basic Training**:
   ```python
   from q_learning_drive import QLearningAgent, PathfinderKit, PathfinderConfig
   
   # Initialize the kit
   config = PathfinderConfig()
   with PathfinderKit(config=config) as kit:
       if kit.setup():
           # Create and train agent
           agent = QLearningAgent(kit)
           agent.start_training(episodes=1000)
   ```

2. **Using a Pre-trained Model**:
   ```python
   agent = QLearningAgent(kit)
   agent.load_model("models/final_model.json")
   ```

3. **Custom Configuration**:
   ```python
   custom_config = {
       'learning_rate': 0.2,
       'discount_factor': 0.9,
       'exploration_rate': 0.5,
       'exploration_min': 0.01,
       'exploration_decay': 0.995,
       'actions': [
           (40, 40),  # Forward
           (60, 20),  # Slight right
           (20, 60),  # Slight left
           (70, 0),   # Hard right
           (0, 70),   # Hard left
           (-30, 30), # Spin right
           (30, -30)  # Spin left
       ]
   }
   
   agent = QLearningAgent(kit, config=custom_config)
   ```

## Configuration Options

- `learning_rate`: How quickly the agent learns (0.0 to 1.0)
- `discount_factor`: Importance of future rewards (0.0 to 1.0)
- `exploration_rate`: Initial probability of taking a random action (0.0 to 1.0)
- `exploration_min`: Minimum exploration rate
- `exploration_decay`: Rate at which exploration decreases
- `actions`: List of possible motor speed pairs (left, right)
- `sensor_bins`: Number of discrete states for sensor values
- `sensor_max`: Maximum expected sensor value (cm)

## Reward Function

The default reward function provides:
- High penalty (-10) for getting too close to obstacles (<10cm)
- Small penalty (-2) for getting close to obstacles (<30cm)
- Small reward (0.1) for normal operation
- Higher reward (1.0) for maintaining good distance (>50cm)

You can customize the reward function by overriding the `get_reward()` method.

## Model Files

Trained models are saved in the `models/` directory with the following format:
- `qtable_XXXXXX.json`: Checkpoints during training
- `final_model.json`: Final saved model

## Visualization (Optional)

For better understanding of the learning process, you can add visualization using matplotlib:

```python
import matplotlib.pyplot as plt

rewards = []

def train_with_visualization(episodes=100):
    agent = QLearningAgent(kit)
    
    for _ in range(episodes):
        total_reward = agent.train_episode()
        rewards.append(total_reward)
        
        # Plot rewards
        plt.clf()
        plt.plot(rewards)
        plt.title('Training Progress')
        plt.xlabel('Episode')
        plt.ylabel('Total Reward')
        plt.pause(0.01)
    
    return agent
```

## Troubleshooting

1. **Agent not learning**:
   - Increase `learning_rate`
   - Adjust reward function
   - Check sensor readings

2. **Too much random movement**:
   - Decrease `exploration_rate`
   - Increase `exploration_decay`

3. **Robot gets stuck**:
   - Add more diverse actions
   - Adjust reward function
   - Check for hardware issues

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
