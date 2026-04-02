from src.core.simulation_environment import SimulationEnvironment
from src.core.routing_engine import RoutingEngine
from src.balancing.least_loaded_balancer import LeastLoadedBalancer

import matplotlib.pyplot as plt
import os


def test_stability_under_load():

    router = RoutingEngine(None, LeastLoadedBalancer(), mode="baseline")
    sim = SimulationEnvironment(10, router)

    logs, queue, history = sim.run()

    # 📊 Plot queue behavior over time
    plt.plot(history)
    plt.title("System Stability Under Load")
    plt.xlabel("Time Step")
    plt.ylabel("Queue Size")

    os.makedirs("results", exist_ok=True)
    plt.savefig("results/stability.png")

    max_queue = max(history)

    print("Max Queue Size:", max_queue)

    # ✅ sanity condition
    assert max_queue > 0