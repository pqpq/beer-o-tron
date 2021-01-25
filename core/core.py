#! usr/bin/python3

#######
# TODO

# Consider an Activity class for test mode.

# Have a names file for temperature sensors, so we can give them nicknames?

# Always run the pump? It will help to even the temperature top to bottom
# Maybe start off not alway running, and have a good look at the temperature logs,
# so we can see whether there is a real difference.

# What happens after a preset Profile expires - we need to extend the
# time as temperature readings continue. Maybe this will happen automatically
# because the temperature log will keep growing, and the graph will be
# updated every 10s?

# Send temperature to GUI as fast as possible, but only log every 10s ?

# Add profile step "off"? Can acheive this by mashout with a low value,
# but that shows on the graph.

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
from gpiozero import Button, LED
from time import sleep
from pathlib import Path
from shutil import copyfile

from profile import Profile
from temperature_reader import TemperatureReader
from graph_writer import GraphWriter
from activity import Idle, Hold, Preset, Activity
from logger import Logger, TemperatureLogger
from utils import send_message, datetime_now_string


# Utility functions

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


# GPIO

button1 = Button(17)
button2 = Button(22)
button3 = Button(23)
button4 = Button(27)

heater = LED(20)
pump = LED(21)

def send_down(button):
    return lambda : send_message("button "+str(button)+" down")

def send_up(button):
    return lambda : send_message("button "+str(button)+" up")

button1.when_pressed = send_down(1)
button1.when_released = send_up(1)
button2.when_pressed = send_down(2)
button2.when_released = send_up(2)
button3.when_pressed = send_down(3)
button3.when_released = send_up(3)
button4.when_pressed = send_down(4)
button4.when_released = send_up(4)

def turn_heater_on():
    heater.on()
    send_message("heat on")

def turn_heater_off():
    heater.off()
    send_message("heat off")

def turn_pump_on():
    pump.on()
    send_message("pump on")

def turn_pump_off():
    pump.off()
    send_message("pump off")

def all_off():
    heater.off()
    pump.off()
    send_message("heat off")
    send_message("pump off")


# Test mode

test_mode = False

def enter_test_mode():
    global test_mode
    if not test_mode:
        test_mode = True
        button2.when_pressed = turn_pump_on
        button2.when_released = turn_pump_off
        button3.when_pressed = turn_heater_on
        button3.when_released = turn_heater_off

def leave_test_mode():
    global test_mode
    if test_mode:
        test_mode = False
        button2.when_pressed = send_down(2)
        button2.when_released = send_up(2)
        button3.when_pressed = send_down(3)
        button3.when_released = send_up(3)

def send_temperature_debug(temperature_reader):
    names = temperature_reader.sensor_names()
    values = temperature_reader.temperatures()
    lines = []
    for n, v in zip(names, values):
        lines.append("" + n + " {:.2f}".format(v))
    message = "testshow \"" + "<br>".join(lines) + "\""
    send_message(message)


def main():

    # should all this be in a big "application" class?
    # then we wouldn't need all these "nonlocal" in the functions.

    installation_path    = "/opt/mash-o-matic/"
    log_folder           = installation_path + "logs/"
    profiles_folder      = installation_path + "profiles/"
    gnuplot_command_file = installation_path + "graph.plt"

    all_off()

    if not Path(gnuplot_command_file).is_file():
        sys.stderr.write("gnuplot file missing: " + gnuplot_command_file + "\n")
        sys.exit()

    temperature_reader = TemperatureReader()
    temperature_reader.start()

    logger = Logger(log_folder + "core", initial_log = "Mash-o-matiC", log_creation_to_stderr = True)
    state_logger = None

    activity = Idle(logger)

    heard_from_gui = False
    keep_looping = True

    def send_splash():
        send_message("image " + installation_path + "splash.png")

    def update_temperatures():
        nonlocal temperature_reader, activity
        temperatures = temperature_reader.temperatures()
        target, state = activity.set_temperatures(temperatures)
        if state == Activity.State.HOT:
            send_message("hot")
            turn_heater_off()
            # start timer to turn pump off after a minute or something?
        if state == Activity.State.COLD:
            send_message("cold")
            turn_pump_on()
            turn_heater_on()
        if state == Activity.State.OK:
            send_message("ok")
            turn_heater_off()
            # timer?
        if state_logger is not None:
            state_logger.log_values([target, 1 if heater.is_lit else 0, 1 if pump.is_lit else 0])
        activity.send_updated_graph()

    def hold(temperature):
        nonlocal activity, state_logger
        if activity.is_holding_temperature():
            activity.change_set_point(temperature)
        else:
            run_folder = create_and_record_run_folder(installation_path, "hold", logger)

            temperature_logger = TemperatureLogger(run_folder, temperature_reader.sensor_names())
            state_logger = Logger(run_folder + "state", initial_log = "Time, Target, Heater, Pump")

            profile = Profile(run_folder + "profile.json", run_folder + "profile.dat", logger)
            profile.create_hold_profile(temperature, Hold.rest_additional_minutes)

            graph_writer = GraphWriter(logger, run_folder + "graph.png", gnuplot_command_file, temperature_logger.path, profile.graph_data_path(), state_logger.path)

            activity = Hold(logger, profile, temperature_logger, graph_writer)
        update_temperatures()

    def preset(profile_name):
        nonlocal activity, state_logger
        if not activity.is_running_preset(profile_name):
            run_folder = create_and_record_run_folder(installation_path, "preset_" + sanitized_stem(profile_name), logger)

            temperature_logger = TemperatureLogger(run_folder, temperature_reader.sensor_names())
            state_logger = Logger(run_folder + "state", initial_log = "Time, Target, Heater, Pump")

            copyfile(profile_name, run_folder + Path(profile_name).name)
            profile = Profile(profile_name, run_folder + "profile.dat", logger)
            profile.write_plot()

            graph_writer = GraphWriter(logger, run_folder + "graph.png", gnuplot_command_file, temperature_logger.path, profile.graph_data_path(), state_logger.path)

            activity = Preset(logger, profile, temperature_logger, graph_writer)
            update_temperatures()

    def send_list():
        details = Profile.get_list(profiles_folder, logger)
        for d in details:
            send_message("preset \"" + d["filepath"] + "\" \"" + d["name"] + "\" \"" + d["description"] + "\"")

    def go_to_idle():
        nonlocal activity, state_logger
        all_off()
        activity = Idle(logger)
        state_logger = None
        send_splash()
        send_message("ok")
        leave_test_mode()

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
            go_to_idle()
        if command == "hold" and has_parameters:
            logger.log(message)
            temperature = float(parts[1])
            hold(temperature)
        if command == "preset" and has_parameters:
            logger.log(message)
            splitbyquotes = message.split('"')
            if len(splitbyquotes) > 1:
                profile_name = splitbyquotes[1]
                preset(profile_name)
        if command == "list":
            send_list()
        if command == "allstop":
            all_off()   # do this first, before complex functions that might throw exceptions
            logger.log(message)
            go_to_idle()
        if command == "testmode":
            logger.log(message)
            go_to_idle()
            enter_test_mode()

        nonlocal heard_from_gui
        if not heard_from_gui:
            send_splash()
            heard_from_gui = True

    def do_one_second_actions():
        if test_mode:
            send_temperature_debug(temperature_reader)
        else:
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
    try:
        main()
        all_off()
    except:
        all_off()
        raise
