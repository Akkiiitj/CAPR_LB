import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import os

from src.core.simulation_environment import SimulationEnvironment
from src.core.routing_engine import RoutingEngine
from src.balancing.least_loaded_balancer import LeastLoadedBalancer
from src.policies.weighted_priority_rearrangement import WeightedPriorityRearrangement


def test_mode_comparison():

    rate = 10
    results = {}

    weights = {
        "deadline":0.4,
        "exec":0.2,
        "wait":0.2,
        "resource":0.1,
        "business":0.1
    }

    modes = ["baseline", "threshold", "rl"]

    for mode in modes:

        if mode == "baseline":
            router = RoutingEngine(None, LeastLoadedBalancer(), mode="baseline")

        else:
            router = RoutingEngine(
                WeightedPriorityRearrangement(weights),
                LeastLoadedBalancer(),
                mode=mode
            )

        sim = SimulationEnvironment(rate, router)

        logs, queue, history = sim.run()

        results[mode] = history

    # 📊 Plot comparison
    for mode in results:
        plt.plot(results[mode], label=mode)

    plt.legend()
    plt.xlabel("Time")
    plt.ylabel("Queue Size")
    plt.title("Mode Comparison")

    os.makedirs("results", exist_ok=True)
    plt.savefig("results/mode_comparison.png")

    # basic assertion
    assert len(results) == 3