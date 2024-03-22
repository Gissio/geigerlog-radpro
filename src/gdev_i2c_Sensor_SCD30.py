#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
I2C sensor module SCD30 for CO2 (by NDIR), Temperature, and Humidity
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

"""
Reference: Sensirion_CO2_Sensors_SCD30_Interface_Description.pdf - Version 0.91 – D1 – August 2018
https://www.sensirion.com/de/umweltsensoren/kohlendioxidsensor/kohlendioxidsensoren-scd30/
"""


class SensorSCD30:
    """Code for the Sensirion SCD30 sensor"""

    addr       = 0x61       # the only option for the SCD30
    name       = "SCD30"
    firmware   = "not set"  # my device: 3.66 (same as example from manual)
    measIntvl  = 5          # Measurement Interval in sec (default = 2)
    frc        = None       # Forced Recalibration value (FRC). Default is 400 [ppm]


    def __init__(self, addr):
        """Init SensorSCD30 class"""

        self.addr       = addr


    def SensorInit(self):
        """Scan for presence, get Serial No, start periodic measurement"""

        fncname = "SensorInit: " + self.name + ": "
        dmsg    = "Sensor {:8s} at address 0x{:02X}".format(self.name, self.addr)

        dprint(fncname)
        setIndent(1)

        ## check for presence of an I2C device at I2C address
        presence = gglobs.I2CDongle.DongleIsSensorPresent(self.addr)
        if not presence:
            # no device found
            setIndent(0)
            return  False, "Did not find any I2C device at address 0x{:02X}".format(self.addr)
        else:
            # device found
            gdprint("Found an I2C device at address 0x{:02X}".format(self.addr))


        # NOTE: Reset on the IOW dongle:
        # When a reset is done, the first call of firmware after reset
        # always results in  a "wrong report ID" response, but the firmware
        # does come out correct.
        #
        # Likewise, the first call to self.SCD30DataReady() also comes
        # out with "wrong report ID" response, but this CANNOT be changed by
        # removing reset!
        #
        ## soft reset
        # dprint(fncname + "Sensor Reset")
        # gdprint(self.SensorReset())

        ## get firmware version
        dprint(fncname + "Get Firmware")
        gdprint(self.SCD30getFirmwareVersion())

        ## get Forced Recalibration value (FRC)
        # after power cycle this returns always "400" irrespective of what it really is!
        dprint(fncname + "Get Forced Recalibration value (FRC)")
        gdprint(fncname + "{} ppm".format(self.SCD30getFRC()))

        ## set interval (default is 2 sec)
        dprint(fncname + "Set Measurement Interval")
        gdprint(self.SCD30MeasurementSetInterval(self.measIntvl))

        ## stop auto measurements                   # need to stop first???
        dprint(fncname + "SCD30MeasurementStop")
        gdprint(self.SCD30MeasurementStop())

        ## start auto measurements
        dprint(fncname + "SCD30MeasurementStart")
        gdprint(self.SCD30MeasurementStart())

        setIndent(0)

        return (True,  "Initialized " + dmsg)



    def SCD30getFirmwareVersion(self):
        """get the Firmware Version as Major.Minor"""

        # 1.4.9 Read firmware version
        # Command:  0xD100 , no argument needed
        # Wait None in datasheet Version 1.0 – D1 – May 2020
        # response: 3 bytes (2 b firmware + 1 bcrc) Firmware version: Major.Minor: 0x03, 0x42 => 3.66 (3.66 is also found on my chip)

        # Duration:
        # ISS: SCD30getFirmwareVersion: duration: 1.6 ms

        start = time.time()
        fncname = "SCD30getFirmwareVersion: "

        tmsg      = "FirmWr"
        register  = 0xD100
        readbytes = 3
        data      = []
        wait      = 0
        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=3, msg=tmsg, wait=wait)

        if len(answ) != readbytes:
            edprint(fncname + "Failure reading Serial Number, reponse: ", answ)
            return "Not Found"

        self.firmware = "{}.{}".format(answ[0], answ[1])

        duration = (time.time() - start) * 1000
        msg = fncname + "got firmware:{}  in:{:0.1f} ms".format(self.firmware, duration)

        return msg


    def SensorReset(self):
        """Soft Reset SCD30 sensor"""

        # 1.4.10 Soft reset
        # The SCD30 provides a soft reset mechanism that forces the sensor into the same state as after
        # powering up without the need for removing the power-supply. It does so by restarting its system
        # controller. After soft reset the sensor will reload all calibrated data. However, it is worth
        # noting that the sensor reloads calibration data prior to every measurement by default. This
        # includes previously set reference values from ASC or FRC as well as temperature offset values
        # last setting. The sensor is able to receive the command at any time, regardless of its internal
        # state. In order to start the soft reset procedure the following command should be sent.

        # duration: 0.7 ms

        start   = time.time()
        fncname = "SensorReset: " + self.name + ": "
        # dprint(fncname)

        tmsg      = "Reset"
        register  = 0xD304
        readbytes = 0
        data      = []
        wrt       = gglobs.I2CDongle.DongleWriteReg(self.addr, register, readbytes, data, addrScheme=3, msg=tmsg)

        # required wait 0.7 ms
        time.sleep(0.001) # 1 ms

        duration = 1000 * (time.time() - start)

        return fncname + "took {:0.1f} ms".format(duration)


    def SCD30MeasurementStart(self):
        """needs to be done only once"""

        # 1.4.1 Trigger continuous measurement with optional ambient pressure compensation
        # Starts continuous measurement of the SCD30 to measure CO 2 concentration, humidity
        # and temperature. Measurement data which is not read from the sensor will be overwritten.
        # The measurement interval is adjustable via the command documented in chapter 1.4.3,
        # initial measurement rate is 2s.
        # Continuous measurement status is saved in non-volatile memory. When the sensor is
        # powered down while continuous measurement mode is active SCD30 will measure
        # continuously after repowering without sending the measurement command. The CO2
        # measurement value can be compensated for ambient pressure by feeding the pressure value
        # in mBar to the sensor. Setting the ambient pressure will overwrite previous settings of
        # altitude compensation. Setting the argument to zero will deactivate the ambient pressure
        # compensation (default ambient pressure = 1013.25 mBar). For setting a new ambient pressure
        # when continuous measurement is running the whole command has to be written to SCD30.
        #
        # command: 0x0010 argument
        # argument: Format: uint16 Available range: 0 & [700 ... 1400]. Pressure in mBar.
        # argument: 0x00 0x00 0x81 : Start continuous measurement without ambient pressure compensation

        fncname = "SCD30MeasurementStart: "

        tmsg      = "StartMeas"
        register  = 0x0010
        readbytes = 0
        data      = [0x00, 0x00, 0x81]
        wrt       = gglobs.I2CDongle.DongleWriteReg(self.addr, register, readbytes, data, addrScheme=3, msg=tmsg)

        return fncname + "Done"


    def SCD30MeasurementStop(self):
        """needs to be done to stop activity"""

        # 1.3.2 Stop continuous measurement
        # Command:  0x0104, no argument     (!!!!!!!!!!!!! in Example 0x0107 is used ????????????)
        #                                   ( but in 1.1.2 I2C Sequence there is again 0x0104 )
        # response: None

        fncname = "SCD30MeasurementStop: "

        tmsg      = "StopMeas"
        register  = 0x0104
        readbytes = 0
        data      = []
        wrt       = gglobs.I2CDongle.DongleWriteReg(self.addr, register, readbytes, data, addrScheme=3, msg=tmsg)

        return fncname + "Done"


    def SCD30MeasurementSetInterval(self, interval):
        """sets the measurement interval. Default is 2 sec"""

        fncname = "SCD30MeasurementSetInterval: "

        # 1.3.3 Set measurement interval
        # Sets the interval used by the SCD30 sensor to measure in continuous measurement mode (see chapter 1.3.1).
        # Initial value is 2 s. The chosen measurement interval is saved in non-volatile memory and thus is not
        # reset to its initial value after power up.

        # Command:  0x4600 argument
        # argument: Format: unit16 Interval in seconds. Available range: [2 ... 1800] given in 2 bytes
        #                   in the order MSB, LSB, followed by CRC8
        #           Set measurement interval to 2s: 0x00, 0x02, 0xE3
        #           Set measurement interval to 5s: 0x00, 0x05, 0x74
        # response: None

        mi        = interval
        mi1       = mi >> 8
        mi2       = mi & 0xFF
        mi3       = getCRC8((mi1, mi2))

        tmsg      = "SetMeasIntvl"
        register  = 0x4600
        readbytes = 0
        # data      = [0x00, 0x02, 0xE3]  # default = 2 sec
        data      = [mi1,  mi2,  mi3]     # my setting (5 sec = 0x00, 0x05, 0x74)

        wrt       = gglobs.I2CDongle.DongleWriteReg(self.addr, register, readbytes, data, addrScheme=3, msg=tmsg)

        return "Measurement Interval set to: {} sec".format(data[0]<<8 | data[1])


    def SCD30getFRC(self):
        """Get the Forced Recalibration value (FRC). Default is 400 ppm"""

        # 1.4.6 (De-)Activate Automatic Self-Calibration (ASC)
        # Subsegment:  Set Forced Recalibration value (FRC)
        # Forced recalibration (FRC) is used to compensate for sensor drifts when a reference value of
        # the CO 2 concentration in close proximity to the SCD30 is available. For best results, the
        # sensor has to be run in a stable environment in continuous mode at a measurement rate of 2s
        # for at least two minutes before applying the FRC command and sending the reference value.
        # The reference CO2 concentration has to be within the range 400 ppm ≤ c ref (CO2 ) ≤ 2000 ppm.

        # Command:  0x5204 argument
        # argument: no argument for GETTING the FRC
        # response: 3 bytes:  FRC MSB, FRC LSB, CRC()
        #           Default 400ppm: 0x01, 0xc2, 0x50

        fncname = "SCD30getFRC: "

        tmsg      = "getFRC"
        register  = 0x5204
        readbytes = 3
        data      = []
        wait      = 0

        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=3, msg=tmsg, wait=wait)

        if len(answ) == readbytes: self.frc  = answ[0] << 8 | answ[1]

        return self.frc


    def SCD30setFRC(self, frcvalue):
        """Set the Forced Recalibration value (FRC). Default is 400 ppm"""

        # 1.4.6 (De-)Activate Automatic Self-Calibration (ASC)
        # Subsegment:  Set Forced Recalibration value (FRC)
        # Forced recalibration (FRC) is used to compensate for sensor drifts when a reference value of
        # the CO 2 concentration in close proximity to the SCD30 is available. For best results, the
        # sensor has to be run in a stable environment in continuous mode at a measurement rate of 2s
        # for at least two minutes before applying the FRC command and sending the reference value.
        # The reference CO2 concentration has to be within the range 400 ppm ≤ c ref (CO2 ) ≤ 2000 ppm.
        #
        # The most recently used reference value is retained in **volatile** memory and can be read out
        # with the command sequence given below. After repowering the sensor, the command will return
        # the standard reference value of 400 ppm.
        # NOTE: After a restart the reference is read as 400, however the applied reference
        #       remains in effect but cannot be read anymore

        # Command:  0x5204 argument
        # argument: SETTING the FRC: Format: uint16 CO2 concentration in ppm: FRC MSB, FRC LSB, CRC8
        #           Default 400ppm: 0x01, 0xc2, 0x50
        # response: None (to read the current calib use SCD30getFRC())
        #

        fncname = "SCD30setFRC: "

        frc       = int(frcvalue)
        frc1      = frc >> 8
        frc2      = frc &  0xFF
        frc3      = getCRC8((frc1, frc2))

        tmsg      = "setFRC"
        register  = 0x5204
        readbytes = 0
        data      = [frc1, frc2, frc3]
        wrt       = gglobs.I2CDongle.DongleWriteReg(self.addr, register, readbytes, data, addrScheme=3, msg=tmsg)

        self.frc = self.SCD30getFRC()

        return fncname + "Done"


    def SCD30DataReady(self):
        """get the data-ready status of sensor;
        return: 1 True      Data are ready
                0 False     Data are NOT ready
                -1          Improper response
        """

        # 1.4.4 Get data ready status
        # Data ready command is used to determine if a measurement can be read from the sensor’s
        # buffer. Whenever there is a measurement available from the internal buffer this command
        # returns 1 and 0 otherwise. As soon as the measurement has been read by the return value
        # changes to 0. Note that the read header should be send with a delay of > 3ms following
        # the write sequence.
        # It is recommended to use data ready status byte before readout of the measurement values.
        #
        # command: 0x0202, no argument needed
        # readbytes: 3;  MSB, LSB, CRC

        start   = time.time()
        fncname = "SCD30DataReady: "
        # dprint(fncname)

        ready     = -1      # code for failure
        tmsg      = "Ready?"
        msg       = ""
        register  = 0x0202
        readbytes = 3
        data      = []
        wait      = 0.003           # wait 3 ms acc to datasheet:  Version 1.0 – D1 – May 2020
        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=3, msg=tmsg, wait=wait)

        duration = (time.time() - start) * 1000

        if len(answ) == readbytes:
            word0 = answ[0] << 8 | answ[1]
            if    word0 == 1:
                ready = True        # Data are ready
                msg   = "30  Data ready"
                color = BOLDGREEN
            else:
                ready = False       # Data are NOT ready
                msg   = "30  Data NOT ready"
                color = BOLDRED

            msg = fncname + " "*70 + "{}{}".format(color, msg)

        elif len(answ) == 0:
            msg = BOLDRED + "30  No data returned: answ= '{}'".format(answ)

        else:
            msg = BOLDRED + "30  Improper data returned: answ= '{}'".format(answ)

        cdprint(msg + "  {:0.1f} ms".format(duration))

        return ready


    def SensorgetValues(self):
        """Read the CO2, Temp and Humid values if available"""

        # 1.4.5 Read measurement
        # When new measurement data is available it can be read out with the following command.
        # Note that the read header should be send with a delay of > 3ms following the write
        # sequence. Make sure that the measurement is completed by reading the data ready status
        # bit before read out.
        #
        # Command: 0x0300, no argument needed. Reads a single measurement of CO2 concentration. (But also the rest!)
        # Example with sensor returning:  CO2 Concentration = 439 PPM
        #                                 Humidity          = 48.8 %
        #                                 Temperature       = 27.2 °C
        # CO2  CO2       CO2  CO2       T    T         T    T         RH   RH        RH   RH
        # MMSB MLSB CRC  LMSB LLSB CRC  MMSB MLSB CRC  LMSB LLSB CRC  MMSB MLSB CRC  LMSB LLSB CRC
        # 0x43 0xDB 0xCB 0x8c 0x2e 0x8f 0x41 0xd9 0x70 0xe7 0xff 0xf5 0x42 0x43 0xbf 0x3a 0x1b 0x74
        # Example: The CO2 concentration 400 ppm corresponds to 0x43c80000 in Big-Endian notation.

        # measurement duration:
        #   mit dongle ISS:  SCD30: CO2:600.779, Temp:22.575, Humid:33.948  dur:  4.9 ...  5.7 ms (avg:  5.2)       1.0x
        #   mit dongle ELV:  SCD30: CO2:773.918, Temp:27.040, Humid:36.856  dur: 14.5 ... 17.8 ms (avg: 14.8 ms)    2.8x
        #   mit dongle IOW:  SCD30: CO2:807.496, Temp:26.786, Humid:37.331  dur: 47   ... 51   ms (avg: 47.9 ms)    9.2x
        #   mit dongle FTD:  SCD30: CO2:807.496, Temp:26.786, Humid:37.331  dur: xx   ... xx   ms (avg: xxxx ms)    xxxx

        #   mit dongle ISS:  100 kHz    SCD30: dur:  4.9 ...  5.7 ms (avg:  5.2)       1.0x
        #   mit dongle ISS:  400 kHz    SCD30: dur:  3.1 ...  4.2 ms (avg:  3.4)       0.65x    1.53x faster

        # @9600 baud
        #   mit dongle ISS:  100 kHz    SCD30: dur: 10.8 ... 12.6 ms (avg: 11.6)
        #   mit dongle ISS:  400 kHz    SCD30: dur:  8.8 ... 10.0 ms (avg:  9.1)
        #   mit dongle ISS: 1000 kHz    SCD30: dur:  8.4 ... 11.1 ms (avg:  9.3)  # slower!




        start   = time.time()
        fncname = "SensorgetValues: " + self.name + ": "
        sgvdata = (gglobs.NAN,) * 3

        cdprint(fncname)
        setIndent(1)

        dataReady = self.SCD30DataReady()

        if  dataReady == 1:
            # data are ready
            tmsg      = "getval"
            register  = 0x0300
            readbytes = 18
            data      = []
            wait      = 0.003       # wait 3 ms acc to datasheet:  Version 1.0 – D1 – May 2020
            answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=3, msg=tmsg, wait=wait)

            #####################################################################################################################
            # reference --> CO2 Concentration = 439 PPM, Temperature = 27.2 °C,  Humidity = 48.8 %
            # answ = [0x43, 0xDB, 0xCB, 0x8c, 0x2e, 0x8f, 0x41, 0xd9, 0x70, 0xe7, 0xff, 0xf5, 0x42, 0x43, 0xbf, 0x3a, 0x1b, 0x74]
            #####################################################################################################################

            if len(answ) == readbytes:
                # Big-Endian notation
                # must convert to float explicitely, because numpy data format creates blobs in the SQL database!

                data_bytes = np.array(answ[0:2]   + answ[3:5],   dtype=np.uint8)
                co2 = float(data_bytes.view(dtype='>f')[0])

                data_bytes = np.array(answ[6:8]   + answ[9:11],  dtype=np.uint8)
                temp = float(data_bytes.view(dtype='>f')[0])

                data_bytes = np.array(answ[12:14] + answ[15:17], dtype=np.uint8)
                humid = float(data_bytes.view(dtype='>f')[0])

                if co2 > 300:   sgvdata = (round(co2, 0), round(temp, 3), round(humid, 3))    # first value is most often CO2==0; should be >400, but give it room

                msg = True, fncname + "CO2:{:6.3f}, Temp:{:6.3f}, Humid:{:6.3f}".format(co2, temp, humid)
            else:
                msg = False, fncname + "Failure reading proper byte count"

        else:
            # data not ready
            msg = False, fncname + "Data NOT ready, or failure to get status, or wrong bytecount"

        duration = (time.time() - start) * 1000
        if msg[0]:      gdprint(msg[1] + "  dur:{:0.2f} ms".format(duration))

        setIndent(0)
        return sgvdata


    def SensorGetInfo(self):

        info  = "{}\n"                             .format("CO2, Temperature, Humidity")
        info += "- Address:         0x{:02X}\n"    .format(self.addr)
        info += "- Firmware:        {}\n"          .format(self.firmware)
        info += "- Measure Intvl:   {} sec\n"      .format(self.measIntvl)
        info += "- Ref. Value:      {} ppm\n"      .format(self.frc)
        info += "- Variables:       {}\n"          .format(", ".join("{}".format(x) for x in gglobs.Sensors["SCD30"][5]))

        return info.split("\n")

