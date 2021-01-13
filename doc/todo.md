# Mash-o-matiC Todo List

- [ ] Make sure core doesn't restart when the same `set` is sent - this could be the user checking the details
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
- [ ] Every run's data file and final graph must be named with date and time, and kept for auditing.
