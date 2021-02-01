"""
Mash-o-matiC Core.
https://github.com/pqpq/beer-o-tron

DS18B20 temperature sensor management
"""

import threading
import sys
from time import sleep
from pathlib import Path


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
            self.errors = 0

        def read(self, lock):
            try:
                with open(self.path + "/temperature") as f:
                    raw_value = f.read()
                    try:
                        value = float(raw_value)
                    except ValueError:
                        sys.stderr.write("Couldn't parse '" + raw_value + "' for temperature sensor '" + self.name + "'\n")
                        self.errors = self.errors + 1
                    else:
                        lock.acquire()
                        self.value = value / 1000
                        lock.release()
                        self.errors = 0
            except FileNotFoundError:
                sys.stderr.write("Couldn't read sensor '" + self.name + "'\n")
                self.errors = self.errors + 1

        def failed(self):
            return self.errors > 10


    def __init__(self, sensor_names_file):
        self.sensors = []
        self.lock = threading.Lock()
        self.sensor_names_file = sensor_names_file

    def start(self):
        self.__discover_sensors()
        self.thread = threading.Thread(target=TemperatureReader.__thread_function, daemon=True, args=(self,))
        self.thread.start()

    def temperatures(self):
        values = []
        failures = []
        self.lock.acquire()
        for i in self.sensors:
            values.append(i.value)
            if i.failed():
                failures.append(i.name)
        self.lock.release()
        if len(failures):
            raise RuntimeError("Temperature sensor problem: " + ",".join(failures))
        return values

    def sensor_names(self):
        values = []
        self.lock.acquire()
        for i in self.sensors:
            values.append(i.name)
        self.lock.release()
        return values

    def __sensor_nicknames(self):
        nicknames = {}
        if Path(self.sensor_names_file).is_file():
            lines = read_file(self.sensor_names_file)
            for line in lines:
                parts = line.strip().split(" ")
                if len(parts) == 2:
                    nicknames[parts[0]] = parts[1]
        return nicknames

    def __discover_sensors(self):
        nicknames = self.__sensor_nicknames()

        count = read_file(TemperatureReader.one_wire_device_path + "w1_bus_master1/w1_master_slave_count")
        if len(count) > 0 and int(count[0]) == 0:
            raise RuntimeError("No temperature sensors")

        sensors = read_file(TemperatureReader.one_wire_device_path + "w1_bus_master1/w1_master_slaves")

        self.lock.acquire()
        self.sensors.clear()
        for i in sensors:
            name = i.rstrip()
            path = TemperatureReader.one_wire_device_path + name
            if name in nicknames:
                nickname = nicknames[name]
                if nickname is not "":
                    name = nickname
            self.sensors.append(TemperatureReader.Sensor(name, path))
        self.lock.release()

    def __read_sensors(self):
        for i in self.sensors:
            i.read(self.lock)

    def __thread_function(self):
        while True:
            self.__read_sensors()
            sleep(1)
