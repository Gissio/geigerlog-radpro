#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
IO-Warrior24 Dongle (IOW24-DG)
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


# from Code Mercenaries: https://www.codemercs.com/de/dongles/iow24dg
# Download code from:    https://www.codemercs.com/de/download
# For Linux use:         https://www.codemercs.com/downloads/iowarrior/IO-Warrior_SDK_linux.zip
#                        and follow the install instructions for libiowkit-1.X
#
# currently using:       IO-Warrior Dynamic Library V1.5 for Windows, 22. Jul 2016
#
# find iowarrior in file system:
# $ find /lib/modules/$(uname -r) -type f -name 'iow*.ko'
# --> /lib/modules/4.15.0-142-generic/kernel/drivers/usb/misc/iowarrior.ko


import ctypes
from   gsup_utils       import *

#
# begin iow declarations -------------------------------------
#
iowkit                                  = None                  # to hold the DLL if the lib was found

# Max number of IOW devices in system = 16
IOWKIT_MAX_DEVICES                      = ctypes.c_ulong(16)

# Max number of pipes per IOW device = 2
IOWKIT_MAX_PIPES                        = ctypes.c_ulong(2)

# pipe names
IOW_PIPE_IO_PINS                        = ctypes.c_ulong(0)
IOW_PIPE_SPECIAL_MODE                   = ctypes.c_ulong(1) # use for I2C

# IO-Warrior vendor & product IDs
IOWKIT_VENDOR_ID                        = 0x07c0
# IO-Warrior 40
IOWKIT_PRODUCT_ID_IOW40                 = 0x1500
# IO-Warrior 24
IOWKIT_PRODUCT_ID_IOW24                 = 0x1501    # used with GeigerLog
IOWKIT_PRODUCT_ID_IOW24_SENSI           = 0x158A
# IO-Warrior PowerVampire
IOWKIT_PRODUCT_ID_IOWPV1                = 0x1511
IOWKIT_PRODUCT_ID_IOWPV2                = 0x1512
# IO-Warrior 56
IOWKIT_PRODUCT_ID_IOW56                 = 0x1503
IOWKIT_PRODUCT_ID_IOW56_ALPHA           = 0x158B

# IOW Legacy devices open modes
IOW_OPEN_SIMPLE                         = ctypes.c_ulong(1)
IOW_OPEN_COMPLEX                        = ctypes.c_ulong(2)

IOWKIT_IO_REPORT                        = ctypes.c_ubyte * 5
IOWKIT_SPECIAL_REPORT                   = ctypes.c_ubyte * 8
IOWKIT56_IO_REPORT                      = ctypes.c_ubyte * 8
IOWKIT56_SPECIAL_REPORT                 = ctypes.c_ubyte * 64
#
# end iowkit declarations -------------------------------------



class IOWdongle:
    """Code for the IO-Warrior24 Dongle"""

    name         = "IOW24-DG"
    readtimeout  = 500    # ms
    writetimeout = 500    # ms  - not implemented in lib for Linux


    def __init__(self):
        """only class init"""
        pass


    def DongleInit(self):
        """opening the USB port and checking for dongle"""

        global IOWKIT_SPECIAL_REPORT, iowkit


        def getIowSetting(text, ret, *args):
            """returns string with Info"""

            sarg = "".join("{:16s} ".format(str(arg)) for arg in args)
            info = "{:30s}: {:5s} {:15s}".format(text, str(ret), sarg)
            return info


        fncname = "DongleInit: {} ".format(self.name)
        dprint(fncname)
        # setIndent(1) # tto many returns following

        if 'linux' not in sys.platform:             # Py3:'linux', Py2:'linux2'
            return (False,  "This dongle is currently supported only on Linux.")

        # find driver: 'libiowkit.so.1'
        import ctypes.util
        iowlib = ctypes.util.find_library("iowkit") # must NOT use prefix (lib), suffix (.so, .so.1, ...)
        cdprint("   " + fncname + "{:30s}: {}".format("Found Library: ", iowlib))
        if iowlib is None:
            msg  = "Cannot find the driver for this dongle.\n"
            msg += "Is the 'iowarrior' driver installed?"
            return (False,  msg)


        # Loading the library:
        # iowkit = ctypes.CDLL("libiowkit.so")          # works ok,  libiowkit.so        is linked to libiowkit.so.1.0.5
        # iowkit = ctypes.CDLL("libiowkit.so.1")        # works ok,  libiowkit.so.1      is linked to libiowkit.so.1.0.5
        # iowkit = ctypes.CDLL("libiowkit.so.1.0.5")    # works ok,  libiowkit.so.1.0.5  is shared library
        iowkit = ctypes.CDLL(iowlib)                    # works ok
        # edprint("iowkit", iowkit)


        #
        # make iowkit settings -----------------------------------------
        # (what part of this is really needed?)
        #
        # IOWKIT_HANDLE IOWKIT_API IowKitOpenDevice(void);
        iowkit.IowKitOpenDevice.argtypes        = None
        iowkit.IowKitOpenDevice.restype         = ctypes.c_voidp

        # void IOWKIT_API IowKitCloseDevice(IOWKIT_HANDLE devHandle); # devhandle ignored
        # void IOWKIT_API IowKitCloseDevice(void);    # allowed also; compare with open
        iowkit.IowKitCloseDevice.argtypes       = None
        iowkit.IowKitCloseDevice.restype        = None

        # IOWKIT_HANDLE IOWKIT_API IowKitGetDeviceHandle(ULONG numDevice);
        iowkit.IowKitGetDeviceHandle.argtypes   = [ctypes.c_ulong]  # numDev = 1 ... 16
        iowkit.IowKitGetDeviceHandle.restype    = ctypes.c_voidp

        # ULONG IOWKIT_API IowKitGetNumDevs(void);
        iowkit.IowKitGetNumDevs.argtypes        = None
        iowkit.IowKitGetNumDevs.restype         = ctypes.c_ulong    # Py default

        # PCHAR IOWKIT_API IowKitVersion(void);
        # res like: IO-Warrior Kit V1.5
        iowkit.IowKitVersion.argtypes           = None
        iowkit.IowKitVersion.restype            = ctypes.c_char_p

        # ULONG IOWKIT_API IowKitProductId(IOWKIT_HANDLE iowHandle);
        # res like: 0x1501
        iowkit.IowKitGetProductId.argtypes      = [ctypes.c_voidp]
        iowkit.IowKitGetProductId.restype       = ctypes.c_ulong    # Py default

        # ULONG IOWKIT_API IowKitGetRevision(IOWKIT_HANDLE iowHandle);
        # res like: 0x1030
        iowkit.IowKitGetRevision.argtypes       = [ctypes.c_voidp]
        iowkit.IowKitGetRevision.restype        = ctypes.c_ulong    # Py default

        # BOOL IOWKIT_API IowKitSetTimeout(IOWKIT_HANDLE devHandle, ULONG timeout);
        iowkit.IowKitSetTimeout.argtypes        = [ctypes.c_voidp, ctypes.c_ulong]
        iowkit.IowKitSetTimeout.restype         = ctypes.c_bool

        # BOOL IOWKIT_API IowKitSetWriteTimeout(IOWKIT_HANDLE devHandle, ULONG timeout);
        iowkit.IowKitSetWriteTimeout.argtypes   = [ctypes.c_voidp, ctypes.c_ulong]
        iowkit.IowKitSetWriteTimeout.restype    = ctypes.c_bool

        # ULONG IOWKIT_API IowKitWrite(IOWKIT_HANDLE devHandle, ULONG self.numPipe, PCHAR buffer, ULONG length);
        iowkit.IowKitWrite.argtypes             = [ctypes.c_voidp, ctypes.c_ulong, ctypes.c_voidp, ctypes.c_ulong]
        iowkit.IowKitWrite.restype              = ctypes.c_ulong    # Py default

        # ULONG IOWKIT_API IowKitRead(IOWKIT_HANDLE devHandle, ULONG self.numPipe, PCHAR buffer, ULONG length);
        iowkit.IowKitRead.argtypes              = [ctypes.c_voidp, ctypes.c_ulong, ctypes.c_voidp, ctypes.c_ulong]
        iowkit.IowKitRead.restype               = ctypes.c_ulong    # Py default

        # BOOL IOWKIT_API IowKitReadImmediate(IOWKIT_HANDLE devHandle, PDWORD value);
        # Return current value directly read from the IO-Warrior I/O pins.
        # not relevant for I2C
        iowkit.IowKitReadImmediate.argtypes     = [ctypes.c_voidp, ctypes.POINTER(ctypes.c_ulong)]
        iowkit.IowKitReadImmediate.restype      = ctypes.c_bool

        # BOOL IOWKIT_API IowKitGetSerialNumber(IOWKIT_HANDLE iowHandle, PWCHAR serialNumber);
        # from iowkit.h:
        # typedef unsigned short *       PWCHAR;
        # from library docu:
        # "The serial number is represented as an Unicode string. The buffer pointed to
        # by serialNumber must be big enough to hold 9 Unicode characters (18 bytes),
        # because the string is terminated in the usual C way with a 0 character."
        #
        # Originally suggested code fails:
        # iowkit.IowKitGetSerialNumber.argtypes  = [ctypes.c_voidp, ctypes.c_wchar_p]
        # It results in Python crashing on conversion of c_wchar_p, probably because
        # the implicit conversion of Python3 expects 4 bytes per unicode char, while
        # the iowlibrary uses only 2.
        # Workaround is a string buffer of length 18 and the conversion is per
        # buffer.raw.decode("utf-8")
        #
        # From the manual: I O W 2 4 - D G
        # Serial numbers are 8 digit hexadecimal numbers.

        iowkit.IowKitGetSerialNumber.argtypes   = [ctypes.c_voidp, ctypes.c_voidp] # ok
        iowkit.IowKitGetSerialNumber.restype    = ctypes.c_bool


        # Open device and get handle self.iow
        # can this fail?
        try:
            self.iow = iowkit.IowKitOpenDevice()
        except Exception as e:
            exceptPrint(e, "iowkit.IowKitOpenDevice")
            self.iow = None

        if self.iow is None:                                               # must check for None, not 0 (zero)
            # return (False,  "No such dongle detected on USB bus")
            return (False,  "A '{}' dongle was not detected".format(self.name))



        setIndent(1)

        # set Read Timeout
        ito = iowkit.IowKitSetTimeout(self.iow, self.readtimeout)
        cdprint(fncname + getIowSetting("IowKitSetTimeout", ito, self.readtimeout, "ms" ))

        # set Write Timeout
        iwto = iowkit.IowKitSetWriteTimeout(self.iow, self.writetimeout)
        cdprint(fncname + getIowSetting("IowKitSetWriteTimeout", iwto, self.writetimeout, "ms - not implemented on Linux" ))

        self.emptyReport = IOWKIT_SPECIAL_REPORT(0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00)
        self.reportSize  = ctypes.sizeof(self.emptyReport)
        cdprint(fncname + getIowSetting("Size of Report", "----", self.reportSize, "0x{:02X}".format(self.reportSize)))

        self.numPipe     = IOW_PIPE_SPECIAL_MODE
        cdprint(fncname + getIowSetting("Pipe Number", "----", self.numPipe.value, "0x{:02X}".format(self.numPipe.value)))

        # Set IOWarrior to I2C mode
        cdprint(fncname + self.IOWsetModeI2C())

        setIndent(0)
        portmsg = "USB"
        return True,  "Initialized Dongle " + self.name


    def DongleTerminate(self):
        """ Close the I2C IOW dongle - has no meaning on IOW"""

        fncname = "DongleTerminate: "
        msg = "Terminating dongle {}".format(self.name)
        return fncname + msg


    def DongleReset(self):
        """Reset the IOW dongle - not defined"""

        return "DongleReset:  Resetting '{}' not available".format(self.name)


    def DongleGetInfo(self):
        """get user relevant info"""


        def getDeviceName (pid):
            """returns name of Device"""
            if   pid == IOWKIT_PRODUCT_ID_IOW24: itype = "24"
            elif pid == IOWKIT_PRODUCT_ID_IOW40: itype = "40"
            elif pid == IOWKIT_PRODUCT_ID_IOW56: itype = "56"
            else:                                itype = " (unknown)"
            return "IO-Warrior{}".format(itype)

        info = ""

        # Get Product
        pid = iowkit.IowKitGetProductId(self.iow)
        info += "{:30s}{}\n".format("- Product:", getDeviceName(pid))

        # Get Kit Version
        ikv = iowkit.IowKitVersion()
        info += "{:30s}{}\n".format("- Version of IOW Kit:", ikv.decode("UTF-8"))

        # Get Firmware Revision
        rev = iowkit.IowKitGetRevision(self.iow)
        info += "{:30s}{}\n".format("- Firmware Version:", hex(rev))

        # Get number of IOWs
        numdevs = iowkit.IowKitGetNumDevs()
        info += "{:30s}{}\n".format("- Count of connected dongles:", numdevs)

        # Get Serial number
        bsno  = ctypes.create_string_buffer(18)     # seesm ok, or are 19 needed for C "\x00" termination?
        isn   = iowkit.IowKitGetSerialNumber(self.iow, ctypes.byref(bsno))
        # Manual: Serial numbers are 8 digit hexadecimal numbers. ( and 2-byte unicode chars!)
        bsno = bsno[:16] # cuto off extra chars
        info += "{:30s}{}\n".format("- SerialNumber of dongle:", bsno.decode("utf-16"))

        ### not needed as user info
        # # Get individual handle
        # igdh = iowkit.IowKitGetDeviceHandle(1)  # device #1
        # info += "{:30s}{}\n".format("- IowKitGetDeviceHandle:", igdh)

        return info.split("\n")


    def DongleIsSensorPresent(self, addr):
        """check a single address for presence of I2C device with address 'addr'"""

        # self.DongleScanPrep("Start")
        response = self.DongleAddrIsUsed(addr)
        # self.DongleScanPrep("End")

        return response


    def DongleScanPrep(self, type):
        """Only the ELV dongle needs this prep"""
        pass


    def DongleAddrIsUsed(self, addr):
        # Write to Sensor at addr with empty data and read 1 byte
        # check if ACK is set or not

        # duration IOW: 6.6 ... 8.0 ms per address (with or without IOW printing)

        start   = time.time()
        fncname = "DongleAddrIsUsed: addr: 0x{:02X}: ".format(addr)

        rbytes   = 1
        register = 0x00
        data     = []
        try:
            self.IOWwriteData(addr, register, data)
            ret, rep = self.IOWreadData(rbytes)
        except Exception as e:
            exceptPrint(e, fncname)

        if rep[0] == 2:                             # is Acknowledge Report
            if rep[1] & 0x80:   check = "NoACK"     # error bit is set; Addr is NOT used
            else:               check = "ACK"       # ok; Addr is used
        else:
            check = "wrong report ID"               # has happened, do what?

        duration = 1000 * (time.time() - start)
        # edprint(fncname + "result: {}  dur: {:0.2f}".format(check, duration))

        if check == "ACK": return True
        else:              return False


    def DongleWriteRead(self, addr, register, readbytes, data, addrScheme=1, msg="", wait=0):
        """combines
        def DongleWriteReg(self, addr, register, readbytes, data, addrScheme=1, msg=""):
        def DongleGetData (self, addr, register, readbytes, data, addrScheme=1, msg=""):
        into one, with error checking after write
        wait it wait phase between write and read call
        """

        # write the data to the register
        wrt  = self.DongleWriteReg(addr, register, readbytes, data, addrScheme=addrScheme, msg=msg)

        if wrt == -99:
            # failure in writing
            return []
        else:
            # Write succeeded
            # wait as required
            time.sleep(wait)

            # testwait
            time.sleep(0.001)

            # now get the data
            answ = self.DongleGetData (addr, register, readbytes, data, addrScheme=addrScheme, msg=msg)

            return answ



    def DongleWriteReg(self, addr, register, readbytes, data, addrScheme=1, msg=""):
        """Writes to register of dongle, perhaps with data"""

        # addr     : the 7 bit address of sensor
        # register : sensor internal register address, 1 byte or 2 byte, like 0x00, 0x3345
        # readbytes: number of bytes to read (not relevant here)
        # data     : any data bytes to write as list of byte values like: [0, 0, 7]
        # command  : LM75 on dongle ELV:   b'S 91 02 P'       # prepare to read 2 bytes from previously set Temp register (=0x00)

        fncname = "   {:15s}: {:15s} ".format("DongleWriteReg", msg)
        cdprint(fncname, " addr:{:02X} reg:{:04X}  data:{}".format(addr, register, data))

        setIndent(1)
        wrt = self.IOWwriteData(addr, register, data, addrScheme=addrScheme, msg=msg)

        # "Any write transactions are acknowledged by a report via interrupt-in endpoint 2"
        # must read the report, or it interferes with data reading!
        ret, rep = self.IOWreadData(0, msg=msg)

        setIndent(0)

        return wrt


    def DongleGetData(self, addr, register, readbytes, data, addrScheme=1, msg=""):
        """Write to Sensor to set for reading, and read until error free Acknowledge
        received, but give up and return with [] after 3 retries
        return: list of values like: [1, 144, 76]"""

        fncname = "   {:15s}: {:15s} ".format("DongleGetData", msg)

        # no read required; return empty list
        if readbytes == 0:
            playWav("err")
            rdprint(fncname + "readbytes == 0")
            return []

        cdprint(fncname, " addr:{:02X} readbytes:{}".format(addr, readbytes))
        setIndent(1)

        # init the read
        gglobs.I2CDongle.IOWInitRead(addr, readbytes, msg=msg)

        # a single report has space for only 6 bytes.
        # when more are needed, repeat reading reports until you have all bytes
        sumrep          = []
        bytes_received  = 0
        repcounts       = 0    # count of repeats on errors
        loop            = 0
        while readbytes > bytes_received:

            # testwait
            time.sleep(0.001)

            loop += 1
            # do the read
            ret, rep = self.IOWreadData(readbytes, msg=msg)
            if rep[0] == 3:
                if rep[1] & 0x80:       # error bit is set
                    edprint(fncname + "Error Bit set - Repeating Read in loop: #", loop)
                    repcounts += 1
                else:
                    sumrep += rep[2:]
                    bytes_received += 6
            else:
                # sometimes repID==2 is found; loop until correct (helpful?)
                edprint(fncname + "--------------- Wrong reportID - got:#{:02X}, expected #03 - Repeating Read in loop: #{}".format(rep[0], loop))
                repcounts += 1

            # if repcounts > 3: return []  # if more than 3 errors return []
            if repcounts > 3:
                sumrep = []
                break

        answ  = sumrep[:readbytes]      # reports give multiple of 6 bytes; take only as many a called for
        cdprint(fncname + "Answer:  ", convertB2Hex(answ))

        setIndent(0)

        return answ


    def IOWwriteData(self, addr, register, data, addrScheme=1, msg=""):
        """ Writing to the sensor """

        start = time.time()
        fncname = "   {:12s}: {:15s} ".format("IOWwriteData", msg)

        if    addrScheme == 1:  reglen  = 1
        elif  addrScheme == 2:  reglen  = 2
        else:                   reglen  = 2     # addrScheme == 3

        addr8 = addr << 1 + 0                                       # set write address:     LM75: 7bit:0x48 -> 8bit:0x90
        lreg  = list(register.to_bytes(reglen, byteorder='big'))    # if addrscheme==2: change 16 bit register to list of  2x 8 bit bytes
        wdata = lreg + data

        wdlen = len(wdata)
        # print("wdlen:", wdlen, ", wdata: ", wdata)

        if wdlen <= 5:
            # all data fit into one single report
            ikw, report = self.IOWwriteReport([addr8] + wdata, start=True, stop=True)
            cdprint("{:15s} ikw:{} report#2: {}".format(fncname, ikw, self.IOWgetReportAsText(report)))


        else:
            # more data than fit into a single report
            ######################################################################################
            ##  NOT TESTED - as no sensor needs more than 5 data !!!!!!!!!!
            ######################################################################################
            #            IOW name    xX   time   reqB   wrt/rec   info     rec
            pTemplate = "IOW {:9s} {:2s} {:10s} [{:3d}] [{:3d}]  {:20s} == {}"

            # first batch of data; with Generate Start, no Generate Stop
            pointer = 5
            data = [addr8] + wdata[:pointer]
            ikw, report = self.IOWwriteReport(data, start=True, stop=False)
            # print(self.pTemplate.format(name, "TX", stime()[11:], wdlen + 1, ikw, info, self.IOWgetReportAsText(report)))

            # next batches without Start, without Stop; leave enough for one last report with Stop=True
            while pointer + 6 < wdlen:
                data = wdata[pointer:pointer+6]
                #print("pointer, data:", pointer, data)
                ikw, report = self.IOWwriteReport(data, start=False, stop=False)
                print(self.pTemplate.format(name, "TX", stime()[11:], wdlen + 1, ikw, info, self.IOWgetReportAsText(report)))
                pointer += 6

            # lastbatch with Stop
            data = wdata[pointer:]
            #print("pointer, last batch:", pointer, data)
            ikw, report = self.IOWwriteReport(data, start=False, stop=True)

        duration = 1000 * (time.time() - start)
        # edprint(fncname + "dur: {:0.1f}".format(duration))

        return ikw


    def IOWwriteReport(self, wdata, start=True, stop=True, addrScheme=1, msg=""):
        """report ID = 2   write a single report """

        start = time.time()
        fncname = "   {:12s}: {:15s} ".format("IOWwriteReport", msg)

        lenwdata = len(wdata)
        if lenwdata  > 6:
            cdprint(fncname + "Programming ERROR in IOWwriteReport: Can't write more than 6 bytes in single report!")
            sys.exit()

        flags             = 0x00
        if start:   flags = flags | 0x80        # sets highest bit      Start
        if stop:    flags = flags | 0x40        # sets 2nd highest bit  Stop    --> 0x80 + 0x40 = 0xC0
        flags             = flags | lenwdata    # lowest 3 bits         count of data 0 ... 6 (not 7!)
        # print("start, stop, flags: ", start, stop, hex(flags), bin(flags))

        data     = wdata + [0x00, 0x00, 0x00, 0x00, 0x00, 0x00] # use only the first 6 items to construct report
        # print(fncname + "data:", data)

        report = IOWKIT_SPECIAL_REPORT(
                                        0x02,       # report ID = 2
                                        flags,      # flags: e.g. C3:  Start, Stop and 3 bytes data (1 byte address plus 2 more bytes)
                                                    # flags: e.g. 06:  No Start, No Stop and 6 bytes data, no address
                                                    # flags: e.g. 84:  Start, No Stop and 4 bytes data, including address
                                                    # flags: e.g. 46:  No Start, Stop and 6 bytes data, no address
                                                    # flags contains the following bits:
                                                    # 7 - Generate Start
                                                    # 6 - Generate Stop
                                                    # 5 - unused, write zero
                                                    # 4 - unused, write zero
                                                    # 3 - unused, write zero
                                                    # 2 - data count MSB
                                                    # 1 - data count
                                                    # 0 - data count LSB
                                        data[0],    # data
                                        data[1],    # data
                                        data[2],    # data
                                        data[3],    # data
                                        data[4],    # data
                                        data[5],    # data
                                      )

        ikw = iowkit.IowKitWrite(self.iow, self.numPipe, ctypes.byref(report), self.reportSize)

        duration = 1000 * (time.time() - start)
        # edprint(fncname + "dur: {:0.1f}".format(duration))

        return ikw, report


    def IOWreadData(self, rbytes, addrScheme=1, msg=""):
        """ Read max of 6 bytes from sensor """

        start = time.time()
        fncname = "   {:12s}: {:15s} ".format("IOWreadData", msg)

        # get an empty report; it'll be filled by the IowKitRead read
        report = copy.copy(self.emptyReport)
        ikr    = iowkit.IowKitRead(self.iow, self.numPipe, ctypes.byref(report), self.reportSize)

        duration = 1000 * (time.time() - start)
        cdprint("{:15s} ikr:{} report#?: {}  dur:{:0.3f}".format(fncname, ikr, self.IOWgetReportAsText(report), duration))

        return ikr, report


    def IOWInitRead(self, addr, count, addrScheme=1, msg=""):
        """report ID = 3  Setup Sensor with 7bit address addr for Read of count bytes"""

        global IOWKIT_SPECIAL_REPORT, iowkit

        start   = time.time()
        fncname = "   {:12s}: {:15s} ".format("IOWInitRead", msg)

        addr8  = (addr << 1) + 1               # LM75: 7bit:0x48 -> 8bit:0x91
        report = IOWKIT_SPECIAL_REPORT(
                                        0x03,  # report ID = 3
                                        count, # count: (=number of bytes to be read from the sensor)
                                        addr8, # command:  sensor read address
                                        0x00,  # set to zero
                                        0x00,  # set to zero
                                        0x00,  # set to zero
                                        0x00,  # set to zero
                                        0x00,  # set to zero
                                      )

        ikw = iowkit.IowKitWrite(self.iow, self.numPipe, ctypes.byref(report), self.reportSize)

        duration = 1000 * (time.time() - start)
        cdprint("{:15s} ikw:{} report#2: {}".format(fncname, ikw, self.IOWgetReportAsText(report)))


    def IOWsetModeI2C(self):
        """report ID = 1:  sets IOW to I2C mode"""

        global IOWKIT_SPECIAL_REPORT, iowkit

        fncname = "IOWsetModeI2C"

        report = IOWKIT_SPECIAL_REPORT(
                                        0x01, # report ID = 1
                                        0x01, # enable I2C mode
                                        0x00, # all flags 0 (Bit 7   - Disable Pull Ups (1 = disable) - IOW24 only (for 3.3V operation)
                                              #              Bit 6   - Use Sensibus Protocol (1 = enable)
                                              #              Bit 5:0 - unused, write zero
                                        0x00, # max timeout of 256x500 microsec (=0.128 sec)
                                        0x00, # must be zero
                                        0x00, # must be zero
                                        0x00, # must be zero
                                        0x00, # must be zero
                                      )

        ikw = iowkit.IowKitWrite(self.iow, self.numPipe, ctypes.byref(report), self.reportSize)

        return "{:30s}: ikw:{} report: {}".format(fncname, ikw, self.IOWgetReportAsText(report))


    def IOWgetReportAsText (self, report):
        """return report array as string"""

        return "".join("%02X " % r for r in report)

