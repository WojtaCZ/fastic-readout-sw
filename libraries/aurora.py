import os

import bitstring
from bitstring import BitArray
from enum import Enum
import struct
from time import perf_counter
import datetime
import pickle


class BlockType(Enum):
    CONTROL = b'\x80'
    DATA = b'\x40'
    INVALID = b'\x00'

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


def __getBlockType(input_data, block_index):
    typeBits = input_data[(block_index * 66) - 2 : (block_index * 66)].tobytes()

    if typeBits == BlockType.CONTROL.value:
        return BlockType.CONTROL
    elif typeBits == BlockType.DATA.value:
        return BlockType.DATA
    else:
        return BlockType.INVALID

def __isValidType(block_type):
    if block_type == BlockType.CONTROL or block_type == BlockType.DATA:
        return True
    else:
        return False

def __getBlockData(input_data, block_index):
    return input_data[(block_index * 66) : (block_index * 66) + 64]

def __getDescrambledBlockBTF(input_data, block_index):
    descrambled = bitstring.BitArray(length=8)

    for bitIndex in range(0, 8):
        descrambled[bitIndex] = input_data[(block_index * 66) + bitIndex] ^ input_data[((block_index-1) * 66) + (64 - (39 - bitIndex))] ^ input_data[((block_index-1) * 66) + (64 - (58 - bitIndex))]

    return descrambled

def __getDescrambledBlockData(input_data, block_index):
    descrambled = bitstring.BitArray(length=64)

    for bitIndex in range(0, 64):
        descrambled[bitIndex] = input_data[(block_index * 66) + bitIndex] ^ input_data[((block_index-1) * 66) + (64 - (39 - bitIndex))] ^ input_data[((block_index-1) * 66) + (64 - (58 - bitIndex))]

    return descrambled

def __parseControlBlock(descrambled_block_data):
    btf = descrambled_block_data[0:8]
    if btf == b'\xe1':
        return separatorBlock(descrambled_block_data)
    elif btf == b'\x1e':
        return separator7Block(descrambled_block_data)
    elif btf == b'\x78':
        return idleBlock(descrambled_block_data)
    elif btf == b'\xd2' or btf == b'\x99' or btf == b'\x55' or btf == b'\xb4' or btf == b'\xcc' or btf == b'\x66' or btf == b'\x33' or btf == b'\x4b' or btf == b'\x87':
        return userKBlock(descrambled_block_data)
    
    return None

def __overrideBlockData(input_data, block_index, override_value):
    input_data[(block_index * 66) : (block_index * 66) + 64] = override_value[:64]
    return input_data

def __correctBlockDataError(input_data, block_index):
    return None
    # Get the raw original block data
    originalData = input_data.copy()
    blockData = __getBlockData(input_data, block_index)

    # Go through all bits in the block
    for bitIndex in range(0, 64):
        # Attempt to flip the bit
        blockData[bitIndex] = not blockData[bitIndex]
        # Override the block data with the new data
        input_data = __overrideBlockData(input_data, block_index, blockData)

        # Check if the data of the following block remained the same (it could have been altered due to the descrambling algorithm)
        if(__getDescrambledBlockData(originalData, block_index + 1) == __getDescrambledBlockData(input_data, block_index + 1)):
            # Check if the block can be parsed now
            block = __parseControlBlock(__getDescrambledBlockData(input_data, block_index)) 

            # If the block was corrected, return it
            if block != None:
                return block

    return None

def __correctBlockSyncError(input_data, block_index):
    # Get the raw original block data
    originalData = input_data.copy()
    blockData = __getBlockData(input_data, block_index)

    # Go through all bits in the block
    for bitIndex in range(0, 64):
        # Attempt to flip the bit
        blockData[bitIndex] = not blockData[bitIndex]
        # Override the block data with the new data
        input_data = __overrideBlockData(input_data, block_index, blockData)

        # Check if the data of the following block remained the same (it could have been altered due to the descrambling algorithm)
        if(__getDescrambledBlockData(originalData, block_index + 1) == __getDescrambledBlockData(input_data, block_index + 1)):
            # Check if the block can be parsed now
            block = __parseControlBlock(__getDescrambledBlockData(input_data, block_index)) 

            # If the block was corrected, return it
            if block != None:
                return block

    return None

def __getBitSlip(input_data, packet_count = 128):
    dataCopy = input_data.copy()
    # If we have less data, use what we have
    if len(dataCopy) < (packet_count * 66):
        packet_count = getPacketCount(input_data)
    
    # Shorten the data to work with a smaller sample, this helps with the performance
    input_data = input_data[:(packet_count + 1) * 66]

    # Create a list to store the number of valid syncs for each bitslip
    validSyncCount = [0]*64
    # Loop through all possible bitslips
    for bitslip in range(0, 64):
        # Loop through the packet count
        for packetIndex in range(0, packet_count):
            type = __getBlockType(input_data, packetIndex)
            if __isValidType(type):
                validSyncCount[bitslip] += 1

        # Shift the data by one bit
        input_data = __shiftStream(input_data, 1)

    # Return the bitslip with the most valid syncs
    return validSyncCount.index(max(validSyncCount))

def __shiftStream(input_data, bitslip):
    return input_data << bitslip

# Get the number of packets in the data
def getPacketCount(input_data):
    return len(input_data) // 66




def parseFile(file, skipControl = False, skipBTFs = []):

    if not os.path.exists(file):
        print(f"Error: {file} does not exist.")
        return

    # Read the scrambled data
    with open(file, "rb") as f:
        rawData = f.read()

    # Create a bitarray out of the raw data
    rawData = bitstring.BitArray(bytes=rawData)

    print("Loaded data size is", round(len(rawData)/8/1024/1024, 2), "MB")
    print("Approximately", len(rawData)//66, "packets")

    # Find the bitslip of the stream
    bitSlip = __getBitSlip(rawData)
    print("Determined Aurora bitslip to be", bitSlip, "bits")

    # Shift the data stream by the bitslip
    rawData = __shiftStream(rawData, bitSlip)

    t_stop = 0
    t_start = 0

    packetDatabase = []

    print("Begin parsing!")

    for blockIndex in range(1, getPacketCount(rawData)):

        # Show the progress
        if(blockIndex % (getPacketCount(rawData) // 100) == 0):
            
            t_stop = perf_counter()

            estimatedSeconds = round(((t_stop - t_start) * (getPacketCount(rawData) - blockIndex))/(getPacketCount(rawData) // 100), 2)
        
            print("Progress:", round(blockIndex / getPacketCount(rawData) * 100, 1), "%. Estimated time remaining: ", datetime.timedelta(seconds=estimatedSeconds))

            t_start = perf_counter()
        
        # Get the block type
        blockType = __getBlockType(rawData, blockIndex)

        # If we don't want to parse control blocks and this is a control block, skip it
        if blockType == BlockType.CONTROL and skipControl:
            continue

        if blockType == BlockType.CONTROL:
            # Get the BTF of the block
            btf = __getDescrambledBlockBTF(rawData, blockIndex)
            
            # If the BTF is in the skip list, skip the block
            if btf in skipBTFs:
                continue
            
            # Descramble the block data
            descrambledBlockData = __getDescrambledBlockData(rawData, blockIndex)
            
            # Cast into a class based on the BTF
            block = __parseControlBlock(descrambledBlockData)

            # Couldn't parse the block, try to fix it
            if block == None:
                block = __correctBlockDataError(rawData, blockIndex)

                # If the block is still invalid, skip it
                if block == None:
                    print("Failed to fix invalid block at packet index", blockIndex,"Data:", __getDescrambledBlockData(rawData, blockIndex), "Skipping!")
                    continue
            
            # Append the block to the database
            packetDatabase.append(block)

        elif blockType == BlockType.DATA:
            # Return the data block
            packetDatabase.append(dataBlock(__getDescrambledBlockData(rawData, blockIndex)))
        
        elif blockType == BlockType.INVALID:
            # If we hit a block with invalid sync, see if there is only one or multiple
            invalidCounter = 0
            for packetOffset in range(0, 32):
                if(__getBlockType(rawData, packetOffset + blockIndex) == BlockType.INVALID):
                    invalidCounter += 1

            # If it was one random block, see if we can get a viable BTF
            if invalidCounter <= 1:
                # See if we can get a valid BTF
                btf = __getDescrambledBlockBTF(rawData, blockIndex)

                # If the BTF should be skipped, dont bother
                if btf in skipBTFs:
                    continue
                
                # Only attempt to fix an Idle block, that should not do any harm
                if btf == b'\x78':
                    # Force the correct header into the data stream
                    rawData[(blockIndex * 66) - 2] = 1
                    rawData[(blockIndex * 66) - 1] = 0

                    # Descramble the block data
                    descrambledBlockData = __getDescrambledBlockData(rawData, blockIndex)
                    
                    # Cast into a class based on the BTF
                    block = __parseControlBlock(descrambledBlockData)

                    if(block != None):
                        packetDatabase.append(block)
                        continue
                    else:
                        print("Failed to fix invalid block at packet index", blockIndex,"Data:", __getDescrambledBlockData(rawData, blockIndex), "Skipping!")
                        continue
            # If there is more than one invalid block, we have a sync error
            else:
                # Determine the new bitslip beginning with the invalid block
                newBitSlip = __getBitSlip(rawData[blockIndex*66:])
                # Shift the stream to fix it
                rawData = __shiftStream(rawData, newBitSlip)

                print("Found a cluster of invalid blocks at index", blockIndex, "Attempting to resync with new bistlip", newBitSlip)
      
                # Get the BTF of the block
                btf = __getDescrambledBlockBTF(rawData, blockIndex)
                
                # If the BTF is in the skip list, skip the block
                if btf in skipBTFs:
                    continue
                
                # Descramble the block data
                descrambledBlockData = __getDescrambledBlockData(rawData, blockIndex)
                
                # Cast into a class based on the BTF
                block = __parseControlBlock(descrambledBlockData)

                # Couldn't parse the block, try to fix it
                if block == None:
                    print("Failed to fix invalid block at packet index", blockIndex,"Data:", __getDescrambledBlockData(rawData, blockIndex), "Skipping!")
                    continue

                # Append the block to the database
                packetDatabase.append(block)

    return packetDatabase


data = parseFile("calpulse.bin", False, [b'\x78'])

with open('calpulse', 'wb') as f:
    pickle.dump(data, f)
    
for d in data:
    print(d)



