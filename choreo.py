import os
import sys
import wiimote as wm

# data structure for a recorded send 
# (maybe recv is a different structure and we use duck typing later?)

# data structure for an arrow

# just use a list of sends
# checkrecv function that checks the buffers(?)

class Arrow:
    def __init__(self, send: wm.Gesturevent, recv: wm.Gesturevent):
        self.send = send
        self.recv = recv

    def __str__(self):
        return (f"{self.recv.target} ({self.send.timestamp}) -->" + 
                f" {self.send.target} ({self.recv.timestamp})")

class EventLog:
    def __init__(self, name, s0, r0, s1, r1):
        self.name = name
        self.s0 = s0
        self.r0 = r0
        self.s1 = s1
        self.r1 = r1

good_basicsendrecv = EventLog(
        "good: basic reciprocal pair",
    [wm.Gesturevent(0, 1)],
    [wm.Gesturevent(4, 1)],
    [wm.Gesturevent(3, 0)],
    [wm.Gesturevent(2, 0)]
    )

good_twosendrecv = EventLog(
        "good: two sends to two recvs",
    [wm.Gesturevent(0, 1), 
     wm.Gesturevent(2, 1)],
    [],
    [],
    [wm.Gesturevent(1, 0), 
     wm.Gesturevent(3, 0)]
    )

good_oneoverlap = EventLog(
        "good: overlapping timestamp for send and unrelated recv",
    [wm.Gesturevent(0, 1), 
     wm.Gesturevent(1, 1)],
    [],
    [],
    [wm.Gesturevent(1, 0), 
     wm.Gesturevent(2, 0)]
    )

bad_outoforder = EventLog(
        "bad: recvs precede sends",
    [wm.Gesturevent(1, 1), 
     wm.Gesturevent(2, 1)],
    [],
    [],
    [wm.Gesturevent(0, 0), 
     wm.Gesturevent(1, 0)]
    )

bad_toomanysends = EventLog(
        "bad: unmatched sends",
    [wm.Gesturevent(1, 1), 
     wm.Gesturevent(2, 1),
     wm.Gesturevent(3, 1),
     wm.Gesturevent(4, 1),
     wm.Gesturevent(5, 1),
     wm.Gesturevent(6, 1),
     wm.Gesturevent(7, 1)],
    [],
    [],
    [wm.Gesturevent(10, 0), 
     wm.Gesturevent(11, 0)]
    )



currentTest = bad_toomanysends

player_0_s = currentTest.s0
player_0_r = currentTest.r0
player_1_s = currentTest.s1
player_1_r = currentTest.r1

wiimotes = [
    wm.WiimoteSim(0, "recordings/empty.csv"),
    wm.WiimoteSim(1, "recordings/empty.csv")]

wiimotes[0].init_events(player_0_s, player_0_r)
wiimotes[1].init_events(player_1_s, player_1_r)

class Execution:
    def __init__(self, wiimotes):
        self.wiimotes = wiimotes
        self.arrows = []

def create_arrow(wiimotes: list[wm.Wiimote], recv: wm.Gesturevent):
    # we use an external index because we can't modify a list
    # while we are traversing it (even if we break as soon as we
    # modify it)
    i = 0
    arrow = None
    for send in wiimotes[recv.target].sends: #type(send) is Gesturevent
        # if prior send exists, create the arrow
        if send.timestamp < recv.timestamp:
            arrow = Arrow(send, recv)
            break
        i += 1
    if i < len(wiimotes[recv.target].sends):
        # if loop broke prematurely, then arrow was made
        # so we remove the send we just put into the arrow
        wiimotes[recv.target].sends.pop(i)
    return arrow

def check_all_recvs(wiimotes: list[wm.Wiimote]):
    for player in wiimotes:
        for recv in player.recvs:
            arrow = create_arrow(wiimotes, recv)
            if arrow is None:
                print("ERROR: recv without matching send")
            else:
                print(arrow)

def check_trailing_sends(wiimotes: list[wm.Wiimote]):
    for player in wiimotes:
        if len(player.sends) > 0:
            print(f"ERROR: {len(player.sends)} send(s) without matching recv")
