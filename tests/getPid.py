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

P = 10
I = 0.8
D = 0
pid = bytearray(struct.pack("fff", P, I, D))

dev.ctrl_transfer(0x40, 6, 0, 0, pid)


pid = struct.unpack('fff', dev.ctrl_transfer(0xC0, 6, 0, 0, len(pid)))

print(pid)