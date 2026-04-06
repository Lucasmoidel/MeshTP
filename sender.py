import time, os, meshtastic.serial_interface, meshtastic, math
from pubsub import pub
import sys
import hashlib
import time
import threading
from tqdm import tqdm

'''
TODO: things
'''

class sender:
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

    _start: bool = False
    _done: bool = False

    _setlen: int = 10
    _set = []
    _currentset: int = -1
    _lastset: bool = False

    _send = True
    _num = 0

    _ack = False
    _sent = []

    def __init__(self, interface, filename: str, targetnode: str, updatefunc, size=200):
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

        self._updatefunc = updatefunc;

        self._size = size
        self._filename = filename
        self._filesize = os.path.getsize(self._filename)
        self._numberOfPakets = math.ceil(os.path.getsize(self._filename) / self._size)
        self._lastpacketsize = os.path.getsize(self._filename)%self._size
        self._packetssent = 0
        self._masterHash = hashlib.file_digest(self._file, "sha256").hexdigest()[:16]
        

    def start(self):
        pub.subscribe(self._onReceive, "meshtastic.receive")
        pub.subscribe(self._onConnection, "meshtastic.connection.established")
        
        while not self._done:
            if self._start and len(self._set) == 0:
                self._nextset()
                if len(self._set) == 0:
                    self._sendpacket(-2)
            self._sendset()
            time.sleep(1)
        print(self._num)
        self._file.close()
        self._interface.close()
        return True

    def _nextset(self):
        self._currentset+=1
        self._set = []
        self._sent = []
        if not self._lastset:
            for i in range((self._currentset*self._setlen), (self._currentset*self._setlen)+self._setlen):
                self._set.append(i)
                if i == self._numberOfPakets-1:
                    self._lastset = True
                    break
            for i in range(self._setlen):
                self._sent.append(-1);
        
    def _sendpacket(self, i: int):
        if (type(i) != int):
            raise ValueError("i wrong type")
        if i == -1:
            packet = ''.join((f"MeshTP",f"{self._numberOfPakets:06x}", f"{self._size:02x}", f"{self._lastpacketsize:02x}", self._masterHash, self._filename.split("/")[-1]))
            self._interface.sendText(packet, destinationId=self._targetnode, wantAck=True)

        elif i == -2:
            if self._send:
                self._interface.sendText("EOF", destinationId=self._targetnode, wantAck=True)
                print("sending EOF")
                self._send = False
                threading.Timer(5, self._timer).start()
        else:
            print("sending " + str(i))
            self._file.seek(self._size*i)
            payload = self._file.read(self._size)
            packet = b''.join((f"{i:06x}".encode('utf-8'), hashlib.sha256(payload).hexdigest()[:4].encode('utf-8'), payload))
            self._sent[i] = self._interface.sendData(packet, self._targetnode, wantAck=True).id
    
    def _timer(self):
        self._send = True

    def _sendset(self):
        if self._send:
            self._num+=1
            for i in self._set:
                self._sendpacket(i)
            self._send = False
            threading.Timer(5, self._timer).start()

    def _onReceive(self, packet, interface):
        #print(packet['decoded'])
        if packet['from'] == self._targetnode or packet['from'] == 1128063444:
            if packet['decoded'].get('portnum') == 'ROUTING_APP':
                self._ack = True
                print(packet['decoded'])
                i = -1
                for num in range(len(self._sent)):
                    if self._sent[num] == packet['decoded'].get('requestId'):
                        i = num
                        self._set.pop(num)
                        self._sent.pop(num)
                        break
                if i > -1:
                    self._packetssent+=1
                    if (i == self._numberOfPakets-1):
                        self._updatefunc(self._filesize, self._lastpacketsize, self._filesize)
                    else:
                        self._updatefunc((self._packetssent*self._size), self._size, self._filesize)
                    print(self._set)


            if packet['decoded']['payload'] == b'ok master':
                self._start = True
                print("got ok master")
                # for i in range(5):
                #     print(self._set)
                #     self._nextset()
            elif packet['decoded']['payload'] == b'ok EOF':
                self._done = True;
                print("got ok EOF")
            # elif packet['decoded']['payload'][0:2] == b'ok' and self._start:
            #     i = int(packet['decoded']['payload'][3:].decode('utf-8'), 16)
            #     try:
            #         self._set.pop(self._set.index(i))
            #     except ValueError:
            #         pass
            #     self._packetssent+=1
            #     if (i == self._numberOfPakets-1):
            #         self._updatefunc(self._filesize, self._lastpacketsize, self._filesize)
            #     else:
            #         self._updatefunc((self._packetssent*self._size), self._size, self._filesize)
            #     print(self._set)



    def _onConnection(self, interface, topic=pub.AUTO_TOPIC):
        print("connected to device \"" + interface.getLongName() + "\"")
        self._sendpacket(-1)