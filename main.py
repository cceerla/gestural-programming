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

print(wiimotes)

#event0 = Wiivent(lib.XWII_EVENT_KEY, 0, key=(lib.XWII_KEY_A, True))
#event1 = Wiivent(lib.XWII_EVENT_KEY, 0, acc=(0,0,100))
#print(event1.data())

for i in range(0,800):
    for wiimote in wiimotes:
        wiimote.process_event()
        if (len(wiimote.recvs) > 0):
            arrow = choreo.create_arrow(wiimotes, wiimote.recvs[0], True)
            if (arrow):
                arrows.append(arrow)
    #print(f"{wiimotes[0].state} ({wiimotes[0].last_event.time})")
    #print(wiimotes[0].last_event)
#choreo.check_all_recvs(wiimotes)
for wiimote in wiimotes:
    print(f"s: {wiimote.sends} r:{wiimote.recvs}")
choreo.check_trailing_sends(wiimotes)
print(arrows)
