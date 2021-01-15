#! usr/bin/python3

"""
Mash-o-matiC Core.

https://github.com/pqpq/beer-o-tron

This is the 'core' code that manages the GPIO, and maintaining whatever temperature
or temperature profile the user has chosen.
This code is what needs to run in order that the thing actually works.
The C++ GUI is just the human interface to this.

"""

import sys
import select
import threading
from gpiozero import Button
from time import sleep
from pathlib import Path
from datetime import datetime

# Utility functions

def read_file(filename):
    with open(filename) as f:
        return f.readlines()

def send_message(message):
    sys.stdout.write(message+'\n')
    sys.stdout.flush()


# Button GPIO

def send_down(button):
    return lambda : send_message("button "+str(button)+" down")

def send_up(button):
    return lambda : send_message("button "+str(button)+" up")
    
button1 = Button(17)
button2 = Button(22)
button3 = Button(23)
button4 = Button(27)

button1.when_pressed = send_down(1)
button1.when_released = send_up(1)
button2.when_pressed = send_down(2)
button2.when_released = send_up(2)
button3.when_pressed = send_down(3)
button3.when_released = send_up(3)
button4.when_pressed = send_down(4)
button4.when_released = send_up(4)


# DS18B20 temperature sensor management

class TemperatureReader:
    """
    A worker thread for reading the temperature sensors.

    The sensor values are updated about once a second by the driver, but
    reading each value (the path/to/devices/name/temperature file) seems
    to take about a second as well. I experimented with select(), but
    even when that said all 4 files were ready to read, it still took
    one second per file to complete the read().
    This lead to the requirement for it to be done in a background worker
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
                value = f.read()
                lock.acquire()
                self.value = float(value) / 1000
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

class Logger:

    # TODO - mini class for logfile: path, file, log()

    def __init__(self, path):
        self.path = path
        if self.path.endswith('/'):
            self.path = self.path[:-1]
        Path(self.path).mkdir(parents=True, exist_ok=True)
        self.main_log_file = None
        self.main_log_file = self.__create("core")
        self.temperature_log_file = None
        self.log("Mash-o-matiC")

    def __del__(self):
        self.main_log_file.flush()
        self.main_log_file.close()

    def __log(self, file, text):
        if file is not None:
            file.write(text + "\n")
            file.flush()

    def log(self, text):
        self.__log(self.main_log_file, text)

    def start_temperature_log(self, sensors):
        if self.temperature_log_file is not None:
            self.temperature_log_file.close()
        self.temperature_log_file = self.__create("temperature")
        self.__log(self.temperature_log_file, ','.join(sensors))

    def log_temperatures(self, values):
        if self.temperature_log_file is None:
            self.log("log_temperatures() called before start_temperature_log()!")
            self.start_temperature_log("(no sensors)")
        values_string = ','.join(map(str, values))
        self.__log(self.temperature_log_file, values_string)

    def __create(self, filename):
        now = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        path = self.path + "/" + filename + "_" + now + ".log"
        self.log("Creating " + path)
        return open(path, "a+")

def main():

    installation_path = "/opt/mash-o-matic/"

    heartbeat_count = 0

    def decode_message(message):
        # Echo heartbeats so GUI is happy
        if (message.startswith("heartbeat")):
            send_message(message)
            nonlocal heartbeat_count
            if heartbeat_count == 0:
                send_message("image " + installation_path + "splash.png")
            heartbeat_count = heartbeat_count + 1

    temperature_reader = TemperatureReader()
    temperature_reader.start()
    
    logger = Logger(installation_path + "logs/")
    logger.start_temperature_log(temperature_reader.sensor_names())

    count = 0
    seconds = 0

    while True:
        # Non-blocking check for whether there's anything to read on stdin
        # select() only signals stdin when ENTER is pressed, so when
        # this fires, the whole line is available, so we must use readline()
        if select.select([sys.stdin], [], [], 0)[0] == [sys.stdin]:
            decode_message(sys.stdin.readline())

        sleep(0.05)

        count = count + 1
        if count == 20:
            count = 0

            seconds = seconds + 1
            send_message("time " + str(seconds))

            temperatures = temperature_reader.temperatures()
            if len(temperatures) > 0:
                average_temperature = 0.0
                logger.log_temperatures(temperatures)
                for i in temperatures:
                    average_temperature = average_temperature + i
                average_temperature = average_temperature / len(temperatures)
                send_message("temp " + str(average_temperature))

if __name__ == "__main__":
    sys.stderr.write("Mash-o-matiC core\n")
    main()
