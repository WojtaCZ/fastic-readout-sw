import usb.core
import usb.util
import struct
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Find our device
dev = usb.core.find(idVendor=0xcafe, idProduct=0x4000)

# Was it found?
if dev is None:
    raise ValueError('Device not found')

# Initialize data lists
current_data = []
voltage_data = []

# Create figure and subplots
fig, (ax1, ax2) = plt.subplots(2, 1)



def update_data(frame):
    # Read current and voltage from the device
    current = struct.unpack('f', dev.ctrl_transfer(0xC0, 0x04, 0, 0, 4))[0]
    voltage = struct.unpack('f', dev.ctrl_transfer(0xC0, 0x05, 0, 0, 4))[0]

    # Append data to lists
    current_data.append(current)
    voltage_data.append(voltage)

    # Limit lists to the last 1000 points
    current_data[:] = current_data[-100:]
    voltage_data[:] = voltage_data[-100:]
    
    # Clear and plot current data
    ax1.clear()
    ax1.plot(current_data)
    ax1.set_title(f'Current (Latest: {current:.2f} uA)')
    ax1.grid(True)  # Add grid to current plot


    # Clear and plot voltage data
    ax2.clear()
    ax2.plot(voltage_data)
    ax2.set_title(f'Voltage (Latest: {voltage:.2f} V)')
    ax2.grid(True)  # Add grid to voltage plot


# Set up the animation
ani = animation.FuncAnimation(fig, update_data, interval=1)

# Show the plot
plt.tight_layout()
plt.show()
