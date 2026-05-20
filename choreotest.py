import os
import sys
#from wiimote import Wiimote, WiimoteSim, WiimoteLive
import wiimote as wm
import choreo
from collections import deque

wiimotes = []
arrows = []

class EventLog:
    def __init__(self, name, s0, r0, s1, r1, s2=deque([]), r2=deque([])):
        self.name = name
        self.s0 = s0
        self.r0 = r0
        self.s1 = s1
        self.r1 = r1
        self.s2 = s2
        self.r2 = r2

good_basicsendrecv = EventLog(
        "good: basic reciprocal pair",
    deque([wm.Gesturevent(0, 1)]),
    deque([wm.Gesturevent(4, 1)]),
    deque([wm.Gesturevent(3, 0)]),
    deque([wm.Gesturevent(2, 0)])
    )

good_twosendrecv = EventLog(
        "good: two sends to two recvs",
    deque([wm.Gesturevent(0, 1), 
     wm.Gesturevent(2, 1)]),
    deque([]),
    deque([]),
    deque([wm.Gesturevent(1, 0), 
     wm.Gesturevent(3, 0)])
    )

good_oneoverlap = EventLog(
        "good: overlapping timestamp for send and unrelated recv",
    deque([wm.Gesturevent(0, 1), 
     wm.Gesturevent(1, 1)]),
    deque([]),
    deque([]),
    deque([wm.Gesturevent(1, 0), 
     wm.Gesturevent(2, 0)])
    )

bad_outoforder = EventLog(
        "bad: recvs precede sends",
    deque([wm.Gesturevent(1, 1), 
     wm.Gesturevent(2, 1)]),
    deque([]),
    deque([]),
    deque([wm.Gesturevent(0, 0), 
     wm.Gesturevent(1, 0)])
    )

bad_toomanysends = EventLog(
        "bad: unmatched sends",
    deque([wm.Gesturevent(1, 1), 
     wm.Gesturevent(2, 1),
     wm.Gesturevent(3, 1),
     wm.Gesturevent(4, 1),
     wm.Gesturevent(5, 1),
     wm.Gesturevent(6, 1),
     wm.Gesturevent(7, 1)]),
    deque([]),
    deque([]),
    deque([wm.Gesturevent(10, 0), 
     wm.Gesturevent(11, 0)])
    )

tests = [good_basicsendrecv, good_twosendrecv, good_oneoverlap, bad_outoforder, bad_toomanysends]

for currentTest in tests:
    player_0_s = currentTest.s0
    player_0_r = currentTest.r0
    player_1_s = currentTest.s1
    player_1_r = currentTest.r1
    player_2_s = currentTest.s2
    player_2_r = currentTest.r2

    wiimotes = [
        wm.WiimoteSim(0, "recordings/empty.csv"),
        wm.WiimoteSim(1, "recordings/empty.csv"),
        wm.WiimoteSim(2, "recordings/empty.csv")]

    wiimotes[0].init_events(player_0_s, player_0_r)
    wiimotes[1].init_events(player_1_s, player_1_r)
    wiimotes[2].init_events(player_2_s, player_2_r)

    print(currentTest.name)
    choreo.check_all_recvs(wiimotes)

