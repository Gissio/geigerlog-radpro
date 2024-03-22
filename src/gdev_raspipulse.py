#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gdev_raspipulse.py  - GeigerLog device for counting pulses on Raspi interrupts

include in programs with:
    import gdev_raspipulse
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


def initRaspiPulse():
    """Inititalize the pulse counter"""

    global RaspiRevision, RaspiGPIOVersion, GPIO

    fncname   = "initRaspiPulse: "

    # is it a Raspi?
    gglobs.isRaspi = is_raspberrypi()

    # configuration device
    # if gglobs.RaspiPulseVariables   == "auto": gglobs.RaspiPulseVariables   = "CPM, CPS, Temp, Press, Humid, Xtra"   # all available
    if gglobs.RaspiPulseVariables   == "auto": gglobs.RaspiPulseVariables   = "CPM, CPS"

    # configuration Raspi hardware
    if gglobs.RaspiPulseMode        == "auto": gglobs.RaspiPulseMode        = "BCM"      # numbering mode: options are: GPIO.BCM or GPIO.BOARD
    if gglobs.RaspiPulsePin         == "auto": gglobs.RaspiPulsePin         = 17         # hardware pin for interrupt in BCM numbering: bcmpin=17 is on boardpin=11
    if gglobs.RaspiPulseEdge        == "auto": gglobs.RaspiPulseEdge        = "RISING"   # register transistion from 0 to 3.3V; options are "GPIO.RISING" or "GPIO.FALLING"
    if gglobs.RaspiPulsePullUpDown  == "auto": gglobs.RaspiPulsePullUpDown  = "PUD_DOWN" # Pull-Down resistor; options are "GPIO.PUD_DOWN" or "GPIO.PUD_UP"

    setLoggableVariables("RaspiPulse", gglobs.RaspiPulseVariables)

    gglobs.Devices["RaspiPulse"][VNAME] = gglobs.Devices["RaspiPulse"][VNAME][0:6]       # limit to no more than 6 variables

    # reset RaspiPulse
    resetRaspiPulse("init")

    if gglobs.isRaspi:
        # it is a Raspi
        simul = ""
        try:
            import RPi.GPIO as GPIO

        except ImportError as ie:
            # module 'RPi.GPIO' not found
            msg  = "The module 'RPi.GPIO' was not found but is required."
            msg += "\nInstall with: 'python3 -m pip install -U RPi.GPIO'"
            exceptPrint(ie, msg)
            return msg

        except Exception as e:
            # module 'RPi.GPIO' was found, but cannot be run
            msg = "Failure on Importing 'RPi.GPIO'"
            exceptPrint(e, msg)
            return msg

        gglobs.RaspiPulseHasGPIO = True
        gglobs.Devices["RaspiPulse"][DNAME] = "Raspi Pulse GPIO"

        RaspiRevision    = GPIO.RPI_INFO['P1_REVISION']
        RaspiGPIOVersion = GPIO.VERSION

        R_Pin    = gglobs.RaspiPulsePin
        R_Mode   = GPIO.BCM      if gglobs.RaspiPulseMode       == "BCM"        else GPIO.BOARD
        R_Edge   = GPIO.RISING   if gglobs.RaspiPulseEdge       == "RISING"     else GPIO.FALLING
        R_PUD    = GPIO.PUD_DOWN if gglobs.RaspiPulsePullUpDown == "PUD_DOWN"   else GPIO.PUD_UP

        GPIO.setmode         (R_Mode)
        GPIO.setup           (R_Pin,    GPIO.IN,    pull_up_down=R_PUD)

        # for each count 1 timestamp entry into deque (with / without bouncetime)
        # GPIO.add_event_detect(R_Pin,    R_Edge,     callback=recordCount)               # without bouncetime
        GPIO.add_event_detect(R_Pin,    R_Edge,     callback=recordCount, bouncetime=1)   # with 1 ms bouncetime

    else:
        # it is NOT a Raspi
        simul = "SIM"
        gglobs.RaspiPulseHasGPIO = False
        gglobs.Devices["RaspiPulse"][DNAME] = "RaspiPulse SIMULATION-ONLY (Poisson distribution data)"

        RaspiRevision       = "(Not a Raspi)"
        RaspiGPIOVersion    = "(Not a Raspi)"

        fprintInColor("INFO: A Raspi was NOT found. This is only a simulation!", "blue")


    gglobs.Devices["RaspiPulse"][CONN] = True

    dprint("Pulse Settings:")
    dprint("   {:27s} : {}".format("Raspi Hardware Revision", RaspiRevision))
    dprint("   {:27s} : {}".format("Raspi SW GPIO Version"  , RaspiGPIOVersion))
    dprint("   {:27s} : {}".format("Pulse Mode"             , gglobs.RaspiPulseMode))
    dprint("   {:27s} : {}".format("Pulse BCM Pin #"        , gglobs.RaspiPulsePin))
    dprint("   {:27s} : {}".format("Pulse Pull up / down"   , gglobs.RaspiPulsePullUpDown))
    dprint("   {:27s} : {}".format("Pulse Edge detection"   , gglobs.RaspiPulseEdge))

    return simul


def terminateRaspiPulse():
    """shuts down the pulse counter; cleanup is important!"""

    fncname = "terminateRaspiPulse: "
    dprint(fncname)
    setIndent(1)

    if gglobs.RaspiPulseHasGPIO:
        try:
            GPIO.cleanup()
        except Exception as e:
            exceptPrint(e, "Failure in GPIO.cleanup")

    gglobs.Devices["RaspiPulse"][CONN] = False

    dprint(fncname + "Terminated")
    setIndent(0)


def recordCount(bcmpin):
    """append a new record to the deque"""

    gglobs.RaspiPulseCountDeque.append(time.time())
    gglobs.RaspiPulseCountTotal += 1


def getValuesRaspiPulse(varlist):
    """get the data from Pulse"""

    ##############################################
    def fudgeSomeDataForRaspiSim(stime):
        """since NOT a Raspi create a CountRecord of time in exponenetial distribution"""

        tt    = stime - (gglobs.logCycle * 1.1)
        mean  = 8                                      # CPS=8
        rmean = 1 / mean
        while tt <= stime:
            tt += np.random.exponential(rmean)          # gap between two pulse starts in sec
            gglobs.RaspiPulseCountDeque.append(tt)      # indicates 1 count at time tt
            gglobs.RaspiPulseCountTotal += 1


    def getRaspiPulseCPS():
        """get CPS counts and return as value"""

        last   = time.time()
        counts = 0
        vtimeL = last - 1      # left time
        vtimeR = last          # right time
        while True:            # find the left limit
            try:                    crp = gglobs.RaspiPulseCountDeque.popleft()
            except Exception as e:  return gglobs.NAN
            if crp > vtimeL:
                counts += 1
                break

        while True: # find the right limit
            try:                    crp = gglobs.RaspiPulseCountDeque.popleft()
            except Exception as e:  break

            if crp <= vtimeR :      counts += 1
            else:                   break

        gglobs.RaspiPulseCPMDeque.append(counts)

        return counts


    def getRaspiPulseCPM():
        """get CPM counts and return as value"""

        CPM = 0
        for i in range(60):
            CPM += gglobs.RaspiPulseCPMDeque[i]

        return CPM


    def getValueRaspiPulse(index):
        """get the values for the sequence of variables"""

        # from the config (now changed for only CPS, CPM)
        # The RaspiPulse Device can only count pulses, but can provide variables:
        #     CPS           counts in 1 sec (the raw data)
        #     CPM           sum of CPS over the last 60 sec
        #     runtime       number of seconds since start or last reset
        #     totalcount    number of counts since start or last reset

        gib = 2**30
        if   index == 0: val = getRaspiPulseCPS()                       # CPS               --> CPS3rd
        elif index == 1: val = getRaspiPulseCPM()                       # CPM               --> CPM3rd
        # # elif index == 2: val = psutil.cpu_percent()                     # % CPU Usage       --> Temp
        # #       So, for instance, a value of 3.14 on a system with 10 logical CPUs
        # #       means that the system load was 31.4% percent over the last N minutes.
        # elif index == 2: val = psutil.getloadavg()[0]                   # % CPU Load Avg    --> Temp        last 1 min
        # elif index == 3: val = psutil.virtual_memory().percent          # % Mem Usage       --> Press
        # elif index == 4: val = gglobs.RaspiPulseCountTotal              # Total Pulses      --> Humid
        # # elif index == 4: val = psutil.virtual_memory().total / gib      # Mem in GiB      --> Humid       Raspi 1.806 Gib, urkam: 31.29 Gib
        # elif index == 5: val = deltatcycle                              # len log cycle (s) --> Xtra        better 1 +/- 10%
        else:            val = gglobs.NAN

        return val
    ##############################################

    start   = time.time()
    fncname = "getValuesRaspiPulse: "
    alldata = {}  # dict for return data

    if gglobs.RaspiPulseLastCycleStart is None: gglobs.RaspiPulseLastCycleStart = gglobs.LogThreadStartTime

    deltatcycle = start - gglobs.RaspiPulseLastCycleStart
    gglobs.RaspiPulseLastCycleStart = start

    if (gglobs.logCycle * 0.9) < deltatcycle < (gglobs.logCycle * 1.1):
        # cycle length is with 10% of logCycle
        if not gglobs.isRaspi: fudgeSomeDataForRaspiSim(start)  # NOT a Raspi, go fudge some data
        newvarlist = [varlist[1]] + [varlist[0]] + varlist[2:]  # flip order of vars CPM & CPS so that CPS is calculated first
        for i, vname in enumerate(newvarlist):
            getval = getValueRaspiPulse(i)
            alldata.update({vname: getval})
            # gdprint(fncname + "i={}, vname={}, getValueRaspiPulse={}".format(i, vname, getval))
    else:
        rdprint("Data rejected - a cycle of {:0.3f} sec is outside tolerated range of +/- 10% to logcycle {} sec".format(deltatcycle, gglobs.logCycle))

    vprintLoggedValues(fncname, varlist, alldata, (time.time() - start) * 1000)

    return alldata


def getInfoRaspiPulse(extended=False):
    """Info on the RaspiPulse Device"""

    Info          = "Configured Connection:        GeigerLog RaspiPulse Device\n"

    if not gglobs.Devices["RaspiPulse"][CONN]:
        Info     += "<red>Device is not connected</red>"
    else:
        Info     += "Connected Device:             {}\n".format(gglobs.Devices["RaspiPulse"][DNAME])
        Info     += "Configured Variables:         {}\n".format(gglobs.RaspiPulseVariables)
        Info     += getTubeSensitivities(gglobs.RaspiPulseVariables)

        if extended:
            Info += "\n"
            Info += "Raspi\n"
            Info += "   Hardware Revision          {}\n".format(RaspiRevision)
            Info += "   Software GPIO Version      {}\n".format(RaspiGPIOVersion)
            Info += "Configured Raspi GPIO settings:\n"
            Info += "   Pulse Mode:                {}\n".format(gglobs.RaspiPulseMode)
            Info += "   Pulse BCM Pin No:          {}\n".format(gglobs.RaspiPulsePin)
            Info += "   Pulse Pull up / down:      {}\n".format(gglobs.RaspiPulsePullUpDown)
            Info += "   Pulse Edge detection:      {}\n".format(gglobs.RaspiPulseEdge)

    return Info


def resetRaspiPulse(cmd = ""):
    """resets device RaspiPulse"""

    fncname  = "resetRaspiPulse: "

    setBusyCursor()

    gglobs.RaspiPulseCountTotal     = 0
    gglobs.RaspiPulseCPMDeque       = deque([gglobs.NAN] * 60, 60)  # 60 NANs, len=60, space for 60 sec CPS data, CPM only after 60 sec
    gglobs.RaspiPulseCountDeque     = deque([])                     # empty; unlimited size
    gglobs.RaspiPulseLastCycleStart = None                          # does it need resetting?

    if cmd != "init":
        fprint(header("Resetting RaspiPulse"))
        fprint ("Successful")

    setNormalCursor()

