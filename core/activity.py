"""
Mash-o-matiC Core.
https://github.com/pqpq/beer-o-tron

Activity classes
"""

from pathlib import Path
from shutil import copyfile

from profile import Profile             # inject this dependency!
from logger import TemperatureLogger    # inject this dependency!
from graph_writer import GraphWriter    # inject this dependency!

from utils import send_message


def average(values):
    average = 0.0
    n = len(values)
    if n > 0:
        for v in values:
            average = average + v
        average = average / n
    return average


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
            self.profile.update_rest()

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
