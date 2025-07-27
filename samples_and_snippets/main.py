import tkinter as tk
import threading
import time
from typing import Iterable
from mocks import parking_database
from interfaces import CarparkSensorListener, CarparkDataProvider


# --------------------- CarparkInfoDisplay ---------------------
class CarparkInfoDisplay:
    DISPLAY_INIT = '– – –'
    SEP = ':'

    def __init__(self, root, title: str, fields: Iterable[str]):
        self.window = tk.Toplevel(root)
        self.window.title(f'{title} - Parking Info')
        self.window.geometry('800x400')
        self.window.resizable(False, False)

        self.fields = fields
        self.gui = {}

        for i, field in enumerate(fields):
            label = tk.Label(self.window, text=field + self.SEP, font=('Arial', 40))
            value = tk.Label(self.window, text=self.DISPLAY_INIT, font=('Arial', 40))
            label.grid(row=i, column=0, sticky=tk.E, padx=10, pady=10)
            value.grid(row=i, column=1, sticky=tk.W, padx=10, pady=10)

            self.gui[f'label_{i}'] = label
            self.gui[f'value_{i}'] = value

    def update(self, new_data: dict):
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


# --------------------- CarparkDisplayManager ---------------------
class CarparkDisplayManager:
    FIELDS = ['Available Bays', 'Temperature', 'Time']

    def __init__(self, root):
        self.display = CarparkInfoDisplay(root, "City Carpark", self.FIELDS)
        self.provider = None
        self._start_display_thread()

    def _start_display_thread(self):
        t = threading.Thread(target=self._refresh_loop, daemon=True)
        t.start()

    def _refresh_loop(self):
        while True:
            time.sleep(1)
            if self.provider and self.display.window.winfo_exists():
                self.refresh()

    def refresh(self):
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


# --------------------- ActivityLogDisplay ---------------------
class ActivityLogDisplay:
    def __init__(self, root, title="Activity Log"):
        self.window = tk.Toplevel(root)
        self.window.title(title)
        self.window.geometry("800x400")
        self.window.resizable(False, False)

        self.text_widget = tk.Text(self.window, font=("Courier", 14), state=tk.DISABLED)
        self.scrollbar = tk.Scrollbar(self.window, command=self.text_widget.yview)
        self.text_widget.config(yscrollcommand=self.scrollbar.set)

        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def append_log(self, message: str):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, message + "\n")
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)


# --------------------- CarSensorSimulator ---------------------
class CarSensorSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Sensor Simulator")
        self.listeners = []
        self._temp_update_timer = None

        self._setup_ui()

    def _setup_ui(self):
        tk.Button(
            self.root, text="🚗 Car Enters", font=('Arial', 40),
            command=self._car_in
        ).grid(row=0, column=0, columnspan=2, pady=10)

        tk.Button(
            self.root, text="Car Leaves 🚙", font=('Arial', 40),
            command=self._car_out
        ).grid(row=1, column=0, columnspan=2, pady=10)

        tk.Label(self.root, text="Temperature (°C)", font=('Arial', 20)).grid(row=2, column=0, sticky=tk.E)
        self.temp_var = tk.StringVar()
        self.temp_var.trace_add('write', self._on_temp_change)
        tk.Entry(self.root, textvariable=self.temp_var, font=('Arial', 20)).grid(row=2, column=1, sticky=tk.W)

        tk.Label(self.root, text="License Plate", font=('Arial', 20)).grid(row=3, column=0, sticky=tk.E)
        self.plate_var = tk.StringVar()
        tk.Entry(self.root, textvariable=self.plate_var, font=('Arial', 20)).grid(row=3, column=1, sticky=tk.W)

        tk.Button(
            self.root, text="Reset Parking", font=('Arial', 20),
            command=self._reset
        ).grid(row=4, column=1, pady=10)

    @property
    def license_plate(self):
        return self.plate_var.get()

    def register_listener(self, listener):
        if isinstance(listener, CarparkSensorListener):
            self.listeners.append(listener)

    def _car_in(self):
        for listener in self.listeners:
            listener.incoming_car(self.license_plate)

    def _car_out(self):
        for listener in self.listeners:
            listener.outgoing_car(self.license_plate)

    def _on_temp_change(self, *args):
        if self._temp_update_timer:
            self._temp_update_timer.cancel()

        self._temp_update_timer = threading.Timer(0.5, self._send_temperature)
        self._temp_update_timer.start()

    def _send_temperature(self):
        try:
            temp = float(self.temp_var.get())
            for listener in self.listeners:
                listener.temperature_reading(temp)
        except ValueError:
            pass

    def _reset(self):
        for listener in self.listeners:
            if hasattr(listener, 'reset_parking'):
                listener.reset_parking()


# --------------------- Main Program ---------------------
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()

    database = parking_database()

    display = CarparkDisplayManager(root)
    display.data_provider = database
    database._update_display = display.refresh

    log_display = ActivityLogDisplay(root)
    database.set_log_display(log_display.append_log)

    sensor_gui = CarSensorSimulator(tk.Toplevel(root))
    sensor_gui.register_listener(database)

    root.mainloop()
