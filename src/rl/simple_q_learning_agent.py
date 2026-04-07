"""
Simple Q-Learning Agent - Baseline Model

A basic Q-Learning implementation for comparison.
Uses simple state space and basic reward function.
"""

import numpy as np
import random
from typing import Dict, Tuple
from collections import defaultdict


class SimpleQLearningAgent:
    """
    Basic Q-Learning agent with minimal state and action spaces.
    Direct mapping: heavy load → add servers, light load → remove servers.
    """
    
    def __init__(self,
                 alpha: float = 0.1,
                 gamma: float = 0.9,
                 epsilon: float = 0.1):
        """
        Initialize simple Q-Learning agent.
        
        Args:
            alpha: Learning rate
            gamma: Discount factor
            epsilon: Exploration rate
        """
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        
        # Simple Q-table: state → action values
        self.q_table = defaultdict(lambda: np.zeros(2))  # Only 2 actions: ADD, REMOVE
        
        # Tracking
        self.episode_count = 0
        self.total_reward = 0
        
        # Action definitions
        self.actions = {
            0: 'add_server',
            1: 'remove_server'
        }
    
    def get_state(self, queue_length: int) -> int:
        """
        Create simple state: just categorize queue length.
        
        State space: 0-4 (5 states based on queue depth)
        - 0: Empty queue (queue_length = 0)
        - 1: Low queue (1-5)
        - 2: Medium queue (6-10)
        - 3: High queue (11-20)
        - 4: Very high queue (21+)
        """
        if queue_length == 0:
            return 0
        elif queue_length <= 5:
            return 1
        elif queue_length <= 10:
            return 2
        elif queue_length <= 20:
            return 3
        else:
            return 4
    
    def choose_action(self, state: int, training: bool = True) -> int:
        """
        Choose action using epsilon-greedy strategy.
        
        Args:
            state: Current state (0-4)
            training: If True, use exploration
        
        Returns: Action index (0=ADD, 1=REMOVE)
        """
        if training and random.random() < self.epsilon:
            # Explore: random action
            return random.randint(0, 1)
        else:
            # Exploit: best action from Q-table
            q_values = self.q_table[state]
            return np.argmax(q_values)
    
    def update_q_value(self,
                       state: int,
                       action: int,
                       reward: float,
                       next_state: int):
        """
        Update Q-value using Q-learning formula.
        
        Q(s,a) = Q(s,a) + α[r + γ * max(Q(s',a')) - Q(s,a)]
        """
        current_q = self.q_table[state][action]
        next_q = np.max(self.q_table[next_state])
        
        new_q = current_q + self.alpha * (reward + self.gamma * next_q - current_q)
        self.q_table[state][action] = new_q
    
    def calculate_reward(self, 
                        queue_length: int,
                        action: int) -> float:
        """
        Calculate simple reward: +1 for good action, -1 for bad action.
        
        Logic:
        - If queue is HIGH and we ADD servers: +1 (good)
        - If queue is HIGH and we REMOVE servers: -1 (bad)
        - If queue is LOW and we REMOVE servers: +1 (good)
        - If queue is LOW and we ADD servers: -1 (bad)
        """
        is_high_queue = queue_length > 8
        
        if action == 0:  # ADD_SERVER
            return 1.0 if is_high_queue else -1.0
        else:  # REMOVE_SERVER
            return 1.0 if not is_high_queue else -1.0
    
    def train_step(self,
                   state: int,
                   action: int,
                   reward: float,
                   next_state: int):
        """Execute one training step."""
        self.update_q_value(state, action, reward, next_state)
        self.total_reward += reward
        self.episode_count += 1
    
    def get_recommended_action(self, queue_length: int) -> str:
        """Get recommended action based on queue length."""
        state = self.get_state(queue_length)
        action_idx = np.argmax(self.q_table[state])
        return self.actions[action_idx]
    
    def get_statistics(self) -> Dict:
        """Get training statistics."""
        return {
            'episodes_trained': self.episode_count,
            'avg_reward_per_step': self.total_reward / max(1, self.episode_count),
            'q_table_size': len(self.q_table),
            'num_states': 5,
            'num_actions': 2
        }


# ============================================================================
# EXAMPLE USAGE: Simple Agent
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SIMPLE Q-LEARNING AGENT - BASELINE")
    print("=" * 70)
    
    agent = SimpleQLearningAgent()
    
    # Simulate 100 training steps
    print("\nTraining agent on simple queue scenarios...")
    for episode in range(100):
        # Random queue scenario
        queue_length = random.randint(0, 30)
        state = agent.get_state(queue_length)
        
        # Choose action
        action = agent.choose_action(state, training=True)
        
        # Calculate reward
        reward = agent.calculate_reward(queue_length, action)
        
        # Simulate next state
        next_queue = max(0, queue_length + (random.randint(-3, 3)))
        next_state = agent.get_state(next_queue)
        
        # Train
        agent.train_step(state, action, reward, next_state)
    
    print("\nTraining complete!")
    print(f"Episodes trained: {agent.episode_count}")
    
    # Test on specific scenarios
    print("\n" + "=" * 70)
    print("DECISION EXAMPLES")
    print("=" * 70)
    
    test_scenarios = [0, 3, 7, 12, 25]
    for queue_len in test_scenarios:
        action = agent.get_recommended_action(queue_len)
        state = agent.get_state(queue_len)
        q_vals = agent.q_table[state]
        print(f"\nQueue Length: {queue_len:2d} | State: {state} → Action: {action:15s} | Q-values: {q_vals}")
    
    print("\n" + "=" * 70)
    print("STATISTICS")
    print("=" * 70)
    stats = agent.get_statistics()
    for key, value in stats.items():
        print(f"{key:25s}: {value}")
