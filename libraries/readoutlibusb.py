from enum import IntEnum
import usb1
import struct
import bitstring
from bitstring import BitArray
import time
from time import perf_counter


class Message(IntEnum):
    READOUT_STATUS = 0
    READOUT_UID = 1
    READOUT_FIRMWARE = 2
    HV_ENABLE = 3
    HV_CURRENT = 4
    HV_VOLTAGE = 5
    HV_PID = 6
    FASTIC_REGISTER = 7
    FASTIC_VOLTAGE = 8
    FASTIC_SYNCRESET = 9
    FASTIC_ICRESET = 10
    FASTIC_CALPULSE = 11
    FASTIC_TIME = 12
    FASTIC_AURORA = 13
    USERBOARD_STATUS = 14
    USERBOARD_INIT = 15
    USERBOARD_UID = 16
    USERBOARD_NAME = 17
    USERBOARD_WRITEPROTECT = 18
    USERBOARD_VOLTAGE = 19
    USERBOARD_REGISTER = 20
    USERBOARD_TOMEMORY = 21
    USERBOARD_FROMMEMORY = 22
    UNKNOWN = 23

context = None
dev = None

def init():
    global context, dev
    context = usb1.USBContext()
    dev = context.openByVendorIDAndProductID(0xcafe, 0x4000)

    if dev is None:
        raise ValueError("Readout was not found!")

    fw = getReadoutFirmware()
    build_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(fw['timestamp']))

    print(f"FastIC+ readout connected!")
    print(f"   UID: {getReadoutUID()}")
    print(f"   Firmware: {fw['revision'].decode('utf-8')}")
    print(f"   Build date: {build_date}")
    print()

def ctrl_transfer(request_type, request, value, index, length_or_data):
    global dev
    if isinstance(length_or_data, int):
        return dev.controlRead(request_type, request, value, index, length_or_data)
    else:
        dev.controlWrite(request_type, request, value, index, length_or_data)



def getStatus():
    global dev
    data = struct.unpack('ffH', ctrl_transfer(0xC0, Message.READOUT_STATUS, 0, 0, 10))
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
    data = struct.unpack('iii', ctrl_transfer(0xC0, Message.READOUT_UID, 0, 0, 12))
    uid = (data[0] << 64) | (data[1] << 32) | data[2]
    return hex(uid)

def getReadoutFirmware():
    global dev
    data = struct.unpack('7p33pI', ctrl_transfer(0xC0, Message.READOUT_FIRMWARE, 0, 0, 7+33+4))
    
    ret = {
        'revision': data[0],
        'branch': data[1],
        'timestamp': data[2]
    }
        
    return ret

def getHvEnabled():
    global dev
    data = struct.unpack('?', ctrl_transfer(0xC0, Message.HV_ENABLE, 0, 0, 4))
    return data[0]

def setHvEnabled(state):
    global dev
    ctrl_transfer(0x40, Message.HV_ENABLE, 0, 0, bytes((state,)))

def getHvCurrent():
    global dev
    data = struct.unpack('f', ctrl_transfer(0xC0, Message.HV_CURRENT, 0, 0, 4))
    return data[0]

def getHvVoltage():
    global dev
    data = struct.unpack('f', ctrl_transfer(0xC0, Message.HV_VOLTAGE, 0, 0, 4))
    return data[0]

def setHvVoltage(value):
    global dev
    ctrl_transfer(0x40, Message.HV_VOLTAGE, 0, 0, bytearray(struct.pack("f", value)))


def getFasticRegister(fastic, register):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    data = struct.unpack('B', ctrl_transfer(0xC0, Message.FASTIC_REGISTER, register, fastic, 1))
    return data[0]

def setFasticRegister(fastic, register, value, force = False):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    ctrl_transfer(0x40, Message.FASTIC_REGISTER, register | ((force & 0x01) << 15), fastic, bytearray(struct.pack("B", value)))

def getFasticVoltage(fastic):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    data = struct.unpack('f', ctrl_transfer(0xC0, Message.FASTIC_VOLTAGE, 0, fastic, 4))
    return data[0]

def getFasticSyncReset(fastic):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    data = struct.unpack('?', ctrl_transfer(0xC0, Message.FASTIC_SYNCRESET, 0, fastic, 1))
    return data[0]

def setFasticSyncReset(fastic, state):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    ctrl_transfer(0x40, Message.FASTIC_SYNCRESET, state, fastic, [0])
    
def getFasticICReset(fastic):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    data = struct.unpack('?', ctrl_transfer(0xC0, Message.FASTIC_ICRESET, 0, fastic, 1))
    return not data[0]

def setFasticICReset(fastic, state):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    ctrl_transfer(0x40, Message.FASTIC_ICRESET, not state, fastic, [0])
    
def getFasticCalPulse(fastic):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    data = struct.unpack('?', ctrl_transfer(0xC0, Message.FASTIC_CALPULSE, 0, fastic, 1))
    return data[0]

def setFasticCalPulse(fastic, state):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    ctrl_transfer(0x40, Message.FASTIC_CALPULSE, state, fastic, [0])
    
def getFasticTime(fastic):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    data = struct.unpack('?', ctrl_transfer(0xC0, Message.FASTIC_TIME, 0, fastic, 1))
    return data[0]

def getFasticAurora(fastic):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    data = struct.unpack('?', ctrl_transfer(0xC0, Message.FASTIC_AURORA, 0, fastic, 1))
    return data[0]

def setFasticAurora(fastic, state):
    global dev
    if fastic < 1 or fastic > 2:
        raise ValueError("FastIC+ index must be either 1 and 2")
    
    ctrl_transfer(0x40, Message.FASTIC_AURORA, state & 0x0001, fastic, [0])
    
#def getUserboardStatus():
    
def getUserboardRegister(register):
    global dev
    data = struct.unpack('B', ctrl_transfer(0xC0, Message.USERBOARD_REGISTER, register, 0, 1))
    return data[0]

def getUserboardUID():
    global dev
    data = struct.unpack('BBBBBBBBBBBBBBBBB', ctrl_transfer(0xC0, Message.USERBOARD_UID, 0, 0, 17))
    shortID = data[0]
    uid = data[1] << 56 | data[2] << 48 | data[3] << 40 | data[4] << 32 | data[5] << 24 | data[6] << 16 | data[7] << 8 | data[8]
    return shortID, uid

def getUserboardName():
    global dev
    data = ctrl_transfer(0xC0, Message.USERBOARD_NAME, 0, 0, 64).decode("utf-8")
    return data

def auroraReceive(fastic, size, filename):
    if fastic not in (1, 2):
        raise ValueError("FastIC+ index must be either 1 or 2")

    ENDPOINT = 0x83 if fastic == 1 else 0x84
    filename += ".bin"

    with open(filename, "wb") as buffer_file:
        print(f"Receiving data and writing to {filename}")
        lenTotal = 0
        try:
            while lenTotal < size:
                data = dev.bulkRead(ENDPOINT, min(4096, size - lenTotal), timeout=1000)
                buffer_file.write(data)
                lenTotal += len(data)

            print(f"Received {lenTotal / 1024:.2f} kB of data")
        except usb1.USBErrorTimeout:
            print("Timeout reached, stopping data reception.")
        except KeyboardInterrupt:
            print("Interrupted by user, stopping data reception.")
        except Exception as e:
            print(f"Error: {e}")
            
            
def read_usb_bulk_to_file(total_bytes: int, out_file: str):
    global dev, context
    VID = 0xcafe
    PID = 0x4000
    ENDPOINT = 0x83
    INTERFACE = 2

    TRANSFER_SIZE = 16 * 1024
    NUM_TRANSFERS = 64
    TIMEOUT_US = 1000

    received = 0
    buffers = []
    completed = False

    def on_transfer(transfer):
        nonlocal received, completed

        status = transfer.getStatus()
        if status == usb1.TRANSFER_COMPLETED:
            data = transfer.getBuffer()[:transfer.getActualLength()]
            if received + len(data) <= total_bytes:
                buffers.append(bytes(data))
                received += len(data)
                if received >= total_bytes:
                    completed = True
                else:
                    transfer.submit()
            else:
                # Only take the remaining bytes needed
                remaining = total_bytes - received
                buffers.append(bytes(data[:remaining]))
                received += remaining
                completed = True
        elif status in (usb1.TRANSFER_CANCELLED, usb1.TRANSFER_ERROR, usb1.TRANSFER_NO_DEVICE):
            if not completed:
                print(f"Transfer failed with status {status}. Check device connection and endpoint configuration.")
        else:
            transfer.submit()  # Retry on temporary errors

    # Claim the interface
    dev.claimInterface(INTERFACE)

    # Start time for performance logging
    start_time = perf_counter()

    # Submit transfers
    for _ in range(NUM_TRANSFERS):
        transfer = dev.getTransfer()
        buffer = bytearray(TRANSFER_SIZE)
        transfer.setBulk(
            ENDPOINT,
            buffer,
            callback=on_transfer,
            timeout=0
        )
        transfer.submit()
        
    setFasticAurora(1, True)

    # Poll until all data is received
    while not completed:
        context.handleEventsTimeout(tv=TIMEOUT_US / 1e6)
    
    setFasticAurora(1, False)
    
    elapsed = perf_counter() - start_time
    mbps = (received * 8) / 1e6 / elapsed
    print(f"Received {received} bytes in {elapsed:.2f}s ({mbps:.2f} Mbps)")

    # Write to file
    with open(out_file, 'wb') as f:
        for chunk in buffers:
            f.write(chunk)
