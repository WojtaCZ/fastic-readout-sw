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
    READOUT_FIRMWARE = 2,
    HV_ENABLE = 3,
    HV_CURRENT = 4,
    HV_VOLTAGE = 5,
    HV_PID = 6,
    FASTIC_REGISTER = 7,
    FASTIC_VOLTAGE = 8,
    FASTIC_SYNCRESET = 9,
    FASTIC_CALPULSE = 10,
    FASTIC_TIME = 11,
    FASTIC_AURORA = 12,
    USERBOARD_STATUS = 13,
    USERBOARD_INIT = 14,
    USERBOARD_UID = 15,
    USERBOARD_NAME = 16,
    USERBOARD_WRITEPROTECT = 17,
    USERBOARD_VOLTAGE = 18,
    USERBOARD_REGISTER = 19,
    USERBOARD_TOMEMORY = 20,
    USERBOARD_FROMMEMORY = 21,
    UNKNOWN = 22
    
def init():
    global dev
    dev = usb.core.find(idVendor=0xcafe, idProduct=0x4000)

    if dev is None:
        raise ValueError("Readout was not found!")

    # Detach kernel driver if necessary
    if dev.is_kernel_driver_active(0):
        dev.detach_kernel_driver(0)

    # Set the active configuration
    dev.set_configuration()

    # Claim the interface
    usb.util.claim_interface(dev, 0)
    
    fw = getReadoutFirmware()
    build_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(fw['timestamp']))
    
    print(f"FastIC+ readout connected!")
    print(f"   UID: {getReadoutUID()}")
    print(f"   Firmware: {fw['revision'].decode('utf-8')}")
    print(f"   Build date: {build_date}")
    print()
    
    

def getStatus():
    global dev
    data = struct.unpack('ffH', dev.ctrl_transfer(0xC0, Message.READOUT_STATUS, 0, 0, 10))
    bits = BitArray(bin=bin(data[2]))
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
    return hex(uid)

def getReadoutFirmware():
    global dev
    data = struct.unpack('7p33pI', dev.ctrl_transfer(0xC0, Message.READOUT_FIRMWARE, 0, 0, 7+33+4))
    
    ret = {
        'revision': data[0],
        'branch': data[1],
        'timestamp': data[2]
    }
        
    return ret

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


def getFasticRegister(fastic, register):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    data = struct.unpack('B', dev.ctrl_transfer(0xC0, Message.FASTIC_REGISTER, register, fastic, 1))
    return data[0]

def setFasticRegister(fastic, register, value, force = False):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    dev.ctrl_transfer(0x40, Message.FASTIC_REGISTER, register | ((force & 0x01) << 15), fastic, bytearray(struct.pack("B", value)))

def getFasticVoltage(fastic):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    data = struct.unpack('f', dev.ctrl_transfer(0xC0, Message.FASTIC_VOLTAGE, 0, fastic, 4))
    return data[0]

def getFasticSyncReset(fastic):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    data = struct.unpack('?', dev.ctrl_transfer(0xC0, Message.FASTIC_SYNCRESET, 0, fastic, 1))
    return data[0]

def setFasticSyncReset(fastic, state):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    dev.ctrl_transfer(0x40, Message.FASTIC_SYNCRESET, state, fastic, [0])
    
def getFasticCalPulse(fastic):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    data = struct.unpack('?', dev.ctrl_transfer(0xC0, Message.FASTIC_CALPULSE, 0, fastic, 1))
    return data[0]

def setFasticCalPulse(fastic, state):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    dev.ctrl_transfer(0x40, Message.FASTIC_CALPULSE, state, fastic, [0])
    
def getFasticTime(fastic):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    data = struct.unpack('?', dev.ctrl_transfer(0xC0, Message.FASTIC_TIME, 0, fastic, 1))
    return data[0]

def getFasticAurora(fastic):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    data = struct.unpack('?', dev.ctrl_transfer(0xC0, Message.FASTIC_AURORA, 0, fastic, 1))
    return data[0]

def setFasticAurora(fastic, state):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    dev.ctrl_transfer(0x40, Message.FASTIC_AURORA, state & 0x0001, fastic, [0])
    
#def getUserboardStatus():
    
def getUserboardRegister(register):
    global dev
    data = struct.unpack('B', dev.ctrl_transfer(0xC0, Message.USERBOARD_REGISTER, register, 0, 1))
    return data[0]

def getUserboardUID():
    global dev
    data = struct.unpack('BBBBBBBBBBBBBBBBB', dev.ctrl_transfer(0xC0, Message.USERBOARD_UID, 0, 0, 17))
    shortID = data[0]
    uid = data[1] << 56 | data[2] << 48 | data[3] << 40 | data[4] << 32 | data[5] << 24 | data[6] << 16 | data[7] << 8 | data[8]
    return uid

def getUserboardName():
    global dev
    data = dev.ctrl_transfer(0xC0, Message.USERBOARD_NAME, 0, 0, 64).decode("utf-8")
    return data

def bulkReceive(fastic, duration, filename):
    global dev
    
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    if fastic == 1:
        ENDPOINT = 0x83
    else:
        ENDPOINT = 0x84
        
    setFasticAurora(fastic, False)
    
    tmp = usb.util.create_buffer(4096)
            
    # Read any old data that we dont care about and trash it
    while True:
        try:
            dev.read(ENDPOINT, tmp, timeout=1)
        except usb.core.USBError as e:
            break
        

    with open(filename, "wb") as buffer_file:
        print(f"Receiving data and writing to {filename}...")
        try:
            # Read data from the USB endpoint
            data = usb.util.create_buffer(4096)
            
            timeStart = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
            totalBytes = 0

            setFasticAurora(fastic, True)
            
            while time.clock_gettime_ns(time.CLOCK_MONOTONIC) - timeStart < (duration*1000000):
                len = dev.read(ENDPOINT, data, timeout=1000)
                if len != 0:
                    totalBytes = totalBytes + len
                    # Write the received data to the file
                    buffer_file.write(data[:len])

            setFasticAurora(fastic, False)
            print(f"Received {totalBytes/1000} kB of data")

        except usb.core.USBError as e:
            setFasticAurora(fastic, False)
            
            if e.errno == 110:  # Timeout error
                print("Timeout reached, stopping data reception.")
            else:
                print(f"USB Error: {e}")
        except KeyboardInterrupt:
            setFasticAurora(fastic, False)
            print("Interrupted by user, stopping data reception.")
    

        

