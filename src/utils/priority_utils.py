def compute_priority(event, weights):
    return (
        weights["deadline"] * (1 / event.deadline_remaining)
        + weights["exec"] * event.estimated_execution_time
        + weights["wait"] * event.waiting_time
        + weights["resource"] * event.resource_requirement
        + weights["business"] * event.business_priority_level
    )