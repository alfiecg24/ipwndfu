# New method - use gaster for help

import usb, dfu, array, ctypes, time, sys, struct

from Transfers import *


def main():
    print("*** Control transfer test ***")
    time.sleep(2)
    device = dfu.acquire_device()
    print("[*] Got device")
    time.sleep(1)
    #print("[*] Initialising DFU interface")
    #control_transfer(device, 0x21, 1, 0, 0, 0x40)
    #print("[*] Control transfer sent")
   # control_transfer(device, 0x21, 4, 0, 0, 0)
    #time.sleep(2)
    #print("[*] If device entered DFU, transfer was a success")
    #time.sleep(1)
   # print("[*] Trying asynchronous transfer")
    #try:
     #   libusb1_async_ctrl_transfer(device, 0x21, 1, 0, 0, b'A' * 10)
     #   print("[*] Asynchronous transfer complete")
    #except AssertionError:
    #    print("[*] Asynchronous transfer failed")

    print("[*] Attempting to stall")
    stall(device)

main()