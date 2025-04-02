import os

import bitstring
from bitstring import BitArray
from enum import Enum
import struct
from time import perf_counter



class BlockType(Enum):
    CONTROL = b'\x80'
    DATA = b'\x40'
    INVALID = b'\x00'

class BlockBtfType(Enum):
    separator = b'\xe1',
    separator7 = b'\x1e',
    idle = b'\x78',


class separatorBlock:
    def __init__(self, descrambledData):
        self.validOctets = int(descrambledData[8:16])
        self.data = descrambledData[(64 - self.validOctets*8):64]

    def __str__(self):
        return f"[SEPARATOR] Valid octets: {self.validOctets} Data: {self.data}"
    
class separator7Block:
    def __init__(self, descrambledData):
        self.data = descrambledData[8:64]

    def __str__(self):
        return f"[SEPARATOR7] Data: {self.data}"
    
class idleBlock:
    def __init__(self, descrambledData):
        self.clockCompensation = bool(descrambledData[8])
        self.channelBonding = bool(descrambledData[9])
        self.notReady = bool(descrambledData[10])
        self.strictAlignment = bool(descrambledData[11])

    def __str__(self):
        if(self.clockCompensation):
            return f"[IDLE] Clock compensation"
        elif(self.channelBonding):
            return f"[IDLE] Channel bonding"
        elif(self.notReady):
            return f"[IDLE] Not ready"
        elif(self.strictAlignment):
            return f"[IDLE] Strict alignment"
        else:
            return f"[IDLE] Clock compensation: {self.clockCompensation} Channel bonding: {self.channelBonding} Not ready: {self.notReady} Strict alignment: {self.strictAlignment}"

class userKBlock:
    def __init__(self, descrambledData):
        self.btf = descrambledData[0:8].tobytes()
        self.data = descrambledData[8:64]

    def __str__(self):
        return f"[USERK] BTF: {self.btf} Data: {self.data}"
    
class dataBlock:
    def __init__(self, descrambledData):
        self.data = descrambledData

    def __str__(self):
        return f"[DATA] Data: {self.data}"

def parseBlock(blockData, index, skipIdles = True):

    blockType = getBlockType(blockData, index)

    if(skipIdles and blockType == BlockType.CONTROL and descrambleBTF(blockData, index) == b'\x78'):
        return None

    descrambledData = descrambleBlock(blockData, index)

    if blockType == BlockType.CONTROL:
        btf = descrambledData[0:8]
        if btf == b'\xe1':
            return separatorBlock(descrambledData)
        elif btf == b'\x1e':
            return separator7Block(descrambledData)
        elif btf == b'\x78':
            return idleBlock(descrambledData)
        elif btf == b'\xd2' or btf == b'\x99' or btf == b'\x55' or btf == b'\xb4' or btf == b'\xcc' or btf == b'\x66' or btf == b'\x33' or btf == b'\x4b' or btf == b'\x87':
            return userKBlock(descrambledData)
            return None
    else:
        return dataBlock(descrambledData)

def getBitSlip(input_data):
    # Maximum number of packets used to check the bitslip
    samplePacketCount = 150

    # If we have less data, use what we have
    if len(input_data) < (samplePacketCount * 66):
        samplePacketCount = getPacketCount(input_data)
    
    # Shorten the data to work with a smaller sample
    input_data = input_data[:(samplePacketCount + 1) * 66]

    validSyncCount = [0]*66
    for bitslip in range(0, 66):
        for packetIndex in range(0, samplePacketCount):
            type = getBlockType(input_data, packetIndex)
            if isValidType(type):
                validSyncCount[bitslip] += 1

        input_data = syncStream(input_data, 1)

    return validSyncCount.index(max(validSyncCount))

def getPacketCount(input_data):
    return len(input_data) // 66

def syncStream(input_data, bitslip):
    return input_data << bitslip

def descrambleBTF(input_data, index):
    descrambled = bitstring.BitArray(length=8)

    for bitIndex in range(0, 8):
        descrambled[bitIndex] = input_data[(index * 66) + bitIndex] ^ input_data[((index-1) * 66) + (64 - (39 - bitIndex))] ^ input_data[((index-1) * 66) + (64 - (58 - bitIndex))]

    return descrambled

def descrambleBlock(input_data, index):
    descrambled = bitstring.BitArray(length=64)

    for bitIndex in range(0, 64):
        descrambled[bitIndex] = input_data[(index * 66) + bitIndex] ^ input_data[((index-1) * 66) + (64 - (39 - bitIndex))] ^ input_data[((index-1) * 66) + (64 - (58 - bitIndex))]

    return descrambled

def getBlockData(input_data, index):
    return input_data[(index * 66) : (index * 66) + 64]

def overrideBlockData(input_data, index, override_value):
    input_data[(index * 66) : (index * 66) + 64] = override_value[:64]
    return input_data

def getBlockType(input_data, index):
    typeBits = input_data[(index * 66) - 2 : (index * 66)].tobytes()

    if typeBits == BlockType.CONTROL.value:
        return BlockType.CONTROL
    elif typeBits == BlockType.DATA.value:
        return BlockType.DATA
    else:
        return BlockType.INVALID
    
def getBlockBtf(input_data, index):
    typeBits = input_data[(index * 66) - 2 : (index * 66)].tobytes()

    if typeBits == BlockType.CONTROL.value:
        return BlockType.CONTROL
    elif typeBits == BlockType.DATA.value:
        return BlockType.DATA
    else:
        return BlockType.INVALID

def isValidType(type):
    if type == BlockType.CONTROL or type == BlockType.DATA:
        return True
    else:
        return False
    
def errorCorrect(input_data, index):
    origData = input_data.copy()
    origBlockData = getBlockData(input_data, index)

    for i in range(0, 64):
        cpy = origBlockData.copy()
        cpy[i] = not cpy[i]

        overrideBlockData(input_data, index, cpy)
        if(descrambleBlock(origData, index-1) == descrambleBlock(input_data, index-1) and descrambleBlock(origData, index+1) == descrambleBlock(input_data, index+1)):
            block = parseBlock(input_data, index)
            if block != None:
                return block


def main():
    input_file = "capture_after_fix.bin"

    if not os.path.exists(input_file):
        print(f"Error: {input_file} does not exist.")
        return

    # Read the scrambled data
    with open(input_file, "rb") as f:
        scrambled_data = f.read()

    data_bitarray = bitstring.BitArray(bytes=scrambled_data)

    print("Data length:", len(data_bitarray))

    bitSlip = getBitSlip(data_bitarray)
    print("Bit slip:", bitSlip)
    data_bitarray = syncStream(data_bitarray, bitSlip)

    print(descrambleBlock(data_bitarray, 589))

  
    # Print the first 100 packets

    t_stop = None
    t_start = None
    print("Parsing", getPacketCount(data_bitarray), "packets")
    for i in range(0, getPacketCount(data_bitarray)):

        

        blockType = getBlockType(data_bitarray, i)

      

        #t_stop = perf_counter()

        #print("Parsing:", t_stop - t_start)
        block = parseBlock(data_bitarray, i, False)

        if not isinstance(block, idleBlock):
           
            if(isinstance(block, userKBlock) and block.btf == b'\xd2'):
                #print("Index:", i, end=" ")
                #packetCount = block.data[54-47:54-24]
                #coarseCouner = block.data[54-24:54]
                #reset = block.data[55]
                #print("Counter extension - Packet count:", packetCount.uint, "Coarse counter:", coarseCouner.uint, "Reset:", bool(reset))
            if block == None:
                print("Index:", i, end=" ")
                print("Error correcting")
                block = errorCorrect(data_bitarray, i)
                if block != None:
                    print("Error correction succeeded")
                    print(block)
                else:
                    print("Error correction failed")
                    print(getBlockData(data_bitarray, i), descrambleBlock(data_bitarray, i))
            #else:
                #print(block)



    #data = getBlockData(data_bitarray, 11915)

    #for i in range(0, 64):
        #cpy = data.copy()
        #cpy[i] = not cpy[i]
        #overrideBlockData(data_bitarray, 11915, cpy)
        #print(descrambleBlock(data_bitarray, 11915-1), descrambleBlock(data_bitarray, 11915),  descrambleBlock(data_bitarray, 11915+1))
        #overrideBlockData(data_bitarray, 11915, data)


    


    #overrideBlockData(data_bitarray, 1, b'\xAB\xAB\xAB\xAB\xAB\xAB\xAB\xAB')



if __name__ == "__main__":
    main()

# 63412 78563412 785    6341    2785    6341    2785
#00000001007820000000000
