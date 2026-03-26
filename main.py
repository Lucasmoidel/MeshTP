from sender import sender
import time, os, meshtastic.serial_interface, meshtastic, math
from pubsub import pub
import sys
import hashlib
import time
import threading
from tqdm import tqdm

def update(current, new, max):
    print(current)
    print(new)
    print(max)

interface = meshtastic.serial_interface.SerialInterface("/dev/ttyACM0")
# pub.subscribe(onReceive, "meshtastic.receive")
# pub.subscribe(onConnection, "meshtastic.connection.established")

send = sender(interface, "testfiles/thing.txt", "818563225", update)
send.start()