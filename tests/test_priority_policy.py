from src.policies.weighted_priority_rearrangement import WeightedPriorityRearrangement
from src.core.event import Event

def test_priority_sorting():

    weights = {
        "deadline":0.5,
        "exec":0.2,
        "wait":0.2,
        "resource":0.1,
        "business":0.1
    }

    policy = WeightedPriorityRearrangement(weights)

    queue = [
        Event(1,0,10,3,0.2,0.1),
        Event(2,0,2,2,0.5,0.8),
        Event(3,0,5,1,0.3,0.3)
    ]

    policy.rearrange(queue, current_time=5)

    assert len(queue) == 3