"""
Mash-o-matiC Core.
https://github.com/pqpq/beer-o-tron

Logger classes
"""

import sys
from pathlib import Path
from datetime import datetime

from utils import datetime_now_string


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

    def log_values(self, values):
        values_string = ", ".join(map(str, values))
        self.log(values_string)

    def error(self, text):
        logged_text = self.log(text)
        sys.stderr.write(logged_text)


class TemperatureLogger(Logger):
    """ A Logger that knows how to log temperatures."""
    def __init__(self, path, temperature_sensor_names):
        super().__init__(path + "temperature", initial_log = "Time, Average, " + ", ".join(temperature_sensor_names))

    def log_temperatures(self, temperatures, average):
        self.log_values([average] + temperatures)
