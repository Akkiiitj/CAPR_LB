import matplotlib
matplotlib.use('Agg')   # 🔥 important for pytest

import matplotlib.pyplot as plt

from src.core.simulation_environment import SimulationEnvironment
from src.core.routing_engine import RoutingEngine
from src.balancing.least_loaded_balancer import LeastLoadedBalancer


def test_thrashing_behavior():

    # ✅ DEFINE ROUTER PROPERLY
    router = RoutingEngine(
        rearrangement_policy=None,
        balancer=LeastLoadedBalancer(),
        mode="baseline"
    )

    sim = SimulationEnvironment(10, router)

    logs, queue, history = sim.run()

    # 🔥 Plot queue oscillation
    plt.plot(history)
    plt.title("Queue Oscillation")

    import os
    os.makedirs("results", exist_ok=True)

    plt.savefig("results/thrashing.png")