# beer-o-tron
Homebrew beer heater controller

This is the software that will run on a RPi with a small touch screen. Application written in Python3, using PyQT, with GUI written in QML (effectively Javascript).

A script running periodically will read temperature from a number of sensors and create a live graph which the application will display in the background. Application will use the temperature readings to decide whether to turn on the heater and pump, according to a pre-set temperature profile (e.g. maintain 66'C for mashing).

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
