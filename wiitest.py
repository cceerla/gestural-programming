import time
import os
import sys
import math
from enum import Enum
from _xwiimote import ffi, lib

# Quincy's recommendations:
#   Kalman filter
#   Normalize!!
#   play back recordings

# GLOBAL VARIABLES

start_time = time.time()
last_movement = time.time()
thresh = 40
mag_thresh = 30
timeout = .1


# wii remote interfaces and event stream
xwii_iface = []

XWS = Enum('XWS', [('WAIT', 1), ('WRITE', 2)])
XW_state = XWS.WAIT

DSS = Enum('DSS', [('START', 1), ('ACCZ', 2), ('ACCY', 3)])
DS_state = DSS.START

BUS = Enum('BUS', [('START', 1), ('SEENZ', 2), ('SEENX', 3), ('SEENY', 4), ('BOTH', 5), ('Z',6)])
BU_state = BUS.START

recording_num = 0
curr_recording = None

x_peak = False
y_peak = False
z_peak = False
moving = False

# stats
magnitude = 0
at_rest = False
a_x = 0 # acceleration (normalized)
a_y = 0
a_z = 0
v_x = 0 # velocity
v_y = 0
v_z = 0
p_x = 0 # position
p_y = 0
p_z = 0
g_x = 0 # gravity
g_y = 0
g_z = 0
r_x = 0 # last raw acc
r_y = 0
r_z = 0
i_x = 0 # impulse (not normalized)
i_y = 0
i_z = 0

def curr_time():
    return time.time() - start_time

# prints cffi strings from a list
def print_strings(ffistrs):
    for cstr in ffistrs:
        print(ffi.string(cstr))

# loads global variable xwii_devices with all of the device strings.
def xw_enumerate():
    wii_monitor = ffi.new("struct xwii_monitor **")
    wii_monitor = lib.xwii_monitor_new(False, False)
    if wii_monitor == ffi.NULL:
        print("in enumerate(): xwii_monitor_new() returned NULL.")

    while (1):
        # get device file path
        ent = ffi.new("char *")
        ent = lib.xwii_monitor_poll(wii_monitor)
        # if null, no more wiimotes found
        if ent == ffi.NULL:
            break
        # convert each file path into an interface, and open it.
        iface = ffi.new("struct xwii_iface **")
        lib.xwii_iface_new(iface, ent)
        lib.xwii_iface_open(iface[0],
            lib.xwii_iface_available(iface[0]) | lib.XWII_IFACE_WRITABLE)
        xwii_iface.append(iface[0])

def xw_get_battery(device:int=0):    
    battery_level = ffi.new("uint8_t *")
    lib.xwii_iface_get_battery(xwii_iface[device], battery_level)
    return battery_level[0]

def xw_get_event(device:int=0):
    event = ffi.new("struct xwii_event *")
    lib.xwii_iface_dispatch(xwii_iface[device], event, ffi.sizeof(event[0]))
    return event

def get_magnitude(x:int, y:int, z:int):
    return math.sqrt((x * x) + (y * y) + (z * z))


def open_recording(num:int):
    global curr_recording
    global start_time
    curr_recording = open(f"recordings/gesture_{num}.csv", "w")
    start_time = time.time() 

def record():
    global curr_recording
    curr_recording.write(f"{curr_time()},{a_x},{a_y},{a_z}," + 
        f"{v_x},{v_y},{v_z},{i_x},{i_y},{i_z},{magnitude}\r\n")

def close_recording(num:int):
    global curr_recording
    curr_recording.close()
    os.system(f"xclip -selection clipboard recordings/gesture_{num}.csv")
    print("Gesture copied to clipboard in CSV format.")

def get_gravity(x: int, y:int, z:int):
    global g_x
    global g_y
    global g_z
    gravity_component = get_magnitude(x, y, z)
    if (abs(gravity_component - 100) < 2):
        g_x = a_x
        g_y = a_y
        g_z = a_z
        #print(f"at rest: <{a_x}, {a_y}, {a_z}> -> {gravity_component}")

def update_stats(last_event):
    global magnitude
    global a_x
    global a_y
    global a_z
    global v_x
    global v_y
    global v_z
    global p_x
    global p_y
    global p_z
    global r_x
    global r_y
    global r_z
    global i_x
    global i_y
    global i_z

    get_gravity(last_event.v.abs[0].x,
                last_event.v.abs[0].y,
                last_event.v.abs[0].z)

    if (last_event.type is lib.XWII_EVENT_ACCEL):
        magnitude = get_magnitude(last_event.v.abs[0].x,
                                  last_event.v.abs[0].y,
                                  last_event.v.abs[0].z)
        if magnitude != 0:
            a_x = last_event.v.abs[0].x / magnitude * 100
            a_y = last_event.v.abs[0].y / magnitude * 100
            a_z = last_event.v.abs[0].z / magnitude * 100
        else:
            a_x = 0
            a_y = 0
            a_z = 0
        i_x = last_event.v.abs[0].x - r_x
        i_y = last_event.v.abs[0].y - r_y
        i_z = last_event.v.abs[0].z - r_z
        r_x = last_event.v.abs[0].x
        r_y = last_event.v.abs[0].y
        r_z = last_event.v.abs[0].z
        v_x += (a_x - g_x)/10
        v_y += (a_y - g_y)/10
        v_z += (a_z - g_z)/10
        p_x += v_x
        p_y += v_y
        p_z += v_z

# last_event is of type cdata struct xwii_event *
def record_gesture(last_event):
    global XW_state
    global recording_num

    if XW_state == XWS.WAIT:
        if (last_event.type is lib.XWII_EVENT_KEY
                and last_event.v.key.code == lib.XWII_KEY_A
                and last_event.v.key.state):
            XW_state = XWS.WRITE
            # task on state transition...
            open_recording(recording_num)

    if XW_state == XWS.WRITE:
        if last_event.type is lib.XWII_EVENT_ACCEL:
            record()
            
        if (last_event.type is lib.XWII_EVENT_KEY
                and last_event.v.key.code == lib.XWII_KEY_A
                and not last_event.v.key.state):
            XW_state = XWS.WAIT
            close_recording(recording_num)
            recording_num += 1

def detect_rest():
    global DS_state
    global BU_state
    global last_movement
    global at_rest

    if (abs(magnitude - 100) > mag_thresh):
        last_movement = time.time()
        at_rest = False
    elif (time.time() - last_movement > timeout):
        at_rest = True

def detect_downswing():
    global DS_state
    if (a_z < -thresh and DS_state is DSS.START):
        DS_state = DSS.ACCZ
    elif (a_y > thresh/2 and DS_state is DSS.ACCZ):
        DS_state = DSS.ACCY
    elif (a_z > thresh and DS_state is DSS.ACCY and BU_state is BUS.START):
        print("SWING DETECTED -----------")
        if (BU_state is not BUS.START):
            print("within a loop")
        DS_state = DSS.START
    elif (at_rest):
        DS_state = DSS.START

def detect_loop():
    global BU_state
    if (a_x < -thresh and BU_state is BUS.START):
        BU_state = BUS.SEENZ
    elif (abs(a_z) < thresh/2 and BU_state is BUS.SEENZ):
        BU_state = BUS.SEENX
    elif (a_y > thresh and BU_state is BUS.SEENX):
        BU_state = BUS.SEENY
    elif (a_x > thresh and BU_state is BUS.SEENY):
        BU_state = BUS.BOTH
    elif (at_rest and BU_state is BUS.BOTH):
        BU_state = BUS.START
        print("LOOP DETECTED -------------")
    elif (at_rest):
        BU_state = BUS.START

def debug_printpeaks():
    global x_peak
    global y_peak
    global z_peak
    global moving
    if (a_x > thresh and moving and not x_peak):
        print("a_x thresh")
        x_peak = True
    if (a_y > thresh and moving and not y_peak):
        print("a_y thresh")
        y_peak = True
    if (a_z > thresh and moving and not z_peak):
        print("a_z thresh")
        z_peak = True
    if (a_x < -thresh and moving and not x_peak):
        print("a_x thresh (-)")
        x_peak = True
    if (a_y < -thresh and moving and not y_peak):
        print("a_y thresh (-)")
        y_peak = True
    if (a_z < -thresh and moving and not z_peak):
        print("a_z thresh (-)")
        z_peak = True
    if (abs(magnitude - 100) > mag_thresh):
        moving = True
    if (abs(a_x) < thresh):
        x_peak = False
    if (abs(a_y) < thresh):
        y_peak = False
    if (abs(a_z) < thresh):
        z_peak = False
    if (abs(magnitude - 100) < mag_thresh):
        moving = False

# MAIN ------------------------------------------------------------------------

xw_enumerate()
print(f"created interfaces: {xwii_iface}")
if len(xwii_iface) < 1:
    print("no wii remotes detected. terminating...")
    sys.exit()

#print(xw_get_battery())

while (1):
    last_event = xw_get_event()
    update_stats(last_event)
    record_gesture(last_event)
    detect_downswing()
    detect_loop()
    detect_rest()
    #debug_printpeaks()
