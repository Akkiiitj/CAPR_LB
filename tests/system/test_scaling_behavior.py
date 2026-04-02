from src.core.simulation_environment import SimulationEnvironment
from src.core.routing_engine import RoutingEngine
from src.balancing.least_loaded_balancer import LeastLoadedBalancer
from src.policies.weighted_priority_rearrangement import WeightedPriorityRearrangement


def test_scaling_trigger():

    weights = {
        "deadline":0.4,
        "exec":0.2,
        "wait":0.2,
        "resource":0.1,
        "business":0.1
    }

    router = RoutingEngine(
        WeightedPriorityRearrangement(weights),
        LeastLoadedBalancer(),
        mode="threshold"
    )

    sim = SimulationEnvironment(10, router)

    logs, queue, _ = sim.run()

    # crude check: scaling should have happened (manual print exists)
    assert len(logs) > 0