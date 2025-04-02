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
with (open("calpulse", "rb")) as openfile:
    while True:
        try:
            objects.append(pickle.load(openfile))
        except EOFError:
            break
        
for obj in objects[0]:
    if isinstance(obj, userKBlock) and obj.btf == b'\xD2':
        reset = (obj.data[55])
        sent = obj.data[-48:-25].uint
        coarse = obj.data[-25:-1].uint
        
        print(sent, coarse, reset)