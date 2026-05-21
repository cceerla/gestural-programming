import os
import sys
#from wiimote import Wiimote, WiimoteSim, WiimoteLive
import wiimote as wm
import choreo
from collections import deque

class EventLog:
    def __init__(self, name: str, events_0:list[wm.Gesturevent], events_1:list[wm.Gesturevent]):
        self.name = name
        self.events_0 = events_0
        self.events_1 = events_1

def run_tests(tests:list[EventLog]):
    for test in tests:
        wiimotes = [
            wm.WiimoteSim(0, "recordings/empty.csv"),
            wm.WiimoteSim(1, "recordings/empty.csv")
            ]

        wiimotes[0].init_events(test.events_0)
        wiimotes[1].init_events(test.events_1)

        print(test.name)
        arrows = choreo.make_arrows(wiimotes)
        if (arrows):
            print(f"Arrows created: \n{arrows}")
        else:
            print("Invalid execution.")

run_tests(
        [EventLog("Good: Single S/R",
                  [wm.Gesturevent(wm.GVType.SEND, 1)],
                  [wm.Gesturevent(wm.GVType.RECV, 0)],
                  )
        ]
    )
