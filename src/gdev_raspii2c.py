#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
gdev_raspii2c.py - GeigerLog device to be used on Raspi for I2C

include in programs with:
    import gdev_raspii2c.py
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

from   gsup_utils  import *


def initRaspiI2C():
    """Initialize I2C"""

    global RaspiRevision, RaspiGPIOVersion, GPIO

    fncname   = "initRaspiI2C: "

    # configuration device
    if gglobs.RaspiI2CVariables   == "auto": gglobs.RaspiI2CVariables   = "Temp, Press"     # everything available (Press=Avg(T)

    # configuration I2C hardware
    if gglobs.RaspiI2CAdress      == "auto": gglobs.RaspiI2CAdress      = 0x48              # default address

    setLoggableVariables("RaspiI2C", gglobs.RaspiI2CVariables)

    gglobs.Devices["RaspiI2C"][VNAME] = gglobs.Devices["RaspiI2C"][VNAME][0:2]              # no more than 2 variables

    # is it a raspberrypi?
    gglobs.isRaspi = is_raspberrypi()

    if gglobs.isRaspi:
        # I2C on Raspi
        simul = ""
        try:
            import smbus
        except ImportError as ie:
            msg  = "The module 'smbus' could not be imported, but is required."
            exceptPrint(ie, msg)
            msg  = "\n\n" + msg + "\nOn Raspberry Pi install with: 'sudo apt install Python-smbus'."
            msg += "\nOn other computers install with 'python3 -m pip install -U smbus'."
            return msg
        except Exception as e:
            msg = str(e)
            exceptPrint(e, "")
            return msg

        try:
            import RPi.GPIO as GPIO
        except ImportError as ie:
            msg  = "The module 'RPi.GPIO' could not be imported, but is required."
            exceptPrint(ie, msg)
            msg  = "\n\n" + msg + "\nOn Raspberry Pi install with: 'sudo apt install python3-rpi.gpio'."
            msg += "\nOn other computers install with 'python3 -m pip install -U RPi.GPIO'."
            return msg
        except Exception as e:
            msg = str(e)
            exceptPrint(e, "")
            return msg


        # initialize I2C-Bus
        gglobs.RaspiI2CHandle   = smbus.SMBus(1)
        gglobs.Devices["RaspiI2C"][DNAME] = "Raspi I2C {}".format(gglobs.RaspiI2CSensor)

        RaspiRevision    = GPIO.RPI_INFO['P1_REVISION']
        RaspiGPIOVersion = GPIO.VERSION

    else:
        # NOT on Raspi; simulation only
        simul = "SIM"
        gglobs.RaspiI2CHandle   = None
        gglobs.Devices["RaspiI2C"][DNAME] = "RaspiI2C SIMULATION-ONLY (Normal distribution data)"

        RaspiRevision       = "(Not a Raspi)"
        RaspiGPIOVersion    = "(Not a Raspi)"

        fprintInColor("INFO: A Raspi was NOT found. This is only a simulation!", "blue")


    dprint("I2C Settings:")
    dprint("   {:27s} : {}".format("I2C Sensor"                 , gglobs.RaspiI2CSensor))
    dprint("   {:27s} : {}".format("I2C Sensor Register"        , gglobs.RaspiI2CSensorRegister))

    gglobs.Devices["RaspiI2C"][CONN] = True

    # resetRaspiI2C()                                           # reset all datapoints
    resetRaspiI2C("init")

    gglobs.RaspiI2CThreadStopFlag = False
    gglobs.RaspiI2CThread         = threading.Thread(target = RaspiI2CThreadTarget)
    gglobs.RaspiI2CThread.daemon  = True
    gglobs.RaspiI2CThread.start()

    dprint("   {:27s} : {}".format("RaspiI2CThread.daemon"      , gglobs.RaspiI2CThread.daemon))
    dprint("   {:27s} : {}".format("RaspiI2CThread.is_alive"    , gglobs.RaspiI2CThread.is_alive()))

    return simul


def terminateRaspiI2C():
    """closes I2C handle"""

    fncname = "terminateRaspiI2C: "
    dprint(fncname)
    setIndent(1)

    gglobs.RaspiI2CThreadStopFlag = True

    if gglobs.RaspiI2CHandle is not None:
        try:
            gglobs.RaspiI2CHandle.close()
        except Exception as e:
            msg = "I2C connection is not available"
            exceptPrint(e, msg)

    gglobs.Devices["RaspiI2C"][CONN] = False

    dprint(fncname + "Terminated")
    setIndent(0)


def RaspiI2CThreadTarget():
    """The Target function for the RaspiI2C thread"""

    fncname  = "RaspiI2CThreadTarget: "

    nexttime = time.time() + 0.01                                   # allows to skip first 10 msec to let printouts finish
    while not gglobs.RaspiI2CThreadStopFlag:
        if time.time() >= nexttime:
            nexttime += 1
            if gglobs.RaspiI2CHandle is None:
                # NOT running on the Raspi, just fudge some normal random numbers
                Temp = np.random.normal(33, 0.5)
            else:
                # running on Raspi
                Temp = getRaspiTempLM75B()

            gglobs.RaspiI2CTempDeque.append(Temp)    # advance the position for storing value, or shift left when full

        time.sleep(0.010)                            # gives a 10 ms precision of calling the log call


def getRaspiTempLM75B():
    """get Temp from Raspi I2C connected LM75B"""

    # NOTE: TIMINGS
    # on Raspi: read_i2c_block_data ( 2 bytes):  < 0.6 ms
    # on Raspi: read_i2c_block_data (32 bytes):  < 8.0 ms

    fncname = "getRaspiTempLM75B: "

    try:
        # read 2 bytes (2 must be given or it will return 32 bytes!)
        raw = gglobs.RaspiI2CHandle.read_i2c_block_data(gglobs.RaspiI2CAdress, gglobs.RaspiI2CSensorRegister, 2)
    except Exception as e:
        exceptPrint(e, "Raspi I2C Reading failed")
        return gglobs.NAN

    msb, lsb = raw
    temp1    = ((msb << 8 | lsb ) >> 5)            # assuming LM75B with 11bit Temp resolution
    if temp1 & 0x400: temp1 = temp1 - 0x800        # 0x400 == 0b0100 0000 0000 == 1024, 0x800 == 0b1000 0000 0000 == 2048
    Temp     = temp1 * 0.125                       # deg Celsius for LM75B; +/- 128°C @11 bit => 0.125 °C per step

    return Temp


def getValuesRaspiI2C(varlist):
    """get the values. only first 2 variables get values"""

    ##############################################
    def getLastData():
        """Last recorded value"""

        return gglobs.RaspiI2CTempDeque[-1]


    def getLastAvg():
        """Last 1 min average"""

        AvgTemp = 0
        lenDT   = len(gglobs.RaspiI2CTempDeque)
        for i in range(lenDT): AvgTemp += gglobs.RaspiI2CTempDeque[i]
        return AvgTemp / lenDT


    def getValueRaspiI2C(index):

        if   index == 0:  val = getLastData()                  # Temperature
        elif index == 1:  val = getLastAvg()                   # Average Temperature
        else:             val = gglobs.NAN

        return val
    ##############################################

    start   = time.time()
    fncname = "getValuesRaspiI2C: "
    alldata = {}                        # dict for return data

    for i, vname in enumerate(varlist):
        getval = getValueRaspiI2C(i)
        alldata.update({vname: getval})
        # gdprint(fncname + "i={}, vname={}, getValueRaspiI2C={}".format(i, vname, getval))

    vprintLoggedValues(fncname, varlist, alldata, (time.time() - start) * 1000)

    return alldata


def getInfoRaspiI2C(extended=False):
    """Info on the RaspiI2C Device"""

    Info =          "Configured Connection:        GeigerLog RaspiI2C Device\n"

    if not gglobs.Devices["RaspiI2C"][CONN]:
        Info +=     "<red>Device is not connected</red>"
    else:
        Info +=     "Connected Device:             {}\n".format(gglobs.Devices["RaspiI2C"][DNAME])
        Info +=     "I2C Sensor:                   {}\n".format(gglobs.RaspiI2CSensor)
        Info +=     "Configured Variables:         {}\n".format(gglobs.RaspiI2CVariables)
        Info +=     getTubeSensitivities(gglobs.RaspiI2CVariables)

        if extended:
            Info += "\n"
            Info += "Raspi\n"
            Info += "   Hardware Revision          {}\n".format(RaspiRevision)
            Info += "   Software GPIO Version      {}\n".format(RaspiGPIOVersion)

            Info += "Configured I2C Sensor Settings:\n"
            Info += "   I2C Address:               {}\n".format(hex(gglobs.RaspiI2CAdress))

    return Info


def resetRaspiI2C(cmd = ""):
    """resets I2C device by emptying the deque"""
    # NOTE: quiet on cmd=="init"

    fncname  = "resetRaspiI2C: "

    setBusyCursor()

    gglobs.RaspiI2CTempDeque = deque([], 60)                    # reset all datapoints; space for 60 sec data

    if gglobs.RaspiI2CHandle is None:
        # NOT running on the Raspi, just fudge some normal random numbers
        Temp = np.random.normal(33, 0.5)
    else:
        # running on Raspi
        Temp = getRaspiTempLM75B()

    gglobs.RaspiI2CTempDeque.append(Temp)

    if cmd != "init":
        fprint(header("Resetting RaspiI2C"))
        fprint ("Successful")

    setNormalCursor()

