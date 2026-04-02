# heavily referenced from cffi docs

from cffi import FFI

ffibuilder = FFI()

# START CDEF
ffibuilder.cdef("""


""")
# END CDEF

ffibuilder.set_source("_xwiimote",
"""
    #include <xwiimote.h>
""",
    libraries=['xwiimote'])

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
