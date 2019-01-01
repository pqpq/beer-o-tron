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

There are three substates. Initially goes straight to *Set*.

### Change
This state is for setting the temperature to maintain. 

Controller: maintain any previously set temperature.

GUI: 
* Temperature shown in a number spinner, with 1 decimal place. Default temperature is 66.6.
* Spinner + and - buttons should press-and-hold to change rapidly (default behaviour?)
* Tick button for OK -> Run
* X button for cancel -> Run, if previously running. -> Main menu, if we came from there.

### Run
Controller: maintain the temperature setpoint.

GUI:
* Screen press goes to the *Menu* state.

### Menu
Controller: maintain the temperature setpoint.

GUI:
* Change temperature -> Change
* Main menu -> Top level menu
* Large button across bottom part of screen "Emergency Stop"
  * send `stop`
  * -> top level menu? 
  * -> Maybe stay put so you can see temperature graph?
