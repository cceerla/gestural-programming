import os
import sys
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

class Execution:
    def __init__(self, wiimotes):
        self.wiimotes = wiimotes
        self.arrows = []

# TODO: deprecated
def create_arrow(wiimotes: list[wm.Wiimote], recv: wm.Gesturevent, can_remove: bool):
    # we use an external index because we can't modify a list
    # while we are traversing it (even if we break as soon as we
    # modify it)
    i = 0
    arrow = None
    receiver = None
    for send in wiimotes[recv.target].sends: #type(send) is Gesturevent
        # if prior send exists, create the arrow
        if send.timestamp < recv.timestamp:
            arrow = Arrow(send, recv)
            receiver = send.target
            wiimotes[recv.target].sends.remove(send)
            break
        i += 1
        print(f"{can_remove} and {receiver}")
    if can_remove and receiver:
        wiimotes[receiver].recvs.remove(recv)
#    if i < len(wiimotes[recv.target].sends):
        # if loop broke prematurely, then arrow was made
        # so we remove the send we just put into the arrow
#        wiimotes[recv.target].sends.pop(i)
    return arrow

# TODO: deprecated
def check_all_recvs(wiimotes: list[wm.Wiimote]):
    for player in wiimotes:
        for recv in player.recvs:
            arrow = create_arrow(wiimotes, recv, False)
            if arrow is None:
                print("ERROR: recv without matching send")
            else:
                print(arrow)

# TODO: deprecated
def check_trailing_sends(wiimotes: list[wm.Wiimote]):
    for player in wiimotes:
        if len(player.sends) > 0:
            print(f"ERROR: {len(player.sends)} send(s) without matching recv")

# TWO PLAYER CASE (triage)

# precond: len(wiimotes) == 2
def make_arrows(wiimotes: list[wm.Wiimote]) -> list[Arrow]:
    p0 = wiimotes[0].events
    p1 = wiimotes[1].events
    p0_turn = True
    curr_recv = None
    p0_i = 0

    arrows = []
    
    while (p0_i < len(p0)):
        if (p0[p0_i].kind == wm.GVType.RECV):
            if (p1[0].kind == wm.GVType.SEND):
                # make an arrow
                arrows.append(Arrow(p1.pop(0), p0.pop(p0_i)))
            elif (p0[0].kind == wm.GVType.RECV):
                # crash out and kill everyone
                print("Everyone called recv and is waiting: deadlock!!")
                print(f"p0{p0}\np1{p1}\nar{arrows}")
                return None
        else:
            p0_i += 1
    if (len(p0) > 0 or len(p1) > 0):
        print("There are unmatched sends :(")
        print(f"p0{p0}\np1{p1}\nar{arrows}")
        return None
    return arrows
