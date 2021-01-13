# History of Mash-o-matiC

*Although git stores the history of this documentation, I've kept old notes and the original thoughts here since they're useful background to the project.*

The project started out being called the *Beer-o-tron*. It might even have become the *Beer-o-tron 5000* or something similarly silly and retro sci-fi. But it doesn't make beer. It only helps with one of the processes: [mashing](https://en.wikipedia.org/wiki/Mashing). So a pun on mashing was more appropriate, and Mash-o-matiC sounds like mathematics, so here we are. For some reason I had always pictured a logo like the names on [50's American cars](https://www.logodesignlove.com/vintage-vehicle-logotypes), and/or [Googie architecture](https://en.wikipedia.org/wiki/Googie_architecture), hence the '-o-' bit, and the splash screen logo.

## Hardware

The first steps were to investigate how to make the hardware. We bought a few of the key components and [tested them](https://shed666.wordpress.com/2015/01/25/water-heater-testing/) then made a [prototype housing](https://shed666.wordpress.com/2015/01/08/water-heater-housing/).

After this I made a heating coil out of 22mm pipe, got a larger element (800W, IIRC) and made the full loop (not documented yet).

I also got a 12v 3A PSU and made a small Veroboard to piggy back on it:
* 12v supply to pump
* Step down to 5v to power the RPi
* SCR to control the heating element
* Terminals to connect to RPi GPIO

I'm going to have to reverse engineer this as I made it at least 2 years ago, and I've forgotten the details!

## Software

This project has been sporadically active for many years. The original plan was to do everything in Python, partly as an educational project with our kids, and partly for me to refresh my Python knowledge. 

We started out with PyQT and QML, but quickly got nowhere. I decided to go with C++/QML for the GUI (almost no C++, mainly QML), piping messages (simple text strings) to/from a separate python script which will do the clever controller things. The C++ side is my day job so not much of a challenge. The interesting bit is the Python.

The problem with PyQT was that we couldn't get the QML to import QT modules. There doesn't seem to be much online help for this - PyQT seems to create applications the old 'designer' way - instantiate widgets in the python and wire up the UI there, rather than letting QML do it. We probably missed a configuration or deployment step but it was taking too long with no results. 

Developed started on Linux Mint 18.1 Cinnamon 64-bit. Now it is on Linux Mint 20 Cinnamon.

### Initial Ideas
* Simple GUI, complicated Python. 
* Use messages from Python to create & remove buttons? Or hide & show pre-set buttons? So the GUI has no state and knows nothing about the logic?
Might make Python too complicated. Maybe better to have some operating modes in GUI (setup, run etc) with fixed layouts, then the Python would control the mode.
* Simple text based messages between Python and GUI. Both effectively using stdin and stdout, wired together with pipes.


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
A simple test main.qml wouldn't run so we needed to install Qt as well.
* https://www.qt.io/download
* Open source version.
* qt-unified-linux-x64-4.0.1-online.run
* installed to /opt
* chose 5.15.2

### QtCreator
Struggled to get anything to build & link.

    /usr/bin/ld: cannot find -lGL

Answer: https://stackoverflow.com/questions/18406369/qt-cant-find-lgl-error
We did this:

    sudo ln -s /usr/lib/x86_64-linux-gnu/mesa/libGL.so.1 /usr/lib/libGL.so

or

    sudo ln -s /usr/lib/x86_64-linux-gnu/libGL.so.1 /usr/lib/libGL.so


### Pipes and Testing

At one point I had the GUI talking to <something> in a second terminal, using two named pipes, but I didn't take notes and I can't for the life of me work out what I did. It echoed the output from the GUI, and you could type commands to the GUI.

https://unix.stackexchange.com/questions/53641/how-to-make-bidirectional-pipe-between-two-programs

Open 2 terminals in the Qt build directory. In either, create 2 named pipes. In one, run ??? and in the other run the GUI:

    terminal1 $ mkfifo f1 f2
    terminal1 $ cat >f1 <f2   # this echoes hearbeats back, but you can't type
    terminal1 $ echo >f1 <f2

and

    terminal2 $ ./gui <f1 >f2

then terminal 1 shows output from the GUI (e.g. heartbeats, mode changes) and typing in terminal 1 sends the results to the GUI as though it was the Python core.

This has all been superceded by the TestStub.

