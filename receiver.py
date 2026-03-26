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
    _debug = False
    _interface = 0
    _targetnode: int = 0

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
    
    def _sendpacket(self, i):
        if i < 0:
            self._interface.sendText("ok master", channelIndex=1)
        else: 
            self._interface.sendText(("ok " + f"{self._numberOfPakets:06x}"), channelIndex=1)

    def _onReceive(self, packet, interface):
        check = b''
        payload = b''

        if (len(packet.get('decoded' , "")) > 0):
            if (len(packet['decoded'].get('payload' , "")) > 0) and packet['decoded']['payload'][0:2] != b'\r':
                if packet['decoded']['payload'][0:6] == b'MeshTP':
                    end = False
                    nodeID = packet['from']
                    self._numberOfPakets = int(packet['decoded']['payload'][6:12].decode('utf-8'), 16)
                    self._size = int(packet['decoded']['payload'][12:14].decode('utf-8'), 16)
                    self._lastpacketsize = int(packet['decoded']['payload'][14:16].decode('utf-8'), 16)
                    self._masterHash = packet['decoded']['payload'][16:32].decode('utf-8')
                    if len(self._filename) == 0:
                        filename = packet['decoded']['payload'][32:].decode('utf-8')
                    if self._debug:
                        print(nodeID)
                        print(self._numberOfPakets)
                        print(self._masterHash)
                        print(self._filename)
                        print("\n")
                    self._file = open(filename, "wb")
                    self._sendPacket(interface, -1)

                elif packet['from'] == nodeID and len(packet['decoded']['payload']) >= 12 and not end:
                    packetnum = int(packet['decoded']['payload'][0:6].decode('utf-8'), 16)
                    check = packet['decoded']['payload'][6:10].decode('utf-8')
                    payload = packet['decoded']['payload'][10:]

                    checksucceed = hashlib.sha256(payload).hexdigest()[:4] == check
                    if checksucceed:
                        
                        self._file.seek(self._size * packetnum)
                        self._file.write(payload)
                        self._file.flush()
                        self._sendPacket(interface, packetnum)
