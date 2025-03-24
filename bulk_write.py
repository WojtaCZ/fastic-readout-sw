import usb.core
import usb.util

# Find the USB device (replace with your device's vendor and product ID)
VENDOR_ID = 0xcafe  # Replace with your device's vendor ID
PRODUCT_ID = 0x4000  # Replace with your device's product ID

# Find the device
device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

if device is None:
    raise ValueError("Device not found")


# Get the endpoint (replace with your endpoint address)
BULK_ENDPOINT = 0x03  # Replace with your bulk endpoint address

# Write a byte to the bulk endpoint
data = b'\x01'  # Replace with the byte you want to send
device.write(BULK_ENDPOINT, data)

print("Byte written to the bulk endpoint.")