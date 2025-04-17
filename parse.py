
from libraries import bitstream
import pickle

data = bitstream.parseFile("testcapture.bin", False, [b'\x78'])

with open('testcapture', 'wb') as f:
    pickle.dump(data, f)
    
