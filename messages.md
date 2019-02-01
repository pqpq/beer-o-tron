# Messages

These are the messages between the Qt GUI and the Python core.

## To GUI

Message|Parameters|Meaning
---|---|---
`hot` | | Sensor temperature is hotter than permitted.
`cold` | | Sensor temperature is colder than permitted.
`ok` | | Sensor temperature is within permitted bounds.
`quit` | | Terminate GUI application
`pump` | [on] | Pump status. Any parameter other than 'on', or no parameter, signifies off.
`heat` | [on] | Heater status. Any parameter other than 'on', or no parameter, signifies off.
`time` | *seconds* | Time update.<br> *seconds* : (int) number of seconds since the run started.
`stop` | | Hide the run timer.
`temp` | *degrees* | Temperature update.<br> *degrees* : (float) current sensor temperature in degrees Centigrade. 
`hearbeat` | | Response to a heartbeat from the GUI. Never sent unrequested.

## From GUI

Message|Parameters|Meaning
---|---|---
`bye` | | GUI is shutting down.
`heartbeat` | | GUI wants to check the core is there.
`set` | *degrees* | Maintain a set temperature.<br> *degrees* : (float) The temperature to maintain in degrees Centigrade. 
`stop` |  | Stop heat and pump immediately.
