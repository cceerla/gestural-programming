import time
import os
from enum import Enum
from _xwiimote import ffi, lib

xwii_iface = []
last_event = ffi.new("struct xwii_event*")

XWS = Enum('XWS', [('WAIT', 1), ('WRITE', 2)])
XW_state = XWS.WAIT

start_time = time.time()

recording_num = 0
curr_recording = None

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
    global last_event

    event = ffi.new("struct xwii_event *")
    lib.xwii_iface_dispatch(xwii_iface[device], event, ffi.sizeof(event[0]))
    last_event = event[0]

def open_recording(num:int):
    global curr_recording
    curr_recording = open(f"recordings/gesture_{num}.csv", "w")

def record(x, y, z):
    global curr_recording
    curr_recording.write(f"{curr_time()},{x},{y},{z}\r\n")

def close_recording(num:int):
    global curr_recording
    curr_recording.close()
    os.system(f"xclip -selection clipboard recordings/gesture_{num}.csv")
    print("Gesture copied to clipboard in CSV format.")

def handle_fsm():
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
            record(last_event.v.abs[0].x,
                   last_event.v.abs[0].y,
                   last_event.v.abs[0].z)
            
        if (last_event.type is lib.XWII_EVENT_KEY
                and last_event.v.key.code == lib.XWII_KEY_A
                and not last_event.v.key.state):
            XW_state = XWS.WAIT
            close_recording(recording_num)
            recording_num += 1

# MAIN ------------------------------------------------------------------------

xw_enumerate()
print(f"created interfaces: {xwii_iface}")

while (1):
    xw_get_event()
    handle_fsm()
