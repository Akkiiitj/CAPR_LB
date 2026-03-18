class RoutingEngine:

    def __init__(self, rearrangement_policy, balancer):
        self.rearrangement_policy = rearrangement_policy
        self.balancer = balancer

    def run(self, env, queue, servers, log_store):

        while True:
            if queue:

                self.rearrangement_policy.rearrange(queue, env.now)

                event = queue.pop(0)
                server = self.balancer.select_server(servers, event)

                env.process(server.process(env, event, log_store))

            yield env.timeout(0.1)