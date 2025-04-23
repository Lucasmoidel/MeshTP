import meshtastic
import meshtastic.serial_interface
import time
from pubsub import pub
import sys
import hashlib


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
#print (hexString)
masterHeader = ""
masterHash = hashlib.file_digest(file, "sha256").hexdigest()[:16]
print (masterHash)
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
print (hashes)






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