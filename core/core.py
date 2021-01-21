#! usr/bin/python3

#######
# TODO

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

# What happens after a preset Profile expires - we need to extend the
# time as temperature readings continue. Maybe this will happen automatically
# because the temperature log will keep growing, and the graph will be
# updated every 10s?

# Tweak gnuplot so trace starts hard on the left side, not off the axis.

# Send temperature to GUI as fast as possible, but only log every 10s ?

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
    """ Get the current time in IS0-8601 format, suitable for including in a file or directory name."""
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

def create_folder_for_path(path):
    if not path.endswith("/"):
        path = path + "/"
    Path(path).mkdir(parents=True, exist_ok=True)
    return path

def create_and_record_run_folder(installation_folder, folder_prefix, logger):
    folder_path = create_folder_for_path(installation_folder + "runs/" + folder_prefix + "_" + datetime_now_string())
    logger.log("Created " + folder_path)
    return folder_path

def sanitized_stem(profile_path):
    stem = Path(profile_path).stem
    return stem.replace(" ", "-")


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
    def __init__(self, path, initial_log = None, log_creation_to_stderr = False):
        parent = Path(path).parent
        Path(parent).mkdir(parents=True, exist_ok=True)
        self.path = path + "_" + datetime_now_string() + ".log"
        self.file = open(self.path, "a+")
        if log_creation_to_stderr:
            sys.stderr.write("Logging to " + self.path + "\n")
        if initial_log is not None:
            # we don't want the time logged against the initial entry
            self.file.write(initial_log + "\n")
            self.file.flush()

    def log(self, text):
        text = datetime.now().strftime("%H:%M:%S") + ", " + text
        if not text.endswith("\n"):
            text = text + "\n"
        self.file.write(text)
        self.file.flush()
        return text

    def error(self, text):
        logged_text = self.log(text)
        sys.stderr.write(logged_text)


class TemperatureLogger(Logger):
    """ A Logger that knows how to log temperatures."""
    def __init__(self, path, temperature_sensor_names):
        super().__init__(path + "temperature", initial_log = "Time, Average, " + ", ".join(temperature_sensor_names))

    def log_temperatures(self, temperatures, average):
        values = [average] + temperatures
        values_string = ", ".join(map(str, values))
        self.log(values_string)


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
        self._graph_data_path = graph_data_path
        self.start_time = datetime.now()
        self.last_change = self.start_time
        self.logger = logger
        if Path(file_path).exists():
            self.profile = json_from_file(self.file_path, self.logger)

    def create_hold_profile(self, temperature, initial_rest_minutes):
        self.profile = {"name": "Hold", "description": "Automatically generated."}
        self.profile["steps"] = [{"start": temperature}, {"rest": initial_rest_minutes}]
        self.__update_generated_files()

    def graph_data_path(self):
        return self._graph_data_path

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
        self.profile["steps"].append({"rest": Hold.rest_additional_minutes})
        self.__update_generated_files()

    def write(self):
        with open(self.file_path, "w+") as f:
            json.dump(self.profile, f, indent=4)

    def write_plot(self):
        """ Write a file containing gnuplot data for the profile."""
        with open(self._graph_data_path, "w+") as f:
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


class GraphWriter:
    """
    Responsible for using gnuplot to generate a graph image for the GUI.

    Use gnuplot to create or update the graph for the Activity.
    The graph has a line for the profile, showing what temperature we
    should be at and a line for the actual temperature.
    As we log the temperature we update the graph so the user can see
    what's going on.
    """
    def __init__(self, logger, graph_output_path, gnuplot_command_file, temperature_log_path, profile_data_path):
        """
        logger: a Logger in case we need to report errors
        graph_output_path : the path for the graph we are creating
        gnuplot_command_file: the file describing how to generate the graph
        temperature_log_path: the path to the temperature log to use for the graph
        profile_data_path: the path to the profile data to use for the graph
        """
        self.logger = logger
        self.temperature_log_path = temperature_log_path
        self.graph_output_path = graph_output_path
        self.command = [
            "gnuplot",
            "-c",
            gnuplot_command_file,
            self.graph_output_path,
            "15",
            "85",
            self.temperature_log_path,
            profile_data_path
        ]

    def path(self):
        return self.graph_output_path

    def write(self):
        if Path(self.temperature_log_path).exists:
            run(self.command)
        else:
            self.logger.error("GraphWriter.write(): no temperature file yet")


class Activity:
    """
    Base class for the activity the program is carrying out.
    There is always an instance of Activity, even when we're not doing anything.
    This means the main loop can always pass relevant events to the Activity
    without testing whether one exists or not (null object pattern).
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
                self.temperature_log.log_temperatures(temperatures, ave)

    def send_updated_graph(self):
        self.graph.write()
        send_message("image " + self.graph.path())

    def is_holding_temperature(self):
        return False

    def is_running_preset(self, preset_profile_name):
        return False


class Idle(Activity):
    """
    An Activity where no temperature is being maintained, but we still send
    the current temperature to the GUI.
    """
    def __init__(self, logger):
        super().__init__(logger)


class Hold(Activity):
    """ An Activity that maintains a fixed temperature hold Profile. """

    # Add time to the current rest so the graph extends into the future a little.
    rest_additional_minutes = 10

    def __init__(self, logger, temperature, run_folder, temperature_sensor_names, gnuplot_command_file):
        """
        logger: a Logger in case we need to report errors
        temperature: the fixed temperature to maintain
        run_folder : the folder for storing all files associated with this run
        temperature_sensor_names: list of sensor names for the temperature log file
        gnuplot_command_file: the file describing how to generate the graph
        """
        super().__init__(logger)
        self.seconds = 0
        self.temperature_log = TemperatureLogger(run_folder, temperature_sensor_names)

        self.profile = Profile(run_folder + "profile.json", run_folder + "profile.dat", logger)
        self.profile.create_hold_profile(temperature, Hold.rest_additional_minutes)

        self.graph = GraphWriter(logger, run_folder + "graph.png", gnuplot_command_file, self.temperature_log.path, self.profile.graph_data_path())

    def is_holding_temperature(self):
        return True

    def tick(self):
        self.seconds = self.seconds + 1
        send_message("time " + str(self.seconds))
        if self.seconds % 60 is 0:
            self.profile.update_rest(additional_minutes = Hold.rest_additional_minutes)

    def change_set_point(self, temperature):
        self.profile.change_set_point(temperature)
        self.send_updated_graph()

    def set_temperatures(self, temperatures):
        super().set_temperatures(temperatures)
        self.send_updated_graph()


class Preset(Activity):
    """ An Activity that runs a preset temperature Profile. """

    def __init__(self, logger, profile, run_folder, temperature_sensor_names, gnuplot_command_file):
        """
        logger: a Logger in case we need to report errors
        profile: path to the file describing to profile
        run_folder : the folder for storing all files associated with this run
        temperature_sensor_names: list of sensor names for the temperature log file
        gnuplot_command_file: the file describing how to generate the graph
        """
        super().__init__(logger)
        self.seconds = 0
        self.temperature_log = TemperatureLogger(run_folder, temperature_sensor_names)

        self.profile = Profile(profile, run_folder + "profile.dat", logger)
        copyfile(profile, run_folder + Path(profile).name)
        self.profile.write_plot()

        self.graph = GraphWriter(logger, run_folder + "graph.png", gnuplot_command_file, self.temperature_log.path, self.profile.graph_data_path())

    def is_running_preset(self, preset_profile_name):
        return preset_profile_name == self.profile.file_path

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
    gnuplot_command_file = installation_path + "graph.plt"

    if not Path(gnuplot_command_file).is_file():
        sys.stderr.write("gnuplot file missing: " + gnuplot_command_file + "\n")
        sys.exit()

    temperature_reader = TemperatureReader()
    temperature_reader.start()

    logger = Logger(log_path + "core", initial_log = "Mash-o-matiC", log_creation_to_stderr = True)

    activity = Idle(logger)

    heard_from_gui = False
    keep_looping = True

    def send_splash():
        send_message("image " + installation_path + "splash.png")

    def update_temperatures():
        nonlocal temperature_reader, activity
        temperatures = temperature_reader.temperatures()
        activity.set_temperatures(temperatures)

    def hold(temperature):
        nonlocal activity
        if activity.is_holding_temperature():
            activity.change_set_point(temperature)
        else:
            run_path = create_and_record_run_folder(installation_path, "set", logger)
            activity = Hold(logger, temperature, run_path, temperature_reader.sensor_names(), gnuplot_command_file)
            update_temperatures()

    def preset(profile_name):
        nonlocal activity
        if not activity.is_running_preset(profile_name):
            run_path = create_and_record_run_folder(installation_path, "run_" + sanitized_stem(profile_name), logger)
            activity = Preset(logger, profile_name, run_path, temperature_reader.sensor_names(), gnuplot_command_file)
            update_temperatures()

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
            # Echo heartbeats so GUI is happy, but don't log them
            send_message(message)
        if command == "idle":
            logger.log(message)
            activity = Idle(logger)
            send_splash()
        if command == "set" and has_parameters:
            logger.log(message)
            temperature = float(parts[1])
            hold(temperature)
        if command == "run" and has_parameters:
            logger.log(message)
            splitbyquotes = message.split('"')
            if len(splitbyquotes) > 1:
                profile_name = splitbyquotes[1]
                preset(profile_name)
        if command == "list":
            Profile.send_list(installation_path, logger)

        nonlocal heard_from_gui
        if not heard_from_gui:
            send_splash()
            heard_from_gui = True

    def do_one_second_actions():
        nonlocal activity
        activity.tick()

    def do_ten_second_actions():
        update_temperatures()

    seconds = 0
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
