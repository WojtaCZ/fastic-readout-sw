from bitstring import BitArray

class dataPacket:
    def __init__(self, data, last_coarse_counter):
        self.channel = data[0:4].uint
        self.pkt_type = data[4:6].uint
        self.timestamp = data[6:28].uint
        self.pulse_width = data[28:42].uint
        self.debug = data[42]
        self.parity_channel = data[43]
        self.parity_pkt_type = data[44]
        self.parity_timestamp = data[45]
        self.parity_pulse_width = data[46]
        self.parity_all = data[47]
        self.parity_channel_check = (data[0:4].count(1) % 2) == self.parity_channel
        self.parity_pkt_type_check = (data[4:6].count(1) % 2) == self.parity_pkt_type
        self.parity_timestamp_check = (data[6:28].count(1) % 2) == self.parity_timestamp
        self.parity_pulse_width_check = (data[28:42].count(1) % 2) == self.parity_pulse_width
        self.parity_all_check = (data[0:4].count(1) + data[4:6].count(1) + data[6:28].count(1) + data[28:42].count(1)) % 2 == self.parity_all
        self.parity_ok = self.parity_channel_check and self.parity_pkt_type_check and self.parity_timestamp_check and self.parity_pulse_width_check and self.parity_all_check
        self.last_coarse_counter = last_coarse_counter

    def __str__(self):
        pkt_type_map = {
            0 : "PKT_TOA_TOTNL",
            1 : "PKT_TOA",
            2 : "PKT_TOTLN",
            3 : "PKT_TOA_TOTLN",
        }
        
        return f"[DATA] \n   Channel: {self.channel} \n   Packet type: {pkt_type_map[self.pkt_type]} \n   Timestamp: {self.timestamp} \n   Last coarse counter: {self.last_coarse_counter} \n   Pulse width: {self.pulse_width} \n   Debug: {self.debug} \n   Parity channel: {int(self.parity_channel)} ({'OK' if self.parity_channel_check else 'ERROR'}) \n   Parity pkt_type: {int(self.parity_pkt_type)} ({'OK' if self.parity_pkt_type_check else 'ERROR'}) \n   Parity timestamp: {int(self.parity_timestamp)} ({'OK' if self.parity_timestamp_check else 'ERROR'}) \n   Parity pulse width: {int(self.parity_pulse_width)} ({'OK' if self.parity_pulse_width_check else 'ERROR'}) \n   Parity all: {int(self.parity_all)} ({'OK' if self.parity_all_check else 'ERROR'}) \n   Oveall parity: {'OK' if self.parity_ok else 'ERROR'}"

class coarseCounterPacket:
    def __init__(self, data):
        self.sent = data[8:31].uint
        self.coarse = data[31:55].uint
        self.reset = (data[55])

    def __str__(self):
        return f"[COARSE COUNTER] \n   Sent packets: {self.sent} \n   Coarse counter: {self.coarse} \n   Was Reset?: {self.reset}"

class statisticsPacket:
    def __init__(self, data):
        self.fifoDrop = data[0:20].uint
        self.pwidthDrop = data[20:40].uint
        self.dcountDrop = data[40:60].uint
        self.triggerDrop = data[60:80].uint
        self.pulseError = data[80:96].uint

    def __str__(self):
        return f"[STATISTICS] \n   FIFO drop: {self.fifoDrop} \n   Pulse width drop: {self.pwidthDrop} \n   Dark count drop: {self.dcountDrop} \n   Trigger drop: {self.triggerDrop} \n   Malformed pulses: {self.pulseError}"