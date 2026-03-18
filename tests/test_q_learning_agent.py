from src.rl.q_learning_agent import QLearningAgent

def test_state_generation():

    agent = QLearningAgent()

    state = agent.get_state(queue_len=12, imbalance=4)

    assert isinstance(state, tuple)


def test_q_update():

    agent = QLearningAgent()

    state = (1,1)
    next_state = (2,1)

    agent.update(state, action=0, reward=-2, next_state=next_state)

    assert state in agent.q_table