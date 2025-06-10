#!/usr/bin/python
import meshtastic
import meshtastic.serial_interface
import time
from pubsub import pub
import sys
import hashlib
import mesh

def printHelpCommand():
    messigefile = open("help.txt", "r")
    print(messigefile.read())
    messigefile.close()

if len(sys.argv) < 4:
    print("incorrect number of argument\n")
    printHelpCommand()
    sys.exit(1)

for i in sys.argv:
    if i == "--help":
        printHelpCommand() # explain the command line options
        sys.exit(0)

isServer = False
sendOrRecive = sys.argv[1]
if sendOrRecive == "send":
    isServer = False;
elif sendOrRecive == "recive":
    isServer = True;
else:
    print("incorrect program role\n")
    printHelpCommand() # explain the command line options
    sys.exit(1)

filename = sys.argv[2]

destinationID = sys.argv[3]

masterPacket = ""
hexpackets = []
packets = []
file = open(filename, "rb")

hexString = ''.join([f'{byte:02x}' for byte in file.read()])
file.seek(0)

masterHash = hashlib.file_digest(file, "sha256").hexdigest()[:16]
#print ("\n\nmasterHash: " + masterHash)


hexpackets = [hexString[i:i+190] for i in range(0, len(hexString), 190)]
#print(hexpackets)

if len(hexpackets) >= 65530:
    print("file is to large")
    sys.exit(1)

n = 1

for i in hexpackets:
    string = f"{n:04x}" + f"{len(i):02x}" + hashlib.sha256(i.encode("utf8")).hexdigest()[:4] + i
    n+=1
    packets.append(string)

newhex = ''

for i in packets:
    datalen = int(i[4:6], 16)
    newhex = newhex + i[10:200]
print (newhex==hexString)
#hashlib.sha256(file.read()).hexdigest()[:16]
file2 = open("/home/lucas/Documents/MeshTP/thing.txt", "wb")
file2.write(bytes.fromhex(newhex))

file2.close()



'''
file2 = open("/home/lucas/Documents/MeshTP/thing.png", "wb")
file2.write(bytes.fromhex(hexString))

file.close()
file2.close()

file3 = open(filename, "rb")

masterHash2 = hashlib.file_digest(file3, "sha256").hexdigest()[:16]
print (masterHash2)

hexString = [hexString[i:i+192] for i in range(0, len(hexString), 192)]

hashes = []

for i in hexString:
    hashes.append(hashlib.sha256(i.encode('utf-8')).hexdigest()[:4])
print(hashes)






#destinationId='!433ce1d4'

def onReceive(packet, interface):
    if "decoded" not in packet:
        return
    if packet["decoded"]["portnum"] == "TEXT_MESSAGE_APP":
        print(packet)
        message = packet.get("decoded", {}).get("payload", b"").decode("utf-8", errors="ignore")
        print(f"From: {packet.get("from")} in channel {packet.get("channel")} - {message}")

def onConnection(interface, topic=pub.AUTO_TOPIC): # called when we (re)connect to the radio
    print("device connected")
    interface.sendText("hello mesh", channelIndex=1)

interface = meshtastic.serial_interface.SerialInterface(devPath='/dev/ttyACM0')

pub.subscribe(onReceive, "meshtastic.receive")
pub.subscribe(onConnection, "meshtastic.connection.established")

try:
    while True:
        time.sleep(1000)
except KeyboardInterrupt:
    print("Disconnecting...")
    interface.close()''' 