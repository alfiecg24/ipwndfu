# Jailbreak guide for iPhone 3GS (old or new bootrom)

### Steps

1. Backup any data. Everything will be removed from your phone as it is a **full** restore.

2. [Figure out whether your device is old or new bootrom](#decoding-iphone-3gs-serial-number)

3. [Generate a custom 24Kpwn IPSW for iPhone 3GS (make sure to select old bootrom)](#how-to-create-a-24kpwn-ipsw).

4. [Restore your custom IPSW](#how-to-restore-to-a-custom-ipsw)



#### Notes:
* Installation takes about 30 seconds. Once NOR is being flashed, the screen will be green for about 10 seconds, and then your phone will reboot.

* If there are any errors before the screen turned green, it is safe to try again.

* If the screen turns red, something went wrong while your phone was being flashed. Trying again probably won't help.

* If there are no issues, the phone will reboot and automatically boot into iOS.

### 3 second delay during boot when using a phone jailbroken with alloc8

alloc8 exploit takes about 3 seconds to run.

When your phone is off, to turn it on you will need to keep holding the Power button for at least 3 seconds, or your phone will not turn on. This might be because LLB protects against accidental presses of the Power button by shutting down the phone if the power button is not being held anymore. Without an exploit it takes less than a second before this check happens, but with alloc8 exploit it will happen after about 3 seconds. It might be possible to change this behavior by patching LLB.

If your phone enters deep sleep, there will be a 3 second delay before it wakes up. This can be fixed if you disable deep sleep with a tweak from Cydia, but your phone's battery life will decrease.


### Where to download older IPSWs

Always download IPSWs directly from Apple, because IPSWs from other sites could be infected with malware.

There is a trusted site where you can find legitimate Apple download links for older IPSW files:

https://ipsw.me/


### How to create a 24Kpwn IPSW

* Download [sn0wbreeze v2.9.6]("https://mega.nz/folder/k4FAXCIB#Fk7pxs6ikYzL3YBvAGX5ig/file/A8M0gaKJ") - it _must_ be this version otherwise your downgrade won't work.
* Download the IPSW of the version you're downgrading to as put these two files in a folder for you to find later on
* For the next steps, you will need a Windows VM. The easiest way is to just get a free trial for [Parallels]("https://www.parallels.com"), but the open-source [UTM]("https://github.com/utmapp/UTM/releases/tag/v3.2.4") is also a great alternative (but requires more setup) - just download `UTM.dmg`.
* Setup your VM, you can find guides online, and then transfer the folder mentioned previously to the VM.
* Open sn0wbreeze - if you get an error about low storage, moving the file into the `C:\` directory usually works. If asked, make sure to create an IPSW for an old bootrom iPhone 3GS.
* Create your custom IPSW with your preferred customisation options, and then [put your device into pwned DFU mode](#how-to-restore-to-a-custom-ipsw) to begin the restore process.


### Compatibility with older iOS versions

Newer phones might not support some older versions of iOS. You cannot brick your phone by attempting to restore an older version of iOS, so it might be worth it to try anyway. If iTunes restore fails with Error 28, the hardware of your phone is not compatible with that version of iOS.

| Manufactured | Error 28   | Success    |
|--------------|------------|------------|
| Week 38 2010 | N/A        | 3.1+       |
| Week 48 2010 | N/A        | 3.1+       |
| Week  3 2011 | 3.x        | 4.3.3+     |
| Week 14 2011 | 3.x        | 4.0+       |
| Week 23 2011 | N/A        | 3.1.2+     |
| Week 29 2011 | 3.x        | 4.0+       |
| Week 36 2011 | 3.x        | 4.0+       |
| Week 26 2012 | 3.x, 4.x   | 5.0+       |

You can find the week and year of manufacture by looking at the serial number of your phone. If your phone is from 2011 or 2012, help me expand this list and let me what versions worked or didn't work.


### Decoding iPhone 3GS serial number

```
Serial number: AABCCDDDEE
AA = Device ID
B = 2009=9, 2010=0, 2011=1, 2012=2
CC = Week of production
DDD = Unique ID
EE = Color
```


### How to restore to a custom IPSW

1. Enter DFU Mode using [this guide](https://www.theiphonewiki.com/wiki/DFU_Mode) if needed.

2. Use the Windows VM to open the iREB program inside sn0wbreeze to put your iPhone in pwned DFU mode.

3. Still working on a way to restore with M1 Macs, for now you will have to use an actual Windows machine. If there is a white screen when restoring, you used the wrong version of sn0wbreeze.

4. If you have an old bootrom device, you're all finished once the restore finishes. If not, use ipwndfu to put your device into pwned DFU using the following commands
```
$ ./ipwndfu -p
*** based on limera1n exploit (heap overflow) by geohot ***
Found: CPID:8920 CPRV:15 CPFM:03 SCEP:03 BDID:00 ECID:XXXXXXXXXXXXXXXX SRTG:[iBoot-359.3.2]
Device is now in pwned DFU Mode.
```

5. Finally, install the alloc8 exploit to NOR and the phone should (hopefully) boot into iOS!

```
$ ./ipwndfu -x
Installing alloc8 exploit to NOR.
Dumping NOR, part 1/8.
Dumping NOR, part 2/8.
Dumping NOR, part 3/8.
Dumping NOR, part 4/8.
Dumping NOR, part 5/8.
Dumping NOR, part 6/8.
Dumping NOR, part 7/8.
Dumping NOR, part 8/8.
NOR backed up to file: nor-backups/nor-XXXXXXXXXXXXXXXX-20170409-224258.dump
Sending iBSS.
Waiting for iBSS to enter Recovery Mode.
Sending iBSS payload to flash NOR.
Sending run command.
If screen is not red, NOR was flashed successfully and device will reboot.
```