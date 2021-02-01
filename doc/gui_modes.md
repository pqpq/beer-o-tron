# The GUI

## Layout
The current temperature will always be displayed, as this is critical information for any/all modes.
Likewise heat, pump, and communication status will always be displayed.
When the core is maintaining a temperature, the elapsed time is displayed.
These are all shown in a permanent status bar across the top of the screen.

The GUI is never in control of the heater and pump. It simply reflects their state.
It **can** tell the Python core to turn them off though, if the user decides something is
wrong (`allstop`), or when a temerature profile is complete (`idle`).

When required, up to four buttons will be displayed in a row along the bottom of the screen, 
lining up with the physcial buttons on the Pi TFT hat.

The background of the screen is an image that is sent from the Python core. 
The GUI is not in control of this and simply displays what it is told to, so image selection is independent from the GUI state.

## States

The GUI software initialises into the top level state.
States are described below in terms of what the buttons do.
*Action* refers to an optional action that is carried out as soon as the button is pressed, in addition to moving to a new state.
*Send* means send a message to the Python core.

General points:
* For consistency, button 1 should always be *back*, *cancel*, or equivalent, so that the navigation is always *up* the menu hierarchy, away from comitting to an action.
* Similarly, when navigating, button 4 should always be *forwards*, *accept*, or equivalent, so that the navigation is always *down* the menu hierarchy, towards comitting to an action.
* Button 4 should be *Stop* whenever the core is running a program, and whenever there is space in any given state's buttons.
* A state that can't show the *Stop* button should be transient, i.e. one the user is navigating through and wouldn't normally stay in.

### Top level

* All transitions into this state involve sending `idle`, so the core can tell the GUI to display the splash screen *if it wants*.
* Transitioning to *Preset Choose* involves repopulating the list: we clear the local data and send `list` which tells the core to send the list entries. This happens every time so the GUI is effectively stateless w.r.t. the list.
* Pressing buttons 4 and 1 together -> Test mode (sends `testmode` message).

| Button | Icon | Action | Next State |
|--------|------|--------|------------|
| 1      | Thermometer | | Hold Temperature |
| 2      | Timeline | Repopulate list | Preset Choose |
| 3      |      |        |            |
| 4      | Stop | Send `allstop` | |


## Hold Temperature

* Displays the preset temperature in the middle of the screen and allows the user to change it.

| Button | Icon | Action     | Next State |
|--------|------|------------|------------|
| 1      | X    | Send `idle`| Top        |
| 2      | -    | Decrease temperature |  |
| 3      | +    | Increase temperature |  |
| 4      | Tick | Send `hold <temperature>` | Hold Run |

## Hold Run

* Core is holding the set temperature.
* Button 1 allows the user to check the temperature or alter it.
* Button 4 is always present when running, as an "emergency stop"

| Button | Icon | Action | Next State |
|--------|------|--------|------------|
| 1      | Menu |        | Hold Temperature |
| 2      |      |        |            |
| 3      |      |        |            |
| 4      | Stop | Send `allstop` | Top |

## Preset Choose

* Displays a list of presets and allows the user to move up and down the list, to choose one item.

| Button | Icon | Action | Next State |
|--------|------|--------|------------|
| 1      | X    |        | Top        |
| 2      | v    | List down   |            |
| 3      | ^    | List up     |            |
| 4      | Tick | List select | Preset Confirm           |

## Preset Confirm

* Displays the name of the chosen presets, and below it the details, so the user can check it is the right one before confirming the selection.

| Button | Icon | Action | Next State |
|--------|------|--------|------------|
| 1      | Back | Send `idle` | Preset Choose |
| 2      |      |        |            |
| 3      |      |        |            |
| 4      | Tick | Send `preset <preset name>` | Preset Run |

## Preset Run

* Core is maintaining the preset temperature profile.
* Button 1 allows the user to check the profile details.
* Button 4 is always present when running, as an "emergency stop"

| Button | Icon | Action | Next State |
|--------|------|--------|------------|
| 1      | Menu |        | Preset Confirm |
| 2      |      |        |            |
| 3      |      |        |            |
| 4      | Stop | Send `allstop` | Top |


## Test Mode

* Core sends all temperature values which are displayed in a column.
* While pressed, buttons 2 and 3 activate heater and pump, but this is done in the core.

| Button | Icon | Action | Next State |
|--------|------|--------|------------|
| 1      | Back | Send `idle` | Top   |
| 2      | Pump |        |            |
| 3      | Flame |       |            |
| 4      | Stop | Send `allstop` | Top |


## Error Mode

* Mode is automatic entered when `error` message is received
* No way out

| Button | Icon | Action | Next State |
|--------|------|--------|------------|
| 1      |      |        |            |
| 2      |      |        |            |
| 3      |      |        |            |
| 4      |      |        |            |


