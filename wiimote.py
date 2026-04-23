import time
import os
import sys
import math
import string
from abc import ABCMeta, abstractmethod
from enum import Enum
from _xwiimote import ffi, lib

### TODO LIST -------------------------------
#   define the constructors for the two different types of wiimotes
#   implement load_event() from file
#   port the functions from wiitest.py



class Wiivent:
    def __init__(self, wv_type, time, acc: tuple[int, int, int, int]=None,
                 key: tuple[int, bool]=None):
        self.wv_type = wv_type
        self.acc = acc
        self.key = key
        self.time = time

    def __repr__(self):
        return f"wiivent<{self.wv_type}, {self.acc}, {self.key}>"

    def data(self):
        if self.wv_type == lib.XWII_EVENT_ACCEL:
            return self.acc
        elif self.wv_type == lib.XWII_EVENT_KEY:
            return self.key

class GPState(Enum):
    WAIT = 0
    CIRCLEOUT = 1
    CIRCLEAPEX = 2
    CIRCLEBACK = 3
    SWINGOUT = 4
    SWINGDOWN = 5

class Wiimote:
    thresh = 40
    mag_thresh = 30
    timeout = .1
    # src: https://stackoverflow.com/questions/4814523/abstractmethod-is-not-defined
    def __init__(self, player:int):
        self.grav = (0,0,0)
        self.last_move = 0
        self.last_event = None
        self.player = player
        self.state = GPState.WAIT

    def __str__(self):
        return f"Wiimote (P{self.player})"

    def __repr__(self):
        return self.__str__()

    def get_magnitude(x, y, z):
        return math.sqrt((x * x) + (y * y) + (z * z))

    def parse_gesture(self):
        x, y, z, mag = self.last_event.data()

        # update time
        if (abs(mag - 100) > Wiimote.thresh):
            self.last_move = self.last_event.time
            at_rest = False
        else:
            at_rest = ((self.last_event.time - self.last_move) > Wiimote.timeout
                and z > 80)
        
        # state machine
        if (self.state is GPState.WAIT and
                (mag - 100) > Wiimote.mag_thresh and
            y > Wiimote.thresh):
            self.state = GPState.SWINGOUT

        elif (self.state is GPState.SWINGOUT and
                abs(mag - 100) > Wiimote.mag_thresh and
              z > Wiimote.thresh):
            self.state = GPState.SWINGDOWN

        elif (self.state is GPState.SWINGDOWN and
              at_rest):
            print(f"detected SWING ({self.last_event.time}) -----------------")
            self.state = GPState.WAIT

        elif (self.state is GPState.WAIT and
                (mag - 100) > Wiimote.mag_thresh and
                abs(x) > Wiimote.thresh):
            self.state = GPState.CIRCLEOUT
        
        elif (self.state is GPState.CIRCLEOUT and
              mag < 130):
            self.state = GPState.CIRCLEAPEX

        elif (self.state is GPState.CIRCLEAPEX and
                abs(mag - 100) > Wiimote.mag_thresh and
              z < -Wiimote.thresh):
            self.state = GPState.CIRCLEBACK

        elif (self.state is GPState.CIRCLEBACK and
              at_rest):
            print(f"detected CIRCLE ({self.last_event.time}) ------------------")
            self.state = GPState.WAIT

        elif (at_rest):
            self.state = GPState.WAIT

    def process_event(self):
        self.load_event()
        if self.last_event.wv_type is lib.XWII_EVENT_ACCEL:
            self.parse_gesture()

# wii remote that takes its inputs from an actual interface
class WiimoteLive(Wiimote):
    def __init__(self, player:int, iface):
        super().__init__(player)
        self.iface = iface

    def load_event(self):
        event = ffi.new("struct xwii_event *")
        lib.xwii_iface_dispatch(xwii_iface[device], event, ffi.sizeof(event[0]))
        if (event.type is lib.XWII_EVENT_ACCEL):
            mag = get_magnitude(
                   event.v.abs[0].x, event.v.abs[0].y, event.v.abs[0].z)
            self.last_event = Wiivent(lib.XWII_EVENT_ACCEL,
                acc=(event.v.abs[0].x, event.v.abs[0].y, event.v.abs[0].z, mag))
        elif (event.type is lib.XWII_EVENT_KEY):
            self.last_event = Wiivent(lib.XWII_EVENT_KEY, 
                key=(event.v.key.code, bool(event.v.key.state)))

# wii remote that takes its inputs from a test file
class WiimoteSim(Wiimote):
    def __init__(self, player: int, filename:str):
        super().__init__(player)
        self.filename = filename
        self.source = open(filename, "r")

    def load_event(self):
        data = self.source.readline().split(',')
        if (len(data) < 2):
           sys.exit() 
        if (data[1] == 'A'):
            ispressed = (data[2] == 'PRESSED')
            self.last_event = (
                Wiivent(lib.XWII_EVENT_KEY, float(data[0]), key=(lib.XWII_KEY_A, ispressed)))
        else:
            mag = float(data[10])
            self.last_event = (
                Wiivent(lib.XWII_EVENT_ACCEL, float(data[0]),
                        acc=(float(data[1]), float(data[2]),
                             float(data[3]), float(data[10]))))

wiimotes = []

if (len(sys.argv) > 1):
    i = 0
    for filename in sys.argv[1:]:
        i+= 1
        wiimotes.append(WiimoteSim(i, filename))

print(wiimotes)

event0 = Wiivent(lib.XWII_EVENT_KEY, 0, key=(lib.XWII_KEY_A, True))
event1 = Wiivent(lib.XWII_EVENT_KEY, 0, acc=(0,0,100))
#print(event1.data())

while 1:
    wiimotes[0].process_event()
    #print(f"{wiimotes[0].state} ({wiimotes[0].last_event.time})")
    #print(wiimotes[0].last_event)
