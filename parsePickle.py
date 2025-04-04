import pickle


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



for idx,obj in enumerate(objects[0]):
    if isinstance(obj, userKBlock) and obj.btf == b'\xD2':
        reset = (obj.data[55])
        sent = obj.data[-48:-25].uint
        coarse = obj.data[-25:-1].uint
        
        print(sent, coarse, reset)
        
    if isinstance(obj, dataBlock):
        #channel = obj.data[0:4].uint
        #detType = obj.data[4:6]
        #timestamp = obj.data[6:28].uint
        #pw = obj.data[28:42].uint
        
        #print(channel, detType, timestamp, pw)
        print(obj)
        i += 1
    
    if isinstance(obj, separator7Block):
        print(obj)
        i += 1
        
    if isinstance(obj, separatorBlock):
        print(obj)
        i += 1
        
    if i > 2:
        break