# GUI Modes

## Startup
Initial state.

Controller: no heat or pump.

Background: splash screen

GUI: simple menu
* Set temperature
* Presets
* Create profile

## Set Temperature
Controller: maintain a set temperature. 

Background: graph showing temperature history.

There are two substates. Initially goes straight to *Set*.

### Set
This state is for setting the temperature to maintain. 

Controller: maintain any previously set temperature.

GUI: 
* Temperature shown in a number spinner, with 1 decimal place. Default temperature is 66.6.
* Spinner + and - buttons should press-and-hold to change rapidly (default behaviour?)
* Tick button for OK
* X button for cancel.

### Run
Controller: maintain the temperature setpoint.

GUI:
* Return button to go back to top level menu.
* Screen press goes to the *Set* state.
