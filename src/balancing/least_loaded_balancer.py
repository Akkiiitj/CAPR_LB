from .base_balancer import BaseBalancer

class LeastLoadedBalancer(BaseBalancer):

    def select_server(self, servers, event):
        return min(servers, key=lambda s: len(s.jobs))