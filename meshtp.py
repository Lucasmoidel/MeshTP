#!/usr/bin/python
import time, os, meshtastic.serial_interface, meshtastic, math
from pubsub import pub
import sys
import hashlib


def printHelpCommand(): # print help
    messigefile = open("help.txt", "r")
    print(messigefile.read())
    messigefile.close()

if len(sys.argv) < 3: # ensure correft number of args
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

if isServer == False:
    size = 80
    filename = sys.argv[2] # name of file
    nodeID='!30ca4899' # hex id of destination node
    numberOfPakets = math.ceil(os.path.getsize(filename) / (size*2))
    print (numberOfPakets)
    file = open(filename, "rb") # open the file
    masterHash = hashlib.file_digest(file, "sha256").hexdigest()[:16] #crate the hash of the original file
    if numberOfPakets > 16777215: # make sure the number of packets can be represented with 6 bytes of hex
        file.close() # close the new file
        print("file is to large")
        printHelpCommand()
        sys.exit(1)
    file.seek(0)
    i = 0;
    def sendPacket(interface, eof=False, master=False):
        if master:
            packet = ''.join((f"MeshTP",f"{numberOfPakets:06x}", masterHash))
            print (masterHash)

            print(f"{numberOfPakets:06x}")
            interface.sendText(packet, channelIndex=1)
            packet = ''
            print("sent master packet ")
        if (not eof):
                #packet, hexbytes = ''
            payload = ''
            for bytes in file.read(size):
                payload = ''.join((payload, f"{bytes:02x}"))
            packet = ''.join((f"{i:06x}",f"{len(payload):02x}",hashlib.sha256(payload.encode("utf-8")).hexdigest()[:4], " ", payload))
            interface.sendText(packet, channelIndex=1)
            packet = ''
        
            print("sent packet " + str(i))
        else:
            interface.sendText("EOF", channelIndex=1)
            print("sent EOF packet")

        

    def onReceive(packet, interface):
        global i
        if packet['fromId'] == '!30ca4899':
            if packet['decoded']['payload'] == b'ok':
                print("got ok")
                if(i < numberOfPakets):
                    sendPacket(interface)
                    i+=1
                else:
                    sendPacket(interface, True)
        
    def onConnection(interface, topic=pub.AUTO_TOPIC): # called when we (re)connect to the radio
        print("device connected")
        sendPacket(interface, master=True)
    

    interface = meshtastic.serial_interface.SerialInterface(devPath='/dev/ttyACM0')
    pub.subscribe(onReceive, "meshtastic.receive")
    pub.subscribe(onConnection, "meshtastic.connection.established")

    try:
        while True:
            time.sleep(1000)
    except KeyboardInterrupt:
        print("Disconnecting...")
        file.close() # close the new file
        interface.close()


if isServer == True:
    filename = sys.argv[2] # name of file
    nodeID = ''
    numberOfPakets = 0
    file = open(filename, "wb") # open the file
    #masterHash = hashlib.file_digest(file, "sha256").hexdigest()[:16] #crate the hash of the original file

    i = 0;
    def sendPacket(interface, eof=False):
        # if (not eof):
        #         #packet, hexbytes = ''
        #     cont = False
        #     payload = ''
        #     for bytes in file.read(size):
        #         payload = ''.join((payload, f"{bytes:02x}"))
        #     print (file.tell()/size)
        #     packet = ''.join((f"{i:06x}",f"{len(payload):02x}",hashlib.sha256(payload.encode("utf-8")).hexdigest()[:4], " ", payload))
        #     interface.sendText(packet, channelIndex=1)
        #     packet = ''
        
        #     print("sent packet " + str(i))
        # else:
        #     interface.sendText("EOF", channelIndex=1)
        #     print("sent EOF packet")
        pass

        

    def onReceive(packet, interface):
        global i
        if (len(packet.get('decoded' , "")) > 0):
            if (len(packet['decoded'].get("payload" , "")) > 0):
                if packet['decoded']['payload'][0:6] == b'MeshTP':
                    nodeID = packet['fromId']
                    print(nodeID)
                    numberOfPakets = int(packet['decoded']['payload'][6:12].decode('utf-8'), 16)
                    print(packet['decoded']['payload'][6:12].decode('utf-8'))
                    print(numberOfPakets)
                    print(packet['decoded']['payload'])
                    masterHash = packet['decoded']['payload'][12:]
                    print(masterHash)


        # if packet['decoded']['payload'] == b'ok':
        #     print("got ok")
        #     if(i < numberOfPakets):
        #         sendPacket(interface)
        #         i+=1
        #     else:
        #         sendPacket(interface, True)
        
    def onConnection(interface, topic=pub.AUTO_TOPIC): # called when we (re)connect to the radio
        print("device connected")
    

    interface = meshtastic.serial_interface.SerialInterface(devPath='/dev/ttyACM1')
    pub.subscribe(onReceive, "meshtastic.receive")
    pub.subscribe(onConnection, "meshtastic.connection.established")

    try:
        while True:
            time.sleep(1000)
    except KeyboardInterrupt:
        print("Disconnecting...")
        file.close() # close the new file
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
