import usb1, struct, time, array, ctypes

def libusb1_create_ctrl_transfer(device, request, timeout):
  ptr = device.getTransfer(0)

  #print(dir(usb1.USBTransfer))
  transfer = ptr._USBTransfer__transfer.contents
  
  transfer.endpoint = 0
  transfer.type = 0
  transfer.timeout = timeout
  transfer.buffer = request.buffer_info()[0]
  transfer.length = len(request)
  transfer.userData = None
  ptr.setCallback(None)
  transfer.flags = 1 << 1


def libusb1_async_ctrl_transfer(
  device: usb1.USBDeviceHandle,
  bm_request_type: int,
  b_request: int,
  w_value: int,
  w_index: int,
  data: bytes,
  timeout: float,
) -> None:

  global request, transfer_ptr, never_free_device
  request_timeout = int(timeout) if timeout >= 1 else 0
  start = time.time()
  never_free_device = device
  request = array.array(
      "B",
      struct.pack("<BBHHH", bm_request_type, b_request, w_value, w_index, len(data))
      + data,
  )
  transfer_ptr = device.getTransfer(request)
  assert device.submit(transfer_ptr) == 0

  while time.time() - start < timeout / 1000.0:
      pass


context = usb1.USBContext()

for device in context.getDeviceIterator(skip_on_error=True):
    if device.getVendorID() == 0x5AC and device.getProductID() == 0x1227:
        device = device.open()
        print(device.getSerialNumber())
        print(type(device))
        #device._controlTransfer(0x80, 6, 0x304, 0x40A, b'A' * 0xC0, len(b'A' * 0xC0), 1)
        libusb1_create_ctrl_transfer(device, 0, 1)