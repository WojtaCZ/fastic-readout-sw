import usb.core
import usb.util
import struct

# Find our device
dev = usb.core.find(idVendor=0xcafe, idProduct=0x4000)

# Was it found?
if dev is None:
    raise ValueError('Device not found')



# 11,12,13 = PID
# 4 = voltage

value = 0.5

ba = bytearray(struct.pack("f", value))
print(struct.unpack('f', ba))
print(ba)
print(dev.ctrl_transfer(0x40, 12, 0, 0, ba))