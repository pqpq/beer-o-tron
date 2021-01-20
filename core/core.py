#! usr/bin/python3

#######
# TODO

# Refactor Activity() classes.
# __init__ for base class?
# break up the other __init__()s - they're a bit big.
# Or split out Profile() class first?

# Split out profile generation, graph generation into a class?
# we're starting to pass around a lot of paths.
# Create it separately and inject into Activity?

# Write the temperature maintainance logic.
# - determine hot/cold/ok
# - GPIO, obviously
# - emit pump and heater status
# - handle 'allstop'

# Log pump / heater on/off in its own file so we can graph it.

# Have a names file for temperature sensors, so we can give them nicknames?

# Always run the pump? It will help to even the temperature top to bottom
# Maybe start off not alway running, and have a good look at the temperature logs,
# so we can see whether there is a real difference.

# Be intelligent about the number of temperature sensors, and send this
# to gnuplot so it uses the right column. Or .... put the average value
# in the first column.

# What happens after a preset Profile expires - we need to extend the
# time as temperature readings continue. Maybe this will happen automatically
# because the temperature log will keep growing, and the graph will be
# updated every 10s?

# Tweak gnuplot so trace starts hard on the left side, not off the axis.

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
import json
from gpiozero import Button
from time import sleep
from pathlib import Path
from datetime import datetime, timedelta
from os import scandir
from shutil import copyfile
from subprocess import run

# Utility functions

def read_file(filename):
    with open(filename) as f:
        return f.readlines()

def send_message(message):
    try:
        sys.stdout.write(message+'\n')
        sys.stdout.flush()
    except BrokenPipeError:
        pass

def datetime_now_string():
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")

def json_from_file(filepath, logger):
    try:
        with open(filepath, "r") as file:
            return json.load(file)
    except:
        logger.error("Problem reading " + filepath)
        logger.error("details: " + str(sys.exc_info()[1]))
    return None

def average(values):
    average = 0.0
    n = len(values)
    if n > 0:
        for v in values:
            average = average + v
        average = average / n
    return average

def log_values_as_csv(log_file, values):
    values_string = ", ".join(map(str, values))
    log_file.log(values_string)

def create_folder_for_path(path):
    if not path.endswith("/"):
        path = path + "/"
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


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
                raw_value = f.read()
                try:
                    value = float(raw_value)
                except ValueError:
                    sys.stderr.write("Couldn't parse '" + rawvalue + "'\n")
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

class Logger:
    """ A simple file based logger. """
    def __init__(self, path):
        parent = Path(path).parent
        Path(parent).mkdir(parents=True, exist_ok=True)
        self.path = path + "_" + datetime_now_string() + ".log"
        self.file = open(self.path, "a+")

    def log(self, text):
        time = datetime.now().strftime("%H:%M:%S")
        if not text.endswith("\n"):
            text = text + "\n"
        self.file.write(time + ", " + text)
        self.file.flush()

    def error(self, text):
        self.log(text)
        sys.stderr.write(text + "\n")


def create_temperature_log(path, temperature_sensor_names):
    path = create_folder_for_path(path)
    temperature_log = Logger(path + "temperature")
    temperature_log.log(", ".join(temperature_sensor_names) + ", average")
    return temperature_log


class Profile():
    """
    Encapsulate a time/temperature profile.

    The profile is the ideal time/temperature relationship that the script
    will try to maintain by measuring the mash temperature and heating it
    when necessary.

    There are two types of profile: preset and hold.

    Preset are created by the user and have an arbitrary number of steps.

    Hold are created by the script, from 'set' messages sent from the GUI
    and are a representation in Profile form of what the user has asked for.
    The simples hold profile has a start temperature followed by a rest
    which extends as time passes.

    Member variables:

    file_path   is the JSON file describing the profile.
                For preset profiles this will have been written by the user.
                For hold profiles this is generated by the code.
    graph_data_path
                is the path of the output file generated when we convert
                the JSON into a time/temperature CSV file for gnuplot.
                For presets this is done once, since the whole profile is
                already known. For a hold profile, the Profile is updated
                as time passes, so the graph needs to be updated frequently
                to keep in sync.
    profile     The JSON representation.
    start_time  When the profile was created. For hold profiles, this is
                used to maintain the rolling rest that terminates the
                profile.
    last_change The last time the hold profile was changed.
    logger      A Logger
    """
    def __init__(self, file_path, graph_data_path, logger):
        self.file_path = file_path
        self.graph_data_path = graph_data_path
        self.start_time = datetime.now()
        self.last_change = self.start_time
        self.logger = logger
        if Path(file_path).exists():
            self.profile = json_from_file(self.file_path, self.logger)

    def create_hold_profile(self, temperature, initial_rest_minutes):
        self.profile = {"name": "Hold", "description": "Automatically generated."}
        self.profile["steps"] = [{"start": temperature}, {"rest": initial_rest_minutes}]

    # This could return a list of tuples so it doesn't have to know about send_message() ?
    @staticmethod
    def send_list(profiles_folder, logger):
        folder = profiles_folder + "profiles/"
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

    def __rest_minutes(self):
        seconds = (datetime.now() - self.last_change).total_seconds()
        return int(round(seconds / 60.0))

    def __update_generated_files(self):
        self.write()
        self.write_plot()

    def __update_rest_step(self, additional_minutes = 0):
        last_step = self.profile["steps"][-1]
        last_step["rest"] = self.__rest_minutes() + additional_minutes

    def update_rest(self, additional_minutes = 0):
        self.__update_rest_step(additional_minutes)
        self.__update_generated_files()

    def change_set_point(self, temperature):
        self.__update_rest_step()
        self.last_change = datetime.now()
        self.profile["steps"].append({"jump": temperature})
        self.profile["steps"].append({"rest": Set.rest_additional_minutes})
        self.__update_generated_files()

    def write(self):
        with open(self.file_path, "w+") as f:
            json.dump(self.profile, f, indent=4)

    def write_plot(self):
        """ Write a file containing gnuplot data for the profile."""
        with open(self.graph_data_path, "w+") as f:
            run_time = self.start_time
            f.write("Time, Temperature\n")
            temperature = 0
            for step in self.profile["steps"]:
                keys = list(step)
                if len(keys) > 0:
                    if keys[0] == "start":
                        temperature = step["start"]
                    if keys[0] == "rest":
                        run_time += timedelta(minutes = step["rest"])
                    if keys[0] == "ramp":
                        run_time += timedelta(minutes = step["ramp"])
                        temperature = step["to"]
                    if keys[0] == "mashout":
                        temperature = step["mashout"]
                        time = run_time.strftime("%H:%M:%S, ")
                        f.write(time + str(temperature) + "\n")
                        run_time += timedelta(minutes = 10)
                    if keys[0] == "jump":
                        temperature = step["jump"]

                    time = run_time.strftime("%H:%M:%S, ")
                    f.write(time + str(temperature) + "\n")
                else:
                    logger.error("Can't make sense of " + str(step))


class Activity:
    """
    Base class for the activity the program is carrying out.
    There is always an instance of Activity, even when we're not doing anything.
    This means the main loop can always pass relevant events to the Activity
    without testing whether one exists or not.
    """
    def __init__(self, logger):
        self.logger = logger
        self.temperature_log = None

    def __del__(self):
        # stop pump & heater?
        send_message("time 0")

    def tick(self):
        pass

    def set_temperatures(self, temperatures):
        if len(temperatures) > 0:
            ave = average(temperatures)
            send_message("temp " + str(ave))
            if self.temperature_log is not None:
                log_values_as_csv(self.temperature_log, temperatures + [ave])

    def update_graph(self):
        """
        Use gnuplot to create or update the graph for this Activity.
        The graph has a line for the profile, showing what temperature we should be at
        and a line for the actual temperature. As we log the temperature we update
        the graph so the user can see what's going on.
        """
        if (Path(self.temperature_log.path).exists):
            command = ["gnuplot",
                       "-c",
                       self.gnuplot_file,
                       self.graph_path,
                       "15",
                       "85",
                       self.temperature_log.path,
                       self.profile.graph_data_path]
            run(command)
        else:
            self.logger.error("Activity.update_graph(): no temperature file yet")

    def send_updated_graph(self):
        self.update_graph()
        send_message("image " + self.graph_path)


class Idle(Activity):
    """
    An Activity where no temperature is being maintained, but we still send
    the current temperature to the GUI.
    """
    def __init__(logger):
        super().__init__(logger)


class Set(Activity):
    """ An Activity that maintains a fixed temperature. """

    # Add time to the current rest so the graph extends into the future a little.
    rest_additional_minutes = 10

    def __init__(self, logger, temperature, path, temperature_sensor_names, gnuplot_file):
        """
        logger: a Logger in case we need to report errors
        temperature: the fixed temperature to maintain
        path : the directory for storing logs etc, associated with the run
        temperature_sensor_names: list of sensor names for the temperature log file
        gnuplot_file: the file describing how to generate the graph
        """
        super().__init__(logger)
        self.seconds = 0
        path = create_folder_for_path(path)
        self.logger.log("Created " + path)
        self.temperature_log = create_temperature_log(path, temperature_sensor_names)

        self.profile = Profile(path + "profile.json", path + "profile.dat", logger)
        self.profile.create_hold_profile(temperature, Set.rest_additional_minutes)
        self.profile.write()

        self.graph_path = path + "graph.png"
        self.profile.write_plot()

        self.gnuplot_file = gnuplot_file

    def tick(self):
        self.seconds = self.seconds + 1
        send_message("time " + str(self.seconds))
        if self.seconds % 60 is 0:
            self.profile.update_rest(additional_minutes = Set.rest_additional_minutes)

    def change_set_point(self, temperature):
        self.profile.change_set_point(temperature)
        self.send_updated_graph()

    def set_temperatures(self, temperatures):
        super().set_temperatures(temperatures)
        self.send_updated_graph()


class Run(Activity):
    """ An Activity that runs a temperature profile. """

    def __init__(self, logger, profile, path, temperature_sensor_names, gnuplot_file):
        """
        logger: a Logger in case we need to report errors
        profile: path to the file describing to profile
        path : the directory for storing logs etc, associated with the run
        temperature_sensor_names: list of sensor names for the temperature log file
        gnuplot_file: the file describing how to generate the graph
        """
        super().__init__(logger)
        self.seconds = 0
        path = create_folder_for_path(path)
        self.logger.log("Created " + path)
        self.temperature_log = create_temperature_log(path, temperature_sensor_names)

        self.profile = Profile(profile, path + "profile.dat", logger)
        copyfile(profile, path + Path(profile).name)

        self.graph_path = path + "graph.png"
        self.profile.write_plot()

        self.gnuplot_file = gnuplot_file

    def tick(self):
        self.seconds = self.seconds + 1
        send_message("time " + str(self.seconds))

    def set_temperatures(self, temperatures):
        super().set_temperatures(temperatures)
        self.send_updated_graph()


def main():

    # should all this be in a big "application" class?
    # then we wouldn't need all these "nonlocal" in the functions.

    installation_path = "/opt/mash-o-matic/"
    log_path = installation_path + "logs/"
    run_path = installation_path + "runs/"
    gnuplot_file = "/home/pi/beer-o-tron/data/graph.plt"

    temperature_reader = TemperatureReader()
    temperature_reader.start()

    logger = Logger(log_path + "core")
    logger.log("Mash-o-matiC")
    sys.stderr.write("Logging to " + logger.path + "\n")

    activity = Idle()

    heard_from_gui = False
    keep_looping = True
    seconds = 0
    poll_period = 0.05
    polls_in_one_second = 1.0 / poll_period
    polls = 0

    def send_splash():
        send_message("image " + installation_path + "splash.png")

    def decode_message(message):
        nonlocal activity, logger, keep_looping, temperature_reader

        parts = message.split()
        if len(parts) == 0:
            return

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
            activity = Idle()
            send_splash()
        if command == "set" and has_parameters:
            logger.log(message)
            temperature = float(parts[1])
            if isinstance(activity, Set):
                activity.change_set_point(temperature)
            else:
                # logic -> util fn()
                path = run_path + "set_" + datetime_now_string()
                activity = Set(logger, temperature, path, temperature_reader.sensor_names(), gnuplot_file)
                temperatures = temperature_reader.temperatures()
                activity.set_temperatures(temperatures)
        if command == "run" and has_parameters:
            logger.log(message)
            splitbyquotes = message.split('"')
            if len(splitbyquotes) > 1:
                profile = splitbyquotes[1]
                if isinstance(activity, Run) and activity.profile.file_path == profile:
                    return
                # put this logic in profile? in a util fn()?
                profile_name = profile.replace(" ", "-")
                stem = Path(profile_name).stem
                path = run_path + "run_" + stem + "_" + datetime_now_string()
                activity = Run(logger, profile, path, temperature_reader.sensor_names(), gnuplot_file)
                temperatures = temperature_reader.temperatures()
                activity.set_temperatures(temperatures)
        if command == "list":
            Profile.send_list(installation_path, logger)

    def do_one_second_actions():
        nonlocal activity
        activity.tick()

    def do_ten_second_actions():
        nonlocal temperature_reader, activity
        temperatures = temperature_reader.temperatures()
        activity.set_temperatures(temperatures)

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
