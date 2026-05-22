import os
import sys
#from wiimote import Wiimote, WiimoteSim, WiimoteLive
import wiimote as wm
import choreo
import display

wiimotes = []
evt_len = [0,0,0,0]

class color:
    CYAN = '\033[36m'
    RED = '\033[31m'
    CLEAR = '\033[0m'
    BOLD = '\033[1m'

print(f"{color.CYAN}-----------------------------------------------------{color.CLEAR}")
print(f"    {color.BOLD}WII REMOTE GESTURAL CHOREOGRAPHY SYNTHESIZER{color.CLEAR}")
print(f"{color.CYAN}-----------------------------------------------------{color.CLEAR}")

if (len(sys.argv) > 1):
    i = 0
    for filename in sys.argv[1:]:
        try:
            file = open(filename)
            wiimotes.append(wm.WiimoteSim(i, file))
        except: 
            print(f"Something went wrong with accessing the file \"{filename}\".\nIt likely doesn't exist. Check your file names and try again...")
            sys.exit()
        i+= 1
else:
    wm.enumerate(wiimotes)
if (len(wiimotes) == 0):
    print("No Wii Remotes detected. Terminating...")
    sys.exit()

print(f"Wii Remotes detected: {wiimotes}")
if (len(wiimotes) != 2):
    print(f"Choreographic synthesis is only implemented for the {color.CYAN}2-player case{color.CLEAR}; you have {color.CYAN}{len(wiimotes)} players connected{color.CLEAR}.")

print("")

if (isinstance(wiimotes[0], wm.WiimoteLive)):
    print(f"Hold the Wii Remote face-up (A-button pointing towards the sky) with the tip\n(infrared sensor window) slightly higher than the base (nunchuk port).\n")
    print(f"Each player can {color.BOLD}SEND{color.CLEAR} a message to the other by flicking the Wii Remote\nforwards and down with the face up, like an overhand toss.\n")
    print(f"They can also {color.BOLD}RECV{color.CLEAR} a message by drawing a clockwise circle in the air with\nthe tip of their Wii Remote.\n")
    print(f"To {color.BOLD}STOP{color.CLEAR} a particular Wii Remote from participating in the execution, double-tap\nthe B-button.\n")

print(f"Beginning execution.")

if (isinstance(wiimotes[0], wm.WiimoteSim)):
    print(f"Simulating from given files...")

print("")

while (1):
    eventsOngoing = False
    for wiimote in wiimotes:
        wiimote.process_event()
        if (len(wiimote.events) > evt_len[wiimote.player]):
            print(f"Detected event: Player {wiimote.player} {wiimote.events[-1]}")
            evt_len[wiimote.player] += 1
        if (wiimote.last_event is not None):
            eventsOngoing = True
    if (not eventsOngoing):
        break

if (len(wiimotes) != 2):
    print("Execution complete. Final state:")
    for wiimote in wiimotes:
        print(f"Player {wiimote.player}: {wiimote.events}")
    print("Synthesis is only supported for 2 players; terminating.")
    sys.exit()
else:
    print(f"Execution complete. Synthesizing:")
    choreography = choreo.synthesize(wiimotes)
    if (choreography.outcome == choreo.Outcome.VALID):
        print(f"{color.CYAN}-----------------------------------------------------{color.CLEAR}")
        print(f"{color.BOLD}                  VALID EXECUTION :D{color.CLEAR}")
        print(f"{color.CYAN}-----------------------------------------------------{color.CLEAR}")
        print(f"The execution was {color.CYAN}valid{color.CLEAR} and a sequence diagram\nis being generated!")
        display.make_chart("choreo", choreography)
        display.view_chart("choreo")
        display.delete_chart_raw("choreo")
    elif (choreography.outcome == choreo.Outcome.BADSEND):
        print(f"{color.CYAN}-----------------------------------------------------{color.CLEAR}")
        print(f"{color.BOLD}                   TRAILING EVENTS :({color.CLEAR}")
        print(f"{color.CYAN}-----------------------------------------------------{color.CLEAR}")
        print(f"There were trailing Events in the execution that didn't get matched with\ntheir opposites. Event log:")
        for wiimote in wiimotes:
            print(f"Player {wiimote.player}: {wiimote.events}")
    elif (choreography.outcome == choreo.Outcome.BADRECV):
        print(f"{color.CYAN}-----------------------------------------------------{color.CLEAR}")
        print(f"{color.BOLD}                   RECEIVE PURGATORY{color.CLEAR}")
        print(f"{color.CYAN}-----------------------------------------------------{color.CLEAR}")
        print(f"Both players were waiting to Receive a Sent message that would never come\n(because the other player was also waiting.) Event log:")
        for wiimote in wiimotes:
            print(f"Player {wiimote.player}: {wiimote.events}")
    #print(choreography)
    #display.play_random_sound("sounds/success")
