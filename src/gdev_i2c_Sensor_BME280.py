#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
I2C module BME280 - for Temperature, Pressure, Humidity
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


"""
Barometric pressure: (use for altitude correction)
Sea level standard pressure:  1013.25 hPa
Barometric formula: p = p0 * exp(- H / H0), with H0 =7990m
p @ Altitude 85m:  p= 1013.25 * exp(-85/7990) = 1013.25 * 0,98942  = 1002,53

Info on Sensor Module Bluedot:
https://www.bluedot.space/bme280-tsl2591/
Vendor Reference: BME280 + TSL2591, ASIN: B0795WWXX8
"Please note that the BME280 is hardwired to use the I2C Address 0x77. The
alternative Address (0x76) is not available! "


# =============================================================================
# comparison of results obtained with the different dongles
# all calibration points agree


# Calibration Data for the BlueDot module BME280 + TSL2591
# validation: data identical between the 2 dongles
#
# via ELV dongle
# ELV BME280 TX 11:04:16   [   ] [ 17]  get cal1             == b'S EE 88 S EF 18 P'
# ELV        RX 11:04:16   [ 24] [ 72]                       == b'BE 6E 9A 69 32 00 77 92 CE D6 D0 0B 00 22 A4 FF F9 FF AC 26 0A D8 BD 10 '
# ELV BME280 TX 11:04:16   [   ] [ 17]  get cal2             == b'S EE A1 S EF 01 P'
# ELV        RX 11:04:16   [  1] [  3]                       == b'4B '
# ELV BME280 TX 11:04:16   [   ] [ 17]  get cal3             == b'S EE E1 S EF 07 P'
# ELV        RX 11:04:16   [  7] [ 21]                       == b'6B 01 00 13 2D 03 1E '

# via IOW dongle
# IOW BME280 TX 11:57:37   [  2] [  8]  get cal1             == 02 C2 EE 88 00 00 00 00
# IOW BME280 RX 11:57:37   [ 24] [  8]                       == 02 02 00 00 00 00 00 00 ACK
# IOW BME280 tx 11:57:37   [ 24] [  8]                       == 03 18 EF 00 00 00 00 00
# IOW BME280 RX 11:57:37   [ 24] [  8]                       == 03 06 BE 6E 9A 69 32 00 ok, Bytes received: 6
# IOW BME280 RX 11:57:37   [ 24] [  8]                       == 03 06 77 92 CE D6 D0 0B ok, Bytes received: 12
# IOW BME280 RX 11:57:37   [ 24] [  8]                       == 03 06 00 22 A4 FF F9 FF ok, Bytes received: 18
# IOW BME280 RX 11:57:37   [ 24] [  8]                       == 03 06 AC 26 0A D8 BD 10 ok, Bytes received: 24
# IOW BME280 RX 11:57:37   [ 24] [ 24]      Final            == BE 6E 9A 69 32 00 77 92 CE D6 D0 0B 00 22 A4 FF F9 FF AC 26 0A D8 BD 10
# IOW BME280 TX 11:57:37   [  2] [  8]  get cal2             == 02 C2 EE A1 00 00 00 00
# IOW BME280 RX 11:57:37   [  1] [  8]                       == 02 02 00 00 00 00 00 00 ACK
# IOW BME280 tx 11:57:37   [  1] [  8]                       == 03 01 EF 00 00 00 00 00
# IOW BME280 RX 11:57:37   [  1] [  8]                       == 03 01 4B 00 00 00 00 00 ok, Bytes received: 6
# IOW BME280 RX 11:57:37   [  1] [  1]      Final            == 4B
# IOW BME280 TX 11:57:37   [  2] [  8]  get cal3             == 02 C2 EE E1 00 00 00 00
# IOW BME280 RX 11:57:37   [  7] [  8]                       == 02 02 00 00 00 00 00 00 ACK
# IOW BME280 tx 11:57:37   [  7] [  8]                       == 03 07 EF 00 00 00 00 00
# IOW BME280 RX 11:57:37   [  7] [  8]                       == 03 06 6B 01 00 13 2D 03 ok, Bytes received: 6
# IOW BME280 RX 11:57:37   [  7] [  8]                       == 03 01 1E 01 00 13 2D 03 ok, Bytes received: 12
# IOW BME280 RX 11:57:37   [  7] [  7]      Final            == 6B 01 00 13 2D 03 1E

# ISS BME280  i1 14:40:32   [ 24] [  4]  get cal1            == b'U\xef\x88\x18'           == 55 EF 88 18
# ISS         RX 14:40:32   [ 24] [ 24]                      == b'\xben\x9ai2\x00w\x92\xce\xd6\xd0\x0b\x00"\xa4\xff\xf9\xff\xac&\n\xd8\xbd\x10'
#                                                                                          == BE 6E 9A 69 32 00 77 92 CE D6 D0 0B 00 22 A4 FF F9 FF AC 26 0A D8 BD 10
# ISS BME280  i1 14:40:32   [  1] [  4]  get cal2            == b'U\xef\xa1\x01'           == 55 EF A1 01
# ISS         RX 14:40:32   [  1] [  1]                      == b'K'                       == 4B
# ISS BME280  i1 14:40:32   [  7] [  4]  get cal3            == b'U\xef\xe1\x07'           == 55 EF E1 07
# ISS         RX 14:40:32   [  7] [  7]                      == b'k\x01\x00\x13-\x03\x1e'  == 6B 01 00 13 2D 03 1E

# =============================================================================
# Calling problems with ISS dongle due to non-standard way of reading from device
# preparations

#activating BME280 on ELVdongle +++++++++++++++++++++++++++++++++++++++++++
#ELV BME280  TX 14:12:42   [  9] [  9]  get ID               == b'S EE D0 P'
#ELV         iR 14:12:42   [  9] [  9]                       == b'S EF 01 P'
#ELV BME280  RX 14:12:42   [  1] [  3]                       == b'60 '
#                                                            Found Sensor BME280

#activating BME280 on IOW24-DG +++++++++++++++++++++++++++++++++++++++++++
#IOW BME280  TX 14:04:43   [  2] [  8]  get ID               == 02 C2 EE D0 00 00 00 00
#IOW         RX 14:04:43   [  1] [  8]                       == 02 02 00 00 00 00 00 00 ACK
#IOW         iR 14:04:43   [  1] [  8]                       == 03 01 EF 00 00 00 00 00
#IOW         RX 14:04:43   [  1] [  8]                       == 03 01 60 00 00 00 00 00 ok, Bytes received: 6
#                                                   Answer:  == 60
#                                                            Found Sensor BME280

#activating BME280 on ISSdongle +++++++++++++++++++++++++++++++++++++++++++
# the I2C official way, NOT working !!!
#ISS BME280  TX 15:01:05   [  3] [  3]  get ID               == b'U\xee\xd0'     == 55 EE D0    # send 2 bytes, addr ee + D0
#ISS         iR 15:01:05   [  1] [  3]                       == b'U\xef\x01'     == 55 EF 01    # prep for reading 1 byte from addr EF
#ISS         RX 15:01:06   [  1] [  0]                       == b'' ==                          # Failure, no bytes returned
#
# with ISS specific workaraound
#ISS BME280  TX 14:15:07   [  3] [  3]  get ID               == b'U\xee\xd0'     == 55 EE D0    # send 2 bytes, addr ee + D0
#ISS BME280  i1 14:15:07   [  1] [  4]  get ID               == b'U\xef\xd0\x01' == 55 EF D0 01 # prep for reading 1 byte from addr EF, but RESEND the register D0
#ISS         RX 14:15:07   [  1] [  1]                       == b'`' == 60                      # success
#                                                            Found Sensor BME280

# when not one but two registered need to be addressed, the ELV and IOW work unmodifyied
# but the ISS requires that a different command be used (56 instead of 55)!
# the ISS has no option for 3 byte commands, while the ELV and IOW would work unmodified
# using ELV dongle
#ELV BME280  TX 10:24:11   [ 12] [ 12]  ctrl_meas            == b'S EE F4 D6 P'                         # send 3 bytes, addr ee + F4 D6
#ELV         iR 10:24:11   [  9] [  9]                       == b'S EF 01 P'                            # prep for reading 1 byte from addr EF
#ELV         RX 10:24:11   [  1] [  3]                       == b'D6 '                                  # success

# using ISS dongle
#ISS BME280  TX 10:31:53   [  4] [  4]  ctrl_meas            == b'U\xee\xf4\xd6'     == 55 EE F4 D6     # send 3 bytes, addr ee + F4 D6
#ISS         iR 10:31:53   [  1] [  3]                       == b'U\xef\x01'         == 55 EF 01        # prep for reading 1 byte from addr EF
#ISS         RX 10:31:53   [  1] [  0]                       == b''                  ==                 # Failure, no bytes returned

#ISS BME280  TX 10:27:16   [  4] [  4]  ctrl_meas            == b'U\xee\xf4\xd6'     == 55 EE F4 D6     # send 3 bytes, addr ee + F4 D6
#ISS         ii 10:27:16   [  1] [  5]                       == b'U\xef\xf4\xd6\x01' == 55 EF F4 D6 01  # prep for reading 1 byte from addr EF, resending F4 D6
#ISS         RX 10:27:16   [  1] [  0]                       == b''                  ==                 # Failure, no bytes returned

#ISS BME280  TX 10:47:54   [  4] [  4]  ctrl_meas            == b'U\xee\xf4\xd6'     == 55 EE F4 D6     # send 3 bytes, addr ee + F4 D6
#ISS         ii 10:47:54   [  1] [  5]                       == b'V\xef\xf4\xd6\x01' == 56 EF F4 D6 01  # using CMD=56 (not 55): prep for reading 1 byte from addr EF, resending F4 D6
#ISS         RX 10:47:54   [  1] [  1]                       == b'\xd6'              == D6              # success
"""


from   gsup_utils       import *


class SensorBME280:
    """Code for the BME280 sensors"""

    addr    = 0x76             # addr options: 0x76, 0x77
    id      = 0x60
    name    = "BME280"


    def __init__(self, addr):
        """Init SensorBME280 class"""

        self.addr    = addr


    def SensorInit(self):
        """Reset, check ID, set reg hum, get calibration, trigger measurement"""

        fncname = "SensorInit: " + self.name + ": "
        dmsg    = "Sensor {:8s} at address 0x{:02X} with ID 0x{:02x}".format(self.name, self.addr, self.id)

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

        # check ID
        tmsg      = "checkID"
        register  = 0xD0
        readbytes = 1
        data      = []
        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)
        if len(answ) == readbytes and answ[0] == self.id:
            response = (True,  "Initialized " + dmsg)
            gdprint("Sensor {} at address 0x{:02X} has proper ID: 0x{:02X}".format(self.name, self.addr, self.id))
        else:
            setIndent(0)
            return (False, "Failure - Did find sensor, but ID: '{}' is not as expected: 0x{:02X}".format(answ, self.id))

        # soft reset
        # does NOT give a return!
        tmsg      = "Soft Reset"
        register  = 0xE0
        readbytes = 0
        data      = [0xB6]
        wrt       = gglobs.I2CDongle.DongleWriteReg (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)

        # set ctrl-hum
        # b101 = 0x05 = oversampling * 16
        tmsg      = "Ctrl_hum"
        register  = 0xf2
        readbytes = 1
        data      = [0x05]
        answ      = gglobs.I2CDongle.DongleWriteRead(self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)

        # Calibration Data calib00...calib25 (0x88 ... 0x9F) 24 values
        tmsg      = "calib1 24"
        register  = 0x88
        readbytes = 24
        data      = []
        self.cal1 = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)

        # Calibration Data calib26...calib41 (0xA1 ) 1 value
        tmsg      = "calib2 1"
        register  = 0xA1
        readbytes = 1
        data      = []
        self.cal2 = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)

        # Calibration Data calib26...calib41 (0xe1 ... 0xe7) 7 values
        tmsg      = "calib3 7"
        register  = 0xe1
        readbytes = 7
        data      = []
        self.cal3 = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)

        setIndent(0)
        return response


    def SensorgetValues(self):
        """ get one measurement of Temp, Press, Humid"""

        # trigger measurement with: ctrl_meas
        # makes one measurement, then waits for next trigger due to forced mode
        # 0b 101 101 10  = D6 = P oversampling * 16, T oversampling * 16,  forced mode
        #
        # max measurement time:  BOSCH: t measure,max = 1.25 + [2.3 ⋅ 1] + [2.3 ⋅ 4 + 0.575] + [0] = 13.325 ms
        # on dongle ISS:  BME280:  T:25.050, P:996.343, H:33.799 duration:  2.7 ...  4.1 ms (avg: 3.3)    1.0x
        # on dongle ELV:  BME280:  T:25.790, P:996.186, H:32.296 duration: 18   ... 20   ms (avg:19.0)    5.8x
        # on dongle IOW:  BME280:  T:24.250, P:983.489, H:35.830 duration: 37.4 ... 40.5 ms (avg:39.9)   12.1x
        # on dongle FTD:  BME280:  T:24.250, P:983.489, H:35.830 duration: 64.8 ... 71.7 ms (avg:65.4)   19.8x

        # on dongle ISS:  100 kHz BME280:                                   duration:  2.7 ...  4.1 ms (avg: 3.3)    1.0x
        # on dongle ISS:  400 kHz BME280:                                   duration:  1.6 ...  3.6 ms (avg: 2.3)    0.7x  (1.4x faster)

        # on dongle ISS: 1000 kHz BME280:(BME280 as only activated module)  duration:  1.6 ...  4.0 ms (avg: 2.4)
        # on dongle ISS:  400 kHz BME280:(BME280 as only activated module)  duration:  1.7 ...  4.8 ms (avg: 2.9)
        # on dongle ISS:  100 kHz BME280:(BME280 as only activated module)  duration:  2.9 ...  7.1 ms (avg: 3.8)

        start    = time.time()
        fncname  = "SensorgetValues: " + self.name + ": "
        fail     = False
        response = (gglobs.NAN,) * 3
        cdprint(fncname)
        setIndent(1)

        # trigger measurement
        try:
            tmsg      = "ctrl_meas"
            register  = 0xf4
            readbytes = 1
            data      = [0xd6]
            answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)
        except Exception as e:
            exceptPrint(e, "ctrl_meas")
            fail = True

        if fail or len(answ) != readbytes:
            rdprint(fncname + tmsg + " failed, giving up")
            setIndent(0)
            return response

        # get raw data
        try:
            tmsg      = "getRawData"
            register  = 0xf7
            readbytes = 8
            data      = []
            answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)
        except Exception as e:
            exceptPrint(e, "get data F7..FE")
            fail = True

        # answ == [128, 0, 0, 128, 0, 0, 128, 0]: does happen in first 1 or even first 2 calls
        if fail or len(answ) != readbytes or answ == [128, 0, 0, 128, 0, 0, 128, 0]:
            rdprint(fncname + tmsg + " failed, giving up")
            setIndent(0)
            return response

        # convert raw data
        try:
            t_raw, p_raw, h_raw = self.BME280getRawData(answ)
            response            = readBME280All(self.cal1, self.cal2, self.cal3, p_raw, t_raw, h_raw) # response = t, p, h
        except Exception as e:
            exceptPrint(e, "convert raw data")

        duration = (time.time() - start) * 1000
        gdprint(fncname + "Values:  T:{:<6.3f}, P:{:<6.3f}, H:{:<6.3f} duration:{:<0.1f} ms".format(*response, duration))
        setIndent(0)

        return response


    def BME280getRawData(self, rec):
        """calcs raw press, temp, hum"""

        msb, lsb, xlsb  = rec[0], rec[1], rec[2]
        press           = (msb << 16 | lsb << 8 | xlsb) >> 4

        msb, lsb, xlsb  = rec[3], rec[4], rec[5]
        temp            = (msb << 16 | lsb << 8 | xlsb) >> 4

        msb, lsb        = rec[6], rec[7]
        humid           = (msb <<  8 | lsb )

        return temp, press, humid


    def SensorReset(self):
        """Soft Reset the BME280 sensor + Ctrl-hum=5 setting"""
        # duration: 6.8 ... 7.4 ms

        start = time.time()

        fncname = "SensorReset: "
        # dprint(fncname)

        # 5.4.2 Register 0xE0 “reset”
        # If the value 0xB6 is written to the register, the device is reset using the complete
        # power-on-reset procedure. Writing other values than 0xB6 has no effect. The readout
        # value is always 0x00.
        tmsg      = "Reset"
        register  = 0xe0
        readbytes = 1
        data      = [0xb6]
        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)   # answ is []

        # 5.4.3 Register 0xF2 “ctrl_hum”
        # The “ctrl_hum” register sets the humidity data acquisition options of the device. Changes to this
        # register only become effective after a write operation to “ctrl_meas”.
        # Bit 2, 1, 0  Controls oversampling of humidity data.
        # 101 (=0x05) : Humidity oversampling ×16
        tmsg      = "ctr_hum"
        register  = 0xf2
        readbytes = 1
        data      = [0x05]
        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)  # answ is [5]

        duration  = 1000 * (time.time() - start)

        return "Done in {:0.1f} ms (Reset + Ctrl-hum = 5)".format(duration)


    def SensorGetInfo(self):

        info  = "{}\n"                             .format("Temperature, Pressure, Humidity")
        info += "- Address:         0x{:02X}\n"    .format(self.addr)
        info += "- ID:              0x{:02X}\n"    .format(self.id)
        info += "- Variables:       {}\n"          .format(", ".join("{}".format(x) for x in gglobs.Sensors["BME280"][5]))

        return info.split("\n")


#--------------------------------------
# code adapted from file bme280.py
# Author : Matt Hawkins
# Date     : 25/07/2016
# http://www.raspberrypi-spy.co.uk/
#--------------------------------------

from ctypes import c_short
from ctypes import c_byte
from ctypes import c_ubyte

def getShort(data, index):
    # return two bytes from data as a signed 16-bit value
    return c_short((data[index+1] << 8) + data[index]).value

def getUShort(data, index):
    # return two bytes from data as an unsigned 16-bit value
    return (data[index+1] << 8) + data[index]

def getChar(data,index):
    # return one byte from data as a signed char
    result = data[index]
    if result > 127:
        result -= 256
    return result

def getUChar(data,index):
    # return one byte from data as an unsigned char
    result =    data[index] & 0xFF
    return result

def readBME280All(cal1, cal2, cal3, pres_raw, t_raw, h_raw):

    # Convert byte data to word values
    dig_T1 = getUShort(cal1, 0)
    dig_T2 = getShort (cal1, 2)
    dig_T3 = getShort (cal1, 4)

    dig_P1 = getUShort(cal1, 6)
    dig_P2 = getShort (cal1, 8)
    dig_P3 = getShort (cal1, 10)
    dig_P4 = getShort (cal1, 12)
    dig_P5 = getShort (cal1, 14)
    dig_P6 = getShort (cal1, 16)
    dig_P7 = getShort (cal1, 18)
    dig_P8 = getShort (cal1, 20)
    dig_P9 = getShort (cal1, 22)

    dig_H1 = getUChar (cal2, 0)

    dig_H2 = getShort (cal3, 0)

    dig_H3 = getUChar (cal3, 2)

    dig_H4 = getChar  (cal3, 3)
    dig_H4 = (dig_H4 << 24) >> 20
    dig_H4 = dig_H4 | (getChar(cal3, 4) & 0x0F)

    dig_H5 = getChar  (cal3, 5)
    dig_H5 = (dig_H5 << 24) >> 20
    dig_H5 = dig_H5 | (getUChar(cal3, 4) >> 4 & 0x0F)

    dig_H6 = getChar  (cal3, 6)

    #Refine temperature
    var1 = ((((t_raw>>3)-(dig_T1<<1)))*(dig_T2)) >> 11
    var2 = (((((t_raw>>4) - (dig_T1)) * ((t_raw>>4) - (dig_T1))) >> 12) * (dig_T3)) >> 14
    t_fine = var1+var2
    temperature = float(((t_fine * 5) + 128) >> 8);

    # Refine pressure and adjust for temperature
    var1 = t_fine / 2 - 64000
    var2 = var1 * var1 * dig_P6 / 32768
    var2 = var2 + var1 * dig_P5 * 2
    var2 = var2 / 4 + dig_P4 * 65536
    var1 = (dig_P3 * var1 * var1 / 524288 + dig_P2 * var1) / 524288
    var1 = (1 + var1 / 32768) * dig_P1
    if var1 == 0:
        pressure=0
    else:
        pressure = 1048576 - pres_raw
        pressure = ((pressure - var2 / 4096.0) * 6250) / var1
        var1 = dig_P9 * pressure * pressure / 2147483648
        var2 = pressure * dig_P8 / 32768
        pressure = pressure + (var1 + var2 + dig_P7) / 16

    # Refine humidity
    humidity = t_fine - 76800
    humidity = (h_raw - (dig_H4 * 64.0 + dig_H5 / 16384.0 * humidity)) * (dig_H2 / 65536.0 * (1.0 + dig_H6 / 67108864.0 * humidity * (1.0 + dig_H3 / 67108864.0 * humidity)))
    humidity = humidity * (1.0 - dig_H1 * humidity / 524288.0)
    if humidity > 100:
        humidity = 100
    elif humidity < 0:
        humidity = 0

    return temperature/100, pressure/100, humidity
