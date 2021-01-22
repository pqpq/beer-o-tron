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
from gpiozero import Button
from time import sleep
from pathlib import Path

from profile import Profile
from temperature_reader import TemperatureReader
from graph_writer import GraphWriter
from activity import Idle, Hold, Preset
from logger import Logger
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


def main():

    # should all this be in a big "application" class?
    # then we wouldn't need all these "nonlocal" in the functions.

    installation_path = "/opt/mash-o-matic/"
    log_folder           = installation_path + "logs/"
    profiles_folder      = installation_path + "profiles/"
    gnuplot_command_file = installation_path + "graph.plt"

    if not Path(gnuplot_command_file).is_file():
        sys.stderr.write("gnuplot file missing: " + gnuplot_command_file + "\n")
        sys.exit()

    temperature_reader = TemperatureReader()
    temperature_reader.start()

    logger = Logger(log_folder + "core", initial_log = "Mash-o-matiC", log_creation_to_stderr = True)

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
            run_path = create_and_record_run_folder(installation_path, "hold", logger)
            activity = Hold(logger, temperature, run_path, temperature_reader.sensor_names(), gnuplot_command_file)
            update_temperatures()

    def preset(profile_name):
        nonlocal activity
        if not activity.is_running_preset(profile_name):
            run_path = create_and_record_run_folder(installation_path, "preset_" + sanitized_stem(profile_name), logger)
            activity = Preset(logger, profile_name, run_path, temperature_reader.sensor_names(), gnuplot_command_file)
            update_temperatures()

    def send_list():
        details = Profile.get_list(profiles_folder, logger)
        for d in details:
            send_message("preset \"" + d["filepath"] + "\" \"" + d["name"] + "\" \"" + d["description"] + "\"")

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
