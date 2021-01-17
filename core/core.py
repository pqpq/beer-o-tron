#! usr/bin/python3

"""
Mash-o-matiC Core.

https://github.com/pqpq/beer-o-tron

This is the 'core' code that manages the GPIO, and maintaining whatever temperature
or temperature profile the user has chosen.
This code is what needs to run in order that the thing actually works.
The C++ GUI is just the human interface to this.

Thoughts/Todos:
class Run()
    init records time, creates run folder, with log and graph. Copy profile file?
    poll updates this and sends 'time' message
    descructor sends 'time 0'?

Have a names file for temperature sensors, so we can give them nicknames?

"""

import sys
import select
import threading
import json
from gpiozero import Button
from time import sleep
from pathlib import Path
from datetime import datetime
from os import scandir
from shutil import copyfile

# Utility functions

def read_file(filename):
    with open(filename) as f:
        return f.readlines()

def send_message(message):
    sys.stdout.write(message+'\n')
    sys.stdout.flush()

def datetime_now_string():
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")

def json_from_file(filepath, logger):
    try:
        file = open(filepath, "r")
        return json.load(file)
    except:
        logger.error("Problem reading " + filepath)
        logger.error("details: " + str(sys.exc_info()[1]))
    return None

def send_profiles(path, logger):
    folder = path + "profiles/"
    with scandir(folder) as it:
        for entry in it:
            if entry.is_file():
                filepath = folder + entry.name
                profile = json_from_file(filepath, logger)
                if profile is not None:
                    try:
                        send_message("preset \"" + filepath + "\" \"" + profile["name"] + "\" \"" + profile["description"] + "\"")
                    except AttributeError:
                        logger.error("Missing attributes in " + filepath)
                        logger.error(str(profile))

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
    """ Encapsulate general logging. """
    class LogFile:
        def __init__(self, path):
            self.path = path + "_" + datetime_now_string() + ".log"
            self.file = open(self.path, "a+")

        def log(self, text):
            time = datetime.now().strftime("%H:%M:%S")
            if not text.endswith("\n"):
                text = text + "\n"
            self.file.write(time + ", " + text)
            self.file.flush()

    def __init__(self, path):
        self.path = path
        parent = Path(path).parent
        sys.stderr.write("path " + path + "\n")
        sys.stderr.write("parent " + str(parent) + "\n")
        Path(parent).mkdir(parents=True, exist_ok=True)
        self.log_file = Logger.LogFile(self.path)

    def log(self, text):
        self.log_file.log(text)

    def error(self, text):
        self.log(text)
        sys.stderr.write(text + "\n")


# Always run the pump? It will help to even the temperature top to bottom
# Maybe start off not alway running, and have a good look at the temperature logs,
# so we can see whether there is a real difference.
class Run:
    """ Details about one run. """
    def __init__(self, path, temperature_sensor_names):
        """ path is the directory for the run, not a file name."""
        self.seconds = 0
        self.path = path
        if not self.path.endswith("/"):
            self.path = self.path + "/"
        Path(self.path).mkdir(parents=True, exist_ok=True)
        self.temperature_log = Logger(self.path + "temperature")
        self.temperature_log.log(", ".join(temperature_sensor_names) + ", average")
        #create graph and send to gui?

    def __del__(self):
        # stop pump & heater?
        send_message("time 0")

    # derived class? compose an implementer?
    # If we're running a profile, what should we do?
    def set(self, temperature):
        # log change of temperature
        # if we're already running, just change it
        sys.stderr.write("Run.set() " + str(temperature) + "\n")

    # derived class? compose an implementer?
    # If we're running a set temperature, what should we do?
    def profile(self, profile):
        # check we haven't already got a profile - should create a new run for a new profile
        # log profile details
        sys.stderr.write("Run.profile() " + profile + "\n")
        copyfile(profile, self.path + Path(profile).name)

    def tick(self):
        self.seconds = self.seconds + 1
        send_message("time " + str(self.seconds))

    def temperature(self, temperatures):
        if len(temperatures) > 0:
            average = 0.0
            for t in temperatures:
                average = average + t
            average = average / len(temperatures)

            values_string = ", ".join(map(str, temperatures))
            self.temperature_log.log(values_string + ", " + str(average))
            send_message("temp " + str(average))

        # determine whether we are hot, cold or ok - send changes to gui
        # turn heater on/off
        # update graph and send image to gui


def main():

    # should all this be in a big "application" class?
    # then we wouldn't need all these "nonlocal" in the functions.

    installation_path = "/opt/mash-o-matic/"
    log_path = installation_path + "logs/"
    run_path = installation_path + "runs/"

    temperature_reader = TemperatureReader()
    temperature_reader.start()

    logger = Logger(log_path + "core")
    logger.log("Mash-o-matiC")
    sys.stderr.write("Logging to " + logger.log_file.path + "\n")

    heard_from_gui = False

    # implement a null object for this so we always have a valid Run object
    run = None

    keep_looping = True

    def send_splash():
        send_message("image " + installation_path + "splash.png")

    def decode_message(message):
        nonlocal run, logger, keep_looping, temperature_reader
        parts = message.split()
        command = parts[0]
        has_parameters = len(parts) > 1

        if command == "bye":
            logger.log(message)
            keep_looping = False
        if command == "heartbeat":
            # Echo heartbeats so GUI is happy
            send_message(message)
            nonlocal heard_from_gui
            if not heard_from_gui:
                send_splash()
                heard_from_gui = True
        if command == "idle":
            logger.log(message)
            run = None
            send_splash()
        if command == "set" and has_parameters:
            logger.log(message)
            if run is None:
                run = Run(run_path + "set_" + datetime_now_string(), temperature_reader.sensor_names())
            run.set(float(parts[1]))
        if command == "run" and has_parameters:
            logger.log(message)
            splitbyquotes = message.split('"')
            if len(splitbyquotes) > 1:
                profile = splitbyquotes[1].replace(" ", "-")
                stem = Path(profile).stem
                run = Run(run_path + "run_" + stem + "_" + datetime_now_string(), temperature_reader.sensor_names())
                run.profile(profile)
        if command == "list":
            send_profiles(installation_path, logger)

    seconds = 0

    def do_one_second_actions():
        nonlocal run
        if run is not None:
            run.tick()

    def do_ten_second_actions():
        nonlocal temperature_reader, run
        if run is not None:
            temperatures = temperature_reader.temperatures()
            run.temperature(temperatures)

    poll_period = 0.05
    polls_in_one_second = 1.0 / poll_period
    polls = 0

    while keep_looping:
        # Non-blocking check for whether there's anything to read on stdin
        # select() only signals stdin when ENTER is pressed, so when
        # this fires, the whole line is available, so we must use readline()
        if select.select([sys.stdin], [], [], 0)[0] == [sys.stdin]:
            decode_message(sys.stdin.readline())

        sleep(poll_period)

        polls = polls + 1
        if polls >= polls_in_one_second:
            polls = 0
            seconds = seconds + 1
            do_one_second_actions()
            if seconds % 10 == 0:
                do_ten_second_actions()


if __name__ == "__main__":
    sys.stderr.write("Mash-o-matiC core\n")
    main()
