from abc import ABC, abstractmethod

class BaseRearrangementPolicy(ABC):

    @abstractmethod
    def rearrange(self, queue, current_time):
        pass