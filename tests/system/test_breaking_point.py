import pandas as pd
from src.core.simulation_environment import SimulationEnvironment
from src.core.routing_engine import RoutingEngine
from src.balancing.least_loaded_balancer import LeastLoadedBalancer


def test_breaking_point():

    results = []

    for rate in range(2, 15):

        router = RoutingEngine(None, LeastLoadedBalancer(), mode="baseline")
        sim = SimulationEnvironment(rate, router)

        logs, queue, _ = sim.run()

        results.append((rate, len(queue)))

    # system must break at some point
    assert any(q > 100 for _, q in results)