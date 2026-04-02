import matplotlib
matplotlib.use('Agg')   # 🔥 important for pytest

import matplotlib.pyplot as plt
import os

from src.core.simulation_environment import SimulationEnvironment
from src.core.routing_engine import RoutingEngine
from src.balancing.least_loaded_balancer import LeastLoadedBalancer


def test_scalability_graph():

    rates = range(2, 12)   # smaller = faster + enough insight
    queue_sizes = []

    for rate in rates:

        router = RoutingEngine(
            rearrangement_policy=None,
            balancer=LeastLoadedBalancer(),
            mode="baseline"
        )

        sim = SimulationEnvironment(rate, router)

        logs, queue, _ = sim.run()

        queue_sizes.append(len(queue))

    # 📊 Plot
    plt.plot(rates, queue_sizes)
    plt.xlabel("Arrival Rate")
    plt.ylabel("Queue Size")
    plt.title("Scalability Test")

    os.makedirs("results", exist_ok=True)
    plt.savefig("results/test_scalability.png")

    # ✅ Assertion (VERY IMPORTANT)
    assert queue_sizes[-1] >= queue_sizes[0]