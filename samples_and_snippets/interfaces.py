from abc import ABC, abstractmethod
from typing import Tuple

class CarparkSensorListener(ABC):
    @abstractmethod
    def incoming_car(self, plate: str):
        pass

    @abstractmethod
    def outgoing_car(self, plate: str):
        pass

    @abstractmethod
    def temperature_reading(self, temp: float):
        pass

    @abstractmethod
    def reset_parking(self):
        pass


class CarparkDataProvider(ABC):
    @property
    @abstractmethod
    def available_spaces(self) -> int:
        pass

    @property
    @abstractmethod
    def temperature(self) -> float:
        pass

    @property
    @abstractmethod
    def current_time(self) -> Tuple[int, int, int]:
        """Returns time tuple (hour, minute, second)"""
        pass
