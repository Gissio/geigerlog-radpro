#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
I2C sensor module GDK101 - PIN Diode as Radiation sensor
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

# Reference: http://allsmartlab.com/eng/294-2/
# I2C Maximum Speed is 100 kHz.
# Document: AN_GDK101_V1.1_I2C.pdf
#   Gamma sensor module GDK101, www.ftlab.co.kr
#   Revision:       1.1
#   Last-Updated:   22/3/2021
#   Author:         FTLAB
# Document: GDK101datasheet_v1.6.pdf
#   GDK101 ver1.6 Gamma Radiation Sensor Module
#   DS_GDK101_016, www.ftlab.co.kr, 0000564592100ETF8210, June 28, 2016

##
## CAUTION: it looks like the GDK101 does need a 5V supply! At 3.3V it appears to
## be working, but count rate comes out as way too high!
##


class SensorGDK101:
    """Code for the SmartFTLab GDK101 sensor"""

    addr       = 0x18       # Default option for the GDK101; all options: 0x18, 0x19, 0x1A, 0x1B
    name       = "GDK101"
    firmware   = "not set"  # my device: "0.6" (??? sollte 1.6 sein???)


    def __init__(self, addr):
        """Init SensorGDK101 class"""

        self.addr       = addr


    def SensorInit(self):
        """Scan for presence, do, Reset, get Firmware"""

        fncname = "SensorInit: " + self.name + ": "
        dmsg    = "Sensor {:8s} at address 0x{:02X}".format(self.name, self.addr)

        dprint(fncname)
        setIndent(1)

        # check for presence of an I2C device at I2C address
        # takes ~0.6 ms
        # start = time.time()
        presence = gglobs.I2CDongle.DongleIsSensorPresent(self.addr)
        # dur = 1000 * (time.time() - start)
        # edprint(fncname + "dur: ", dur)

        if not presence:
            # no device found
            setIndent(0)
            msg = "Did not find any I2C device at address 0x{:02X}".format(self.addr)
            edprint(fncname + msg)
            return  False, msg
        else:
            # device found
            gdprint("Found an I2C device at address 0x{:02X}".format(self.addr))


        # soft reset
        dprint(fncname + "Sensor Reset")
        gdprint(self.SensorReset())

        ## get status
        dprint(fncname + "Get Status")
        gdprint(self.GDK101getStatus())

        ## get firmware version
        dprint(fncname + "Get Firmware")
        gdprint(self.GDK101getFirmwareVersion())

        setIndent(0)

        return (True,  "Initialized " + dmsg)


    def GDK101getStatus(self):
        """get Status Power and Vibration"""

        # Read the status of power and vibration
        # CMD   Description                 Read Data 1             Read Data 2
        # 0xB0  Read the status of          0 - Power On ~ 10sec    0 - Not detect vibrations
        #       measurement and vibration   1 - 10sec to 10min      1 - Detect vibrations
        #                                   2 - after 10 min

        # Duration:
        # ISS: GDK101getStatus: duration: 1.5 ms
        # ELV: GDK101getStatus: duration:

        start   = time.time()
        fncname = "GDK101getStatus: "
        dprint(fncname)

        tmsg      = "Status"
        register  = 0xB0
        readbytes = 2
        data      = []
        wait      = 0   #0.01 # sec
        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg, wait=wait)

        if len(answ) == readbytes:
            # ok
            status = "{} - {}".format(answ[0], answ[1])
        else:
            # FAILURE
            status = "FAILURE reading Status"
            edprint(fncname + status + ", reponse: ", answ)

        duration = (time.time() - start) * 1000
        msg = fncname + "got status: {}  in: {:0.1f} ms".format(status, duration)

        return msg


    def GDK101getFirmwareVersion(self):
        """get the Firmware Version as Major.Minor"""

        # Read firmware version
        # CMD   Description             Read Data 1         Read Data 2
        # 0xB4  Read Firmware Version   Main of version     Sub of version

        # Duration:
        # ISS: GDK101getFirmwareVersion: duration: 1.4 ms
        # ELV: GDK101getFirmwareVersion: duration:

        start     = time.time()
        fncname   = "GDK101getFirmwareVersion: "
        dprint(fncname)

        tmsg      = "FirmWr"
        register  = 0xB4
        readbytes = 2
        data      = []
        wait      = 0   #0.01
        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg, wait=wait)

        if len(answ) == readbytes:
            # ok
            self.firmware = "{}.{}".format(answ[0], answ[1])
        else:
            # FAILURE
            self.firmware = "Failure reading Firmware"
            edprint(fncname + self.firmware + ", reponse: ", answ)

        duration = (time.time() - start) * 1000
        msg = fncname + "got firmware: {}  in: {:0.1f} ms".format(self.firmware, duration)

        return msg


    def GDK101getMeasuringTime(self):
        """get the Measuring Time in minutes"""

        # Read Measuring Time
        # CMD   Description             Read Data 1         Read Data 2
        # 0xB1  Read Measuring Time     Minutes of time     Seconds of time

        # Duration:
        # ISS: GDK101getMeasuringTime: duration: 1.8 ms
        # ELV: GDK101getMeasuringTime: duration:

        start     = time.time()
        fncname   = "GDK101getMeasuringTime: "
        dprint(fncname)

        tmsg      = "mtime"
        register  = 0xB1        # Read measuring time
        readbytes = 2
        data      = []
        wait      = 0   #0.01
        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg, wait=wait)
        edprint(fncname + "answ: ", answ)

        if len(answ) == readbytes:
            value = (answ[0] * 60 + answ[1]) / 60                       # (minutes * 60 + seconds) / 60 ==> minutes
            msg   = fncname + "{}:{:6.2f}".format(tmsg, value)
            bmsg  = True, msg
            value = (round(value, 5))
        else:
            msg   = fncname + "Failure reading proper byte count"
            bmsg  = False, msg
            value = gglobs.NAN

        duration = (time.time() - start) * 1000
        pmsg     = msg + "  dur:{:0.2f} ms".format(duration)
        if bmsg[0]:  gdprint(pmsg)
        else:        edprint(pmsg)

        return value


    def SensorReset(self):
        """Soft Reset GDK101 sensor"""

        # Reset
        # CMD   Description             Read Data 1         Read Data 2
        # 0xA0  Reset                   0 - Fail            Not used
        #                               1 - Pass
        # NOTE: it is hard to believe that there is a return value sent by the device
        # after it received a RESET command! I don't get one.
        #
        # Duration:
        # ISS: SensorReset:    duration: 1003 ms
        # ELV: SensorReset:    duration:

        start   = time.time()
        fncname = "SensorReset: " + self.name + ": "
        dprint(fncname)

        tmsg      = "Reset"
        register  = 0xA0
        readbytes = 2
        data      = []
        wrt       = gglobs.I2CDongle.DongleWriteReg(self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)
        # time.sleep(2)
        answ      = gglobs.I2CDongle.DongleGetData(self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)

        # wait      = 2
        # answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg, wait=wait)
        edprint(fncname + "answ: ", answ)

        duration = 1000 * (time.time() - start)

        return fncname + "took {:0.1f} ms".format(duration)


    def SensorgetValues(self):
        """Read the count rate values for 1 and 10 min"""
        # NOTE: count rates are reported as µSv/h values,
        #       converted here to CPM with Sensitivity
        #       value of 8.33 CPM/(µSv/h) instead of official value of 12!

        # Read Measured Value 10 min
        # CMD   Description                 Read Data 1         Read Data 2
        # 0xB2  Read Measured Value         Integer of value    Decimal of value
        #       (10min avg. 1min update)
        #
        # Duration:
        # ISS: SensorgetValues: 10 min    duration: 4.2 ms
        # ELV: SensorgetValues: 10 min    duration:
        #
        # Read Measured Value 1 min
        # CMD   Description                 Read Data 1         Read Data 2
        # 0xB3  Read Measured Value         Integer of value    Decimal of value
        #       (1min avg. 1min update)
        #
        #
        # Duration:
        # ISS: SensorgetValues:  1 min    duration: 2.3 ms
        # ELV: SensorgetValues:  1 min    duration:
        #

        start   = time.time()
        fncname = "SensorgetValues: " + self.name + ": "
        sgvdata = [gglobs.NAN] * 3

        cdprint(fncname)
        setIndent(1)


        # 1 min average
        tmsg      = "get1min"
        register  = 0xB3        # get CPM
        readbytes = 2
        data      = []
        wait      = 0   #0.01
        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg, wait=wait)
        edprint(fncname + "answ: ", answ)

        if len(answ) == readbytes:
            value = answ[0] + (answ[1] / 100)   # ist µSv value, not CPM
            msg   = fncname + "{}:{:6.2f}".format(tmsg, value)
            bmsg  = True, msg
            sgvdata[0] = (round(value * 8.33, 2))
        else:
            msg  = fncname + "Failure reading proper byte count"
            bmsg = False, msg

        duration = (time.time() - start) * 1000
        if bmsg[0]:      gdprint(msg + "  dur:{:0.2f} ms".format(duration))


        # 10 min average
        tmsg      = "get10m"
        register  = 0xB2        # get CPM over 10 min
        readbytes = 2
        data      = []
        wait      = 0   #0.01
        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg, wait=wait)
        edprint(fncname + "answ: ", answ)

        if len(answ) == readbytes:
            value = answ[0] + (answ[1] / 100)   # ist µSv value, not CPM
            msg  = fncname + "{}:{:6.2f}".format(tmsg, value)
            bmsg = True, msg
            sgvdata[1] = (round(value * 8.33, 2))
        else:
            msg  = fncname + "Failure reading proper byte count"
            bmsg = False, msg

        duration = (time.time() - start) * 1000
        if bmsg[0]:      gdprint(msg + "  dur:{:0.2f} ms".format(duration))

        # other
        ydprint("Measuring Time")
        sgvdata[2] = self.GDK101getMeasuringTime()

        ydprint("Status:")
        ydprint(self.GDK101getStatus())

        ydprint("Firmware:")
        ydprint(self.GDK101getFirmwareVersion())

        setIndent(0)
        return sgvdata


    def SensorGetInfo(self):

        info  = "{}\n"                             .format("Count Rate")
        info += "- Address:         0x{:02X}\n"    .format(self.addr)
        info += "- Firmware:        {}\n"          .format(self.firmware)
        info += "- Variables:       {}\n"          .format(", ".join("{}".format(x) for x in gglobs.Sensors["GDK101"][5]))

        return info.split("\n")

