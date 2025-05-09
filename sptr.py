from libraries import readout
from libraries import bitstream
from libraries import fastic
from libraries.packettypes import dataPacket, coarseCounterPacket, statisticsPacket
import time
import csv
import matplotlib.pyplot as plt
import datetime

# Number of the fastic to be used
fasticNumber = 1

# Bias voltage value (NOTE: The actual voltage on the userboard migth be about 0.2V lower than this setpoint)
biasVoltage = 45

# Filename to be saved
FILENAME = "sptr"

# Add a timestamp to the filename
FILENAMETS = FILENAME + "-" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S%f")

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

###
### CONFIGURE THE FASTIC FOR THE SPTR
###

# Enable single ended positive polarity mode
readout.setFasticRegister(fasticNumber, 0x00, 0x11)

# Enable only channel 0 in single ended mode
readout.setFasticRegister(fasticNumber, 0x01, 0x01)

# Set trigger to external
readout.setFasticRegister(fasticNumber, 0x67, 0x30)
readout.setFasticRegister(fasticNumber, 0x82, 0x29)

# Enable energy pedestal suppression
readout.setFasticRegister(fasticNumber, 0x60, 0xC7)

# Enable injection pulse routing to channel 0
readout.setFasticRegister(fasticNumber, 0x02, 0x01)

###
### END CONFIGURATION - THE FOLLOWING LINES SHOULD NOT NEED TO BE CHANGED
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
readout.auroraReceive(fasticNumber, 1000*1000, FILENAMETS)

time.sleep(1)

# Disable HV voltage
readout.setHvEnabled(False)


# Get the Aurora packets from the stream
bitstream.parseBitstream(FILENAMETS, FILENAME, False, [b'\x78'])

# Parse the Aurora packets into FastIC packets
fasticPackets = fastic.parseAurora(FILENAME)

coarseResolutionPs = (1/40000000) * 1e12
fastResolutionPs =   coarseResolutionPs / 64
ultraFastResolutionPs = fastResolutionPs / 1024

# List to store time differences
time_differences = []

# Print the data packets into the console
for index, packet in enumerate(fasticPackets):
    if isinstance(packet, dataPacket):
        # If a non-trigger packet was found
        if packet.channel != 8:
            print(packet)
            # Create the timestamp of the packet
            timestamp = packet.timestamp * ultraFastResolutionPs + packet.last_coarse_counter * coarseResolutionPs
            
            # Timestamps of both triggers near the packet
            triggerTimestamp1 = 0
            triggerTimestamp2 = 0
            
            # Search the nearest trigger packet from this index to the end of the list
            for searchedPacket in fasticPackets[index:]:
                # If we hit trigger
                if isinstance(searchedPacket, dataPacket):
                    if searchedPacket.channel == 8:
                        triggerTimestamp1 = searchedPacket.timestamp * ultraFastResolutionPs + searchedPacket.last_coarse_counter * coarseResolutionPs
                        break
                
            # Search the other side
            for searchedPacket in reversed(fasticPackets[:index]):
                # If we hit trigger
                if isinstance(searchedPacket, dataPacket):
                    if searchedPacket.channel == 8:
                        triggerTimestamp2 = searchedPacket.timestamp * ultraFastResolutionPs + searchedPacket.last_coarse_counter * coarseResolutionPs
                        break
            
            # Calculate the time difference and take the minimum (closest packet)
            timeDiff = min(abs(timestamp - triggerTimestamp1), abs(timestamp - triggerTimestamp2))
            
            # Add the time difference to the list
            time_differences.append(timeDiff)

# Plot the histogram of time differences
plt.hist(time_differences, bins=50, color='blue', alpha=0.7)
plt.title("Histogram of Time Differences")
plt.xlabel("Time Difference (ps)")
plt.ylabel("Frequency")
plt.grid(True)
plt.show()
            
            
