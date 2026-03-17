#!/usr/bin/python
import time, os, meshtastic.serial_interface, meshtastic, math
from pubsub import pub
import sys
import hashlib
import time
import threading
from tqdm import tqdm

'''
todo:

1 add user defined serial device ✅
2 add user defined mesh device (hex or decimal) and remove man in the middle ✅
3 use DM instead of channel 
4 add -o output file for recive ✅
5 add progress bar ✅
6 compression???
7 move to a new channel / freq to not interfere with regular traffic ??
8 impliment device discovery https://github.com/meshtastic/python/blob/master/examples/scan_for_devices.py
9 add length check on input file name

'''

debug = False

def printHelpCommand(): # print help
    messigefile = open("help.txt", "r")
    print(messigefile.read())
    messigefile.close()

if len(sys.argv) < 2: # ensure correft number of args
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
    done = False
    size = 212
    nodeID = 0
    filename = sys.argv[2] # name of file
    if (sys.argv[4][0] == "!"):
        nodeID = int(sys.argv[4][1:],16)
    else:
        nodeID = int(sys.argv[4])
    numberOfPakets = math.ceil(os.path.getsize(filename) / size)
    print(str(numberOfPakets) + " packets")
    file = open(filename, "rb") # open the file
    masterHash = hashlib.file_digest(file, "sha256").hexdigest()[:16] #crate the hash of the original file
    lastpacketsize = os.path.getsize(filename)%size

    if numberOfPakets > 16777215: # make sure the number of packets can be represented with 6 bytes of hex
        file.close() # close the new file
        print("file is to large")
        printHelpCommand()
        sys.exit(1)
    file.seek(0)
    i = 0;
    start = False
    pbar = tqdm(total=os.path.getsize(filename), unit=" bytes", smoothing=1.0, leave=False)
    barloc = 0
    def sendPacket(interface, eof=False, master=False):
        global pbar
        if not eof and not master:
                #packet, hexbytes = ''
            
            payload = b''
            file.seek(size*i)
            payload = file.read(size)
            packet = b''.join((f"{i:06x}".encode('utf-8'), hashlib.sha256(payload).hexdigest()[:4].encode('utf-8'), payload))
            interface.sendData(packet, channelIndex=1)
            packet = ''
            if debug:
                print("sent packet " + str(i))
        if master:
            packet = ''.join((f"MeshTP",f"{numberOfPakets:06x}", f"{size:02x}", f"{lastpacketsize:02x}", masterHash, filename))
            
            if debug:
                print (masterHash)
                print(f"{numberOfPakets:06x}")
                
            interface.sendText(packet, channelIndex=1)
            packet = ''
            if debug:
                print("sent master packet ")

        if eof:
            interface.sendText("EOF", channelIndex=1)
            if debug:
                print("sent EOF packet")

        

    def onReceive(packet, interface):
        global i
        global start
        global barloc
        global pbar
        if packet['from'] == nodeID or packet['from'] == 1128063444:
            if packet['decoded']['payload'] == b'ok master':
                start = True
                sendPacket(interface)
            elif packet['decoded']['payload'][0:2] == b'ok' and start:
                i = int(packet['decoded']['payload'][3:].decode('utf-8'), 16)+1
                
                if debug:
                    print("got ok " + str(i-1))
                if(i < numberOfPakets):
                    if i != barloc:
                        pbar.update(size)
                        barloc = i
                    sendPacket(interface)
                else:
                    pbar.update(lastpacketsize)
                    sendPacket(interface, True)
                    close()
        
    def onConnection(interface, topic=pub.AUTO_TOPIC): # called when we (re)connect to the radio
        print("device connected")
        sendPacket(interface, master=True)
    

    interface = meshtastic.serial_interface.SerialInterface(devPath=sys.argv[3])
    pub.subscribe(onReceive, "meshtastic.receive")
    pub.subscribe(onConnection, "meshtastic.connection.established")

    def close():
        global done
        print("Disconnecting...")
        file.close() # close the new file
        interface.close()
        done = True
    try:
        while True:
            time.sleep(0.01)
            if type(pbar) != int:
                pbar.refresh()
            if done:
                pbar.close()
                sys.exit(0)
    except KeyboardInterrupt:
        close()


if isServer == True:
    filename  = "" # name of file
    carg = False
    if (len(sys.argv) > 3 and sys.argv[3] == "-o"):
        filename = sys.argv[4]
        carg = True
    nodeID = ''
    numberOfPakets = 0
    file = 0
    end = False
    size = 0
    masterHash = ''
    pbar = 0
    i = 0;
    lastpacketsize = 0
    filesize = 0
    lastpacket = -1
    def timer(interface, packetnum, ready):
        if (i == packetnum and not end):
            if debug:
                print("retry !!!!!!!!!!!!!!!! " + str(i) + " " + str(packetnum))

            sendPacket(interface, packetnum, ready)

    def sendPacket(interface, num, ready=False):
        if ready == True:
            interface.sendText("ok master", channelIndex=1)
            if debug:
                print("sent ok master")
            threading.Timer(15, timer, args=(interface, num, ready)).start()
        else:
            interface.sendText(("ok " + f"{i:06x}"), channelIndex=1)
            if debug:
                print("sent ok " + str(num))
            threading.Timer(15, timer, args=(interface, num, ready)).start()


        

    def onReceive(packet, interface):
        global i
        global nodeID
        global numberOfPakets
        global masterHash
        global file
        global filename
        global end
        global size
        global pbar
        global lastpacketsize
        global filesize
        global lastpacket
        length = 0
        check = b''
        payload = b''

        if (len(packet.get('decoded' , "")) > 0):
            if (len(packet['decoded'].get('payload' , "")) > 0) and packet['decoded']['payload'][0:2] != b'\r':
                if packet['decoded']['payload'][0:3] == b'EOF':
                    end = True
                    file.close()
                    file = open(filename, "rb") # open the file
                    
                    print("done " + filename + " checksum: " + str(masterHash == hashlib.file_digest(file, "sha256").hexdigest()[:16]))
                    file.close()
                    pbar.close()
                    pbar = 0
                elif packet['decoded']['payload'][0:6] == b'MeshTP':
                    end = False
                    nodeID = packet['from']
                    numberOfPakets = int(packet['decoded']['payload'][6:12].decode('utf-8'), 16)
                    size = int(packet['decoded']['payload'][12:14].decode('utf-8'), 16)
                    lastpacketsize = int(packet['decoded']['payload'][14:16].decode('utf-8'), 16)
                    masterHash = packet['decoded']['payload'][16:32].decode('utf-8')
                    if not carg:
                        filename = packet['decoded']['payload'][32:].decode('utf-8')
                    if debug:
                        print(nodeID)
                        print(numberOfPakets)
                        print(masterHash)
                        print(filename)
                        print("\n")
                    file = open(filename, "wb")
                    pbar = tqdm(total=(size*(numberOfPakets-1)+lastpacketsize), unit=" bytes", smoothing=1.0, leave=False)
                    sendPacket(interface, i, ready=True)

                elif packet['from'] == nodeID and len(packet['decoded']['payload']) >= 12 and not end:
                    packetnum = int(packet['decoded']['payload'][0:6].decode('utf-8'), 16)
                    check = packet['decoded']['payload'][6:10].decode('utf-8')
                    payload = packet['decoded']['payload'][10:]

                    checksucceed = hashlib.sha256(payload).hexdigest()[:4] == check
                    if debug:
                        print(str(packetnum) + " " + str(length) + " " + str(check) + " " + str(checksucceed))
                    if not checksucceed:
                        sendPacket(interface, i)
                    i = packetnum
                    file.seek(size * i)
                    if debug:
                        print("write packet " + str(i) + " at " + str(size * i))
                    file.write(payload)
                    if debug:
                        print(file.tell())
                    if lastpacket < i:
                        pbar.update(len(payload))
                    lastpacket = i
                    sendPacket(interface, i)


                


    def onConnection(interface, topic=pub.AUTO_TOPIC): # called when we (re)connect to the radio
        print("device connected")
    
    meshtastic.serial_interface.SerialInterface(devPath=sys.argv[2])
    pub.subscribe(onReceive, "meshtastic.receive")
    pub.subscribe(onConnection, "meshtastic.connection.established")

    def close():
        print("Disconnecting...")
        interface.close()

    try:
        while True:
            time.sleep(0.01)    
            if type(pbar) != int:
                pbar.refresh()

    except KeyboardInterrupt:
        close()