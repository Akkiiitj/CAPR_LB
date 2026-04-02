
from rl.q_learning_agent import QLearningAgent



def test_rl_learning_curve():

    agent = QLearningAgent()
    values = []

    state = (1,1)

    for _ in range(100):
        agent.update(state, 0, -1, state)
        values.append(agent.q_table[state][0])

    import matplotlib.pyplot as plt
    plt.plot(values)
    plt.title("Q Learning Convergence")
    plt.savefig("results/rl_curve.png")