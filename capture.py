from libraries import readout
from libraries import bitstream
from libraries import fastic
from libraries.packettypes import dataPacket, coarseCounterPacket, statisticsPacket
import time
import csv
import datetime

# Number of the fastic to be used
fasticNumber = 1

# Bias voltage value (NOTE: The actual voltage on the userboard migth be about 0.2V lower than this setpoint)
biasVoltage = 45

# Filename to be saved
FILENAME = "capture" 

# Add a timestamp to the filename
FILENAME = FILENAME + "-" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S%f")

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
readout.setFasticRegister(fasticNumber, 0x01, 0x80)


###
### ADD other configuration for the fastic registers
###

shortID, UID = readout.getUserboardUID()

if(shortID == 0x00):
    print(f"The userboard is not connected.")
    exit(1)

# Set the bias voltage
readout.setHvVoltage(biasVoltage)
readout.setHvEnabled(True)

# Let it stabilize
print(f"Waiting for the HV to stabilize...")
time.sleep(5)

print(f"HV Voltage: {readout.getHvVoltage()}V")
print(f"HV Current: {readout.getHvCurrent()}uA")
print()

# Receive 1000kB of data
readout.auroraReceive(fasticNumber, 1000*1000, FILENAME)

time.sleep(1)

# Disable HV voltage
readout.setHvEnabled(False)

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
        
            
# Save the packets to an CSV file
with open(FILENAME + ".csv", mode='w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    
    # Write the header row
    csv_writer.writerow(["CoarseCounter", "Timestamp", "Channel", "Type", "PulseWidth", "Debug"])
    
    # Write packet data
    for packet in fasticPackets:
        if isinstance(packet, dataPacket):
            csv_writer.writerow([packet.last_coarse_counter, packet.timestamp, packet.channel, packet.pkt_type, packet.pulse_width, packet.debug])
       

        