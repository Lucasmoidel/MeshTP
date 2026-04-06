import time, os, meshtastic.serial_interface, meshtastic, math
from pubsub import pub
import sys
import hashlib
import time
import threading
from tqdm import tqdm

'''
TODO: 
'''

class receiver:
    _debug = True
    _interface = 0
    _targetnode: int = 0

    _done = False
     
    _updatefunc = 0

    _filename: str = ""
    _file = 0
    _filesize: int = 0

    _numberOfPakets: int = 0
    _size: int = 0
    _lastpacketsize = 0
    _packetssent: int = 0;

    _masterHash = 0

    def __init__(self, interface, updatefunc, filename=""):
        self._interface = interface
        self._updatefunc = updatefunc
        self._filename = filename

    def start(self):
        pub.subscribe(self._onReceive, "meshtastic.receive")
        pub.subscribe(self._onConnection, "meshtastic.connection.established")
        
        while not self._done:
            time.sleep(1)

        self._file.close()

        file = open(self._filename, "rb") # open the file
                    
        print("done " + self._filename + " checksum: " + str(self._masterHash == hashlib.file_digest(file, "sha256").hexdigest()[:16]))
        file.close()

        self._interface.close()
        return True
    
    def _sendPacket(self, i):
        if i == -1:
            self._interface.sendText("ok master", destinationId=self._targetnode, wantAck=True)
            if self._debug:
                print("sent ok master")
        elif i == -2:
            self._interface.sendText("ok EOF", destinationId=self._targetnode, wantAck=True)
            if self._debug:
                print("sent ok EOF")
        else: 
            #self._interface.sendText(("ok " + f"{i:06x}"), destinationId=self._targetnode, wantAck=True)
            if self._debug:
                print("sent ok " + f"{i:06x}")
            #time.sleep(2)

    def _onReceive(self, packet, interface):
        check = b''
        payload = b''
        
        if (len(packet.get('decoded' , "")) > 0):
            if (len(packet['decoded'].get('payload' , "")) > 0) and packet['decoded']['payload'][0:2] != b'\r':
                if packet['decoded']['payload'][0:6] == b'EOF':
                    self._sendPacket(-2)
                    time.sleep(5)
                    self._done = True
                elif packet['decoded']['payload'][0:6] == b'MeshTP':
                    self._done = False
                    self._targetnode = packet['from']
                    self._numberOfPakets = int(packet['decoded']['payload'][6:12].decode('utf-8'), 16)
                    self._size = int(packet['decoded']['payload'][12:14].decode('utf-8'), 16)
                    self._lastpacketsize = int(packet['decoded']['payload'][14:16].decode('utf-8'), 16)
                    self._masterHash = packet['decoded']['payload'][16:32].decode('utf-8')
                    if len(self._filename) == 0:
                        self._filename = packet['decoded']['payload'][32:].decode('utf-8')
                    if self._debug:
                        print(self._targetnode)
                        print(self._numberOfPakets)
                        print(self._masterHash)
                        print(self._filename)
                        print("\n")
                    self._filesize = ((self._numberOfPakets-1)*self._size) + self._lastpacketsize

                    self._file = open(self._filename, "wb")
                    self._sendPacket(-1)

                elif packet['from'] == self._targetnode and len(packet['decoded']['payload']) >= 12 and not self._done:
                    packetnum = int(packet['decoded']['payload'][0:6].decode('utf-8'), 16)
                    print(packet['decoded']['payload'][0:6].decode('utf-8'))
                    check = packet['decoded']['payload'][6:10].decode('utf-8')
                    payload = packet['decoded']['payload'][10:]

                    checksucceed = hashlib.sha256(payload).hexdigest()[:4] == check
                    if checksucceed:
                        self._file.seek(self._size * packetnum)
                        self._file.write(payload)
                        self._file.flush()
                        print(packetnum)
                        #self._sendPacket(packetnum)
                    print(str(os.path.getsize(self._filename)) + " " + str(self._filesize))

    def _onConnection(self, interface, topic=pub.AUTO_TOPIC):
        print("connected to device \"" + interface.getLongName() + "\"")