#!/usr/bin/python
from sender import sender
from receiver import receiver
import time, os, meshtastic.serial_interface, meshtastic, math
from pubsub import pub
import sys
import hashlib
import time
import threading
from tqdm import tqdm


def printHelpCommand(): # print help
    messigefile = open("help.txt", "r")
    print(messigefile.read())
    messigefile.close()

for i in sys.argv: # check for --help
    if i == "--help":
        printHelpCommand() # explain the command line options
        sys.exit(1)

sendOrReceive = sys.argv[1] # send or receive is set to arg 1

bar = 0


def update(current, new, max, done=False):
    global bar
    if done:
        bar.close()
    if current == new:
        bar = tqdm(total=max, unit=" bytes", smoothing=1.0, leave=False)
    if current>=new:
        bar.update(new)
        bar.refresh()

if sendOrReceive == "send":
    if len(sys.argv) < 5: # ensure correft number of args
        print("incorrect number of argument\n")
        printHelpCommand()
        sys.exit(1)

    interface = meshtastic.serial_interface.SerialInterface(sys.argv[3])
    send = sender(interface, sys.argv[2], sys.argv[4], update)
    send.start()
    bar.close()

elif sendOrReceive == "receive":
    if len(sys.argv) < 3: # ensure correft number of args
        print("incorrect number of argument\n")
        printHelpCommand()
        sys.exit(1)

    interface = meshtastic.serial_interface.SerialInterface(sys.argv[2])
    receive = receiver(interface, update)
    receive.start()
    bar.close()

else: # inclorrect syntax and print help
    print("incorrect program role\n")
    printHelpCommand() # explain the command line options
    sys.exit(1)