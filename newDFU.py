import sys, time
import usb1

MAX_PACKET_SIZE = 0x800

def acquire_device(timeout=5.0, match=None, fatal=True):
    context = usb1.USBContext()

    for device in context.getDeviceIterator(skip_on_error=True):
        if device.getVendorID() == 0x5AC and device.getProductID() == 0x1227:
            device = device.open()
            return device

def release_device(device: usb1.USBDeviceHandle):
    device = device.close()