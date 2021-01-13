# Temperature Profile File Format

*Todo*

We need a file format for non-trivial mash profiles:

* Short name (listed in the GUI). E.g "Wheat beer"
* Details. A few sentences, shown to the user in the GUI so they don't have to guess what the short name entails, before committing to a run. E.g. "40' rest for 30mins"
* Data points
    * Desired temperature, and how long to hold it
    * Ramps: start and end temperature, and how long to take. 
* Some established format like XML? Overly complex?
* JSON? Bit lighter than XML, and easier to read

## Everything as (incremental time/temperature) pairs

    {
        "name": "string parsed as name",
        "description": "string parsed as description",
        "points" : [

Get to the initial temperature as fast as possible:

            { "minutes": 0, "temperature": 40.0 },

30 minute rest. Its only a rest because the `temperature` is the same as the previous step. The code doesn't interpret it as such, it simply interpolates the required temperature every unit of time, and tries to get the actual temperature to that value.

            { "minutes": 30, "temperature": 40.0 },

15 minute ramp up to 55 degrees.

            { "minutes": 15, "temperature": 55.0 },

20 minute rest

            { "minutes": 20, "temperature": 55.0 },

etc...

            { "minutes": 10, "temperature": 65.0 },
            { "minutes": 45, "temperature": 65.0 },
            { "minutes": 10, "temperature": 75.0 },
        ]
    }

## Named actions

Would it be clearer if each action had its own name, rather than everything being a temperature point? Quite possibly. This also allows new kinds of step to be added in the future.

e.g.:

    {
        "name": "example",
        "description": "format with named actions",
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

* start : get to this temperature ASAP
* rest : obvious
* ramp : obvious
* mashout: ramp to temperature ASAP and hold indefinitely


## Ramping the temperature

You can't just go from one temperature to another as fast as possible, as the rate of change might be too high (if the heater is powerful enough). The rule of thumb in all the brewing books is 1 degree per minute. I don't really know why. Possibly because if you exceed this you risk localised boiling which denatures the enzymes. I don't really see why you can't exceed this if you have the right heating technology. Maybe the enzymes don't like sudden change?

Should we enforce this? But what do we do if a file is illegal?

Maybe we can't enforce it, and simple do whatever the file says. Garbage in garbage out. It is unlikely the kit will be able to put in sufficient heat for it to be a problem anyway.

If we don't reach the desired temperature by the required time, presumably we extend the step. We can't really move on! The graph will show the user what has happened.
