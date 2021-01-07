# Mash-o-matiC
Homebrew beer mash heater controller

This is the software that will run on a RPi with a small touch screen. Application written in Python3, using PyQT, with GUI written in QML (effectively Javascript).

A script running periodically will read temperature from a number of sensors and create a live graph which the application will display in the background. Application will use the temperature readings to decide whether to turn on the heater and pump, according to a pre-set temperature profile (e.g. maintain 66'C for mashing).

After getting nowhere with PyQT and QML, we decided to go with C++/QML for the GUI (almost no C++, mainly QML), piping "messages" (currently TBD, probably simple ASCII) to/from a separate python script which will do the clever controller things.

The problem with PyQT was that we couldn't get the QML to import QT modules. There doesn't seem to be much online help for this - PyQT seems to create applications the old 'designer' way - instantiate widgets in the python and wire up the UI there, rather than letting QML do it. We probably missed a configuration or deployment step but it was taking too long with no results. Since I use Qt/C++/QML for work, a C++ app is a doddle, and the UI aspects of this aren't the interesting bits. With luck the UI will be trivial.

[Messages](messages.md)

[GUI modes](gui_modes.md)

## Ideas
Simple GUI, complicated Python. Use messages from python to create & remove buttons? Or hide & show pre-set buttons? So the GUI has no state and knows nothing about the logic?
Might make Python too complicated. Maybe better to have some operating modes in GUI (setup, run etc) with fixed layouts, then the python would control the mode.

## Notes

Initially developed on Linux Mint 18.1 Cinnamon 64-bit.
Now Linux Mint 20 Cinnamon.

### Pipes and Testing
We decided that the GUI would send and receive messages on stdin and stdout. In the final system it would communicate with the Python core over pipes. This has the benefit of being able to test the GUI by itself from the command line.

At one point I had the GUI talking to <something> in a second terminal, using two named pipes, but I didn't take notes and I can't for the life of me work out what I did. It echoed the output from the GUI, and you could type commands to the GUI.

https://unix.stackexchange.com/questions/53641/how-to-make-bidirectional-pipe-between-two-programs

Open 2 terminals in the Qt build directory. In either, create 2 named pipes. In one, run ??? and in the other run the GUI:

    terminal1 $ mkfifo f1 f2
    terminal1 $ cat >f1 <f2   # this echoes hearbeats back, but you can't type
    terminal1 $ echo >f1 <f2

and

    terminal2 $ ./gui <f1 >f2

then terminal 1 shows output from the GUI (e.g. heartbeats, mode changes) and typing in terminal 1 sends the results to the GUI as though it was the python core.

### Icons
https://material.io/tools/icons/?style=baseline

### Installing PyQt

Software Manager

Python3-pyqt5

PyQt5 exposes the Qt5 API to Python 3. This package contains the following modules:
* QtCore
* QtDBus
* QtDesigner
* QtGui
* QtHelp
* QtNetwork
* QtPrintSupport
* QtTest
* QtWidgets
* QtXml


Python3-pyqt5.qtquick

The QtQuick module of PyQt5 provides a framework for developing applications and libraries with the QML language.

This package contains the Python 3 version of this module.

### Installing Qt (core)
Simple test main.qml wouldn't run so we needed to install Qt as well.
https://www.qt.io/download
Open source version.
qt-unified-linux-x64-4.0.1-online.run
installed to /opt
chose 5.15.2

### QtCreator
Struggled to get anything to build & link.

    /usr/bin/ld: cannot find -lGL
Answer: https://stackoverflow.com/questions/18406369/qt-cant-find-lgl-error

We did this:

    sudo ln -s /usr/lib/x86_64-linux-gnu/mesa/libGL.so.1 /usr/lib/libGL.so

or

    sudo ln -s /usr/lib/x86_64-linux-gnu/libGL.so.1 /usr/lib/libGL.so

### TestStub

Simple test app that can be connected to gui through pipes:
    mkfifo f1 f2
    TestStub >f1 <f2 & cat <f1 >f2
which can inject all types of message, and echoes anything sent back.

