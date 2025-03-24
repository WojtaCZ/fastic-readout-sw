import usb
import binascii
import struct
import matplotlib.pyplot as plt
import matplotlib.animation as animation

readout = usb.core.find(idVendor=0xcafe, idProduct=0x4000)

if readout is None:
    raise ValueError('Device not found')

readout.read(0x83, 512, 10000)

# Initialize lists to store voltage and current values
hvVoltage_list = []
hvCurrent_list = []

# Set up the plot
fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)

line1, = ax1.plot([], [], 'b-', label='HV Voltage')
line2, = ax2.plot([], [], 'r-', label='HV Current')

ax1.set_ylim(0, 80)
ax2.set_ylim(0, 10000)

ax1.set_ylabel('HV Voltage (V)', color='b')
ax2.set_ylabel('HV Current (A)', color='r')
ax2.set_xlabel('Time')

ax1.legend(loc='upper left')
ax2.legend(loc='upper left')

# Add gridlines
ax1.grid(True)
ax2.grid(True)

def animate(i):
    data = readout.read(0x83, 512, 10000)
   # print(binascii.hexlify(data))
    #print(len(data))
    
    data = data[0:56]

    if len(data) < 56:
        return

    dataStruct = struct.unpack('iBdddddd', data)
   # print(dataStruct)
    temp = dataStruct[2]
    voltage = dataStruct[3]
    fastIC1Voltage = dataStruct[4]
    fastIC2Voltage = dataStruct[5]
    hvVoltage = dataStruct[6]
    hvCurrent = dataStruct[7]

    # Append new data to lists
    hvVoltage_list.append(hvVoltage)
    hvCurrent_list.append(hvCurrent)

    # Keep only the most recent 100 values
    hvVoltage_list[:] = hvVoltage_list[-100:]
    hvCurrent_list[:] = hvCurrent_list[-100:]

    # Update plot data
    line1.set_data(range(len(hvVoltage_list)), hvVoltage_list)
    line2.set_data(range(len(hvCurrent_list)), hvCurrent_list)

    # Rescale the plot
    ax1.relim()
    ax1.autoscale_view()
    ax2.relim()
    ax2.autoscale_view()

    # Update the title with the most recent values
    fig.suptitle(f'HV Voltage: {hvVoltage:.2f} V, HV Current: {hvCurrent:.2f} A')


ani = animation.FuncAnimation(fig, animate, interval=10)

plt.show()
