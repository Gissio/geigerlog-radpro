#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
AmbioMon++ - calling AmbioMon++ running on ESP32
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

from   gsup_utils           import *
import gsup_sql                         # database handling


###############################################################################
# used only internally within gdev_ambiomon.py

def _getAmbioUrl():
    """get url like 'http://10.0.0.78/'; Port is always 80"""

    return "http://{}".format(gglobs.AmbioServerIP)


def _getAmbioDevice():
    # get the device like 'ESP32-WROOM-Dev' by calling page '/id' yielding:
    #   2020-06-02 09:39:01, ESP32-WROOM-Dev, 10.0.0.85, ambiomon.local, 3

    fncname = "_getAmbioDevice: "

    try:
        url   = _getAmbioUrl() + "/id"
        page  = urllib.request.urlopen(url, timeout=gglobs.AmbioTimeout)
        data  = page.read().decode("UTF-8").split(",")
        #print(fncname + "data: ", data)
    except Exception as e:
        edprint(fncname + "Failed at url:'{}' with Exception: ".format(url), e, debug=True)
        return "NONE"

    if len(data) > 3:   gglobs.AmbioCPUFrequency = data[3].strip()
    else:               gglobs.AmbioCPUFrequency = "unknown"
    return data[2].strip()


def _convertUnixtimeToDateTime(unixtime):
    """convert a Unix time in sec into datetime like: 2020-05-10 11:48:50"""

    return datetime.datetime.utcfromtimestamp(unixtime).strftime('%Y-%m-%d %H:%M:%S')


def _printException(e, rec):
    dprint  ("Exception _parseValueAdder: ", e)
    efprint ("AmbioMon History Download had error: ", cleanHTML(e))
    qefprint("Record is ignored, has Error: ", rec)
    dprint  ("Record is ignored, has Error: ", rec)


def _parseValueAdderCPS(i, rec):
    """Add the parse results to the *.his list"""

    # create the data for the database; datalist covers:
    # Index, DateTime, <modifier>,  CPM, CPS, CPM1st, CPS1st, CPM2nd, CPS2nd,  CPM3rd, CPS3rd, Temp, Press, Humid, Xtra
    # 0      1         2            3    4    5       6       7        8       9       10      11    12     13     14

    #~ print("_parseValueAdder: i, rec:", i, rec)
    try:
        reclist      = rec.split(",", 5)        #
        datalist     = [None] * (gglobs.datacolsDefault + 2)   # (13 + 2)=15 x None
        datalist[0]  = i                        # byte index
        datalist[1]  = reclist[0]               # DateTime UTC
        datalist[2]  = "0 hours"                # the modifier for julianday; here: no modification
        datalist[4]  = reclist[1]               # cps

        datalist[9]  = reclist[2]               # selector
        datalist[10] = reclist[3]               # volt

        gglobs.HistoryDataList.append (datalist)

    except Exception as e:
        _printException(e, rec)


def _parseValueAdderCAM(i, rec):
    """Add the parse results to the *.his list"""

    # create the data for the database; datalist covers:
    # Index, DateTime, <modifier>,  CPM, CPS, CPM1st, CPS1st, CPM2nd, CPS2nd,  CPM3rd, CPS3rd, Temp, Press, Humid, X
    # 0      1         2            3    4    5       6       7        8       9       10      11    12     13     14

    #~ print("_parseValueAdder: i, rec:", i, rec)
    try:
        reclist      = rec.split(",", 9)    # results in datetime + 6 values + 1 extra for the rest
        datalist     = [None] * (gglobs.datacolsDefault + 2)   # (13 + 2)=15 x None
        datalist[0]  = i                    # byte index
        datalist[1]  = reclist[0]           # DateTime UTC
        datalist[2]  = "0 hours"            # the modifier for julianday; here: no modification
        datalist[3]  = reclist[1]           # cpm

        datalist[9]  = reclist[6]           # selector
        datalist[10] = reclist[7]           # volt

        datalist[11] = reclist[2]           # temp
        datalist[12] = reclist[3]           # pressure
        datalist[13] = reclist[4]           # humidity
        datalist[14] = reclist[5]           # air quality

        gglobs.HistoryDataList.append (datalist)

    except Exception as e:
        _printException(e, rec)


# gdev_ambiomon.py use only
###############################################################################


###############################################################################
# Public Functions


def makeAmbioHistory(source, device):  # source == "AMDeviceCAM" or "AMDeviceCPS"
    """read the history from an AmbioMon device"""

    fncname = "makeAmbioHistory: "

    if not gglobs.Devices["AmbioMon"][ACTIV]:
        emsg = "AmbioMon device is not activated"
        dprint(fncname + emsg)
        return -1, emsg

    dprint(fncname + "from source: '{}' using device: '{}'".format(source, device))
    dprint(fncname + "gglobs.AMFilePath: {}".format(gglobs.AMFilePath))
    setIndent(1)

    error           = 0         # default: no error
    message         = ""        # default: no message

    start = time.time()

    if   source == "AMDeviceCPS" or source == "AMDeviceCAM":
    # get data from AmbioMon device

        # if not gglobs.AmbioConnection:
        if not gglobs.Devices["AmbioMon"][CONN] :
            emsg = "AmbioMon device is not connected"
            dprint(fncname + emsg)
            return -1, emsg

        if   source == "AMDeviceCPS": url = _getAmbioUrl() + "/cps.data"
        elif source == "AMDeviceCAM": url = _getAmbioUrl() + "/cam.data"
        fprint("Using URL: ", url)

        try:
            page        = urllib.request.urlopen(url, timeout=10)
            devicedata  = page.read()   # type(devicedata) = <class 'byte'>
        except Exception as e:
            dprint("Failed urlib: Exception: ", e, debug=True)
            playWav("err")
            efprint("{} Reading data from Web failed with exception:\n{}".format(stime(), cleanHTML(e)))
            setIndent(0)
            QtUpdate()
            return -1, cleanHTML(e)

    elif source == "AMFileCPS" or source == "AMFileCAM":
    # get data from AmbioMon File
        try:
            devicedata = readBinaryFile(gglobs.AMFilePath)
        except Exception as e:
            playWav("err")
            efprint("{} Reading data from File failed with exception:\n{}".format(stime(), cleanHTML(e)))
            setIndent(0)
            QtUpdate()
            return -1, cleanHTML(e)

    stop       = time.time()

    dtime      = (stop - start)
    lendevicedata = len(devicedata)
    msg        = "Downloaded {:0.1f} kB from {} in {:0.1f} milliseconds ({:0.1f} kB/s)".format(lendevicedata / 1000, source, dtime * 1000, lendevicedata/dtime/1000)
    vprint(msg)
    fprint(msg)
    fprint("Processing data ...")
    QtUpdate()

    data_originDB   = (stime(), gglobs.Devices["AmbioMon"][DNAME])
    dbheader        = "File created by reading log from device"
    dborigin        = "Download from device"
    dbdevice        = "{}".format(data_originDB[1])

    dumpdata = []
    if   source == "AMDeviceCPS" or source == "AMFileCPS":
        #~ upformat = "<HBBL" + "Humid" * 60
        #~upformat = "<BBBL" + "Humid" * 60
        upformat = "<BBHL" + "Humid" * 60
        wprint("Unpack Format: ", upformat)
        for i in range(0, len(devicedata), 128):
            dbuf = devicedata[i : i + 128]
            data = struct.unpack(upformat, dbuf)
            #~volt = data[2] + 350     # volt is given minus 350 to fit into 1 byte
            volt = data[2]            # volt is given as int
            dcfg = data[1] & 0x03    # selector is 1, or 2, or 3

            for j in range(0, 60):   # make 60 records
                dt = _convertUnixtimeToDateTime(data[3] - 60 + j)
                sdata = "{},{},{},{}".format(
                                    dt,
                                    data[4 + j],
                                    dcfg,
                                    volt,
                                    )
                dumpdata.append(sdata)
            #~ if i > 1000: break

    elif source == "AMDeviceCAM" or source == "AMFileCAM":
        upformat = "<BBHLLfffff"
        wprint("Unpack Format: ", upformat)
        for i in range(0, len(devicedata), 32):
            dbuf = devicedata[i : i + 32]
            data = struct.unpack(upformat, dbuf)
            #~volt = data[2] + 350     # volt is given minus 350 to fit into 1 byte
            volt = data[2]           # volt is now in 2 bytes, int 16
            dcfg = data[1] & 0x03    # selector is 1, or 2, or 3

            sdata = "{},{},{:0.2f},{:0.2f},{:0.2f},{:0.2f},{},{}".format( # make single record
                                _convertUnixtimeToDateTime(data[3]),
                                data[4],
                                data[5],
                                data[6],
                                data[7],
                                data[8],
                                dcfg,
                                volt,
                                )
            dumpdata.append(sdata)

    #~for a in dumpdata[:6]:  print("dumpdata:", a)
    #~print()
    #~for a in dumpdata[-6:]: print("dumpdata:", a)

    if len(dumpdata) == 0:
        error   = -1
        message = "No valid data found!"
        dprint(message)

    else:
    # parse HIST data
        gglobs.HistoryDataList      = []
        gglobs.HistoryParseList     = []
        gglobs.HistoryCommentList   = []

        #~ _getParsedHistoryCPS(dumpdata)
        if   source == "AMDeviceCPS" or source == "AMFileCPS":
            for i, rec in enumerate(dumpdata):
                _parseValueAdderCPS(i, rec)

        elif source == "AMDeviceCAM" or source == "AMFileCAM":
            for i, rec in enumerate(dumpdata):
                _parseValueAdderCAM(i, rec)

    # add headers
        dbhisClines    = [None] * 3
        #                  ctype    jday, jday modifier to use time unmodified
        dbhisClines[0] = ["HEADER", None, "0 hours", dbheader]
        dbhisClines[1] = ["ORIGIN", None, "0 hours", dborigin]
        dbhisClines[2] = ["DEVICE", None, "0 hours", dbdevice]

    # write to database
        gsup_sql.DB_insertDevice        (gglobs.hisConn, *data_originDB)
        gsup_sql.DB_insertComments      (gglobs.hisConn, dbhisClines)
        gsup_sql.DB_insertComments      (gglobs.hisConn, gglobs.HistoryCommentList)
        gsup_sql.DB_insertData          (gglobs.hisConn, gglobs.HistoryDataList)
        gsup_sql.DB_insertParse         (gglobs.hisConn, gglobs.HistoryParseList)

    # write device data to database
        saveToBin = True
        if saveToBin:   gsup_sql.DB_insertBin(gglobs.hisConn, devicedata)

        # fprint("Database is created", debug=gglobs.debug)
        msg = "Database is created"
        fprint(msg)
        dprint(msg)

    setIndent(0)
    return error, message


def setAmbioServerIP():
    """Set settings for Ambiomon when in Station mode"""

    # setting a server address must be possible without a prior connection,
    # because Init fails if IP not accessible

    fncname = "setAmbioServerIP: "

    dprint(fncname)
    setIndent(1)

    # AmbioServer IP
    lstaip = QLabel("Domain Name or IP Adress of AmbioMon")
    lstaip.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    staip  = QLineEdit()
    staip.setToolTip("Enter the local Domain Name (if supported) or local IP where your AmbioMon device can be reached")
    staip.setText("{}".format(gglobs.AmbioServerIP))

    graphOptions=QGridLayout()
    graphOptions.setContentsMargins(10,10,10,10) # spacing around the graph options
    graphOptions.addWidget(lstaip, 0, 0)
    graphOptions.addWidget(staip,  0, 1)

    # Dialog box
    d = QDialog()
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setFont(gglobs.fontstd)
    d.setWindowTitle("Set AmbioMon Device IP")
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

    if gglobs.logging:         # no change of parameters when logging
        gglobs.btn  .setEnabled(False)
        staip       .setEnabled(False)

    retval = d.exec()
    #print("reval:", retval)

    if retval != 1:
        # ESCAPE pressed or Cancel Button
        dprint(fncname + "Canceling; settings unchanged")

    else:
        # OK pressed
        gglobs.AmbioServerIP = staip.text().strip()

        dprint(fncname + "new IP Address:    ", gglobs.AmbioServerIP)
        fprint(header("Configure AmbioMon WiFi Station Mode"))
        fprint("AmbioMon Station Mode IP:"     , "{}"    .format(gglobs.AmbioServerIP))

    setIndent(0)



def sendToSerial():
    """Sends text to the AmbioMon via Serial"""

    fncname = "sendToSerial: "

    dprint(fncname)
    setIndent(1)

    # Message
    lstaip = QLabel("Message for AmbioMon")
    lstaip.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    staip  = QLineEdit()
    staip.setToolTip("Enter a message tp be send to AmbioMon via Serial")
    staip.setText("")

    graphOptions=QGridLayout()
    graphOptions.setContentsMargins(10,10,10,10) # spacing around the graph options
    graphOptions.addWidget(lstaip, 0, 0)
    graphOptions.addWidget(staip,  0, 1)

    # Dialog box
    d = QDialog()
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setFont(gglobs.fontstd)
    d.setWindowTitle("Send Message to AmbioMon")
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
    #print("reval:", retval)

    if retval != 1:
        # ESCAPE pressed or Cancel Button
        dprint(fncname + "Canceling; settings unchanged")

    else:
        # OK pressed
        msg = staip.text().strip()

        dprint(fncname + "Message:    ", msg)
        fprint(header("Sending Message to AmbioMon"))
        fprint("AmbioMon Message:"     , "{}"    .format(msg))

        if gglobs.ESP32Serial == None:
            openESP32Serial()

        gglobs.ESP32Serial.write(bytes(msg + "\n", "UTF-8"))

    setIndent(0)


def setAmbioLogDatatype():
    """Set the datatype GeigerLog will request from Ambiomon (LAST or AVG)"""

    if not gglobs.Devices["AmbioMon"][CONN] : return "No connected device"

    dprint("setAmbioLogDatatype:")
    setIndent(1)

    lstaip = QLabel("Data as LAST value or last AVG value?\n(No change during logging)" + " "*15)
    lstaip.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    b0 = QRadioButton("LAST")             # this is default
    b1 = QRadioButton("AVG")
    b0.setToolTip("Select 'LAST' to get last value of data, or 'AVG' to get last 1 min average of values")
    b1.setToolTip("Select 'LAST' to get last value of data, or 'AVG' to get last 1 min average of values")

    if gglobs.AmbioDataType == "LAST" : b0.setChecked(True)
    else:                               b1.setChecked(True)

    layoutT = QHBoxLayout()
    layoutT.addWidget(b0)
    layoutT.addWidget(b1)

    graphOptions=QGridLayout()
    graphOptions.setContentsMargins(10,10,10,10) # spacing around the options
    graphOptions.addWidget(lstaip,          0, 0)
    graphOptions.addLayout(layoutT,         0, 1)

    # Dialog box
    d = QDialog()
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setFont(gglobs.fontstd)
    d.setWindowTitle("Select Data Type Mode")
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

    if gglobs.logging:         # no change of parameters when logging
        gglobs.btn  .setEnabled(False)

    retval = d.exec()
    #print("reval:", retval)

    if retval != 1:
        # ESCAPE pressed or Cancel Button clicked
        dprint("setAmbioLogDatatype: Settings unchanged")
    else:
        if b0.isChecked(): gglobs.AmbioDataType = "LAST"    # b0.isChecked()
        else:              gglobs.AmbioDataType = "AVG"     # b1.isChecked()

        fprint(header("Select Data Type Mode"))
        # fprint("AmbioMon Data Type:", "{}"    .format(gglobs.AmbioDataType), debug=True)
        msg = "AmbioMon Data Type:", "{}".format(gglobs.AmbioDataType)
        fprint(msg)
        dprint(msg)

    setIndent(0)


def getValuesAmbioMon(varlist):
    """Read all AmbioMon data"""

    def getValueAmbioMon(index):
        """check for missing value and make floats"""

        try:
            if data[index] == "":   # missing value
                val = gglobs.NAN
            else:
                try:
                    val = float(data[index])
                except Exception as e:
                    msg = "index: {}".format(index)
                    exceptPrint(e, msg)
                    val = gglobs.NAN
        except Exception as e:
            val = gglobs.NAN

        return val


    start = time.time()

    fncname = "getValuesAmbioMon: "

    if gglobs.AmbioDataType == "LAST":  url = _getAmbioUrl() + "/lastdata"
    else:                               url = _getAmbioUrl() + "/lastavg"

    alldata      = {}       # data to be returned
    data         = []       # data read from url
    attempts     = 0        # no of attempts to get a connection
    attempts_max = 1 if gglobs.AmbioTimeout > gglobs.logCycle else gglobs.logCycle // gglobs.AmbioTimeout # max no of attempts - only as many as fit into logCycle

    while attempts < attempts_max:
        if not gglobs.logging:  break  # logging might be stopped while trying

        attempts  += 1
        etext      = "None"

        try:
            #raise Exception("test")
            #raise urllib.error.URLError("my dear test")

            dstart = time.time()
            page   = urllib.request.urlopen(url, timeout=gglobs.AmbioTimeout)        # 40...120 ms, rest < 0.05 ms
            dstop  = time.time()
            data   = page.read().decode("UTF-8").split(",")

            # test:
            data   = data[1:]
            # gdprint(data)
            # endtest

            if gglobs.werbose:
                wprint(fncname + "page: geturl : ", page.geturl())   # e.g.  http://10.0.0.85/lastdata
                wprint(fncname + "page: getcode: ", page.getcode())  # 200
                for a, b in page.info().items(): wprint (fncname + "page: info:    {:20s}:   {}".format(a, b))
                for i, a in enumerate(data):     wprint (fncname + "data: {:2d}:  {:20s}"       .format(i, a.strip()))
                wprint(fncname + "download ambio data: {:0.1f} ms".format((dstop - dstart) * 1000))

            for vname in varlist:
                if   vname == "CPM":
                                        cpm = getValueAmbioMon(1) if (getValueAmbioMon(1) != 4294967295) else gglobs.NAN

                                        alldata.update({vname:      cpm              })   # CPM
                elif vname == "CPS":    alldata.update({vname:      getValueAmbioMon(2)      })   # CPS
                elif vname == "CPS2nd": alldata.update({vname:      getValueAmbioMon(16)     })   # CPU frequency MHz

                ##################### this is the normal definition
                elif vname == "Temp":   alldata.update({"Temp":    getValueAmbioMon(3)      })   # T   from BMEX80
                elif vname == "Press":  alldata.update({"Press":   getValueAmbioMon(4)      })   # P   from BMEX80
                elif vname == "Humid":  alldata.update({"Humid":   getValueAmbioMon(5)      })   # H   from BMEX80
                elif vname == "Xtra":   alldata.update({"Xtra":    getValueAmbioMon(6)      })   # X   Airq BME680 resistance kOhm (plotted as (LOG10(1/VAL) + 3 )*50)
                ##################### end normal definition

                # # special definition
                # elif vname == "Temp":  alldata.update({vname:      float(data[12])     })   # T   ESPBattReading
                # elif vname == "Press": alldata.update({vname:      float(data[16])     })   # P   ESP CPU frequency
                # elif vname == "Humid": alldata.update({vname:      float(data[17])     })   # H   CurrentReading
                # elif vname == "Xtra":  alldata.update({vname:      float(data[15])     })   # X   readVoltESPpin(PIN_Vchip, 200)

            gglobs.AmbioCPUFrequency = getValueAmbioMon(16) # i.e. is updated with every call for data

            break

        except urllib.error.URLError as e:
            exceptPrint(e, "")
            etext = cleanHTML(e.reason)

        except Exception as e:
            exceptPrint(e, "")
            etext = cleanHTML(e)

        if attempts == 1:
            msg  = "Reading AmbioMon Values from '{}'\nfailed with error: '{}'".format(url, etext)
            msg += " (Timeout setting: {} sec)".format(gglobs.AmbioTimeout) if "timed out" in etext else ""
            qefprint(stime() + " " + msg)
        else:
            msg = "Repeat #{} of {} failed".format(attempts, attempts_max)
            edprint(msg)
            qefprint(msg)

        if attempts == attempts_max:
            playWav("err")
            if attempts_max > 1:
                msg = "max repeats reached, giving up"
                edprint(msg)
                qefprint(msg)
            fprint("")
            break

        QtUpdate() # without it no update of NotePad


    # # calling ESP32 via serial
    # rsc = readESP32Serial()
    # #print(rsc)
    # listrsc = rsc.strip().split(",")
    # #print("readESP32Serial: listrsc: ", listrsc)
    # try:
    #     #~alldata.update({"Temp":     float(listrsc[0])     })   # T   CurrentLastDeltat
    #     alldata.update({"Temp":       float(listrsc[4])     })   # T   Duration in µs of all shunt actions
    #     alldata.update({"Press":      float(listrsc[1])     })   # P   CurrentLastADC
    #     alldata.update({"Humid":      float(listrsc[2])     })   # H   CurrentLastVolt
    #     if gglobs.FirstLogValuesCall:
    #         alldata.update({"Xtra":      gglobs.NAN         })   # X   CurrentIntegral - 1st value is wrong
    #     else:
    #         alldata.update({"Xtra":      float(listrsc[3])  })   # X   CurrentIntegral
    #     #raise Exception("test readSerial")
    # except Exception as e:
    #     exceptPrint(e, fncname + "readESP32Serial: listrsc: {}".format(listrsc))

    vprintLoggedValues(fncname, varlist, alldata, (time.time() - start) * 1000)

    return alldata


def openESP32Serial():
    """Open the Serial connection to the ESP32"""

    fncname = "openESP32Serial: "

    dv              = "/dev/ttyUSB0" # device
    br              = 115200         # baudrate
    to              = 3              # timeout
    wto             = 1              # write timeout

    # try to close it first
    closeESP32Serial()

    # now try to open it
    try:
        gglobs.ESP32Serial = serial.Serial(dv, br, timeout=to, write_timeout=wto)
        fprint(fncname + "connected")
    except Exception as e:
        closeESP32Serial()
        msg = fncname + "Open failed"
        exceptPrint(e, msg)
        qefprint(msg)


def closeESP32Serial():
    """Try to close the Serial connection to the ESP32 and Null it"""

    try:    gglobs.ESP32Serial.close()
    except: pass

    gglobs.ESP32Serial = None



def writeESP32Serial(msg):
    """Try to close the Serial connection to the ESP32 and Null it"""

    try:
        gglobs.ESP32Serial.write(msg)
        # without delay after writing, ESP isn't fast enough to provide answer
        #  1 ms: too short
        #  2 ms: works most but not always
        #  3 ms: works most but not always
        #  4 ms: works most but not always
        #  5 ms: works most but not always
        # 10 ms: works; occasionally a failure
        time.sleep(0.010)
    except: qefprint("Failure writing to the ESPSerial")


def readESP32Serial():
    """read the ESP32 terminal output"""
    # results in problems with other serial devices

    # using 2 terminals
    # https://unix.stackexchange.com/questions/261531/how-to-send-output-from-one-terminal-to-another-without-making-any-new-pipe-or-f

    fncname = "readESP32Serial: "
    vprint(fncname)

    logfile         = "esp32.termlog"
    bytesWaiting    = 0                             # to avoid reference error
    empty           = "nan, nan, nan, nan, nan, nan, nan, nan, nan"
    glval           = empty
    logfilepath     = os.path.join(gglobs.dataPath, logfile) # save in data dir

    # if the serial port is not open then try to open it now,
    # and clear the logfile if sucessful
    if gglobs.ESP32Serial == None:
        openESP32Serial()
        if gglobs.ESP32Serial == None:  # tried to connect again, but failed
            edprint("gglobs.ESP32Serial == None --- returning with nans")
            return glval
        try:
            with open(logfilepath, 'wt', encoding="UTF-8", errors='replace', buffering = 1) as f:
                f.write("Starting at: {}\n".format(longstime()))
        except Exception as e:
            exceptPrint(e, "readESP32Serial")

    setIndent(1)

    writeESP32Serial(b"GeigerLog\n")

    while True:
        try:
            bytesWaiting = gglobs.ESP32Serial.in_waiting
            #print("bytesWaiting: ", bytesWaiting)
        except Exception as e:
            msg = "Exception: fasilure in getting bytesWaiting"
            exceptPrint(e, fncname + msg)
            closeESP32Serial()
            break

        if bytesWaiting == 0: break

        try:
            # readline(size): Read and return one line from the stream. If
            # size is specified, at most size bytes will be read.
            #print("bytes waiting before readline: ", gglobs.ESP32Serial.in_waiting)
            rec = gglobs.ESP32Serial.readline()
            #print("rec: ", rec)
        except Exception as e:
            msg = "Exception: failure in 'readline'"
            exceptPrint(e, fncname + msg)
            closeESP32Serial()
            break

        try:
            rec = rec.decode('UTF-8')
            #print("rec.decode: ", rec)
        except Exception as e:
            msg = "Exception: failure in 'decode'"
            exceptPrint(e, fncname + msg)
            closeESP32Serial()
            break

        if rec[-1] != "\n": rec += "\n"         # add a linefeed if none present
        if rec.startswith("ESP32: GeigerLog"):
            vprint(rec[:-1])                    # remove LF for print
            glval = rec[17:-1]                  # cut off 'GeigerLog:' and LF

        try:
            with open(logfilepath, 'at', encoding="UTF-8", errors='replace', buffering = 1) as f:
                f.write(rec)                        # keep LF
        except Exception as e:
            exceptPrint(e, fncname + "write to logfilepath")

    #print("glval: ", glval)
    if glval == empty: vprint("ESP32: GeigerLog - No Data!")

    setIndent(0)

    return glval


def initAmbioMon():
    """Initialize AmbioMon"""

    fncname = "initAmbioMon: "

    dprint(fncname)
    setIndent(1)

    # set configuration
    if gglobs.AmbioServerIP    == "auto": gglobs.AmbioServerIP    = getGeigerLogIP()    # GeigerLog's onw IP
    if gglobs.AmbioServerPort  == "auto": gglobs.AmbioServerPort  = 80                  # default port no
    if gglobs.AmbioTimeout     == "auto": gglobs.AmbioTimeout     = 3                   # 1 sec scheint zu kurz, 2 häufig zu kurz, 3 meist ok, 5 sec bringt nichts
    if gglobs.AmbioDataType    == "auto": gglobs.AmbioDataType    = "LAST"              # using 'lastdata' call, not avg for 'lastavg'
    if gglobs.AmbioVariables   == "auto": gglobs.AmbioVariables   = "CPM, CPS, Temp, Press, Humid, Xtra"

    gglobs.Devices["AmbioMon"][DNAME] = _getAmbioDevice()                               # expect like 'ESP32-WROOM-Dev'; needs IP; 'NONE' on failure

    if gglobs.Devices["AmbioMon"][DNAME] == "NONE":
        # not connected
        gglobs.Devices["AmbioMon"][CONN] = False
        msg = "No connection to: AmbioServerIP: '{}'".format(gglobs.AmbioServerIP)
        edprint(fncname + msg)
    else:
        # connected
        gglobs.Devices["AmbioMon"][CONN] = True
        msg  = ""
        dprint(fncname + "connected to: AmbioServerIP: '{}', detected device: '{}'".format(gglobs.AmbioServerIP, gglobs.Devices["AmbioMon"][DNAME]))

        setLoggableVariables("AmbioMon", gglobs.AmbioVariables)

    setIndent(0)
    return msg


def terminateAmbioMon():
    """opposit of init ;-)"""

    fncname = "terminateAmbioMon: "

    dprint(fncname)
    setIndent(1)

    gglobs.Devices["AmbioMon"][CONN]  = False

    dprint(fncname + "Terminated")
    setIndent(0)


def getInfoAmbioMon(extended=False):
    """Info on the AmbioMon Device"""

    AmbioInfo  = ""
    AmbioInfo += "Configured Connection:        Server IP:Port: '{}:{}'  Timeout: {} sec\n"\
        .format(gglobs.AmbioServerIP, gglobs.AmbioServerPort, gglobs.AmbioTimeout)

    if not gglobs.Devices["AmbioMon"][CONN]: return AmbioInfo + "<red>Device is not connected</red>"

    AmbioInfo += "Connected Device:             {}\n"             .format(gglobs.Devices["AmbioMon"][DNAME])
    AmbioInfo += "CPU Frequency:                {} MHz\n"           .format(gglobs.AmbioCPUFrequency)
    AmbioInfo += "Configured Variables:         {}\n"               .format(gglobs.AmbioVariables)
    AmbioInfo += getTubeSensitivities(gglobs.AmbioVariables)

    AmbioInfo += "Data Type Mode [LAST, AVG]:   {}\n"               .format(gglobs.AmbioDataType)
    AmbioInfo += "\n"
    AmbioInfo += "TESTING USAGE:\n"
    AmbioInfo += "   CPS2nd:                    CPU frequency\n"
    AmbioInfo += "   T     :                    ESP Batt volt\n"
    AmbioInfo += "   H     :                    ?            \n"
    AmbioInfo += "   X     :                    Avg ESP BattV\n"

    if extended == True:
        AmbioInfo += "Geiger tube voltage:          {} Volt\n"  .format(gglobs.AmbioVoltage)
        AmbioInfo += "Cycletime:                    {} sec\n"   .format(gglobs.AmbioCycletime)
        AmbioInfo += "Frequency:                    {} Hz\n"    .format(gglobs.AmbioFrequency)
        AmbioInfo += "PWM:                          {}\n"       .format(gglobs.AmbioPwm)
        AmbioInfo += "Saving:                       {}\n"       .format(gglobs.AmbioSav)
        AmbioInfo += "Server Timeout [s]            {}\n"       .format(gglobs.AmbioTimeout)

    return AmbioInfo


def pingAmbioServer():
    """
    Ping the AmbioMon Server.
    Remember that a host may not respond to a ping (ICMP) request even if the
    host name is valid!
    """
    setBusyCursor()

    fprint(header("Pinging AmbioMon Server " + gglobs.AmbioServerIP))
    QtUpdate() # to make the header visible right away

    presult, ptime = ping(gglobs.AmbioServerIP)

    pr = "Ping Result:"
    if presult:
        playWav("ok")
        fprint (pr, "Success, ", ptime)
    else:
        efprint(pr, "Failure")

    setNormalCursor()

