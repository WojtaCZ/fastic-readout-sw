from libraries import readout
from libraries import bitstream
from libraries import fastic
from libraries.packettypes import dataPacket, coarseCounterPacket, statisticsPacket
import time
import csv
import datetime

# Number of the fastic to be used
fasticNumber = 2

# Number of the fastic channel to be used
fasticChannel = 5

# Bias voltage value (NOTE: The actual voltage on the userboard migth be about 0.2V lower than this setpoint)
biasVoltage = 54

# Sample size for each treshold in bytes
sampleSizeBytes = 1000


# Filename to be saved
FILENAME = "treshold_scan" 

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
# Enable the selectec channel
readout.setFasticRegister(fasticNumber, 0x01, 0x01 << fasticChannel)
# Only enable readout for the selected channel
readout.setFasticRegister(fasticNumber, 0x80, 0x01 << fasticChannel)
# Disable trigger channel
readout.setFasticRegister(fasticNumber, 0x82, 0x88)
# Set the LSB to minimum
readout.setFasticRegister(fasticNumber, 0x28, 0x00)



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
time.sleep(2)

voltage = readout.getHvVoltage()

if voltage < biasVoltage - 0.5 or voltage > biasVoltage + 0.5:
    print()
    print(f"Voltage out of setpoin range: {voltage}")
    print(f"Please check the connections and the voltage setting. Maybe the power supply is limitting the output due to overcurrent.")
    print(f"Current: {readout.getHvCurrent()}uA")
    exit(1)
    
print(f"HV Voltage: {readout.getHvVoltage()}V")
print(f"HV Current: {readout.getHvCurrent()}uA")
print()
import matplotlib.pyplot as plt

packetCount = 64*[0]
errorCount = 64*[0]

plt.ion()  # Turn on interactive mode
fig, ax = plt.subplots(figsize=(10, 6))
line1, = ax.plot(range(64), packetCount, marker='o', linestyle='-', color='b', label='Valid Packets')
line2, = ax.plot(range(64), errorCount, marker='x', linestyle='--', color='r', label='Error Packets')
ax.set_title("Threshold vs Dark counts (kcps)")
ax.set_xlabel("Threshold")
ax.set_ylabel("Dark counts (kcps)")
ax.legend()
ax.grid(True)

for treshold in range(0, 64):
    
    # COMP_Time_Global_ITH
    readout.setFasticRegister(fasticNumber, 0x26, treshold | 0x80)

    # Receive the data
    readout.auroraReceive(fasticNumber, sampleSizeBytes, FILENAME)
    
    # Get the Aurora packets from the stream
    bitstream.parseBitstream(FILENAME, FILENAME, False, [b'\x78'])

    # Parse the Aurora packets into FastIC packets
    fasticPackets = fastic.parseAurora(FILENAME)

    # Print the data packets into the console
    for packet in fasticPackets:
        if isinstance(packet, dataPacket):
           
            if packet.channel == fasticChannel and packet.parity_ok:
                packetCount[treshold] += 1
                
            if not packet.parity_ok:
                errorCount[treshold] += 1
            
        if isinstance(packet, coarseCounterPacket):
            # Do nothing
            pass
        if isinstance(packet, statisticsPacket):   
            # Do nothing
            pass

    packetCount[treshold] = (packetCount[treshold] / (sampleSizeBytes / 10000000))/1000
    errorCount[treshold] = (errorCount[treshold] / (sampleSizeBytes / 10000000))/1000
    # Update the chart
    line1.set_ydata(packetCount)
    line2.set_ydata(errorCount)
    ax.relim()
    ax.autoscale_view()
    plt.pause(0.1)  # Pause to update the plot

plt.ioff()  # Turn off interactive mode
plt.show()

# Disable HV voltage
readout.setHvEnabled(False)



        

            
