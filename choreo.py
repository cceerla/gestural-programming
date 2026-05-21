import os
import sys
from enum import Enum
import wiimote as wm

# data structure for a recorded send 
# (maybe recv is a different structure and we use duck typing later?)

# data structure for an arrow

# just use a list of sends
# checkrecv function that checks the buffers(?)

# no total order: only assuming logical time / causal consistency
# logical counter

class Arrow:
    def __init__(self, send: wm.Gesturevent, recv: wm.Gesturevent):
        self.send = send
        self.recv = recv

    def __str__(self):
        return (f"{self.recv.target} -->" + 
                f" {self.send.target}")
    def __repr__(self):
        return self.__str__()

class Outcome(Enum):
    VALID = 0
    BADSEND = 1
    BADRECV = 2

# TWO PLAYER CASE (triage)

# precond: len(wiimotes) == 2
def make_arrows(wiimotes: list[wm.Wiimote]) -> tuple[Outcome, list[wm.Gesturevent], list[wm.Gesturevent], list[Arrow]]:
    p0 = wiimotes[0].events
    p1 = wiimotes[1].events
    p0_turn = True
    p0_i = 0
    p1_i = 0

    arrows = []
    
    while (p0_i < len(p0) and p1_i < len(p1)): # (while we're still in at least one)
        if (p0_turn):
            if (p0[p0_i].kind == wm.GVType.RECV): # if we hit a recv,
                # extra logic on this side: if both blocked, crash out
                # (we only need this once)
                if (p1[0].kind == wm.GVType.RECV):
                    print("Both are waiting to recv: womp womp.")
                    return (Outcome.BADRECV, p0, p1, arrows)
                else:
                    arrows.append(Arrow(p1.pop(0), p0.pop(p0_i)))
                    p0_i -= 1
                # block
                p0_turn = False
            else:
                if (p1[0].kind == wm.GVType.RECV): # if we hit a send, we see if
                                                   # we can pair it w a recv
                                                   # at the beginning of the other
                    arrows.append(Arrow(p0.pop(p0_i), p1.pop(0)))
                else:
                    # if the other isn't blocked, keep going until we block
                    p0_i += 1
        else: # when p1 isn't blocked, we do the reciprocal
            if (p1[p1_i].kind == wm.GVType.RECV):
                if (p1[0].kind == wm.GVType.SEND):
                    arrows.append(Arrow(p0.pop(0), p1.pop(p0_i)))
                    p0_i -= 1
                p0_turn = True
            else:
                if (p0[0].kind == wm.GVType.RECV):
                    arrows.append(Arrow(p1.pop(p1_i), p0.pop(0)))
                else:
                    p1_i += 1
    if (len(p0) > 0 or len(p1) > 0):
        print("Unmatched sends: womp womp.")
        return (Outcome.BADSEND, p0, p1, arrows)
    return (Outcome.VALID, p0, p1, arrows)
