import usb1
from time import perf_counter
from libraries import readoutlibusb
from libraries import bitstream
from libraries import fastic
from libraries.packettypes import dataPacket, coarseCounterPacket, statisticsPacket
import time
import csv
import datetime



# Number of the fastic to be used
fasticNumber = 1

# Filename to be saved
FILENAME = "libusb"


# Connect to the readout system
try:
    readoutlibusb.init()
except Exception as e:
    print(f"Error initializing readout: {e}")
    exit(1)

# Reset the FastIC+ chip so that the registers are in a known state
readoutlibusb.setFasticICReset(fasticNumber, True)
time.sleep(0.1)
readoutlibusb.setFasticICReset(fasticNumber, False)
time.sleep(0.5)

# Get the FastIC+ revision numbers
fastic1_rev = readoutlibusb.getFasticRegister(1, 0x7f)
fastic2_rev = readoutlibusb.getFasticRegister(2, 0x7f)
print(f"FastIC+ revisions:")
print(f"   FastIC+ 1: {(fastic1_rev & 0xf0) >> 4}.{fastic1_rev & 0x0f}")
print(f"   FastIC+ 2: {(fastic2_rev & 0xf0) >> 4}.{fastic2_rev & 0x0f}")
print()

# Enable single ended positive polarity mode
readoutlibusb.setFasticRegister(fasticNumber, 0x00, 0x11)
# Enable only channel 0 in single ended mode
readoutlibusb.setFasticRegister(fasticNumber, 0x01, 0x01)
# Enable injection pulse routing to channel 0
readoutlibusb.setFasticRegister(fasticNumber, 0x02, 0x01)

# Enable the injection pulse
readoutlibusb.setFasticCalPulse(fasticNumber, True)

# Receive 1000kB of data
#readoutlibusb.auroraReceive(fasticNumber, 1000*1000, FILENAME)
readoutlibusb.read_usb_bulk_to_file(1000*1000, FILENAME+ ".bin")

# Disable the injection pulse
readoutlibusb.setFasticCalPulse(fasticNumber, False)

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
        
