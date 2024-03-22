#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
WiFiServer - calling WiFiServer Devices
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

# A WiFiServer needs to respond to these calls:
# - id
# - lastdata
# - lastavg
# - reset
#
# http://serverip:port/folder/id
#                      response:         DeviceName
#                      response example: AmbioMon
# http://serverip:port/folder/lastdata
#                      response:         CPM, CPS, CPM1st, CPS1st, CPM2nd, CPS2nd,  CPM3rd, CPS3rd, Temp, Press, Humid, Xtra
#                      response example: 100.496, 1.159,,,,,,,25.000, -18.000, 54.000, 97.000
# http://serverip:port/folder/lastavg
#                      response:         CPM, CPS, CPM1st, CPS1st, CPM2nd, CPS2nd,  CPM3rd, CPS3rd, Temp, Press, Humid, Xtra
#                      response example: 100.496, 1.159,,,,,,,25.000, -18.000, 54.000, 97.000
# http://serverip:port/folder/reset
#                      response:         <anything>
#                      response example: Ok
#
# Demo code using PHP files on Apache server with Port=80:
#
# <?php
# // use for: id
# $ID      = "GeigerLog";
# $date    = date("Y-m-d H:i:s");
# $devname = "PHP Simulator on Apache";
# echo sprintf("%s, %s, %s", $ID, $date, $devname);
# ?>
#
# <?php
# // use for: /lastdata, /lastavg
# /*
# * makes approx normal dist
# * Alternative of "stats_rand_gen_normal()".
# * "Box–Muller transform" based random deviate generator.
# * @ref https://en.wikipedia.org/wiki/Box%E2%80%93Muller_transform
# *
# * @param  float|int $av Average/Mean
# * @param  float|int $sd Standard deviation
# * @return float
# */
# function rand_pseudo_normal($av, $sd): float
# {
#     $x = mt_rand() / mt_getrandmax();
#     $y = mt_rand() / mt_getrandmax();
#
#     return sqrt(-2 * log($x)) * cos(2 * pi() * $y) * $sd + $av;
# }
#
# function rand_pseudo_poisson($av): float
# {
#     // use with $av >= 10
#     return abs(rand_pseudo_normal($av, sqrt($av)));
# }
#
# $ID     = "GeigerLog";
# $date   = date("Y-m-d H:i:s");
# $CPM    = rand_pseudo_poisson(100);
# $CPS    = rand_pseudo_poisson(1.67);
# $T      = rand( 20, 25);
# $P      = rand(-20, 20);
# $H      = rand( 40, 60);
# $X      = rand( 80, 100);
#
# // GL-cfg: WiFiServer: Option auto defaults to 'CPM, CPS, Temp, Press, Humid'
# echo sprintf("%s, %s, %0.3f, %0.3f,,,,,,,%0.3f, %0.3f, %0.3f, %0.3f", $ID, $date, $CPM, $CPS, $T, $P, $H, $X);
# ?>
#
# <?php
# // use for: reset
# echo "Ok";
# ?>


__author__          = "ullix"
__copyright__       = "Copyright 2016, 2017, 2018, 2019, 2020, 2021, 2022"
__credits__         = [""]
__license__         = "GPL3"

from   gsup_utils           import *


def initWiFiServer():
    """Initialize WiFiServer"""

    fncname = "initWiFiServer: "

    dprint(fncname + "Initializing WiFiServer")
    setIndent(1)

    # set configuration
    if gglobs.WiFiServerIP          == "auto": gglobs.WiFiServerIP        = getGeigerLogIP()      # GL computer's own IP
    if gglobs.WiFiServerPort        == "auto": gglobs.WiFiServerPort      = 80                    # std Port (0...65535 ok)
    if gglobs.WiFiServerFolder      == "auto": gglobs.WiFiServerFolder    = "GL"                  # folder on WiFiServer device
    if gglobs.WiFiServerTimeout     == "auto": gglobs.WiFiServerTimeout   = 0.3                   # Failed readings: 0.18%)
    if gglobs.WiFiServerDataType    == "auto": gglobs.WiFiServerDataType  = "LAST"                # using 'lastdata' call, not avg for 'lastavg'
    if gglobs.WiFiServerVariables   == "auto": gglobs.WiFiServerVariables = "CPM, CPS, Temp, Press, Humid"   # simple default

    gglobs.WiFiServerTotalDur           = 0                           # duration of calling URL
    gglobs.WiFiServerTrials             = 0                           # max number of trials in calling URL

    gglobs.WiFiServerUrl                = getWiFiServerUrl()          # get like: 'http://10.0.0.78:4000/folder'
    gglobs.Devices["WiFiServer"][DNAME] = getDeviceNameWiFiServer()   # get like: 'GeigerLog WiFiServer' or 'None'

    if gglobs.Devices["WiFiServer"][DNAME] == "NONE":
        # not connected
        gglobs.Devices["WiFiServer"][CONN] = False
        msg = "No connection to Device at URL: '{}'".format(gglobs.WiFiServerUrl)
        rdprint(fncname + msg)

    else:
        # connected
        gglobs.Devices["WiFiServer"][CONN] = True
        msg = ""
        dprint(fncname + "connected to Device at URL: '{}', detected name: '{}'".format(
                                                        gglobs.WiFiServerUrl,
                                                        gglobs.Devices["WiFiServer"][DNAME],
                                                        ))

        setLoggableVariables("WiFiServer", gglobs.WiFiServerVariables)

    setIndent(0)

    return msg


def terminateWiFiServer():
    """opposit of init ;-)"""

    fncname = "terminateWiFiServer: "

    dprint(fncname)
    setIndent(1)

    gglobs.Devices["WiFiServer"][CONN] = False

    dprint(fncname + "Terminated")
    setIndent(0)


def getInfoWiFiServer(extended=False):
    """Info on the WiFiServer Device"""

    WiFiInfo  = ""
    WiFiInfo += "Configured Connection:        URL: '{}'   Timeout: {} sec\n".format(gglobs.WiFiServerUrl, gglobs.WiFiServerTimeout)

    if not gglobs.Devices["WiFiServer"][CONN]: return WiFiInfo + "<red>Device is not connected</red>"

    WiFiInfo +=     "Connected Device:             {}\n"        .format(gglobs.Devices["WiFiServer"][DNAME])
    WiFiInfo +=     "Configured Variables:         {}\n"        .format(gglobs.WiFiServerVariables)
    WiFiInfo +=     "Configured Mode [LAST, AVG]:  {}\n"        .format(gglobs.WiFiServerDataType)
    WiFiInfo +=     getTubeSensitivities(gglobs.WiFiServerVariables)

    if extended:
        WiFiInfo += "\n"
        WiFiInfo += "Calling URL: Max Repeats:     {}\n"        .format(gglobs.WiFiServerTrials)
        WiFiInfo += "Calling URL: Max Deltat:      {:0.1f} ms\n".format(gglobs.WiFiServerTotalDur)

    return WiFiInfo


def getWiFiServerUrl():
    """get url like 'http://10.0.0.78:4000' or 'http://10.0.0.78:4000/folder'"""

    # empty folder must not have leading "/"
    if gglobs.WiFiServerFolder == "": WSFolder = ""
    else:                             WSFolder = "/{}".format(gglobs.WiFiServerFolder)
    url = "http://{}:{}{}".format(gglobs.WiFiServerIP, gglobs.WiFiServerPort, WSFolder)
    # gdprint(url)

    return url


# calling wifi
def getUrlResponse(GET, trials=1):
    """get url antwort"""

    # GET == id:         10 ms (range: 6 ... 20 ms)
    # GET == reset:      10 ms (range: 8 ... 17 ms)
    # GET == lastdata:   70 ms (range: 60 ... 250 ms)
    # GET == lastavg:    same as lastdata
    #                    Spikes up to 250 ms every 60 sec very(!) regularly
    #                    On Raspi: ~55 ms, no (!) spikes!

    ################################################
    def lcl_exceptMsg(e, excmsg):
        """print the local exception message """

        exceptPrint(e, excmsg)
        if gglobs.devel:
            Queueprint("DVL {} {}{:9s}: '{}'".format(longstime(), fncname, excmsg, cleanHTML(e)))
    ################################################

    gurStart    = time.time()

    fncname     = "getUrlResponse: "
    url         = gglobs.WiFiServerUrl + GET
    response    = None
    trial       = 0

    while True:
        trial += 1
        try:
            xstart = time.time()
            with urllib.request.urlopen(url, timeout=gglobs.WiFiServerTimeout) as page:
                response = page.read().strip().decode("UTF-8")

            if gglobs.timing:
                xdur = 1000 * (time.time() - xstart)
                gglobs.ManuValue[2] = xdur
                rdprint(fncname + "duration: {:5.1f} ms  GET:{} response: ".format(xdur, GET), response)

                if trial == 2:
                    t2msg = "DVL {} {}{:9s}: '{}'".format(longstime(), fncname, "Success on 2nd trial", "")
                    rdprint(t2msg)
                    Queueprint(t2msg)

            break   # break the while loop on successful wifi call

        except TimeoutError as e:
            # NOTE: DEPRECATION:  "exception 'socket.timeout':  A deprecated alias of TimeoutError."
            lcl_exceptMsg(e, 'TimeOutError')

        except urllib.error.HTTPError as e:
            lcl_exceptMsg(e, 'HTTPError')

        except urllib.error.URLError as e:
            lcl_exceptMsg(e, 'URLError')

        except OSError as e:
            lcl_exceptMsg(e, "OSError")

        except Exception as e:
            lcl_exceptMsg(e, 'Exception')

        # break when - a) max trials reached
        #       or   - b) cumulative duration reaches half of cycle time
        if trial >= trials or (time.time() - gurStart) > (gglobs.logCycle * 0.5) :
            break

        time.sleep(0.01)


    TotalDur = 1000 * (time.time() - gurStart)
    msg = "after {} trial(s) in {:0.0f} ms from {}".format(trial, TotalDur, url)

    if trial    > gglobs.WiFiServerTrials:   gglobs.WiFiServerTrials   = trial
    if TotalDur > gglobs.WiFiServerTotalDur: gglobs.WiFiServerTotalDur = TotalDur

    # mdprint(fncname + "Trial:#{}, MaxTrials:{}, TotalDur:{:0.1f} ms, MaxTotalDur:{:0.1f} ms, Response:'{}'".format(
    #         trial,
    #         gglobs.WiFiServerTrials,
    #         TotalDur,
    #         gglobs.WiFiServerTotalDur,
    #         response,
    #         ))

    return response, msg


# "/lastdata" or "/lastavg"
def getValuesWiFiServer(varlist):
    """Read all WiFiServer data"""

    # request : http://serverip:port/folder/lastdata
    # response: CPM, CPS, CPM1st, CPS1st, CPM2nd, CPS2nd,  CPM3rd, CPS3rd, Temp, Press, Humid, Xtra
    # example : 100.496, 1.159,,,,,,,25.000, 1018.000, 54.000, 97.000

    #### local functions ######################################################
    def getValueWiFiServer(index):
        """check for missing value and make floats"""

        idata = data[index]
        val   = gglobs.NAN

        if idata > "":   # not a missing value
            try:
                val = float(idata)
            except Exception as e:
                exceptPrint(e, "index: {}".format(index))

        return val
    #### end local functions ##################################################

    gVstart   = time.time()

    fncname = "getValuesWiFiServer: "
    alldata = {}                                                                    # dict for return data
    thisGET = "/lastdata" if gglobs.WiFiServerDataType == "LAST" else "/lastavg"

    # get response on /lastxyz
    response, errmsg = getUrlResponse(thisGET, trials=3)

    if response is None:
        # got no response
        gglobs.LogReadingsFail += 1
        msg  = fncname + "NO DATA " + errmsg
        msg += " - Failed readings: {:0.3%}".format(gglobs.LogReadingsFail / gglobs.LogReadings)
        if gglobs.devel: Queueprint("DVL " + longstime() + " " + msg)
        edprint(fncname + msg)

    else:
        # got a response
        # rdprint(fncname + "response:{} errmsg:{}".format(response, errmsg))

        data = response.split(",")

        if len(data) >= len(gglobs.varsCopy):
            # got complete set of data
            for i, vname in enumerate(gglobs.varsCopy):
                if vname in varlist:
                    value = getValueWiFiServer(i)
                    alldata.update({vname: value})
                    # gdprint(fncname + "i={}, vname={}, value={}".format(i, vname, value))
        else:
            # got some data but not complete
            msg = fncname + "WiFiServer sent incomplete Data: expecting {} values, got only {}".format(len(gglobs.varsCopy), len(data))
            edprint(msg)
            Queueprint(msg)

    gVdur = 1000 * (time.time() - gVstart)

    if gglobs.timing:
        gglobs.ManuValue[1] = gVdur

    vprintLoggedValues(fncname, varlist, alldata, gVdur)

    return alldata


def setWiFiServerProperties():
    """Set Properties: Data type to request: LAST or AVG"""

    fncname = "setWiFiServerProperties: "

    dprint(fncname)
    setIndent(1)

    # Choose type of data
    lstaip2 = QLabel("Data as <b>LAST</b> value or last <b>AVG</b> value? &nbsp; &nbsp;")
    lstaip2.setAlignment(Qt.AlignLeft )
    b0      = QRadioButton("LAST")             # this is default
    b1      = QRadioButton("AVG")
    ttip    = "Select 'LAST' to get last value of data, or 'AVG' to get last 1 min average of values"
    b0.setToolTip(ttip)
    b1.setToolTip(ttip)
    if    gglobs.WiFiServerDataType == "LAST" : b0.setChecked(True)
    else:                                       b1.setChecked(True)

    # put radiobutton in H box
    layoutRB = QHBoxLayout()
    layoutRB.addWidget(b0)
    layoutRB.addWidget(b1)

    gridl=QGridLayout()
    gridl.setContentsMargins(10,10,10,10) # spacing around
    gridl.addWidget(lstaip2,     0, 0)
    gridl.addLayout(layoutRB,    0, 1)

    # Dialog box
    d = QDialog()
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setWindowTitle("Set WiFiServer Data Type")
    d.setWindowModality(Qt.WindowModal)
    d.setMinimumWidth(400)

    # Buttons
    bbox = QDialogButtonBox()
    bbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok )
    bbox.accepted.connect(lambda: d.done(1))
    bbox.rejected.connect(lambda: d.done(-1))

    okbtn = bbox.button(QDialogButtonBox.Ok)

    layoutV = QVBoxLayout(d)
    layoutV.addLayout(gridl)
    layoutV.addWidget(bbox)

    if gglobs.logging:         # no change of parameters when logging
        okbtn.setEnabled(False)

    retval = d.exec()
    #print("reval:", retval)

    if retval != 1:
        # ESCAPE pressed or Cancel Button clicked
        dprint(fncname + "Settings unchanged")

    else:
        fprint(header("WiFiServer Data Type"))

        # data type
        if b0.isChecked(): gglobs.WiFiServerDataType = "LAST"    # b0.isChecked()
        else:              gglobs.WiFiServerDataType = "AVG"     # b1.isChecked()
        msg = "WiFiServer Data Type:", "{}".format(gglobs.WiFiServerDataType)
        fprint(msg)
        dprint(msg)

    setIndent(0)


def pingWiFiServer():
    """Ping the WiFiServer"""

    # NOTE: Remember that a host may not respond to a ping (ICMP) request
    #       even if the host name is valid and the host exists!

    setBusyCursor()

    fprint(header("Pinging WiFiServer IP: " + gglobs.WiFiServerIP))
    QtUpdate() # to make the header visible right away

    presult, ptime = ping(gglobs.WiFiServerIP)

    pr = "Ping Result:"
    if presult:
        fprint (pr, "Success, ", ptime)
        playWav("ok")
    else:
        efprint(pr, "Failure")

    setNormalCursor()


# id
def getDeviceNameWiFiServer():
    """get the name of the external device"""
    # request url:  http://serverip:port/folder/id
    # return: response:  DeviceName  (example: 'GeigerLog WiFiServer', or: 'WiFiServer Simulator on Apache PHP')

    fncname  = "getDeviceNameWiFiServer: "

    response, errmsg = getUrlResponse("/id", trials=3)
    if response is None: devname = "NONE"
    else:                devname = cleanHTML(response)
    # gdprint("response: ", response, ", devname: ", devname, ", errmsg: ", errmsg)

    return devname


# reset
def resetWiFiServer():
    """Reset the GLWiFiServer"""

    fncname  = "resetWiFiServer: "

    setBusyCursor()

    fprint(header("Resetting WiFiServer IP: " + gglobs.WiFiServerIP))
    QtUpdate() # to make the header visible right away when resetting takes longer

    response = getUrlResponse("/reset", trials=3)
    if response is None: efprint("Failed")
    else:                fprint ("Successful")

    setNormalCursor()

