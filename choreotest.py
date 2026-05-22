import os
import sys
import re
#from wiimote import Wiimote, WiimoteSim, WiimoteLive
import wiimote as wm
import choreo
import display

alphanum = re.compile('[^a-zA-Z0-9]')

class EventLog:
    def __init__(self, name: str, events_0:list[wm.Gesturevent], events_1:list[wm.Gesturevent]):
        self.name = name
        self.events_0 = events_0
        self.events_1 = events_1

def run_tests(tests:list[EventLog]):
    global alphanum

    for test in tests:
        wiimotes = [
            wm.WiimoteSim(0, "recordings/empty.csv"),
            wm.WiimoteSim(1, "recordings/empty.csv")
            ]

        wiimotes[0].init_events(test.events_0)
        wiimotes[1].init_events(test.events_1)

        print("-------------------------------------------------------")
        print(test.name)
        print("-------------------------------------------------------")
        choreography = choreo.synthesize(wiimotes)
        print(choreography)
        if (choreography.outcome == choreo.Outcome.VALID):
            stripped_name = alphanum.sub('', test.name)
            display.chart_choreography(f"test_out/{stripped_name}", choreography)

run_tests(
        [
        EventLog("Good: Empty Execution",
            [],
            [],
            ),
        EventLog("Good: Single S/R",
            [wm.Gesturevent(wm.GVType.SEND, 1)],
            [wm.Gesturevent(wm.GVType.RECV, 0)],
            ),
        EventLog("Good: Reciprocal S/R",
            [wm.Gesturevent(wm.GVType.SEND, 1),
             wm.Gesturevent(wm.GVType.RECV, 1)],
            [wm.Gesturevent(wm.GVType.RECV, 0),
             wm.Gesturevent(wm.GVType.SEND, 0)],
            ),
        EventLog("Good: Series of Sends and Recvs",
            [wm.Gesturevent(wm.GVType.SEND, 1),
             wm.Gesturevent(wm.GVType.SEND, 1),
             wm.Gesturevent(wm.GVType.RECV, 1)],
            [wm.Gesturevent(wm.GVType.RECV, 0),
             wm.Gesturevent(wm.GVType.SEND, 0),
             wm.Gesturevent(wm.GVType.RECV, 0)],
            ),
        EventLog("Good: Long series of Sends for Recvs",
            [wm.Gesturevent(wm.GVType.SEND, 1),
             wm.Gesturevent(wm.GVType.SEND, 1),
             wm.Gesturevent(wm.GVType.SEND, 1),
             wm.Gesturevent(wm.GVType.SEND, 1),
             wm.Gesturevent(wm.GVType.SEND, 1),
             wm.Gesturevent(wm.GVType.SEND, 1)],
            [wm.Gesturevent(wm.GVType.RECV, 0),
             wm.Gesturevent(wm.GVType.RECV, 0),
             wm.Gesturevent(wm.GVType.RECV, 0),
             wm.Gesturevent(wm.GVType.RECV, 0),
             wm.Gesturevent(wm.GVType.RECV, 0),
             wm.Gesturevent(wm.GVType.RECV, 0)],
            ),
        EventLog("Bad: Unpaired Send 0",
            [wm.Gesturevent(wm.GVType.SEND, 1)],
            [],
            ),
        EventLog("Bad: Unpaired Recv 0",
            [wm.Gesturevent(wm.GVType.RECV, 1)],
            [],
            ),
        EventLog("Bad: Unpaired Recv 1",
            [],
            [wm.Gesturevent(wm.GVType.RECV, 0)],
            ),
        EventLog("Bad: Unpaired Send 1",
            [],
            [wm.Gesturevent(wm.GVType.SEND, 0)],
            ),
        EventLog("Bad: Two Recvs",
            [wm.Gesturevent(wm.GVType.RECV, 1)],
            [wm.Gesturevent(wm.GVType.RECV, 0)],
            ),
        EventLog("Bad: Two Sends",
            [wm.Gesturevent(wm.GVType.SEND, 1)],
            [wm.Gesturevent(wm.GVType.SEND, 0)],
            ),
        EventLog("Bad: Causal Loop",
            [wm.Gesturevent(wm.GVType.RECV, 1),
             wm.Gesturevent(wm.GVType.SEND, 1)],
            [wm.Gesturevent(wm.GVType.RECV, 0),
             wm.Gesturevent(wm.GVType.SEND, 0)],
            ),
        ]
    )
