from libraries import readout
from libraries import bitstream
from libraries import fastic
from libraries.packettypes import dataPacket, coarseCounterPacket, statisticsPacket
import time
import csv
import datetime

# Filename to be saved
FILENAME = "fifo_overflow" 

# Get the Aurora packets from the stream - skip idle packets (0x78), this speeds up the processing a lot. Othe BTFs can be specified too
# This takes the .bin file as an input and outputs a .aurora file with parsed aurora packets
bitstream.parseBitstream(FILENAME, FILENAME, False)

# Parse the Aurora packets into FastIC packets
fasticPackets = fastic.parseAurora(FILENAME)

# Print the data packets into the console
for idx, packet in enumerate(fasticPackets):
    if isinstance(packet, dataPacket):
        # Print only packets with wrong parity
        if not packet.parity_ok:
            print(idx, packet)
            pass
        
    if isinstance(packet, coarseCounterPacket):
        # Do nothing
        #  print(packet)
        pass
    if isinstance(packet, statisticsPacket):   
        #print(packet)
        pass



        

            