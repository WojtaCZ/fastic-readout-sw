from libraries import readout
from libraries import bitstream
from libraries import fastic
from libraries.packettypes import dataPacket, coarseCounterPacket, statisticsPacket
import time
import csv
import matplotlib.pyplot as plt
import datetime

# Number of the fastic to be used
fasticNumber = 2

# Number of the fastic channel to be used
fasticChannel = 2

# Bias voltage value (NOTE: The actual voltage on the userboard migth be about 0.2V lower than this setpoint)
biasVoltage = 56

# Sample size for the capture in bytes
sampleSizeBytes = 1000*1000*5

# Filename to be saved
FILENAME = "consecutive_delay"

# Add a timestamp to the filename
#FILENAMETS = FILENAME + "-" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S%f")
FILENAMETS = FILENAME


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
# Enable the selectec channel
readout.setFasticRegister(fasticNumber, 0x01, 0x01 << fasticChannel)
# Only enable readout for the selected channel
readout.setFasticRegister(fasticNumber, 0x80, 0x01 << fasticChannel)
# Disable trigger channel
readout.setFasticRegister(fasticNumber, 0x82, 0x88)

# Set the TIME LSB to minimum
readout.setFasticRegister(fasticNumber, 0x28, 0x04)

# Max aurora data frame size - this is needed for correct synchronization
readout.setFasticRegister(fasticNumber, 0xA2, 0x01, True)

treshold = 16
readout.setFasticRegister(fasticNumber, 0x26, treshold | 0x80)
        



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

# Receive data
readout.auroraReceive(fasticNumber, sampleSizeBytes, FILENAMETS)

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
delays = []
prevTimestamp = 0


errorPackets = 0
okPackets = 0

# Print the data packets into the console
for index, packet in enumerate(fasticPackets):
    if isinstance(packet, dataPacket):
        if not packet.parity_ok:
            # Print only packets with wrong parity
            errorPackets += 1
            pass
        
        # If a non-trigger packet was found
        if packet.channel == fasticChannel and packet.parity_ok:
            okPackets += 1
            # Create the timestamp of the packet
            timestamp = packet.timestamp * ultraFastResolutionPs + packet.last_coarse_counter * coarseResolutionPs

            timeDiff = timestamp - prevTimestamp
            
            prevTimestamp = timestamp
            
            # Add the time difference to the list
            delays.append(timeDiff)

print(f"Number of error packets: {errorPackets}, number of ok packets: {okPackets}")
print("If the error counter is too high, consider increasing the treshold. The stream is probably saturated.")

# Plot the histogram of time differences with x-axis limits
plt.hist(delays, bins=400, color='blue', alpha=0.7)
plt.title("Histogram of Time Differences")
plt.xlabel("Time Difference (ps)")
plt.ylabel("Frequency")
plt.xlim(-0.5e6, 0.5e6)  # Limit x-axis to -1000ps and 1000ps
plt.grid(True)
plt.show()
