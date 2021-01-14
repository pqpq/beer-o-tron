#! usr/bin/python3

import sys
import select
import threading
from gpiozero import Button
from time import sleep

oneWireDevicePath = "/sys/bus/w1/devices/"

def sendMessage(message):
    sys.stdout.write(message+'\n')
    sys.stdout.flush()

def sendDown(button):
    return lambda : sendMessage("button "+str(button)+" down")

def sendUp(button):
    return lambda : sendMessage("button "+str(button)+" up")
    
button1 = Button(17)
button2 = Button(22)
button3 = Button(23)
button4 = Button(27)

button1.when_pressed = sendDown(1)
button1.when_released = sendUp(1)
button2.when_pressed = sendDown(2)
button2.when_released = sendUp(2)
button3.when_pressed = sendDown(3)
button3.when_released = sendUp(3)
button4.when_pressed = sendDown(4)
button4.when_released = sendUp(4)


temperatureSensors = []
temperatures = []

def readFile(fileName):
    with open(fileName) as f:
        return f.readlines()

def discoverTemperatureSensors(lock):
    global temperatureSensors
    temperatureSensors.clear()
    sensors = readFile(oneWireDevicePath + "w1_bus_master1/w1_master_slaves")
    lock.acquire()
    for i in sensors:
        temperatureSensors.append(oneWireDevicePath + i.rstrip())
        temperatures.append(0.0)
    lock.release()
    
def readTemperatureSensors(lock):
    global temperatureSensors
    index = 0
    for i in temperatureSensors:
        with open(i + "/temperature") as f:
            value = f.read()
            lock.acquire()
            temperatures[index] = float(value) / 1000
            index = index + 1
            lock.release()
    
def temperatureThreadFunction(lock):
    print("temperatureThreadFunction()", lock)
    discoverTemperatureSensors(lock)
    while True:
        readTemperatureSensors(lock)
        sleep(1)

def getTemperatures(lock):
    values = []
    lock.acquire()
    for i in temperatures:
        values.append(i)
    lock.release()
    return values


heartbeatCount = 0

def decodeMessage(message):
    # Echo heartbeats so GUI is happy
    if (message.startswith("heartbeat")):
        sendMessage(message)
        global heartbeatCount
        if heartbeatCount == 0:
            sendMessage("image /opt/mash-o-matic/splash.png")
        heartbeatCount = heartbeatCount + 1

temperatureLock = threading.Lock()
temperatureWorkerThread = threading.Thread(target=temperatureThreadFunction, daemon=True, args=(temperatureLock,))
temperatureWorkerThread.start()

count = 0
seconds = 0

while True:
    # Non-blocking check for whether there's anything to read on stdin
    # select() only signals stdin when ENTER is pressed, so when
    # this fires, the whole line is available, so we must use readline()
    if select.select([sys.stdin], [], [], 0)[0] == [sys.stdin]:
        decodeMessage(sys.stdin.readline())
    
    sleep(0.05)

    count = count + 1
    if count == 20:
        count = 0

        seconds = seconds + 1
        sendMessage("time " + str(seconds))

        averageTemperature = 0.0
        temperatures = getTemperatures(temperatureLock)
        for i in temperatures:
            averageTemperature = averageTemperature + i
        averageTemperature = averageTemperature / len(temperatures)
        sendMessage("temp " + str(averageTemperature))
        