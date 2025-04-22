import meshtastic
import meshtastic.serial_interface
import time
from pubsub import pub
import sys


for i in sys.argv:
    if i == "--help":
        printHelpCommand() # explain the command line options

isServer = False
sendOrRecive = sys.argv[1]
if sendOrRecive == "send":
    isServer = False;
elif sendOrRecive == "recive":
    isServer = True;
else:
    raise Exception("incorrect command line argument")
    printHelpCommand() # explain the command line options

print(isServer)

filename = sys.argv[2]
file = open(filename, "rb")
hexString = ''.join([f'{byte:02x}' for byte in file.read()])
print (hexString)
masterHeader = ""

file2 = open("/home/lucas/Documents/MeshTP/thing.png", "wb")
file2.write(bytes.fromhex(hexString))

file.close()
file2.close()








#destinationId='!433ce1d4'

'''def onReceive(packet, interface):
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