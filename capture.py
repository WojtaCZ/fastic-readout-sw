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
fasticChannel = 2

# Bias voltage value (NOTE: The actual voltage on the userboard migth be about 0.2V lower than this setpoint)
biasVoltage = 56

# Sample size for the capture in bytes
sampleSizeBytes = 1000*300

# Save as CSV file?
saveCSV = False

# Filename to be saved
FILENAME = "capture" 

# Add a timestamp to the filename
#FILENAME = FILENAME + "-" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S%f")

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

# Set the TIME LSB to minimum
readout.setFasticRegister(fasticNumber, 0x28, 0x04)

# Set TIME treshold to 60
treshold = 60
readout.setFasticRegister(fasticNumber, 0x26, 0x80 | treshold)

# Max aurora data frame size
readout.setFasticRegister(fasticNumber, 0xA2, 0x01, True)


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
   # exit(1)

print(f"HV Voltage: {readout.getHvVoltage()}V")
print(f"HV Current: {readout.getHvCurrent()}uA")
print()

# Receive 1000kB of data
readout.auroraReceive(fasticNumber, sampleSizeBytes, FILENAME)

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
        

if saveCSV:      
    # Save the packets to an CSV file
    with open(FILENAME + ".csv", mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        
        # Write the header row
        csv_writer.writerow(["CoarseCounter", "Timestamp", "Channel", "Type", "PulseWidth", "Debug"])
        
        # Write packet data
        for packet in fasticPackets:
            if isinstance(packet, dataPacket):
                csv_writer.writerow([packet.last_coarse_counter, packet.timestamp, packet.channel, packet.pkt_type, packet.pulse_width, packet.debug])
        

            