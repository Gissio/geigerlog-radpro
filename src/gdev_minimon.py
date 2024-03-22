#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gdev_minimon.py - GeigerLog commands to handle the MiniMon device
"""

###############################################################################
#    This file is part of GeigerLog.
#
#    GeigerLog is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    GeigerLog is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with GeigerLog.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

__author__          = "ullix"
__copyright__       = "Copyright 2016, 2017, 2018, 2019, 2020, 2021, 2022"
__credits__         = [""]
__license__         = "GPL3"



# MiniMon is a CO2 monitor available from multiple distributors, e.g. also from
# TFA Drostman. On Amazon as https://www.amazon.de/gp/product/B00TH3OW4Q/
# or: https://www.co2meter.com/products/co2mini-co2-indoor-air-quality-monitor
#
# The original may be: https://www.zyaura.com/product-detail/zgm053u/
# Download a manual from: https://www.zyaura.com/support-download/manual-zgm053u/
#
# Datasheet:
# http://co2meters.com/Documentation/AppNotes/AN146-RAD-0401-serial-communication.pdf
#
# Software:
# https://hackaday.io/project/5301-reverse-engineering-a-low-cost-usb-co-monitor
# https://github.com/heinemml/CO2Meter/blob/master/CO2Meter.py
#
#
# The USB ID by lsusb is:     ID 04d9:a052 Holtek Semiconductor, Inc.
#
# uderv rules:
# see more details at the end under: MiniMon  Version 1.0
# put into folder '/etc/udev/rules.d' a file named '90-co2mini.rules' with this content:
#
#     # To activate use command:   sudo udevadm control --reload-rules
#     # then unplug and replug MiniMon
#
#     ACTION=="remove", GOTO="minimon_end"
#
#     # Use this line if you have several MiniMons.
#     # The name /dev/minimon will be attached with numbers depending on the hidraw dev it is linked to, like: /dev/minimon1, /dev/minimon2, etc
#     #SUBSYSTEMS=="usb", KERNEL=="hidraw*", ATTRS{idVendor}=="04d9", ATTRS{idProduct}=="a052", GROUP="plugdev", MODE="0660", SYMLINK+="co2mini%n", GOTO="minimon_end"
#
#     # Use this line if you have only a single MiniMon
#     # The name /dev/minimon will never change
#     SUBSYSTEMS=="usb", KERNEL=="hidraw*", ATTRS{idVendor}=="04d9", ATTRS{idProduct}=="a052", GROUP="plugdev", MODE="0660", SYMLINK+="minimon", GOTO="minimon_end"
#
#     LABEL="minimon_end"


# import fcntl
from   gsup_utils       import *


def initMiniMon():
    """Start the MiniMon"""

    global fileHandleMiniMon, key, values, MiniMonThread, MiniMonThreadStop, old_alldata, old_time

    fncname ="initMiniMon: "

    if 'linux' not in sys.platform:             # Py3:'linux', Py2:'linux2'
        return "MiniMon runs aon Linux only!"

    dprint(fncname + "Initializing MiniMon")
    setIndent(1)

    gglobs.Devices["MiniMon"][DNAME] = "MiniMon"

    if gglobs.MiniMonVariables == "auto": gglobs.MiniMonVariables = "Temp, None, Xtra"  # Temp=Temperatur, Humidity=ignored, Xtra=CO2
    if gglobs.MiniMonOS_Device == "auto": gglobs.MiniMonOS_Device = "/dev/minimon"      # requires udev rule
    if gglobs.MiniMonInterval  == "auto": gglobs.MiniMonInterval  = 60                  # force saving after 60 seconds

    gglobs.MiniMonVariables = correctVariableCaps(gglobs.MiniMonVariables)              # not needed, but for consistency
    setLoggableVariables("MiniMon", gglobs.MiniMonVariables)                            # cleanup var names
    gglobs.Devices["MiniMon"][VNAME] = gglobs.Devices["MiniMon"][VNAME][0:3]            # list of no more than 3 variables

    # does the dev exist and is writable?
    if not os.access(gglobs.MiniMonOS_Device , os.W_OK):
        errmsg = "Could not find MiniMon device - is it connected and powered?"
        edprint(errmsg)
        setIndent(0)
        return errmsg

    # try opening the connection to the MiniMon device ('dev/minimon' if using udev entry)
    try:
        fileHandleMiniMon = open(gglobs.MiniMonOS_Device, "a+b",  0)
    except Exception as e:
        errmsg = "Could not open MiniMon device - is it connected and powered?"
        exceptPrint(e, errmsg)
        setIndent(0)
        return errmsg

    # try setting the HIDIOCSFEATURE_9
    # key needed for decryption in readMiniMonData
    key                 = [0xc4, 0xc6, 0xc0, 0x92, 0x40, 0x23, 0xdc, 0x96]
    HIDIOCSFEATURE_9    = 0xC0094806
    set_report3         = b"\x00" + bytearray(key)

    try:
        import fcntl
    except Exception as e:
        errmsg = "Could not import fcntl"
        exceptPrint(e, errmsg)
        setIndent(0)
        return errmsg

    try:
        fcntl.ioctl(fileHandleMiniMon, HIDIOCSFEATURE_9, set_report3)
    except Exception as e:
        errmsg = "Could not set FEATURE of MiniMon device - is it connected and powered?"
        exceptPrint(e, errmsg)
        setIndent(0)
        return errmsg

    # init to defaults
    values      = {}
    old_time    = 0

    # set the 'old_alldata' to all NAN
    old_alldata = {}
    for vname in gglobs.Devices["MiniMon"][VNAME]:
        if vname != "None":  old_alldata.update({vname: gglobs.NAN})
    # edprint(fncname + "old_alldata: ", old_alldata)

    # start threading
    MiniMonThreadStop    = False        # flag must be set before starting thread
    MiniMonThread        = threading.Thread(target = MiniMonThreadTarget)
    MiniMonThread.daemon = True
    MiniMonThread.start()
    # edprint("MiniMonThread.daemon: ", MiniMonThread.daemon)

    gglobs.Devices["MiniMon"][CONN] = True

    setIndent(0)

    return ""


def terminateMiniMon():
    """Stop the MiniMon"""

    global fileHandleMiniMon, MiniMonThread, MiniMonThreadStop

    fncname ="terminateMiniMon: "

    dprint(fncname)
    setIndent(1)

    dprint(fncname + "stopping thread")
    MiniMonThreadStop = True
    MiniMonThread.join() # "This blocks the calling thread until the thread
                         #  whose join() method is called is terminated."

    # verify that thread has ended, but wait not longer
    # than 3 sec (takes 0.006...0.016 ms)
    start = time.time()
    dur   = 0
    while MiniMonThread.is_alive():
        dur = 1000 * (time.time() - start)
        if dur > 3000: break

    dprint(fncname + "thread-status: is_alive: {}, waiting took: {:0.1f} ms".format(MiniMonThread.is_alive(), dur))

    # closing the MiniMon device
    # origin: initMiniMon: fileHandleMiniMon = open(gglobs.MiniMonOS_Device, "a+b",  0)
    try:
        fileHandleMiniMon.close()
        dprint(fncname + "Device '{}' closed".format(gglobs.MiniMonOS_Device))
    except Exception as e:
        errmsg = fncname + "Could not close device {} - terminating anyway".format(gglobs.MiniMonOS_Device)
        exceptPrint(e, errmsg)

    gglobs.Devices["MiniMon"][CONN] = False

    dprint(fncname + "Terminated")
    setIndent(0)


def MiniMonThreadTarget():
    """Thread that constantly triggers readings from the usb device."""

    global values, MiniMonThreadStop

    ### local function ############################################
    def printlostmsg():
        """used when the MiniMon connection was lost"""
        # must NOT use fprint - because thread - but using print ok

        global values, MiniMonThreadStop

        MiniMonThreadStop = True
        msg = "Lost connection to MiniMon device; stopping MiniMon.\nReconnect all devices in order to continue!"
        values = {}
        values["error"] = msg
        Queueprint(msg)
        dprint(msg.replace("\n", " "), debug=True)
    ### END local function ########################################

    fncname = "MiniMonThreadTarget: "

    while not MiniMonThreadStop:
        start = time.time()

        if os.access(gglobs.MiniMonOS_Device , os.R_OK):
            #dprint(fncname + "os:  {} is readable".format(gglobs.MiniMonOS_Device))
            try:
                brecMM = fileHandleMiniMon.read(8)       # len: 8, like: b'\xcd\xe4\x1f \xf0F\xbf*'
                extractMiniMonData(brecMM)

            except Exception as e:
                stre = str(e)
                exceptPrint("readMiniMonData: " + stre, "Failure in: data = list(fileHandleMiniMon.read(8))")
                if "[Errno 5]" in stre:          # [Errno 5] = input/output error
                    printlostmsg()

        else:
            edprint(fncname + "os:  {} is NOT readable".format(gglobs.MiniMonOS_Device))
            printlostmsg()

        minsleep = 0.05
        maxsleep = 3
        tsleep   = gglobs.logCycle * 0.5 # sleep for half a logCycle
        tsleep   = max(tsleep, minsleep) # but at least 50 ms = 0.1 sec * 0.5
        tsleep   = min(tsleep, maxsleep) # sleep no longer than 3 sec
        time.sleep(tsleep)


def extractMiniMonData(brecMM):
    """
    Function that reads one record from the device, decodes it, validates the
    checksum and, if valid, overwrites 'values' with the new data.
    """

    global values, MiniMonThreadStop

    fncname = "extractMiniMonData: "

    data  = list(brecMM)
    #print(fncname + "original  data: {}  hexlist: {}".format(decList(data), hexList(data)))

    if data[4] != 0x0d:
        # see: https://github.com/heinemml/CO2Meter/issues/4
        # newer devices don't encrypt the data, if byte 4 != 0x0d assume encrypted data
        # could result in wrong data sometimes?!
        data = decrypt(key, data)

    # must be decrypted first
    checksum = sum(data[:3]) & 0xff
    #print(fncname + "decrypted data: {}  hexlist: {}  checksum: {}  {}".format(decList(data), hexList(data), hex(checksum), checksum == data[3]))

    # at this stage data[4]==13 or there is an error
    if data[4] != 0x0d:
        edprint(fncname + "Byte[4] error: {}".format(hexList(data)))

    # verify checksum
    elif checksum != data[3]:
        edprint(fncname + "Checksum error: {}   checksum: {}".format(hexList(data), hex(checksum)))

    # ok, good data
    else:
        op = data[0]
        if op in [0x50, 0x42, 0x41]:                    # co2: 0x50==80, temp: 0x42==66, humid: 0x41==65
            val         = data[1] << 8 | data[2]
            values[op]  = val
            # mdprint(fncname + "op: {:3d}, val: {:5d}   values: {}".format(op, val, sortDict(values)))


def getInfoMiniMon(extended = False):
    """Info on the MiniMon"""

    MiniMonInfo  = "Configured Connection:        {}\n".format(gglobs.MiniMonOS_Device)

    if not gglobs.Devices["MiniMon"][CONN]: return MiniMonInfo + "<red>Device is not connected</red>"

    MiniMonInfo += "Connected Device:             {}\n"    \
                   "Configured Variables:         {}\n".   \
                   format(gglobs.Devices["MiniMon"][DNAME], gglobs.MiniMonVariables)

    if extended:
        MiniMonInfo += ""

    return MiniMonInfo


def getValuesMiniMon(varlist):
    """Read all data; return empty dict when not available"""

    global values, old_alldata, old_time

    start = time.time()

    fncname = "getValuesMiniMon: "

    alldata = {}
    for vmm in gglobs.Devices["MiniMon"][VNAME]:       # list of varnames
        # edprint(fncname + "vmm: ", vmm)
        if vmm != "None": alldata.update({vmm: gglobs.NAN})

    new_time = time.time()

    if "error" in values:
        playWav("err")
        efprint(values["error"])
        values = {}

    else:
        for i, vname in enumerate(varlist):
            # edprint(fncname + "i: ", i, "  vname: ", vname)

            if vname == "None": continue

            if   i == 0:
            # Temperature
                if 0x42 in values:
                    temp  = round(values[0x42] / 16.0 - 273.15, 2)   # 0x42 = 66
                    temp  = scaleVarValues(vname, temp, gglobs.ValueScale[vname])
                    alldata.update(  {vname: temp})

            elif i == 1:
            # Humidity
                if 0x41 in values:
                    humid = round(values[0x41] / 100.0        , 2)   # 0x41 = 65 # !not 0x44! as in original code
                    humid = scaleVarValues(vname, humid, gglobs.ValueScale[vname])
                    alldata.update(  {vname: humid})

            else: # i == 2
            # CO2
                if 0x50 in values:
                    co2   = values[0x50]                             # 0x50 = 80
                    co2   = scaleVarValues(vname, co2, gglobs.ValueScale[vname])
                    alldata.update(  {vname: co2})

    if (new_time - old_time) >= gglobs.MiniMonInterval:
        # saving now even if no values have changed
        old_time = new_time

    else:
        # do not save if all values are same as last reading
        if alldata == old_alldata:
                alldata = {}
        else:
                old_alldata = alldata
                old_time    = new_time

    vprintLoggedValues(fncname, varlist, alldata, (time.time() - start) * 1000)

    return alldata


def decrypt(key,  data):
    cstate = [0x48,  0x74,  0x65,  0x6D,  0x70,  0x39,  0x39,  0x65]
    shuffle = [2, 4, 0, 7, 1, 6, 5, 3]

    phase1 = [0] * 8
    for i, o in enumerate(shuffle):
        phase1[o] = data[i]

    phase2 = [0] * 8
    for i in range(8):
        phase2[i] = phase1[i] ^ key[i]

    phase3 = [0] * 8
    for i in range(8):
        phase3[i] = ( (phase2[i] >> 3) | (phase2[ (i-1+8)%8 ] << 5) ) & 0xff

    ctmp = [0] * 8
    for i in range(8):
        ctmp[i] = ( (cstate[i] >> 4) | (cstate[i]<<4) ) & 0xff

    out = [0] * 8
    for i in range(8):
        out[i] = (0x100 + phase3[i] - ctmp[i]) & 0xff

    return out


def hexList(d):
    return " ".join("%02X" % e for e in d)


def decList(d):
    return " ".join("%3d" % e for e in d)




# # *****************************************************************************
# # ************  MiniMon  Version 1.0 ******************************************
# # *****************************************************************************
# #
# # is a Python3 program to read data for CO2, Temperature, and Humidity (if
# # available) from a "CO2 Monitor" distributed by various suppliers.
# #
# # The program was adapted to Python3 by ullix.
# #
# # The original version is by: Henryk Plötz, (2015):
# # https://hackaday.io/project/5301-reverse-engineering-a-low-cost-usb-co-monitor/log/17909-all-your-base-are-belong-to-us
# #
# # MiniMon was verified to work on a device distributed by TFA Drostmann,
# # obtained from Amazon:
# # https://www.amazon.de/gp/product/B00TH3OW4Q/ref=ppx_yo_dt_b_asin_title_o02_s00?ie=UTF8&psc=1
# #
# # The device is used with the HIDRAW driver, which is the kernel interface for
# # Raw Access to USB and Bluetooth Human Interface Devices.
# #
# # Find out to which driver-address your MiniMon-device has connected by issuing
# # from the command line, before and after you connect the MiniMon-device to your
# # computer:
# #                        ls -al /dev/hidraw*
# #
# # The newly appearing one is the one to choose, e.g. /dev/hidraw1
# #
# # Start MiniMon program with:   ./minimon.py deviceaddr
# #                          e.g. ./minimon.py /dev/hidraw1
# #
# #
# # Depending on permissions settings on your computer, you may may have to start
# # as sudo (root). To overcome this, put a udev rule on your computer by putting
# # into folder '/etc/udev/rules.d' a file named '90-co2mini.rules' with this
# # 3-line content:
# #
# #   ACTION=="remove", GOTO="co2mini_end"
# #   SUBSYSTEMS=="usb", KERNEL=="hidraw*", ATTRS{idVendor}=="04d9", ATTRS{idProduct}=="a052", GROUP="plugdev", MODE="0660", SYMLINK+="co2mini%n", GOTO="co2mini_end"
# #   LABEL="co2mini_end"
# #
# # Then restart your computer or issue the command:
# #                       sudo udevadm control --reload-rules
# #
# # Then unplug and replug your MiniMon-device.
# #
# # This will a) allow the group plugdev (change as appropriate, or put your user
# # into that group) access to the device node and b) symlink the hidraw devices
# # of all connected CO₂ monitors.
# #
# # You will now always find your MiniMon-device at /dev/co2miniN, with N being
# # a number 0, 1, 2, ...
# #
# # The data will be logged to a CSV (Comma Separated Values) file 'minmonlog.csv'
# # in your current directory. If you want a different one, change this in the
# # code (approx line 85ff).
# #
# # A timestamp is added to the data:
# #           2020-06-01 16:08:27     CO2: 502 ppm,   T: 28.04 °C
# #
# #
# # Example output in a normal office setting:
# #    CO2: 501 ppm,  T: 26.29 °C
# #    CO2: 501 ppm,  T: 26.29 °C
# #    CO2: 501 ppm,  T: 26.29 °C
# #    CO2: 502 ppm,  T: 26.29 °C
# #    CO2: 502 ppm,  T: 26.29 °C
# #    CO2: 502 ppm,  T: 26.29 °C
# #
# # after exhaling towards the backside of the MiniMon-device, you may find this
# # output, while the display on the device itself only shows 'Hi' with the
# # red LED on
# #    CO2: 9723 ppm,  T: 26.85 °C
# #    CO2: 9723 ppm,  T: 26.85 °C
# #    CO2: 9723 ppm,  T: 26.85 °C
# #    CO2: 9723 ppm,  T: 26.85 °C
# #    CO2: 9723 ppm,  T: 26.85 °C
# #    CO2: 7824 ppm,  T: 26.85 °C
# #    CO2: 7824 ppm,  T: 26.85 °C
# #    CO2: 7824 ppm,  T: 26.85 °C
# #



# def appendToFile(path, writestring):
#     """Write-Append data; add linefeed"""
#
#     with open(path, 'at', encoding="UTF-8", errors='replace', buffering = 1) as f:
#         f.write((writestring + "\n"))


# if __name__ == "__main__":
#     """if the minimon is called directly without GeigerLog"""

#     ##########################################
#     # Define the full path to your log file
#     logFile = "./minimonlog.csv"
#     ##########################################

#     # Key retrieved from /dev/random, guaranteed to be random ;)
#     key = [0xc4, 0xc6, 0xc0, 0x92, 0x40, 0x23, 0xdc, 0x96]

#     if len(sys.argv) < 2:
#         print("ERROR: you must provide a hidraw device name. Start like:\n"\
#               "\t./gdev_minimon.py /dev/minimon"
#               "\nor\t./gdev_minimon.py /dev/hidraw1"
#              )
#         sys.exit()

#     devname = sys.argv[1]
#     fileHandleMiniMon = open(devname, "a+b",  0)

#     HIDIOCSFEATURE_9 = 0xC0094806
#     set_report3 = b"\x00" + bytearray(key)

#     fcntl.ioctl(fileHandleMiniMon, HIDIOCSFEATURE_9, set_report3)

#     values = {}
#     co2 = temp = humid = float('nan')
#     counter = 0
#     appendToFile(logFile, "#DateTime,              CO2, Temperature")
#     while True:
#         counter += 1
#         #print(counter, " -"*50)

#         data    = list(fileHandleMiniMon.read(8))
#         #print(f"raw data:  ", decList(data))

#         if data[4] != 0x0d:
#             # see: https://github.com/heinemml/CO2Meter/issues/4
#             # some (newer?) devices don't encrypt the data, if byte 4 != 0x0d
#             # assume encrypted data
#             # ??? might result in wrong data sometimes?!!!
#             decrypted = decrypt(key, data)
#         else:
#             decrypted = data

#         if decrypted[4] != 0x0d or (sum(decrypted[:3]) & 0xff) != decrypted[3]:
#             print (hexList(data), " => ", hexList(decrypted),  "Checksum error")

#         else:
#             op  = decrypted[0]
#             val = decrypted[1] << 8 | decrypted[2]

#             values[op] = val
#             #print("values: ", values)

#             # Output all data, mark just received value with asterisk
#             #print( ", ".join( "%s%02X: %04X %5i" % ([" ", "*"][op==k], k, v, v) for (k, v) in sorted(values.items())), "  ",)

#             if 0x50 in values:      co2   = values[0x50]                    # 0x50 = 80
#             if 0x42 in values:      temp  = values[0x42] / 16.0 - 273.15    # 0x42 = 66
#             if 0x41 in values:      humid = values[0x41] / 100.0            # 0x41 = 65 Note: old value 0x44 is wrong! (if no H sensor, then this will be 0

#             logstring = "{:s}, {:5.0f}, {:6.2f}, {:6.2f}".format(stime(), co2, temp, humid)
#             appendToFile(logFile, logstring)
#             print(logstring)


# """
#             key |value| chk  CR
# decrypted:   66  18 175   3  13   0   0   0 #
# decrypted:  109  12 189  54  13   0   0   0
# decrypted:  110  53 251 158  13   0   0   0
# decrypted:  113   2 170  29  13   0   0   0
# decrypted:   80   2 171 253  13   0   0   0 #
# decrypted:   87  31 145   7  13   0   0   0
# decrypted:   86  44  74 204  13   0   0   0
# decrypted:   65   0   0  65  13   0   0   0 #
# decrypted:   67  14  50 131  13   0   0   0
# decrypted:   66  18 175   3  13   0   0   0 #
# decrypted:  109  12 189  54  13   0   0   0
# decrypted:  110  53 251 158  13   0   0   0
# decrypted:  113   2 170  29  13   0   0   0
# decrypted:   80   2 171 253  13   0   0   0 #
# decrypted:   79  33 137 249  13   0   0   0
# decrypted:   82  44  71 197  13   0   0   0
# decrypted:   65   0   0  65  13   0   0   0 #
# decrypted:   67  14  51 132  13   0   0   0
# decrypted:   66  18 175   3  13   0   0   0 #
# decrypted:  109  12 189  54  13   0   0   0
# decrypted:  110  53 251 158  13   0   0   0
# decrypted:  113   2 170  29  13   0   0   0
# decrypted:   80   2 171 253  13   0   0   0 #
# decrypted:   87  31 143   5  13   0   0   0
# decrypted:   86  44  76 206  13   0   0   0
# decrypted:   65   0   0  65  13   0   0   0 #
# decrypted:   67  14  50 131  13   0   0   0
# decrypted:   66  18 175   3  13   0   0   0 #
# decrypted:  109  12 189  54  13   0   0   0
# decrypted:  110  53 251 158  13   0   0   0
# decrypted:  113   2 170  29  13   0   0   0
# decrypted:   80   2 171 253  13   0   0   0 #
# decrypted:   79  33 129 241  13   0   0   0
# decrypted:   82  44  64 190  13   0   0   0
# decrypted:   65   0   0  65  13   0   0   0 #
# decrypted:   67  14  53 134  13   0   0   0
# decrypted:   66  18 175   3  13   0   0   0 #
# decrypted:  109  12 189  54  13   0   0   0
# decrypted:  110  53 251 158  13   0   0   0
# decrypted:  113   2 170  29  13   0   0   0
# decrypted:   80   2 171 253  13   0   0   0 #
# decrypted:   87  31 144   6  13   0   0   0
# decrypted:   86  44  76 206  13   0   0   0
# decrypted:   65   0   0  65  13   0   0   0 #
# decrypted:   67  14  53 134  13   0   0   0
# decrypted:   66  18 175   3  13   0   0   0 #

# raw data:   112 228 238  32 252  70 191  42
# raw data:   170 228 254  32 106  70 191  98
# raw data:   246 228 246  32  14  70 191  66
# raw data:    88 228  78  33  94  70 191 242
# raw data:    91 228  87  33  36  70 191  34
# raw data:    63 228 110  33 137  70 191   2
# raw data:   198 228 102  32 142  70 191   2
# raw data:    62 228  95  32 128  70 191 234
# raw data:    44 228 119  32  90  70 191  74
# raw data:   112 228 238  32 252  70 191  42
# raw data:   170 228 254  32 106  70 191  98
# raw data:   246 228 246  32  14  70 191  66
# raw data:    88 228  78  33  94  70 191 242
# raw data:    91 228  87  33  36  70 191  34
# raw data:    63 228 110  33 137  70 191   2
# raw data:   198 228 102  32 142  70 191   2
# raw data:   246 228  31  32 241  70 191 114
# raw data:   253 228  23  32  91  70 191 218
# raw data:   112 228 238  32 252  70 191  42
# raw data:   170 228 254  32 106  70 191  98
# raw data:   246 228 246  32  14  70 191  66
# raw data:    88 228  78  33  94  70 191 242
# raw data:    83 228  87  33  36  70 191  58
# raw data:    63 228 110  33 137  70 191   2
# raw data:   198 228 102  32 142  70 191   2
# raw data:    22 228  95  32 128  70 191 194
# raw data:    36 228 119  32  90  70 191  66

# """

