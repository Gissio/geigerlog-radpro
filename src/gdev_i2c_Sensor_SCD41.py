#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
I2C sensor module SCD41 for CO2 (by photoacoustic sensing), Temperature, and Humidity
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
Reference: Sensirion Data sheet SCD4x - Breaking the size barrier in CO2 sensing; Version 1.1 – April 2021
File: "Sensirion_CO2_Sensors_SCD40_SCD41_Datasheet.pdf"
https://www.sensirion.com/de/umweltsensoren/evaluationskit-sek-environmental-sensing/evaluationskit-sek-scd41/
"""



class SensorSCD41:
    """Code for the SCD41 sensors"""

    addr    = 0x62          # the only option for the SCD41
    name    = "SCD41"
    serno   = "not set"     # SCD41 Serial Number, like: 273.325.796.834.238


    def __init__(self, addr):
        """Init SensorSCD41 class"""

        self.addr    = addr


    def SensorInit(self):
        """Scan for presence, get Serial No, start periodic measurement"""

        fncname = "SensorInit: " + self.name + ": "
        dmsg    = "Sensor {:8s} at address 0x{:02X}".format(self.name, self.addr)

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

        # # reset (takes 1.2 sec)
        # not good. Also resets the calibration!
        # gdprint(fncname + "Sensor Reset")
        # self.SensorReset()

        # # reinit
        # Before sending the reinit command, the stop measurement command must be issued.!!!
        # gdprint(fncname + "Sensor re-init")
        # self.SCD41reinit()

        # # run self test - das geht schief auf ISS!!! vielleicht:  (timing out after 500mS)???
        # gdprint(fncname + "Sensor Self-Test")
        # self.SCD41SelfTest()

        # # stop auto measurements (maybe active from last start!!)
        gdprint(fncname + "stopping Auto-Measurement")
        wrt  = self.SCD41StopPeriodicMeasurement()

        # # get serial number - requires that auto-measurement is stopped!
        gdprint(fncname + "Getting SerNo:")
        self.serno = "{:n}".format(self.SCD41getSerialNumber())
        gdprint(fncname + "Got SerNo: " + self.serno)

        # # Trigger auto measurements
        # gdprint(fncname + "Triggering Auto-Measurement")
        wrt  = self.SCD41StartPeriodicMeasurement()

        setIndent(0)

        return (True,  "Initialized " + dmsg)


    def SCD41reinit(self):
        """reinit the sensor"""

        # 3.9.5 reinit
        # The reinit command reinitializes the sensor by reloading user settings from EEPROM.
        # Before sending the reinit command, the stop measurement command must be issued. If
        # the reinit command does not trigger the desired re-initialization, a power-cycle
        # should be applied to the SCD4x.
        # takes 20 ms

        fncname = "SCD41reinit: "

        tmsg      = "reinit"
        register  = 0x3646
        readbytes = 0
        data      = []
        wrt       = gglobs.I2CDongle.DongleWriteReg(self.addr, register, readbytes, data, addrScheme=2, msg=tmsg)

        # Required wait 20 ms
        time.sleep(0.02)

        return wrt


    def SCD41SelfTest(self):
        """run a self test - takes 10 sec"""

        # 3.9.3 perform_self_test
        # Description: The perform_self_test feature can be used as an end-of-line test to
        # check sensor functionality and the customer power supply to the sensor.
        # Write 0x3639 (hexadecimal) Command
        # Wait 10000 ms
        # Response 0x0000 0x81 No malfunction detected (CRC of 0x0000 = 0x81)

        fncname = "SCD41SelfTest: "

        tmsg      = "SelfTest"
        register  = 0x3639
        readbytes = 3
        data      = []
        wait      = 10      # Required wait 10000 ms!
        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=2, msg=tmsg, wait=wait)

        if len(answ) == readbytes and answ == [0x00, 0x00, 0x81]: gdprint(fncname + "SelfTest OK, response: ", answ)
        else:                                                     edprint(fncname + "SelfTest WRONG, response: ", answ)

        return answ


    def SCD41getSerialNumber(self):
        """get the Serial Number"""

        # CAUTION CAUTION CAUTION CAUTION CAUTION CAUTION CAUTION CAUTION
        #        must NOT be called with Auto-Measurement ongoing !!!!!
        # CAUTION CAUTION CAUTION CAUTION CAUTION CAUTION CAUTION CAUTION
        #
        # Write: 0x3682
        # Response: 9 bytes
        # Serial number = word[0] << 32 | word[1] << 16 | word[2]
        # Example:            0xf896 0x31  0x9f07 0xc2  0x3bbe 0x89       ==> 273’325’796’834’238
        # Max. command duration: 1 ms

        # my code on Example: [0xf8, 0x96, 0x31, 0x9f, 0x07, 0xc2, 0x3b, 0xbe, 0x89] ==> 273’325’796’834’238 ==> my code is ok
        # my device with:
        # ISS: SCD41getSerialNumber: answ: [13, 65, 205, 191, 7, 30, 59, 79, 58]  SerNo:  14.576.028.957.519
        # ELV: SCD41getSerialNumber: answ: [13, 65, 205, 191, 7, 30, 59, 79, 58]  SerNo:  14.576.028.957.519     # das isses wohl


        fncname = "SCD41getSerialNumber: "

        tmsg      = "SerNo"
        register  = 0x3682
        readbytes = 9
        data      = []
        wait      = 0.001       # 1 ms wait suggested by manual (bei IOW: 100 ms reicht auch nicht)
        answ      = gglobs.I2CDongle.DongleWriteRead  (self.addr, register, readbytes, data, addrScheme=2, msg=tmsg, wait=wait)

        if    len(answ) != readbytes                                    \
           or answ == [128, 6, 4, 128, 6, 4, 128, 6, 4]                 \
           or answ == [255, 255, 255, 255, 255, 255, 255, 255, 255]:
            edprint(fncname + "Failure reading Serial Number, reponse: ", answ)
            return gglobs.NAN

        # check for correct crc
        words = 3
        if getCRC8((answ[0], answ[1])) == answ[2]:   words -= 1
        if getCRC8((answ[3], answ[4])) == answ[5]:   words -= 1
        if getCRC8((answ[6], answ[7])) == answ[8]:   words -= 1
        if words > 0:
            if getCRC8((answ[0], answ[1])) == answ[2]:   gdprint(fncname + "Word0 has correct crc8")
            else:                                        edprint(fncname + "Word0 has WRONG crc8")
            if getCRC8((answ[3], answ[4])) == answ[5]:   gdprint(fncname + "Word1 has correct crc8")
            else:                                        edprint(fncname + "Word1 has WRONG crc8")
            if getCRC8((answ[6], answ[7])) == answ[8]:   gdprint(fncname + "Word2 has correct crc8")
            else:                                        edprint(fncname + "Word2 has WRONG crc8")

        # answ = [0xf8, 0x96, 0x31, 0x9f, 0x07, 0xc2, 0x3b, 0xbe, 0x89] # example serial number
        # answ = [13, 65, 205, 191, 7, 30, 59, 79, 58]                  # my serial number
        word0 = answ[0] << 8 | answ[1]
        word1 = answ[3] << 8 | answ[4]
        word2 = answ[6] << 8 | answ[7]
        serialno = word0 << 32 | word1 << 16 | word2

        gdprint(fncname + " "*68 + "SerNo: {:n}".format(serialno) )

        return serialno


    def SCD41StartPeriodicMeasurement(self):
        """needs to be done only once"""

        # 3.5.1 start_periodic_measurement
        # signal update interval is 5 seconds.
        # write 0x21b1
        # response: None

        fncname = "SCD41StartPeriodicMeasurement: "

        tmsg      = "StartMeas"
        register  = 0x21b1
        readbytes = 0
        data      = []
        wrt       = gglobs.I2CDongle.DongleWriteReg(self.addr, register, readbytes, data, addrScheme=2, msg=tmsg)

        return wrt


    def SCD41StopPeriodicMeasurement(self):
        """needs to be done to stop activity"""

        # 3.5.3 stop_periodic_measurement
        # Note that the sensor will only respond to other commands after
        # waiting 500 ms after issuing the stop_periodic_measurement command.
        # Write 0x3f86
        # response: None

        fncname = "SCD41StopPeriodicMeasurement: "

        tmsg      = "StopMeas"
        register  = 0x3f86
        readbytes = 0
        data      = []
        wrt       = gglobs.I2CDongle.DongleWriteReg(self.addr, register, readbytes, data, addrScheme=2, msg=tmsg)

        # Required wait 500 ms
        dprint(fncname + "waiting 500 ms")
        time.sleep(0.5)

        return wrt


    def SCD41DataReady(self):
        """get the data-ready status of sensor;
        return: 1 True      Data are ready
                0 False     Data are NOT ready
                -1          Improper response
        """

        # 3.8.2 get_data_ready_status
        # write: 0xe4b8
        # Wait 1 ms
        # read:  3 bytes
        # If the least significant 11 bits of word[0] are 0 → data not ready
        # else → data ready for read-out
        # response should  be an 0x8XXX value

        start   = time.time()
        fncname = "SCD41DataReady: "
        # dprint(fncname)

        ready     = -1      # code for failure
        tmsg      = "Ready?"
        register  = 0xe4b8
        readbytes = 3
        data      = []
        wait      = 0.001       # Required wait 1 ms
        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=2, msg=tmsg, wait=wait)

        duration = (time.time() - start) * 1000

        if len(answ) == readbytes:
            word0 = answ[0] << 8 | answ[1]
            if (word0 & 0x7FF) != 0:
                # Data are ready
                ready = True
                msg   = "41  Data ready"
                color = BOLDGREEN
            else:
                # Data are NOT ready
                ready = False
                msg   = "41  Data NOT ready"
                color = BOLDRED

            # msg = " "*74 + fncname + "{} {}".format(color, msg)
            msg = fncname + " "*70 + "{}{}".format(color, msg)

        elif len(answ) == 0:
            msg = BOLDRED + "41  No data returned: answ= '{}'".format(answ)

        else:
            msg = BOLDRED + "41  Improper data returned: answ= '{}'".format(answ)

        cdprint(msg + "  {:0.1f} ms".format(duration))

        return ready


    def SensorgetValues(self):
        """Read the CO2, Temp and Humid values if available"""

        # any result only after 5 sec after start and after EACH reading;
        # from Data sheet: "... the buffer is emptied upon read-out."

        # 3.5.2 read_measurement
        # write 0xec05
        # read 9 bytes
        # Example: read sensor output (500 ppm, 25 °C, 37 % RH)
        #          Response: 0x01f4 0x7b 0x6667 0xa2 0x5eb9 0x3c
        #
        # CO2 [ppm] = word[0]
        # T   [°C]  = word[1] / 2^16 * 175 - 45
        # RH  [%]   = word[2] / 2^16 * 100

        # measurement duration:
        #   with dongle ISS:  SCD41: CO2:829.000, Temp:24.182, Humid:32.088  duration:  4.3 ...  5.5 ms (avg: 4.8 ms)  1.0x
        #   with dongle ELV:  SCD41: CO2:922.000, Temp:24.524, Humid:31.822  duration: 11.7 ... 24.7 ms (avg:13.1 ms)  2,7x
        #   with dongle IOW:  SCD41: CO2:837.000, Temp:26.841, Humid:30.222  duration: 39.2 ... 40.4 ms (avg:39.9 ms)  8.3x
        #   with dongle FTD:  SCD41: CO2:837.000, Temp:26.841, Humid:30.222  duration: 65.8 ... 70.1 ms (avg:67.1 ms) 14.0x

        #   with dongle ISS:  100 kHz    SCD41:  duration:  4.3 ...  5.5 ms (avg: 4.8 ms)  1.0x
        #   with dongle ISS:  400 kHz    SCD41:  duration:  3.0 ...  5.9 ms (avg: 3.5 ms) 0.73x      1.37x

        # @ 9600 baud
        #   with dongle ISS:  100 kHz    SCD41:  duration:  4.5 ...  6.1 ms (avg: 5.2 ms)
        #   with dongle ISS:  400 kHz    SCD41:  duration:  2.9 ...  4.7 ms (avg: 3.3 ms)
        #   with dongle ISS: 1000 kHz    SCD41:  duration:  2.6 ...  5.0 ms (avg: 3.4 ms)  # slower!



        start   = time.time()
        fncname = "SensorgetValues: " + self.name + ": "
        sgvdata = (gglobs.NAN,) * 3

        cdprint(fncname)
        setIndent(1)

        dataReady = self.SCD41DataReady()
        # ################ test
        # dataReady = 1
        # ##########################

        if dataReady != 1:
            # data are NOT ready or failure to get ready status or not exactly 3 values received
            # debug print output already given in SCD41DataReady function
            pass

        else:
            # data are ready: dataReady == 1
            tmsg      = "getval"
            register  = 0xec05
            readbytes = 9
            data      = []
            answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=2, msg=tmsg)
            duration  = (time.time() - start) * 1000

            if len(answ) == readbytes:
                if set([0x80, 0x06, 0x04]).issubset(answ):  # check if 80 06 04 is in answ (Indicates wrong data)
                    msg = TYELLOW + fncname + "Wrong data: ", answ

                else:
                    # data look ok
                    word0 = answ[0] << 8 | answ[1]  # answ[2] is CRC
                    word1 = answ[3] << 8 | answ[4]  # answ[5] is CRC
                    word2 = answ[6] << 8 | answ[7]  # answ[8] is CRC

                    p16     = 2 ** 16
                    co2     = word0
                    temp    = word1 / p16 * 175 - 45
                    humid   = word2 / p16 * 100
                    sgvdata = (co2, temp, humid)

                    msg = TGREEN + fncname + "CO2:{:6.3f}, Temp:{:6.3f}, Humid:{:6.3f}  dur:{:0.2f} ms".format(*sgvdata, duration)
            else:
                msg = TYELLOW + fncname + "Failure reading proper byte count"

            gdprint(msg)

        setIndent(0)

        return sgvdata


    def SensorGetInfo(self):

        info  = "{}\n"                             .format("CO2, Temperature, Humidity")
        info += "- Address:         0x{:02X}\n"    .format(self.addr)
        info += "- Serial No:       {}\n"          .format(self.serno)
        info += "- Variables:       {}\n"          .format(", ".join("{}".format(x) for x in gglobs.Sensors["SCD41"][5]))

        return info.split("\n")


    def SensorReset(self):
        """Factory Reset SCD41 sensor"""

        # 3.9.4 perfom_factory_reset
        # Write 0x3632
        # response: None
        # Max. command duration [ms]: 1200

        # duration: 0.6 ms + 1.2 sec waiting!

        start   = time.time()
        fncname = "SensorReset: " + self.name + ": "
        # dprint(fncname)

        tmsg      = "Reset"
        register  = 0x3632
        readbytes = 0
        data      = []
        wrt       = gglobs.I2CDongle.DongleWriteReg(self.addr, register, readbytes, data, addrScheme=2, msg=tmsg)

        duration = 1000 * (time.time() - start)

        # Required wait 1200 ms
        time.sleep(1.2)

        return fncname + "took {:0.1f} ms + 1.2 sec wait".format(duration)


    def SCD41setFRC(self, co2ref):
        """Forced ReCalibration of the device"""

        # 3.7.1 perform_forced_recalibration
        # Description: To successfully conduct an accurate forced recalibration, the following steps need to be carried out:
        # 1.Operate the SCD4x in the operation mode later used in normal sensor operation (periodic measurement, low power
        #   periodic measurement or single shot) for > 3 minutes in an environment with homogenous and constant CO2
        #   concentration.
        # 2.Issue stop_periodic_measurement. Wait 500 ms for the stop command to complete.
        # 3.Subsequently issue the perform_forced_recalibration command and optionally read out the FRC correction (i.e. the
        #   magnitude of the correction) after waiting for 400 ms for the command to complete.
        #
        # • A return value of 0xffff indicates that the forced recalibration has failed.
        # Note that the sensor will fail to perform a forced recalibration if it was not operated before sending the command.
        # Please make sure that the sensor is operated at the voltage desired for the application when applying the forced
        # recalibration sequence.
        # Write 0x362f
        # Command Input: 0x01e0 = 480 ppm,  CRC of 0x01e0 = 0xb4
        # Overall Write:  0x362f 0x01e0 0xb4
        # Wait 400 ms command execution time
        # Response: 3 bytes:  0x7fce 0x7b (hexadecimal) Response: -50 ppm CRC of 0x7fce


        fncname = "SCD41setFRC: " + self.name + ": "
        dprint(fncname)

        # convert the reference value to msb lsb, crc
        msb, lsb  = int((co2ref // 256)),  (co2ref & 0xFF)
        # msb, lsb, crc8 = 0x01, 0xe0, 0xb4                     # TEST set to 480 ppm

        crc8      = getCRC8((msb, lsb))
        cdprint(fncname + "CO2ref: {} ppm, => msb:{}, lsb:{}, crc8:{}, Hex: {:02X} {:02X} {:02X}".format(co2ref, msb, lsb, crc8, msb, lsb, crc8))

        self.SCD41StopPeriodicMeasurement() #register  = 0x3f86

        # write to the dongle
        tmsg      = "ForceCalib"
        register  = 0x362f
        readbytes = 3
        data      = [msb, lsb, crc8]
        wait      = 0.4             # 400 ms wait
        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=2, msg=tmsg, wait=wait)

        cdprint(fncname + "force calib answ: {}".format(answ) )

        # calc corr
        corr = gglobs.NAN
        if len(answ) == 3:
            word0 = answ[0] << 8 | answ[1]  # answ[2] is CRC
            corr  = word0 - 0x8000
            cdprint(fncname + "word0:{} (=0x{:04x}), CO2 corr:{} ppm".format(word0, word0, corr) )

        self.SCD41StartPeriodicMeasurement()

        return corr

