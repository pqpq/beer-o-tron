# Messages

These are the messages between the Qt GUI and the Python core.

## To GUI

Message|Parameters|Meaning
---|---|---
`hot` | | Sensor temperature is hotter than permitted.
`cold` | | Sensor temperature is colder than permitted.
`ok` | | Sensor temperature is within permitted bounds.
`pump` | [on] | Pump status. Any parameter other than 'on', or no parameter, signifies off.
`heat` | [on] | Heater status. Any parameter other than 'on', or no parameter, signifies off.
`time` | *seconds* | Time update.<br> *seconds* : (int) number of seconds since the run started.<br>A value of 0 indicates no run is in progress and the time can be hidden.
`temp` | *degrees* | Temperature update.<br> *degrees* : (float) current sensor temperature in degrees Centigrade. 
`heartbeat` | | Response to a heartbeat from the GUI. Never sent unrequested.
`preset` | *id* *name* *details* | A pre-set temperature profile.<br>*id* is the unique identifier, delimited with double quotes.<br>*name* is a short name delimited with double quotes.<br>*details* is a longer description delimited with double quotes.
`button` | *number* [up&#124;down] | Button *number* is pressed or released.<br>With neither 'up' or 'down', a momentary press is simulated.<br>Buttons are numbered 1-4, from left to right.
`image` | *filename* | Set the background image to *filename*.<br>Resent to reload the same image whenever it changes.
`testshow`| *text* | Arbitrary text to display on the test page.<bt>Delimited in double quotes. May contain &lt;br&gt; line breaks.

## From GUI

Message|Parameters|Meaning
---|---|---
`bye` | | GUI is shutting down.
`heartbeat` | | GUI wants to check the core is there.
`hold` | *degrees* | Hold a set temperature.<br> *degrees* : (float) The temperature to maintain in degrees Centigrade. 
`allstop` |  | Stop heat and pump immediately.
`list` |  | Request the list of pre-set profiles.<br>When this is sent the GUI clears its list, so any `preset` messages will populate the new list rather than overwrite the old.
`preset` | *id* | Run the pre-set temperature profile called *id* (delimited in double quotes).
`idle` | | Stop the preset or set temperature program.
