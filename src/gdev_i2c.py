#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gdev_i2c.py - I2C support; limited to dongle ELV with Sensors BME280, TSL2591, and LM75
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

import gdev_i2c_Dngl_ELV            as ELV      # I2C dongle ELV
import gdev_i2c_Dngl_ISS            as ISS      # I2C dongle ISS
import gdev_i2c_Dngl_IOW            as IOW      # I2C dongle IOW24
# import gdev_i2c_Dngl_FTD            as FTD      # I2C dongle FT232H

import gdev_i2c_Sensor_LM75         as LM75     # I2C sensor
import gdev_i2c_Sensor_BME280       as BME280   # I2C sensor
import gdev_i2c_Sensor_SCD30        as SCD30    # I2C sensor
import gdev_i2c_Sensor_SCD41        as SCD41    # I2C sensor
import gdev_i2c_Sensor_TSL2591      as TSL2591  # I2C sensor

import gdev_i2c_Sensor_BH1750       as BH1750   # I2C sensor
import gdev_i2c_Sensor_GDK101       as GDK101   # I2C sensor


Sensors = {
           # Sensor-        I2C         Activation   Connection     Class       Var-        Vars                               Burn-in
           # Name           Address     Status       Status         handle      count       list                               cycles
           #                0           1            2              3           4           5                                  6
           "LM75"       : [ None,       False,       False,         None,       1,          ["CPM2nd"                      ],  1 ],
           "BME280"     : [ None,       False,       False,         None,       3,          ["Temp",    "Press",   "Humid" ],  3 ],
           "SCD30"      : [ None,       False,       False,         None,       3,          ["CPM2nd",  "CPM3rd",  "CPS3rd"],  1 ],
           "SCD41"      : [ None,       False,       False,         None,       3,          ["CPM",     "CPM1st",  "CPS1st"],  1 ],
           "TSL2591"    : [ None,       False,       False,         None,       2,          ["CPM3rd",  "CPS3rd"           ],  2 ],
           "BH1750"     : [ None,       False,       False,         None,       1,          ["CPM3rd"                      ],  1 ],
           "GDK101"     : [ None,       False,       False,         None,       3,          ["CPM3rd",  "CPS3rd",  "Temp"  ],  1 ],
          }

gglobs.Sensors = Sensors

# Index into Sensors dict
I2CADDR    = 0
I2CACTIV   = 1
I2CCONN    = 2
I2CHNDL    = 3
I2CVCNT    = 4
I2CVARS    = 5
I2CRUNS    = 6


def initI2C():
    """Init the dongle with the sensors"""

    fncname = "initI2C: "
    dprint(fncname)
    setIndent(1)

    gglobs.Devices["I2C"][CONN]  = False
    gglobs.Devices["I2C"][DNAME] = "I2C Sensors"

    # init the dongle
    if   gglobs.I2CDongleCode == "ISS":  gglobs.I2CDongle = ISS.ISSdongle()
    elif gglobs.I2CDongleCode == "ELV":  gglobs.I2CDongle = ELV.ELVdongle()
    elif gglobs.I2CDongleCode == "IOW":  gglobs.I2CDongle = IOW.IOWdongle()
    # elif gglobs.I2CDongleCode == "FTD":  gglobs.I2CDongle = FTD.FTDdongle() # not worth using

    success, msg  = gglobs.I2CDongle.DongleInit()
    if success:
        fprint(msg)
        dprint(msg)
    else:
        setIndent(0)
        return "Failure initializing dongle '{}': {}".format(gglobs.I2CDongle.name, msg)

    # init the sensors
    SensorCount = 0
    for sensor in Sensors:

        if not gglobs.I2CSensor[sensor][0]:
            cdprint("sensor: {:8s} - not activated".format(sensor) )
            continue
        else:
            cdprint("aaaasensor: ", sensor)

        Sensors[sensor][I2CACTIV]   = gglobs.I2CSensor[sensor] [0]  # gglobs: I2CSensor["LM75"] = [False, 0x48, None]
        Sensors[sensor][I2CADDR]    = gglobs.I2CSensor[sensor] [1]
        Sensors[sensor][I2CVARS]    = gglobs.I2CSensor[sensor] [2]

        address = Sensors[sensor][I2CADDR]
        if   sensor == "LM75"    : Sensors[sensor][I2CHNDL] = LM75    .SensorLM75     (address)
        elif sensor == "BME280"  : Sensors[sensor][I2CHNDL] = BME280  .SensorBME280   (address)
        elif sensor == "SCD30"   : Sensors[sensor][I2CHNDL] = SCD30   .SensorSCD30    (address)
        elif sensor == "SCD41"   : Sensors[sensor][I2CHNDL] = SCD41   .SensorSCD41    (address)
        elif sensor == "TSL2591" : Sensors[sensor][I2CHNDL] = TSL2591 .SensorTSL2591  (address)
        elif sensor == "BH1750"  : Sensors[sensor][I2CHNDL] = BH1750  .SensorBH1750   (address)
        elif sensor == "GDK101"  : Sensors[sensor][I2CHNDL] = GDK101  .SensorGDK101   (address)

        response = Sensors[sensor][I2CHNDL].SensorInit()
        if response is None:
            edprint(fncname + "response: ", response)
            continue

        if response[0]:
            SensorCount += 1
            Sensors[sensor][I2CCONN] = True
            msg = response[1]
            fprint(msg)
            dprint(msg)

        else:
            msg = "Failure initializing sensor {} on dongle {} with message:\n{}".format(sensor, gglobs.I2CDongle.name, response[1])
            Sensors[sensor][I2CCONN] = False
            efprint(msg, debug=True)

    ###### end sensor-init loop ######################

    if SensorCount == 0:
        returnmsg = "No Sensors found"

    else:
        fprint("I2C device has got {} sensor(s)".format(SensorCount))
        gglobs.Devices["I2C"][CONN]  = True

        SensorsBurnIn()

        # set the variables
        allvars = []
        for sensor in Sensors:
            if not Sensors[sensor][I2CACTIV]: continue
            temp = []
            for vname in Sensors[sensor][I2CVARS]:
                cvname = correctVariableCaps(vname)

                if cvname != "" and cvname != "auto":   temp.append(cvname)
                else:                                   temp.append("Unused")                   # need a temporary place holder for a value from the sensor
            Sensors[sensor][I2CVARS] = temp[ : Sensors[sensor][I2CVCNT]]
            allvars += Sensors[sensor][I2CVARS]

        allvars = [s for s in allvars if s != 'Unused'] # remove all "Unused"
        gglobs.I2CVariables = ", ".join(allvars)

        setLoggableVariables("I2C", gglobs.I2CVariables)
        dprint(fncname + "Loggable Variables: ", gglobs.I2CVariables)

        # get all info + extended info
        getInfoI2C(extended=True, FirstCall=True)

        returnmsg = ""

    setIndent(0)
    return returnmsg


def SensorsBurnIn():
    """First Values may be invalid"""

    fncname = "SensorsBurnIn: "
    dprint(fncname)
    setIndent(1)

    for sensor in Sensors:
        # rdprint(fncname + "sensor: ", sensor)
        if Sensors[sensor][I2CCONN]:       # use connected sensors only
            # make measurements to discard
            for i in range(0, Sensors[sensor][I2CRUNS]):
                # print(fncname, sensor, i)
                Sensors[sensor][I2CHNDL].SensorgetValues() # discard values
                time.sleep(0.05)
    setIndent(0)


def terminateI2C():
    """shutting down thread, closing ELV, resetting connection flag"""

    fncname = "terminateI2C: "

    dprint(fncname)
    setIndent(1)

    dprint(fncname + gglobs.I2CDongle.DongleTerminate())    # does nothing but closing the port

    gglobs.Devices["I2C"][CONN]  = False

    dprint(fncname + "Terminated")
    setIndent(0)


def resetI2C():
    """Reset the ELV dongle and sensors"""

    fncname = "resetI2C: "
    setBusyCursor()

    dprint(fncname + "---------------------------------------------------")
    setIndent(1)

    fprint(header("Resetting I2C System"))
    fprint("In progress ...")
    QtUpdate()

    # reset the dongle
    try:
        msg = gglobs.I2CDongle.DongleReset()                               # takes >=3 sec on ELV
        dprint(fncname + "Dongle: {} - {}".format(gglobs.I2CDongle.name, msg))
    except Exception as e:
        exceptPrint(e, fncname + "DongleReset failed")

    # reset all sensors
    for sensor in Sensors:
        # cdprint(fncname + "sensor: ", sensor)
        if Sensors[sensor][I2CCONN]:
            try:
                msg = Sensors[sensor][I2CHNDL].SensorReset()
                dprint(fncname + "Sensor: {} - {}".format(sensor, msg))
            except Exception as e:
                exceptPrint(e, fncname + "Resetting sensor {} failed".format(sensor))

    SensorsBurnIn()

    fprint("I2C System Reset done")
    dprint(fncname + "Done")

    setNormalCursor()
    setIndent(0)


def getInfoI2C(extended=False, FirstCall=False):
    """Calls the devices via serial on FirstCall=True only; otherwise conflicting double
    access to serial port"""

    fncname = "getInfoI2C: "

    if   gglobs.I2CDongleCode == "ISS":
        info = "Configured Connection:        Port: {} \n".format(gglobs.I2Cusbport)

    elif gglobs.I2CDongleCode == "ELV":

        info = "Configured Connection:        Port: {} Baud: {} Timeouts[s]: R:{} W:{}\n".format\
                                    (
                                        gglobs.I2Cusbport,
                                        gglobs.I2Cbaudrate,
                                        gglobs.I2CtimeoutR,
                                        gglobs.I2CtimeoutW
                                    )

    elif gglobs.I2CDongleCode == "IOW" or gglobs.I2CDongleCode == "FTD":    # FTD is NOT in use
        info = "Configured Connection:        Native USB connection\n"

    if not gglobs.Devices["I2C"][CONN]: return info + "<red>Device is not connected</red>"

    infoExt = info

    if FirstCall:
        # on first call query all devices and sensors

        # Dongle
        # DongleInfo: on ELV like: ['Last Adress:0xED', 'Baudrate:115200 bit/s', 'I2C-Clock:99632 Hz', 'Y00', 'Y10', 'Y20', 'Y30', 'Y40', 'Y50', 'Y60', 'Y70']
        cdprint(fncname + "dongle: ----------------------------------------------", gglobs.I2CDongle.name)
        DongleInfo     = gglobs.I2CDongle.DongleGetInfo()
        gglobs.Devices["I2C"][DNAME] = gglobs.I2CDongle.name     # like: ['ELV USB-I2C-Interface v1.8 (Cal:5E)'

        info += "{:30s}{}\n" .format("Connected Device:", "Dongle: {}".format(gglobs.I2CDongle.name))
        info += "{:30s}{}\n" .format("Configured Variables:", gglobs.I2CVariables)
        info += "\n"

        infoExt  = info
        infoExt += "Dongle: {}\n".format(gglobs.I2CDongle.name)
        infoExt += "\n".join(DongleInfo)
        infoExt += "\n"

        # Sensors
        for sensor in Sensors:
            if Sensors[sensor][I2CCONN]:
                cdprint(fncname + "sensor: ", sensor)
                SensorInfo = Sensors[sensor][I2CHNDL].SensorGetInfo()
                # msg      =  "{:30s}{}\n".format("Sensor: " + sensor, SensorInfo[0])
                msg      = "{:30s}{}".format("Sensor: " + sensor, SensorInfo[0])
                vmsg     = " - Variables: " + ", ".join("{}".format(x) for x in gglobs.Sensors[sensor][5]) + "\n"

                info    += msg + vmsg
                infoExt += msg + "\n"
                for a in SensorInfo[1:]: infoExt += " "*11 + a + "\n"
        info += "\n"
        gglobs.I2CInfo      = info
        gglobs.I2CInfoExt   = infoExt

    else:
        # on 2nd and later
        if extended:    info = gglobs.I2CInfoExt
        else:           info = gglobs.I2CInfo

    # Tube sensitivities
    info += getTubeSensitivities(gglobs.I2CVariables)

    # cdprint("\n" + info)

    return info


def scanI2CBus():
    """scans the I2C bus by writing 0x00 to each address from 0 ... 127"""

    # scan full bus
    # duration: Dongle: ISS: Found a total of 5 I2C device(s) in   50 ms     1.0x
    # duration: Dongle: ELV: Found a total of 5 I2C device(s) in  170 ms     3.4x
    # duration: Dongle: IOW: Found a total of 5 I2C device(s) in 1010 ms    20.2x

    # check single address
    # duration: Dongle: ISS: 0.27 ... 0.39 ms   (avg=0.31 ms)       1.0x
    # duration: Dongle: ELV: 1.04 ... 5.13 ms   (avg=1.22 ms)       3.9x
    # duration: Dongle: IOW: 5.2 ...  8.3  ms   (avg=7.7 ms)       24.8x

    fncname = "scanI2CBus: "

    gglobs.I2CDongle.DongleScanPrep("Start")    # needed for ELV dongle

    devicecount = 0
    start       = time.time()
    dscan       = fncname + "\n" # cumulative scan string
    scanfmt     = "0x{:02X}  "
    scan        = "       0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F"
    fprint(header("Scanning I2C Bus"))
    fprint(scan)
    QtUpdate()
    scan        = scanfmt.format(0) + "-- "

    # addr=0x00 is General Call Address for devices;
    # They may or may not respond; gives no conclusive info, therefore skip it.
    # Multiple other addresses are also not available, but my devices do not
    # seem to respond at those addresses
    # https://www.i2c-bus.org/addressing/general-call-address/
    for addr in range(1, 128):
        if addr % 16  == 0:
            fprint(scan)
            QtUpdate()
            dscan += scan + "\n"
            scan   = scanfmt.format(addr)

        try:
            if gglobs.I2CDongle.DongleAddrIsUsed(addr):
                scan   += "{:02X} ".format(addr)
                devicecount += 1
            else:
                scan   += "-- "
        except Exception as e:
            exceptPrint(e, fncname + "Failure with DongleAddrIsUsed")

    duration = time.time() - start
    scan += "\n\nFound a total of {} I2C device(s) in {:0.2f} sec\n".format(devicecount, duration)
    fprint(scan)
    dprint(dscan + scan)

    gglobs.I2CDongle.DongleScanPrep("End")    # needed for ELV dongle


def getValuesI2C(varlist):
    """Read all I2C data"""

    gVstart = time.time()

    fncname = "getValuesI2C: "

    cdprint(fncname, varlist)
    setIndent(1)

    # set sensor values for all vars to NAN
    SensorValues = {}
    for vname in gglobs.varsCopy:    SensorValues [vname] = gglobs.NAN

    # get the data from the sensors
    for sensor in Sensors:
        if Sensors[sensor][I2CACTIV]:
            sval = Sensors[sensor][I2CHNDL].SensorgetValues() # sval is tuple with 1 ... 3 values
            # edprint(fncname + "sensor: ", sensor, ", value: ", sval)
            for i in range(Sensors[sensor][I2CVCNT]):
                try:                    svname = Sensors[sensor][I2CVARS][i]
                except Exception as e:  svname = None
                if svname is not None: SensorValues[svname] = sval[i]
    # rdprint(fncname + "SensorValues: ", SensorValues)

    # scale values and set to alldata
    alldata = {}
    for vname in varlist:
        if vname == "Unused" or vname == "None": continue
        sval         = SensorValues[vname]
        scaled_sval  = round(scaleVarValues(vname, sval, gglobs.ValueScale[vname]), 3)
        alldata.update({vname: scaled_sval})

    gVdur = 1000 * (time.time() - gVstart)

    setIndent(0)
    vprintLoggedValues(fncname, varlist, alldata, gVdur)

    return alldata


def forceCalibration():
    """force CO2 calibration on the SCD30 and SCD41 sensor"""

    fncname = "forceCalibration: "

    # request the CO2 ref value
    frc = getCO2RefValue()
    if np.isnan(frc): return

    mdprint(fncname + "refVal: ", frc)

    if Sensors["SCD30"][I2CHNDL] is not None:
        Sensors["SCD30"][I2CHNDL].SCD30setFRC(frc)
        fprint("Sensor SCD30 is calibrated")
    else:
        # gglobs.exgg.showStatusMessage("Sensor is not available")
        efprint("Sensor SCD30 is not available")

    QtUpdate()

    if Sensors["SCD41"][I2CHNDL] is not None:
        Sensors["SCD41"][I2CHNDL].SCD41setFRC(frc)
        fprint("Sensor SCD41 is calibrated")
    else:
        gglobs.exgg.showStatusMessage("Sensor is not available")
        efprint("Sensor SCD41 is not available")

    QtUpdate()

    # set all info + extended info
    getInfoI2C(extended=True, FirstCall=True)


def getCO2RefValue():
    """Enter a value manually"""

    fncname = "getCO2RefValue: "

    # getCO2RefValue should not be callable when logging
    if gglobs.logging:
        gglobs.exgg.showStatusMessage("Cannot change sensor calibration when logging! Stop logging first")
        return

    dprint(fncname)
    setIndent(1)

    # Calib Value
    lv1 = QLabel("Enter Reference CO2 [ppm]\n(Not less than 400)")
    lv1.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    v1  = QLineEdit()
    v1.setToolTip("Enter the CO2 calibration value for the SCD41 sensor")
    v1.setText("")

    graphOptions=QGridLayout()
    graphOptions.setContentsMargins(10,10,10,10) # spacing around the graph options

    graphOptions.addWidget(lv1,     0, 0)
    graphOptions.addWidget(v1,      0, 1)

    # Dialog box
    d = QDialog()
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setWindowTitle("Set CO2 Reference Value")
    d.setWindowModality(Qt.WindowModal)
    d.setMinimumWidth(400)

    # Buttons
    bbox = QDialogButtonBox()
    bbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok )
    bbox.accepted.connect(lambda: d.done(1))
    bbox.rejected.connect(lambda: d.done(-1))

    gglobs.btn = bbox.button(QDialogButtonBox.Ok)
    gglobs.btn.setEnabled(True)

    layoutV = QVBoxLayout(d)
    layoutV.addLayout(graphOptions)
    layoutV.addWidget(bbox)

    retval = d.exec()
    # print("reval:", retval)

    co2ref = gglobs.NAN

    if retval != 1:
        # ESCAPE pressed or Cancel Button
        dprint(fncname + "Canceling; no changes made")

    else:
        # OK pressed
        fprint(header("Calibrate CO2 Sensors"))
        QtUpdate()

        v1val = v1.text().strip().replace(",", ".")
        # cdprint("v1.text: ", v1.text(), ", v1val: ", v1val)

        if v1val > "":
            try:
                co2ref = int(float(v1val))
                cdprint("co2ref: ", co2ref, ", v1val: ", v1val)

            except Exception as e:
                msg = "CO2 Reference must be given as a number of at least '400' (ppm); you entered: '{}'".format(v1val)
                exceptPrint(e, msg)
                efprint(msg)
                co2ref = gglobs.NAN

            if co2ref < 400:
                efprint("CO2 Reference value must be at least '400' ppm; you entered: {} ppm".format(v1val))
                co2ref = gglobs.NAN

    setIndent(0)

    return co2ref

