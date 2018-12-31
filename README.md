# beer-o-tron
Homebrew beer heater controller

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

Developed on Linux Mint 18.1 Cinnamon 64-bit

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
qt-unified-linux-x64-3.0.6-online.run
installed to /opt
chose 5.12

### QtCreator
Struggled to get anything to build & link.

    /usr/bin/ld: cannot find -lGL
Answer: https://stackoverflow.com/questions/18406369/qt-cant-find-lgl-error

We did this:

    sudo ln -s /usr/lib/x86_64-linux-gnu/mesa/libGL.so.1 /usr/lib/libGL.so

