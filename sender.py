import time, os, meshtastic.serial_interface, meshtastic, math
from pubsub import pub
import sys
import hashlib
import time
import threading
from tqdm import tqdm

class sender:
    _interface = 0
    _targetnode: int = 0
    _filename: str = ""
    _file = 0
    _filesize: int = 0

    _numberOfPakets: int = 0
    _size: int = 0
    _lastpacketsize = 0

    _masterHash = 0

    _done: bool = False

    _setlen: int = 2
    _set = []
    _currentset: int = -1
    _lastset: bool = False
    def __init__(self, interface, filename: str, targetnode: str, size=200):
        self._interface = interface

        if (type(filename) != str):
            raise ValueError("filename wrong type")
        
        self._file = open(filename, 'rb')
        if (type(size) != int):
            raise ValueError("size wrong type")
        
        if (type(targetnode) != str):
            raise ValueError("targetnode wrong type")
        
        if (targetnode[0] != "!"):
            self._targetnode = int(targetnode)

        self._size = size
        self._filename = filename
        self._filesize = os.path.getsize(self._filename)
        self._numberOfPakets = math.ceil(os.path.getsize(self._filename) / self._size)
        self._lastpacketsize = os.path.getsize(self._filename)%self._size
        self._masterHash = hashlib.file_digest(self._file, "sha256").hexdigest()[:16]
        
        self._nextset()
        pub.subscribe(self._onReceive, "meshtastic.receive")
        pub.subscribe(self._onConnection, "meshtastic.connection.established")
        while not self._done:
            time.sleep(1)
        self._file.close()
        self._interface.close()
        return True

    def _nextset(self):
        self._currentset+=1
        self._set = []
        if not self._lastset:
            for i in range((self._currentset*self._setlen), (self._currentset*self._setlen)+self._setlen):
                self._set.append(i)
                if i == self._numberOfPakets-1:
                    self._lastset = True
                    break

        
    def _sendpacket(self, interface, i: int):
        if (type(i) != int):
            raise ValueError("i wrong type")
        if i == -1:
            packet = ''.join((f"MeshTP",f"{self._numberOfPakets:06x}", f"{self._size:02x}", f"{self._lastpacketsize:02x}", self._masterHash, self._filename.split("/")[-1]))
            interface.sendText(packet, channelIndex=1)
        else:
            self._file.seek(self._size*i)
            payload = self._file.read(self._size)
            packet = b''.join((f"{i:06x}".encode('utf-8'), hashlib.sha256(payload).hexdigest()[:4].encode('utf-8'), payload))
            interface.sendData(packet, channelIndex=1)

    def _onReceive(self, packet, interface):
        if packet['from'] == self._targetnode or packet['from'] == 1128063444:
            if packet['decoded']['payload'] == b'ok master':
                for i in range(5):
                    print(self._set)
                    self._nextset()


    def _onConnection(self, interface, topic=pub.AUTO_TOPIC):
        print("connected to device \"" + interface.getLongName() + "\"")
        self._sendpacket(interface, -1)



