import time
from _xwiimote import ffi, lib

xwii_iface = []
last_event = ffi.new("struct xwii_event")

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
    last_event = event[0]
    
    match event[0].type:
        case lib.XWII_EVENT_ACCEL:
            print(f"<{event[0].v.abs[0].x:+04d}," + 
                  f" {event[0].v.abs[0].y:+04d}," + 
                  f" {event[0].v.abs[0].z:+04d}>")
        case lib.XWII_EVENT_KEY:
            if event[0].v.key.state:
                print(f"key: {event[0].v.key.code}")

def handle_fsm():
    pass

# MAIN

xw_enumerate()
print(f"created interfaces: {xwii_iface}")

print(xw_get_battery(0))

while (1):
    xw_get_event()
    handle_fsm()
