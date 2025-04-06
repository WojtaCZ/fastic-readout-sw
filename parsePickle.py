import pickle
import bitstring
from bitstring import BitArray

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



objects = []
with (open("calpulse2", "rb")) as openfile:
    while True:
        try:
            objects.append(pickle.load(openfile))
        except EOFError:
            break
        
i = 0


statArray = bitstring.BitArray()
dataArray = bitstring.BitArray()

coarseCounter = 0
lastCoarse = 0

ccLast = 0

hasPreviousData = False

for idx,obj in enumerate(objects[0]):
    
    #if(idx < 6000):
        #continue
        
    if hasPreviousData == True and not isinstance(obj, dataBlock) and not isinstance(obj, separatorBlock) and not isinstance(obj, separator7Block):
        hasPreviousData = False
        print("Received data block size:", len(dataArray), "bits")
        
        for p in range(0):
            print(dataArray[0:48].bin)
            trig = dataArray[0]
            channel = dataArray[1:4].uint
            detType = dataArray[4:6]
            timestamp = dataArray[6:28].uint
            pw = dataArray[28:42].uint
            print("Packet", p, "Trigger", trig, "Channel", channel, "Type", detType, "Timestamp", timestamp, "Pulsewidth", pw, "Debug", dataArray[42], "Parity bits", dataArray[43:48], dataArray[1:4].count(1) % 2, dataArray[4:6].count(1) % 2, dataArray[6:28].count(1) % 2, dataArray[28:42].count(1) % 2, dataArray[0:47].count(1) % 2)
            print("Correct parities", )
            dataArray = dataArray[48:]

        dataArray = bitstring.BitArray()
    
    if isinstance(obj, userKBlock) and obj.btf == b'\xD2':
        reset = (not obj.data[55])
        sent = obj.data[-48:-25].uint
        coarse = obj.data[-25:-1].uint
        
        if reset == True:
            coarseCounter += coarse
            lastCoarse = 0
        elif reset == False:
            coarseCounter += coarse - lastCoarse
            lastCoarse = coarse

        
        #print(sent, (coarse * 25)/1000000, coarseCounter * 25 / 1000000, (coarseCounter - ccLast) * 25 / 1000000, reset)
        
        ccLats = coarseCounter
    
    if isinstance(obj, userKBlock) and obj.btf == b'\x99':
        statArray.append(obj.data)
        
    if isinstance(obj, userKBlock) and obj.btf == b'\x55':
        statArray.append(obj.data)
        fifoDrop = statArray[0:20].uint
        pwidthDrop = statArray[20:40].uint
        dcountDrop = statArray[40:60].uint
        triggerDrop = statArray[60:80].uint
        pulseError = statArray[80:96].uint
        statArray = bitstring.BitArray()
        #print("FIFO drop:", fifoDrop, "Pulsewidth drop:", pwidthDrop, "Darkcount drop:", dcountDrop, "Trigger drop:", triggerDrop, "Pulse error:", pulseError)
        


        
    if isinstance(obj, dataBlock):
        dataArray.append(obj.data)
        hasPreviousData = True
        #print(obj)
        i += 1
    
    if isinstance(obj, separator7Block):
        dataArray.append(obj.data)
        hasPreviousData = True
        #print(obj)
        i += 1
        
    if isinstance(obj, separatorBlock):
        dataArray.append(obj.data)
        hasPreviousData = True
         #print(obj)
        i += 1
        
    if i > 30:
        break
    
