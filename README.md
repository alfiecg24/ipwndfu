![](repo/ipwndfu.png)
# Open-source jailbreaking tool for millions of iOS devices


**Read [disclaimer](#disclaimer) before using this software.*

## About this fork
#### The following are goals for this fork

* gain Python3 support, as the [original ipwndfu](https://github.com/axi0mx/ipwndfu) is out of date
* fix libusb errors that may arise when running on modern macOS version
* add the ability to run ipwndfu on M1 macs
* add support for more devices

#### Any contributions are greatly appreciated!

## checkm8

* permanent unpatchable bootrom exploit for hundreds of millions of iOS devices

* meant for researchers, this is not a jailbreak with Cydia yet

* allows dumping SecureROM, decrypting keybags for iOS firmware, and demoting device for JTAG

* check compatibility using the [compatibility page](https://github.com/alfiecg24/ipwndfu/blob/master/Compatibility.md)
## Quick start guide for checkm8

1. Use a cable to connect device to your Mac. Hold buttons as needed to enter DFU Mode.

2. First run ```./ipwndfu -p``` to exploit the device. Repeat the process if it fails, it is not reliable.

3. Run ```./ipwndfu --dump-rom``` to get a dump of SecureROM.

4. Run ```./ipwndfu --decrypt-gid KEYBAG``` to decrypt a keybag.

5. Run ```./ipwndfu --demote``` to demote device and enable JTAG.

## alloc8 and 24Kpwn

* allows for untethered (blobless) downgrades and jailbreaks on all iPhone 3GS devices
* lets you dump NOR or flash your own custom NOR/NOR backup

## Quick start guide for alloc8

1. Use a cable to connect device to your Mac. Hold buttons as needed to enter DFU Mode.

2. First, run ```./ipwndfu -p``` to exploit the device. Repeat the process if it fails, the exploit may not work on the first try.

3. Next, run ```./ipwndfu -x``` to install alloc8 exploit to NOR. As long as the screen is not red, the exploit should have been successful.
   
4. If you have an old BootROM device, ipwndfu will tell you to let you use 24Kpwn instead - which is faster than alloc8.

5. Check out the [jailbreak guide](https://github.com/axi0mX/ipwndfu/blob/master/JAILBREAK-GUIDE.md) for a more detailed tutorial.

## Features

* Place modern devices into pwned DFU mode using the checkm8 exploit

* Jailbreak and downgrade iPhone 3GS with either of the alloc8 or 24Kpwn untethered bootrom exploits.

* Utilise the follwing exploits: limera1n, SHAtter, steaks4uce, alloc8 24Kpwn and checkm8.

* Dump SecureROM from pwned devices.

* Dump/flash NOR on the iPhone 3GS.

* Encrypt or decrypt hex data on a connected device in pwned DFU Mode using its GID or UID key.


## Dependencies

This tool should be compatible with Mac and Linux. It won't work in a virtual machine - the USB passthrough is not quick enough for the exploits.

* libusb, `If you are using Linux: install libusb using your package manager.`
* [iPhone 3GS iOS 4.3.5 iBSS](#ibss)


## Tutorial

This tool can be used to downgrade or jailbreak iPhone 3GS (new bootrom) without SHSH blobs, as documented in the [jailbreak guide](https://github.com/axi0mX/ipwndfu/blob/master/JAILBREAK-GUIDE.md).


## Exploit write-up

Write-up for alloc8 exploit can be found here:

https://github.com/axi0mX/alloc8


## iBSS

Download iPhone 3GS iOS 4.3.5 IPSW from Apple:

http://appldnld.apple.com/iPhone4/041-1965.20110721.gxUB5/iPhone2,1_4.3.5_8L1_Restore.ipsw

In Terminal, extract iBSS using the following command, then move the file to ipwndfu folder:

```
unzip -p <path-to-IPSW> Firmware/dfu/iBSS.n88ap.RELEASE.dfu > <path-to-ipwndfu>/n88ap-iBSS-4.3.5.img3
```


## Coming soon!

* Reorganize and refactor code.

* Easier setup: download iBSS automatically using partial zip.

* Dump SecureROM on S5L8720 devices.

* Install custom boot logos on devices jailbroken with 24Kpwn and alloc8.

* Enable verbose boot on devices jailbroken with 24Kpwn and alloc8.

## Disclaimer

**This is BETA software.**

Backup your data.

This tool is currently in beta and could potentially brick your device. It will attempt to save a copy of data in NOR to nor-backups folder before flashing new data to NOR, and it will attempt to not overwrite critical data in NOR which your device requires to function. If something goes wrong, hopefully you will be able to restore to latest IPSW in iTunes and bring your device back to life, or use nor-backups to restore NOR to the original state, but I cannot provide any guarantees.

**There is NO warranty provided.**

THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY APPLICABLE LAW. THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM IS WITH YOU. SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING, REPAIR OR CORRECTION.

## Toolchain

You will not need to use `make` or compile anything to use ipwndfu. However, if you wish to make changes to assembly code in `src/*`, you will need to use an ARM toolchain and assemble the source files by running `make`.

If you are using macOS with Homebrew, you can use binutils and gcc-arm-embedded. You can install them with these commands:

```
brew install binutils
brew cask install https://raw.githubusercontent.com/Homebrew/homebrew-cask/b88346667547cc85f8f2cacb3dfe7b754c8afc8a/Casks/gcc-arm-embedded.rb
```

## Credit

geohot for limera1n exploit

posixninja and pod2g for SHAtter exploit

chronic, CPICH, ius, MuscleNerd, Planetbeing, pod2g, posixninja, et al. for 24Kpwn exploit

pod2g for steaks4uce exploit

walac for pyusb
