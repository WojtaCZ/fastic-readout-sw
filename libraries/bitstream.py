import os

import bitstring
from bitstring import BitArray
from enum import Enum
import struct
from time import perf_counter
import datetime
import pickle
from blocktypes import separatorBlock, separator7Block, idleBlock, userKBlock, dataBlock

class BlockType(Enum):
    CONTROL = b'\x80'
    DATA = b'\x40'
    INVALID = b'\x00'

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

    blockFirstBit = ((block_index-1) * 66)
    blockData = input_data[blockFirstBit : blockFirstBit + 64] + input_data[blockFirstBit + 66: blockFirstBit + 64 + 66]

    
    for bitIndex in range(64, 64+8):
        descrambled[bitIndex - 64] = blockData[bitIndex] ^ blockData[bitIndex - 39] ^ blockData[bitIndex - 58 ] 

    return descrambled

def __getDescrambledBlockData(input_data, block_index):
    descrambled = bitstring.BitArray(length=64)


    blockFirstBit = ((block_index-1) * 66)
    blockData = input_data[blockFirstBit : blockFirstBit + 64] + input_data[blockFirstBit + 66: blockFirstBit + 64 + 66]

    
    for bitIndex in range(64, 128):
        descrambled[bitIndex - 64] = blockData[bitIndex] ^ blockData[bitIndex - 39] ^ blockData[bitIndex - 58 ] 
        
    #print("Descrambled block data", descrambled)
    return descrambled

def __parseControlBlock(descrambled_block_data):
    btf = descrambled_block_data[0:8]
    if btf == b'\x1e':
        return separatorBlock(descrambled_block_data)
    elif btf == b'\xe1':
        return separator7Block(descrambled_block_data)
    elif btf == b'\x78':
        return idleBlock(descrambled_block_data)
    elif btf == b'\xd2' or btf == b'\x99' or btf == b'\x55' or btf == b'\xb4' or btf == b'\xcc' or btf == b'\x66' or btf == b'\x33' or btf == b'\x4b' or btf == b'\x87':
        return userKBlock(descrambled_block_data)
    
    return None

def __getBitSlip(input_data, packet_count = 512):
    dataCopy = input_data.copy()
    # If we have less data, use what we have
    if len(dataCopy) < (packet_count * 66):
        packet_count = getPacketCount(input_data)
    
    # Shorten the data to work with a smaller sample, this helps with the performance
    input_data = input_data[:(packet_count + 1) * 66]

    # Create a list to store the number of valid syncs for each bitslip
    validSyncCount = [0]*66
    # Loop through all possible bitslips
    for bitslip in range(0, 66):
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
                print("Incorrect block data at packet index", blockIndex)
                continue

            # Append the block to the database
            packetDatabase.append(block)

        elif blockType == BlockType.DATA:
            # Return the data block
            packetDatabase.append(dataBlock(__getDescrambledBlockData(rawData, blockIndex)))
        
        elif blockType == BlockType.INVALID:
            print("Incorrect block data at packet index", blockIndex)
            break
           

    return packetDatabase



