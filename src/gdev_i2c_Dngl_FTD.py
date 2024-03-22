#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Adafruit FTDI232H Dongle
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

# Adafruit FT232H Breakout - General Purpose USB to GPIO, SPI, I2C - USB C & Stemma QT -- Product ID: 2264
# webpage:      https://www.adafruit.com/product/2264
# pinout:       https://learn.adafruit.com/circuitpython-on-any-computer-with-ft232h/pinouts
# lsusb:        0x0403:0x6014 Future Technology Devices International, Ltd FT232H Single HS USB-UART/FIFO IC
#               bcdUSB 2.00
# dmesg:        ftdi_sio 3-11:1.0: FTDI USB Serial Device converter detected


import pyftdi
import pyftdi.i2c

from   gsup_utils       import *


class FTDdongle:
    """Code for the FTD Dongle: Adafruit FT232H """

    name            = "Adafruit FT232H"
    module_id_def   = None                      # the default value
    module_id       = None                      # to be read from dongle; MUST be == 7
    firmware        = None                      # to be read from dongle; (my module == 0x07)
    ISS_mode        = None                      # to be read from dongle; (default == 0x40)
    SerialNumber    = None                      # to be read from dongle; (my module == "00027171")

    DongleHndl      = None


    def __init__(self):
        """only class init"""
        pass


    def DongleInit(self):
        """opening the serial port and testing for correct dongle"""

        fncname = "DongleInit: {} ".format(self.name)
        dprint(fncname)
        setIndent(1)

        # Instantiate an I2C controller
        self.DongleHndl = pyftdi.i2c.I2cController()

        # Configure the first interface (IF/1) of the FTDI device as an I2C master
        try:
            self.DongleHndl.configure('ftdi://ftdi:232h/1', clockstretching=True)
        except Exception as e:
            msg = "Dongle not found"
            exceptPrint(e, msg)
            return (False,  msg)

        cdprint("is configured:   ", self.DongleHndl.configured)
        cdprint("direction:       ", self.DongleHndl.direction)
        cdprint("gpio_pins:       ", self.DongleHndl.gpio_pins)
        cdprint("gpio_all_pins:   ", self.DongleHndl.gpio_all_pins)
        cdprint("frequency:       ", self.DongleHndl.frequency)
        cdprint("frequency_max:   ", self.DongleHndl.frequency_max)
        # rdprint("poll 0x75:     ", self.DongleHndl.poll(0x75, write=False, relax=True))
        # rdprint("poll 0x76:     ", self.DongleHndl.poll(0x76, write=False, relax=True))
        # rdprint("poll 0x77:     ", self.DongleHndl.poll(0x77, write=False, relax=True))
        # rdprint("poll 0x78:     ", self.DongleHndl.poll(0x78, write=False, relax=True))

        setIndent(0)

        return (True,  "Initialized Dongle " + self.name)


    def DongleTerminate(self):
        """Close the FTDI interface."""

        # close(freeze=False)
        # Close the FTDI interface.
        # Parameters
        # freeze (bool) – if set, FTDI port is not reset to its default state on close.
        # Return type: None

        fncname = "DongleTerminate: "
        msg     = "Closing the FTDI Interface of Dongle {}".format(self.name)
        self.DongleHndl.close()

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
        """Scan for presence of a device on the dongle"""

        # Dongle Scan for all devices ??? ms per address, ??? sec overall

        start = time.time()
        fncname = "DongleAddrIsUsed: "

        for i in range(1):
            try:
                # using the dongle itself with  clockstretching=True
                bread = self.DongleHndl.poll(addr, write=True,  relax=True)             # found all except SCD30
                # bread = self.DongleHndl.poll(addr, write=False, relax=True)             #  alles und immer False
                # bread = self.DongleHndl.poll(addr, write=True, relax=False)             # found all except SCD30
                # bread = self.DongleHndl.poll(addr, write=False, relax=False)            # found non-existing 0x49, missing SCD30

                # using the dongle itself with  clockstretching=False
                # bread = self.DongleHndl.poll(addr, write=True,  relax=True)             # found all except SCD30
                # bread = self.DongleHndl.poll(addr, write=False, relax=True)             #  alles und immer False
                # bread = self.DongleHndl.poll(addr, write=True, relax=False)             # found all except SCD30
                # bread = self.DongleHndl.poll(addr, write=False, relax=False)            # found non-existing 0x49, missing SCD30, and SCD41

                # using the attached sensors
                # shndl = self.DongleHndl.get_port(addr)  # always returns a port handle, no matter whether a device exists
                # gdprint("slave addr reported: ", hex(shndl.address))  # war stets ok

                # polling
                # bread = shndl.poll(write=False, relax=True, start=True)           # finds non-existing syensors and misses existing, changes from run to run
                # bread = shndl.poll(write=False, relax=False, start=True)          # alles und immer False
                # bread = shndl.poll(write=False, relax=False, start=False)         # alles und immer True
                # bread = shndl.poll(write=False, relax=True, start=False)          # alles und immer True

                # bread = shndl.poll(write=True, relax=True, start=True)            # alles und immer False
                # bread = shndl.poll(write=True, relax=False, start=False)          # alles und immer True
                # bread = shndl.poll(write=True, relax=False, start=True)           # alles und immer False
                # bread = shndl.poll(write=True, relax=True, start=False)           # alles und immer True

                # reading
                # bread = shndl.read(readlen=1, relax=True, start=True)             # alles und immer False; only NACK responses

                # writing
                # bread = shndl.write(b"\x00", relax=True, start=True)              # only NACK responses
                # bread = shndl.write(b"\xff", relax=True, start=True)              # all sensors recognized except SCD30
                # bread = shndl.write_to(0, b"\xff", relax=True, start=True)        # all sensors recognized except SCD30 and SCD41

                # other
                # bread= self.DongleHndl.validate_address(addr)                     # always returns None

                # bread = True
            except Exception as e:
                exceptPrint(e, "slave.write")
                bread = False


            # rdprint("addr: ", hex(addr), ",  bread: ", bread)

        duration2 = 1000 * (time.time() - start)
        cdprint(fncname + "addr: 0x{:02X}  present:{}  dur:{:0.2f} ms".format(addr, bread, duration2))

        return bread


    def DongleGetInfo(self):
        """Show the ISS dongle info"""

        info = ""
        info += "- Name:            {}\n"               .format(self.name)
        info += "- Bus frequency:   {}\n"               .format(self.DongleHndl.frequency)

        return info.split("\n")


    def DongleWriteRead(self, addr, register, readbytes, data, addrScheme=1, msg="", wait=0):
        """combines
        def DongleWriteReg(self, addr, register, readbytes, data, addrScheme=1, msg=""):
        def DongleGetData (self, addr, register, readbytes, data, addrScheme=1, msg=""):
        into one, with error checking after write
        wait it wait phase between write and read call
        """

        wrt       = self.DongleWriteReg(addr, register, readbytes, data, addrScheme=addrScheme, msg=msg)
        if wrt == -99:
            # failure in writing
            return []
        else:
            # get the data after a wait, and only if the Write succeeded
            time.sleep(wait)
            return self.DongleGetData (addr, register, readbytes, data, addrScheme=addrScheme, msg=msg)


    def DongleWriteReg(self, addr, register, readbytes, data, addrScheme=1, msg=""):
        """Writes to register of dongle, perhaps with data"""

        # addr     : the 7 bit address of sensor
        # register : sensor internal register address, 1 byte or 2 byte, like 0x00, 0x3345
        # readbytes: number of bytes to read (not relevant here)
        # data     : any data bytes to write as list

        start = time.time()

        fncname = "   {:15s}: {:15s} ".format("DongleWriteReg", msg)
        # dprint(fncname)

        if    addrScheme == 1:  reglen  = 1
        elif  addrScheme == 2:  reglen  = 2
        else:                   reglen  = 2

        bcmd  = register.to_bytes(reglen, byteorder='big')
        bcmd += b"".join(bytes([a]) for a in data)
        # print("bcmd: ", bcmd)
        lbcmd = list(bcmd)
        # print("lbcmd: ", lbcmd)
        try:
            # shndl = self.DongleHndl.get_port(addr)
            # bread = shndl.write(bcmd, relax=True, start=True)                         # only NACK responses
            # bread = shndl.write(lbcmd, relax=False, start=False)                      # only NACK responses
            # bread = shndl.exchange(out=lbcmd, readlen=readbytes, relax=True, start=True) # only NACK responses
            # bread = shndl.write_to(register, out=data, relax=True, start=True)          # cannot handle 2 byte registers! EXCEPTION: 'ubyte format requires 0 <= number <= 255' in file: 'gdev_i2c_Dngl_FTDI.py' in line 222

            self.DongleHndl.write(addr, lbcmd, relax=True)                              # always NACK response on SCD30; ok on LM75
                                                                                        # EXCEPTION: 'NACK from slave' i2c.write on Reset of TSL2591

            # bread = self.DongleHndl.read(addr, readlen=readbytes, relax=True)
            # print("bread: ", bread)

            success = True
        except Exception as e:
            exceptPrint(e, "i2c.write")
            success = False

        duration = 1000 * (time.time() - start)
        cdprint(fncname + "duration: ", duration)
        cdprint(fncname + "success:{:6s}  {:50s}  ".format(str(success), convertB2Hex(bcmd)))

        return success


    def DongleGetData(self, addr, register, readbytes, data, addrScheme=1, msg=""):
        """writes init-reading, then reads data"""

        # addr     : the 7 bit address of sensor
        # register : sensor internal register address, 1 byte or 2 byte, like 0x00, 0x3345
        # readbytes: number of bytes to read (not relevant here)
        # data     : any data bytes to write
        # command  : LM75: ELV!   b'S 91 02 P'       # prepare to read 2 bytes from previously set Temp register (=0x00)

        fncname = "   {:15s}: {:15s} ".format("DongleGetData", msg)
        # dprint(fncname)

        # read bytes
        try:
            brec = self.DongleHndl.read(addr, readlen=readbytes, relax=True)
            lrec = list(brec)                                           # make list of bytes from byte sequence
            success = True
        except Exception as e:
            exceptPrint(e, "i2c.read")
            lrec = []
            success = False

        cdprint(fncname + "bwrt:{:6s}  {:50s}  bexp:{:2n} brcvd:{:2n} {}".format(str(success), "no cmd", readbytes, len(lrec), lrec))

        return lrec

