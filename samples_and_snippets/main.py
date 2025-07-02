import tkinter as tk
import threading
import time
from typing import Iterable

from interfaces import CarparkSensorListener, CarparkDataProvider
from mocks import parking_database


# -------------------------------
# GUI DISPLAY CLASS
# -------------------------------
class CarparkInfoDisplay:
    """Displays live parking information in a separate window."""

    DISPLAY_INIT = '– – –'
    SEP = ':'

    def __init__(self, root, title: str, fields: Iterable[str]):
        self.window = tk.Toplevel(root)
        self.window.title(f'{title} - Parking Info')
        self.window.geometry('800x400')
        self.window.resizable(False, False)

        self.fields = fields
        self.gui = {}

        # Create label and value widgets for each field
        for i, field in enumerate(fields):
            label = tk.Label(
                self.window, text=field + self.SEP, font=('Arial', 40)
            )
            value = tk.Label(
                self.window, text=self.DISPLAY_INIT, font=('Arial', 40)
            )
            label.grid(row=i, column=0, sticky=tk.E, padx=10, pady=10)
            value.grid(row=i, column=1, sticky=tk.W, padx=10, pady=10)

            self.gui[f'label_{i}'] = label
            self.gui[f'value_{i}'] = value

    def update(self, new_data: dict):
        """Update display with new carpark data."""
        if not self.window.winfo_exists():
            return

        for key in self.gui:
            if key.startswith('label_'):
                idx = key.split('_')[1]
                field = self.gui[key].cget("text").rstrip(self.SEP)
                value_key = f'value_{idx}'

                if field in new_data and value_key in self.gui:
                    try:
                        self.gui[value_key].config(text=new_data[field])
                    except tk.TclError:
                        pass

        try:
            self.window.update_idletasks()
        except tk.TclError:
            pass


# -------------------------------
# DISPLAY CONTROLLER
# -------------------------------
class CarparkDisplayManager:
    """Manages background updates to the display."""

    FIELDS = ['Available Bays', 'Temperature', 'Time']

    def __init__(self, root):
        self.display = CarparkInfoDisplay(root, "City Carpark", self.FIELDS)
        self.provider = None
        self._start_display_thread()

    def _start_display_thread(self):
        """Starts a background thread to refresh the display periodically."""
        t = threading.Thread(target=self._refresh_loop, daemon=True)
        t.start()

    def _refresh_loop(self):
        """Loop that refreshes the display every second."""
        while True:
            time.sleep(1)
            if self.provider and self.display.window.winfo_exists():
                self.refresh()

    def refresh(self):
        """Pull data from provider and update the display."""
        if not self.display.window.winfo_exists():
            return

        try:
            current_time = self.provider.current_time
            if not isinstance(current_time, time.struct_time):
                current_time = time.localtime()

            values = {
                'Available Bays': f'{self.provider.available_spaces:03d}',
                'Temperature': f'{self.provider.temperature:.1f}℃',
                'Time': time.strftime('%H:%M:%S', current_time),
            }

            self.display.update(values)

        except Exception as e:
            print("Display update error:", e)

    @property
    def data_provider(self):
        return self.provider

    @data_provider.setter
    def data_provider(self, provider):
        if isinstance(provider, CarparkDataProvider):
            self.provider = provider


# -------------------------------
# SENSOR SIMULATOR GUI
# -------------------------------
class CarSensorSimulator:
    """Simulates sensor events via GUI."""

    def __init__(self, root):
        self.root = root
        self.root.title("Sensor Simulator")
        self.listeners = []

        self._setup_ui()

    def _setup_ui(self):
        """Initialize GUI widgets."""
        tk.Button(
            self.root, text="🚗 Car Enters", font=('Arial', 40),
            command=self._car_in
        ).grid(row=0, column=0, columnspan=2, pady=10)

        tk.Button(
            self.root, text="Car Leaves 🚙", font=('Arial', 40),
            command=self._car_out
        ).grid(row=1, column=0, columnspan=2, pady=10)

        # Temperature input
        tk.Label(
            self.root, text="Temperature (°C)", font=('Arial', 20)
        ).grid(row=2, column=0, sticky=tk.E)

        self.temp_var = tk.StringVar()
        self.temp_var.trace_add('write', self._on_temp_change)

        tk.Entry(
            self.root, textvariable=self.temp_var, font=('Arial', 20)
        ).grid(row=2, column=1, sticky=tk.W)

        # License plate input
        tk.Label(
            self.root, text="License Plate", font=('Arial', 20)
        ).grid(row=3, column=0, sticky=tk.E)

        self.plate_var = tk.StringVar()

        tk.Entry(
            self.root, textvariable=self.plate_var, font=('Arial', 20)
        ).grid(row=3, column=1, sticky=tk.W)

        # Reset button
        tk.Button(
            self.root, text="Reset Parking", font=('Arial', 20),
            command=self._reset
        ).grid(row=4, column=1, pady=10)

    @property
    def license_plate(self):
        return self.plate_var.get()

    def register_listener(self, listener):
        """Attach a listener to receive simulated sensor events."""
        if isinstance(listener, CarparkSensorListener):
            self.listeners.append(listener)

    def _car_in(self):
        """Simulate car entering event."""
        for listener in self.listeners:
            listener.incoming_car(self.license_plate)

    def _car_out(self):
        """Simulate car leaving event."""
        for listener in self.listeners:
            listener.outgoing_car(self.license_plate)

    def _on_temp_change(self, *args):
        """Send temperature updates when user changes value."""
        try:
            temp = float(self.temp_var.get())
            for listener in self.listeners:
                listener.temperature_reading(temp)
        except ValueError:
            pass

    def _reset(self):
        """Reset the parking lot via all registered listeners."""
        for listener in self.listeners:
            if hasattr(listener, 'reset_parking'):
                listener.reset_parking()


# -------------------------------
# MAIN ENTRY POINT
# -------------------------------
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()  # Hide the base root window

    # Load mock database as data provider
    database = parking_database()

    # Set up the display manager
    display = CarparkDisplayManager(root)
    display.data_provider = database
    database._update_display = display.refresh  # Optional: allow DB to trigger GUI update

    # Set up the sensor simulator GUI
    sensor_gui = CarSensorSimulator(tk.Toplevel(root))
    sensor_gui.register_listener(database)

    # Run the GUI event loop
    root.mainloop()
