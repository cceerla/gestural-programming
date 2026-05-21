import time
import os
import sys
import math
import string
from abc import ABCMeta, abstractmethod
from enum import Enum
from _xwiimote import ffi, lib
from collections import deque

### TODO LIST -------------------------------

# KNOWN ISSUE: WII REMOTE HAS TO BE HELD FLAT OR POINTER UP AS REST POSN FOR GESTURES TO BE RECOGNIZED

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

class GVType(Enum):
    SEND = 0
    RECV = 1
    END  = 2

class Gesturevent:
    def __init__(self, kind: GVType, target: int):
        self.kind = kind
        self.target = target

    def __str__(self):
        return f"Gesturevent {self.kind} -> {self.target}"
    def __repr__(self):
        return self.__str__()

class SwState(Enum):
    WAIT  = 0
    START = 1
    MOVE  = 2
    STOP  = 3

class CiState(Enum):
    WAIT = 0
    RISE = 1
    PEAK = 2
    FALL = 3

class DTState(Enum):
    WAIT = 0
    PRESS = 1
    BETWEEN = 2
    DOUBLE = 3

class Wiimote:
    max_players = 4
    thresh = 40
    mag_thresh = 50 # TODO: this threshold differs from person to person
    timeout = .05
    doubletap_timeout = .6
    sample = 5
    # src: https://stackoverflow.com/questions/4814523/abstractmethod-is-not-defined
    def __init__(self, player:int):
        # last HID event from the wii remote
        self.last_event = None

        # used in gesture parsing
        self.last_move = 0
        self.swing_state = SwState.WAIT
        self.circle_state = CiState.WAIT
        self.until_sample = Wiimote.sample
        self.prev_acc = (0,0,0)
        self.at_rest = False

        # used in button parsing
        self.btnB_dt = DTState.WAIT
        self.btnB_to = -1

        # used for general housekeeping/integration
        self.new_events = True
        self.player = player
        self.start = time.time()
        
        # passed on to choreo synthesis
        if player == 0:     # hard-coded for 2 player case, atm
            self.target = 1
        if player == 1:
            self.target = 0
        self.events = []
        self.vec_clk = 0

        # button states
        self.buttons = {"A": False,
                        "B": False,
                        "L": False, 
                        "R": False, 
                        "U": False, 
                        "D": False,
                        "+": False,
                        "-": False}

    def __str__(self):
        return f"Wiimote (P{self.player})"

    def __repr__(self):
        return self.__str__()

    def get_rest(self, z:float, mag:float):
        # update time
        if (abs(mag - 100) > (Wiimote.mag_thresh/2)):
            self.last_move = self.last_event.time
            self.at_rest = False
        else:
            self.at_rest = ((self.last_event.time - self.last_move) > Wiimote.timeout
                           and z > 80)

    def parse_swing(self, x:float, y:float, z:float, mag:float):
        if (self.swing_state == SwState.WAIT and
            -z > Wiimote.thresh):
            self.swing_state = SwState.START
        elif (self.swing_state == SwState.START and
              mag - 100 > (2 * Wiimote.mag_thresh) and
              y > Wiimote.thresh):
            self.swing_state = SwState.MOVE
        elif (self.swing_state == SwState.MOVE and
              mag - 100 > (2 * Wiimote.mag_thresh) and
              z > Wiimote.thresh):
            self.swing_state = SwState.STOP
    
    def parse_circle(self, x:float, y:float, z:float, mag:float):
        if (self.circle_state == CiState.WAIT and
            -x > 2*Wiimote.thresh):
            self.circle_state = CiState.RISE
        elif (self.circle_state == CiState.RISE and
              x > Wiimote.thresh):
            self.circle_state = CiState.PEAK
        elif (self.circle_state == CiState.PEAK and
              mag - 100 > (Wiimote.mag_thresh)):
            self.circle_state = CiState.FALL

    def parse_gesture(self):
        x, y, z, mag = self.last_event.data()
        self.prev_acc = (x, y, z)
        
        
        # state machine
        self.get_rest(z, mag)
        self.parse_swing(x, y, z, mag)
        self.parse_circle(x, y, z, mag)
        
        # interactions

        # reset swing if partially through circle
        if (self.circle_state == CiState.PEAK):
            self.swing_state = SwState.WAIT

        # when at rest, check if we saw a gesture / clean up partial gestures
        if (self.at_rest):
            if (self.circle_state != CiState.FALL):
                self.circle_state = CiState.WAIT
            else:
                # CIRCLE DETECTED!!
                print(f"detected CIRCLE ({self.last_event.time}) ------------------")
                self.events.append(Gesturevent(GVType.RECV, self.target))
                self.vec_clk += 1
                self.circle_state = CiState.WAIT
                self.swing_state = SwState.WAIT # circle gesture contains a swing gesture
                                                # when done quickly
            if (self.swing_state != SwState.STOP):
                self.swing_state = SwState.WAIT
            else:
                # SWING DETECTED!!
                print(f"detected SWING ({self.last_event.time}) -----------------")
                self.events.append(Gesturevent(GVType.SEND, self.target))
                self.vec_clk += 1
                self.swing_state = SwState.WAIT

    
    def parse_doubletap(self):
        if (self.btnB_dt == DTState.WAIT and self.buttons["B"]):
            self.btnB_dt = DTState.PRESS
            self.btnB_to = time.time()
        elif (self.btnB_dt == DTState.PRESS and not self.buttons["B"]):
            self.btnB_dt = DTState.BETWEEN
        elif (self.btnB_dt == DTState.BETWEEN and self.buttons["B"]):
            self.btnB_dt = DTState.DOUBLE
        elif (self.btnB_dt != DTState.DOUBLE and 
              (time.time() - self.btnB_to) > self.doubletap_timeout):
            self.btnB_dt = DTState.WAIT

    def parse_button(self):
        key, pressed = self.last_event.data()
        #print((key, pressed))
        
        if (key == lib.XWII_KEY_A):
            self.buttons["A"] = pressed
        if (key == lib.XWII_KEY_B):
            self.buttons["B"] = pressed
        if (key == lib.XWII_KEY_LEFT):
            self.buttons["L"] = pressed
        if (key == lib.XWII_KEY_RIGHT):
            self.buttons["R"] = pressed
        if (key == lib.XWII_KEY_UP):
            self.buttons["U"] = pressed
        if (key == lib.XWII_KEY_DOWN):
            self.buttons["D"] = pressed
        if (key == lib.XWII_KEY_PLUS):
            self.buttons["+"] = pressed
        if (key == lib.XWII_KEY_MINUS):
            self.buttons["-"] = pressed

        self.parse_doubletap()
        #print(self.buttons)
        #if pressed:
        #    print(f"keycode: {key} / {lib.XWII_KEY_LEFT}")
        
    def manage_state(self):        
        if (self.btnB_dt == DTState.DOUBLE):
            self.new_events = False

    def process_event(self):
        self.load_event()
        if self.last_event is None:
            # wii remote has stopped receiving events/data
            # reasonable thing to do here is nothing
            pass
        elif self.last_event.wv_type is lib.XWII_EVENT_ACCEL:
            self.parse_gesture()
        elif self.last_event.wv_type is lib.XWII_EVENT_KEY:
            self.parse_button()
        
        self.manage_state()

    def init_events(self, events: list[Gesturevent]):
        self.events = events

# wii remote that takes its inputs from an actual interface
class WiimoteLive(Wiimote):
    def __init__(self, player:int, iface):
        super().__init__(player)
        self.iface = iface

    def load_event(self):
        event = ffi.new("struct xwii_event *")
        lib.xwii_iface_dispatch(self.iface, event, ffi.sizeof(event[0]))
        if (self.new_events):
            if (event.type is lib.XWII_EVENT_ACCEL):
                mag = get_magnitude(
                       event.v.abs[0].x, event.v.abs[0].y, event.v.abs[0].z)
                self.last_event = Wiivent(lib.XWII_EVENT_ACCEL, time.time()-self.start,
                    acc=(event.v.abs[0].x / mag * 100,
                         event.v.abs[0].y / mag * 100,
                         event.v.abs[0].z / mag * 100,
                         mag))
            elif (event.type is lib.XWII_EVENT_KEY):
                #print(f"{event.time}: {event.v.key.code}, {event.v.key.state}")
                self.last_event = Wiivent(lib.XWII_EVENT_KEY, time.time()-self.start,  
                    key=(event.v.key.code, bool(event.v.key.state)))
        else:
            self.last_event = None

# wii remote that takes its inputs from a test file
class WiimoteSim(Wiimote):
    def __init__(self, player: int, filename:str):
        super().__init__(player)
        self.filename = filename
        self.source = open(filename, "r")

    def load_event(self):
        data = self.source.readline().split(',')
        if (len(data) < 2):
            #sys.exit() 
            self.last_event = None
            return
        if (data[1] == 'A'):
            ispressed = (data[2] == 'PRESSED')
            self.last_event = (
                Wiivent(lib.XWII_EVENT_KEY, float(data[0]), key=(lib.XWII_KEY_A, ispressed)))
        else:
            mag = float(data[10])
            self.last_event = (
                Wiivent(lib.XWII_EVENT_ACCEL, float(data[0]),
                        acc=(float(data[1]), float(data[2]),
                             float(data[3]), mag)))

def get_magnitude(x, y, z):
    return math.sqrt((x * x) + (y * y) + (z * z))

def enumerate(wiimotes: list[Wiimote]):
    wii_monitor = ffi.new("struct xwii_monitor **")
    wii_monitor = lib.xwii_monitor_new(False, False)
    if wii_monitor == ffi.NULL:
        print("in enumerate(): xwii_monitor_new() returned NULL.")

    for player in range(0,Wiimote.max_players):
        # get device file path
        ent = ffi.new("char *")
        ent = lib.xwii_monitor_poll(wii_monitor)
        # if null, no more wiimotes found
        if ent == ffi.NULL:
            break
        # convert each file path into an interface, and open it.
        iface = ffi.new("struct xwii_iface **")
        lib.xwii_iface_new(iface, ent)
        lib.xwii_iface_open(iface[0],
            lib.xwii_iface_available(iface[0]) | lib.XWII_IFACE_WRITABLE)
        wiimotes.append(WiimoteLive(player, iface[0]))
