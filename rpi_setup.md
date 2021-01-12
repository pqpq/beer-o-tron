# Cross Compiling for RPi

The full RPi installer doesn't seem to have Qt5 libraries installed by default, 
and even if it did they're not the latest and greatest, so we have to build
them ourselves.

This is all basically following these instructions: https://wiki.qt.io/RaspberryPi2EGLFS


## Target

A brand new Model 3 B, caller 'masher'.


On RPi:
    sudo nano /etc/apt/sources.list
    # then uncomment the deb-src line
    sudo apt-get update
    sudo apt-get build-dep qt4-x11
    sudo apt-get build-dep libqt5gui5 
    sudo apt-get install libudev-dev libinput-dev libts-dev libxcb-xinerama0-dev libxcb-xinerama0
    sudo mkdir /usr/local/qt5pi
    sudo chown pi:pi /usr/local/qt5pi

## Host

On host, get the cross-compiler:

    mkdir raspi
    cd raspi
    git clone https://github.com/raspberrypi/tools

Then this lot seems to be copying the libs and general build environment from the Pi to the local machine, presumably so when we cross compile we have all the right libs ready and waiting, rather than having to create some kind of cross compile environment:

    mkdir sysroot sysroot/usr sysroot/opt
    rsync -avz pi@masher:/lib sysroot
    rsync -avz pi@masher:/usr/include sysroot/usr
    rsync -avz pi@masher:/usr/lib sysroot/usr
    rsync -avz pi@masher:/opt/vc sysroot/opt
    wget https://raw.githubusercontent.com/Kukkimonsuta/rpi-buildqt/master/scripts/utils/sysroot-relativelinks.py
    chmod +x sysroot-relativelinks.py
    # I had to ln -s /usr/bin/python2 /usr/bin/python to make the next line work, as it assumes Python 2
    ./sysroot-relativelinks.py sysroot 

Now build a version of Qt for the RPi with all the Qt modules we need:

    git clone git://code.qt.io/qt/qtbase.git -b 5.12
    cd qtbase
    ./configure -release -opengl es2 -device linux-rasp-pi3-g++ -device-option CROSS_COMPILE=~/raspi/tools/arm-bcm2708/gcc-linaro-arm-linux-gnueabihf-raspbian/bin/arm-linux-gnueabihf- -sysroot ~/raspi/sysroot -opensource -confirm-license -make libs -prefix /usr/local/qt5pi -extprefix ~/raspi/qt5pi -hostprefix ~/raspi/qt5 -v
    make -j4
    make -j4 install
    cd ..

    # This is a dependency of qtquickcontrols2
    git clone git://code.qt.io/qt/qtdeclarative.git -b 5.12
    cd qtdeclarative
    ~/raspi/qt5/bin/qmake
    make -j4
    make install
    cd ..

    # This is a dependency of qtquickcontrols2
    git clone git://code.qt.io/qt/qtxmlpatterns.git -b 5.12
    cd qtxmlpatterns
    ~/raspi/qt5/bin/qmake
    make -j4
    make install
    cd ..

    # I don't think this needs the ./configure line.
    # I think I copy & pasted it, but haven't re-run it since, to check
    # qtquickcontrols2 doesn't have a configure script, just configure.json
    git clone git://code.qt.io/qt/qtquickcontrols2.git -b 5.12
    cd qtquickcontrols2
    ./configure -release -opengl es2 -device linux-rasp-pi3-g++ -device-option CROSS_COMPILE=~/raspi/tools/arm-bcm2708/gcc-linaro-arm-linux-gnueabihf-raspbian/bin/arm-linux-gnueabihf- -sysroot ~/raspi/sysroot -opensource -confirm-license -make libs -prefix /usr/local/qt5pi -extprefix ~/raspi/qt5pi -hostprefix ~/raspi/qt5 -v
    make -j4
    make -j4 install
    cd ..

    # Needed for SVG image format support
    git clone git://code.qt.io/qt/qtsvg.git -b 5.12
    cd qtsvg
    ~/raspi/qt5/bin/qmake
    make -j4
    make install
    cd ..


At this point we have Qt5 libs, headers and plugins in ~/raspi/qt5Pi, ready for copying back to the Pi.

    cd .. 
    rsync -avz qt5pi pi@masher:/usr/local

Prove it works:

    # on host
    cd qtbase/examples/opengl/qopenglwidget
    ~/raspi/qt5/bin/qmake
    make
    scp qopenglwidget pi@masher:/home/pi

    # on pi
    echo /usr/local/qt5pi/lib | sudo tee /etc/ld.so.conf.d/qt5pi.conf
    sudo ldconfig

    sudo mv /usr/lib/arm-linux-gnueabihf/libEGL.so.1.1.0    /usr/lib/arm-linux-gnueabihf/libEGL.so.1.1.0_backup 
    sudo mv /usr/lib/arm-linux-gnueabihf/libGLESv2.so.2.1.0 /usr/lib/arm-linux-gnueabihf/libGLESv2.so.2.1.0_backup 
    sudo ln -s /opt/vc/lib/libEGL.so        /usr/lib/arm-linux-gnueabihf/libEGL.so.1.1.0 
    sudo ln -s /opt/vc/lib/libGLESv2.so     /usr/lib/arm-linux-gnueabihf/libGLESv2.so.2.1.0 
    sudo ln -s /opt/vc/lib/libbrcmEGL.so    /opt/vc/lib/libEGL.so 
    sudo ln -s /opt/vc/lib/libbrcmGLESv2.so /opt/vc/lib/libGLESv2.so

It segfaults. Hmmm.

To build mash-o-matic:

    cd path/to/beer-o-tron/gui
    ~/raspi/qt5/bin/qmake
    make
    scp gui pi@masher:/home/pi

    ssh -X pi@masher
    ./gui 

It works! But SVG doesn't, so go back in time and build qtsvg (see above).





