from .base_rearrangement_policy import BaseRearrangementPolicy
from src.utils.priority_utils import compute_priority
from configs.simulation_config import FIXED_THRESHOLD

class WeightedPriorityRearrangement(BaseRearrangementPolicy):

    def __init__(self, weights):
        self.weights = weights

    def rearrange(self, queue, current_time):

        for event in queue:
            event.waiting_time = current_time - event.arrival_time

        if len(queue) >= FIXED_THRESHOLD:
            queue.sort(
                key=lambda e: compute_priority(e, self.weights),
                reverse=True
            )