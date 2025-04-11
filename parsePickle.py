import pickle
import bitstring
from bitstring import BitArray
from blocktypes import separatorBlock, separator7Block, idleBlock, userKBlock, dataBlock

def parse_channels_data(hex_string):
    # Configurable constants (match these to your design)
    FP_TIMESTAMP_BITS = 22
    FP_PULSE_WIDTH_BITS = 14
    FP_CHANNEL_ADDRESS_BITS = 4

    # Bit widths for each field
    BIT_WIDTHS = {
        "channel": FP_CHANNEL_ADDRESS_BITS,
        #"locked": 1,
        "pkt_type": 2,
        "timestamp": FP_TIMESTAMP_BITS,
        "pulse_width": FP_PULSE_WIDTH_BITS,
        "debug": 1,
        "parity_channel": 1,
        "parity_pkt_type": 1,
        "parity_timestamp": 1,
        "parity_pulse_width": 1,
        "parity_parity": 1
    }

    TOTAL_BITS = sum(BIT_WIDTHS.values())
    BITS_PER_HEX_CHAR = 4
    HEX_CHARS_PER_PACKET = (TOTAL_BITS + BITS_PER_HEX_CHAR - 1) // BITS_PER_HEX_CHAR

    # Convert hex string to binary string
    bin_str = bin(int(hex_string, 16))[2:].zfill(len(hex_string) * 4)

    # Pad if necessary
    if len(bin_str) % TOTAL_BITS != 0:
        print("Padding!")
        bin_str = bin_str.zfill((len(bin_str) // TOTAL_BITS + 1) * TOTAL_BITS)

    # Helper: extract field from bits
    def extract_fields(bits):
        idx = 0
        fields = {}
        for key, width in BIT_WIDTHS.items():
            fields[key] = bits[idx:idx + width]
            idx += width
        return fields

    # Helper: decode packet type
    pkt_type_map = {
        '00': "PKT_TOA_TOTNL",
        '01': "PKT_TOA",
        '10': "PKT_TOTLN",
        '11': "PKT_TOA_TOTLN",
    }

    # Process each packet
    num_packets = len(bin_str) // TOTAL_BITS
    for i in range(num_packets):
        bits = bin_str[i * TOTAL_BITS:(i + 1) * TOTAL_BITS]
        fields = extract_fields(bits)

        channel_parity_check = 'OK' if ((fields['channel'].count('1') % 2) == int(fields['parity_channel'])) else 'FAIL'
        pkt_type_parity_check = 'OK' if ((fields['pkt_type'].count('1') % 2) == int(fields['parity_pkt_type'])) else 'FAIL'
        timestamp_parity_check = 'OK' if ((fields['timestamp'].count('1') % 2) == int(fields['parity_timestamp'])) else 'FAIL'
        pulse_width_parity_check = 'OK' if ((fields['pulse_width'].count('1') % 2) == int(fields['parity_pulse_width'])) else 'FAIL'
        parity_parity_check = 'OK' if (((int(fields['parity_pkt_type']) + int(fields['parity_timestamp']) + int(fields['parity_pulse_width'])) % 2) == int(fields['parity_parity'])) else 'FAIL'

        fields['timestamp'] = int(fields['timestamp'], 2)
        fields['pulse_width'] = int(fields['pulse_width'], 2)

        print(f"  --- Packet {i+1} ---")
        print(f"  Channel: {int(fields['channel'], 2)}")
        #print(f"  Locked: {bool(int(fields['locked'], 2))}")
        print(f"  Packet Type: {pkt_type_map[fields['pkt_type']]}")
        print(f"  Timestamp: {fields['timestamp']}")
        #print(f"     Coarse    (25ns): {fields['timestamp'] >> 10}")
        #print(f"     Fine     (781ps): {(fields['timestamp'] >> 5) % (1<<5)}")
        #print(f"     Ultrafine (25ps): {fields['timestamp'] % (1<<5)}")
        print(f"  Pulse Width: {fields['pulse_width']}")
        #print(f"     Coarse    (25ns): {fields['pulse_width'] >> 5}")
        #print(f"     Fine     (781ps): {fields['pulse_width'] % (1<<5)}")
        print(f"  Debug: {bool(int(fields['debug'], 2))}")
        print(f"  Parity channel: {fields['parity_channel']} ({channel_parity_check})")
        print(f"  Parity pkt_type: {fields['parity_pkt_type']} ({pkt_type_parity_check})")
        print(f"  Parity timestamp: {fields['parity_timestamp']} ({timestamp_parity_check})")
        print(f"  Parity pulse_width: {fields['parity_pulse_width']} ({pulse_width_parity_check})")
        print(f"  Parity parity: {fields['parity_parity']} ({parity_parity_check})")
        print()
        
def parse_statistics_data(data):
    fifoDrop = data[0:20].uint
    pwidthDrop = data[20:40].uint
    dcountDrop = data[40:60].uint
    triggerDrop = data[60:80].uint
    pulseError = data[80:96].uint

    print(f"--- Statistics ---")
    print(f"FIFO drop: {int(fifoDrop)}")
    print(f"Pulse width drop: {int(pwidthDrop)}")
    print(f"Dark count drop: {int(dcountDrop)}")
    print(f"Trigger drop: {int(triggerDrop)}")
    print(f"Malformed pulses: {int(pulseError)}")
    print()
    
def parse_coarse_counter(data):
    sent = data[8:31].uint
    coarse = data[31:55].uint
    reset = (data[55])
    
    print(f"--- Coarse counter ---")
    print(f"Sent packets: {int(sent)}")
    print(f"Coarse counter: {int(coarse)}")
    print(f"Was reset? - {reset}")
    print()
    
    
    

statArray = bitstring.BitArray()
dataArray = bitstring.BitArray()

dataCounter = 0
hasPreviousData = False


# Load the parsed pickle file
objects = []
with (open("fic1_capture_w_injection_50us", "rb")) as openfile:
    while True:
        try:
            objects.append(pickle.load(openfile))
        except EOFError:
            break


# Go through the objects
for idx,obj in enumerate(objects[0]):
    

    # PARSE THE COARSE COUNTER
    if isinstance(obj, userKBlock) and obj.btf == b'\xD2':
        parse_coarse_counter(obj.data)
        reset = (not obj.data[55])
        sent = obj.data[-48:-25].uint
        coarse = obj.data[-25:-1].uint
        print(sent)
        

    
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
        dataArray.append(obj.data)
        hasPreviousData = True
    
    if isinstance(obj, separator7Block):
        dataArray.append(obj.data)
        hasPreviousData = True
        
    if isinstance(obj, separatorBlock):
        dataArray.append(obj.data)
        hasPreviousData = True
        
    # If we received data previously but now, the block is a control, parse the data
    if hasPreviousData == True and not isinstance(obj, dataBlock) and not isinstance(obj, separatorBlock) and not isinstance(obj, separator7Block):
        hasPreviousData = False
        print("Received data block size:", len(dataArray), "bits")
        print("Hex data:", dataArray.hex)
        parse_channels_data(dataArray.hex)
        dataArray = bitstring.BitArray()
        dataCounter += 1
    
    # Just for debuggint to limit the packet count being parsed
    if dataCounter > 5000:
        break
    
