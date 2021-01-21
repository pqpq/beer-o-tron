# Temperature Profile File Format

Profiles are described in JSON as this is trivial to read and write from Python.


    {
        "name": "example",
        "description": "A sentence or two describing the profile.<br>Can have breaks - it is displayed over several lines.",
        "steps" : [
            { "start": 40.0 }
            { "rest": 30 }
            { "ramp": 15, "to": 55.0 }
            { "rest": 20 }
            { "ramp": 10, "to": 65.0 }
            { "rest": 45 }
            { "mashout": 75 }
        ]
    }


Contents are:
* A short name (listed in the GUI). E.g "Wheat beer"
* A description. This is a few sentences, shown to the user in the GUI so they don't have to guess what the short name entails, before committing to a run.
* The steps:


| Step      | Value         | Additional values | Action  |
|:---------:|:-------------:|:-----------------:|:--------|
| `start`   | temperature   |                   | Initial temperature |
| `rest`    | minutes       |                   | Maintain the previous temperature |
| `ramp`    | minutes       | `to` temperature  | Ramp from previous temperature to the given value, over the given interval |
| `jump`    | temperature   |                   | Immediately jump to the new temperature |
| `mashout` | temperature   |                   | Jump to the new temperature and hold it indefinitely |



## Ramping the temperature

You can't just go from one temperature to another as fast as possible, as the rate of change might be too high (if the heater is powerful enough). The rule of thumb in all the brewing books is 1 degree per minute. I don't really know why. Possibly because if you exceed this you risk localised boiling which denatures the enzymes. I don't really see why you can't exceed this if you have the right heating technology. Maybe the enzymes don't like sudden change?

Should we enforce this? But what do we do if a file is illegal?

Maybe we can't enforce it, and simple do whatever the file says. Garbage in garbage out. It is unlikely the kit will be able to put in sufficient heat for it to be a problem anyway.

If we don't reach the desired temperature by the required time, presumably we extend the step. We can't really move on! The graph will show the user what has happened. We'll have to see how things behave in real life. Extending might be hard to do, especially deciding whether or not you've reached the required value properly (consider noise).

