import os
import sys
from time import perf_counter

import struct
import usb.core
import usb.util
import time

def format_bytes(size):
   B = float(size)
   KB = float(1024)
   MB = float(KB ** 2) # 1,048,576
   if B < KB:
      return '{0} {1}'.format(B,'B')
   elif KB <= B < MB:
      return '{0:.2f} KB'.format(B/KB)
   else :
      return '{0:.2f} MB'.format(B/MB)

# USB device configuration
VENDOR_ID = 0xcafe  # Replace with your device's vendor ID
PRODUCT_ID = 0x4000  # Replace with your device's product ID
ENDPOINT = 0x83  # Endpoint address for bulk transfer (IN endpoint 3)
BUFFER_FILE = "fic1_capture_w_injection_1us_V2.bin"  # File to store received binary data
CHUNK_SIZE = 1024*4  # Size of each bulk transfer in bytes
MULTIPLES = 512



def main():

    frameOld = 0
    frameNew = 0
    # Find the USB device
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if dev is None:
        raise ValueError("Device not found")
    

    # Open the binary buffer file for writing
    timeOld = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
    with open(BUFFER_FILE, "wb") as buffer_file:
        print(f"Receiving data and writing to {BUFFER_FILE}...")
        try:
            # Read data from the USB endpoint
            data = usb.util.create_buffer(CHUNK_SIZE)

            while True:
                len = dev.read(ENDPOINT, data, timeout=10000)
                if len != 0:
                    print(f"Received {len} bytes")
                    # Write the received data to the file
                    buffer_file.write(data[:len])

        except usb.core.USBError as e:
            if e.errno == 110:  # Timeout error
                print("Timeout reached, stopping data reception.")
            else:
                print(f"USB Error: {e}")
        except KeyboardInterrupt:
            print("Interrupted by user, stopping data reception.")

if __name__ == "__main__":
    main()
