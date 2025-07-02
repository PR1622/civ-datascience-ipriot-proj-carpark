import time
from interfaces import CarparkSensorListener, CarparkDataProvider


class parking_database(CarparkSensorListener, CarparkDataProvider):
    def __init__(self):
        self._total_spaces = 100
        self._occupied = set()  # store license plates
        self._temperature = 20.0
        self._update_display = None

    @property
    def available_spaces(self):
        return self._total_spaces - len(self._occupied)

    @property
    def temperature(self):
        return self._temperature

    @property
    def current_time(self):
        t = time.localtime()
        return (t.tm_hour, t.tm_min, t.tm_sec)

    # Sensor listener methods
    def incoming_car(self, plate: str):
        if plate and len(self._occupied) < self._total_spaces:
            self._occupied.add(plate)
            self._trigger_update()

    def outgoing_car(self, plate: str):
        if plate in self._occupied:
            self._occupied.remove(plate)
            self._trigger_update()

    def temperature_reading(self, temp: float):
        self._temperature = temp
        self._trigger_update()

    def reset_parking(self):
        self._occupied.clear()
        self._temperature = 20.0
        self._trigger_update()

    def _trigger_update(self):
        if self._update_display:
            self._update_display()
