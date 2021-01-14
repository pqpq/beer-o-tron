#! usr/bin/python3

import sys
import select
import io
from gpiozero import Button
from time import sleep

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

def decodeMessage(message):
    # Echo heartbeats so GUI is happy
    if (message.startswith("heartbeat")):
        sendMessage(message)

# Fake some stuff for now
import random
temperature = 20.1
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
        seconds = seconds + 1
        sendMessage("time " + str(seconds))
        temperature += (random.random() - 0.5)
        sendMessage("temp " + str(temperature))
        count = 0
        