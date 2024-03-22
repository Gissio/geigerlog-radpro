#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
I2C sensor module LM75(B) - Digital temperature sensor and thermal watchdog
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

# LM75B Digital temperature sensor and thermal watchdog
# LM75:   9 bit resolution
# LM75B: 11 bit resolution
# https://www.nxp.com/docs/en/data-sheet/LM75B.pdf

#activating LM75 on ELVdongle +++++++++++++++++++++++++++++++++++++++++++
#ELV LM75    TX 12:47:18   [  9] [  9]  Init Sensor Reg      == b'S 90 00 P'                # send 2 bytes, addr90+00
#ELV LM75    iR 12:47:18   [  9] [  9]                       == b'S 91 02 P'                # prep for reading 2 bytes from addr 91
#ELV LM75    RX 12:47:18   [  2] [  6]                       == b'1A A0 '                   # get 2 bytes 1A 80 = 26.5°C

#activating LM75 on IOW24-DG +++++++++++++++++++++++++++++++++++++++++++
#IOW LM75    TX 13:11:35   [  2] [  8]  Init Sensor Reg      == 02 C2 90 00 00 00 00 00     # send 2 bytes, addr90+00
#IOW         RX 13:11:35   [  2] [  8]                       == 02 02 00 00 00 00 00 00 ACK # ack
#IOW LM75    iR 13:11:35   [  2] [  8]                       == 03 02 91 00 00 00 00 00     # prep for reading 2 bytes from addr 91
#IOW         RX 13:11:35   [  2] [  8]                       == 03 02 1A 80 00 00 00 00     # get 2 bytes 1A 80 = 26.5°C

#activating LM75 on ISSdongle +++++++++++++++++++++++++++++++++++++++++++
# the I2C official way, NOT working !!!
#ISS LM75    TX 12:59:50   [  3] [  3]  Init Sensor Reg      == b'U\x90\x00' == 55 90 00    # send 2 bytes, addr90+00
#ISS LM75    iR 12:59:50   [  2] [  3]                       == b'U\x91\x02' == 55 91 02    # prep for reading 2 bytes from addr 91
#ISS LM75    RX 12:59:50   [  2] [  0]                       == b'' ==                      # get nothing

#activating LM75 on ISSdongle +++++++++++++++++++++++++++++++++++++++++++
# with ISS specific workaraound
#ISS LM75    TX 12:57:44   [  3] [  3]  Init Sensor Reg      == b'U\x90\x00' == 55 90 00    # send 2 bytes, addr90+00
#ISS LM75    iR 12:57:44   [  2] [  4]                       == b'U\x91\x00\x02' == 55 91 00 02 # prep for reading 2 bytes from addr 91 AND set reg 00!
#ISS LM75    RX 12:57:44   [  2] [  2]                       == b'\x1a\x80' == 1A 80        # get 2 bytes 1A 80 = 26.5°C



class SensorLM75:
    """Code for the LM75(B) sensors"""

    addr    = 0x48              # addr options: 0x48 | 0x49 | 0x4A | 0x4B | 0x4C | 0x4D | 0x4E | 0x4F
    name    = "LM75"
    subtype = "LM75B"


    def __init__(self, addr):
        """Init SensorLM75 class"""

        self.addr    = addr


    def SensorInit(self):
        """Check for presence of sensor"""

        fncname = "SensorInit: " + self.name + ": "
        dmsg    = "Sensor {:8s} at address 0x{:02X} set for subtype {}".format(self.name, self.addr, self.subtype)

        dprint(fncname)
        setIndent(1)

        # check for presence of an I2C device at I2C address
        if not gglobs.I2CDongle.DongleIsSensorPresent(self.addr):
            # no device found
            setIndent(0)
            return  False, "Did not find any I2C device at address 0x{:02X}".format(self.addr)
        else:
            # device found
            gdprint("Found an I2C device at address 0x{:02X}".format(self.addr))

        setIndent(0)
        return (True,  "Initialized " + dmsg)


    def SensorgetValues(self):
        """ Write to reg 00 and read the Temp """

        # The device can be set to operate in either mode: normal or shutdown. In normal operation
        # mode, the temp-to-digital conversion is executed every 100 ms and the Temp register is
        # updated at the end of each conversion. During each ‘conversion period’ (T conv ) of about
        # 100 ms the device takes only about 10 ms, called ‘temperature conversion time’ (t conv(T) ),
        # to complete a temperature-to-data conversion and then becomes idle for the time
        # remaining in the period

        # sensor via ELV braucht diese sequence:
        # wrt       = gglobs.I2CDongle.ELVwriteBytes(b"S 90 00 P")  # adressierung reg
        # wrt       = gglobs.I2CDongle.ELVwriteBytes(b"S 91 02 P")  # init reading
        # answ      = gglobs.I2CDongle.ELVreadBytes(readbytes)      # reading

        # measurement duration:
        #   mit dongle ISS:   SensorgetValues: Temp:25.125,  duration:  1.1 ...  2.1 ms   (avg: 1.4)  1.0x
        #   mit dongle ELV:   SensorgetValues: Temp:25.125,  duration:  8.4 ...  9.0 ms   (avg: 8.7)  6.2x
        #   mit dongle IOW:   SensorgetValues: Temp:23.750,  duration:  9.1 ... 17.7 ms   (avg:13.6)  9.7x
        #   mit dongle FTD:   SensorgetValues: Temp:23.750,  duration: 31.7 ... 49.4 ms   (avg:33.1) 23.6x

        start = time.time()
        fncname = "SensorgetValues: " + self.name + ": "
        cdprint(fncname)
        setIndent(1)

        tmsg      = "getData"
        register  = 0x00
        readbytes = 2
        data      = []
        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)

        if len(answ) == readbytes:
            Temp = self.LM75calcTemperature(*answ)
            msg = ""
        elif len(answ) == 0:
            Temp = gglobs.NAN
            msg = BOLDRED + "No data returned: answ= '{}'".format(answ)
        else:
            Temp = gglobs.NAN
            msg = BOLDRED + "Improper data returned: answ= '{}'".format(answ)

        duration = (time.time() - start) * 1000
        cdprint(fncname + "Temp:{:<6.3f},  duration:{:<0.2f} ms  ".format(Temp, duration), msg)
        setIndent(0)
        return (Temp,)


    def SensorGetInfo(self):

        info  = "{}\n"                             .format("Temperature")
        info += "- Address:         0x{:02X}\n"    .format(self.addr)
        info += "- Subtype:         {}\n"          .format(self.subtype)
        info += "- Variables:       {}\n"          .format(", ".join("{}".format(x) for x in gglobs.Sensors["LM75"][5]))

        return info.split("\n")


    def SensorReset(self):
        """Reset LM75 Temp sensor - option does not exist"""

        return "has no resetting option"


    def LM75runAllFunctions(self):
        """ for LM75 sensor """

        gdprint("LM75runAllFunctions - nothing defined")


    def LM75calcTemperature (self, msb, lsb):
        """
        returns Temp in deg Celsius calculated from msb, lsb
        - use 11 bit conversion for LM75B,
        -      9 bit conversion for LM75
        Temp is in 2 bytes in Two's complement
        """
        #11-bit binary
        #(two’s complement) Hexadecimal Value
        #011 1111 1000      3F8         +127.000 °C
        #011 1111 0111      3F7         +126.875 °C
        #011 1111 0001      3F1         +126.125 °C
        #011 1110 1000      3E8         +125.000 °C
        #000 1100 1000      0C8         + 25.000 °C
        #000 0000 0001      001         +  0.125 °C
        #000 0000 0000      000            0.000 °C
        #111 1111 1111      7FF         -  0.125 °C
        #111 0011 1000      738         - 25.000 °C
        #110 0100 1001      649         - 54.875 °C
        #110 0100 1000      648         - 55.000 °C

        if self.subtype == "LM75B": # 11bit
            temp1 = ((msb << 8 | lsb ) >> 5)
            if temp1 & 0x400:               # 0x400 == 0b0100 0000 0000
                temp1 = temp1 - 0x800       # 0x800 == 0b1000 0000 0000
            Temp  = temp1 * 0.125           # deg Celsius for LM75B (11bit)

        else:                       # 9 bit
            temp1 = ((msb << 8 | lsb ) >> 7)
            if temp1 & 0x100:               # 0b1 0000 0000
                temp1 = temp1 - 0x200       # 0b10 0000 0000
            Temp  = temp1 * 0.5             # deg Celsius  for LM75 ( 9bit)

        return Temp

