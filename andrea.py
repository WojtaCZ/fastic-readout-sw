#!/bin/python3

def parse_channels_data(hex_string):
    # Configurable constants (match these to your design)
    FP_TIMESTAMP_BITS = 22
    FP_PULSE_WIDTH_BITS = 14
    FP_CHANNEL_ADDRESS_BITS = 4

    # Bit widths for each field
    BIT_WIDTHS = {
        "channel": FP_CHANNEL_ADDRESS_BITS,
        "locked": 1,
        "pkt_type": 2,
        "timestamp": FP_TIMESTAMP_BITS,
        "pulse_width": FP_PULSE_WIDTH_BITS,
        "debug": 1,
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

        pkt_type_parity_check = 'OK' if ((fields['pkt_type'].count('1') % 2) == int(fields['parity_pkt_type'])) else 'FAIL'
        timestamp_parity_check = 'OK' if ((fields['timestamp'].count('1') % 2) == int(fields['parity_timestamp'])) else 'FAIL'
        pulse_width_parity_check = 'OK' if ((fields['pulse_width'].count('1') % 2) == int(fields['parity_pulse_width'])) else 'FAIL'
        parity_parity_check = 'OK' if (((int(fields['parity_pkt_type']) + int(fields['parity_timestamp']) + int(fields['parity_pulse_width'])) % 2) == int(fields['parity_parity'])) else 'FAIL'

        fields['timestamp'] = int(fields['timestamp'], 2)
        fields['pulse_width'] = int(fields['pulse_width'], 2)

        print(f"--- Packet {i+1} ---")
        print(f"Channel: {int(fields['channel'], 2)}")
        print(f"Locked: {bool(int(fields['locked'], 2))}")
        print(f"Packet Type: {pkt_type_map[fields['pkt_type']]}")
        print(f"Timestamp: {fields['timestamp']}")
        print(f"   Coarse    (25ns): {fields['timestamp'] >> 10}")
        print(f"   Fine     (781ps): {(fields['timestamp'] >> 5) % (1<<5)}")
        print(f"   Ultrafine (25ps): {fields['timestamp'] % (1<<5)}")
        print(f"Pulse Width: {fields['pulse_width']}")
        print(f"   Coarse    (25ns): {fields['pulse_width'] >> 5}")
        print(f"   Fine     (781ps): {fields['pulse_width'] % (1<<5)}")
        print(f"Debug: {bool(int(fields['debug'], 2))}")
        print(f"Parity pkt_type: {fields['parity_pkt_type']} ({pkt_type_parity_check})")
        print(f"Parity timestamp: {fields['parity_timestamp']} ({timestamp_parity_check})")
        print(f"Parity pulse_width: {fields['parity_pulse_width']} ({pulse_width_parity_check})")
        print(f"Parity parity: {fields['parity_parity']} ({parity_parity_check})")
        print()

# Example usage
hex_input = "04003ceb0e76"
parse_channels_data(hex_input)