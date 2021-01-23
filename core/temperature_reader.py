"""
Mash-o-matiC Core.
https://github.com/pqpq/beer-o-tron

DS18B20 temperature sensor management
"""

import threading
import sys
from time import sleep


def read_file(filename):
    with open(filename) as f:
        return f.readlines()


class TemperatureReader:
    """
    A worker thread for reading the DS18B20 temperature sensors.

    The sensor values are updated about once a second by the driver, but
    reading each value (the path/to/devices/name/temperature file) seems
    to take about a second as well. I experimented with select(), but
    even when that said all 4 files were ready to read, it still took
    one second per file to complete the read().
    This led to the requirement for it to be done in a background worker
    thread.
    """

    one_wire_device_path = "/sys/bus/w1/devices/"

    class Sensor:
        """ Encapsulate one temperature sensor."""
        def __init__(self, name, path):
            self.name = name
            self.path = path
            self.value = 0.0

        def read(self, lock):
            with open(self.path + "/temperature") as f:
                raw_value = f.read()
                try:
                    value = float(raw_value)
                except ValueError:
                    sys.stderr.write("Couldn't parse '" + raw_value + "'\n")
                else:
                    lock.acquire()
                    self.value = value / 1000
                    lock.release()

    def __init__(self):
        self.sensors = []
        self.lock = threading.Lock()

    def start(self):
        self.thread = threading.Thread(target=TemperatureReader.__thread_function, daemon=True, args=(self,))
        self.thread.start()

    def temperatures(self):
        values = []
        self.lock.acquire()
        for i in self.sensors:
            values.append(i.value)
        self.lock.release()
        return values

    def sensor_names(self):
        values = []
        self.lock.acquire()
        for i in self.sensors:
            values.append(i.name)
        self.lock.release()
        return values

    def __discover_sensors(self):
        self.sensors.clear()
        sensors = read_file(TemperatureReader.one_wire_device_path + "w1_bus_master1/w1_master_slaves")
        self.lock.acquire()
        for i in sensors:
            name = i.rstrip()
            self.sensors.append(TemperatureReader.Sensor(name, TemperatureReader.one_wire_device_path + name))
        self.lock.release()

    def __read_sensors(self):
        for i in self.sensors:
            i.read(self.lock)

    def __thread_function(self):
        self.__discover_sensors()
        while True:
            self.__read_sensors()
            sleep(1)
