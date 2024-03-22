#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
I2C module TSL2591 ALS (Ambient-Light-Sensor) for Visible + Infrared light
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

# Document: "TSL2591 Datasheet - Apr. 2013 - ams163.5"
# e.g.: https://www.manualshelf.com/manual/adafruit/1980/datasheet-english.html

# Sensor Bluedot:
# Herstellerreferenz: BME280 + TSL2591, ASIN: B0795WWXX8
# Light sensor: address 0x29"
# ATTENTION:
# this board responds also to address 0x28, but only in scans
# From: https://www.exp-tech.de/sensoren/licht/5226/adafruit-tsl2591-high-dynamic-range-digital-light-sensor
# "This board/chip uses I2C 7-bit address 0x29 and 0x28 (yes BOTH!)"
# 0x28 addr is present, but no data can be read from it!
#
# Gain and Integration time determine sensitivity and quality of measurement
    # Gain, doc page 6
    #         Name   Factor
    # AGAIN  = Low    1
    # AGAIN  = Med    25      1
    # AGAIN  = High   428     17.12       1
    # AGAIN  = Max    9876    395.04      23.07

    # Integration time, doc page 13
    # ATIME  = 100 ms
    # ATIME  = 200 ms
    # ATIME  = 300 ms
    # ATIME  = 400 ms
    # ATIME  = 500 ms
    # ATIME  = 600 ms

#activating TSL2591 on ELVdongle +++++++++++++++++++++++++++++++++++++++++++
#ELV TSL2591 TX 14:12:43   [  9] [  9]  get ID               == b'S 52 B2 P'
#ELV         iR 14:12:43   [  9] [  9]                       == b'S 53 01 P'
#ELV TSL2591 RX 14:12:43   [  1] [  3]                       == b'50 '
#                                                            Found Sensor TSL2591

#activating TSL2591 on IOW24-DG +++++++++++++++++++++++++++++++++++++++++++
#IOW TSL2591 TX 14:04:43   [  2] [  8]  get ID               == 02 C2 52 B2 00 00 00 00
#IOW         RX 14:04:43   [  1] [  8]                       == 02 02 00 00 00 00 00 00 ACK
#IOW         iR 14:04:43   [  1] [  8]                       == 03 01 53 00 00 00 00 00
#IOW         RX 14:04:43   [  1] [  8]                       == 03 01 50 00 00 00 00 00 ok, Bytes received: 6
#                                                   Answer:  == 50
#                                                            Found Sensor TSL2591

#activating TSL2591 on ISSdongle +++++++++++++++++++++++++++++++++++++++++++
#ISS TSL2591 TX 13:51:03   [  3] [  3]  get ID               == b'UR\xb2' == 55 52 B2
#ISS TSL2591 i1 13:51:03   [  1] [  4]  get ID               == b'US\xb2\x01' == 55 53 B2 01
#ISS         RX 13:51:03   [  1] [  1]                       == b'P' == 50
#                                                            Found Sensor TSL2591


class SensorTSL2591:
    """Code for the TSL2591 sensors"""

    name        = "TSL2591"
    addr        = 0x29              # it has no other addr but 0x29
    id          = 0x50              # ID 0x50 is a fixed value
    PID         = 0x00              # acc to document, page 16
                                    # The PID register provides an identification of the devices package.
                                    # This register is a read-only register whose value never changes.
                                    # PID bits 5:4 Package Identification = 00
    CMD         = 0xA0              # CMD Register = 0b1 01 0 0000 = 0xA0 is: CMD + Normal operation

    #                Name:  FieldVal,  Factor
    SensorGain  = {
                    "Low":  (0b00,     1),
                    "Med":  (0b01,     25),
                    "High": (0b10,     428),
                    "Max":  (0b11,     9876),
                  }

    #                Name:  FieldVal,  ms
    SensorInteg = {                             # the signal value is increasing LINEARLY with integration time
                    "100ms":(0b000,    100),
                    "200ms":(0b001,    200),
                    "300ms":(0b010,    300),
                    "400ms":(0b011,    400),
                    "500ms":(0b100,    500),
                    "600ms":(0b101,    600),
                  }

    lastselindex   = 1              # index to SensorGain Low, Med, High, Max; start with Med; best
                                    # chance for success in fewest cycles


    def __init__(self, addr):
        """Init SensorTSL2591 class"""

        self.addr = addr            # addr: 0x29 (it has no other, but for conistency of programming)


    def SensorInit(self):
        """check ID, check PID, Reset, enable measurement"""

        fncname = "SensorInit: " + self.name + ": "
        dmsg    = "Sensor {:8s} at address 0x{:02X} with ID 0x{:02x} ".format(self.name, self.addr, self.id)

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

        # Get Device ID = 0x50
        # The ID register provides the device identification. This register is a read-only register
        # whose value never changes.
        # ID Register (0x12) (Bit 7:0) value: 0x50
        tmsg      = "Get ID"
        register  = self.CMD + 0x12
        readbytes = 1
        data      = []
        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)
        if len(answ) == readbytes and answ[0] == self.id:
            response = (True,  "Initialized " + dmsg)
            gdprint("Sensor {} at address 0x{:02X} has proper ID: 0x{:02X}".format(self.name, self.addr, self.id))
        else:
            setIndent(0)
            return (False, "Failure - Did find an I2C device, but it has wrong ID: '{}' instead of {}".format(answ, self.id))

        # Get package identification (PID)
        # PID Register (0x11) (Bit 5:4) (2 bits only!)
        # PID: Package Identification = 00 (really, just 0x00!)
        # lohnt sich das drinzulassen?
        tmsg      = "Get PID"
        register  = self.CMD + 0x11
        readbytes = 1
        data      = []
        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)
        if len(answ) > 0:
            pid       = answ[0] & 0b00110000
            if pid == self.PID:
                gdprint(fncname + "Package Identification 0b{:02b} confirmed".format(pid))
                pass
            else:
                efprint(fncname + "Package Identification 0b{:02b} not as expected".format(pid))
                setIndent(0)
                return (False, "Failure - Did find sensor, but Package Identification is: '{}' and not: {}".format(pid, self.PID))
        else:
            edprint(fncname + "Package Identification 0b{:02b} not as expected, answ:", answ)
            setIndent(0)
            return (False, "Failure - Did find sensor, but Package Identification is: '{}' and not: {}".format(pid, self.PID))

        # reset to Power-Up status
        gdprint(fncname + "Reset to Power-up Status")
        self.SensorReset()

        # enable measurements
        gdprint(fncname + "Enable Measurements")
        self.TSL2591enableMeasurements()

        setIndent(0)

        return response


    def TSL2591enableMeasurements(self):

        # Enable measurements
        # Enable Register (0x00)
        # The ENABLE register is used to power the device on/off, enable functions and interrupts.
        # Here using only PON (Power the device on), and AEN (enable measurements)
        # PON Bit #0:   Power ON. This field activates the internal oscillator to permit the timers and
        #               ADC channels to operate. Writing a one activates the oscillator. Writing a zero
        #               disables the oscillator.
        # AEN Bit #1:   ALS Enable. This field activates ALS function. Writing a one activates the ALS.
        #               Writing a zero disables the ALS.
        # set Register: 0b 0000 00 11  => 0x03
        tmsg      = "set PON+AEN"
        register  = self.CMD + 0x00
        readbytes = 1
        data      = [0x03]
        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)


    def SensorgetValues(self):
        """get Lum in Auto mode. 1st run fast with 100ms integration time, then with desired time"""

        # duration:
        # total duration is mainly determined by integration time:
        #   using 2 cycles with 1st=100ms followed by 2nd=200 ms ==> observed duration is very stable
        # therfore comparing duration minus 300 ms!
        #                                                                                                                                     avg-300 ms
        # ISS dongle: TSL2591:  Vis:0.6000, IR:0.1963, RAW-Vis:11853, RAW-IR:3879, Gain:9876, Integ:200 ms, dur: 312 ... 318 ms (avg: 314 ms)    14 ms    1.0x
        # ELV dongle: TSL2591:  Vis:107.58, IR: 15.34, RAW-Vis: 5379, RAW-IR: 767, Gain: 25,  Integ:200 ms, dur: 385 ... 389 ms (avg: 387 ms)    87 ms    6.2x
        # IOW dongle: TSL2591:  Vis:183.92, IR:  29.6, RAW-Vis: 9196, RAW-IR:1480, Gain: 25,  Integ:200 ms, dur: 454 ... 456 ms (avg: 455 ms)   155 ms   11.1x
        # FTD dongle: TSL2591:  Vis:183.92, IR:  29.6, RAW-Vis: 9196, RAW-IR:1480, Gain: 25,  Integ:200 ms, dur: 620 ... 665 ms (avg: 627 ms)   327 ms   23.4x

        #                                                                 avg-300 ms
        # ISS dongle: TSL2591:  100 kHz dur: 312 ... 318 ms (avg: 314 ms)    14   ms    1.0x
        # ISS dongle: TSL2591:  400 kHz dur: 310 ... 318 ms (avg: 313.3 ms)  15.3 ms    sogar langsamer???

        start = time.time()
        fncname = "SensorgetValues: " + self.name + ": "
        cdprint(fncname)
        setIndent(1)

        SensorIntegIndex = "200ms"
        finalatime       = SensorIntegIndex
        finalIntTime     = self.SensorInteg[SensorIntegIndex][1]
        # gdprint(fncname + "finalatime: ", finalatime)
        # gdprint(fncname + "finalIntTime: ", finalIntTime)

        selector  = ("Low",      # Factor = 1
                     "Med",      # Factor = 25
                     "High",     # Factor = 428
                     "Max",      # Factor = 9876
                    )
        selindex    = self.lastselindex # =1 => Factor 25, # start with Med; best chance for success in fewest cycles
        again       = selector[selindex]
        atime       = "100ms"      # make first guess fast; then use final, slow inttime
        firstRun    = True
        dataFormat  = "Vis:{:6.5g}, IR:{:6.5g}, RAW-Vis:{:5.0f}, RAW-IR:{:4.0f}, Gain:{:3.0f}, Integ:{} ms"

        while True:
            breakflag   = False

            #get a lum value
            lumstart = time.time()
            lumdata  = self.TSL2591getLum(gain=again, intgrl=atime)
            duration = (time.time() - lumstart) * 1000
            cdprint(fncname + "getLum: " + dataFormat.format(*lumdata) + ", dur:{:0.0f} ms".format(duration))

            vis, ir, visraw, irraw, gainFct, inttime = lumdata  # need visraw and inttime only

            if np.isnan(vis) and np.isnan(ir): break # if all nan then exit


            # lower limit for autoscale must be <= min(2600, 3800, 2800)
            # chosen is 2500
            #        Name   Factor
            #                                             104
            #AGAIN = Low    1                            2600     152
            #AGAIN = Med    25      1                   65000    3800     163
            #AGAIN = High   428     17.12       1               65000    2800
            #AGAIN = Max    9876    395.04      23,07                   65000

            lastselindex = selindex
            testraw      = visraw * finalIntTime / inttime  # estimate the value with selected final integ time
            # cdprint(fncname + "testraw: ", testraw)

            if testraw > 65000:                         # too much light
                selindex += -1                          # 1 step down
                if selindex < 0:
                    selindex = 0
                    breakflag = True       # reached the bottom?
                # cdprint(fncname + "AutoDEcrease Gain 1 step")

            elif testraw < 152:                         # allows 2 step up:
                selindex += 2                           # 1 step up
                if selindex > 3:
                    selindex = 3
                    breakflag = True       # broke the ceiling?
                # cdprint(fncname + "AutoINcrease Gain 2 steps")

            elif testraw < 2500:                        # allows 1 step up
                selindex += 1                           # 1 step up
                if selindex > 3:
                    selindex = 3
                    breakflag = True       # broke the ceiling?
                # cdprint(fncname + "AutoINcrease Gain 1 step")
            else:
                breakflag = True

            if breakflag and not firstRun:
                break

            # set for next getLum
            firstRun    = False
            again       = selector[selindex]            # set new gain
            atime       = finalatime                    # set best resolution for final run

        self.lastselindex = selindex

        # The Final Auto-lumdata are the same as last prelim lumdata !

        duration = (time.time() - start) * 1000
        gdprint(fncname + "Total:  " + dataFormat.format(*lumdata) + ", dur:{:0.0f} ms".format(duration))

        setIndent(0)
        return (vis, ir)


    def TSL2591getLum(self, gain = 'Low', intgrl = "100ms"):
        """non-Auto mode"""

        start    = time.time()
        fncname  = "TSL2591getLum: "
        response = (gglobs.NAN, ) * 6            # default

        gainFV   = self.SensorGain[gain][0]      # Field Value
        gainFct  = self.SensorGain[gain][1]      # Gain Factor

        intFV    = self.SensorInteg[intgrl][0]   # Field Value
        intTime  = self.SensorInteg[intgrl][1]   # integration time in ms
        intFct   = intTime / 100                 # Gain Factor by integration time


        # Control Register (0x01) - Setting Gain Mode and Integration Time
        tmsg      = "set gain+integ"
        register  = self.CMD + 0x01
        readbytes = 1
        data      = [gainFV << 4 | intFV ]      # at start: 0x10
        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)

        if len(answ) != 1:
            msg = BOLDRED + "No data or wrong data returned: answ= '{}'".format(answ)
            rdprint(fncname + msg)
            return response

        ####################################################################################################################
        # Cycling the AEN bit does NOT seem necessary
        # DOCH!!! DOCH!!! DOCH!!! DOCH!!! DOCH!!! DOCH!!! DOCH!!!
        # If left out, spikes come up in rather regular intervals!
        # Enable Register (0x00)
        # Cycle the AEN (ALS Enable) bit in the Enable Register
        # Enable Register (0x00)
        tmsg      = "Disable AEN"
        register  = self.CMD
        readbytes = 1
        data      = [0x01]  # ALS Disable, only PON is laft
        answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)

        # Enable Register (0x00)
        # AEN: Bit #1:  ALS Enable. This field activates ALS function. Writing a one activates the ALS.
        #               Writing a zero disables the ALS.
        # PON: Bit #0:  Power ON. This field activates the internal oscillator to permit the timers and
        #               ADC channels to operate. Writing a one activates the oscillator. Writing a zero
        #               disables the oscillator
        tmsg      = "Enable AEN"
        register  = self.CMD + 0x00         # PON + ALS Enable
        readbytes = 1
        data      = [0x03]
        answ      = gglobs.I2CDongle.DongleWriteRead  (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)
        ####################################################################################################################

        # get status
        # Read the Status register until the AVALID bit (Bit #0 in Status) is set
        # The Status Register provides the internal status of the device. This register is read only.
        # AVALID Bit #0  ALS Valid. Indicates that the ADC channels have completed an integration cycle
        # since the AEN bit was asserted.
        tmsg         = "Status"
        start_status = time.time()
        time.sleep(intTime / 1000)          # sleeping for integration time; makes Status=ready on first call
        callcounter = 1
        while True:
            # Status Register (0x13)
            register  = self.CMD + 0x13
            readbytes = 1
            data      = []
            answ      = gglobs.I2CDongle.DongleWriteRead (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)

            if len(answ) == readbytes: answBit0 = answ[0] & 0x01
            else:                      answBit0 = 0

            if answBit0:
                # edprint(fncname + "Data ready")
                break
            else:
                if (time.time() - start_status) > 3 or callcounter > 3:
                    edprint(fncname + "Notbremse - Data not ready after 3 sec or callcounter > 10!")
                    return response         # notbremse nach 5 sec
                time.sleep(0.005)
                cdprint(fncname + "Data not ready in call #{}".format(callcounter))
                callcounter += 1


        # ALS Data Register (0x14 - 0x17)
        tmsg      = "ALS Data"
        register  = self.CMD + 0x14
        readbytes = 4
        data      = []
        answ      = gglobs.I2CDongle.DongleWriteRead  (self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)

        if len(answ) == readbytes:
            visraw = answ[0] | (answ[1] << 8)
            irraw  = answ[2] | (answ[3] << 8)

            # Results were validated for being a good approximation by this
            # normalization over Gain and integration factors
            vis    = visraw  / gainFct / intFct
            ir     = irraw   / gainFct / intFct
            response = vis, ir, visraw, irraw, gainFct, intTime # need visraw for auto function in SensorgetValues

        else:
            # Error: answ too short or too long
            edprint(fncname + "incorrect data, answ: ", answ)
            # response = (gglobs.NAN, ) * 6

        # duration = (time.time() - start) * 1000
        # dataFormat  = "Vis:{:6.5g}, IR:{:6.5g}, RAW-Vis:{:5.0f}, RAW-IR:{:4.0f}, Gain:{:3.0f}, Integ:{} ms"
        # gdprint(fncname + "Init:   " + dataFormat.format(*response) + ", dur:{:0.0f} ms".format(duration))

        return response


    def SensorGetInfo(self):

        info  = "{}\n"                            .format("Ambient Light (Visible, Infrared)")
        info += "- Address:         0x{:02X}\n"   .format(self.addr)
        info += "- ID:              0x{:02X}\n"   .format(self.id)
        info += "- Variables:       {}\n"         .format(", ".join("{}".format(x) for x in gglobs.Sensors["TSL2591"][5]))

        return info.split("\n")


    def SensorReset(self):
        """Reset the sensor to Power-up status"""

        # System reset. When asserted, the device will reset equivalent to a power-on reset.
        # This also clears any Gain and Integ-Time setting!
        # SRESET is self-clearing.
        # Control Register: 0x01
        #
        # IMPORTANT: the System Reset will NOT return an ACK! (observed on both ELV and IOW)
        #
        # duration: ELV: 3.7 ms
        #           ISS: 0.8 ms

        start     = time.time()
        fncname   = "SensorReset: "

        tmsg      = "Reset"
        register  = self.CMD + 0x01     # Control call
        readbytes = 1
        data      = [0x80]              # System Reset, AGAIN=00, ATIME=000
        answ      = gglobs.I2CDongle.DongleWriteRead(self.addr, register, readbytes, data, addrScheme=1, msg=tmsg)

        duration = 1000 * (time.time() - start)

        return fncname + "Done in {:0.1f} ms".format(duration)
