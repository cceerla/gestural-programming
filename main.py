import os
import sys
#from wiimote import Wiimote, WiimoteSim, WiimoteLive
import wiimote as wm
import choreo

wiimotes = []
arrows = []

if (len(sys.argv) > 1):
    i = 0
    for filename in sys.argv[1:]:
        wiimotes.append(wm.WiimoteSim(i, filename))
        i+= 1
else:
    wm.enumerate(wiimotes)
if (len(wiimotes) == 0):
    print("no wii remotes detected. terminating...")
    sys.exit()

print(f"wiimotes detected: {wiimotes}")

#event0 = Wiivent(lib.XWII_EVENT_KEY, 0, key=(lib.XWII_KEY_A, True))
#event1 = Wiivent(lib.XWII_EVENT_KEY, 0, acc=(0,0,100))
#print(event1.data())

while (1):
    eventsOngoing = False
    for wiimote in wiimotes:
        wiimote.process_event()
        if (len(wiimote.recvs) > 0):
            arrow = choreo.create_arrow(wiimotes, wiimote.recvs[0], True)
            if (arrow):
                arrows.append(arrow)
                print(f"arrow found: {arrow}")
        if (wiimote.last_event is not None):
            eventsOngoing = True
    if (not eventsOngoing):
        break

print(f"execution complete. end state:")
#choreo.check_all_recvs(wiimotes)
for wiimote in wiimotes:
    print(f"{wiimote}: s: {wiimote.sends} r:{wiimote.recvs}")
choreo.check_trailing_sends(wiimotes)
print(arrows)
