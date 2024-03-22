#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Devantech USB-ISS Dongle
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


# lsusb:    - ID 04d8:ffee Microchip Technology, Inc. Devantech USB-ISS
#           - bcdUSB 2.00
# dmesg:    - Product: USB-ISS, Manufacturer: Devantech Ltd., SerialNumber: 00027171

# 2010 put on market:
# from:     https://de.reichel-versand.de/DEV-USB-ISS.shtml
# "Erscheinungsdatum (Datum der letzten technischen Spezifikation): 2010-12-06"
# from:     https://www.robot-electronics.co.uk/htm/usb_iss_tech.htm
# "Testing the USB-ISS: We have a small test program which will let you try out the
# different operating modes of the USB-ISS module. It is written in Visual C# 2010 version.

# Stopping ACM0
# systemctl stop ModemManager.service  not tested
# more: https://community.keyboard.io/t/device-or-resource-busy/451/5


from   gsup_utils       import *


class ISSdongle:
    """Code for the ISS Dongle"""

    name            = "USB-ISS"
    module_id_def   = 0x07                      # the default value
    module_id       = None                      # to be read from dongle; MUST be == 7
    firmware        = None                      # to be read from dongle; (my module == 0x07)
    ISS_mode        = None                      # to be read from dongle; (default == 0x40)
    SerialNumber    = None                      # to be read from dongle; (my module == "00027171")

    DongleSer       = None                      # serial port pointer


    def __init__(self):
        """only class init"""
        pass


    def DongleInit(self):
        """opening the serial port and testing for correct dongle"""

        fncname = "DongleInit: {} ".format(self.name)
        dprint(fncname)
        setIndent(1)

        if gglobs.I2Cusbport   == "auto" : gglobs.I2Cusbport  = None
        if gglobs.I2Cbaudrate  == "auto" : gglobs.I2Cbaudrate = 115200
        if gglobs.I2CtimeoutR  == "auto" : gglobs.I2CtimeoutR = 3
        if gglobs.I2CtimeoutW  == "auto" : gglobs.I2CtimeoutW = 1

        # open serial port
        success, portmsg  = self.ISSOpenPort()
        if not success:
            setIndent(0)
            return False, portmsg

        # 1) set ISS mode
        ModeOptions  = ("H100", "H400", "H1000")        # hardware mode 100 kHz, 400 kHz, 1000 kHz,
        success, msg = self.ISSsetMode(ModeOptions[0])  # set to hardware mode 100 kHz
        if success :
            gdprint(msg)
        else:
            edprint(msg)
            return False, msg

        # 2) get ISS-VERSION
        success, msg = self.ISSgetVersion()
        if success:
            gdprint(msg)
        else:
            edprint(msg)
            return False, msg

        # 3) get serial number
        self.ISSgetSerialNumber()

        setIndent(0)

        return (True,  "Initialized Dongle " + self.name)


    def DongleTerminate(self):
        """Close the I2C serial port and set serial handle to None"""

        fncname = "DongleTerminate: "
        msg     = "Closing Serial Port of Dongle {}".format(self.name)
        try:
            gglobs.I2CDongle.DongleSer.close()
        except Exception as e:
            msg = "Exception " + msg
            exceptPrint(e, msg)

        gglobs.I2CDongle.DongleSer = None # will be renewed on init

        return fncname + msg


    def DongleReset(self):
        """ Reset the ISS dongle """

        return "has no resetting option"


    def DongleIsSensorPresent(self, addr):
        """check a single address for presence of I2C device with address 'addr'"""

        # self.DongleScanPrep("Start")
        response = self.DongleAddrIsUsed(addr)
        # self.DongleScanPrep("End")
        return response


    def DongleScanPrep(self, type):
        """Only the ELV dongle needs a prep"""
        pass


    def DongleAddrIsUsed(self, addr):
        """Scan for presence of a device on the ISS dongle
        using the special Test command 0x58"""

        # Checking for the existence of an I2C device (V5 and later firmware only)
        # I2C_TEST 	Device I2C Address
        # 0x58 	    0xA0   (0xA0 is Example for SHIFTED address! My address would be >>1 => 0x50!!!)
        # This 2 byte command was added to V5 following customer requests. It checks
        # for the ACK response to a devices address. A single byte is returned,
        # zero if no device is detected or non-zero if the device was detected.

        # duration: 0.27 ... 0.39 ms per address

        fncname = "DongleAddrIsUsed: "

        command = b'\x58' + bytes([addr << 1])
        wrt     = self.ISSwriteBytes(command)
        bread   = self.ISSreadBytes(1)

        if    int(bread[0]) == 0:
            # edprint(fncname + "No device detected")
            return False
        else:
            # edprint(fncname + "Found a device")
            return True


    def DongleGetInfo(self):
        """Show the ISS dongle info"""

        spacer = " " * 11
        info   = ""
        info  += spacer + "- Module ID:       0x{:02X}\n"     .format(self.module_id)
        info  += spacer + "- Firmware:        0x{:02X}\n"     .format(self.firmware)
        info  += spacer + "- Operating Mode:  0x{:02X} : {}\n".format(self.ISS_mode, self.ISSgetModeText(self.ISS_mode))
        info  += spacer + "- Serial Number:   {}\n"           .format(self.SerialNumber)

        return info.split("\n")


    def DongleWriteRead(self, addr, register, readbytes, data, addrScheme=1, msg="", wait=0):
        """combines
        def DongleWriteReg(self, addr, register, readbytes, data, addrScheme=1, msg=""):
        def DongleGetData (self, addr, register, readbytes, data, addrScheme=1, msg=""):
        into one, with error checking after write
        wait it wait phase between write and read call
        """

        wrt  = self.DongleWriteReg(addr, register, readbytes, data, addrScheme=addrScheme, msg=msg)
        if wrt == -99:
            # failure in writing
            return []
        else:
            # Write succeeded
            # wait as required
            time.sleep(wait)

            # now get the data
            answ = self.DongleGetData (addr, register, readbytes, data, addrScheme=addrScheme, msg=msg)

            return answ


    def DongleWriteReg(self, addr, register, readbytes, data, addrScheme=1, msg=""):
        """Writes to register of dongle, perhaps with data"""

        # addr     : the 7 bit address of sensor
        # register : sensor internal register address, 1 byte or 2 byte, like 0x00, 0x3345
        # readbytes: number of bytes to read (not relevant here)
        # data     : any data bytes to write as list

        fncname = "   {:15s}: {:15s} ".format("DongleWriteReg", msg)
        # dprint(fncname)

        if    addrScheme == 1:  reglen  = 1
        elif  addrScheme == 2:  reglen  = 2
        else:                   reglen  = 2     # addrScheme == 3

        # write to register with data
        bcmd     = b'\x54'
        bcmd    += bytes([(addr << 1) + 0])     # NOTE: +0 for WRITING to the sensor!
        bcmd    += bytes([reglen + len(data)])  # number of bytes to write
        bcmd    += register.to_bytes(reglen, byteorder='big')
        bcmd    += b"".join(bytes([a]) for a in data)

        wrt      = self.ISSwriteBytes(bcmd, msg=msg)          # wrt  = no of bytes written
        if wrt == -99: return wrt # return on write error

        # ISS sends a single byte return after writing data
        #
        # from: https://www.robot-electronics.co.uk/htm/usb_iss_i2c_tech.htm
        # After all bytes have been received the USB-ISS performs the IC2 write
        # operation out to the SRF08 and sends a single byte back to the PC. This
        # returned byte will be 0x00 (zero) if the write command failed and non-zero
        # if the write succeeded. The PC should wait for this byte to be returned
        # (timing out after 500mS) before proceeding with the next transaction.

        brec = self.ISSreadBytes(1, msg=msg)        # read byte to clean up
        lrec = list(brec)                           # make list of bytes from byte sequence
        if len(brec) == 0:      edprint(fncname + "no return byte")
        cdprint(fncname + "bwrt:{:3n}  {:50s}  bexp:{:2n} brcvd:{:2n} {}".format(wrt, convertB2Hex(bcmd), 1, len(lrec), lrec))

        return wrt


    def DongleGetData(self, addr, register, readbytes, data, addrScheme=1, msg=""):
        """writes init-reading, then reads data"""

        # addr     : the 7 bit address of sensor
        # register : sensor internal register address, 1 byte or 2 byte, like 0x00, 0x3345 (not relevant here)
        # readbytes: number of bytes to read
        # data     : any data bytes to write (not relevant here)

        fncname = "   {:15s}: {:15s} ".format("DongleGetData", msg)
        # dprint(fncname)

        if    addrScheme == 1:  reglen  = 1
        elif  addrScheme == 2:  reglen  = 2
        else:                   reglen  = 2     # addrScheme == 3

        # write init command
        bcmd    = b'\x54'                                           # new starter
        bcmd   += bytes([(addr << 1) + 1])                          # NOTE: +1 for READING from the sensor!
        bcmd   += bytes([readbytes])                                # Bytes-to-Read
        wrt     = self.ISSwriteBytes(bcmd, msg=msg)                 # wrt  = no of bytes written
        if wrt == -99: return []

        # read bytes
        brec = self.ISSreadBytes(readbytes, msg=msg)                # read byte sequence:
        lrec = list(brec)                                           # make list of bytes from byte sequence

        cdprint(fncname + "bwrt:{:3n}  {:50s}  bexp:{:2n} brcvd:{:2n} {}".format(wrt, convertB2Hex(bcmd), readbytes, len(lrec), lrec))

        return lrec

######## Begin ISS specific functions

    def ISSgetVersion(self):
        """get ISS_version consisting of 3 values"""

        # ISS-VERSION will return three bytes.
        #   The first is the Module ID, this will always be 7.
        #   The second byte is the firmware revision number.
        #   The third byte is the current operating mode, ISS_MODE.
        #
        # ISS_MODE is initialized to 0x40 (I2C-S_100KHZ) on power up.
        #
        # CAUTION: Clock stretching limited to HARDWARE Mode!
        # Example:
        #   Send    0x5A, 0x01.
        #   Receive 0x07, 0x02, 0x40.

        fncname = "ISSgetVersion: "
        rdef    = "Dongle {} responded with ".format(self.name)

        # Ergebins: 15.6 second bei 9600 baud setting
        # --> 6410 /sec * 5 bytes = 32k/s => *8 =256k bits/s
        # Ergebins: 15.7 second bei 921600 baud setting
        # dprint("starting")
        # for i in range(100000):
        #     wrt  = gglobs.I2CDongle.DongleSer.write(b'\x5A\x01')     # wrt  = no of bytes written
        #     rec = gglobs.I2CDongle.DongleSer.read(3)
        # dprint("stopped")

        wrt  = self.ISSwriteBytes(b'\x5A\x01')  # ISSgetVersion
        rec  = self.ISSreadBytes(3)

        if len(rec) == 3:
            self.module_id = rec[0]
            self.firmware  = rec[1]
            self.ISS_mode  = rec[2]
            if self.module_id == self.module_id_def:
                # ok
                resp = True, rdef + "proper ID: {}, firmware: {}, mode: 0x{:02X} ({})".format(*rec, self.ISSgetModeText(self.ISS_mode))
            else:
                # bad ID
                resp = False, rdef + "improper ID: {}".format(self.module_id)
        else:
            # bad ISS-VERSION
            resp = False, rdef + "improper ISS-VERSION: {}".format(rec)

        return resp


    def ISSgetModeText(self, modevalue):
        """get the verabl text on set mode"""

        if   modevalue == 0x20:  modemsg = "Software Mode 'I2C_S_20kHz'"
        elif modevalue == 0x30:  modemsg = "Software Mode 'I2C_S_50kHz'"
        elif modevalue == 0x40:  modemsg = "Software Mode 'I2C_S_100kHz'"
        elif modevalue == 0x50:  modemsg = "Software Mode 'I2C_S_400kHz'"
        elif modevalue == 0x60:  modemsg = "Hardware Mode 'I2C_H_100kHz'"
        elif modevalue == 0x70:  modemsg = "Hardware Mode 'I2C_H_400KHZ'"
        elif modevalue == 0x80:  modemsg = "Hardware Mode 'I2C_H_1000KHZ'"
        else:                    modemsg = "Unknown"

        return modemsg


    def ISSsetMode(self, newMode):
        """set ISS mode to I2C mode"""

        # CAUTION !! CAUTION !! CAUTION !! CAUTION !! CAUTION !! CAUTION !!
        # Software mode does NOT support (full) clock streching !!!!
        #
        # Set I2C Mode "hardware" or "software" (default mode is "software")
        # ISS_MODE sets the operating mode. This sets up the modules I/O pins and
        # hardware for the required mode. There are 4 operating modes (I2C, SPI,
        # Serial and I/O) some which can be combined. I2C mode is further broken
        # down into the various fixed frequencies and the use of software (bit bashed)
        # or hardware I2C ports. The full list is:
        # Operating Mode 	Value
        # IO_MODE 	        0x00
        # IO_CHANGE 	    0x10
        # I2C_S_20KHZ 	    0x20
        # I2C_S_50KHZ 	    0x30
        # I2C_S_100KHZ 	    0x40    * 100 kHz software
        # I2C_S_400KHZ  	0x50
        # I2C_H_100KHZ 	    0x60    * 100 kHz hardware
        # I2C_H_400KHZ 	    0x70
        # I2C_H_1000KHZ 	0x80
        # SPI_MODE  	    0x90
        # SERIAL  	        0x01
        # I/O_CHANGE is not really an operating mode. It's used to change the I/O mode
        # between Analogue Input, Digital Input and digital Output without changing
        # Serial or I2C settings.
        # The I2C modes will have I/O on the I/O1 and I/O2 pins. Serial mode will have
        # I/O on the I/O3 and I/O4 pins. I2C and Serial can be combined, for example
        # I2C_S_100KHZ (0x40) + SERIAL (0x01) = 0x41.
        # SPI requires all four I/O pins so there are no other options for this mode.
        #
        #   ISS_CMD 	ISS_MODE 	I2C_MODE 	IO_TYPE (see I/O mode above)
        #   0x5A 	    0x02 	    0x60 	    0x04
        # This example will initialize I2C to 100khz using the hardware I2C peripheral in the PIC chip.
        # ISS_MODE (0x02) is fixed for setting any operating commands. IO_TYPE must be set to 0x04
        #
        # Response Bytes
        #   The response to the mode setting frames is always two bytes.
        #   The first byte is ACKnowledge (0xFF) or NotACKnowledge (0x00).
        #   If you get an ACK then the second byte will be just 0x00.
        #   If you get a NACK then the second byte will be the reason, as follows:
        #   0x05 Unknown Command
        #   0x06 Internal Error 1   }
        #   0x07 Internal Error 2   } you should never see these
        # Under normal circumstances the response will be 0xFF, 0x00

        if   newMode == "S20"     : newModeVal = 0x20   # Set I2C Mode "software" (I2C_S_20KHZ)
        elif newMode == "S50"     : newModeVal = 0x30   # Set I2C Mode "software" (I2C_S_50KHZ)
        elif newMode == "S100"    : newModeVal = 0x40   # Set I2C Mode "software" (I2C_S_100KHZ, default)
        elif newMode == "S400"    : newModeVal = 0x50   # Set I2C Mode "software" (I2C_S_400KHZ)
        elif newMode == "H100"    : newModeVal = 0x60   # Set I2C Mode "hardware 100 kHz"
        elif newMode == "H400"    : newModeVal = 0x70   # Set I2C Mode "hardware 400 kHz"
        elif newMode == "H1000"   : newModeVal = 0x80   # Set I2C Mode "hardware 1000 kHz"                  # failures with many exceptions

        wrt  = self.ISSwriteBytes(b'\x5A\x02' + bytes([newModeVal]) + b'\x04')
        rec  = self.ISSreadBytes(2)

        if rec == b'\xff\x00':  msg = True,  "Dongle {} mode setting was completed successfully".format(self.name)
        else:                   msg = False, "FAILURE dongle {} mode setting, ERROR: {}".format(self.name, rec)

        return msg


    def ISSgetSerialNumber(self):
        """get Serial Number"""

        # GET_SER_NUM will return the modules unique 8 byte USB serial number.
        # Example:
        #   Send 0x5A, 0x03.
        #   Receive 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x31. (that's "00000001")
        # The received serial number will always be ASCII digits in the range "0" to "9" ( 0x30 to 0x39 ).
        wrt  = self.ISSwriteBytes(b'\x5A\x03')
        rec2 = self.ISSreadBytes(8)
        self.SerialNumber = rec2.decode("ASCII")
        gdprint("Dongle {} has Serial Number: {}".format(self.name, self.SerialNumber))



    def ISSwriteBytes(self, writebytes, msg=""):
        """write to the ISS dongle"""

        start   = time.time()
        fncname = "{:15s}: {:15s} ".format("ISSwriteBytes", msg)
        setIndent(1)

        try:
            wrt  = gglobs.I2CDongle.DongleSer.write(writebytes)     # wrt  = no of bytes written
        except Exception as e:
            exceptPrint(fncname + str(e), "")
            wrt  = -99

        duration = (time.time() - start ) * 1000
        # cdprint(fncname + "bwrt:{:3d}  {:50s}  dur:{:0.3f} ms".format(wrt, convertB2Hex(writebytes), duration))

        setIndent(0)
        return wrt


    def ISSreadBytes(self, bytecount, msg=""):
        """read from the dongle"""

        start = time.time()
        fncname = "{:15s}: {:15s} ".format("ISSreadBytes", msg)
        setIndent(1)

        try:
            rec = gglobs.I2CDongle.DongleSer.read(bytecount)
            while True:
                wcount = gglobs.I2CDongle.DongleSer.in_waiting
                if wcount == 0: break
                # print(fncname + "wcount: ", wcount, ", bytecount: ", bytecount)
                rec += gglobs.I2CDongle.DongleSer.read(wcount)
                time.sleep(0.005)

        except Exception as e:
            msg = fncname + "Exception Failure reading ISS bytes"
            exceptPrint(e, msg)
            rec = []

        duration = (time.time() - start ) * 1000
        # cdprint(fncname + "bexp:{:3d}  {:50s}  dur:{:0.3f} ms".format(bytecount, convertB2Hex(rec), duration))

        setIndent(0)
        return rec  # return rec as bytes sequence


    def ISSOpenPort(self):
        """open serial port for dongle"""

        # for USB-ISS all serial port settings are ignored except portname, which on Linux is "/dev/ttyACMx"
        #
        # is next responsible for the slow termination? 15 sec to drain?
        #
        # from: https://chromium.googlesource.com/chromiumos/third_party/kernel/+/refs/heads/0.11.257.B/drivers/usb/class/cdc-acm.c
        # blob: a98e388933401e583fac1537b0286e0bfee5e104
        #
        # /*
        # * cdc-acm.c
        # * USB Abstract Control Model driver for USB modems and ISDN adapters
        # * Sponsored by SuSE
        # ...
        # */
        # #define ACM_CLOSE_TIMEOUT	15	/* seconds to let writes drain */
        # ...
        #


        ## local ###################################################################################
        def lcl_ISS_getSerialPortBaud(device):
            """
            gets the USB-to-Serial port name and baudrate for ISS
            This tests for a match of USB's vid + pid associated with device. If match found,
            then it tests for proper communication checking with specific call/answers
            """

            # output by: lsusb
            # ISS I2C dongle
            #   bcdUSB               2.00
            #   idVendor           0x04d8 Microchip Technology, Inc.
            #   idProduct          0xffee Devantech USB-ISS
            #   iManufacturer           1
            #   iProduct                2
            #   iSerial                 3

            fncname   = "ISSOpenPort - lcl_ISS_getSerialPortBaud: "

            dprint(fncname + "for device '{}'".format(device))
            setIndent(1)

            portfound   = None
            baudfound   = None
            tmplt_match = "Found Chip ID match for '{}' at: Port:'{}' - vid:0x{:04x}, pid:0x{:04x}"
            tmplt_found = "Found: Port:{}, Baud:{}, description:{}, vid:0x{:04x}, pid:0x{:04x}"

            ports = getPortList(symlinks=False)

            for port in ports:
                if  port.vid == 0x04D8 and port.pid == 0xFFEE:
                    gdprint(fncname, tmplt_match.format(device, port.device, port.vid, port.pid))
                    baudrate = lcl_ISSautoBaudrate(port.device)
                    if baudrate is not None and baudrate > 0:
                        portfound = port.device
                        baudfound = baudrate
                        break

            if portfound is not None: gdprint(fncname + tmplt_found.format(portfound, baudfound, port.description, port.vid, port.pid), " - Returning:", (portfound, baudfound))
            else:                     rdprint(fncname + tmplt_found.format(portfound, baudfound, "", 0, 0), " - Returning:", (portfound, baudfound))

            setIndent(0)
            return (portfound, baudfound)


        def lcl_ISSautoBaudrate(usbport):
            """Tries to find a proper baudrate by testing for successful serial communication """

            """
            NOTE: the device port can be opened without error at any baudrate, even
            when no communication can be done, e.g. due to wrong baudrate. Therefore we
            test for successful communication by checking for the return string
            containing expected sequence.
            On success, this baudrate will be returned. A baudrate=0 will be returned
            when all communication fails. On a serial error, baudrate=None will be returned.
            """

            fncname = "lcl_ISSautoBaudrate: "

            dprint(fncname + "on port: '{}'".format(usbport))
            setIndent(1)

            baudrates = gglobs.I2Cbaudrates
            baudrates.sort(reverse=True)                # to start with highest baudrate
            for baudrate in baudrates:
                dprint(fncname + "Trying baudrate: ", baudrate)
                try:
                    with serial.Serial(usbport, baudrate, timeout=0.5, write_timeout=0.5) as ABRser:
                        bwrt = ABRser.write(b'\x5A\x01')
                        brec = ABRser.read(3)
                        # cdprint("---------------------" + fncname + "brec: ", brec)
                        while True:
                            time.sleep(0.05)
                            cnt = ABRser.in_waiting
                            if cnt == 0: break
                            brec += ABRser.read(cnt)

                    if len(brec) == 3 and brec[0] == self.module_id_def:
                        baudmsg = "SUCCESS with baudrate: {}".format(baudrate)
                        gdprint("Dongle {} responded with proper ID: {}".format(gglobs.I2CDongleCode, self.module_id_def))
                        gglobs.I2CDeviceDetected = "USB-ISS"
                        break
                    else:
                        msg = "Dongle {} responded with improper ID".format(gglobs.I2CDongleCode)

                except Exception as e:
                    exceptPrint(e, "")
                    baudmsg  = "EXCEPTION in Serial communication with baudrate: {}".format(baudrate)
                    baudrate = None         # serial error
                    break

                baudmsg  = "FAILURE - No success at any baudrate"
                baudrate = 0    # all communication failed

            dprint(fncname + baudmsg)
            setIndent(0)

            return baudrate

        ## end local ##################################################################################


        fncname = "ISSOpenPort: "

        if gglobs.I2Cusbport == None:
            # auto-find port and baud
            port, baud = lcl_ISS_getSerialPortBaud("ISS")   # try to get both port and baud
            if port is None or baud is None:
                return (False,  "A {} dongle was not detected".format(self.name))
            else:
                gglobs.I2Cusbport  = port
                gglobs.I2Cbaudrate = baud
                msg = "A dongle {} was detected at port: {} and baudrate: {}".\
                        format(self.name, gglobs.I2Cusbport, gglobs.I2Cbaudrate)
            fprint(msg)
            dprint(msg)

        else:
            # in non-None mode take the configured value
            msg = "A dongle {} was <b>user configured</b> for port: {}".format(self.name, gglobs.I2Cusbport)

            fprint(msg)
            dprint(msg)

            # it could be the wrong port! check for proper communication
            newbaudrate = lcl_ISSautoBaudrate(gglobs.I2Cusbport)
            if newbaudrate == 0 or newbaudrate is None:
                setIndent(0)
                return False, "Could not find a device"


        portmsg = "Port:{}".format(gglobs.I2Cusbport)
        msg     = "not set"
        repeats = 0
        lstart  = time.time()
        while True:
            if repeats > 20:
                tmsg = (False,  "Port is busy for too long. Giving up.")
                break

            try:
                gglobs.I2CDongle.DongleSer = serial.Serial(gglobs.I2Cusbport)
                gglobs.I2CDongle.DongleSer.flushInput() # helful?
                msg = "Serial Device opened at {}".format(portmsg)
                gdprint(fncname + msg)
                tmsg = (True, msg)
                break

            except OSError as e:
                edprint(fncname + "OSError: ERRNO:{} ERRtext:'{}'".format(e.errno, e.strerror))
                repeats += 1
                if e.errno == 2:
                    # port is missing
                    msg = "Serial Port {} not available".format(gglobs.I2Cusbport)
                    tmsg = (False,  msg)
                    break

                elif e.errno == 16:
                    # port is busy; may last > 16sec
                    msg  = "Serial Port {} is busy. Please, wait up to 20 sec.".format(gglobs.I2Cusbport) + " time: {:0.0f} sec".format(time.time() - lstart)
                    if repeats == 0: efprint(msg)
                    else:            qefprint(msg)
                    QtUpdate()
                    tmsg = (False, msg)
                    time.sleep(2)

                else:
                    # what else there may be
                    msg  = "Serial Port {} could not be opened.".format(gglobs.I2Cusbport) + " time: {:0.0f} sec".format(time.time() - lstart)
                    if repeats == 0: efprint(msg)
                    else:            qefprint(msg)
                    QtUpdate()
                    tmsg = (False, msg)
                    time.sleep(1)

            except Exception as e:
                msg = "Serial Port for dongle {} at {} could not be opened".format(self.name, portmsg)
                exceptPrint(e, fncname + "ERROR " + msg)
                tmsg = (False,  msg)
                break

        fprint(msg)
        dprint(tmsg)
        cdprint(fncname + "Exiting with msg: ", tmsg)
        return tmsg

