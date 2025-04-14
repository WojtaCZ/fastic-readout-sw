#!/usr/bin/python3

import sys
import serial
from time import perf_counter

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

def main():
    if len(sys.argv) != 2:
        print("No port name specified")
        exit()
    
    ser = serial.Serial(sys.argv[1])
    

    print("Testing port", sys.argv[1])
    
    t_start = perf_counter()
    data = ser.read(512*4096)
    t_stop = perf_counter()
    
    print("Time:", t_stop - t_start)
    print("Data size:", len(data))
    print("Throughput:", format_bytes(512*4096 / (t_stop - t_start)) + "/s")

if __name__ == "__main__":
    main()