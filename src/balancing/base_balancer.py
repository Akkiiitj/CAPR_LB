from abc import ABC, abstractmethod

class BaseBalancer(ABC):

    @abstractmethod
    def select_server(self, servers, event):
        pass