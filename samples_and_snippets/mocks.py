import time
from interfaces import CarparkSensorListener, CarparkDataProvider


class ParkingDatabase(CarparkSensorListener, CarparkDataProvider):
    def __init__(self):
        self._total_spaces = 100
        self._occupied = set()  # Set of license plates
        self._temperature = 20.0
        self._update_display = None
        self._activity_log = []
        self._log_display_callback = None  # Hook for GUI

    @property
    def available_spaces(self):
        return self._total_spaces - len(self._occupied)

    @property
    def temperature(self):
        return self._temperature

    @property
    def current_time(self):
        return time.localtime()

    def set_log_display(self, callback):
        self._log_display_callback = callback

    def log_activity(self, message: str):
        now = time.localtime()
        timestamp = time.strftime('%H:%M:%S', now)
        log_entry = f"[{timestamp}] {message}"
        self._activity_log.append(log_entry)
        print(log_entry)
        if self._log_display_callback:
            self._log_display_callback(log_entry)

    def get_activity_log(self):
        return self._activity_log.copy()

    def incoming_car(self, plate: str):
        if plate and len(self._occupied) < self._total_spaces:
            self._occupied.add(plate)
            self.log_activity(f"Car {plate} entered. Available spaces: {self.available_spaces}")
            self.trigger_update()
        else:
            self.log_activity(f"Car {plate} attempted to enter but parking is full.")

    def outgoing_car(self, plate: str):
        if plate in self._occupied:
            self._occupied.remove(plate)
            self.log_activity(f"Car {plate} exited. Available spaces: {self.available_spaces}")
            self.trigger_update()
        else:
            self.log_activity(f"Car {plate} attempted to exit but was not found.")

    def temperature_reading(self, temp: float):
        self._temperature = temp
        self.log_activity(f"Temperature updated to {temp:.1f}°C")
        self.trigger_update()

    def reset_parking(self):
        self._occupied.clear()
        self._temperature = 20.0
        self.log_activity("Parking system reset. All spaces cleared and temperature set to 20.0°C.")
        self.trigger_update()

    def trigger_update(self):
        if self._update_display:
            self._update_display()


def parking_database():
    return ParkingDatabase()
