# Test Results

These graphs are what are sent to the GUI, so are 320x240, with no horizontal axis values (because there isn't the screen space).
* The green/brown line is the desired profile. 
* The black line is the average temperature.
* There are 4 coloured dotted lines showing the individual sensor values, but these tend to just make the black line look messy.
* The orange blocks show when the heater is on.

## Initial tests

### In air
Water in the heating loop, but the loop in air, so not damped by a large mass of water.

![Test in air](air_test.png)

Undamped, the temperature overshoots due to the slow response of the temperature sensors. This is to be expected and not a problem

### In water
In 10l of water

![Test in water](water_test.png)

From the logged data, the gradient from 20&deg; to 40&deg; is exactly 1&deg;/minute.

## Temperature values

4 temperature sensors, 1 near the top, 1 near the bottom, and 2 just dangling:

Stirred water to ensure even temperature:
* Black electronic thermometer (0.5&deg; accuracy?) 58.4
* Average 57.7&deg;, with <= 0.5&deg; between all 4 values
* Seems to be reading 0.7&deg; low

Another test, again after stirring:
* Glass thermometer 49.5&deg;
* Average 48.8&deg; (values 48.75, 48.50, 48.69, 49.69)
* Seems to be reading 0.6&deg; low.

Although accuracy of a fraction of a degree isn't required, this does indicate that altering the code to heat until its at the target temperature, rather than 0.5&deg; below, wouldn't hurt.

## First proper profile run

10 litres of water in insulated mash tun but with lid off.

![Wheat profile test run](test1.png)

Points:
* It can't quite heat at 1&deg;/minute, but its not far off.
* When trying to get to 75&deg;, the thermal cut out did its job and didn't reset before I stopped the test. With 65&deg;+ water in the loop, and adding 800W, the hot water was **too** hot!
* At this point the code is saying `cold` (to the GUI), and heating, when, `t <= target - 0.5` and saying `hot` when `t > target + 0.5`.
* The graph isn't detailed enough to see, but when holding 40&deg; it hovers around t - 0.5.

## Conclusions so far

* If we leave the pump running, the coil will even out the temperature difference from top to bottom of the mash so we can probably get away with 1 sensor placed away from the coil.
* Safety cut out has too low temperature. It turns out to have been only 70&deg;, so will try a 90&deg; part. If these don't work it will have to be moved away from the element, but the point being where it is now, is to sense overheating when the pump fails.
* Some experiments with different control algorithms just lead to large overshoots, so we will stick with the simple "heat when t <= target - 0.5". Tests indicate hovering at 0.5&deg; low is fine as we're under reading by 0.5 to 0.7.
* There is a lag created by having the temperature sensor in the mash away from the coil - it is measuring the temperature as convected away from the coil.

## More tests

I tried the 90&deg; cutout, but instead of cutting the power, the water boiled and started spurting from the overflow bottle so I panicked and switched it off. Need to do a proper test. At least it can hold 75&deg; now.

Looking at the results from 4 temperature sensors in different places, and comparing them to the glass and electronic thermometers (used to produce the numbers above), I concluded that one sensor placed higher up, near the tube, would be good enough, so this is the final configuration.

After properly assembling everything onto the mash tun lid I ran some more tests with the lid on.
This was with 9l of water, and the loop which displaces another litre, bringing the level quite close to the top.

First, a proper profile:

![Full profile test run](wheat_test.png)

Then I left it on, but with the pump disconnected, to record the water cooling. This is over 9.5 hours!

![Cooling curve](cooling_curve.png)

