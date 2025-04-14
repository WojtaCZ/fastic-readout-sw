from libraries import readout
from libraries import bitstream
import pickle 

import time
from multiprocessing import Process

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

# Enable only channel 0 in single ended mode
readout.setFasticRegister(1, 0x01, 0x01)
# Enable injection pulse routing to channel 0
readout.setFasticRegister(1, 0x01, 0x01)


print("Seting comparator tresholds")

# Set the comparator tresholds 
readout.setFasticRegister(1, 0x26, 0x81)
readout.setFasticRegister(1, 0x28, 25)

readout.setFasticRegister(1, 0x27, 0x81)
readout.setFasticRegister(1, 0x29, 25)

print("Enabling injection")

# Enable the injection pulse
readout.setFasticCalPulse(1, True)

#readout.bulkReceive(1, 1000, "testcapture.bin")
# Start the receive thread

#readout.bulkReceive(1, 10, "testcapture.bin")
receive_thread = Process(target=readout.bulkReceive, args=(1, 100, "testcapture.bin"))
receive_thread.start()
time.sleep(1)
readout.setFasticAurora(1, True)
# Enable the aurora stream
#while not receive_thread.is_alive():
    #time.sleep(0.000001)
time.sleep(1)
# time.sleep(1)
readout.setFasticAurora(1, False)

receive_thread.join()



