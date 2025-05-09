import usb1
from time import perf_counter
from libraries import readout
from libraries import bitstream
from libraries import fastic
from libraries.packettypes import dataPacket, coarseCounterPacket, statisticsPacket
import time
import csv
import datetime



def read_usb_bulk_to_file(total_bytes: int, out_file: str):
    VID = 0xcafe
    PID = 0x4000
    ENDPOINT = 0x83
    INTERFACE = 0

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

    with usb1.USBContext() as context:
        handle = context.openByVendorIDAndProductID(VID, PID, skip_on_error=True)
        if handle is None:
            handle.claimInterface(INTERFACE)
        #handle.claimInterface(INTERFACE)

        # Start time for performance logging
        start_time = perf_counter()

        readout.setFasticAurora(1, True)
            
        # Submit transfers
        for _ in range(NUM_TRANSFERS):
            transfer = handle.getTransfer()
            buffer = bytearray(TRANSFER_SIZE)
            transfer.setBulk(
                ENDPOINT,
                buffer,
                callback=on_transfer,
                timeout=0
            )
            transfer.submit()

        # Poll until all data is received
        while not completed:
            context.handleEventsTimeout(tv=TIMEOUT_US / 1e6)
        
        readout.setFasticAurora(1, False)
        
        elapsed = perf_counter() - start_time
        mbps = (received * 8) / 1e6 / elapsed
        print(f"Received {received} bytes in {elapsed:.2f}s ({mbps:.2f} Mbps)")

        # Write to file
        with open(out_file, 'wb') as f:
            for chunk in buffers:
                f.write(chunk)




# Number of the fastic to be used
fasticNumber = 1

# Filename to be saved
FILENAME = "libusb"


# Connect to the readout system
try:
    readout.init()
except Exception as e:
    print(f"Error initializing readout: {e}")
    exit(1)

# Reset the FastIC+ chip so that the registers are in a known state
readout.setFasticICReset(fasticNumber, True)
time.sleep(0.1)
readout.setFasticICReset(fasticNumber, False)
time.sleep(0.5)

# Get the FastIC+ revision numbers
fastic1_rev = readout.getFasticRegister(1, 0x7f)
fastic2_rev = readout.getFasticRegister(2, 0x7f)
print(f"FastIC+ revisions:")
print(f"   FastIC+ 1: {(fastic1_rev & 0xf0) >> 4}.{fastic1_rev & 0x0f}")
print(f"   FastIC+ 2: {(fastic2_rev & 0xf0) >> 4}.{fastic2_rev & 0x0f}")
print()

# Enable single ended positive polarity mode
readout.setFasticRegister(fasticNumber, 0x00, 0x11)
# Enable only channel 0 in single ended mode
readout.setFasticRegister(fasticNumber, 0x01, 0x01)
# Enable injection pulse routing to channel 0
readout.setFasticRegister(fasticNumber, 0x02, 0x01)

# Enable the injection pulse
readout.setFasticCalPulse(fasticNumber, True)

# Receive 1000kB of data
#readout.auroraReceive(fasticNumber, 1000*1000, FILENAME)
read_usb_bulk_to_file(1000*1000*10, FILENAME+ ".bin")

# Disable the injection pulse
readout.setFasticCalPulse(fasticNumber, False)

# Get the Aurora packets from the stream
bitstream.parseBitstream(FILENAME, FILENAME, False, [b'\x78'])

# Parse the Aurora packets into FastIC packets
fasticPackets = fastic.parseAurora(FILENAME)

# Print the data packets into the console
for packet in fasticPackets:
    if isinstance(packet, dataPacket):
        print(packet)
        print()
    if isinstance(packet, coarseCounterPacket):
        # Do nothing
        pass
    if isinstance(packet, statisticsPacket):
        # Do nothing
        pass
        
