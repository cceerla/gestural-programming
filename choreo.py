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

class Outcome(Enum):
    VALID = 0
    BADSEND = 1
    BADRECV = 2

class Arrow:
    def __init__(self, send: wm.Gesturevent, recv: wm.Gesturevent):
        self.send = send
        self.recv = recv

    def __str__(self):
        return (f"{self.recv.target} -->" + 
                f" {self.send.target}")
    def __repr__(self):
        return self.__str__()

class Choreography:
    def __init__(self, outcome:Outcome, hosts:list[list[wm.Gesturevent]], arrows:list[Arrow]):
        self.outcome = outcome
        self.hosts = hosts
        self.arrows = arrows

    def __str__(self):
        output = ""
        if (self.outcome == Outcome.VALID):
            output += "Valid execution.\n"
            output += f"Arrows: {self.arrows}"
        elif (self.outcome == Outcome.BADSEND):
            output += "Invalid Execution; trailing Sends.\n"
            output += "State at error:\n"
            for p in range(0, len(self.hosts)):
                output += f"p{p}: {self.hosts[p]}\n"
            output += f"Ar: {self.arrows}"
        elif (self.outcome == Outcome.BADRECV):
            output += "Invalid Execution; Recv purgatory.\n"
            output += "State at error:\n"
            for p in range(0,len(self.hosts)):
                output += f"p{p}: {self.hosts[p]}\n"
            output += f"Ar: {self.arrows}"
        return output

# TWO PLAYER CASE (triage)

# precond: len(wiimotes) == 2
def synthesize(wiimotes: list[wm.Wiimote]) -> Choreography:
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
                    return Choreography(Outcome.BADRECV, [p0, p1], arrows)
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
        return Choreography(Outcome.BADSEND, [p0, p1], arrows)
    return Choreography(Outcome.VALID, [p0, p1], arrows)
