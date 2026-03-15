#!/usr/bin/python
import time, os, meshtastic.serial_interface, meshtastic, math
from pubsub import pub
import sys
import hashlib
import time
import threading



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
        sys.exit(1)



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
    size = 100
    filename = sys.argv[2] # name of file
    nodeID=818563225 # hex id of destination node
    numberOfPakets = math.ceil(os.path.getsize(filename) / size)
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
    start = False
    def sendPacket(interface, eof=False, master=False):
        if not eof and not master:
                #packet, hexbytes = ''
            payload = ''
            for bytes in file.read(size):
                payload = ''.join((payload, f"{bytes:02x}"))
            packet = ''.join((f"{i:06x}",f"{len(payload):02x}",hashlib.sha256(payload.encode("utf-8")).hexdigest()[:4], payload))
            interface.sendText(packet, channelIndex=1)
            packet = ''
        
            print("sent packet " + str(i))
        if master:
            packet = ''.join((f"MeshTP",f"{numberOfPakets:06x}", masterHash, filename))
            print (masterHash)

            print(f"{numberOfPakets:06x}")
            interface.sendText(packet, channelIndex=1)
            packet = ''
            print("sent master packet ")

        if eof:
            interface.sendText("EOF", channelIndex=1)
            print("sent EOF packet")

        

    def onReceive(packet, interface):
        global i
        global start
        if packet['from'] == nodeID or packet['from'] == 1128063444:
            if packet['decoded']['payload'] == b'ok master':
                start = True
                sendPacket(interface)
            elif packet['decoded']['payload'][0:2] == b'ok' and start:
                i = int(packet['decoded']['payload'][3:].decode('utf-8'), 16)+1

                print("got ok " + str(i-1))
                if(i < numberOfPakets):
                    sendPacket(interface)
                else:
                    sendPacket(interface, True)
                    close()
        
    def onConnection(interface, topic=pub.AUTO_TOPIC): # called when we (re)connect to the radio
        print("device connected")
        sendPacket(interface, master=True)
    

    interface = meshtastic.serial_interface.SerialInterface(devPath='/dev/ttyACM1')
    pub.subscribe(onReceive, "meshtastic.receive")
    pub.subscribe(onConnection, "meshtastic.connection.established")

    def close():
        print("Disconnecting...")
        file.close() # close the new file
        interface.close()
    try:
        while True:
            time.sleep(100)
    except KeyboardInterrupt:
        close()


if isServer == True:
    filename  = "" # name of file
    nodeID = ''
    numberOfPakets = 0
    file = 0
    end = False
    size = 0

    i = 0;

    def timer(interface, packetnum, ready):
        print(i)
        print(packetnum)
        if (i == packetnum and not end):
            print("retry")
            sendPacket(interface, ready)

    def sendPacket(interface, ready=False):
        if ready:
             interface.sendText("ok master", channelIndex=1)
             print("sent ok master")
             threading.Timer(10, timer, args=(interface, i, ready)).start()
        else:
             interface.sendText(("ok " + f"{i:06x}"), channelIndex=1)
             print("sent ok " + f"{i:06x}")
             threading.Timer(10, timer, args=(interface, i, ready)).start()


        

    def onReceive(packet, interface):
        global i
        global nodeID
        global numberOfPakets
        global file
        global filename
        global end
        global size
        length = 0
        check = b''
        payload = b''
        if (len(packet.get('decoded' , "")) > 0):
            if (len(packet['decoded'].get('payload' , "")) > 0) and packet['decoded']['payload'][0:2] != b'\r':
                if packet['decoded']['payload'][0:3] == b'EOF':
                    end = True
                    file.close()
                    print("done " + filename)
                if packet['decoded']['payload'][0:6] == b'MeshTP':
                    end = False
                    nodeID = packet['from']
                    print(packet['decoded']['payload'][6:12])
                    numberOfPakets = int(packet['decoded']['payload'][6:12].decode('utf-8'), 16)
                    masterHash = packet['decoded']['payload'][12:28]
                    filename = packet['decoded']['payload'][28:].decode('utf-8')
                    print(nodeID)
                    print(numberOfPakets)
                    print(masterHash)
                    print(filename)
                    print("\n\n")
                    file = open(filename, "wb")
                    sendPacket(interface, ready=True)

                elif packet['from'] == nodeID and len(packet['decoded']['payload']) >= 12 and packet.get('channel' , "") == 1 and not end:
                    packetnum = int(packet['decoded']['payload'][0:6].decode('utf-8'), 16)
                    length = int(packet['decoded']['payload'][6:8].decode('utf-8'), 16)
                    check = packet['decoded']['payload'][8:12]
                    payload = packet['decoded']['payload'][12:length+12]
                    print(str(packetnum) + " " + str(length) + " " + str(check))
                    print(hashlib.sha256(payload.decode('utf-8').encode('utf-8')).hexdigest()[:4] == check.decode('utf-8'))
                    i = packetnum
                    if i == 0:
                        size = int(length/2)
                    file.seek(size * i)
                    file.write(bytes.fromhex(payload.decode('utf-8')))
                    sendPacket(interface)
                    i+=1


                


    def onConnection(interface, topic=pub.AUTO_TOPIC): # called when we (re)connect to the radio
        print("device connected")
    

    interface = meshtastic.serial_interface.SerialInterface(devPath='/dev/ttyACM0')
    pub.subscribe(onReceive, "meshtastic.receive")
    pub.subscribe(onConnection, "meshtastic.connection.established")

    def close():
        print("Disconnecting...")
        interface.close()

    try:
        while True:
            time.sleep(100)

    except KeyboardInterrupt:
        close()