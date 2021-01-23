"""
Mash-o-matiC Core.
https://github.com/pqpq/beer-o-tron

GraphWriter class
"""

from pathlib import Path
from subprocess import run


class GraphWriter:
    """
    Responsible for using gnuplot to generate a graph image for the GUI.

    Use gnuplot to create or update the graph for the Activity.
    The graph has a line for the profile, showing what temperature we
    should be at and a line for the actual temperature.
    As we log the temperature we update the graph so the user can see
    what's going on.
    """
    def __init__(self, logger, graph_output_path, gnuplot_command_file, temperature_log_path, profile_data_path, state_log_path):
        """
        logger: a Logger in case we need to report errors
        graph_output_path : the path for the graph we are creating
        gnuplot_command_file: the file describing how to generate the graph
        temperature_log_path: the path to the temperature log to use for the graph
        profile_data_path: the path to the profile data to use for the graph
        state_log_path: the path to the state data to use for the graph
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
        if Path(self.temperature_log_path).is_file():
            run(self.command)
        else:
            self.logger.error("GraphWriter.write(): no temperature file yet")
