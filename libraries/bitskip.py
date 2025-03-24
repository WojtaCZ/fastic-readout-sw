import os

import bitstring
from bitstring import BitArray
from enum import Enum
import struct
from time import perf_counter
import datetime

file = "bitskip_testdata_1024_fixedBuff.bin"

if not os.path.exists(file):
    print(f"Error: {file} does not exist.")
    exit()

# Read the scrambled data
with open(file, "rb") as f:
    rawData = f.read()



# Create a bitarray out of the raw data
#rawData = bitstring.BitArray(bytes=rawData)

print("Loaded data size is", round(len(rawData)/8/1024/1024, 2), "MB")


for i in range(0, len(rawData)-4):
    if(rawData[i*4] != rawData[0] or rawData[i*4+1] != rawData[1] or rawData[i*4+2] != rawData[2] or rawData[i*4+3] != rawData[3]):
        print("Error at", (i + 1)%1024, ":", rawData[i*4], rawData[i*4+1], rawData[i*4+2], rawData[i*4+3],"   ", rawData[0], rawData[1], rawData[2], rawData[3])


