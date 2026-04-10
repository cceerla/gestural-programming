import time
import os
import sys
from enum import Enum
from _xwiimote import ffi, lib

# GLOBAL VARIABLES

start_time = time.time()
thresh = 160

# wii remote interfaces and event stream
xwii_iface = []

XWS = Enum('XWS', [('WAIT', 1), ('WRITE', 2)])
XW_state = XWS.WAIT

DSS = Enum('DSS', [('START', 1), ('ACCZ', 2), ('ACCY', 3), ('DECZ', 4)])
DS_state = DSS.START

recording_num = 0
curr_recording = None

# stats
a_x = 0 # acceleration
a_y = 0
a_z = 0
v_x = 0 # velocity
v_y = 0
v_z = 0
p_x = 0 # position
p_y = 0
p_z = 0
g_x = 0
g_y = 0
g_z = 0

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

def open_recording(num:int):
    global curr_recording
    curr_recording = open(f"recordings/gesture_{num}.csv", "w")

def record():
    global curr_recording
    curr_recording.write(f"{curr_time()},{a_x},{a_y},{a_z}," + 
        f"{v_x},{v_y},{v_z},{p_x},{p_y},{p_z}\r\n")

def close_recording(num:int):
    global curr_recording
    curr_recording.close()
    os.system(f"xclip -selection clipboard recordings/gesture_{num}.csv")
    print("Gesture copied to clipboard in CSV format.")

def update_stats(last_event):
    global a_x
    global a_y
    global a_z
    global v_x
    global v_y
    global v_z
    global p_x
    global p_y
    global p_z

    if (last_event.type is lib.XWII_EVENT_ACCEL):
        a_x = last_event.v.abs[0].x
        a_y = last_event.v.abs[0].y
        a_z = last_event.v.abs[0].z
        v_x += a_x
        v_y += a_y
        v_z += a_z
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

def detect_downswing():
    global DS_state
    if (a_z < -thresh and DS_state is DSS.START):
        DS_state = DSS.ACCZ
    if (a_y > thresh/2 and DS_state is DSS.ACCZ):
        DS_state = DSS.ACCY
    if (a_z > thresh and DS_state is DSS.ACCY):
        print("swing detected")
        DS_state = DSS.DECZ
        DS_state = DSS.START

# MAIN ------------------------------------------------------------------------

xw_enumerate()
print(f"created interfaces: {xwii_iface}")
if len(xwii_iface) < 1:
    print("no wii remotes detected. terminating...")
    sys.exit()

while (1):
    last_event = xw_get_event()
    update_stats(last_event)
    record_gesture(last_event)
    detect_downswing()
