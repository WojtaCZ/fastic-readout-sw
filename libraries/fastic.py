import pickle
import bitstring
from bitstring import BitArray
from libraries.blocktypes import separatorBlock, separator7Block, idleBlock, userKBlock, dataBlock
from libraries.packettypes import dataPacket, coarseCounterPacket, statisticsPacket
import math

fasticPacketDatabase = []

lastCoarse = 0
coarseCounter = 0

def parse_channels_data(data, coarse):
    global coarseCounter
    
    for packet in range(0, len(data) // 48):
        packet = dataPacket(data[0:48], coarseCounter)
        fasticPacketDatabase.append(packet)
        data = data[48:]

   
def parse_statistics_data(data):
    packet = statisticsPacket(data)
    fasticPacketDatabase.append(packet)
    
def parse_coarse_counter(data):
    global lastCoarse
    global coarseCounter
    
    packet = coarseCounterPacket(data)
    fasticPacketDatabase.append(packet)

    coarse = data[31:55].uint
    reset = (data[55])
    
    if(not reset):
        coarseCounter = coarse
    else:
        coarseCounter = coarseCounter + coarse

    lastCoarse = (int(coarse)*25)
    
    
statArray = bitstring.BitArray()
dataArray = bitstring.BitArray()

hasPreviousData = False

def parseAurora(filename):
    global hasPreviousData
    global statArray
    global dataArray
    global dataCounter
    
    filename = filename + ".aurora"
    
    # Load the parsed pickle file
    objects = []
    with (open(filename, "rb")) as f:
        while True:
            try:
                objects.append(pickle.load(f))
            except EOFError:
                break


    # Go through the objects
    for idx,obj in enumerate(objects[0]):
        

        # PARSE THE COARSE COUNTER
        if isinstance(obj, userKBlock) and obj.btf == b'\xD2':
            parse_coarse_counter(obj.data)
        
        # PARSE THE STATISTICS 
        # First part of the statistics datay
        if isinstance(obj, userKBlock) and obj.btf == b'\x99':
            statArray.append(obj.data)
        # Second part of the statistics data
        if isinstance(obj, userKBlock) and obj.btf == b'\x55':
            statArray.append(obj.data)
            parse_statistics_data(statArray)
            statArray = bitstring.BitArray()
            
        # PARSE THE DATA BLOCKS
        # Just append to the array
        if isinstance(obj, dataBlock):
            dataArray = obj.data + dataArray
            hasPreviousData = True
        
        if isinstance(obj, separator7Block):
            dataArray = obj.data + dataArray
            hasPreviousData = True
            
        if isinstance(obj, separatorBlock):
            dataArray = obj.data + dataArray
            hasPreviousData = True
            
        # If we received data previously but now, the block is a control, parse the data
        if hasPreviousData == True and not isinstance(obj, dataBlock) and not isinstance(obj, separatorBlock) and not isinstance(obj, separator7Block):
            hasPreviousData = False
            parse_channels_data(dataArray, coarseCounter)
            dataArray = bitstring.BitArray()
            
    return fasticPacketDatabase
        
