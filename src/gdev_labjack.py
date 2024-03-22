#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
gdev_labjack.py - GeigerLog commands to handle the LabJack U3 device

NOTE: verfied to work on Linux; it may work on Mac
      Not working on Windows, which needs a different installation of Exodriver
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
For LabJack Python support from LabJack company see:
    https://labjack.com/support/software/examples/ud/labjackpython

INSTALLATIONS:
To use this device you need the installation of:
- the so called Exodriver
- the Python module: LabJackPython.py
- the Python module: u3.py
- the Python module: ei1050.py (needed only if external probe EI1050 is used)

- Exodriver -- Linux-only:
    The Exodriver is here: https://labjack.com/support/software/installers/exodriver
    The latest version is 2.6.0, compatible with Linux kernels from 2.6.28 onwards.
    The exodriver is stored as: /usr/local/lib/liblabjackusb.so.

- LabJackPython and
- u3:
    LabJackPython is needed in the version 2.0.0 (Jan 2019) or later. Latest
    version is 2.0.4 from September 9, 2020 (status Feb 2021).
    u3 is part of LabJackPython, it will be automatically installed with it.

    Downloadable from: https://labjack.com/support/software/examples/ud/labjackpython,
    but preferably the modules are installed via pip:
        python3 -m pip install -U LabJackPython
    On my Python Virtual instllations 'u3.py' is located at: (X= 6,7,8,9,10)
    ~/geigerlog/vgl3X/lib/python3.X/site-packages/u3.py

- ei1050.py:
    https://github.com/labjack/LabJackPython/tree/master/Examples/EI1050
    A usage example: https://forums.labjack.com/index.php?showtopic=5804
    A threading example:
    https://github.com/labjack/LabJackPython/blob/master/Examples/EI1050/ei1050SampleApp.py

NOTE:
    For detection of a busy LabJack see my discussion "Detecting the presence of
    an U3 even when in use elsewhere" at: https://labjack.com/comment/6040

###############################################################################
WIRING REQUIREMENTS:
###############################################################################
VOLTAGES:

Connections to be made for measuring voltages with the LabJack U3:
Use LJTick-Divider(type 4), which extends the permitted voltages to +0 ... +10V,
and connect each voltage between VINA and GND, and VINB and GND, resp.

###############################################################################
EI1050 PROBE for TEMPEARTURE and HUMIDITY

EI1050 has 5 wires in the colors brown, red, white, green, black.
Make connections between EI1050 and LabJack U3:

EI1050      U3
Color:      Pin:
----------------
brown       FIO7
red         FIO7 (same as brown)
white       FIO5
green       FIO4
black       GND

###############################################################################
CONNECTING an LED

will be lit for the duration of a LabJack measurment cycle
A current limiting resistor is not necessary as the pins are current limited

LED: connect between GND (short lead) and FIO7 (long lead)

###############################################################################
GeigerLog configuration
###############################################################################
EXAMPLE mapping and Extended Info output beginning with GeigerLog 1.2.2:

==== Device Mappings =================================================================
The configuration is determined in the configuration file geigerlog.cfg. The
full mapping looks like this:
Note: EI1050 is not connected

Device      :  CPM    CPS    CPM1st CPS1st CPM2nd CPS2nd CPM3rd CPS3rd   T   P   H   X
--------------------------------------------------------------------------------------
LabJack     :  X      X      X      X      X      X      X      X        X   -   X   X
Mapping is valid

==== LabJack Device Extended =========================================================
Configured Connection:        USB (auto-configuration)
Connected Device:             'LabJack U3B'
Connected Probe (Status):     EI1050 (Probe EI1050 not readable)
Connection:                   USB
Configured Variables:         CPM, CPS, CPM1st, CPS1st
LabJack Software Versions:
--- LabJackPython                : 2.0.4
--- U3                           : undefined
--- EI1050                       : ei1050_local
LabJack Config:
--- FirmwareVersion              : 1.54
--- BootloaderVersion            : 0.11
--- HardwareVersion              : 1.21
--- ProductID                    : 3
--- LocalID                      : 2
--- TimerCounterMask             : 0
--- FIOAnalog                    : 255
--- FIODirection                 : 0
--- FIOState                     : 0
--- EIOAnalog                    : 255
--- EIODirection                 : 0
--- EIOState                     : 0
--- CIODirection                 : 0
--- CIOState                     : 0
--- DAC1Enable                   : 0
--- DAC0                         : 0
--- DAC1                         : 0
--- TimerClockConfig             : 0
--- TimerClockDivisor            : 256
--- CompatibilityOptions         : 0
--- VersionInfo                  : 1
--- DeviceName                   : U3B
###############################################################################
"""

from   gsup_utils       import *

import ctypes
try:
    l = ctypes.CDLL("liblabjackusb.so", use_errno=False)            # errno False/True: no effect seen
    # gdprint("gdev_labjack.py - " + "LabJack driver is installed: ", l)
    foundDriver = True
except Exception as e:
    exceptPrint(e, "ctypes.CDLL(liblabjackusb.so errno=false")
    foundDriver = False

if foundDriver:
    try:
        import LabJackPython                        # see installation instructions above
        gglobs.LJimportLJP = True
    except Exception as e:
        exceptPrint(e, "")

    try:
        import u3                                   # u3 is part of LabJackPython
        gglobs.LJimportU3 = True
    except Exception as e:
        exceptPrint(e, "")

    try:
        import ei1050                               # is made to be part of GeigerLog
        gglobs.LJimportEI1050 = True
    except Exception as e:
        # it fails when u3 module is not importable
        exceptPrint(e, "EI1050 import failed on importing U3")



def initLabJack():
    """Initialize LabJack U3 (with probe EI1050 if activated)"""

    global LJdevice, LJprobe, targetQueue, thread

    fncname = "initLabJack: "
    dprint(fncname + "Initializing LabJack on Linux")

    if 'linux' not in sys.platform:             # Py3:'linux', Py2:'linux2'
        msg = "LabJack is currently supported only on Linux."
        return msg

    if not foundDriver:
        msg  = "LabJack driver 'liblabjackusb.so' was not found.\n"
        msg += "This is required to run LabJack. Is it installed?"
        return msg

    # LabJackPython
    if not gglobs.LJimportLJP:
        msg  = "Python module 'LabJackPython' was not found.\n"
        msg += "To run a LabJack U3 device this module is required.\n"
        msg += "Verify that 'LabJackPython' is installed using GeigerLog tool: 'GLpipcheck.py'."
        return msg
    else:
        gdprint("   " + fncname + "Python module 'LabJackPython' is installed")
        gglobs.versions["LabJackPython"]  = LabJackPython.__version__


    # rdprint("LabJackPython.staticLib: ", LabJackPython.staticLib)

    # U3
    if not gglobs.LJimportU3:
        msg  = "Python module 'U3' was not found, which is part of 'LabJackPython'.\n"
        msg += "To run a LabJack U3 device this module is required.\n"
        msg += "Reinstall 'LabJackPython', see GeigerLog tool: 'GLpipcheck.py'."
        return msg
    else:
        gdprint("   " + fncname + "Python module 'U3' is installed")
        gglobs.versions["U3"]           = "version undefined"    # this has no version!

    # EI1050
    # check only if the EI1050 use is configured for use
    if gglobs.LJEI1050Activation:
        if not gglobs.LJimportEI1050:
            msg  = "Python module 'ei1050' was not found.\n"
            msg += "You can run LabJack without this probe by setting 'LJEI1050Activation = no'\n"
            msg += "in the GeigerLog configuration file, but then will not be able to record\n"
            msg += "the Temperature and Humidity values provided by this probe."
            return msg
        else:
            gdprint("   " + fncname + "Python module 'EI1050' is installed")
            gglobs.versions["EI1050"]   = ei1050.__version__

    setIndent(1)

    # List All paramter for device type 3: LabJackPython.listAll(3)
    # this shows only an empty dict after LJdevice = u3.U3() command,
    # and back to original data after a LJdevice.close() command!
    cdprint(fncname + "LabJackPython.listAll(3):")
    try:
        listAll = LabJackPython.listAll(3)
    except Exception as e:
        exceptPrint(e, "listAll(3)")
        msg  = "The Exodriver required for LabJack appears to be missing."
        setIndent(0)
        return msg

    # print the list
    if len(listAll) > 0:
        for a in listAll:
            for aa in listAll[a]:
                cdprint("   {:20s}  '{}'".format(aa, listAll[a][aa]))
        cdprint("")
    else:
        cdprint(fncname + "   list is empty")

    # open the device
    # IMPORTANT: first detach from USB in case it is still attached
    try:    LJdevice.close()
    except: pass

    try:
        LJdevice = u3.U3()
        #LJdevice.debug = True
    except Exception as e:
        exceptPrint(e, "@ LJdevice = u3.U3()")
        stre = str(e)
        if   "Couldn't open device. Please check that the device you are trying to open is connected." in stre:
            errmsg = "No LabJack device found."
        elif "Couldn't open device. Device access or claim error" in stre:
            errmsg = "A LabJack device was found, but it may already be in use by a different program."
        elif "name 'u3' is not defined" in stre:
            errmsg = "Failure loading LabJack driver 'u3'. Please, check installation."
        else:
            errmsg = "Connecting to LabJack device gave unexpected error: {}".format(stre)

        edprint(fncname + "ERROR: U3 exception: " + errmsg)

        gglobs.Devices["LabJack"][CONN] = False
        setIndent(0)

        return errmsg

    # Finally, all is well

    gglobs.Devices["LabJack"][DNAME] = "LabJack" + " " + LJdevice.configU3()["DeviceName"]

    if gglobs.LJEI1050Activation and gglobs.LJimportEI1050:
        targetQueue = queue.Queue()
        thread  = ei1050.EI1050Reader(LJdevice, targetQueue)
        thread.start()
        LJprobe = ei1050.EI1050(LJdevice)

    if gglobs.LJVariables  == "auto":   gglobs.LJVariables = "Temp, Humid, Xtra"
    setLoggableVariables("LabJack", gglobs.LJVariables)

    setEI1050Status()
    cdprint(fncname + "Calibration data")
    myCalData = LJdevice.getCalibrationData()
    if gglobs.verbose:
        for key, val in myCalData.items(): cdprint("   {:22s} : {}".format(key, val))


    # configure LabJack for IO-Type, IO-direction, DACs, etc
    cdprint(fncname + "configureLabJack")

    # U3:
    LJdevice.configU3(DAC1Enable = 1) # hmmmm scheint keine Wirkung zu haben
    #LJdevice.configU3(DAC1Enable = 0) # hmmmm

    #~LJdevice.getFeedback(u3.DAC0_8(Value = 0x33))
    #~LJdevice.getFeedback(u3.DAC0_8(Value = 76))
    LJdevice.getFeedback(u3.DAC0_8(Value = 0))
    LJdevice.getFeedback(u3.DAC1_8(Value = 0))

    #~LJdevice.configIO(FIOAnalog = 0b00001111)         # set lower 4 FIO pin to analog, upper 4 to digital
    LJdevice.configIO(FIOAnalog = 0b11001111)           # set lower 4 FIO pin to analog, next 2 to digital, final 2 to analog

    # show config
    for key, val in LJdevice.configIO().items():
        cdprint("   {:22s} : {:4d}  {:#010b}".format(key, val, val))

    # EI1050 probe
    # There are no settings for the EI1050 probe


    gglobs.Devices["LabJack"][CONN] = True
    getValuesLabJack(gglobs.Devices["LabJack"][1])      # do a first read (data may not be settled)

    setIndent(0)

    return ""


def terminateLabJack():
    """opposit of init ;-)"""

    #global LJdevice, LJprobe, targetQueue, thread # is thread needed here?

    fncname = "terminateLabJack: "

    dprint(fncname)
    setIndent(1)

    if gglobs.LJEI1050Activation and gglobs.LJimportEI1050:
        try:
            thread.stop()
            thread.join()       # ???
        except Exception as e:
            exceptPrint(fncname + str(e), "Stopping LabJack thread EI1050 failed")

    if gglobs.Devices["LabJack"][CONN] :
        LJdevice.close()                    # important to detach from USB  !!!
        gglobs.Devices["LabJack"][CONN]   = False

    dprint(fncname + "Terminated")
    setIndent(0)


# # def setLabJackSettings(a = 0, b = 0, c = 0):
# def setLabJackSettings():
#     """Set Settings ... at the LabJack Device"""

#     fncname = "setLabJackSettings: "
#     cdprint(fncname)

#     # U3:
#     LJdevice.configU3(DAC1Enable = 1) # hmmmm scheint keine Wirkung zu haben
#     #LJdevice.configU3(DAC1Enable = 0) # hmmmm

#     #~LJdevice.getFeedback(u3.DAC0_8(Value = 0x33))
#     #~LJdevice.getFeedback(u3.DAC0_8(Value = 76))
#     LJdevice.getFeedback(u3.DAC0_8(Value = 0))
#     LJdevice.getFeedback(u3.DAC1_8(Value = 0))

#     #~# set lower 4 FIO pin to analog, upper 4 to digital
#     #~LJdevice.configIO(FIOAnalog = 0b00001111)

#     # set lower 4 FIO pin to analog, next 2 to digital, final 2 to analog
#     LJdevice.configIO(FIOAnalog = 0b11001111)

#     # show config
#     for key, val in LJdevice.configIO().items(): cdprint("   {:22s} : {:4d}  {:#010b}".format(key, val, val))

#     # EI1050 probe
#     # There are no settings for the EI1050 probe


def getInfoLabJack(extended = False):
    """Info on the LabJack Device"""

    fncname = "getInfoLabJack: "

    LJInfo      = "Configured Connection:        USB (auto-configuration)\n"

    if not gglobs.Devices["LabJack"][CONN]: return LJInfo + "<red>Device is not connected</red>"

    LJInfo     += "Connected Device:             {}\n".format(gglobs.Devices["LabJack"][DNAME])
    if gglobs.LJEI1050Activation:
        LJInfo += "Connected Probe:              {} (Status: {})\n".format("EI1050", gglobs.LJEI1050status)
    else:
        LJInfo += "Connected Probe:              Not activated\n"
    LJInfo     += "Configured Variables:         {}\n".format(gglobs.LJVariables)

    if extended == True:
        LJInfo += "\nLabJack Software Versions:\n"
        # LJInfo += "--- {:28s} : {}\n".format("LabJackPython", gglobs.LJversionLJP)
        # LJInfo += "--- {:28s} : {}\n".format("U3",            gglobs.LJversionU3)
        # LJInfo += "--- {:28s} : {}\n".format("EI1050",        gglobs.LJEI1050version)
        LJInfo += "--- {:28s} : {}\n".format("LabJackPython", gglobs.versions["LabJackPython"])
        LJInfo += "--- {:28s} : {}\n".format("U3",            gglobs.versions["U3"])
        LJInfo += "--- {:28s} : {}\n".format("EI1050",        gglobs.versions["EI1050"])

        LJInfo += "LabJack Config:"
        for key, value in LJdevice.configU3().items():
            LJInfo += "\n--- {:28s} : {}".format(key, value)

        LJInfo += "\nLabJack Calibration:\n"
        CalData = LJdevice.getCalibrationData()
        for key, val in CalData.items():
            #print("   {:22s} : {}".format(key, val))
            LJInfo += "--- {:28s} : {}\n".format(key,        val)

    return LJInfo


def getValuesLabJack(varlist):

    start = time.time()
    fncname = "getValuesLabJack: "
    #print(fncname + "varlist: {}".format(varlist))

    alldata         = {}
    latestReading   = None

    LJdevice.setFIOState(4, 1) # Set FIO #4 output high to switch on LED
    #~LJdevice.getFeedback(u3.LED( True) ) # zu langsam
    #~time.sleep(0.3)

    if gglobs.LJEI1050Activation and gglobs.LJimportEI1050:
        # only Temp, Humid are from EI1050 and are collected in thread
        while not targetQueue.empty():
            try:
                latestReading = targetQueue.get()
            except Exception as e:
                exceptPrint(fncname + str(e), "targetQueue.get() failed")
                latestReading = gglobs.NAN # oder sollte das None sein?

    #if latestReading != None:
    # not tested when EI1050 is present!!!

    for vname in varlist:
        #print(fncname + "------------------------------------vame: ", vname)

    # AIN 0
        if   vname == "CPM":
            CAIN             = 4 * LJdevice.getAIN(0, longSettle=True)
            CAIN             = round(scaleVarValues(vname, CAIN, gglobs.ValueScale[vname]), 3)
            alldata.update({vname: CAIN})

    # AIN 1
        elif vname == "CPS":
            #~ain0Command = u3.AIN(31, 31, True)
            #~print("ain0Command=", ain0Command)
            #~AIN0 = LJdevice.getFeedback( ain0Command )[0]
            #~print("AIN0: ", AIN0, "hex: ", hex(AIN0), "bin: ", bin(AIN0))
            #~Vain0 = LJdevice.binaryToCalibratedAnalogVoltage(AIN0, isLowVoltage = True, isSingleEnded = True)
            #~print("Vain0: ", Vain0, "Vain0 * 4: ", 4 * Vain0)
            #~CAIN = Vain0 #* 4

            CAIN             = 4 * LJdevice.getAIN(1, longSettle=True)
            #CAIN             = LJdevice.getAIN(31, longSettle=True)
            CAIN             = round(scaleVarValues(vname, CAIN, gglobs.ValueScale[vname]), 3)
            alldata.update({vname: CAIN})

            #~vref = LJdevice.getAIN(1, 31, longSettle=True)
            #~print("getAIN(1, 31 vref= ", vref)
            #~vref = LJdevice.getAIN(1, 30, longSettle=True)
            #~print("getAIN(1, 30 vref= ", vref)
            #~vref = LJdevice.getAIN(31, 31, longSettle=True)
            #~print("getAIN(31, 31  vref= ", vref)

    # AIN 2
        elif vname == "CPM1st":
            FIO  = 2
            AIN  = getAIN(FIO)
            CAIN = AIN >> 4

            #CAIN             = 4 * LJdevice.getAIN(2, longSettle=True)
            #CAIN             = round(scaleVarValues(vname, CAIN, gglobs.ValueScale[vname]), 3)
            alldata.update({vname: CAIN})

    # AIN 3
        elif vname == "CPS1st":
            FIO  = 3
            AIN  = getAIN(FIO)
            CAIN = AIN >> 4

            #CAIN             = 4 * LJdevice.getAIN(3, longSettle=True)
            #CAIN             = round(scaleVarValues(vname, CAIN, gglobs.ValueScale[vname]), 3)
            alldata.update({vname: CAIN})

    # AIN 4
    # ist jetzt digital
        #~elif vname == "CPM2nd":
            #~CAIN             = 4 * LJdevice.getAIN(4, longSettle=True)
            #~CAIN             = round(scaleVarValues(vname, CAIN, gglobs.ValueScale[vname]), 3)
            #~alldata.update({vname: CAIN})

    # AIN 5
    # ist jetzt digital
        #~elif vname == "CPS2nd":
            #~CAIN             = 4 * LJdevice.getAIN(5, longSettle=True)
            #~CAIN             = round(scaleVarValues(vname, CAIN, gglobs.ValueScale[vname]), 3)
            #~alldata.update({vname: CAIN})


    # changed association for use with LJTick InAmp
    # AIN 6
        elif vname == "CPM2nd":
            CAIN             = 1 * LJdevice.getAIN(6, longSettle=True)
            #~CAIN             = CAIN / 51 * 1000 # for result in mV
            CAIN             = CAIN * 1000 # for result in mV
            CAIN             = round(scaleVarValues(vname, CAIN, gglobs.ValueScale[vname]), 3)
            alldata.update({vname: CAIN})

    # AIN 7
        elif vname == "CPS2nd":
            FIO  = 6 # usin #6!!
            AIN  = getAIN(FIO)
            CAIN = AIN >> 4

            #~CAIN             = 1 * LJdevice.getAIN(7, longSettle=True)
            #~CAIN             = CAIN / 11
            CAIN             = round(scaleVarValues(vname, CAIN, gglobs.ValueScale[vname]), 3)
            alldata.update({vname: CAIN})

    # AIN 6
        elif vname == "CPM3rd":
            CAIN             = 4 * LJdevice.getAIN(6, longSettle=True)
            CAIN             = round(scaleVarValues(vname, CAIN, gglobs.ValueScale[vname]), 3)
            alldata.update({vname: CAIN})

    # AIN 7
        elif vname == "CPS3rd":
            CAIN             = 4 * LJdevice.getAIN(7, longSettle=True)
            CAIN             = round(scaleVarValues(vname, CAIN, gglobs.ValueScale[vname]), 3)
            alldata.update({vname: CAIN})

    # from the probe EI1050
        elif vname == "Temp":
            Temp             = getEI1050Temperature(latestReading)
            Temp             = round(scaleVarValues(vname, Temp, gglobs.ValueScale[vname]), 3)
            alldata.update({vname: Temp})

    # GET ALL OF THEM
        elif vname == "Press":
            pAIN             = 4 * LJdevice.getAIN(0)
            pAIN             = round(scaleVarValues(vname, pAIN, gglobs.ValueScale[vname]), 3)
            alldata.update({"CPM": pAIN})

            pAIN             = 4 * LJdevice.getAIN(1)
            pAIN             = round(scaleVarValues(vname, pAIN, gglobs.ValueScale[vname]), 3)
            alldata.update({"CPS": pAIN})

            pAIN             = 4 * LJdevice.getAIN(2)
            pAIN             = round(scaleVarValues(vname, pAIN, gglobs.ValueScale[vname]), 3)
            alldata.update({"CPM1st": pAIN})

            pAIN             = 4 * LJdevice.getAIN(3)
            pAIN             = round(scaleVarValues(vname, pAIN, gglobs.ValueScale[vname]), 3)
            alldata.update({"CPS1st": pAIN})

            pAIN             = 4 * LJdevice.getAIN(4)
            pAIN             = round(scaleVarValues(vname, pAIN, gglobs.ValueScale[vname]), 3)
            alldata.update({"CPM2nd": pAIN})

            pAIN             = 4 * LJdevice.getAIN(5)
            pAIN             = round(scaleVarValues(vname, pAIN, gglobs.ValueScale[vname]), 3)
            alldata.update({"CPS2nd": pAIN})

    # from the probe EI1050
        elif vname == "Humid":
            Hum              = getEI1050Humidity(latestReading)
            Hum              = round(scaleVarValues(vname, Hum,  gglobs.ValueScale[vname]), 3)
            alldata.update({vname: Hum})

    # from the U3 internal Temp sensor
        elif vname == "Xtra":
            u3it             = getLJinternalTemperature()
            u3it             = round(scaleVarValues(vname, u3it, gglobs.ValueScale[vname]), 3)
            alldata.update({vname: u3it})


    LJdevice.setFIOState(4, 0) # Set FIO #4 output low to switch off LED
    #~LJdevice.getFeedback(u3.LED( False) )

    stop = time.time()
    vprintLoggedValues(fncname, varlist, alldata, (stop - start) * 1000)

    return alldata


def getAIN(FIO):

    ainCommand = u3.AIN(FIO, 31, True)
    #print("ain0Command=", ain0Command)
    AIN   = LJdevice.getFeedback(ainCommand)[0]
    AINs4 = AIN >> 4
    VAIN  = LJdevice.binaryToCalibratedAnalogVoltage(AIN, isLowVoltage = True, isSingleEnded = True)
    print("#{} AIN:{:5d} hex:{:4X}    AINs4:{:5d}  hex:{:4X}    VAIN:{:5.3f},  VAIN*4:{:5.3f}".format(FIO, AIN, AIN, AINs4, AINs4, VAIN, 4 * VAIN))

    return AIN


def getLJinternalTemperature():
    """LJ U3 internal sensor temperature (NOT from the EI1050)"""

    fncname = "getLJinternalTemperature: "
    u3it    = gglobs.NAN
    try:                    u3it    = LJdevice.getTemperature() - 273.15
    except Exception as e:  exceptPrint(fncname + str(e), " failed")

    return u3it


def getEI1050Temperature(latestReading):
    """LJ EI1050 probe temperature"""

    if latestReading is None: return gglobs.NAN

    fncname = "getEI1050Temperature: "
    Temp    = gglobs.NAN
    try:                    Temp    = latestReading.getTemperature()
    except Exception as e:  exceptPrint(fncname + str(e), " failed")

    return Temp


def getEI1050Humidity(latestReading):
    """LJ EI1050 probe Humidity"""

    if latestReading is None: return gglobs.NAN

    fncname = "getEI1050Humidity: "
    Hum    = gglobs.NAN
    try:                    Hum    = latestReading.getHumidity()
    except Exception as e:  exceptPrint(fncname + str(e), " failed")

    return Hum


def setEI1050Status():
    """LJ EI1050 probe status"""

    fncname = "setEI1050Status: "
    try:        gglobs.LJEI1050status = LJprobe.getStatus()
    except:     gglobs.LJEI1050status = "Probe EI1050 not readable"

