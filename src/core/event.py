class Event:
    def __init__(self, event_id, arrival_time, deadline, exec_time, resource, business):
        self.id = event_id
        self.arrival_time = arrival_time
        self.deadline_remaining = deadline
        self.estimated_execution_time = exec_time
        self.resource_requirement = resource
        self.business_priority_level = business
        self.waiting_time = 0
        self.start_time = None
        self.finish_time = None