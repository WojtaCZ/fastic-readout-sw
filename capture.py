from libraries import readout
from libraries import bitstream
import pickle 

import time
import math
from multiprocessing import Process

fastic = 2

def calibrateTimeTreshold():
    
    histogram = [0] * int(math.pow(2, 6+6))
    for msbTreshold in range(0, int(math.pow(2, 6))):
        msb = 0x80 | msbTreshold & 0x3F
        for lsbTreshold in range(0, int(math.pow(2, 6))):
            lsb = lsbTreshold & 0x3F
            print(hex(msb & 0x7F), hex(lsb & 0x7F))
            readout.setFasticRegister(1, 0x27, msbTreshold)
            readout.setFasticRegister(1, 0x2A, lsbTreshold)
            for i in range(0, 20):
                histogram[(msbTreshold << 6) + lsbTreshold] = histogram[(msbTreshold << 6) + lsbTreshold] + readout.getFasticTime(1)
                
    import matplotlib.pyplot as plt

    # Plot the histogram
    plt.bar(range(len(histogram)), histogram, color='blue')
    plt.title("Histogram of Time Thresholds")
    plt.xlabel("Threshold")
    plt.ylabel("Count")
    plt.show()
    

def calibrateTreshold():
    
    histogram = [0] * int(math.pow(2, 6))
    for treshold in range(0, int(math.pow(2, 6))):
        readout.setFasticRegister(1, 0x33, treshold)
        time.sleep(0.01)
        for i in range(0, 20):
            histogram[treshold] = histogram[treshold] + readout.getFasticTime(1)
            time.sleep(0.0001)
                
    import matplotlib.pyplot as plt

    # Plot the histogram
    plt.bar(range(len(histogram)), histogram, color='blue')
    plt.title("Histogram of Time Thresholds")
    plt.xlabel("Threshold")
    plt.ylabel("Count")
    plt.show()
    
try:
    readout.init()
except Exception as e:
    print(f"Error initializing readout: {e}")
    exit(1)



# Get the FastIC+ revision numbers
fastic1_rev = readout.getFasticRegister(1, 0x7f)
fastic2_rev = readout.getFasticRegister(2, 0x7f)
print(f"FastIC+ revisions:")
print(f"   FastIC+ 1: {(fastic1_rev & 0xf0) >> 4}.{fastic1_rev & 0x0f}")
print(f"   FastIC+ 2: {(fastic2_rev & 0xf0) >> 4}.{fastic2_rev & 0x0f}")
print()


# Enable single ended positive polarity mode
readout.setFasticRegister(fastic, 0x00, 0x11)
# Enable only channel 0 in single ended mode
readout.setFasticRegister(fastic, 0x01, 0x01)
# Enable injection pulse routing to channel 0
readout.setFasticRegister(fastic, 0x02, 0x01)

print("Seting comparator tresholds")

#calibrateTimeTreshold()
readout.setFasticRegister(fastic, 0x26, 0xFF)
readout.setFasticRegister(fastic, 0x27, 0xFF)
print("Enabling injection")

# Enable the injection pulse
readout.setFasticCalPulse(fastic, True)



readout.bulkReceive(fastic, 100, "testcapture.bin")


readout.setFasticCalPulse(fastic, False)





