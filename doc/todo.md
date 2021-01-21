# Mash-o-matiC Todo List

- [x] Make sure core doesn't restart when the same `set` is sent - this could be the user checking the details
- [ ] Make sure the core switches to the splash screen when `idle` is sent. Or ... keep the previous graph, so user can see what happened?
- [ ] How do we alert the user the preset has finished?
- [ ] Entry in pre-set file format for final action:
    - heat off? 
    - Maintain mash out at X degrees ?
- [ ] Consider a web interface? Could simply be the graph, no interaction.
- [ ] Can we ever have a GUI mode for entering a new preset?
    - Very convoluted with just 4 buttons.
    - For each point we need temp +/- and time +/-. 
    - Need to be able to add and remove points. 
    - Alphanumeric entry for name and details will be a real chore. On screen KB instead of +/- each char?
- [ ] Instead of wordy description of each profile, we could simply graph it and show that. Tiny icon size graph with no axes, just to get a feel? Or show a bit graph in the background of the confirmation page? Too subtle? Or have 2 columns: words, alongside small graph?
- [ ] Calculate total length of a profile and automatically add this to the description, or have it as a new field in the `preset` message?
- [ ] Every run's data file and final graph must be named with date and time, and kept for auditing. Is this any different to keeping the .../runs/xxx/ directory?
- [ ] Rename `set` and `run` to `hold` and `preset` to match the terminology that has evolved in the Python.
- [ ] Temperature status
    - Even bigger current value?
    - Add desired value on the status line? Its not obvious from the graph. Where would it fit? Get gnuplot to do it somehow?
- [ ] Sliding window for the graph? e.g. only show 1 hour. Show rest in some kind of compressed form? Could output a different file, and plot with a different colour, on different axes that just happen to coincide. Or same axes, but fudge the times so the curve is compressed.
- [ ] Actual sliding window on the GUI - send an image that is wider than 320, and use the middle keys to scroll. Nice idea... hmm.
    - always show right most part
    - middle keys scroll back and forth.
    - after a minute, revert.
    - needs temperature axis on both ends of graph.
    - calculate graph dimension from profile total time.


