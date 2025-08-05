#!/usr/bin/python
import time, os, meshtastic.serial_interface, meshtastic, math
from pubsub import pub
import sys
import hashlib

def printHelpCommand(): # print help
    messigefile = open("help.txt", "r")
    print(messigefile.read())
    messigefile.close()
if len(sys.argv) < 4: # ensure correft number of args
    print("incorrect number of argument\n")
    printHelpCommand()
    sys.exit(1)

for i in sys.argv: # check for --help
    if i == "--help":
        printHelpCommand() # explain the command line options
        sys.exit(0)

isServer = False # set default server val
sendOrRecive = sys.argv[1] # send or recive is set to arg 1
if sendOrRecive == "send": # set isServer based on sendOrRecive
    isServer = False;
elif sendOrRecive == "recive": # set isServer based on sendOrRecive
    isServer = True;
else: # inclorrect syntax and print help
    print("incorrect program role\n")
    printHelpCommand() # explain the command line options
    sys.exit(1)

def onReceive(packet, interface):
    pass
def onConnection(interface, topic=pub.AUTO_TOPIC): # called when we (re)connect to the radio
    print("device connected")
    if isServer == False:

        filename = sys.argv[2] # name of file
        destination_ID='!e3549734' # hex id of destination node
        numberOfPakets = math.ceil(os.path.getsize(filename) / 99)
        print (os.path.getsize(filename))
        file = open(filename, "rb") # open the file
        masterHash = hashlib.file_digest(file, "sha256").hexdigest()[:16] #crate the hash of the original file

        if numberOfPakets > 16777215: # make sure the number of packets can be represented with 6 bytes of hex
            file.close() # close the new file
            print("file is to large")
            printHelpCommand()
            sys.exit(1)
        file.seek(0)
        #packet, hexbytes = ''
        for i in range(1):
            payload = ''
            for bytes in file.read(99):
                payload = ''.join((payload, f"{bytes:02x}"))
            packet = ''.join((f"{i:06x}",f"{len(payload):02x}",hashlib.sha256(payload.encode("utf-8")).hexdigest()[:4], payload))
        interface.sendText(packet, destinationId=destination_ID)
        file.close() # close the new file
        print("sent")
    

interface = meshtastic.serial_interface.SerialInterface(devPath='/dev/ttyUSB0')

pub.subscribe(onReceive, "meshtastic.receive")
pub.subscribe(onConnection, "meshtastic.connection.established")

try:
    while True:
        time.sleep(1000)
except KeyboardInterrupt:
    print("Disconnecting...")
    interface.close()




'''



for i in range(len(packets)): # generate the packets with the header and the payload
    

newhex = '' # create newhex variable

for i in packets: # reasemble the hex data to create the original hexString variable
    datalen = int(i[6:8], 16)
    newhex = newhex + i[12:210]
print (newhex==hexString) # check to make sure it encoded and decoded it correctly (the hexString and the newhex strings are the same)
#hashlib.sha256(file.read()).hexdigest()[:16]
file2 = open("/home/lucas/Documents/MeshTP/thing.txt", "wb") # open a new file
file2.write(bytes.fromhex(newhex)) # write the decoded data to a new file

file2.close() # close the new file




'''
