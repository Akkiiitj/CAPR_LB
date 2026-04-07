"""
Enhanced Q-Learning agent for dynamic load balancing.

Multi-dimensional state space:
- Predicted load (from linear model)
- Queue length
- Server count
- Spike phase

Action space:
- Add servers
- Remove servers  
- Rearrange queue
- Do nothing
"""

import numpy as np
import random
from typing import Dict, Tuple, List
from collections import defaultdict
import pickle


class EnhancedQLearningAgent:
    """
    Enhanced Q-Learning agent with multi-dimensional state and action spaces.
    Incorporates external prediction signals for more informed decisions.
    """
    
    def __init__(self,
                 alpha: float = 0.1,
                 gamma: float = 0.95,
                 epsilon: float = 0.2,
                 epsilon_decay: float = 0.995,
                 min_epsilon: float = 0.05):
        """
        Initialize Q-Learning agent.
        
        Args:
            alpha: Learning rate (0-1)
            gamma: Discount factor (0-1)
            epsilon: Exploration rate (0-1)
            epsilon_decay: Decay factor for epsilon
            min_epsilon: Minimum epsilon for exploration
        """
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon
        
        self.q_table = defaultdict(lambda: np.zeros(4))  # 4 actions
        
        # Tracking
        self.episode_count = 0
        self.total_reward = 0
        self.episode_rewards = []
        
        # Action definitions
        self.actions = {
            0: 'add_server',
            1: 'remove_server',
            2: 'rearrange_queue',
            3: 'do_nothing'
        }
    
    def discretize_state(self, 
                        predicted_load: float,
                        queue_length: int,
                        active_servers: int,
                        spike_probability: float) -> Tuple[int, int, int, int]:
        """
        Convert continuous state values to discrete buckets.
        
        Returns: (load_bucket, queue_bucket, server_bucket, spike_bucket)
        """
        # Discretize predicted load (0-100 normalized)
        load_bucket = min(9, max(0, int(predicted_load / 12.5)))  # 0-9 buckets
        
        # Discretize queue length
        queue_bucket = min(9, max(0, int(queue_length / 5)))  # 0-9 buckets
        
        # Discretize active servers (0-20 range)
        server_bucket = min(9, max(0, int(active_servers / 2)))  # 0-9 buckets
        
        # Discretize spike probability (0-100%)
        spike_bucket = min(3, max(0, int(spike_probability * 4)))  # 0-3 buckets
        
        return (load_bucket, queue_bucket, server_bucket, spike_bucket)
    
    def get_state(self,
                 predicted_load: float,
                 queue_length: int,
                 active_servers: int,
                 spike_probability: float = 0.0) -> Tuple:
        """
        Create state tuple by discretizing inputs.
        """
        state = self.discretize_state(predicted_load, queue_length, 
                                     active_servers, spike_probability)
        return state
    
    def choose_action(self, state: Tuple, training: bool = True) -> int:
        """
        Choose action using epsilon-greedy strategy.
        
        Args:
            state: Current state tuple
            training: If True, use exploration. If False, use exploitation only.
        
        Returns: Action index (0-3)
        """
        if training and random.random() < self.epsilon:
            # Explore: random action
            return random.randint(0, 3)
        else:
            # Exploit: best action from Q-table
            q_values = self.q_table[state]
            return np.argmax(q_values)
    
    def update_q_value(self,
                       state: Tuple,
                       action: int,
                       reward: float,
                       next_state: Tuple,
                       done: bool = False):
        """
        Update Q-value using Q-learning update rule.
        
        Q(s,a) = Q(s,a) + α[r + γ * max(Q(s',a')) - Q(s,a)]
        """
        current_q = self.q_table[state][action]
        next_q = np.max(self.q_table[next_state]) if not done else 0
        
        new_q = current_q + self.alpha * (reward + self.gamma * next_q - current_q)
        self.q_table[state][action] = new_q
    
    def calculate_reward(self,
                        queue_length: int,
                        response_time: float,
                        servers_used: int,
                        max_servers: int,
                        sla_met: bool = True,
                        action: int = None) -> float:
        """
        Calculate reward signal for action.
        
        Rewards:
        - Negative for high queue/response time (objective: minimize latency)
        - Negative for over-provisioning
        - Positive bonus for SLA compliance
        - Negative penalty for queue rearrangement overhead
        """
        reward = 0.0
        
        # Primary objective: minimize queue depth
        reward -= queue_length * 0.5
        
        # Secondary: minimize response time
        reward -= min(response_time / 100, 10)  # Normalize response time
        
        # Efficiency: penalize over-provisioning
        utilization = 1.0 - (servers_used / max_servers) if max_servers > 0 else 0
        if utilization < 0.3:  # Under 30% utilized
            reward -= 2.0
        
        # SLA compliance bonus
        if sla_met:
            reward += 5.0
        else:
            reward -= 10.0
        
        # Action-specific considerations
        if action == 0:  # add_server
            if queue_length > 10:  # Good decision if queue is high
                reward += 2.0
            else:  # Bad decision if queue is low
                reward -= 1.0
        
        elif action == 1:  # remove_server
            if queue_length < 5:  # Good decision if queue is low
                reward += 2.0
            else:  # Bad decision if queue is high
                reward -= 3.0
        
        elif action == 2:  # rearrange_queue
            if queue_length > 8:  # Rearrangement useful when queue is large
                reward += 1.0
            else:  # Overhead not worth it for small queues
                reward -= 0.5
        
        # Stability bonus: penalize if too many actions
        # This is handled in training loop
        
        return reward
    
    def train_step(self,
                   current_state: Tuple,
                   action: int,
                   reward: float,
                   next_state: Tuple,
                   done: bool = False):
        """Execute one training step."""
        self.update_q_value(current_state, action, reward, next_state, done)
        
        self.total_reward += reward
        
        if done:
            self.episode_rewards.append(self.total_reward)
            self.episode_count += 1
            self.total_reward = 0
            
            # Decay epsilon
            if self.epsilon > self.min_epsilon:
                self.epsilon *= self.epsilon_decay
    
    def get_recommended_action(self,
                              predicted_load: float,
                              queue_length: int,
                              active_servers: int,
                              max_servers: int,
                              spike_probability: float = 0.0) -> Tuple[str, float]:
        """
        Get recommended action with confidence.
        
        Returns: (action_name, q_value)
        """
        state = self.get_state(predicted_load, queue_length, active_servers, spike_probability)
        action_idx = np.argmax(self.q_table[state])
        q_value = self.q_table[state][action_idx]
        
        return self.actions[action_idx], float(q_value)
    
    def get_all_actions_scores(self, state: Tuple) -> Dict[str, float]:
        """Get Q-values for all actions in a state."""
        q_values = self.q_table[state]
        return {
            self.actions[i]: float(q_values[i])
            for i in range(4)
        }
    
    def get_statistics(self) -> Dict:
        """Get training statistics."""
        return {
            'episodes_trained': self.episode_count,
            'avg_reward': np.mean(self.episode_rewards) if self.episode_rewards else 0,
            'max_reward': max(self.episode_rewards) if self.episode_rewards else 0,
            'min_reward': min(self.episode_rewards) if self.episode_rewards else 0,
            'current_epsilon': self.epsilon,
            'q_table_size': len(self.q_table),
            'alpha': self.alpha,
            'gamma': self.gamma
        }
    
    def save_model(self, file_path: str):
        """Save trained Q-table and parameters."""
        model_data = {
            'q_table': dict(self.q_table),  # Convert defaultdict to dict
            'alpha': self.alpha,
            'gamma': self.gamma,
            'epsilon': self.epsilon,
            'episode_count': self.episode_count,
            'episode_rewards': self.episode_rewards,
            'actions': self.actions
        }
        
        with open(file_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"✓ Q-Learning model saved to {file_path}")
    
    def load_model(self, file_path: str):
        """Load trained Q-table and parameters."""
        with open(file_path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.q_table = defaultdict(lambda: np.zeros(4), model_data['q_table'])
        self.alpha = model_data['alpha']
        self.gamma = model_data['gamma']
        self.epsilon = model_data['epsilon']
        self.episode_count = model_data['episode_count']
        self.episode_rewards = model_data['episode_rewards']
        
        print(f"✓ Q-Learning model loaded from {file_path}")


class DQNAgent:
    """
    (Future) Deep Q-Network agent for more complex state spaces.
    Placeholder for neural network-based agent.
    """
    
    def __init__(self, state_size: int, action_size: int):
        """Initialize DQN agent."""
        self.state_size = state_size
        self.action_size = action_size
        # Implementation would use PyTorch/TensorFlow
        pass


class QLearningTrainer:
    """
    Training loop manager for Q-Learning agent with simulated environment.
    """
    
    def __init__(self, agent: EnhancedQLearningAgent):
        self.agent = agent
        self.training_log = []
    
    def train_episode(self,
                     initial_state: Tuple,
                     max_steps: int = 1000,
                     environment_simulator = None) -> Dict:
        """
        Run one training episode.
        
        Args:
            initial_state: Starting state
            max_steps: Maximum steps in episode
            environment_simulator: Callable that advances state and returns metrics
        
        Returns: Episode statistics
        """
        state = initial_state
        episode_log = []
        
        for step in range(max_steps):
            # Choose action
            action = self.agent.choose_action(state, training=True)
            
            # Simulate action (environment responds)
            if environment_simulator:
                next_state, metrics = environment_simulator(state, action)
                done = metrics.get('done', False)
            else:
                # Random progression (for testing)
                next_state = state
                done = False
            
            # Calculate reward
            queue_length = next_state[1]  # From state tuple
            response_time = 50  # Simplified
            servers_used = next_state[2]
            sla_met = queue_length < 15
            
            reward = self.agent.calculate_reward(
                queue_length, response_time, servers_used, 
                max_servers=20, sla_met=sla_met, action=action
            )
            
            # Update agent
            self.agent.train_step(state, action, reward, next_state, done)
            
            episode_log.append({
                'step': step,
                'state': state,
                'action': self.agent.actions[action],
                'reward': reward,
                'next_state': next_state
            })
            
            state = next_state
            
            if done:
                break
        
        stats = {
            'episode': self.agent.episode_count,
            'steps': len(episode_log),
            'total_reward': self.agent.episode_rewards[-1] if self.agent.episode_rewards else 0,
            'epsilon': self.agent.epsilon
        }
        
        return stats
