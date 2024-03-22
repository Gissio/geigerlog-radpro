#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
ELV USB-I2C Dongle
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


from   gsup_utils       import *


class ELVdongle:
    """Code for the ELV USB-I2C Dongle"""

    name            = "ELV USB-I2C"

    # Serial port
    DongleSer       = None                      # serial port pointer

    def __init__(self):
        """make instance of dongle"""
        pass


    def DongleInit(self):
        """opening the serial port and testing for correct dongle"""

        fncname = "DongleInit: {}: ".format(self.name)

        dprint(fncname)
        setIndent(1)

        if gglobs.I2Cusbport   == "auto" : gglobs.I2Cusbport  = None    # None results in auto-find of port
        if gglobs.I2Cbaudrate  == "auto" : gglobs.I2Cbaudrate = 115200  # baudrate tested ok: 230400, 460800
        if gglobs.I2CtimeoutR  == "auto" : gglobs.I2CtimeoutR = 3
        if gglobs.I2CtimeoutW  == "auto" : gglobs.I2CtimeoutW = 1

        # open serial port
        success, portmsg = self.ELVOpenPort()
        if not success:
            setIndent(0)
            return False, portmsg

        # set dongle defaults
        cdprint(fncname + "Setting dongle defaults")
        wrt = self.ELVwriteBytes(b'<')     # stop macro with '<' (Should be default)
        wrt = self.ELVwriteBytes(b'y30')   # set 'y30' in order to NOT get ACK and NACK (is default)

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

        gglobs.I2CDongle.DongleSer = None # will be renewed on next init

        return fncname + msg


    def DongleReset(self, type="Factory"):
        """Reset the ELV dongle"""

        # returns: Factory: b'\r\nFull Init...'   (14 bytes) # takes ~7.2 ms
        #          else:    b'\r\nReset...'       (10 bytes) # takes ~6.9 ms
        # HOWEVER: this is followed in both commands by:
        #             b'\r\nELV USB-I2C-Interface v1.8 (Cal:5E)\r\n'
        # but it takes seconds before this second part is sent by the ELV device.
        # If another command is issued in that time, it interferes with that new
        # command!
        # The total duration on my system is:
        #                   ZAA Factory Reset:  takes 3.25 sec
        #                   Z4B Reset:          takes 1.80 sec

        start   = time.time()
        fncname = "DongleReset: "
        gdprint(fncname + "type: ", type)

        if      type == "Factory": code = b"ZAA"    # 1.) Setzt alle Einstellungen auf den Auslieferungszustand zurück.
                                                    # 2.) Löscht den Makrospeicher.
                                                    # 3.) Führt einen Reset aus.
        else:                      code = b"Z4B"    # Führt sofort einen Reset aus (alle Einstellungen bleiben).

        wrt  = self.ELVwriteBytes(code)
        brec = self.ELVreadBytes(10)                # brec: b'\r\nELV USB-I2C-Interface v1.8 (Cal:5E)\r\n00 \r\n'

        time.sleep(1)                               # 1 sec wait allows both reset types to complete within 3 sec timeout

        while True and (time.time() - start) < 5:
            wbrec = self.ELVreadBytes(10)           # wbrec: b'\r\nELV USB-I2C-Interface v1.8 (Cal:5E)\r\n00 \r\n'
            # cdprint(fncname + "while loop, wbrec: ", wbrec)
            if b"ELV" in wbrec:
                brec += wbrec
                break

        duration = 1000 * (time.time() - start)

        return str(brec) + "  Total dur: {:0.1f} ms".format(duration)


    def DongleGetInfo(self):
        """get the ELV's startup info"""

        # get ELV info:
        #   - send b'?'
        #   - read approx. 179 bytes:
        #           b'\r\nELV USB-I2C-Interface v1.8 (Cal:5E)
        #             \r\nLast Adress:0xC5
        #             \r\nBaudrate:115200 bit/s
        #             \r\nI2C-Clock:99632 Hz
        #             \r\nY00
        #             \r\nY10
        #             \r\nY20
        #             \r\nY30
        #             \r\nY40
        #             \r\nY50
        #             \r\nY60
        #             \r\nY70
        #             \r\n'

        wrt  = self.ELVwriteBytes(b'?')
        brec = self.ELVreadBytes(100)
        srec = (brec.strip().decode()).replace("\r", "")

        info = []
        for line in srec.split("\n"):
            info.append("           - {}".format(line))

        return info


    def DongleScanPrep(self, type):
        """Only the ELV dongle needs this prep done before any scans!
        NOTE its use in gdev_i2c !
        type = "Start" or "END"
        """

        fncname = "DongleScanPrep: "

        if    type == "Start": code = b'y31'
        else:                  code = b'y30'
        wrt = self.ELVwriteBytes(code)


    def DongleIsSensorPresent(self, addr):
        """check a single address for presence of I2C device with address 'addr'"""
        # only ELV needs the DongleScanPrep!

        self.DongleScanPrep("Start")
        response = self.DongleAddrIsUsed(addr)
        self.DongleScanPrep("End")

        return response


    def DongleAddrIsUsed(self, addr):
        """Check for presence of I2C device with address 'addr'"""
        # use when checking multiple addr in a row
        # write Start-Addr-Stop and check for ACK or NACK

        fncname   = "DongleAddrIsUsed: "

        readbytes = 1
        saddr     = "{:02X}".format((addr << 1) + 0)                      # note: +0!
        bcommand  = bytes('S {} P'.format(saddr), 'ASCII')
        wrt       = self.ELVwriteBytes(bcommand)
        answ      = self.ELVreadBytes(readbytes)

        msg = fncname + "command: {:12s}  addr: 0x{:02X}  answ: {}".format(str(bcommand), addr, answ)

        if   answ == b"N":  # NACK
            rdprint(msg)
            return False

        elif answ == b"K":  # ACK
            cdprint(msg)
            return True

        else:               # crap, like:  b'', b'\r\nnot recognized', ...
            edprint(msg)
            return False


    def DongleWriteRead(self, addr, register, readbytes, data, addrScheme=1, msg="", wait=0):
        """combines
        def DongleWriteReg(self, addr, register, readbytes, data, addrScheme=1, msg=""):
        def DongleGetData (self, addr, register, readbytes, data, addrScheme=1, msg=""):
        into one, with error checking after write
        wait it wait phase between write and read call
        """

        wrt = self.DongleWriteReg(addr, register, readbytes, data, addrScheme=addrScheme, msg=msg)
        if wrt == -99:
            # failure in writing
            return []
        else:
            # get the data after a wait, and only if the Write succeeded
            time.sleep(wait)
            return self.DongleGetData (addr, register, readbytes, data, addrScheme=addrScheme, msg=msg)


    def DongleWriteReg(self, addr, register, readbytes, data, addrScheme=1, msg=""):
        """Writes to register of dongle, perhaps with data"""

        fncname = "   {:15s}: {:15s} ".format("DongleWriteReg", msg)
        # dprint(fncname)

        # write to register with data (if there are any)
        saddr       = "{:02X}".format((addr << 1) + 0)                      # NOTE: +0!
        sreg        = "{:02X}".format(register)
        if addrScheme == 1: sreg        = "{:02X}".format(register)
        else:               sreg        = "{:04X}".format(register)         # if reg is 0x0123 then the zero is not shown unless :04X is chosen!
        sdata       = "".join("%02X " % d for d in data)
        bcommand    = bytes('S {} {} {} P'.format(saddr, sreg, sdata), 'ASCII')
        wrt         = self.ELVwriteBytes(bcommand)

        cdprint(fncname + "wrt:{:2n}  {:45s} expect readbytes: {}".format(wrt, str(bcommand), readbytes))

        return wrt


    def DongleGetData(self, addr, register, readbytes, data, addrScheme=1, msg=""):
        """writes inits reading, then reads data
        return: list of int values
        """

        fncname = "   {:15s}: {:15s} ".format("DongleGetData", msg)
        # dprint(fncname)

        if readbytes == 0: return []

        # read init command (doesn't use register!)
        saddr       = "{:02X}".format((addr << 1) + 1)                      # read address, note: +1!
        sreadbytes  = "{:02X}".format(readbytes)                            # no of bytes to read
        bcommand    = bytes('S {} {} P'.format(saddr, sreadbytes), 'ASCII')
        wrt         = self.ELVwriteBytes(bcommand)

        # read bytes
        brec        = self.ELVreadBytes(readbytes)     # besser weniger als zuviel --- read byte sequence:  3 chars per byte('FF ') + 2 (CR + LF)
        srec        = brec.strip().decode()
        # cdprint(fncname + "wrt:{:2n}  {:45s} bexp:{:2n} brcvd:{:2n} srec: {}".format(wrt, str(brec), readbytes, len(brec), srec))

        # check for Err messages
        if  "Exception"         in srec or  \
            "Err"               in srec or  \
            "Buffer"            in srec or  \
            "Solve"             in srec or  \
            "USB-I2C-Interface" in srec:
            edprint(fncname + "ELV ERROR message in byterec: " + str(brec))
            return []

        else:
            # convert string to list of int values
            srecs = srec.split(" ")
            if len(srecs) == 0: lrec = []
            else:               lrec = [int(x, 16) for x in srec.split(" ")]
            cdprint(fncname + "wrt:{:2n}  {:45s} brcvd: {}".format(wrt, str(bcommand), brec))
            return lrec


    def ELVwriteBytes(self, writebytes, msg=""):
        """write to the ELV dongle"""

        fncname = "   {:15s}: {:15s} ".format("ELVwriteBytes", msg)

        # start = time.time()
        try:
            wrt  = gglobs.I2CDongle.DongleSer.write(writebytes)  # wrt  = no of bytes written
        except Exception as e:
            exceptPrint(e, fncname)
            wrt  = -99

        # duration = (time.time() - start ) * 1000
        # dprint(fncname + "wrt:{:2d}  {}, dur:{:0.3f} ms".format(wrt, writebytes, duration))

        return wrt


    def ELVreadBytes(self, bytecount, msg=""):
        """read from the dongle"""

        fncname = "   {:15s}: {:15s} ".format("ELVreadBytes", msg)

        # start = time.time()
        try:
            rec = gglobs.I2CDongle.DongleSer.read(bytecount)
            # dprint("ELVreadBytes:  bytecount: ", bytecount, ", rec: ", rec)

            while True:
                wcount = gglobs.I2CDongle.DongleSer.in_waiting
                # print("wcount: ", wcount, ", bytecount: ", bytecount)
                if wcount == 0: break
                rec += gglobs.I2CDongle.DongleSer.read(wcount)
                time.sleep(0.005)

        except Exception as e:
            exceptPrint(e, fncname)
            rec = "ELVreadBytes Exception Failure"

        # duration = (time.time() - start ) * 1000
        # dprint(fncname + "bytecount: {:2d}, rec:{}, dur:{:0.1f} ms".format(bytecount, rec, duration))

        return rec  # return bytes sequence


    # not used anywhere
    def ELVgetMacro(self):
        """ Print the Macrocode in the memory """

        wrt  = self.ELVwriteBytes(b'U')
        rec  = self.ELVreadBytes(255+26)

        return rec


    def ELVOpenPort(self):
        """open serial port for ELV dongle"""
        # on Linux this is a "/dev/ttyUSB*" port


        ## local ###################################################################################
        def lcl_ELV_getSerialPortBaud(device):
            """
            gets the USB-to-Serial port name and baudrate for ISS
            This tests for a match of USB's vid + pid associated with device. If match found,
            then it tests for proper communication checking with specific call/answers
            """

            # output by: lsusb
            # ELV I2C dongle
            #   bcdUSB               1.10
            #   idVendor           0x10c4 Cygnal Integrated Products, Inc.
            #   idProduct          0xea60 CP210x UART Bridge / myAVR mySmartUSB light
            #   iManufacturer           1 Silicon Labs
            #   iProduct                2 ELV USB-I2C-Interface
            #   iSerial                 3 TL4E6D5KBAHDFQF0

            fncname   = "ELVOpenPort - lcl_ELV_getSerialPortBaud: "

            dprint(fncname + "for device '{}'".format(device))
            setIndent(1)

            portfound   = None
            baudfound   = None
            tmplt_match = "Found Chip ID match for device '{}' at Port:'{}' - vid:0x{:04x}, pid:0x{:04x}"
            tmplt_found = "Found: Port:{}, Baud:{}, description:'{}', vid:0x{:04x}, pid:0x{:04x}"

            ports = getPortList(symlinks=False)

            for port in ports:
                if  port.vid == 0x10C4 and port.pid == 0xEA60:
                    gdprint(fncname, tmplt_match.format(device, port.device, port.vid, port.pid))
                    baudrate = lcl_ELVautoBaudrate(port.device)
                    if baudrate is not None and baudrate > 0:
                        portfound = port.device
                        baudfound = baudrate
                        break

            if portfound is not None: gdprint(fncname + tmplt_found.format(portfound, baudfound, port.description, port.vid, port.pid))
            else:                     rdprint(fncname + tmplt_found.format(portfound, baudfound, "", 0, 0))
            # edprint(fncname + "Returning: ", (portfound, baudfound))

            setIndent(0)
            return (portfound, baudfound)


        def lcl_ELVautoBaudrate(usbport):
            """Tries to find a proper baudrate by testing for successful serial
            communication at up to all possible baudrates, beginning with the
            highest"""

            """
            NOTE: the device port can be opened without error at any baudrate, even
            when no communication can be done, e.g. due to wrong baudrate. Therefore we
            test for successful communication by checking for the return string
            containing 'ELV'.
            On success, this baudrate will be returned. A baudrate=0 will be returned
            when all communication fails. On a serial error, baudrate=None will be returned.
            """

            fncname = "lcl_ELVautoBaudrate: "

            dprint(fncname + "on port: '{}'".format(usbport))
            setIndent(1)

            baudrates = gglobs.I2Cbaudrates
            baudrates.sort(reverse=True)                # to start with highest baudrate
            for baudrate in baudrates:
                dprint(fncname + "Trying baudrate: ", baudrate)
                try:
                    ABRser = serial.Serial(usbport, baudrate, timeout=0.5, write_timeout=0.5)
                    ABRser.write(b'?')
                    # expect rec:     b'\r\nELV USB-I2C-Interface v1.8 (Cal:5E)\r\nLast Adress:0x91\r\nBaudrate:115200 bit/s\r\n
                    # (approx 179 b)    I2C-Clock:99632 Hz\r\nY00\r\nY10\r\nY20\r\nY30\r\nY40\r\nY50\r\nY60\r\nY70\r\n'
                    rec = ABRser.read(100)  # normally 179 bytes
                    while True:
                        time.sleep(0.05)
                        try:
                            cnt = ABRser.in_waiting
                            ABRser.read(cnt)
                        except Exception as e:
                            exceptPrint(e, fncname + "ABRser.in_waiting Exception at dongle: {}".format(gglobs.I2CDongleCode))
                            cnt = 0
                        if cnt == 0: break

                    ABRser.close()

                    # raise Exception("testing")

                    if b"ELV" in rec:
                        baudmsg = "SUCCESS with baudrate: {}".format(baudrate)
                        gglobs.I2CDeviceDetected = "ELV USB-I2C"
                        break

                except Exception as e:
                    exceptPrint(e, "")
                    baudmsg  = "EXCEPTION in Serial communication with baudrate: {}".format(baudrate)
                    baudrate = None
                    break

                baudmsg  = "FAILURE - No success at any baudrate"
                baudrate = 0

            dprint(fncname + baudmsg)
            setIndent(0)

            return baudrate

        ## end local ##################################################################################


        fncname = "ELVOpenPort: "

        if gglobs.I2Cusbport == None:

            # try to auto-find port and baud
            port, baud = lcl_ELV_getSerialPortBaud("ELV")
            if port is None or baud is None:
                return (False,  "A '{}' dongle was not detected".format(self.name))

            else:
                gglobs.I2Cusbport  = port
                gglobs.I2Cbaudrate = baud
                msg = "A {} dongle was detected at port: {} and baudrate: {}".format(self.name, gglobs.I2Cusbport, gglobs.I2Cbaudrate)
                fprint(msg)
                dprint(msg)

        else:

            # in non-auto mode take the configured value for port and baud,
            # but do check for proper communication
            newbaudrate = lcl_ELVautoBaudrate(gglobs.I2Cusbport)
            if newbaudrate == 0 or newbaudrate is None:
                setIndent(0)
                return False, "Could not find a device"

        portmsg = "Port:'{}' Baud:{} TimeoutR:{}s TimeoutW:{}s"\
                    .format(gglobs.I2Cusbport, gglobs.I2Cbaudrate, gglobs.I2CtimeoutR, gglobs.I2CtimeoutW)

        if os.path.exists(gglobs.I2Cusbport):
            try:
                gglobs.I2CDongle.DongleSer = serial.Serial\
                    (gglobs.I2Cusbport, gglobs.I2Cbaudrate, timeout=gglobs.I2CtimeoutR, write_timeout=gglobs.I2CtimeoutW)
                # gglobs.I2CDongle.DongleSer.flushInput() # helful?

                msg = "Serial device opened at {}".format(portmsg)
                gdprint(fncname + msg)
                return (True,  portmsg)

            except Exception as e:
                exceptPrint(e, fncname + "ERROR Serial port for dongle {} could not be opened".format(self.name))
                errmsg = "A '{}' dongle was not detected at:\n{}".format(self.name, portmsg)
                return (False,  errmsg)
        else:
            errmsg  = "The USB port '{}' does NOT exist.".format(gglobs.I2Cusbport)
            dprint(fncname + errmsg)
            return (False,  errmsg)

