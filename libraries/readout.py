from enum import IntEnum
import usb.core
import usb.util
import struct
import bitstring
from bitstring import BitArray
import time

class Message(IntEnum):
    READOUT_STATUS = 0,
    READOUT_UID = 1,
    HV_ENABLE = 2,
    HV_CURRENT = 3,
    HV_VOLTAGE = 4,
    HV_PID = 5,
    FASTIC_REGISTER = 6,
    FASTIC_VOLTAGE = 7,
    FASTIC_SYNCRESET = 8,
    FASTIC_CALPULSE = 9,
    FASTIC_TIME = 10,
    FASTIC_AURORA = 11,
    USERBOARD_STATUS = 12,
    USERBOARD_INIT = 13,
    USERBOARD_UID = 14,
    USERBOARD_NAME = 15,
    USERBOARD_WRITEPROTECT = 16,
    USERBOARD_VOLTAGE = 17,
    USERBOARD_REGISTER = 18,
    USERBOARD_TOMEMORY = 19,
    USERBOARD_FROMMEMORY = 20,
    UNKNOWN = 21

def getStatus():
    global dev
    data = struct.unpack('ffH', dev.ctrl_transfer(0xC0, Message.READOUT_STATUS, 0, 0, 10))
    print(data)
    bits = BitArray(bin=bin(data[2]))
    print(bits)
    print(bin(data[2]))
    ret = {
        'temperature': data[0],
        'voltage': data[1],
        'pg1V2D': bool(bits[0]),
        'pg1V2T': bool(bits[1]),
        'pg1V2A': bool(bits[2]),
        'pg3V3A': bool(bits[3]),
        'pg1V8D': bool(bits[4]),
        'clockOutputEnabled': bits[5],
        'clockInReset': bits[6],
        'clockLostLock': bits[7],
        'clockLostSignal': bits[8],
    }
    
    return ret
    
def getReadoutUID():
    global dev
    data = struct.unpack('iii', dev.ctrl_transfer(0xC0, Message.READOUT_UID, 0, 0, 12))
    uid = (data[0] << 64) | (data[1] << 32) | data[2]
    return uid

def getHvEnabled():
    global dev
    data = struct.unpack('?', dev.ctrl_transfer(0xC0, Message.HV_ENABLE, 0, 0, 4))
    return data[0]

def setHvEnabled(state):
    global dev
    dev.ctrl_transfer(0x40, Message.HV_ENABLE, 0, 0, bytes((state,)))

def getHvCurrent():
    global dev
    data = struct.unpack('f', dev.ctrl_transfer(0xC0, Message.HV_CURRENT, 0, 0, 4))
    return data[0]

def getHvVoltage():
    global dev
    data = struct.unpack('f', dev.ctrl_transfer(0xC0, Message.HV_VOLTAGE, 0, 0, 4))
    return data[0]

def setHvVoltage(value):
    global dev
    dev.ctrl_transfer(0x40, Message.HV_VOLTAGE, 0, 0, bytearray(struct.pack("f", value)))

# Find our device
dev = usb.core.find(idVendor=0xcafe, idProduct=0x4000)

# Was it found?
if dev is None:
    raise ValueError('Device not found')


setHvEnabled(True)
print(getHvVoltage())
print(getHvCurrent())
setHvVoltage(20)
time.sleep(3)
print(getHvVoltage())
print(getHvCurrent())