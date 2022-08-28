import sys, time
import usb1 # pyusb: use 'pip install pyusb' to install this module

MAX_PACKET_SIZE = 0x800

def acquire_device(timeout=5.0, match=None, fatal=True):
    context = usb1.USBContext()

    for device in context.getDeviceIterator(skip_on_error=True):
        if device.getVendorID() == 0x5AC and device.getProductID() == 0x1227:
            return device

def release_device(device: usb1.USBDeviceHandle, interface: usb1.USBInterface):
    #print 'Releasing device handle.'
    device.releaseInterface(interface)
    device = device.close()

def reset_counters(device):
    #print 'Resetting USB counters.'
    assert device.ctrl_transfer(0x21, 4, 0, 0, 0, 1000) == 0

def usb_reset(device: usb1.USBDeviceHandle):
    print('Performing USB port reset.')
    try:
        device.resetDevice()
    except usb.core.USBError:
        # OK: doesn't happen on Yosemite but happens on El Capitan and Sierra
        pass
        print('Caught exception during port reset; should still work.')

def send_data(device, data):
    print('Sending 0x%x of data to device.' % len(data))
    index = 0
    while index < len(data):
        amount = min(len(data) - index, MAX_PACKET_SIZE)
        assert device.ctrl_transfer(0x21, 1, 0, 0, data[index:index + amount], 5000) == amount
        index += amount

def get_data(device, amount):
    print('Getting 0x%x of data from device.' % amount)
    data = str()
    while amount > 0:
        part = min(amount, MAX_PACKET_SIZE)
        ret = device.ctrl_transfer(0xA1, 2, 0, 0, part, 5000)
        assert len(ret) == part
        data += ret.tostring()
        amount -= part
    return data

def request_image_validation(device):
    print('Requesting image validation.')
    assert device._controlTransfer(0x21, 1, 0, 0, b'', 0, 1000) == 0
    device._controlTransfer(0xA1, 3, 0, 0, 6, 1000)
    device.ctrl_transfer(0xA1, 3, 0, 0, 6, 1000)
    device.ctrl_transfer(0xA1, 3, 0, 0, 6, 1000)
    usb_reset(device)
