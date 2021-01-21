"""
Mash-o-matiC Core.
https://github.com/pqpq/beer-o-tron

Utility functions
"""

import sys
from datetime import datetime


def send_message(message):
    try:
        sys.stdout.write(message + '\n')
        sys.stdout.flush()
    except BrokenPipeError:
        pass


def datetime_now_string():
    """ Get the current time in IS0-8601 format, suitable for including in a file or directory name."""
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")
