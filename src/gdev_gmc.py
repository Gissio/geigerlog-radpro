#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
gdev_gmc.py - GeigerLog commands to handle the Geiger counter

include in programs with:
    import gdev_gmc
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
__credits__         = ["Phil Gillaspy", "GQ"]
__license__         = "GPL3"

# credits:
# device command coding taken from:
# - Phil Gillaspy, https://sourceforge.net/projects/gqgmc/
# - and GQ documents 'GQ-RFC1201 GMC Communication Protocol. Re. 1.30'
# - and 'GQ-RFC1201,GQ Ver 1.40 Jan-2015' http://www.gqelectronicsllc.com/downloads/download.asp?DownloadID=62
# - also document 'GQ-RFC1801 GMC Communication Protocol' http://www.gqelectronicsllc.com/downloads/download.asp?DownloadID=91
# - and GQ's disclosure at: http://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=4948

from   gsup_utils           import *

# common to all GMC counters
cfgKeyLowDefault = {
#                                           Index
#    key                          Value,    from       to
    "Power"                   : [ None,     (0,        0 + 1) ],
    "Alarm"                   : [ None,     (1,        1 + 1) ],
    "Speaker"                 : [ None,     (2,        2 + 1) ],
    "BackLightTimeoutSeconds" : [ None,     (4,        4 + 1) ],     # see Light States
    "AlarmCPMValue"           : [ None,     (6,        6 + 1) ],     # AlarmlevelCPM (Hi, Lo Byte)
    "CalibCPM_0"              : [ None,     (8,        8 + 2) ],     # calibration_0 CPM Hi+Lo Byte
    "CalibuSv_0"              : [ None,     (10,      10 + 4) ],     # calibration_0 uSv 4 Byte
    "CalibCPM_1"              : [ None,     (14,      14 + 2) ],     # calibration_1 CPM Hi+Lo Byte
    "CalibuSv_1"              : [ None,     (16,      16 + 4) ],     # calibration_1 uSv 4 Byte
    "CalibCPM_2"              : [ None,     (20,      20 + 2) ],     # calibration_2 CPM Hi+Lo Byte
    "CalibuSv_2"              : [ None,     (22,      22 + 4) ],     # calibration_2 uSv 4 Byte
    "AlarmValueuSv"           : [ None,     (27,      27 + 4) ],     # Alarm Value in units of uSv/h, 4 bytes
    "AlarmType"               : [ None,     (31,      31 + 1) ],     # Alarmtype: CPM (=0) or µSv/h (=1)
    "SaveDataType"            : [ None,     (32,      32 + 1) ],     # History Save Data Type, see savedatatypes
    "MaxCPM"                  : [ None,     (49,      49 + 2) ],     # MaxCPM Hi + Lo Byte
    "LCDBackLightLevel"       : [ None,     (53,      53 + 1) ],     # Backlightlevel; seems to go from 0 ... 20
    "Battery"                 : [ None,     (56,      56 + 1) ],     # Battery Type: 1 is non rechargeable. 0 is chargeable.
    "Baudrate"                : [ None,     (57,      57 + 1) ],     # Baudrate, coded differently for 300 and 500/600 series
    "ThresholdCPM"            : [ None,     (62,      62 + 2) ],     # yes, at 62! Threshold in CPM (2 bytes)
    "ThresholdMode"           : [ None,     (64,      64 + 1) ],     # yes, at 64! Mode: 0:CPM, 1:µSv/h, 2:mR/h
    "ThresholduSv"            : [ None,     (65,      65 + 4) ],     # yes, at 65! Threshold in usv (4 bytes)
}


# only WiFi enabled counters
# FET (FastEstTime): on 500+ series: 5, 10, 15, 20, 30, 60=sec, 3=dynamic (firmware >= 2.28)
#                  : on 300, 320 series not defined
#

# cfgKeyHiDefault = {
cfgKeyHighDefault = {
# g.GMC_WifiIndex:          0         1           2                    3                      4                     5
#                           from      from      cfg256ndx             cfg512ndx              cfg512ndx              cfg256ndx
#                           GL cfg    counter   HI only GMC-320+V5    GMC-500/600            GMC500+2.24            only GMC-300S
#                                                                                                                   no WiFi but FET
    "SSID"              : [ None,     None,     (69,     69 + 16),    (69,     69 + 32) ,    (69,     69 + 64),     (69,     69 + 16) ],  # user specific value
    "Password"          : [ None,     None,     (85,     85 + 16),    (101,   101 + 32) ,    (133,   133 + 64),     (85,     85 + 16) ],  # user specific value
    "Website"           : [ None,     None,     (101,   101 + 25),    (133,   133 + 32) ,    (197,   197 + 32),     (101,   101 + 25) ],  # default: www.gmcmap.com
    "URL"               : [ None,     None,     (126,   126 + 12),    (165,   165 + 32) ,    (229,   229 + 32),     (126,   126 + 12) ],  # default: log2.asp
    "UserID"            : [ None,     None,     (138,   138 + 12),    (197,   197 + 32) ,    (261,   261 + 32),     (138,   138 + 12) ],  # user specific value
    "CounterID"         : [ None,     None,     (150,   150 + 12),    (229,   229 + 32) ,    (293,   293 + 32),     (150,   150 + 12) ],  # user specific value

    "Period"            : [ None,     None,     (162,   162 +  1),    (261,   261 +  1) ,    (325,   325 +  1),     (253,   253 +  1) ],  # value can be 1 ... 255
    "WiFi"              : [ None,     None,     (163,   163 +  1),    (262,   262 +  1) ,    (326,   326 +  1),     (253,   253 +  1) ],  # WiFi On=1 Off=0

    "FET"               : [ None,     None,     (253,   253 +  1),    (510,   510 +  1) ,    (328,   328 +  1),     (69,    69  +  1) ],  # FET
    "DEADTIME_ENABLE"   : [ None,     None,     (253,   253 +  1),    (510,   510 +  1) ,    (335,   335 +  1),     (253,   253 +  1) ],  # enable dead time setting (fw 2.41+)
    "DEADTIME_TUBE1"    : [ None,     None,     (253,   253 +  2),    (510,   510 +  2) ,    (336,   336 +  2),     (253,   253 +  2) ],  # DEADTIME_TUBE1_HIBYTE, LOBYTE
    "DEADTIME_TUBE2"    : [ None,     None,     (253,   253 +  2),    (510,   510 +  2) ,    (338,   338 +  2),     (253,   253 +  2) ],  # DEADTIME_TUBE2_HIBYTE, LOBYTE
    "TARGET_HV"         : [ None,     None,     (253,   253 +  2),    (510,   510 +  2) ,    (346,   346 +  2),     (253,   253 +  2) ],  # Voltage read out
    "HV_CALIB"          : [ None,     None,     (253,   253 +  1),    (510,   510 +  1) ,    (348,   348 +  1),     (253,   253 +  1) ],  # HV_CALIB (?)
    "DATETIME"          : [ None,     None,     (253,   253 +  1),    (379,   379 +  6) ,    (348,   348 +  1),     ( 70,    70 +  6) ],  # DateTime (for what?) YY,MM,DD,hh,mm,ss
}
# cfgKeyHi = cfgKeyHiDefault.copy()    # shallow copy


# # only WiFi enabled counters
# cfgKeyHighDefault = {
# # gglobs.GMC_WifiIndex:  0         1           2                    3                      4
# #                   GMCmap    cfgMap      cfg256ndx            cfg512ndx
# #                   from GL   from GMC
# #                   config    device    # only GMC-320+V5     # GMC-500/600          # GMC500+2.24
#     "SSID"      : [ None,     None,     (69,     69 + 16),    (69,     69 + 32) ,    (69,     69 + 64) ],
#     "Password"  : [ None,     None,     (85,     85 + 16),    (101,   101 + 32) ,    (133,   133 + 64) ],
#     "Website"   : [ None,     None,     (101,   101 + 25),    (133,   133 + 32) ,    (197,   197 + 32) ],
#     "URL"       : [ None,     None,     (126,   126 + 12),    (165,   165 + 32) ,    (229,   229 + 32) ],
#     "UserID"    : [ None,     None,     (138,   138 + 12),    (197,   197 + 32) ,    (261,   261 + 32) ],
#     "CounterID" : [ None,     None,     (150,   150 + 12),    (229,   229 + 32) ,    (293,   293 + 32) ],

#     # entries for 320V5 modified: 112 -> 162, 113 -> 163                                                                                             not on 300 series
#     "Period"    : [ None,     None,     (162,   162 +  1),    (261,   261 +  1) ,    (325,   325 +  1) ], # 0 ... 255
#     "WiFi"      : [ None,     None,     (163,   163 +  1),    (262,   262 +  1) ,    (326,   326 +  1) ], # WiFi On=1 Off=0
#     "FET"       : [ None,     None,     (255,   255 +  1),    (263,   263 +  1) ,    (328,   328 +  1) ], # FET
#     # FET (FastEstTime): on 500+ series: 5, 10, 15, 20, 30, 60=sec, 3=dynamic (firmware >= 2.28)
#     #                  : on 300, 320 series not defined
# }


# the History mode of saving
savedatatypes = (
                    "OFF (no history saving)",
                    "CPS, save every second",
                    "CPM, save every minute",
                    "CPM, save hourly average",
                    "CPS, save every second if exceeding threshold",
                    "CPM, save every minute if exceeding threshold",
                )

# Light states
LightState    = (
                    "Light: OFF",
                    "Light: ON",
                    "Timeout: 1",
                    "Timeout: 3",
                    "Timeout: 10",
                    "Timeout: 30",
                )

# to keep track of illegal entries in cal* fields
validMatrix   = {
                    "cal0cpm" : True ,
                    "cal0usv" : True ,
                    "cal1cpm" : True ,
                    "cal1usv" : True ,
                    "cal2cpm" : True ,
                    "cal2usv" : True ,
                }


def initGMC():
    """
    Sets configuration, gets counter version, verifies communication
    Return: on success: ""
            on failure: <errmessage>
    """

    ## local ###################################################################################
    def lcl_getGMC_SerialConfig(device):
        """
        gets the USB-to-Serial port name and baudrate for GMC
        This tests for a match of USB's vid + pid associated with device. If match found,
        then it tests for proper communication checking with specific call/answers
        """

        # output by: lsusb
        # GMC-300E+:
        #   bcdUSB               1.10
        #   idVendor           0x1a86 QinHeng Electronics
        #   idProduct          0x7523 HL-340 USB-Serial adapter
        #   iManufacturer           0
        #   iProduct                2 USB Serial
        #
        # GMC-500+:
        #   bcdUSB               1.10
        #   idVendor           0x1a86 QinHeng Electronics
        #   idProduct          0x7523 HL-340 USB-Serial adapter
        #   iManufacturer           0
        #   iProduct                2 USB2.0-Serial

        fncname   = "initGMC - lcl_getGMC_SerialConfig: "

        dprint(fncname + "for device: '{}'".format(device))
        setIndent(1)

        portfound   = None
        baudfound   = None
        tmplt_port  = "Checking Port:{},  device:{}, product:{}, vid:{}, pid:{}"
        tmplt_found = "Found: Port:{}, Baud:{}, description:{}, vid:0x{:04x}, pid:0x{:04x}"
        tmplt_match = "Found Chip ID match for device '{}' at: Port:'{}' - vid:0x{:04x}, pid:0x{:04x}"

        ports = getPortList(symlinks=False)

        for port in ports:
            if  port.vid == 0x1a86 and port.pid == 0x7523:
                gdprint(fncname, tmplt_match.format(device, port, port.vid, port.pid))
                baudrate = lcl_GMC_autoBaudrate(port.device)     # like: port.device: /dev/ttyUSB0
                if baudrate is not None and baudrate > 0:
                    portfound = port.device
                    baudfound = baudrate
                    break

        if portfound is not None:
            gdprint(fncname + tmplt_found.format(portfound, baudfound, port.description, port.vid, port.pid))

        setIndent(0)
        return (portfound, baudfound)


    def lcl_GMC_autoBaudrate(usbport):
        """
        Tries to find a proper baudrate by testing for successful serial communication
        at up to all possible baudrates, beginning with the highest.
        return: returnBR = None     :   serial error
                returnBR = 0        :   No device found
                returnBR = <number> :   highest baudrate which worked
        """

        # NOTE: the device port can be opened without error at any baudrate permitted by the Python code,
        # even when no communication can be done, e.g. due to wrong baudrate. Therefore we test for
        # successful communication by checking for the return string for getVersion beginning with 'GMC'.


        fncname = "lcl_GMC_autoBaudrate: "

        dprint(fncname + "Testing port: '{}'".format(usbport))
        setIndent(1)

        baudrates = gglobs.GMCbaudrates[:]
        baudrates.sort(reverse=True) # to start with highest baudrate

        loop    = 1
        foundit = False
        brec    = None
        while loop <= 3:
            for baudrate in baudrates:
                dprint(fncname + "Trying baudrate: ", baudrate)
                try:
                    with serial.Serial(usbport, baudrate=baudrate, timeout=0.3, write_timeout=0.5) as ABRser:
                        brec = getGMC_Version(ABRser)    # try to get the GMC device version
                except Exception as e:
                    errmessage1 = fncname + "FAILURE: Reading from device; returning None"
                    exceptPrint(e, errmessage1)
                    setIndent(0)
                    return None     # Python's None signals communication error

                if brec.startswith("GMC"):
                    # it is a GMC device
                    foundit = True
                    dprint(fncname + "Success - found GMC device '{}' using baudrate {}".format(gglobs.GMCDeviceDetected, baudrate))

                    # now check for a Model definition
                    if gglobs.GMC_ID[0] is not None:
                        if brec.startswith(gglobs.GMC_ID[0]):
                            # it is the specified Model
                            foundit = True
                            dprint(fncname + "Success - matches Model '{}' ".format(gglobs.GMC_ID[0]))

                            # now check for a SerialNumber definition
                            if gglobs.GMC_ID[1] is not None:
                                serno = getGMC_SerialNumber(usbport, baudrate)
                                if serno.startswith(gglobs.GMC_ID[1]):
                                    # it is the specified SerialNo
                                    foundit = True
                                    dprint(fncname + "Success - matches SerialNumber '{}' ".format(gglobs.GMC_ID[1]))
                                    break   # the for loop
                                else:
                                    # not the specified SerialNo
                                    foundit = False
                        else:
                            # not the specified Model
                            foundit = False
                    else:
                        # a GMC device was found ok, and a specific Model was not requested
                        break   # the for loop
                else:
                    # not a GMC device found; try next baudrate
                    foundit = False

            if foundit:
                returnBR = baudrate
                break # the while loop

            cdprint("fail in loop #{} - repeating".format(loop))

            loop     += 1
            returnBR  = 0
            dprint(fncname + "FAILURE No matching device detected, baudrate: {}".format(returnBR))

        setIndent(0)
        return returnBR

    ## end local ##################################################################################


    global cfgKeyLow, cfgKeyHigh

    fncname                  = "initGMC: "
    dprint(fncname)
    setIndent(1)

    gglobs.GMCDeviceName     = "GMC Device"
    gglobs.GMC_configsize    = "auto"
    gglobs.GMC_maxdur        = 0

    gglobs.GMCLast60CPS      = np.full(60, gglobs.NAN)  # storing last 60 sec of CPS values, filled with all NAN
    gglobs.GMCEstFET         = np.full(60, 0)           # storing last 60 sec of CPS values, filled with all 0

    cfgKeyLow                = cfgKeyLowDefault.copy()  # shallow copy
    cfgKeyHigh               = cfgKeyHighDefault.copy() # shallow copy

    cfgKeyHigh["SSID"]     [0] = str(gglobs.WiFiSSID)
    cfgKeyHigh["Password"] [0] = str(gglobs.WiFiPassword)
    cfgKeyHigh["Website"]  [0] = str(gglobs.gmcmapWebsite)
    cfgKeyHigh["URL"]      [0] = str(gglobs.gmcmapURL)
    cfgKeyHigh["UserID"]   [0] = str(gglobs.gmcmapUserID)
    cfgKeyHigh["CounterID"][0] = str(gglobs.gmcmapCounterID)
    cfgKeyHigh["Period"]   [0] = str(gglobs.gmcmapPeriod)
    cfgKeyHigh["WiFi"]     [0] = str(gglobs.gmcmapWiFiSwitch)
    cfgKeyHigh["FET"]      [0] = str(gglobs.GMC_FastEstTime)  # is re-defined below after device properties were detected

    if gglobs.GMC_usbport  == "auto":  gglobs.GMC_usbport   = None
    if gglobs.GMC_baudrate == "auto":  gglobs.GMC_baudrate  = 115200
    if gglobs.GMC_timeoutR == "auto":  gglobs.GMC_timeoutR  = 3
    if gglobs.GMC_timeoutW == "auto":  gglobs.GMC_timeoutW  = 1
    if gglobs.GMC_ID       == "auto":  gglobs.GMC_ID        = (None, None)

    # edprint(fncname + "gglobs.GMC_usbport: ", gglobs.GMC_usbport)
    if  gglobs.GMC_usbport == None:
        # user has not defined a port; auto-find it now

        port, baud = lcl_getGMC_SerialConfig("GMC")
        # rdprint(fncname + "port, baud: ", port, baud)
        if port is None or baud is None:
            setIndent(0)
            return "A {} was not detected.".format(gglobs.GMCDeviceName)
        else:
            gglobs.GMC_usbport          = port
            gglobs.GMC_baudrate         = baud
            gglobs.Devices["GMC"][0]    = gglobs.GMCDeviceDetected         # detected at getGMC_Version()

            # Example fprint:
            # GMC Device 'GMC-300Re 4.54' was detected at port: /dev/ttyUSB0 and baudrate: 57600
            fprint("{} '{}' was detected at port: {} and baudrate: {}".format(
                                                                              gglobs.GMCDeviceName,
                                                                              gglobs.GMCDeviceDetected,
                                                                              gglobs.GMC_usbport,
                                                                              gglobs.GMC_baudrate))
    else:
        # user has defined a port; use it if it exists, and don't try anything else

        if not os.path.exists(gglobs.GMC_usbport):
            # edprint("den shit gibbes nich")
            return "The user defined port '{}' does not exist".format(gglobs.GMC_usbport)
        else:
            # use the port configured by the user
            # Example fprint:   A GMC Device was user configured for port: '/dev/ttyUSB0'
            fprint("A device {} was <b>user configured</b> for port: '{}'".format(
                                                                                    gglobs.GMCDeviceName,
                                                                                    gglobs.GMC_usbport,))
            baudrate = lcl_GMC_autoBaudrate(gglobs.GMC_usbport)
            if baudrate is not None and baudrate > 0:
                gglobs.GMC_baudrate = baudrate
                fprint("{} '{}' was detected at port: {} and baudrate: {}".format(
                                                                                gglobs.GMCDeviceName,
                                                                                gglobs.GMCDeviceDetected,
                                                                                gglobs.GMC_usbport,
                                                                                gglobs.GMC_baudrate))
            else:
                return "A {} was not detected at user defined port '{}'.".format(
                                                                                gglobs.GMCDeviceName,
                                                                                gglobs.GMC_usbport)

    # a serial connection does exist
    returnmsg = ""
    gglobs.Devices["GMC"][DNAME] = gglobs.GMCDeviceDetected
    gglobs.Devices["GMC"][CONN]  = True

    # set device details and variables
    getGMC_DeviceProperties()
    setLoggableVariables("GMC", gglobs.GMC_Variables)

    # set FET to new setting
    cfgKeyHigh["FET"][0] = str(gglobs.GMC_FastEstTime)

    # turn Heartbeat --> OFF
    # just in case it had been turned on!
    turnGMC_HeartbeatOFF()

    # ### for heartbeat testing only! ################
    # ### turn Heartbeat --> ON
    # turnGMC_HeartbeatON()
    # ################################################

    setIndent(0)

    return returnmsg

    #
    # using AT code for 8266 chip in WiFi enabled counters
    #
    # getResponseAT(b'<AT>>')                 # b'AT\r\r\n\r\nOK\r\n\n'
    # getResponseAT(b'<AT+RST>>')             # b'AT+RST\r\r\n\r\nOK\r\nWIFI DISCONNECT\r\n\r\n ets Jan  8 2013,rst cause:2, boot mode:(3,6)\r\n\r\nload 0x40100000, len 1856, room 16 \r\ntail 0\r\nchksum 0x63\r\nload 0x3ffe8000, len 776, room 8 \r\ntail 0\r\nchksum 0x02\r\nload 0x3ffe8310, len 552, room 8 \r\ntail 0\r\nchksum 0x7'
    # # getResponseAT(b'<AT+GMR>>')             # b'AT+GMR\r\r\nAT version:1.2.0.0(Jul  1 2016 20:04:45)\r\nSDK version:1.5.4.1(39cb9a32)\r\nAi-Thinker Technology Co. Ltd.\r\nDec  2 2016 14:21:16\r\nOK\r\nWIFI DISCONNECT\r\nWIFI CONNECTED\r\nWIFI GOT IP\r\n\n'
    # # getResponseAT(b'<AT+CIFSR>>')           # b'AT+CIFSR\r\r\n+CIFSR:APIP,"192.168.4.1"\r\n+CIFSR:APMAC,"a2:20:a6:36:ac:ba"\r\n+CIFSR:STAIP,"10.0.0.42"\r\n+CIFSR:STAMAC,"a0:20:a6:36:ac:ba"\r\n\r\nOK\r\n\n'
    # #                                         # FritzBox: GMC-500+: A0:20:A6:36:AC:BA == STAMAC!
    # getResponseAT(b'<AT+CIPSTART="TCP","10.0.0.20",8000>>')
    # getResponseAT(b'<AT+CIFSR>>')

    # # getResponseAT(b'<AT+CIPMODE=0>>')
    # # getResponseAT(b'<AT+CIPMODE=1>>')     # 1 führt zur Blockade von CIPSTART

    # # getResponseAT(b'<AT+CWLIF>>')         # b'AT+CWLIF\r\r\n\r\nOK\r\n\n'
    # # getResponseAT(b'<AT+CWSAP?>>')        # b'AT+CWSAP?\r\r\n+CWSAP:"AI-THINKER_36ACBA","",1,0,4,0\r\n\r\nOK\r\nWIFI GOT IP\r\n\n'
    # # getResponseAT(b'<AT+CWMODE?>>')       # b'AT+CWMODE?\r\r\n+CWMODE:3\r\n\r\nOK\r\nWIFI DISCONNECT\r\nWIFI CONNECTED\r\nWIFI GOT IP\r\n\n'
    # # getResponseAT(b'<AT+CWMODE=?>>')      # b'AT+CWMODE=?\r\r\n+CWMODE:(1-3)\r\n\r\nOK\r\nWIFI GOT IP\r\n\n'

    # # getResponseAT(b'<AT+CWLIF="mac">>')   # --> error                         ??? not avialable?
    # # getResponseAT(b'<AT+CMD>>')           # b'AT+CMD?\r\r\n\r\nERROR\r\n\n'   ??? not avialable?
    # # getResponseAT(b'<AT+CMD?>>')          # b'AT+CMD?\r\r\n\r\nERROR\r\n\n'   ??? not avialable?


def xxxmakeSerialGMC():
    """Make the serial connection for the GMC counter"""

    fncname = "makeSerialGMC: "


    portmsg        = "port='{}' baudrate={} timeoutR={} timeoutW={}".format(
                                gglobs.GMC_usbport,
                                gglobs.GMC_baudrate,
                                gglobs.GMC_timeoutR,
                                gglobs.GMC_timeoutW
                            )
    FailMessage    = "Exception on connecting using: " + portmsg

    try:
        # raise Exception("testing")
        # gglobs.GMCser is like:
        #   Serial<id=0x7f2014d371d0, open=True>(port='/dev/ttyUSB0', baudrate=115200, bytesize=8,
        #   parity='N', stopbits=1, timeout=20, xonxoff=False, rtscts=False, dsrdtr=False)
        # takes < 0.8 ms
        gglobs.GMCser = serial.Serial(  gglobs.GMC_usbport,
                                        gglobs.GMC_baudrate,
                                        timeout=gglobs.GMC_timeoutR,
                                        write_timeout=gglobs.GMC_timeoutW)

        gotException = False
        FailMessage  = ""

    except serial.SerialException as e:
        gotException = True
        exceptPrint(e, fncname + "SerialException: " + FailMessage)
        terminateGMC()

    except Exception as e:
        gotException = True
        exceptPrint(e, fncname + "Exception: " + FailMessage)
        terminateGMC()

    return (gotException, FailMessage)


def terminateGMC():
    """close Serial connection if open, and reset some properties"""

    start = time.time()

    fncname = "terminateGMC: "

    dprint(fncname )
    setIndent(1)

    if gglobs.GMCser != None:
        try:        gglobs.GMCser.close()
        except:     edprint(fncname + "Failed trying to close Serial Connection; terminating anyway", debug=True)

    gglobs.GMCser          = None
    gglobs.GMC_usbport     = "auto"
    gglobs.GMC_baudrate    = "auto"
    gglobs.GMC_timeoutR    = "auto"
    gglobs.GMC_timeoutW    = "auto"
    gglobs.GMC_configsize  = "auto"

    gglobs.Devices["GMC"][CONN] = False

    dprint(fncname + "Terminated")
    setIndent(0)


#
# Commands and functions implemented in GMC device
#

def getGMC_Version(GMCserial):
    """Get GMC hardware model and firmware version"""

    # send <GETVER>> and read 14 bytes
    # returns total of 14 bytes ASCII chars from GQ GMC unit.
    # includes 7 bytes hardware model and 7 bytes firmware version.
    # e.g.: 'GMC-300Re 4.20'
    #
    # see: http://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=4948 Reply #30
    # Quote EmfDev:
    # "On the 500 and 600 series, the GETVER return can be any length.
    # So far its only 14 bytes or 15 bytes. But it should return any given
    # model name completely so the length is variable.
    # And the '+' sign is included in the model name. e.g. GMC500+Re 1.10
    # But I don't think the 300 or 320 has been updated so maybe you can ask
    # support for the fix."
    #
    # ATTENTION: new counters may deliver 15 bytes and more
    #            e.g. "GMC-500+Re 1.18"         --> 15 bytes
    #                 "GMC-320+V5\x00RRe 5.73"  --> 19 bytes    NOTE: the zero WITHIN the string!

    fncname     = "getGMC_Version: "
    errmessage  = None

    # dprint(fncname + " -----------------------------------------------------")
    setIndent(1)

    try:
        GMCserial.write(b'<GETVER>>')
    except Exception as e:
        errmessage = fncname + "ERROR: Failure writing to GMCserial"
        exceptPrint(e, errmessage)
        setIndent(0)
        return errmessage

    try:
        brec = GMCserial.read(14)   # may leave bytes in the pipeline
        while True:
            time.sleep(0.1)
            cnt = GMCserial.in_waiting
            if cnt == 0: break
            brec += GMCserial.read(cnt)

    except Exception as e:
        errmessage = fncname + "ERROR: Serial communication error"
        exceptPrint(e, errmessage)
        setIndent(0)
        return errmessage

    try:
        GMCversion = brec.decode("UTF-8").replace("\x00", "?") # latest GMC-320+V5 has Null char in name!
        gglobs.GMCDeviceDetected = GMCversion
    except Exception as e:
        errmessage = fncname  + "ERROR getting Version - Bytes are not ASCII: " + str(brec)
        exceptPrint(e, errmessage)
        setIndent(0)
        return errmessage + "brec: " + str(brec)


    ###############################################################################
    ### FOR TESTING ONLY - start GL with command: 'testing' #########################
    ### use in combination with testing setting in getGMC_Config()
    # if gglobs.testing:
    #     pass
    #     recd = "GMC-300Re 3.20"
        # recd = "GMC-300Re 4.20"
        # recd = "GMC-300Re 4.22"
        # recd = "GMC-320Re 3.22"            # device used by user katze
        # recd = "GMC-320Re 4.19"
        # recd = "GMC-320Re 5.xx"            # with WiFi
        # recd = 'GMC-320+V5\x00RRe 5.73'    # b'GMC-320+V5\x00RRe 5.73' # from Tom Johnson's new GMC-320
        # recd = "GMC-500Re 1.00"
        # recd = "GMC-500Re 1.08"
        # recd = "GMC-500+Re 1.0x"
        # recd = "GMC-500+Re 1.18"
        # recd = "GMC-500+Re 2.28"           # latest version as of 2021-10-20
        # recd = "GMC-600Re 1.xx"
        # recd = "GMC-600+Re 2.xx"           # fictitious device; not (yet) existing
        #                                     simulates the bug in the 'GMC-500+Re 1.18'
        # recd = None
        # GMCversion = recd
    ### TESTING END #################################################################
    ###############################################################################

    if len(brec) == 0:
        dprint(fncname + "FAILURE: No data returned")
    else:
        mdprint(fncname + "len:{} bytes, rec:{}, GMCversion:'{}', errmessage:'{}'".format(
                        len(brec), brec, GMCversion, errmessage))

    setIndent(0)

    return GMCversion


def cleanupGMC(ctype = "Dummy"):
    """clearing the pipeline"""

    if gglobs.Devices["GMC"][CONN] :
        dprint("cleanupGMC: '{}': Cleaning pipeline '{}'".format(gglobs.GMCDeviceDetected, ctype))
        if   ctype == "before": getGMC_ExtraByte()
        elif ctype == "after":  getGMC_ExtraByte()
        else:                   getGMC_ExtraByte() # whatever; just as placeholder


def getValuesGMC(varlist):
    """get all data for vars in varlist from a GMC Geiger counter"""

    ########################################################################
    # Extended stuff; not implemented - keep as reminder:
    #
    #   True counter values are returned only for CPM, CPS, CPM1st, CPS1st, CPM2nd, CPS2nd,
    #   Other returns (not disclosed in config):
    #       CPM3rd: CPM calculated from last 60 CPS
    #       CPS3rd: Counts per MINUTE with simulated Fast Estimate Time
    #       Humid:  Duration of calling all vars (totaldur)
    #       Xtra:   Delta Time "computer minus device" (negative if device is faster than computer)
    #
    #     elif vname == "CPM3rd": alldata[vname] = getGMC_CPMfromCPS(alldata, "CPS1st") # CPM calculated from last 60 CPS; requires CPS1st!
    #     elif vname == "CPS3rd": alldata[vname] = getGMC_CPMwithFET(alldata, "CPS1st") # Counts per MINUTE with simulated Fast Estimate Time; requires CPS1st!
    #     elif vname == "Xtra":   alldata[vname] = getGMC_DeltaTime()[0]                # Delta Time "computer minus device" (negative if device is faster than computer)
    #
    ########################################################################

    fncname = "getValuesGMC: "
    # cdprint(fncname, varlist)

    alldata = {}

    if os.path.exists(gglobs.GMC_usbport):
        totalstart    = time.time()
        setIndent(1)
        keysVarsCopy = list(gglobs.varsCopy.keys())[0:6] # first 6 vars only
        for vname in varlist:
            if vname in keysVarsCopy: alldata[vname] = getValueGMCvar(vname)
        setIndent(0)
        totaldur = 1000 * (time.time() - totalstart)    # sum of all GMC data calls

    else:
        msg = "The USB port '{}' does NOT exist.".format(gglobs.GMC_usbport)
        Queueprint(msg)
        dprint(fncname + msg)
        totaldur = -1

    vprintLoggedValues(fncname, varlist, alldata, totaldur)

    return alldata


def getValueGMCvar(vname):
    """Write to and read from device and convert to value; return value"""
    # NOTE: MUST NOT call with vname in ["CPM3rd", "CPS3rd", "Temp", "Press", "Humid", "Xtra"]

    # for the 300series counter:
    # send <GETCPM>> and read 2 bytes
    # In total 2 bytes data are returned from GQ GMC unit as a 16 bit unsigned integer.
    # The first byte is MSB byte data and second byte is LSB byte data.
    #   e.g.: 00 1C  -> the returned CPM is 28
    #   e.g.: 0B EA  -> the returned CPM is 3050
    #
    # send <GETCPS>> and read 2 bytes
    # In total 2 bytes data are returned from GQ GMC unit
    #
    # my observation: highest bit in MSB is always set -> mask out!
    # e.g.: 80 1C  -> the returned CPS is 28
    # e.g.: FF FF  -> 3F FF -> the returned maximum CPS is 16383
    #                 or 16383 * 60 = 982980 CPM
    #
    # for the 500, 600 series counter:
    # send <GETCPM>> and read 4 bytes -- all GETCPM* commands return 4 bytes!


    # local function #######################################################
    def getCommandCode(vname):
        """return tuple: (<GET_CallCode>>, maskHighBit)"""

        CmdCode = (b'', False)  # default when illegal vname used

        if   vname == "CPM":    CmdCode = (b'<GETCPM>>' , False ) # the normal CPM call; on GMC-500+ gets CPM as sum of both tubes
        elif vname == "CPS":    CmdCode = (b'<GETCPS>>' , True  ) # the normal CPS call; on GMC-500+ gets CPM as sum of both tubes
        elif vname == "CPM1st": CmdCode = (b'<GETCPML>>', False ) # get CPM from High Sensitivity tube; that should be the 'normal' tube
        elif vname == "CPS1st": CmdCode = (b'<GETCPSL>>', True  ) # get CPS from High Sensitivity tube; that should be the 'normal' tube
        elif vname == "CPM2nd": CmdCode = (b'<GETCPMH>>', False ) # get CPM from Low  Sensitivity tube; that should be the 2nd tube in the 500+
        elif vname == "CPS2nd": CmdCode = (b'<GETCPSH>>', True  ) # get CPS from Low  Sensitivity tube; that should be the 2nd tube in the 500+

        return CmdCode
    ########################################################################

    gVstart   = time.time()

    fncname = "getValueGMCvar: "

    if not os.path.exists(gglobs.GMC_usbport):
        # den shit gibbes nich
        # kann passieren, wenn nach Start der USB Stecker gezogen wird!
        msg = "The Serial port '{}' does not exist. Cannot read var: '{}'".format(gglobs.GMC_usbport, vname)
        Queueprint(msg)
        dprint(fncname + msg)

        return gglobs.NAN

    else:
        flagException = False
        comment       = ""              # " --> Temp" if gglobs.timing else ""
        trial         = 0               # trial counter
        trials        = 3               # limit no of trials

        # get CmdCode for the variable vname
        wcommand, maskHighBit = getCommandCode(vname)

        usbport       = gglobs.GMC_usbport
        baudrate      = gglobs.GMC_baudrate
        timeout       = 0.3                         # gglobs.GMC_timeoutR
        write_timeout = 0.5                         # gglobs.GMC_timeoutW

        # try multi-times; on failure return b''
        while True:
            trial += 1

            try:
                tstart = time.time()

                ##Windows CANNOT open when already opened elsewhere!
                with serial.Serial(usbport, baudrate=baudrate, timeout=timeout, write_timeout=write_timeout) as gVser:
                    bwrt   = gVser.write(wcommand)        # bwrt: Number of bytes written, type: <class 'int'>
                    brec   = gVser.read(gglobs.GMC_Bytes) # brec: data record of           type: <class 'bytes'>

                tdur   = 1000 * (time.time() - tstart)        # duration in millisec
                break                                         # break the while loop on first success

            except Exception as e:
                exceptPrint(e, fncname + "FAILURE getting GMC data for variable '{}' ".format(vname))
                brec          = b''
                flagException = True
                tdur          = -1


            # break when too many trials, or cumulative duration reaches half of cycle time.
            # this is only for single var; there could be 6 calls total for vars => 0.5 sec
            if trial >= trials or (time.time() - gVstart) > (gglobs.logCycle * 0.1) : break

            time.sleep(0.05)

    # # GMC_maxdur tracking
    # if gglobs.devel:
    #     if tdur > gglobs.GMC_maxdur:
    #         gglobs.GMC_maxdur = tdur
    #         Queueprint("DVL {} {:9s} {:0.2f} ms".format(longstime(), "GMC_maxdur single call:", gglobs.GMC_maxdur)
    #
    #     cdprint(fncname + "Trial:#{} Var:{:6s}= {:20s} dur[ms]:{:<6.2f} maxdur[ms]:{:<6.2f} {}".format(
    #                                                     trial,
    #                                                     vname,
    #                                                     str(brec),
    #                                                     tdur,
    #                                                     gglobs.GMC_maxdur,
    #                                                     comment))

    if len(brec) == gglobs.GMC_Bytes:
        # ok, got correct no of bytes, either 2 or 4
        if    gglobs.GMC_Bytes == 4:
            value = ((brec[0]<< 8 | brec[1]) << 8 | brec[2]) << 8 | brec[3]

        elif  gglobs.GMC_Bytes == 2:
            value = brec[0] << 8 | brec[1]
            if maskHighBit : value = value & 0x3fff     # mask out high bits; ONLY for CPS* calls on 300 series counters

    else:
        # too few or too many bytes
        msg = fncname + "FAILURE: "
        if brec == b'':
            # no bytes were returned -- perhaps timeout; perhaps Exception
            if flagException:                        msg += "Exception"
            if tdur >= 1000 * gglobs.GMC_timeoutR:   msg += "Timeout ({:0.1f} ms)".format(tdur)
            msg += " - No Bytes received "
        else:
            # bytes missing or too many
            msg += "Wrong Bytecount: got {} bytes, expected {}!".format(len(brec), gglobs.GMC_Bytes)

        if gglobs.devel:
            edprint(msg)
            Queueprint("DVL " + longstime() + " " + msg)

        value = gglobs.NAN

    # if 0:   # use 0 or 10 to block or show
    #     duration = 1000 * (time.time() - gVstart)
    #     cdprint(fncname + "cmd:{:13s} GMC_Bytes:{:1d} maskHighBit:{:5s} brec:{:20s} value:{:6.3f} dur:{:0.1f} ms (max:{:0.1f} ms)".
    #         format( str(wcommand),
    #                 gglobs.GMC_Bytes,
    #                 str(maskHighBit),
    #                 str(brec),
    #                 value,
    #                 duration,
    #                 gglobs.GMC_maxdur,
    #               )
    #            )

    return scaleVarValues(vname, value, gglobs.ValueScale[vname])


def getGMC_CPMwithFET(valuedict, vname):
    """calculate CPM from the last N values of CPS;
    N is used as in Fast Estimate Time, i.e. N = FET = 3, 5, 10, 15, 20, 30, 60
    used in getValuesGMC:  cps data from CPS1st, CPM mapped to CPM"""

    # from: http://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=9506
    # reply#29, EmfDev:

    #     The calculation for fast Estimate is:
    #     Let X = duration in seconds
    #     Estimated CPM = SUM(Last X seconds CPS reading) * (60/X)
    #     e.g. for 5 sec fast estimate. (e.g. [1, 0, 1, 0, 2] ==> sum = 4)
    #     Estimated CPM = 4 * 60/5 = 4*12 = 48.

    #     for Dynamic Fast Estimate:
    #     x varies depending on how stable the data is from 3 seconds to 60 seconds.
    #     If the latest few CPS is significantly higher than the average CPS then the
    #     x goes to 3 for 3 seconds and then starts going to 60 as long as the CPS is
    #     stable or around certain range from the average CPS. If dynamic estimate
    #     reaches 60 seconds reading then it becomes the same as 60 second reading,
    #     then when there is sudden change in CPS again it will trigger to change
    #     back to estimate faster.

    #     These numbers are called "estimate" for a reason and so the accuracy is not
    #     that great. Some users who survey the unknown do not want to put the unit
    #     there for too long and just wants to get an estimate or check if there is
    #     radiation.


    try:
        lastcps = valuedict[vname]
    except Exception as e:
        exceptPrint(e, "getGMC_CPMwithFET: vname: {}".format(vname))
        return gglobs.NAN

    # keep np array at 60 values and use last 60 only
    gglobs.GMCEstFET = np.append(gglobs.GMCEstFET, lastcps)[1:]

    # estimate 60 sec based on last FET counts
    # try:    FET = gglobs.GMC_FastEstTime
    # except: FET = 60
    # return int(np.nansum(gglobs.GMCEstFET[-FET:]) * 60 / FET) # without int a blob is saved to DB!

    FET          = gglobs.GMC_FastEstTime
    try:    rFET = int(np.nansum(gglobs.GMCEstFET[-FET:]) * 60 / FET) # without int a blob is saved to DB!
    except: rFET = gglobs.NAN

    return rFET


def getGMC_CPMfromCPS(valuedict, vname):
    """calculate CPM from the last 60 values of CPS;
    used in getValuesGMC:  cps data from CPS1st, CPM mapped to CPM3rd"""

    try:                    lastcps = valuedict[vname]
    except Exception as e:
                            exceptPrint(e, "getGMC_CPMfromCPS: vname: {}".format(vname))
                            return gglobs.NAN

    # append single value to np array but use last 60 only
    gglobs.GMCLast60CPS = np.append(gglobs.GMCLast60CPS, lastcps)[1:]

    return float(np.sum(gglobs.GMCLast60CPS)) # without float a blob is saved to DB!


def turnGMC_HeartbeatON():
    # 3. Turn on the GQ GMC heartbeat
    # Note:     This command enable the GQ GMC unit to send count per second data to host every second automatically.
    # Command:  <HEARTBEAT1>>
    # Return:   A 16 bit unsigned integer is returned every second automatically. Each data package consist of 2 bytes
    #           data from GQ GMC unit. The first byte is MSB byte data and second byte is LSB byte data.
    # e.g.:     10 1C     the returned 1 second count is 28.   Only lowest 14 bits are used for the valid data bit.
    #           The highest bit 15 and bit 14 are reserved data bits.
    # Firmware supported:  GMC-280, GMC-300  Re.2.10 or later

    fncname = "turnGMC_HeartbeatON: "

    brec, error, errmessage = serialGMC_COMM(b'<HEARTBEAT1>>', 0, orig(__file__))

    return (brec, error, errmessage)


def turnGMC_HeartbeatOFF():
    # 4. Turn off the GQ GMC heartbeat
    # Command:  <HEARTBEAT0>>
    # Return:   None
    # Firmware supported:  Re.2.10 or later

    fncname = "turnGMC_HeartbeatOFF: "
    dprint(fncname)
    setIndent(1)

    brec, error, errmessage = serialGMC_COMM(b'<HEARTBEAT0>>', 0, orig(__file__))
    if error == 0:  dprint (fncname + "Success")
    else:           edprint(fncname + "FAILURE: " + errmessage)

    setIndent(0)


def getGMC_VOLT():
    # Get battery voltage status
    # send <GETVOLT>> and read 1 byte
    # returns one byte voltage value of battery (X 10V)
    # e.g.: return 62(hex) is 9.8V
    # Example: Geiger counter GMC-300E+
    # with Li-Battery 3.7V, 800mAh (2.96Wh)
    # -> getGMC_VOLT reading is: 4.2V
    # -> Digital Volt Meter reading is: 4.18V
    #
    # GMC 500/600 is different. Delivers 5 ASCII bytes
    # z.B.[52, 46, 49, 118, 0] = "4.1v\x00"

    defname = "getGMC_VOLT: "
    dprint(defname)
    setIndent(1)

    rec, error, errmessage = serialGMC_COMM(b'<GETVOLT>>', gglobs.GMC_voltagebytes, orig(__file__))
    try:
        dprint(defname + "VOLT: raw: {}  (len:{})".format(rec, len(rec)))
    except Exception as e:
        exceptPrint(e, "Voltage format is not matching expectations!")
        error = 99

    ######## TESTING (uncomment all 4) ####################################
    # ATTENTION: Voltage in Firmware 2.42 does NOT have the Null character!
    #######################################################################
    #rec         = b'3.76v\x00'              # 3.76 Volt
    #error       = 1
    #errmessage  = "testing"
    #dprint(defname + "TESTING with rec=", rec, debug=True)
    ################################################

    if error == 0 or error == 1:
        if   gglobs.GMC_voltagebytes == 1:
            rec = str(rec[0]/10.0)

        elif gglobs.GMC_voltagebytes == 5:
            reccopy = rec[:]
            reccopy = reccopy.replace(b"\x00", b"").replace(b"v", b"")  # it ends with \x00:  b'4.6v\x00'
            rec     = reccopy.decode('UTF-8')

        else:
            rec = str(rec) + " Unexpected voltage format @config: GMC_voltagebytes={}".format(gglobs.GMC_voltagebytes)
    else:
        rec         = "ERROR: Voltage has unexpected format!"
        error       = 1
        errmessage  = defname + "ERROR getting voltage"

    dprint(defname + "Using config setting GMC_voltagebytes={}:  Voltage='{}', err={}, errmessage='{}'".format(gglobs.GMC_voltagebytes, rec, error, errmessage))
    setIndent(0)

    return (rec, error, errmessage)



# def getGMC_VOLT():
#     # Get battery voltage status
#     # send <GETVOLT>> and read 1 byte
#     # returns one byte voltage value of battery (X 10V)
#     # e.g.: return 62(hex) is 9.8V
#     # Example: Geiger counter GMC-300E+
#     # with Li-Battery 3.7V, 800mAh (2.96Wh)
#     # -> getGMC_VOLT reading is: 4.2V
#     # -> Digital Volt Meter reading is: 4.18V
#     #
#     # GMC 500/600 is different. Delivers 5 ASCII bytes
#     # z.B.[52, 46, 49, 49, 118] = "4.11v"

#     fncname = "getGMC_VOLT: "
#     dprint(fncname)
#     setIndent(1)

#     rec, error, errmessage = serialGMC_COMM(b'<GETVOLT>>', gglobs.GMC_voltagebytes, orig(__file__)) # raw:b'4.7v\x00'
#     rec = rec[:-2]  # remove trailing 'v' and NULL value
#     dprint(fncname + "VOLT: raw:", rec)


#     ######## TESTING (uncomment all 4) #############
#     #rec         = b'3.76v'              # 3.76 Volt
#     #error       = 1
#     #errmessage  = "testing"
#     #dprint(fncname + "TESTING with rec=", rec, debug=True)
#     ################################################

#     if error == 0 or error == 1:
#         if   gglobs.GMC_voltagebytes == 1:  rec = str(rec[0]/10.0)
#         elif gglobs.GMC_voltagebytes == 5:  rec = rec.decode('UTF-8')
#         else:                               rec = str(rec) + " @config: GMC_voltagebytes={}".format(gglobs.GMC_voltagebytes)

#     else:
#         rec         = "ERROR"
#         error       = 1
#         errmessage  = fncname + "ERROR getting voltage"

#     dprint(fncname + "Using config setting GMC_voltagebytes={}:  Voltage='{}', err={}, errmessage='{}'".format(gglobs.GMC_voltagebytes, rec, error, errmessage))
#     setIndent(0)

#     return (rec, error, errmessage)


def getGMC_SPIR(address = 0, datalength = 4096):
    """Reads datalength bytes from the internal flash memory at address to get history data"""

    # Request history data from internal flash memory
    # Command:  <SPIR[A2][A1][A0][L1][L0]>>
    # A2,A1,A0 are three bytes address data, from MSB to LSB.
    # The L1,L0 are the data length requested.
    # L1 is high byte of 16 bit integer and L0 is low byte.
    # The length normally not exceed 4096 bytes in each request.
    # Return: The history data in raw byte array.
    # Comment: The minimum address is 0, and maximum address value is
    # the size of the flash memory of the GQ GMC Geiger count. Check the
    # user manual for particular model flash size.

    # address must not exceed 2^(3*8) = 16 777 215 because high byte
    # is clipped off and only lower 3 bytes are used here
    # (but device address is limited to 2^20 - 1 = 1 048 575 = "1M"
    # anyway, or even only 2^16 - 1 = 65 535 = "64K" !)

    # datalength must not exceed 2^16 = 65536 or python conversion
    # fails with error; should be less than 4096 anyway

    # device delivers [(datalength modulo 4096) + 1] bytes,
    # e.g. with datalength = 4128 (= 4096 + 32 = 0x0fff + 0x0020)
    # it returns: (4128 modulo 4096) + 1 = 32 + 1 = 33 bytes

    # This contains a WORKAROUND activated with  'GMC_SPIRbugfix=True':
    # it asks for only (datalength - 1) bytes,
    # but as it then reads one more byte, the original datalength is obtained

    # BUG WARNING - WORKAROUND ##################################################
    #
    # GMC-300   : no workaround, but use 2k GMC_SPIRpage only!
    # GMC-300E+ : use workaround 'datalength - 1' with 4k GMC_SPIRpage
    # GMC-320   : same as GMC-300E+
    # GMC-320+  : same as GMC-300E+
    # GMC-500   : ist der Bug behoben oder nur auf altem Stand von GMC-300 zurück?
    #             workaround ist nur 2k GMC_SPIRpage anzufordern
    # GMC-500+  : treated as a GM-500
    # GMC-600   : treated as a GM-500
    # GMC-600+  : treated as a GM-500
    # End BUG WARNING - WORKAROUND ##############################################

    fncname = "getGMC_SPIR: "

    # address: pack into 4 bytes, big endian; then clip 1st byte = high byte!
    ad = struct.pack(">I", address)[1:]

    # datalength: pack into 2 bytes, big endian; use all bytes
    # but adjust datalength to fix bug!
    if gglobs.GMC_SPIRbugfix:   dl = struct.pack(">H", datalength - 1)
    else:                       dl = struct.pack(">H", datalength    )

    dprint(fncname + "   requested: datalength:{:5d} (0x{:02x}{:02x})  address: {:5d} (0x{:02x}{:02x}{:02x}), ".\
            format(datalength, dl[0], dl[1], address, ad[0], ad[1], ad[2]))
    setIndent(1)

    rec, error, errmessage = serialGMC_COMM(b'<SPIR' + ad + dl + b'>>', datalength, orig(__file__)) # returns bytes

    if rec != None :    msg = "datalength:{:5d}".format(len(rec))
    else:               msg = "ERROR: No data received!"

    dprint(fncname + "received:  {}, err={}, errmessage='{}'".format(msg, error, errmessage))
    setIndent(0)

    return (rec, error, errmessage)

# not in use! not good! Use GMC_EraseMemBySPISE instead!
def GMC_EraseMemByFacRESET():
    """Erase the History Data saved to memory Factory Reset and re-updatin CFG"""

    # not good; see Reply #12 of: http://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=9812
    # quote:For now maybe you can try to get cfg, then factory reset, then write to cfg which will be faster.
    # @EmfDev, that sounded like a great idea, but at the end it was even a lot worse that the SPISE thing,
    # both in speed and reliability. Writing the config to the counter is a rather slow process, since -
    # according to your documents - it needs to be done byte-by-byte. Writing a single byte to the config
    # of a GMC500 takes 14 ms (21 ms for a GMC300). So, 512 bytes need 512 * 0.014 = 7.2 sec. Plus overhead
    # makes it ~9 sec, just as much as the SPISE process takes.
    # But on top of this the config-writing is notoriously unreliable, often requiring 1, 2, or even 3
    # re-writes, before a read-back confirms the correct configuration finally made it to the counter.
    # And more, on top of this the ECFG command also has a tendency to timeout. Again, most of the time
    # requiring multiple repeats.
    # Overall this Factory Reset based approach may easily result in 20 to 30 sec before it is finished!
    # The SPISE approach is anything but a speed champion, but at least is a lot more reliable to handle.
    # Hopefully the firmware can be improved on this.


    start = time.time()

    fncname = "GMC_EraseMemByFacRESET: "
    dprint(fncname)
    setIndent(1)

    # cleaning pipeline
    getGMC_ExtraByte()

    origcfg, error, errmessage = getGMC_Config()
    mdprint(fncname + "getGMC_Config: rcvd: cfg={}, err={}, errmessage='{}'".format(origcfg[:25], error, errmessage))
    cdprint(fncname + "CFG as HEX  : \n{}"    .format(BytesAsHex(origcfg)))

    # cleaning pipeline
    getGMC_ExtraByte()

    setGMC_FACTORYRESET()
    resetcfg, error, errmessage = getGMC_Config()
    mdprint(fncname + "after FacReset CFG as HEX  : \n{}"    .format(BytesAsHex(resetcfg)))

    # write the new config data
    writeGMC_Config(origcfg)

    # # mod of 1.4.1 --> 1.4.2: no verification of written config
    # # read the config
    # checkCFG, error, errmessage = getGMC_Config()

    # if origcfg == checkCFG:
    #     fprint("Verifying written data:", "Ok")
    #     gdprint("Verifying written data: Ok")
    # else:
    #     efprint("Error in written data")
    #     edprint("Error in written data")
    #     edprint("intended cfg:\n", BytesAsHex(origcfg))
    #     fprint("Try to re-write!")

    #     for i in range(len(origcfg)):
    #         if origcfg[i] != checkCFG[i]:
    #             rdprint("byte addr:{:<3d} w:{:#04X} r:{:#04X}".format(i, origcfg[i], checkCFG[i]))


    # cleaning pipeline
    getGMC_ExtraByte()

    rec, error, errmessage = serialGMC_COMM(b'<GetSPISA>>', 4, orig(__file__))
    dprint(fncname + "GetSPISA: rcvd: rec={}, err={}, errmessage='{}'".format(rec, error, errmessage))

    # cleaning pipeline
    getGMC_ExtraByte()


    setIndent(0)

    return (rec, error, errmessage)


def GMC_EraseMemBySPISE():
    """Erase the History Data saved to memory"""

    # from http://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=9812
    # 1. SPISE[0xAA][0xAA][0xAA] this is a sector erase. each sector is 4KB.
    # e.g. 53 50 49 53 45 00 00 00 -> erase first sector
    # then
    # 2. Need to set the SPI Save Address back to 0x000000. No need if device is off.
    # SetSPISA[0xAA][0xAA][0xAA] -> SPI save address.
    # If you want to erase the full storage must erase all the sectors.
    # Maybe it is better to do it when device is off so that timestamp will be saved during power on.
    # Go to Top of Page
    # 3C 53 65 74 53 50 49 53 41 00 00 00 3E 3E
    # <  S  e  t  S  P  I  S  A  (3x Null)>  >
    #
    # Conclusion:
    # the above comments by EmDev are partially wrong!
    # It only works on GMC-300E+ and GMC-500+ if you do:
    #   1) Power OFF
    #   2) Delete all content with SPISE command
    #   3) send SetSPISA
    #   4) Power ON

    start = time.time()
    fncname = "GMC_EraseMemBySPISE: "
    dprint(fncname)
    setIndent(1)

    # cleaning pipeline
    getGMC_ExtraByte()

    # delete all memory in chunks of 4096
    page = 4096
    for address in range(0, gglobs.GMC_memory, page):

        # address: pack into 4 bytes, big endian;
        # then clip 1st byte = high byte, so only 3 LSB bytes are left!
        # result like: address: 49152 --> ad: 0x 00 c0 00
        ad = struct.pack(">I", address)[1:]

        # returns bytes;
        # GMC-500+:     read time: 33 ... 36 ms; some calls >100 ms (approx every 50th)
        #               returns:  b'\xaa'   (1 byte only)
        # GMC-300E+:    read time: 33 ... 40 ms; some calls 80 ms, 230 ms
        #               returns:   b'\x00\x80\x00' (3 bytes; is same as address given)
        rec, error, errmessage = serialGMC_COMM(b'<SPISE' + ad + b'>>', 1, orig(__file__))
        msg = fncname + "SPISE: address: {:5d} (0x {:02x} {:02x} {:02x})  ".format(address, ad[0], ad[1], ad[2])
        dprint(msg + "rcvd: rec={}, err={}, errmessage='{}'".format(rec, error, errmessage))

    rec, error, errmessage = serialGMC_COMM(b'<GetSPISA>>', 4, orig(__file__))
    msg = fncname + "GetSPISA "
    dprint(msg + "rcvd: rec={}, err={}, errmessage='{}'".format(rec, error, errmessage))

    # send SetSPISA[0xAA][0xAA][0xAA]
    SPISaveAddress = b'\x00\x00\x00'
    rec, error, errmessage = serialGMC_COMM(b'<SetSPISA' + SPISaveAddress + b'>>', 0, orig(__file__)) # returns bytes
    dprint(fncname + "SetSPISA\x00\x00\x00: rcvd: rec={}, err={}, errmessage='{}'".format(rec, error, errmessage))

    cdprint(fncname + "Duration: {:0.1f} sec".format(time.time() - start))

    rec, error, errmessage = serialGMC_COMM(b'<GetSPISA>>', 4, orig(__file__))
    msg = fncname + "GetSPISA "
    dprint(msg + "rcvd: rec={}, err={}, errmessage='{}'".format(rec, error, errmessage))

    setIndent(0)

    return (rec, error, errmessage)


def getGMC_ExtraByte(SerPointer = None):

    fncname = "getGMC_ExtraByte: "
    dprint(fncname)
    setIndent(1)

    # rdprint(fncname, "SerPointer is:", SerPointer)

    if SerPointer is None:
        try:
            if os.path.exists(gglobs.GMC_usbport):
                with serial.Serial(gglobs.GMC_usbport,
                                gglobs.GMC_baudrate,
                                timeout=gglobs.GMC_timeoutR,
                                write_timeout=gglobs.GMC_timeoutW) as GMCserEB:
                    xrec = origgetGMC_ExtraByte(GMCserEB)
            else:
                xrec = b""

        except Exception as e:
            exceptPrint(e, fncname + "USBport missing?")
            xrec = b""
    else:
        xrec = origgetGMC_ExtraByte(SerPointer)

    setIndent(0)

    return xrec


def origgetGMC_ExtraByte(SerPointerEB):
# def getGMC_ExtraByte():
    """read until no further bytes coming"""

    start   = time.time()
    fncname = "origgetGMC_ExtraByte: "
    xrec    = b""

    time.sleep(0.005) # this code may be running too fast and missing waiting bytes. Happened with 500+

    if os.path.exists(gglobs.GMC_usbport):
        try:
            # failed when called from 2nd instance of GeigerLog; just to avoid crash
            bytesWaiting = SerPointerEB.in_waiting
            # rdprint(fncname, "bytes waiting; ", bytesWaiting)
        except Exception as e:
            exceptPrint(e, "Exception bytesWaiting")
            bytesWaiting = 0
    else:
        # edprint("den shit gibbes nich")
        bytesWaiting = 0

    if bytesWaiting > 0:
        # read until nothing is in_waiting
        # mdprint(fncname + "Bytes waiting: {}".format(bytesWaiting))
        while True:
            try:
                x = SerPointerEB.read(bytesWaiting)
                # edprint("x: len:", len(x), " ", x)
                time.sleep(0.010)   # this loop may be running too fast and missing waiting bytes.
                                    # Happened with 500+
            except Exception as e:
                edprint(fncname + "Exception: {}".format(e))
                exceptPrint(e, fncname + "Exception: ")
                x = b""

            if len(x) == 0: break
            xrec += x

            try:
                bytesWaiting = SerPointerEB.in_waiting
            except Exception as e:
                exceptPrint(e, fncname + "SerPointerEB.in_waiting Exception")
                bytesWaiting = 0

            if bytesWaiting == 0: break

        msg = BOLDRED + "Got {} extra bytes from reading-pipeline: {}".format(len(xrec), xrec[:70])

        duration = 1000 * (time.time() - start)
        cdprint(fncname + msg + " - duration:{:0.1f} ms".format(duration))

    return xrec


def getGMC_Config():
    """Get configuration data from the counter"""

    # send <GETCFG>> and read all bytes
    # returns
    # - the cfg as Python bytes, should be 256 or 512 bytes long
    # - the error value (0, -1, +1)
    # - the error message as string
    # fills gglobs.GMC_cfg with cfg as read

    # NOTE: 300series uses 256 bytes; 500 and 600 series 512 bytes
    # config size is determined by deviceproperties

    global cfgKeyLow, cfgKeyHigh

    start = time.time()

    fncname = "getGMC_Config: "
    dprint(fncname)
    setIndent(1)

    startGETCFG = time.time()
    cfg, error, errmessage = serialGMC_COMM(b'<GETCFG>>', gglobs.GMC_configsize, orig(__file__))
    durGETCFG = time.time() - startGETCFG

    if cfg is not None:     dprint (fncname + "Got {} bytes; first 30: {}".format(len(cfg), BytesAsHex(cfg[:30])))
    else:                   dprint (fncname + "Got no bytes")

    mdprint(fncname + "CFG as HEX  : (Duration: {:0.3f} sec)\n{}".format(durGETCFG, BytesAsHex(cfg)))
    dprint()
    mdprint(fncname + "CFG as DEC  : \n{}"    .format(BytesAsDec(cfg)))
    dprint()
    mdprint(fncname + "CFG as ASCII: \n{}"    .format(BytesAsASCIIFF(cfg)))
    dprint()

    ###############################################################################
    ####### BEGIN TESTDATA ########################################################
    # replaces current cfg with cfg from other runs
    # requires that a testdevice was activated in getGMC_Version
    # only do this when command 'testing' was given on command line !
    if gglobs.testing:
        if gglobs.GMC_configsize == 512:
            # using a 512 bytes sequence; data from a GMC-500(non-plus) readout
            #
            # power is OFF:
            cfg500str = "01 00 00 02 1F 00 00 64 00 3C 3E C7 AE 14 27 10 42 82 00 00 00 19 41 1C 00 00 00 3F 00 00 00 00 02 02 00 00 00 00 FF FF FF FF FF FF 00 01 00 78 0A FF FF 3C 00 05 FF 01 00 00 0A 00 01 0A 00 64 00 3F 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 77 77 77 2E 67 6D 63 6D 61 70 2E 63 6F 6D 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 6C 6F 67 32 2E 61 73 70 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02 00 02 11 05 1E 10 34 05 FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF"
            cfg500    = cfg500str.split(' ')

            # power is ON:
            cfg500    = ["0"] + cfg500[1:]
            #print("cfg500:\n", len(cfg500), cfg500)

            cfg = b''
            for a in cfg500: cfg += bytes([int(a, 16)]) # using hex data

        elif "GMC-320Re 5." in gglobs.GMCDeviceDetected :  # 320v5 device (with WiFi)
            cfg = (cfg[:69] + b'abcdefghijklmnopqrstuvwxyz0123456789' * 10)[:256] # to simulate WiFi settings just fill up config

        elif gglobs.GMC_configsize == 256: # 320v4 device
            # next line from 320+ taken on: 2017-05-26 15:29:38
            # power is off:
            cfg320plus = [255, 0, 0, 2, 31, 0, 0, 100, 0, 60, 20, 174, 199, 62, 0, 240, 20, 174, 199, 63, 3, 232, 0, 0, 208, 64, 0, 0, 0, 0, 63, 0, 2, 2, 0, 0, 0, 0, 255, 255, 255, 255, 255, 255, 0, 1, 0, 120, 25, 255, 255, 60, 1, 8, 255, 1, 0, 254, 10, 0, 1, 10, 0, 100, 0, 0, 0, 0, 63, 17, 5, 23, 16, 46, 58, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255]
            # power is on:
            cfg320plus = [  0] + cfg320plus[1:]

            cfg = b''
            for a in cfg320plus: cfg += bytes([a]) # using dec data

        else:
            pass

        error       = 1
        errmessage  = "SIMULATION"

        print("TESTDATA: cfg:", len(cfg), type(cfg))
        print(BytesAsHex(cfg))
        print(BytesAsASCIIFF(cfg))
        print("TESTDATA:  END ------------")

        # the cfg will have been changed
        dprint (fncname + "CFG as HEX  : \n{}"    .format(BytesAsHex(cfg)))
        dprint (fncname + "CFG as DEC  : \n{}"    .format(BytesAsDec(cfg)))
        dprint (fncname + "CFG as ASCII: \n{}"    .format(BytesAsASCIIFF(cfg)))
    ####### END TESTDATA ##########################################################
    ###############################################################################


    gglobs.GMC_cfg = cfg  # set the global value with whatever you got, real or fake data

    if cfg == None:
        dprint(fncname + "ERROR: Failed to get any configuration data", debug=True)

    else:
        # cfg is != None
        # set endian
        if gglobs.GMC_endianness == 'big': fString = ">f"  # use big-endian ---   500er, 600er:
        else:                              fString = "<f"  # use little-endian -- other than 500er and 600er:

        # set low keys
        try:
            for key in cfgKeyLow:
                cfgKeyLow[key][0] = cfg[cfgKeyLow[key][1][0] : cfgKeyLow[key][1][1]]
        except Exception as e:
            edprint(fncname + "Exception: cfgKeyLow[{}]: {}".format(key, e))
            exceptPrint(e, fncname + "Exception: cfgKeyLow[{}]".format(key))
            setIndent(0)
            return cfg, -1, fncname + "Exception: {}".format(e)

        try:
            cfgKeyLow["CalibCPM_0"]  [0]     = struct.unpack(">H",    cfgKeyLow["CalibCPM_0"]  [0] )[0]
            cfgKeyLow["CalibCPM_1"]  [0]     = struct.unpack(">H",    cfgKeyLow["CalibCPM_1"]  [0] )[0]
            cfgKeyLow["CalibCPM_2"]  [0]     = struct.unpack(">H",    cfgKeyLow["CalibCPM_2"]  [0] )[0]

            cfgKeyLow["CalibuSv_0"]  [0]     = struct.unpack(fString, cfgKeyLow["CalibuSv_0"]  [0] )[0]
            cfgKeyLow["CalibuSv_1"]  [0]     = struct.unpack(fString, cfgKeyLow["CalibuSv_1"]  [0] )[0]
            cfgKeyLow["CalibuSv_2"]  [0]     = struct.unpack(fString, cfgKeyLow["CalibuSv_2"]  [0] )[0]

            cfgKeyLow["MaxCPM"    ]  [0]     = struct.unpack(">H",    cfgKeyLow["MaxCPM"]      [0] )[0]

            cfgKeyLow["ThresholdCPM"][0]     = struct.unpack(">H",    cfgKeyLow["ThresholdCPM"][0] )[0]
            cfgKeyLow["ThresholduSv"][0]     = struct.unpack(fString, cfgKeyLow["ThresholduSv"][0] )[0]

        except Exception as e:
            edprint(fncname + "Exception: set cfgKeyLow[{}]: {}".format("?", e))
            exceptPrint(e, fncname + "set cfgKeyLow[{}]".format("?"))
            setIndent(0)
            return cfg, -1, fncname + "Exception: set cfgKeyLow[?]: {}".format(e)


        # set High keys
        ndx = gglobs.GMC_WifiIndex
        try:
            if ndx != None:
                # set the WiFi part of the config
                # gdprint("ndx = ", ndx)
                for key in cfgKeyHigh:
                    # gdprint("key: ", key)
                    if key == "Period":
                        # Period is one byte, value = 0...255 (minutes)
                        cfgKeyHigh[key][1] = str(ord((cfg[cfgKeyHigh[key][ndx][0] : cfgKeyHigh[key][ndx][1]])))

                    elif key == "FET":
                        if cfgKeyHigh[key][ndx][0] != None:
                            # FastEstTime is one byte, value = 3(dynamic), 5,10,15,20,30,60 seconds
                            cfgKeyHigh[key][1] = str(ord((cfg[cfgKeyHigh[key][ndx][0] : cfgKeyHigh[key][ndx][1]])))
                        else:
                            cfgKeyHigh[key][1] = None

                    else:
                        try:
                            temp               = cfg[cfgKeyHigh[key][ndx][0] : cfgKeyHigh[key][ndx][1]]
                            cfgKeyHigh[key][1] = temp.replace(b"\x00", b"").replace(b"\xff", b"").decode("UTF-8")
                        except Exception as e:
                            cfgKeyHigh[key][1] = "Failure getting Config: {}".format(e)
                    #print("key: {:13s} cfgKeyHigh[][1]: {}".format(key, cfgKeyHigh[key][1]))

            else:
                # no WiFi
                for key in cfgKeyHigh:
                    #~cfgKeyHigh[key][1] = "None"
                    cfgKeyHigh[key][1] = ""
        except Exception as e:
            exceptPrint(e, "FAILURE to set the WiFi part of config")

    cdprint(fncname + "Full Duration: {:0.3f} sec".format(time.time() - start))
    setIndent(0)

    return cfg, error, errmessage


def writeGMC_ConfigSingle(cfgaddress, value):
    """prepare cfg by modifying single byte, then writing full cfg to the config memory"""

    dprint("writeGMC_ConfigSingle: cfgaddress: {}, value: {}".format(cfgaddress, value))
    setIndent(1)

    # get a fresh config and make a copy
    getGMC_Config()
    cfgcopy = copy.copy(gglobs.GMC_cfg)

    # modify cfgcopy at cfgaddress with value
    cfgcopy = cfgcopy[:cfgaddress] + bytes([value]) + cfgcopy[cfgaddress + 1:]
    cdprint("writeGMC_ConfigSingle: new cfg\n", BytesAsHex(cfgcopy))

    writeGMC_Config(cfgcopy)

    setIndent(0)


def writeGMC_Config(config):
    """write a full config"""

    # 9. Write configuration data
    # Command:  <WCFG[A0][D0]>>
    # A0 is the address and the D0 is the data byte(hex).
    # A0 is offset of byte in configuration data.
    # D0 is the assigned value of the byte.
    # Return: 0xAA
    # Firmware supported: GMC-280, GMC-300 Re.2.10 or later

    """
    from: http://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=4948 Reply #20
    EmfDev:
    The <ECFG>> and <CFGUPDATE>> still work.

    But the <WCFG[A0][D0]>> is now <WCFG[Hi][Lo][Ch]>>
    So instead of 2, there are 3 params.
    Hi - High byte
    Lo - Low byte
    Ch - Byte to write

    3c 57 43 46 47 00 02 01 3e 3e example for writing 1 to the speaker.
    I think you already know that you can't change a byte from 0x00 to 0x01 but
    you can change it from 0x01 to 0x00

    So one way users can change config is to:
    1. <GETCFG>> copy each byte of the config
    2. <ECFG>> erase config from the device
    3. Edit the config you got from 1 like you can change speaker from 1 to 0 or 0 to 1
    4. <WCFG[0x00 - 0x01][0x00 - 0xFF][valid 8bits]>> starting from position 0 to the end of config
    5. <CFGUPDATE>>
    """

    wgcstart = time.time()

    fncname = "writeGMC_Config: "

    dprint(fncname)
    setIndent(1)

    cfgcopy = copy.copy(config)
    # dprint(fncname + "Config copy: len: {}:\n".format(len(cfgcopy)), BytesAsHex(cfgcopy))

    if   len(cfgcopy) <= 256 and gglobs.GMC_configsize == 256:  doUpdate = 256
    elif len(cfgcopy) <= 512 and gglobs.GMC_configsize == 512:  doUpdate = 512
    else: # ERROR:
        msg = "Number of configuration data inconsistent with detected device.\nUpdating config will NOT be done, as Device might be damaged by it!"
        efprint(msg)
        dprint(fncname + msg.replace('\n', ' '), debug=True)
        setIndent(0)
        return

    # remove right side FFs; after erasing the config memory this will be the default anyway
    cfgstrip = cfgcopy.rstrip(b'\xFF')
    dprint(fncname + "Config right-stripped from FF: len:{}:\n".format(len(cfgstrip)), BytesAsHex(cfgstrip))

    # erase config on device
    dprint(fncname + "Erase Config with ECFG")

    startecfg = time.time()
    rec = serialGMC_COMM(b'<ECFG>>', 1, orig(__file__))
    cdprint(fncname + "ECFG: Duration: {:0.3f} sec".format(time.time() - startecfg))
    # GMC-300E+: ECFG: Duration: 0.204 sec (??), 0.045 sec, 0.044 sec, 0.041 sec
    # GMC-500+:  ECFG: Duration: 0.155 sec

    # ecfgcfg = getGMC_Config()   # don't need the call: all config bytes are now 0xff
    # rdprint("ecfgcfg", ecfgcfg)
    # cdprint(fncname + "after get config after ECFG: Duration: {:0.3f} sec".format(time.time() - start)) #  Duration: 0.000 sec

    # write the config to device
    dprint(fncname + "Write new Config Data for Config Size: >>>>>>>>>>>>>>>> {} <<<<<<<<<<<<".format(doUpdate))

    #### GMC Bug #######################################################
    # GMC-500 always times out at byte #11.
    # solved: it is a bug in the firmware; data resulted in ">>>"
    ####################################################################
    ##### Writing #####################################################################
    # GMC-500:  single byte write :    0.014 sec
    #           All 512 bytes :        up to addr: 0x10f (=271), Full Duration: 1.6 sec
    # GMC-300:  single byte write :    about 10 ms
    #           All 256 bytes :        up to addr: 0x043 (=67)   Full Duration: 1.0 sec
    ###################################################################################

    # mod of 1.4.1 --> 1.4.2: no time.sleeps, opening Serial outside of loop
    startAllups = time.time()
    pfs = "addr:{:>3d} (0x{:03X}), cfgval:{:>3d} (0x{:02X})"
    with serial.Serial(gglobs.GMC_usbport, gglobs.GMC_baudrate, timeout=0.3) as GMCserData:
        for i, cfgval in enumerate(cfgstrip):
            startsingle = time.time()

            if doUpdate == 256: A0 = bytes([i])           # SINGLE byte : address writing config of up to 256 bytes
            else:               A0 = struct.pack(">H", i) # DOUBLE bytes: pack address into 2 bytes, big endian, for address writing config of up to 512 bytes

            D0 = bytes([cfgval])
            if D0 == ">": edprint("D0 == > !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            GMCserData.write(b'<WCFG' + A0 + D0 + b'>>')
            GMCserData.read(1)

            duration   = 1000 * (time.time() - startsingle)
            extra      = "  Duration: {:0.1f} ms".format(duration)
            ix         = int.from_bytes(A0, byteorder='big')
            cx         = int.from_bytes(D0, byteorder='big')
            mdprint(fncname + pfs.format(i, ix, cfgval, cx), extra)

    cdprint(fncname + "Duration All Bytes: {:0.1f} sec".format(time.time() - startAllups))

    # activate new config on device
    updateGMC_Config()

    # overall
    cdprint(fncname + "Duration Overall w. Update: {:0.1f} sec".format(time.time() - wgcstart))

    setIndent(0)


def updateGMC_Config():
    # 13. Reload/Update/Refresh Configuration
    # must come after writing config to enable new config
    # Command: <CFGUPDATE>>
    # Return: 0xAA
    # Firmware supported: GMC-280, GMC-300 Re.2.20 or later
    # in GMC-500Re 1.08 this command returns:  b'0071\r\n\xaa'
    # see http://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=4948 #40

    fncname = "updateGMC_Config: "
    dprint(fncname)
    setIndent(1)

    rec = serialGMC_COMM(b'<CFGUPDATE>>', 1, orig(__file__))

    dprint(fncname + "rec: ", rec)

    setIndent(0)


def saveGMC_ConfigToFile():
    """save the GMC device config to a file - use for testing"""

    fncname = "saveGMC_ConfigToFile: "
    cfg, error, errmessage = getGMC_Config()
    path = gglobs.dataPath + "/config" + stime() + ".bin"
    writeBinaryFile(path, cfg)


def setGMC_ConfigSettings():
    """puts the config settings into cfg and writes it to the config memory"""

    global cfgKeyLow, cfgKeyHigh

    fncname = "setGMC_ConfigSettings: "

    setBusyCursor()
    dprint(fncname)
    setIndent(1)

    while True: # to allow jumping to exit

        gcfg = bytearray(gglobs.GMC_cfg)
        cdprint(fncname + "gcfg:\n" + BytesAsASCIIFF(gcfg))

    # low index - single byte values
        # lowkeys = "Power", "Alarm", "Speaker", "SaveDataType", "BackLightTimeoutSeconds" # changes!!!!!!!!!!!!!!
        lowkeys = "Alarm", "Speaker", "SaveDataType", "BackLightTimeoutSeconds" # changes!!!!!!!!!!!!!!
        for key in lowkeys:
            # all keys are only 1 byte long
            cfgrec      = cfgKeyLow[key]
            ndxfrom     = cfgrec[1][0]
            try: keyval = int(cfgrec[0])
            except Exception as e:
                edprint(fncname + "low index - single byte values: Exception: ", e)
                keyval = 0
            writeBytesToCFG(gcfg, ndxfrom, [keyval])

            cdprint(fncname + "#1 cfgKeyLow: {:15s}, val: {:1d}, ndx: {}".format(key, keyval, cfgrec[1]))

    # low index - multi byte values (GMC_endianness)
        if gglobs.GMC_endianness == 'big': fString = ">f"  # use big-endian ---   500er, 600er:
        else:                              fString = "<f"  # use little-endian -- other than 500er and 600er:
        lowkeys = "CalibCPM_0", "CalibuSv_0", "CalibCPM_1", "CalibuSv_1", "CalibCPM_2", "CalibuSv_2"
        for key in lowkeys:
            # keys are either 2 bytes or 4 bytes width
            cfgrec      = cfgKeyLow[key]
            ndxfrom     = cfgrec[1][0]
            ndxto       = cfgrec[1][1]
            width       = ndxto - ndxfrom
            if width == 2:
                try:
                    keyval = struct.pack(">H",    int(cfgrec[0])) #int(cfgKeyLow[key][0])
                except Exception as e:
                    edprint(fncname + "low index - multi byte values: Exception: ", e)
                    keyval = [0, 0]
                writeBytesToCFG(gcfg, ndxfrom, keyval)

            elif width == 4:
                try:
                    keyval = struct.pack(fString,    float(cfgrec[0])) #int(cfgKeyLow[key][0])
                except Exception as e:
                    edprint(fncname + "low index - multi byte values: Exception: ", e)
                    keyval = [0, 0, 0, 0]
                writeBytesToCFG(gcfg, ndxfrom, keyval)

            cdprint("#2 cfgKeyLow: {:15s}, val: {}, width: {:2d}, ndx: {}".format(key, keyval, width, cfgKeyLow[key][1]))


        if gglobs.GMC_WifiEnabled:
            cdprint("now writing highkey stuff" * 5)
        # high index
            #print("gglobs.GMC_WifiIndex: ", gglobs.GMC_WifiIndex)
            padding = b"\x00" * 64
            colndx  = gglobs.GMC_WifiIndex
            for key in cfgKeyHigh:
                cfgrec      = cfgKeyHigh[key]
                ndxfrom     = cfgrec[colndx][0]
                ndxto       = cfgrec[colndx][1]
                width       = ndxto - ndxfrom           # bytes reserved for this var

                if key == "Period":
                    try:    keyval = int(cfgrec[1])
                    except Exception as e:
                        edprint(fncname + "high index - Period: Exception: ", e)
                        keyval = 3
                    writeBytesToCFG(gcfg, ndxfrom, [keyval])

                elif key == "WiFi":
                    try:    keyval = int(cfgrec[1])
                    except Exception as e:
                        edprint(fncname + "high index - WiFi: Exception: ", e)
                        keyval = 1
                    writeBytesToCFG(gcfg, ndxfrom, [keyval])

                elif key == "FET":
                    try:    keyval = int(cfgrec[1])
                    except Exception as e:
                        edprint(fncname + "high index - FastEstTime: Exception: ", e)
                        keyval = 1
                    if not keyval in (3,5,10,15,20,30,60): keyval = 60
                    writeBytesToCFG(gcfg, ndxfrom, [keyval])

                else:
                    try:
                        keyval      = bytearray(cfgrec[1], "utf-8")
                        keyval      = (keyval + padding)[0:width]
                    except Exception as e:
                        edprint(fncname + "high index - multi bytes: Exception: ", e)
                        keyval = ("ERROR" + padding)[0:width]
                    writeBytesToCFG(gcfg, ndxfrom, keyval)

                cdprint(fncname + "cfgKeyHigh: {:15s}, width: {:2d}".format(key, width), cfgrec[1], keyval)

            cdprint(fncname + "gcfg:\n" + BytesAsASCIIFF(gcfg))
            gglobs.GMC_FastEstTime = cfgKeyHigh["FET"][1]

        fprint("Config is set, now writing to device ...")
        QtUpdate()

    # write the new config data
        writeGMC_Config(bytes(gcfg))
        fprint("Writing is complete; new configuration is activated.")


    # # mod of 1.4.1 --> 1.4.2: no verification of written config
    # # read the config
    #     checkCFG, error, errmessage = getGMC_Config()

    #     if gcfg == checkCFG:
    #         fprint("<green>Verifying written data:", "Ok")
    #         gdprint(fncname + "Verifying written data: Ok")

    #     else:
    #         msg = "Error in written data"
    #         efprint(msg)
    #         fprint("Try to re-write!")

    #         edprint(fncname + msg)
    #         ydprint(fncname + "intended cfg:\n", BytesAsHex(gcfg))

    #         ydprint(fncname + "Comparing")
    #         for i in range(len(gcfg)):
    #             if gcfg[i] != checkCFG[i]:
    #                 # ydprint(fncname + "Wrong byte at: addr:{:<3d} written:{:#04X} read:{:#04X}".format(i, gcfg[i], checkCFG[i]))
    #                 ydprint(fncname + "Wrong byte at: addr:{:#04x} written:{:#04x} read:{:#04x}".format(i, gcfg[i], checkCFG[i]))

        break   # final exit from while

    getGMC_HistSaveMode()
    gglobs.exgg.setGMCPowerIcon()

    setIndent(0)
    setNormalCursor()


def writeBytesToCFG(cfg, address, bytesrec):
    """write the bytes in byterec to the Python var cfg beginning at address"""

    for i in range(0, len(bytesrec)):
        cfg[address + i] = bytesrec[i]


def editGMC_Configuration():
    """Edit the configuration from the GMC config memory"""

    """ checking radiobuttons
    radio1 = QRadioButton("button 1")
    radio2 = QRadioButton("button 2")
    radio3 = QRadioButton("button 3")

    for i in range(1,4):
        buttonname = "radio" + str(i)           # das geht???????
        if buttonname.isChecked():
            print buttonname + "is Checked"
    """

    global cfgKeyLow, cfgKeyHigh

    rmself = gglobs.exgg    # access to ggeiger "remote self"

    if not gglobs.Devices["GMC"][CONN] :
        showStatusMessage("No GMC Device Connected")
        return

    fncname = "editGMC_Configuration: "

    dprint(fncname)
    setIndent(1)

    # get a fresh config
    cfg, error, errmessage = getGMC_Config()
    # print("error, errmessage: ", error, errmessage, ", cfg:\n", cfg)
    if error < 0 or cfg is None:
        efprint("Error:" + errmessage)
        setIndent(0)
        return

    # https://www.tutorialspoint.com/pyqt/pyqt_qlineedit_widget.htm
    # https://snorfalorpagus.net/blog/2014/08/09/validating-user-input-in-pyqt4-using-qvalidator/

    setDefault = False  # i.e. False==show what is read from device

    while True:
        fbox = QFormLayout()
        fbox.setFieldGrowthPolicy (QFormLayout.AllNonFixedFieldsGrow)
        fbox.addRow(QLabel("<span style='font-weight:900;'>All GMC Counter</span>"))

    # Power
        r01 = QRadioButton("On")
        r02 = QRadioButton("Off")
        r01.setChecked(False)
        r02.setChecked(False)
        if isGMC_PowerOn() == 'ON': r01.setChecked(True)
        else:                       r02.setChecked(True)
        powergroup = QButtonGroup()
        powergroup.addButton(r01)
        powergroup.addButton(r02)
        hbox0 = QHBoxLayout()
        hbox0.addWidget(r01)
        hbox0.addWidget(r02)
        hbox0.addStretch()
        # fbox.addRow(QLabel("Power State"), hbox0)

    # Alarm
        r11 = QRadioButton("On")
        r12 = QRadioButton("Off")
        r11.setChecked(False)
        r12.setChecked(False)
        alarmgroup = QButtonGroup()
        alarmgroup.addButton(r11)
        alarmgroup.addButton(r12)
        hbox1 = QHBoxLayout()
        hbox1.addWidget(r11)
        hbox1.addWidget(r12)
        hbox1.addStretch()
        fbox.addRow(QLabel("Alarm State"), hbox1)
        if isGMC_AlarmOn() == 'ON': r11.setChecked(True)
        else:                       r12.setChecked(True)

    # Speaker
        r21 = QRadioButton("On")
        r22 = QRadioButton("Off")
        r21.setChecked(False)
        r22.setChecked(False)
        speakergroup = QButtonGroup()
        speakergroup.addButton(r21)
        speakergroup.addButton(r22)
        hbox2 = QHBoxLayout()
        hbox2.addWidget(r21)
        hbox2.addWidget(r22)
        hbox2.addStretch()
        fbox.addRow(QLabel("Speaker State"), hbox2)
        if isGMC_SpeakerOn() == 'ON':   r21.setChecked(True)
        else:                           r22.setChecked(True)

    # history Savedatatype
        # 0 "OFF (no history saving)",
        # 1 "CPS, save every second",
        # 2 "CPM, save every minute",
        # 3 "CPM, save hourly average",
        # 4 "CPS, save every second if exceeding threshold",
        # 5 "CPM, save every minute if exceeding threshold",
        index, text = getGMC_HistSaveMode()
        cb1   = QComboBox()
        cb1.addItems(savedatatypes)
        # cb1.setCurrentIndex(gglobs.GMC_savedataindex)
        cb1.setCurrentIndex(index)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(cb1)
        fbox.addRow(QLabel("History Saving Mode"), hbox3)

    # Light states                       DropDn    reported by
        # LightState = ( "Light: OFF",     # 0     counter: 0
        #                "Light: ON",      # 1     counter: 1
        #                "Timeout: 1",     # 2     counter: 2
        #                "Timeout: 3",     # 3     counter: 4
        #                "Timeout: 10",    # 4     counter: 11
        #                "Timeout: 30",    # 5     counter: 31
        #                 )
        hbox4 = QHBoxLayout()
        cb2   = QComboBox()
        cb2.addItems(LightState)

        # print("cfgKeyLow[BackLightTimeoutSeconds] [0]", cfgKeyLow["BackLightTimeoutSeconds"] [0])
        # print("ord(cfgKeyLow[BackLightTimeoutSeconds] [0]", ord(cfgKeyLow["BackLightTimeoutSeconds"] [0]))
        LightStatusValue = ord(cfgKeyLow["BackLightTimeoutSeconds"] [0])
        # LightStatusIndex = 0
        if   LightStatusValue == 0 : LightStatusIndex = 0
        elif LightStatusValue == 1 : LightStatusIndex = 1
        elif LightStatusValue == 2 : LightStatusIndex = 2
        elif LightStatusValue == 4 : LightStatusIndex = 3
        elif LightStatusValue == 11: LightStatusIndex = 4
        else                       : LightStatusIndex = 5

        cb2.setCurrentIndex(LightStatusIndex)
        hbox4.addWidget(cb2)
        fbox.addRow(QLabel("Light State"), hbox4)

    # sensitivity
        cpmtip   = "Enter an integer number 1 ... 1 Mio"
        usvtip   = "Enter a number 0.00001 ... 100 000"
        cpmlimit = (1, 1000000)
        usvlimit = (0.00001, 100000, 5 )

      # sensitivity 0
        rmself.cal1_cpm = QLineEdit()
        rmself.cal1_cpm.setFont(gglobs.fontstd)
        rmself.cal1_cpm.setValidator (QIntValidator(*cpmlimit))
        rmself.cal1_cpm.setToolTip(cpmtip)

        rmself.cal1_usv = QLineEdit()
        rmself.cal1_usv.setFont(gglobs.fontstd)
        rmself.cal1_usv.setValidator(QDoubleValidator(*usvlimit))
        rmself.cal1_usv.setToolTip(usvtip)

        rmself.cal1_fac = QLabel("")                      # CPM / (µSv/h)
        rmself.cal1_fac.setAlignment(Qt.AlignCenter)

        rmself.cal1_rfac = QLabel("")                     # reverse: µSv/h/CPM
        rmself.cal1_rfac.setAlignment(Qt.AlignCenter)

      # sensitivity 1
        rmself.cal2_cpm = QLineEdit()
        rmself.cal2_cpm.setValidator (QIntValidator(*cpmlimit))
        rmself.cal2_cpm.setFont(gglobs.fontstd)
        rmself.cal2_cpm.setToolTip(cpmtip)

        rmself.cal2_usv = QLineEdit()
        rmself.cal2_usv.setValidator(QDoubleValidator(*usvlimit))
        rmself.cal2_usv.setFont(gglobs.fontstd)
        rmself.cal2_usv.setToolTip(usvtip)

        rmself.cal2_fac = QLabel()
        rmself.cal2_fac.setAlignment(Qt.AlignCenter)

        rmself.cal2_rfac = QLabel()
        rmself.cal2_rfac.setAlignment(Qt.AlignCenter)

      # sensitivity 2
        rmself.cal3_cpm = QLineEdit()
        rmself.cal3_cpm.setValidator (QIntValidator(*cpmlimit))
        rmself.cal3_cpm.setFont(gglobs.fontstd)
        rmself.cal3_cpm.setToolTip(cpmtip)

        rmself.cal3_usv = QLineEdit()
        rmself.cal3_usv.setValidator(QDoubleValidator(*usvlimit))
        rmself.cal3_usv.setFont(gglobs.fontstd)
        rmself.cal3_usv.setToolTip(usvtip)

        rmself.cal3_fac = QLabel()
        rmself.cal3_fac.setAlignment(Qt.AlignCenter)

        rmself.cal3_rfac = QLabel()
        rmself.cal3_rfac.setAlignment(Qt.AlignCenter)

      # Grid
        calOptions = QGridLayout()
        calOptions.setContentsMargins(0,0,0,0)

        row = 0
        calOptions.addWidget(QLabel("Point"),          row, 0)
        calOptions.addWidget(QLabel("CPM"),            row, 1)
        calOptions.addWidget(QLabel("µSv/h"),          row, 2)
        calOptions.addWidget(QLabel("CPM/(µSv/h)"),    row, 3)
        calOptions.addWidget(QLabel("µSv/h/CPM"),      row, 4)

        row = 1
        calOptions.addWidget(QLabel("#1"),             row, 0)
        calOptions.addWidget(rmself.cal1_cpm,          row, 1)
        calOptions.addWidget(rmself.cal1_usv,          row, 2)
        calOptions.addWidget(rmself.cal1_fac,          row, 3)
        calOptions.addWidget(rmself.cal1_rfac,         row, 4)

        row = 2
        calOptions.addWidget(QLabel("#2"),             row, 0)
        calOptions.addWidget(rmself.cal2_cpm,          row, 1)
        calOptions.addWidget(rmself.cal2_usv,          row, 2)
        calOptions.addWidget(rmself.cal2_fac,          row, 3)
        calOptions.addWidget(rmself.cal2_rfac,         row, 4)

        row = 3
        calOptions.addWidget(QLabel("#3"),             row, 0)
        calOptions.addWidget(rmself.cal3_cpm,          row, 1)
        calOptions.addWidget(rmself.cal3_usv,          row, 2)
        calOptions.addWidget(rmself.cal3_fac,          row, 3)
        calOptions.addWidget(rmself.cal3_rfac,         row, 4)

        for i in range(0, 3):
            calcpm = cfgKeyLow["CalibCPM_{}".format(i)][0]
            calusv = cfgKeyLow["CalibuSv_{}".format(i)][0]
            calfac = calcpm / calusv
            rcalfac = 1 / calfac

            if   i == 0:
                rmself.cal1_cpm. setText("{:1.0f}".format(calcpm))
                rmself.cal1_usv. setText("{:1.3f}".format(calusv))
                rmself.cal1_fac. setText("{:9.3f}".format(calfac))
                rmself.cal1_rfac.setText("{:9.5f}".format(rcalfac))
            elif i == 1:
                rmself.cal2_cpm. setText("{:1.0f}".format(calcpm))
                rmself.cal2_usv. setText("{:1.3f}".format(calusv))
                rmself.cal2_fac. setText("{:9.3f}".format(calfac))
                rmself.cal2_rfac.setText("{:9.5f}".format(rcalfac))
            elif i == 2:
                rmself.cal3_cpm. setText("{:1.0f}".format(calcpm))
                rmself.cal3_usv. setText("{:1.3f}".format(calusv))
                rmself.cal3_fac. setText("{:9.3f}".format(calfac))
                rmself.cal3_rfac.setText("{:9.5f}".format(rcalfac))

        fbox.addRow("\n\nCalibration Points", calOptions)

        rmself.cal1_cpm.textChanged.connect(lambda: checkCalibValidity("cal0cpm", rmself.cal1_cpm, rmself.cal1_usv, rmself.cal1_fac, rmself.cal1_rfac ))
        rmself.cal1_usv.textChanged.connect(lambda: checkCalibValidity("cal0usv", rmself.cal1_cpm, rmself.cal1_usv, rmself.cal1_fac, rmself.cal1_rfac ))
        rmself.cal2_cpm.textChanged.connect(lambda: checkCalibValidity("cal1cpm", rmself.cal2_cpm, rmself.cal2_usv, rmself.cal2_fac, rmself.cal2_rfac ))
        rmself.cal2_usv.textChanged.connect(lambda: checkCalibValidity("cal1usv", rmself.cal2_cpm, rmself.cal2_usv, rmself.cal2_fac, rmself.cal2_rfac ))
        rmself.cal3_cpm.textChanged.connect(lambda: checkCalibValidity("cal2cpm", rmself.cal3_cpm, rmself.cal3_usv, rmself.cal3_fac, rmself.cal3_rfac ))
        rmself.cal3_usv.textChanged.connect(lambda: checkCalibValidity("cal2usv", rmself.cal3_cpm, rmself.cal3_usv, rmself.cal3_fac, rmself.cal3_rfac ))

 ###############################################################################
    # WiFi settings
        if not gglobs.GMC_WifiEnabled:
            wififlag = False
            wifimsg  = QLabel("<span style='font-weight:400;'>This counter is not WiFi enabled</span>")
        else:
            wififlag = True
            # if setDefault : wifimsg = QLabel("<span style='font-weight:900;'>Showing User configuration read from GeigerLog's config file</span>")
            if setDefault : wifimsg = QLabel("<span style='font-weight:900;'>Showing GeigerLog configuration read from its configuration file</span>")
            else:           wifimsg = QLabel("<span style='font-weight:900;'>Showing active configuration read from the Counter</span>")

        dashline = QLabel("<span style='font-weight:500;'>{}</span>".format("-" * 70))
        dashline.setAlignment(Qt.AlignCenter)
        fbox.addRow(dashline)
        fbox.addRow(QLabel("<span style='font-weight:900;'>WiFi Capable GMC Counter</span>"), wifimsg)

    # WiFi On Off settings
        r31 = QRadioButton("On")
        r32 = QRadioButton("Off")
        r31.setChecked(False)
        r32.setChecked(False)
        r31.setEnabled(wififlag)
        r32.setEnabled(wififlag)
        wifigroup = QButtonGroup()
        wifigroup.addButton(r31)
        wifigroup.addButton(r32)
        hbox3 = QHBoxLayout()
        hbox3.addWidget(r31)
        hbox3.addWidget(r32)
        hbox3.addStretch()
        fbox.addRow(QLabel("WiFi"), hbox3)
        if isGMC_WifiOn() == 'ON':   r31.setChecked(True)
        else:                        r32.setChecked(True)

    # WiFi text settings
        wwifi = 32
        l1e=QLineEdit()                     # SSID (< 32 char)
        l1e.setMaxLength (wwifi)
        l2e=QLineEdit()                     # pw (< 63 char)
        l2e.setMaxLength (wwifi * 2 - 1)
        l3e=QLineEdit()                     # website
        l3e.setMaxLength (wwifi)
        l4e=QLineEdit()                     # url
        l4e.setMaxLength (wwifi)
        l5e=QLineEdit()                     # counter id
        l5e.setMaxLength (wwifi)
        l6e=QLineEdit()                     # user id
        l6e.setMaxLength (wwifi)
        l7e=QLineEdit()                     # period (0 ... 255)
        l7e.setMaxLength (3)

        fbox.addRow("WiFi SSID",            l1e)
        fbox.addRow("WiFi Password",        l2e)
        fbox.addRow("Server Website",       l3e)
        fbox.addRow("Server URL",           l4e)
        fbox.addRow("Server CounterID",     l5e)
        fbox.addRow("Server UserID",        l6e)
        fbox.addRow("Server Period (min)",  l7e)

        # fill the text fields
        if setDefault : ndx = 0 # i.e. show what is defined in the GeigerLog config
        else:           ndx = 1 # otherwise from device
        l1e.setText(cfgKeyHigh["SSID"]      [ndx])
        l2e.setText(cfgKeyHigh["Password"]  [ndx])
        l3e.setText(cfgKeyHigh["Website"]   [ndx])
        l4e.setText(cfgKeyHigh["URL"]       [ndx])
        l5e.setText(cfgKeyHigh["CounterID"] [ndx])
        l6e.setText(cfgKeyHigh["UserID"]    [ndx])
        # print("ndx: ", ndx)
        # print("-------------------------------------------------cfgKeyHigh['Period']    [ndx]:", cfgKeyHigh["Period"]    [ndx], type(cfgKeyHigh["Period"]    [ndx]))
        l7e.setText(cfgKeyHigh["Period"]    [ndx])

        l1e.setEnabled(wififlag)
        l2e.setEnabled(wififlag)
        l3e.setEnabled(wififlag)
        l4e.setEnabled(wififlag)
        l5e.setEnabled(wififlag)
        l6e.setEnabled(wififlag)
        l7e.setEnabled(wififlag)

    # FET (Fast Estimate) Capable GMC counter
        # separate with dashline
        dashline2 = QLabel("<span style='font-weight:500;'>{}</span>".format("-" * 70))
        dashline2.setAlignment(Qt.AlignCenter)
        fbox.addRow(dashline2)

        # header
        if not gglobs.GMC_FETenabled:
            FETmsg = QLabel("<span style='font-weight:400;'>This counter has no FET setting</span>")
        else:
            FETmsg = QLabel("<span style='color:red;'>CAUTION: before chosing anything but 60 see GeigerLog manual</span>")
        fbox.addRow(QLabel("<span style='font-weight:900;'>FET Capable GMC Counter</span>"), FETmsg)

        # selector
        lcb5 = QLabel("FET (Fast Estimate Time) ")
        lcb5.setEnabled(gglobs.GMC_FETenabled)

        cb5 = QComboBox()
        cb5.addItems(["60", "30", "20", "15", "10", "5", "3"])
        cb5.setCurrentIndex(0)
        cb5.setEnabled(gglobs.GMC_FETenabled)

        hbox5 = QHBoxLayout()
        hbox5.addWidget(cb5)
        fbox.addRow(lcb5, hbox5)

    # final blank line
        fbox.addRow(QLabel(""))

    # dialog
        dialog = QDialog()
        dialog.setWindowIcon(gglobs.iconGeigerLog)
        dialog.setFont(gglobs.fontstd)
        dialog.setWindowTitle("Set GMC Configuration")
        dialog.setWindowModality(Qt.WindowModal)

        # buttonbox: https://srinikom.github.io/pyside-docs/PySide/QtGui/QDialogButtonBox.html
        bbox = QDialogButtonBox()
        bbox.setStandardButtons(QDialogButtonBox.Ok|QDialogButtonBox.Cancel|QDialogButtonBox.Reset|QDialogButtonBox.Help)
        bbox.rejected.connect           (lambda: dialog.done(0))    # cancel, ESC key
        bbox.accepted.connect           (lambda: dialog.done(1))    # ok
        bbox.helpRequested.connect      (lambda: dialog.done(2))    # Help: Apply ...
        bbox.clicked .connect           (lambda: dialog.done(3))    # reset

        gglobs.bboxbtn = bbox.button(QDialogButtonBox.Ok)           # ok button
        gglobs.bboxbtn.setEnabled(True)

        bboxhbtn = bbox.button(QDialogButtonBox.Help)               # Help button
        # bboxhbtn.setText("Show User Configuration")
        bboxhbtn.setText("Show GeigerLog Configuration")
        bboxhbtn.setEnabled(wififlag)

        bboxRbtn = bbox.button(QDialogButtonBox.Reset)              # Reset button
        bboxRbtn.setText("Show Counter's Active Configuration")
        bboxRbtn.setEnabled(wififlag)

        layoutV   = QVBoxLayout(dialog)
        layoutV.addLayout(fbox)
        layoutV.addWidget(bbox)

        popupdlg = dialog.exec()
        #~print("-------------Ex:", popupdlg)

        if   popupdlg == 0:
            setIndent(0)
            return              # reject
        elif popupdlg == 1:     break               # accept; end while
        elif popupdlg == 2:     setDefault = True   # help, Apply ... i.e. show what is defined in the GeigerLog config
        elif popupdlg == 3:     setDefault = False  # reset           i.e. show what is read from device
        else:
            setIndent(0)
            return              # should never be called

    # while ends here

    # cdprint("Power:       r01 is Checked: ", r01.isChecked(), ", Power:       r02 is Checked: ", r02.isChecked())
    cdprint("Alarm:       r11 is Checked: ", r11.isChecked(), ", Alarm:       r12 is Checked: ", r12.isChecked())
    cdprint("Speaker:     r21 is Checked: ", r21.isChecked(), ", Speaker:     r22 is Checked: ", r22.isChecked())
    cdprint("HistSavMode: cb1.currentIndex():", cb1.currentIndex())
    cdprint("LightStatus: cb2.currentIndex():", cb2.currentIndex())

    cdprint("cal1_cpm: ", rmself.cal1_cpm.text ())
    cdprint("cal1_usv: ", rmself.cal1_usv.text ())
    cdprint("cal2_cpm: ", rmself.cal2_cpm.text ())
    cdprint("cal2_usv: ", rmself.cal2_usv.text ())
    cdprint("cal3_cpm: ", rmself.cal3_cpm.text ())
    cdprint("cal3_usv: ", rmself.cal3_usv.text ())

    ndx = 0
    # cfgKeyLow["Power"]          [ndx] = 0 if r01.isChecked() else 255
    cfgKeyLow["Alarm"]          [ndx] = 1 if r11.isChecked() else 0
    cfgKeyLow["Speaker"]        [ndx] = 1 if r21.isChecked() else 0
    cfgKeyLow["SaveDataType"]   [ndx] = cb1.currentIndex()

    cb2ci = cb2.currentIndex()
    if   cb2ci == 0 : LightStatusValue = 0  # "Light: OFF",     # 0     counter: 0
    elif cb2ci == 1 : LightStatusValue = 1  # "Light: ON",      # 1     counter: 1
    elif cb2ci == 2 : LightStatusValue = 2  # "Timeout: 1",     # 2     counter: 2
    elif cb2ci == 3 : LightStatusValue = 4  # "Timeout: 3",     # 3     counter: 4
    elif cb2ci == 4 : LightStatusValue = 11 # "Timeout: 10",    # 4     counter: 11
    else            : LightStatusValue = 31 # "Timeout: 30",    # 5     counter: 31
    cfgKeyLow["BackLightTimeoutSeconds"] [ndx] = LightStatusValue

    cfgKeyLow["CalibCPM_0"]     [ndx] = rmself.cal1_cpm.text()
    cfgKeyLow["CalibuSv_0"]     [ndx] = rmself.cal1_usv.text()
    cfgKeyLow["CalibCPM_1"]     [ndx] = rmself.cal2_cpm.text()
    cfgKeyLow["CalibuSv_1"]     [ndx] = rmself.cal2_usv.text()
    cfgKeyLow["CalibCPM_2"]     [ndx] = rmself.cal3_cpm.text()
    cfgKeyLow["CalibuSv_2"]     [ndx] = rmself.cal3_usv.text()

    for key in cfgKeyLow:
        cdprint("cfgKeyLow:  {:25s}".format(key), cfgKeyLow[key][ndx])
    cdprint()

    if gglobs.GMC_WifiEnabled:
        cdprint("WiFi:        r31 is Checked: ", r31.isChecked(), ", WiFi:        r32 is Checked: ", r32.isChecked())
        ndx = 1
        cfgKeyHigh["SSID"]       [ndx] = l1e.text()
        cfgKeyHigh["Password"]   [ndx] = l2e.text()
        cfgKeyHigh["Website"]    [ndx] = l3e.text()
        cfgKeyHigh["URL"]        [ndx] = l4e.text()
        cfgKeyHigh["CounterID"]  [ndx] = l5e.text()
        cfgKeyHigh["UserID"]     [ndx] = l6e.text()
        cfgKeyHigh["Period"]     [ndx] = l7e.text()
        cfgKeyHigh["WiFi"]       [ndx] = r31.isChecked()

        for key in cfgKeyHigh:
            cdprint("cfgKeyHigh: {:20s}".format(key), cfgKeyHigh[key][ndx])

    if gglobs.GMC_FETenabled:
        ndx = 1
        cfgKeyHigh["FET"][ndx] = int(cb5.currentText())
        cdprint("Fast Est Time: cb5.currentIndex():", cb5.currentIndex())
        cdprint("Fast Est Time: cb5.currentText():",  cb5.currentText())

    cdprint()

    fprint(header("Set GMC Configuration"))
    QtUpdate()

    setGMC_ConfigSettings()

    setIndent(0)


def checkCalibValidity(field, var1, var2, var3, var4):
    """verify proper sensitivity data"""

    # GMC popup editing:
    # var1 = rmself.calN_cpm
    # var2 = rmself.calN_usv
    # var3 = rmself.calN_fac
    # var4 = rmself.calN_rfac

    #~QValidator.Invalid                    0   The string is clearly invalid.
    #~QValidator.Intermediate               1   The string is a plausible intermediate value.
    #~QValidator.Acceptable                 2   The string is acceptable as a final result; i.e. it is valid.

    #~QDoubleValidator.StandardNotation     0   The string is written as a standard number (i.e. 0.015).
    #~QDoubleValidator.ScientificNotation   1   The string is written in scientific form. It may have an exponent part(i.e. 1.5E-2).

    rmself = gglobs.exgg

    if "," in var1.text(): var1.setText(var1.text().replace(",", ""))   # no comma
    if "," in var2.text(): var2.setText(var2.text().replace(",", "."))  # replace comma with period

    fncname = "checkCalibValidity: "
    cdprint("\n" + fncname + "--- field, var1, var2, var3, var4: ", field, var1.text(), var2.text(), var3.text(), var4.text())

    sender = rmself.sender()
    cdprint("sender.text():",   sender.text())

    validator = sender.validator()

    state = validator.validate(sender.text(), 0)
    cdprint("state:    ", state)
    cdprint("state[0]: ", state[0])

    if state[0] == QValidator.Acceptable:
        bgcolor = 'white'
        validMatrix[field] = True

    elif state[0] == QValidator.Intermediate:
        bgcolor = '#fff79a' # yellow
        validMatrix[field] = False

    else:
        playWav("err")
        bgcolor = '#f6989d' # red
        validMatrix[field] = False

    sender.setStyleSheet('QLineEdit { background-color: %s }' % bgcolor)

    if False in validMatrix.values():   gglobs.bboxbtn.setEnabled(False)
    else:                               gglobs.bboxbtn.setEnabled(True)

    try:    ivar1 = int(abs(float(var1.text().replace(",", "."))))
    except: ivar1 = float('nan')

    try:    fvar2 = abs(float(var2.text().replace(",", ".")))
    except: fvar2 = float('nan')

    var3.setText("{:8.5g}".format(float('nan') if fvar2 == 0 else ivar1 / fvar2))   # calib fac  (New)
    var4.setText("{:8.5g}".format(float('nan') if ivar1 == 0 else fvar2 / ivar1))   # calib rfac (Old)


def getGMC_SerialNumber(usbport, baudrate):
    # Get serial number
    # send <GETSERIAL>> and read 7 bytes
    # each nibble of 4 bit is a single hex digit of a 14 character serial number
    # e.g.: F488007E051234
    #
    # return: the serial number as a 14 character ASCII string

    fncname = "getGMC_SerialNumber: "
    dprint(fncname)
    setIndent(1)

    try:
        with serial.Serial(usbport, baudrate=baudrate, timeout=0.3, write_timeout=0.5) as ABRser:
            bwrt = ABRser.write(b'<GETSERIAL>>')
            brec = ABRser.read(7)    # try to get the GMC device serial number
    except Exception as e:
        errmessage1 = fncname + "FAILURE: Reading from device; returning None"
        exceptPrint(e, errmessage1)
        setIndent(0)
        return None

    dprint(fncname + "raw: brec: ", brec)

    if len(brec) == 7:
        hexlookup = "0123456789ABCDEF"
        srec = ""
        for i in range(0, 7):
            n1    = ((brec[i] & 0xF0) >> 4)
            n2    = ((brec[i] & 0x0F))
            srec += hexlookup[n1] + hexlookup[n2]
        # dprint(fncname + "decoded: '{}' ".format(srec), type(srec))
    else:
        srec = "undefined"

    setIndent(0)

    return srec


def setGMC_DATETIME():
    # from GQ-RFC1201.txt:
    # NOT CORRECT !!!!
    # 22. Set year date and time
    # command: <SETDATETIME[YYMMDDHHMMSS]>>
    # Return: 0xAA
    # Firmware supported: GMC-280, GMC-300 Re.3.00 or later

    # from: GQ-GMC-ICD.odt
    # CORRECT! 6 bytes, no square brackets
    # <SETDATETIME[YY][MM][DD][hh][mm][ss]>>

    dprint("setGMC_DATETIME:")
    setIndent(1)

    tl      = list(time.localtime())  # tl: [2018, 4, 19, 13, 2, 50, 3, 109, 1]
                                      # for: 2018-04-19 13:02:50
    tl0     = tl.copy()

    tl[0]  -= 2000
    tlstr   = b''
    for i in range(0, 6):  tlstr += bytes([tl[i]])
    dprint("setGMC_DATETIME: now:", tl0[:6], ", coded:", tlstr)

    rec, error, errmessage = serialGMC_COMM(b'<SETDATETIME'+ tlstr + b'>>', 1, orig(__file__))

    setIndent(0)

    return (rec, error, errmessage)


def getGMC_DATETIME():
    # Get date and time
    # send <GETDATETIME>> and read 7 bytes: YY MM DD HH MM SS 0xAA
    #
    # return: date and time in the format:
    #           YYYY-MM-DD HH:MM:SS
    # e.g.:     2017-12-31 14:03:19

    fncname = "getGMC_DATETIME: "
    cdprint(fncname)
    setIndent(1)

    prec  = "2000-01-01 00:00:01" # default fake date to use on error

    # <GETDATETIME>> yields: rec: b'\x12\x04\x13\x0c9;\xaa' , len:7
    #                for:         2018-04-19 12:57:59
    rec, error, errmessage = serialGMC_COMM(b'<GETDATETIME>>', 7, orig(__file__))

    if rec == None:
        dprint(fncname + "ERROR: no DateTime received - ", errmessage)
    else:
        if error == 0 or error == 1:  # Ok or only Warning
            try:
                prec = datetime.datetime(rec[0] + 2000, rec[1], rec[2], rec[3], rec[4], rec[5])
            except Exception as e:
                if rec ==  [0, 1, 1, 0, 0, 80, 170]:    # the values found after first start!
                    prec        = "2000-01-01 00:00:01" # overwrite rec with fake date
                    error       = -1
                    errmessage  = "ERROR getting Date & Time - Set at device first!"
                else:
                    # conversion to date failed
                    prec        = "2099-09-09 09:09:09" # overwrite rec with fake date
                    error       = -1
                    errmessage  = "ERROR getting Date & Time"

        else:   # a real error
            dprint(fncname + "ERROR getting DATETIME: ", errmessage, debug=True)

        cdprint(fncname + "raw: len: {} rec: {}   parsed: {}  errmsg: '{}'".format(len(rec), str(rec), prec, errmessage))

    setIndent(0)

    return (prec, error, errmessage)


def getGMC_TEMP():
    # NOTE: Temperature may be completely inactive in 500 and 600 versions
    # and or produce random results! see:
    # http://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=4948
    #
    # Get temperature
    # Firmware supported: GMC-320 Re.3.01 or later (NOTE: Not for GMC-300!)
    # send <GETTEMP>> and read 4 bytes
    # Return: Four bytes celsius degree data in hexdecimal: BYTE1,BYTE2,BYTE3,BYTE4
    # Here: BYTE1 is the integer part of the temperature.
    #       BYTE2 is the decimal part of the temperature.
    #       BYTE3 is the negative signe if it is not 0.  If this byte is 0,
    #       then current temperture is greater than 0, otherwise the temperature is below 0.
    #       BYTE4 always 0xAA (=170dec)

    fncname = "getGMC_TEMP: "
    dprint(fncname)
    setIndent(1)

    rec, error, errmessage = serialGMC_COMM(b'<GETTEMP>>', 4, orig(__file__))

    # # TESTING example for '-28.8 °C' ###
    # rec        = b'\x1c\x08\x01\xaa'
    # error      = 0
    # errmessage = "testing"
    # ####################################

    srec = ""
    for i in range(len(rec)): srec += "{}, ".format(rec[i])

    cdprint(fncname + "Temp raw: rec= {} (=dec: {}), err={}, errmessage='{}'".format(rec, srec[:-2], error, errmessage))

    if error == 0 or error == 1:  # Ok or Warning
        if "GMC-3" in gglobs.GMCDeviceDetected :   # all 300 series
            temp = rec[0] + rec[1]/100.0     # unclear: is  decimal part rec[1] single digit or a 2 digit?
                                            # 3 digit not possible as byte value is from 0 ... 255
                                            # expecting rec[1] always from 0 ... 9
            if rec[2] != 0 : temp *= -1
            # if rec[1]  > 9 : temp  = "ERROR: Temp={} - illegal value found for decimal part of temperature={}".format(temp, rec[1])

            # edprint("temp: ", rec[0] + rec[1]/100.0, "  ", rec[0] + rec[1]/10.0)
            rec = temp

        elif   "GMC-5" in gglobs.GMCDeviceDetected \
            or "GMC-6" in gglobs.GMCDeviceDetected:  # GMC-500/600
            # rec[1] is always one of dec: 0, 8, 10, 12, 14 - nothong else???
            # temp = rec[0] + rec[1]/10.0    # unclear: is  decimal part rec[1] single digit or a 2 digit?
            temp = rec[0] + rec[1]/100.0     # unclear: is  decimal part rec[1] single digit or a 2 digit?
                                             # 3 digit not possible as byte value is from 0 ... 255
                                             # expecting rec[1] always from 0 ... 9
            #if rec[2] <= 0 : temp *= -1     # guessing: value=1 looks like positive Temperature. Negative is??? Maybe not right at all
            if rec[2] != 0 : temp *= -1      # using the old definition again
            # if rec[1]  > 9 : temp  = "ERROR: Temp={} - illegal value found for decimal part of temperature={}".format(temp, rec[1])

            # edprint("temp: ", rec[0] + rec[1]/100.0, "  ", rec[0] + rec[1]/10.0, "  ", rec[0] + (rec[1]<<4)/100.0)

            rec = temp

        else: # perhaps even 200 series?
            rec = "UNDEFINED"

    dprint(fncname + "Temp      rec= {}, err={}, errmessage='{}'".format(rec, error, errmessage))

    setIndent(0)

    return (rec, error, errmessage)


def getGMC_GYRO():
    # Get gyroscope data
    # Firmware supported: GMC-320 Re.3.01 or later (NOTE: Not for GMC-300!)
    # Send <GETGYRO>> and read 7 bytes
    # Return: Seven bytes gyroscope data in hexdecimal: BYTE1,BYTE2,BYTE3,BYTE4,BYTE5,BYTE6,BYTE7
    # Here: BYTE1,BYTE2 are the X position data in 16 bits value. The first byte is MSB byte data and second byte is LSB byte data.
    #       BYTE3,BYTE4 are the Y position data in 16 bits value. The first byte is MSB byte data and second byte is LSB byte data.
    #       BYTE5,BYTE6 are the Z position data in 16 bits value. The first byte is MSB byte data and second byte is LSB byte data.
    #       BYTE7 always 0xAA

    fncname = "getGMC_GYRO: "

    dprint(fncname)
    setIndent(1)

    rec, error, errmessage = serialGMC_COMM(b'<GETGYRO>>', 7, orig(__file__))
    dprint(fncname + "raw: rec={}, err={}, errmessage='{}'".format(rec, error, errmessage))

    if error in (0, 1):             # Ok or Warning
        x = rec[0] * 256 + rec[1]
        y = rec[2] * 256 + rec[3]
        z = rec[4] * 256 + rec[5]
        srec = "X=0x{:04x}, Y=0x{:04x}, Z=0x{:04x}   ({}, {}, {})".format(x, y, z, x, y, z)
    else:
        srec = "Failure getting Gyro data:  rec='{}' errmsg='{}".format(rec, errmessage)

    dprint(fncname + srec)

    setIndent(0)

    return srec, error, errmessage


def setGMC_POWEROFF():
    # 12. Power OFF
    # Command: <POWEROFF>>
    # Return: none
    # Firmware supported: GMC-280, GMC-300 Re.2.11 or later

    # sleeping after Power OFF
    #   on a GMC-300E+ a minimum of 2 sec is needed
    #   on a GMC-500+  a minimum of 1 sec is needed
    #   using 3 sec to be safe

    rec  = serialGMC_COMM(b'<POWEROFF>>', 0, orig(__file__))
    dprint("setGMC_POWEROFF: ", rec)

    time.sleep(3)

    return rec


def setGMC_POWERON():
    # 26. Power ON
    # Command: <POWERON>>
    # Return: none
    # Firmware supported: GMC-280, GMC-300, GMC-320 Re.3.10 or later

    # sleeping after Power ON
    #   on a GMC-300E+ not tested
    #   on a GMC-500+  not tested
    #   using 3 sec to be safe, as for setGMC_POWEROFF

    rec  = serialGMC_COMM(b'<POWERON>>', 0, orig(__file__))
    dprint("setGMC_POWERON: ", rec)

    time.sleep(3)

    return rec


def setGMC_REBOOT():
    # 21. Reboot unit
    # command: <REBOOT>>
    # Return: None
    # Firmware supported: GMC-280, GMC-300 Re.3.00 or later
    # Duration: 20.2 ms
    # GMC 300 takes 580 ms before responding normally

    fncname = "setGMC_REBOOT: "
    dprint(fncname)
    setIndent(1)

    rec  = serialGMC_COMM(b'<REBOOT>>', 0, orig(__file__))
    dprint(fncname, rec)

    time.sleep(0.6)

    setIndent(0)

    return rec


def setGMC_FACTORYRESET():
    # 20. Reset unit to factory default
    # command: <FACTORYRESET>>
    # Return: 0xAA
    # Firmware supported: GMC-280, GMC-300 Re.3.00 or later

    fncname = "setGMC_FACTORYRESET: "
    dprint(fncname)
    setIndent(1)

    rec  = serialGMC_COMM(b'<FACTORYRESET>>', 1, orig(__file__))
    dprint(fncname, rec)
    time.sleep(0.1)
    dprint(fncname + "Done")
    setIndent(0)

    return rec


#
# Derived commands and functions
#


def getGMC_DeltaTime():
    """reads the DateTime from computer and device, converts into a number,
    and returns the int of delta time in sec"""

    fncname = "getGMC_DeltaTime: "

    rec, error, errmessage = getGMC_DATETIME()

    if error < 0:
        # error
        edprint(fncname + "rec:{}, error:{}, errmessage:'{}'".format(rec, error, errmessage))
        return (gglobs.NAN, rec)

    # ok or Warning only
    time_computer = longstime()
    time_device   = str(rec)
    time_delta    = round((mpld.datestr2num(time_computer) - mpld.datestr2num(time_device)) * 86400, 6)
    cdprint(fncname + "device:{}, computer:{}, Delta Comp ./. Dev:{:0.3f} sec".format(time_device, time_computer, time_delta))

    return (time_delta, rec)


def getGMC_TimeMessage():
    """determines difference between times of computer and device and gives message"""

    getDeltaTime   = getGMC_DeltaTime() # returns (time_delta, DateTime)

    deltatime      = getDeltaTime[0]    # is nan on error
    # print("deltatime", deltatime)
    deviceDateTime = getDeltaTime[1]
    # print("deviceDateTime", deviceDateTime)

    return getDeltaTimeMessage(deltatime, deviceDateTime)


def isGMC_PowerOn(getconfig=False):
    """Checks Power status in the configuration"""

    #PowerOnOff byte:
    #at config offset  : 0
    #300 series        : 0 for ON and 255 for OFF
    #http://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=4948  Reply #14
    #confirmed in Reply #17
    #500/600 series    : PowerOnOff byte: 0 for ON, and 1 for OFF
    # returns: ON, OFF, or UNKNOWN as string

    if getconfig:       getGMC_Config()    # refresh the config if so requested

    try:        c = ord(cfgKeyLow["Power"][0])
    except:
        try:    c = cfgKeyLow["Power"][0]
        except Exception as e:
            dprint( "isGMC_PowerOn: Exception: {}".format(e))
            return "UNKNOWN"

    try:
        if "GMC-3" in gglobs.GMCDeviceDetected:         # all 300series
            #print("GMC-3 in gglobs.GMCDeviceDetected")
            if   c == 0:            p = "ON"
            elif c == 255:          p = "OFF"
            else:                   p = c

        elif "GMC-5" in gglobs.GMCDeviceDetected or \
             "GMC-6" in gglobs.GMCDeviceDetected :      # 500, 500+, 600, 600+
            # as stated by EmfDev from GQ, but strange because different from
            # handling the Speaker and Alarm settings
            if   c == 0:            p = "ON"
            elif c  > 0:            p = "OFF"
            else:                   p = c

        else:
            p = "UNKNOWN"
    except:
        p = "UNKNOWN"

    return p


def isGMC_AlarmOn():
    """Checks Alarm On status in the configuration.
    Alarm is at offset:1"""

    try:    c = ord(cfgKeyLow["Alarm"][0])
    except: return "UNKNOWN"

    if   c == 0:            p = "OFF"
    elif c == 1:            p = "ON"
    else:                   p = c

    return p


def isGMC_SpeakerOn():
    """Checks Speaker On status in the configuration.
    Speaker is at offset:2"""

    try:    c = ord(cfgKeyLow["Speaker"][0])
    except: return "UNKNOWN"

    if   c == 0:            p = "OFF"
    elif c == 1:            p = "ON"
    else:                   p = c

    return p


def isGMC_WifiOn():
    """Checks WiFi status in the configuration"""

    if not gglobs.GMC_WifiEnabled: return "No WiFi"

    fncname = "isGMC_WifiOn: "

    try:   c = gglobs.GMC_cfg[cfgKeyHigh["WiFi"][gglobs.GMC_WifiIndex][0]]
    except Exception as e:
        dprint(fncname + "Exception: {}".format(e))
        c = 255
    #~print(fncname + "c=", c)

    if   c == 0:            return "OFF"
    elif c == 1:            return "ON"
    else:                   return "Unknown"


def getLightStatus():

    try:    c = ord(cfgKeyLow["BackLightTimeoutSeconds"][0])
    except: return "UNKNOWN"

    if   c == 0 : p = "Light: OFF"
    elif c == 1 : p = "Light: ON"
    else        : p = "Timeout: {} sec".format(c - 1)

    return p


def getGMC_BatteryType():
    """Checks Battery Type in the configuration"""

    # cfg Offset Battery = 56
    # Battery Type: 1 is non rechargeable.
    #               0 is chargeable.

    try:    c = ord(cfgKeyLow["Battery"][0])
    except: return "Unknown (Exception)"

    if   c == 0:    p = "ReChargeable"
    elif c == 1:    p = "Non-ReChargeable"
    else:           p = "Unknown (Type:{})".format(c)

    return p


# is not in use; keep for config reference
def XXXgetGMC_BAUDRATE():
    """reads the baudrate from the counter's configuration data"""

    # NOTE: kind of pointless, because in order to read the config data
    # from the device you must already know the baudrate, or the comm
    # will fail :-/

    # discovered for the 300 series:
    #     baudrate = 1200         # config setting:  64
    #     baudrate = 2400         # config setting: 160
    #     baudrate = 4800         # config setting: 208
    #     baudrate = 9600         # config setting: 232
    #     baudrate = 14400        # config setting: 240
    #     baudrate = 19200        # config setting: 244
    #     baudrate = 28800        # config setting: 248
    #     baudrate = 38400        # config setting: 250
    #     baudrate = 57600        # config setting: 252
    #     baudrate = 115200       # config setting: 254
    #     #baudrate = 921600      # config setting: not available
    #
    # discovered for the GMC-500 and 600 series
    # by EmfDev from GQ from here:
    # http://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=4948 Reply #14
    # The baudrate config is now
    #     baudrate = 115200       # config setting: 0
    #     baudrate = 1200         # config setting: 1
    #     baudrate = 2400         # config setting: 2
    #     baudrate = 4800         # config setting: 3
    #     baudrate = 9600         # config setting: 4
    #     baudrate = 14400        # config setting: 5
    #     baudrate = 19200        # config setting: 6
    #     baudrate = 28800        # config setting: 7
    #     baudrate = 38400        # config setting: 8
    #     baudrate = 57600        # config setting: 9

    fncname = "getGMC_BAUDRATE: "
    dprint(fncname)
    setIndent(1)

    if  "GMC-3" in gglobs.GMCDeviceDetected:
        # all 300series
        brdict  = {64:1200, 160:2400, 208:4800, 232:9600, 240:14400, 244:19200, 248:28800, 250:38400, 252:57600, 254:115200}

    elif "GMC-5" in gglobs.GMCDeviceDetected or "GMC-6" in gglobs.GMCDeviceDetected :
        # 500, 500+, 600, 600+
        brdict  = {0:115200, 1:1200, 2:2400, 3:4800, 4:9600, 5:14400, 6:19200, 7:28800, 8:38400, 9:57600}

    else:
        brdict  = {}

    # print(fncname + "cfg Baudrate:")
    # for key, value in sorted(brdict.items()):
    #    print ("      {:08b} {:3d} {:6d}".format(key, key, value))

    try:
        key = ord(cfgKeyLow["Baudrate"][0])
        cdprint("key: ", key)
        rec = brdict[key]
    except Exception as e:
        exceptPrint(e, "cfgKeyLow[Baudrate] ")
        key = -999
        rec = "ERROR: Baudrate cannot be determined"

    dprint(fncname + str(rec) + " with cfgKeyLow[\"Baudrate\"][0]={}".format(key))

    setIndent(0)

    return rec


#xyz
def serialGMC_COMM(sendtxt, RequestLength, caller=("", "", -1)):
    """open the port to make the serial call
    return: (brec, error, errmessage)
    """
    # brec:       bytes as received
    # error==0:   OK
    # error==1:   Warning
    # error==-1:  ERROR
    # errmessage: <string>

    fncname = "serialGMC_COMM: "
    dprint(fncname)
    setIndent(1)

    brec        = b""
    error       = -1
    errmessage  = "some error"

    try:
        if os.path.exists(gglobs.GMC_usbport):
            with  serial.Serial(gglobs.GMC_usbport,
                                gglobs.GMC_baudrate,
                                timeout=gglobs.GMC_timeoutR,
                                write_timeout=gglobs.GMC_timeoutW) as gglobs.GMCser:
                (brec, error, errmessage) = origserialGMC_COMM(sendtxt, RequestLength, caller=caller)
        else:
            brec, error, errmessage  = (b"", -1, "USB port '{}' does not exist".format(gglobs.GMC_usbport))

    except Exception as e:
        exceptPrint(e, fncname + "USBport missing?")
        (brec, error, errmessage) = (b"", -1, "USB port '{}' does not exist".format(gglobs.GMC_usbport))

    setIndent(0)

    return (brec, error, errmessage)


def origserialGMC_COMM(sendtxt, RequestLength, caller=("", "", -1)):
# def serialGMC_COMM(sendtxt, RequestLength, caller=("", "", -1)):
    """write to and read from serial port, exit on serial port error
    return: (brec, error, errmessage)
        brec:       bytes as received
        error==0:   OK,
        error==1:   Warning,
        error==-1:  ERROR
        errmessage: string
    """

    fncname = "serialGMC_COMM: "

    # cdprint(fncname + "sendtxt:{}  RequestLength:{}  caller:'{}'".format(sendtxt, RequestLength, caller))
    setIndent(1)

    brec        = None
    error       = 0
    errmessage  = ""

    while True:

    #write sendtxt to serial port
        breakWrite = True
        srcinfo    = ""
        try:
            bwrt = gglobs.GMCser.write(sendtxt)          # bwrt = no of bytes written
            breakWrite = False

        except serial.SerialException as e:
            srcinfo = fncname + "ERROR: WRITE failed with SerialException when writing: '{}'".format(sendtxt)
            exceptPrint(e, srcinfo)
        except serial.SerialTimeoutException as e:
            # Exception that is raised on WRITE timeouts.
            srcinfo = fncname + "ERROR: WRITE failed with SerialTimeoutException when writing: '{}'".format(sendtxt)
            exceptPrint(e, srcinfo)
        except Exception as e:
            srcinfo = fncname + "ERROR: WRITE failed with Exception when writing: '{}'".format(sendtxt)
            exceptPrint(e, srcinfo)

        if breakWrite:
            terminateGMC()
            brec        = None
            error       = -1
            errmessage  = fncname + "ERROR: WRITE failed. See log for details"
            break


    # read from serial port
        startrtime = time.time()

        breakRead = True
        srcinfo   = ""
        srce      = ""
        try:
            wstart = time.time()
            while gglobs.GMCser.in_waiting == 0 and (time.time() - wstart) < 0.3:
                pass
            brec  = gglobs.GMCser.read(RequestLength)
            brec += getGMC_ExtraByte(gglobs.GMCser)
            breakRead  = False

        except serial.SerialException as e:
            srcinfo = fncname + "EXCEPTION: READ failed with SerialException"
            srce    = e
        except Exception as e:
            srcinfo = fncname + "EXCEPTION: READ failed with exception"
            srce    = e

        if srcinfo > "":
            edprint(fncname + "EXCEPTION: caller is: {} in line no: {}".format(caller[0], caller[2]), debug=True)
            exceptPrint(srce, srcinfo)

        rdur  =  1000 * (time.time() - startrtime)
        # rdprint(fncname + "caller is: {} in line no: {} duration: {:0.1f} ms".format(caller[0], caller[2], rdur))

        if breakRead:
            terminateGMC()
            brec        = None
            error       = -1
            errmessage  = fncname + "ERROR: READ failed. See log for details"
            break

        if 0:
            if   b"CPM" in sendtxt:   CPtype = "CPM*"             # any CPMxxx
            elif b"CPS" in sendtxt:   CPtype = "CPS*"             # any CPSxxx
            else:                     CPtype = "Non-CPX"          # anything but CPM*, CPS*

            try:    brtime = rdur / len(brec)
            except: brtime = gglobs.NAN

            if   rdur > (gglobs.GMC_timeoutR * 1000):
                marker = BOLDRED + " Timeout--" * 5               # mark TIMEOUT lines

            elif brtime > 20:                                     # mark long read times
                                                                # >20 ms per Byte: GMC-300E+: often 11 ... 23 ms
                marker  = BOLDRED + " Long read time!  "
                marker += "{:0.0f} ms ({:0.0f} ms/B) {}  ".format(rdur, brtime, CPtype)
                marker += ">" * 25

            else:
                marker = ""


            recShort = brec[:10]
            cdprint(fncname + "got {} out of {} bytes in {:0.1f} ms, first ≤10 bytes: {} dec: '{}'".format(
                                                                len(brec),
                                                                RequestLength,
                                                                rdur,
                                                                recShort,
                                                                " ".join("%d" % e for e in recShort),
                                                                ),
                                                            marker)

    # Retry loop
        if len(brec) >= RequestLength:
            pass

        else:
            # check for read timeout
            if rdur > (gglobs.GMC_timeoutR * 1000):
                # yes, a read timeout
                msg  = "{} GMC TIMEOUT ERROR Serial Port; command {} exceeded {:3.1f}s".format(stime(), sendtxt, gglobs.GMC_timeoutR)
                qefprint(html_escape(msg)) # escaping needed as GMC commands like b'<GETCPS>>' have <> brackets
                edprint(fncname + msg, " - rdur:{:5.1f} ms".format(rdur), debug=True)

            efprint("{} Got {} data bytes, expected {}.".format(stime(), len(brec), RequestLength))
            qefprint("{} Retrying.".format(stime()))
            QtUpdate()

            edprint(fncname + "ERROR: Received length: {} is less than requested: {}".format(len(brec), RequestLength), debug=True)
            edprint(fncname + "brec (len={}): {}".format(len(brec), BytesAsHex(brec)))

            # RETRYING
            count    = 0
            countmax = 3
            while True:
                count += 1
                errmsg = fncname + "RETRY to get full return record, trial #{}".format(count)
                dprint(errmsg, debug=True)

                time.sleep(0.5) # extra sleep after not reading enough data

                extra = getGMC_ExtraByte(gglobs.GMCser)   # just to make sure the pipeline is clean

                gglobs.GMCser.write(sendtxt)

                rtime = time.time()
                brec   = gglobs.GMCser.read(RequestLength)
                dprint("Timing (ms): Retry read:{:6.3f}".format(1000 * (time.time() - rtime)))

                if len(brec) == RequestLength:
                    bah = BytesAsHex(brec)
                    if len(bah) > 50: sbah = ", brec:\n" + bah
                    else:             sbah = ", brec:" + bah
                    dprint(fncname + "RETRY: RequestLength is {} bytes. OK now. Continuing normal cycle".format(len(brec)), sbah, debug=True)
                    errmessage += "; ok after {} retry".format(count)
                    extra = getGMC_ExtraByte(gglobs.GMCser)   # just to make sure the pipeline is clean
                    fprint("{} Retry successful.".format(stime()))
                    gglobs.exgg.addGMC_Error(errmessage)
                    break
                else:
                    dprint(u"RETRY:" + fncname + "RequestLength is {} bytes. Still NOT ok; trying again".format(len(brec)), debug=True)
                    pass

                if count >= countmax:
                    dprint(fncname + "RETRY: Retried {} times, always failure, giving up. Serial communication error.".format(count), debug=True)
                    error       = -1
                    errmessage  = "ERROR communicating via serial port. Giving up."
                    efprint(errmessage)
                    gglobs.exgg.addGMC_Error(errmessage)
                    break

                efprint("ERROR communicating via serial port. Retrying again.")

        break

    setIndent(0)

    return (brec, error, errmessage)


def GMCsetDateTime():
    """ set date and time on GMC device to computer date and time"""

    fncname = "GMCsetDateTime: "

    dprint(fncname)
    setIndent(1)

    fprint(header("Set Date&Time of GMC Device"))
    fprint("Setting device time to computer time")

    setGMC_DATETIME()

    fprint(getGMC_TimeMessage())

    setIndent(0)


def getGMC_HistSaveMode():
    """
    Bytenumber:32  Parameter: CFG_SaveDataType
    savedatatypes:
    0 = OFF (no history saving)
    1 = CPS, save every second
    2 = CPM, save every minute
    3 = CPM, save hourly average
    4 = CPS, save every second if exceeding threshold
    5 = CPM, save every minute if exceeding threshold
    """

    fncname = "getGMC_HistSaveMode: "

    sdt     = 9999
    sdttxt  = savedatatypes[:]
    # edprint(fncname + "len(sdttxt):{}, sdttxt:{}".format(len(sdttxt), sdttxt))
    # edprint(fncname + "cfgKeyLow['SaveDataType'][0]: ", cfgKeyLow["SaveDataType"][0])

    if cfgKeyLow["SaveDataType"][0] != None:
        try:
            sdt = ord(cfgKeyLow["SaveDataType"][0])
        except:
            # edprint(fncname + "cfgKeyLow['SaveDataType'][0]: ", cfgKeyLow["SaveDataType"][0])
            # edprint(fncname + "sdt: ", sdt)
            try:
                sdt = int(cfgKeyLow["SaveDataType"][0])
            except Exception as e:
                edprint(fncname + "Exception: ", e)

    # edprint(fncname + "cfgKeyLow['SaveDataType'][0]: ", cfgKeyLow["SaveDataType"][0])
    # edprint(fncname + "sdt: ", sdt)

    try:
        if sdt <= len(sdttxt):  txt = sdttxt[sdt]
        else:                   txt = "UNKNOWN"
        gglobs.GMC_savedatatype  = txt
        gglobs.GMC_savedataindex = sdt
    except Exception as e:
        edprint(fncname + "Exception: ", e)
        txt= fncname + "Error: undefined type: {}".format(sdt)

    # edprint(fncname + "return: sdt:{}, txt:{}".format(sdt, txt) )
    return sdt, txt  # <index>, <mode as text>


def setGMC_HistSaveMode():
    """sets the History Saving Mode"""

    dprint("setGMC_HistSaveMode:")
    setIndent(1)

    while True:
        # get current config
        cfg, error, errmessage = getGMC_Config()
        gglobs.GMC_cfg = cfg
        if error < 0:
            fprint("Error:" + errmessage)
            break

        SDT, SDTtxt = getGMC_HistSaveMode()
        gglobs.GMC_savedatatype = SDTtxt

        # setup dialog and get new config setting
        selection   = savedatatypes
        text, ok    = QInputDialog().getItem(None, 'Set History Saving Mode', "Select new history saving mode and press ok:   ", selection, SDT, False )
        vprint("Set History Saving Mode:", "text=", text, ",  ok=", ok)
        if not ok: break      # user has selected Cancel

        fprint(header("Set History Saving Mode"))

        newSDT = selection.index(text)
        #print "newSDT:", newSDT

        # write the new config data
        setBusyCursor()
        writeGMC_ConfigSingle(cfgKeyLow["SaveDataType"][1][0], newSDT)
        setNormalCursor()

        fprint("Device History Saving Mode:", "{}".format(getGMC_HistSaveMode()[1]))

        break

    setIndent(0)


def switchGMC_DeviceSpeaker(newstate = "ON"):
    """Switch Device Speaker to ON or OFF"""

    setBusyCursor()
    fprint(header("Switch Device Speaker {}".format(newstate)))

    if newstate == "ON": st = 1
    else:                st = 0

    # write the new config data (will get a fresh config)
    writeGMC_ConfigSingle(cfgKeyLow["Speaker"][1][0], st)

    if gglobs.GMC_cfg[cfgKeyLow["Speaker"][1][0]] == 1: ipo = "ON"
    else:                                               ipo = "OFF"

    fprint("Device Speaker State is: ",  ipo)

    setNormalCursor()


def switchGMC_DeviceAlarm(newstate = "ON"):
    """Switch Device Alarm to ON or OFF"""

    setBusyCursor()
    fprint(header("Switch Device Alarm {}".format(newstate)))

    if newstate == "ON":    st = 1
    else:                   st = 0

    # write the new config data
    writeGMC_ConfigSingle(cfgKeyLow["Alarm"][1][0], st)
    time.sleep(1.0)

    fprint("Device Alarm State is: ",  isGMC_AlarmOn())

    setNormalCursor()


def fprintGMC_ConfigMemory():
    """prints the 256 or 512 bytes of device configuration memory to the NotePad"""

    fncname = "fprintGMC_ConfigMemory: "
    setBusyCursor()

    fprint(header("GMC Device Configuration"))
    dprint(fncname)
    setIndent(1)

    cfg, error, errmessage = getGMC_Config()

    fText = ""
    if   cfg == None:
        msg = "FAILURE getting config from device. See log for details."
        dprint(fncname + msg + " errmessage: " + errmessage)
        fText += msg
    else:
        lencfg = len(cfg)
        #~print("cfg: len: {}\n{}".format(lencfg, BytesAsHex(cfg)))
        #~print("cfg: len: {}\n{}".format(lencfg, BytesAsDec(cfg)))
        if error < 0 and lencfg not in (256, 512):
            msg = "FAILURE getting config from device. See log for details."
            dprint(fncname + msg + " errmessage: " + errmessage)
            fText += msg
        else:
            # len(cfg) == 256 or == 512, even with error
            fText     += "The configuration size is: {} bytes\n".format(lencfg)
            fText     += "Format: index(hex):index(dec)  | value(hex)=value(dec)=char(ASCII) | value ... \n"
            cfgcopy    = copy.copy(cfg)                 # use copy of cfg
            cfgstrp    = cfgcopy.rstrip(b'\xFF')        # remove the right-side FF values
            lencfgstrp = len(cfgstrp)
            if lencfgstrp == 0:
                fText += "ERROR: GMC Configuration memory is empty. Try a factory reset!"
            else:
                for i in range(0, lencfgstrp, 8):
                    pcfg = "{:03X}:{:3d}  | ".format(i, i)
                    for j in range(0, 8):
                        k = i + j
                        if k < lencfgstrp:
                            pcfg += "{:02x}={:3d}={:1s}|".format(cfgstrp[k], cfgstrp[k], IntToChar(cfgstrp[k]))
                    fText += pcfg + "\n"

                if lencfgstrp < lencfg:
                    fText += "Remaining {} values up to address {} are all 'ff=255'\n".format(lencfg - lencfgstrp, lencfg - 1)

                fText += "\nThe configuration as ASCII (0xFF as 'F', other non-ASCII characters as '.'):\n" + BytesAsASCIIFF(cfgcopy)

    fText = cleanHTML(fText)    # replace any < or > which may come up in ASCII of cfg

    fprint(fText)
    dprint(fncname + "\n" + fText)
    setIndent(0)
    setNormalCursor()


def getInfoGMC(extended = False):
    """builds string msg of basic or extended info on the GMC device"""

    fncname  = "getInfoGMC: "

    tmp      = "{:30s}{}\n"
    gmcinfo  = ""
    gmcinfo += tmp.format("Configured Connection:", "Port:'{}' Baud:{} Timeouts[s]: R:{} W:{}".format(
        gglobs.GMC_usbport,
        gglobs.GMC_baudrate,
        gglobs.GMC_timeoutR,
        gglobs.GMC_timeoutW)
    )

    if not gglobs.Devices["GMC"][CONN]: return gmcinfo + "<red>Device is not connected</red>"

    # device name
    gmcinfo += tmp.format("Connected Device:", gglobs.GMCDeviceDetected)

    # GMC_Variables
    gmcinfo += tmp.format("Configured Variables:", gglobs.GMC_Variables)

    # Tube sensitivities
    gmcinfo += getTubeSensitivities(gglobs.GMC_Variables)

    if gglobs.logging :
        gmcinfo += "<blue><b>INFO: </b>Cannot contact the Device for info when logging. For access to remaining info<br>stop logging first.</blue>\n"
        return gmcinfo

    # only on non-logging:

    # read the config
    cfg, error, errmessage = getGMC_Config()

    # time check
    gmcinfo += getGMC_TimeMessage()

    # power state
    gmcinfo += tmp.format("Device Power State:", isGMC_PowerOn(getconfig=False))

    # FET enabled counter
    if gglobs.GMC_FETenabled:
        try:    fet = int(float(gglobs.GMC_FastEstTime))
        except: fet = gglobs.NAN
        gmcinfo += tmp.format("FET (Fast Estimate Time):", "{} seconds".format(fet))
        if fet != 60:
            gmcinfo += tmp.format("<red>CAUTION: anything different from 60 sec results in false data!","")
            gmcinfo += tmp.format("<red>Correct in menu: Device -> GMC Series -> 'Set GMC Configuration'.", "")
            gmcinfo += tmp.format("<red>See GeigerLog manual.", "")


    if extended == True:
        gmcinfo += "\n"
        gmcinfo += tmp.format("Extended Info:", "")

        # Alarm state
        gmcinfo += tmp.format("Device Alarm State:", isGMC_AlarmOn())

        # Alarm level CPM
        CPMAlarmType = "Unknown"
        try:
            msb = gglobs.GMC_cfg[cfgKeyLow["AlarmCPMValue"][1][0]]
            lsb = gglobs.GMC_cfg[cfgKeyLow["AlarmCPMValue"][1][1]]
            AlarmCPM     = msb * 256 + lsb
            AlarmType    = gglobs.GMC_cfg[cfgKeyLow["AlarmType"][1][0]]
            CPMAlarmType = "Selected" if AlarmType == 0 else "NOT selected"
        except Exception as e:
            exceptPrint(e, "Alarm level CPM")
            AlarmCPM = gglobs.NAN
        gmcinfo += tmp.format("Device Alarm Level CPM:  ", "{:12s}: CPM:   {:<5.0f} (= µSv/h: {:5.3f})".format(CPMAlarmType, AlarmCPM, AlarmCPM / gglobs.Sensitivity[0]))

        # Alarm level µSv/h
        uSvAlarmType = "Unknown"
        try:
            # set endian
            if gglobs.GMC_endianness == 'big': fString = ">f"  # use big-endian ---   500er, 600er:
            else:                              fString = "<f"  # use little-endian -- other than 500er and 600er:

            AlarmuSv     = struct.unpack(fString, cfgKeyLow["AlarmValueuSv"][0] )[0]
            AlarmType    = gglobs.GMC_cfg[cfgKeyLow["AlarmType"][1][0]]
            uSvAlarmType = "Selected" if AlarmType == 1 else "NOT selected"
        except Exception as e:
            exceptPrint(e, "Alarm level uSv")
            AlarmuSv = gglobs.NAN
        gmcinfo += tmp.format("Device Alarm Level µSv/h:", "{:12s}: µSv/h: {:<5.3f} (= CPM:   {:<5.0f})".format(uSvAlarmType, AlarmuSv, AlarmuSv * gglobs.Sensitivity[0]))

        # Speaker state
        gmcinfo += tmp.format("Device Speaker State:", isGMC_SpeakerOn())

        # Light state
        gmcinfo += tmp.format("Device Light State:", getLightStatus())

        # Save Data Type
        sdt, sdttxt = getGMC_HistSaveMode()
        gmcinfo += tmp.format("Device Hist. Saving Mode:", sdttxt)

        # MaxCPM
        value = cfgKeyLow["MaxCPM"][0]
        gmcinfo += tmp.format("Device Max CPM:", "{} (invalid if equal to 65535!)".format(value))

        # baudrate as read from device
        # not properly readable; inactivated
        # also: rather pointless, as you need to already know it in order to read it :-/
        # gmcinfo += tmp.format("Baudrate read from device:", getGMC_BAUDRATE())

        # voltage
        rec, error, errmessage = getGMC_VOLT()
        if error < 0:   gmcinfo += tmp.format("Device Battery Voltage:", "{}"      .format(errmessage))
        else:           gmcinfo += tmp.format("Device Battery Voltage:", "{} Volt" .format(rec)       )

        # Battery Type
        gmcinfo += tmp.format("Device Battery Type Setting:", getGMC_BatteryType())

        # # temperature
        # # temperature is taken out of firmware.
        # # Apparently not valid at all in 500 series, not working in the 300series
        # rec, error, errmessage = getGMC_TEMP()
        # if error < 0:
        #     gmcinfo += tmp.format("Device Temperature:", "'{}'" .format(errmessage))
        # else:
        #     edprint(fncname + "rec: ", rec, type(rec))
        #     gmcinfo += tmp.format("Device Temperature:", "{} °C".format(rec))   # ONLY for GMC-320 ?

        # gyro
        rec, error, errmessage = getGMC_GYRO()
        if error < 0:
            gmcinfo += tmp.format("Device Gyro Data:", "'{}'".format(errmessage))
        else:
            gmcinfo += tmp.format("Device Gyro data:", rec)
            gmcinfo += tmp.format("", "(only GMC-320 Re.3.01 and later)")

        # Device History Saving Mode - Threshold
        try:
            ThM = ord(cfgKeyLow["ThresholdMode"][0])
            if  ThM in (0, 1, 2):
                ThresholdMode = ("CPM", "µSv/h", "mR/h")
                gmcinfo += tmp.format("Device Hist. Threshold Mode:",   ThresholdMode[ThM])
                gmcinfo += tmp.format("Device Hist. Threshold CPM:",    cfgKeyLow["ThresholdCPM"][0] )
                gmcinfo += tmp.format("Device Hist. Threshold µSv/h:",  "{:0.3f}".format(cfgKeyLow["ThresholduSv"][0]))
            else:
                gmcinfo += tmp.format("Device Hist. Threshold Mode:",   "Not available on this device")
        except Exception as e:
            gmcinfo += tmp.format(str(e), "")

        # get the current writing position in the History memory
        rec, error, errmessage = serialGMC_COMM(b'<GetSPISA>>', 4, orig(__file__))
        writepos = (rec[0] << 16) | rec[1] << 8 | rec[2]
        dprint(fncname + "GetSPISA: rcvd: rec={}, err={}, errmessage='{}'".format(rec, error, errmessage))
        dprint(fncname + "GetSPISA: Write position: Byte #{} (@{:0.3%} of memory)".format(writepos, writepos / gglobs.GMC_memory))
        gmcinfo += tmp.format("Device Hist. Write position:", "Byte #{} (@{:0.3%} of memory)".format(writepos, writepos / gglobs.GMC_memory))

        # blank line
        gmcinfo += "\n"

        # serial number of counter
        sn = getGMC_SerialNumber(gglobs.GMC_usbport, gglobs.GMC_baudrate)
        gmcinfo += tmp.format("Device Serial Number:", "{}".format(sn))

        # Calibration settings
        try:
            gmcinfo += tmp.format("\nDevice Calibration Points:", "        CPM  =   µSv/h   CPM / (µSv/h)      µSv/h/CPM")
            for i in range(0, 3):
                calcpm = cfgKeyLow["CalibCPM_{}".format(i)][0]
                calusv = cfgKeyLow["CalibuSv_{}".format(i)][0]
                try:    calfac      = calcpm / calusv
                except: calfac      = gglobs.NAN
                try:    invcalfac   = calusv / calcpm
                except: invcalfac   = gglobs.NAN
                gmcinfo += tmp.format("   Calibration Point", "#{:}: {:6.0f}  = {:7.3f}       {:6.2f}          {:0.5f}".format(
                                                                i + 1, calcpm, calusv, calfac, invcalfac))
        except Exception as e:
            exceptPrint(e, "Calibration Info")
            gmcinfo += "Failure getting Calibration Info from Counter - the counter may need restarting!"

        # WiFi enabled counter
        if gglobs.GMC_WifiEnabled:
            sfmt   = "{:30s}{}\n"
            skeys  = ("SSID", "Password", "Website", "URL", "UserID", "CounterID", "Period")

            # Web related High bytes in Config - as read out from device
            ghc    = "\nDevice Settings for GMCmap (currently active):\n"
            for key in skeys: ghc += sfmt.format("   " + key, cfgKeyHigh[key][1])
            ghc += sfmt.format("   WiFi:",           isGMC_WifiOn())
            gmcinfo += tmp.format(ghc[:-1], "")

            # Web related High bytes in GL Config
            ghc    = "\nGeigerLog's Configuration for Counter's GMCmap Settings:\n"
            for key in skeys: ghc += sfmt.format("   " + key, cfgKeyHigh[key][0])
            ghc += sfmt.format("   WiFi:", "ON" if cfgKeyHigh[key][0] else "OFF")
            gmcinfo += tmp.format(ghc[:-1], "")

        # Firmware settings
        ghc = "\nGeigerLog's Configuration for Counter's Firmware:\n"
        fmt = "   {:27s}{}\n"
        if gglobs.GMCDeviceDetected != "auto":
            ghc += fmt.format("Memory (bytes):",                "{:,}".format(gglobs.GMC_memory))
            ghc += fmt.format("SPIRpage Size (bytes):",         "{:,}".format(gglobs.GMC_SPIRpage))
            ghc += fmt.format("SPIRbugfix (True | False):",     "{:}" .format(gglobs.GMC_SPIRbugfix))
            ghc += fmt.format("Config Size (bytes):",           "{:}" .format(gglobs.GMC_configsize))
            ghc += fmt.format("Voltagebytes (1 | 5):",          "{:}" .format(gglobs.GMC_voltagebytes))
            ghc += fmt.format("Endianness (big | little):",     "{:}" .format(gglobs.GMC_endianness))

        gmcinfo += ghc

        # No of bytes in CP* records
        gmcinfo += fmt.format("Bytes in CP* records:", gglobs.GMC_Bytes)

    return gmcinfo


#xyz
def doEraseSavedData():
    """Erase all data in History memory"""

    fncname = "doEraseSavedData: "

    msg = QMessageBox()
    msg.setWindowIcon(gglobs.iconGeigerLog)
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle("Erase Saved Data")
    msg.setText("All data save into the counter's History memory will be erased.\n\nPlease confirm with OK, or Cancel")
    msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    msg.setDefaultButton(QMessageBox.Cancel)
    msg.setEscapeButton(QMessageBox.Cancel)
    retval = msg.exec()

    if retval == QMessageBox.Ok:    # QMessageBox.Ok == 1024
        # edprint("retval: ", retval)

        dprint(fncname)
        setIndent(1)
        setBusyCursor()

        fprint(header("GMC Device Erase Saved History Data"))
        QtUpdate()

        getGMC_Config()                 # reads config into the local copy
        if isGMC_PowerOn() == "OFF":    # reads only the local config copy
            power_was_on = False
        else:
            power_was_on = True
            fprint("Switching Power OFF")
            gglobs.exgg.dbtnGMCPower.setIcon(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_power-round_off.png'))))
            QtUpdate()
            setGMC_POWEROFF()

        fprint("Begin Erasing")
        QtUpdate()

        rec, err, errmessage = GMC_EraseMemBySPISE()        # ok to use
        # rec, err, errmessage = GMC_EraseMemByFacRESET()   # not good!
        if err == 0 or err == 1:    fprint("Done Erasing")
        else:                       efprint("ERROR trying to Erase Saved Data: " + errmessage)
        QtUpdate()

        if power_was_on:
            fprint("Switching Power ON")
            gglobs.exgg.dbtnGMCPower.setIcon(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_power-round_on.png'))))
            QtUpdate()
            setGMC_POWERON()

        setNormalCursor()
        setIndent(0)


def doREBOOT(force = False):
    """reboot the GMC device"""

    if force:
        retval = QMessageBox.Ok
    else:
        msg = QMessageBox()
        msg.setWindowIcon(gglobs.iconGeigerLog)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Reboot GMC Device")
        msg.setText("Rebooting your GMC device.\n\nPlease confirm with OK, or Cancel")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Cancel)
        msg.setEscapeButton(QMessageBox.Cancel)
        retval = msg.exec()

    if retval == QMessageBox.Ok:
        fprint(header("GMC Device Reboot"))
        rec, err, errmessage = setGMC_REBOOT()
        if err in (0, 1):    fprint("REBOOT completed")
        else:                fprint("ERROR in setGMC_REBOOT: " + errmessage)


def doFACTORYRESET(force = False):
    """Does a FACTORYRESET of the GMC device"""

    d = QInputDialog()
    d.setWindowIcon(gglobs.iconGeigerLog)
    warning ="""
CAUTION - You are about to reset the GMC device to factory condition!
All data and your changes of settings will be lost. \n
If you want to proceed, enter the word 'FACTORYRESET' (in all capital)
and press OK"""

    if force: text, ok = ("FACTORYRESET", True)
    else:     text, ok = d.getText(None, 'FACTORYRESET', warning)

    vprint("Factory Reset:", "text=", text, ",  ok=", ok)
    if ok:
        fprint(header("GMC Device FACTORYRESET"))
        if text == "FACTORYRESET":
            rec, err, errmessage = setGMC_FACTORYRESET()
            if err == 0 or err == 1: fprint("FACTORYRESET completed")
            else:                    fprint("ERROR in setGMC_FACTORYRESET: " + errmessage)
        else:
            fprint("Entry '{}' not matching 'FACTORYRESET' - Reset NOT done".format(text))



###############################################################################
###############################################################################
###############################################################################
###############################################################################

def getGMC_DeviceProperties():
    """define a device and its parameters"""
    # NOTE: does NOT make a call to the device!

    # GETVER                    Model               nominal (observed)
    # GMC-300Re 2.39,           GMC-300             2.xx    (2.39)
    # GMC-300Re 3.xx,           GMC-300             3.xx    (3.20)
    #                           GMC-300E                                        does such a model exist?
    # GMC-300Re 4.xx,           GMC-300E+           4.xx    (4.20, 4.22, 4.54)
    #                           GMC-320                                         does such a model exist?
    # GMC-320Re 4.xx,           GMC-320+            4.xx    (4.19)
    # GMC-320Re 5.xx,           GMC-320+V5 (WiFi)   5.xx
    # GMC-320+V5\x00RRe 5.73,   GMC-320+V5 (WiFi)   5.xx    (5.73)              from Tom Johnson's new GMC-320
    # GMC-500Re 1.xx,           GMC-500 and 500+    1.xx    (1.00, 1.08)
    # GMC-500+Re 1.xx,          GMC-500+            1.??    (1.18(bug), 1.21, 1.22)
    # GMC-500+Re 2.xx,          GMC-500+            2.??
    # GMC-500+Re 2.40,          GMC-500+            2.40    2.40                with new 2nd tube
    # GMC-600Re 1.xx,           GMC-600 and 600+    1.xx    2.26

    ## local ###################################################
    def showUnknownDeviceMsg(DeviceName):
        """if any 'last resort' config had been reached"""

        fncname = "showUnknownDeviceMsg: "

        msg = "<b>ATTENTION</b> A GMC device '{}' was detected, but of a so far unknown model!".format(DeviceName)
        edprint(fncname + msg, debug=True)
        efprint(msg)
        qefprint("Review the 'Extended Info' for this GMC device. You may have to edit the")
        qefprint("configuration file <b>geigerlog.cfg</b> to adapt the settings to this new device.")

    ## end local ###############################################

    fncname = "getGMC_DeviceProperties: "

    dprint(fncname)
    setIndent(1)

    # gglobs.GMCDeviceDetected is set in function "getGMC_Version()"
    dprint("Detected device  : '{}'".format(gglobs.GMCDeviceDetected))

    # reset all
    gglobs.GMC_memory        = "auto"
    gglobs.GMC_SPIRpage      = "auto"
    gglobs.GMC_SPIRbugfix    = "auto"
    gglobs.GMC_configsize    = "auto"
    gglobs.GMC_voltagebytes  = "auto"
    gglobs.GMC_endianness    = "auto"
    gglobs.GMC_Bytes         = "auto"
    # gglobs.GMC_Variables     = "auto"
    gglobs.GMC_locationBug   = "auto"
    gglobs.GMC_WifiIndex     = "auto"
    gglobs.GMC_DualTube      = "auto"
    gglobs.GMC_baudrate      = "auto"
    gglobs.GMC_FETenabled    = "auto"
    gglobs.GMC_FastEstTime   = "auto"

    gglobs.Sensitivity[0]    = "auto"
    gglobs.Sensitivity[1]    = "auto"
    gglobs.Sensitivity[2]    = "auto"


    #
    # default settings
    #
    GMC_locationBug             = "GMC-500+Re 1.18, GMC-500+Re 1.21"
    GMC_sensitivityDef          = 154        # CPM/(µSv/h) - all counter except GMC600
    GMC_sensitivity1st          = 154        # CPM/(µSv/h) - all counter respond even if they have only a single tube
    GMC_sensitivity2nd          = 2.08       # CPM/(µSv/h) - only GMC 500 with 2 tubes
                                             # Note: different 2nd tube in GMC-500+ v2.40 with claimed
                                             # sensitivity 21.37
    GMC_DualTube                = False      # all are single tube, except 1) 500+ and 2) 500(without +) owned by the_Mike
    GMC_WifiEnabled             = True       # all are WiFi, except 300 series (set via GMC_WiFiIndex)
    GMC_baudrate                = 115200     # all, except for GMC300 Re2 Re3 and Re4, for which this is set to 57600
    GMC_FETenabled              = False      # only 500 and 600 counter are enabled
    GMC_FastEstTime             = 60         # which effectively switches FET off

    if "GMC-300Re 2." in gglobs.GMCDeviceDetected :
        #######################################################################
        # 'GMC-300Re 2.39' is used by user ori0n:
        # see:  http://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=9893
        #
        # various aspects not yet determined!!!
        #
        # errors from:      <GETDATETIME>>
        #                   <GETGYRO>>
        # not working:      reboot              # confirmed in GQ-RFC1201 - Ver 1.40 Jan-2015
        #                   factoryreset        # confirmed in GQ-RFC1201 - Ver 1.40 Jan-2015
        # sensitivity:      200 CPM / (µSv/h) (setting: 0.005 µSv/h/CPM)
        # tube:             ?
        # Device Battery Voltage:       10.0 Volt   # had 9V rechargeable (Block Batterie Akku)
        # Device Battery Type Setting:  24          # why?
        #######################################################################
        GMC_memory               = 2**16                        # 65536 seems ok,  used by ori0n
        GMC_SPIRpage             = 2048                         # used by ori0n
        GMC_SPIRbugfix           = False                        # used by ori0n
        GMC_configsize           = 256                          # used by ori0n
        GMC_voltagebytes         = 1                            # used by ori0n
        GMC_endianness           = 'little'                     # used by ori0n
        GMC_Variables            = "CPM1st, CPS1st"             # used by ori0n
        GMC_Bytes                = 2                            # used by ori0n
        GMC_WifiIndex            = None                         # no WiFi
        GMC_baudrate             = 57600                        # used by ori0n


    elif "GMC-300Re 3." in gglobs.GMCDeviceDetected :
        #######################################################################
        # the "GMC-300" delivers the requested page after ANDing with 0fff
        # hence when you request 4k (=1000hex) you get zero
        # therefore use pagesize 2k only
        #######################################################################
        GMC_memory               = 2**16
        GMC_SPIRpage             = 2048
        GMC_SPIRbugfix           = False
        GMC_configsize           = 256
        GMC_voltagebytes         = 1
        GMC_endianness           = 'little'
        GMC_Variables            = "CPM1st, CPS1st"
        GMC_Bytes                = 2
        GMC_WifiIndex            = None
        GMC_baudrate             = 57600


    elif "GMC-300Re 4." in gglobs.GMCDeviceDetected:
        #######################################################################
        # when using a page of 4k, you need the datalength workaround in
        # gcommand, i.e. asking for 1 byte less
        # 'GMC-300Re 4.54' from AZ Jan 2021 has Serial No: F488C39506ABFA
        # when writing config data into the unused portion of the memory, the
        # counter seems to delete the changes after ~1 sec
        #######################################################################
        GMC_memory               = 2**16
        GMC_SPIRpage             = 4096
        GMC_SPIRbugfix           = True
        GMC_configsize           = 256
        GMC_voltagebytes         = 1
        GMC_endianness           = 'little'
        GMC_Variables            = "CPM1st, CPS1st"
        GMC_Bytes                = 2
        GMC_WifiIndex            = None
        GMC_baudrate             = 57600


    elif "GMC-300SRe 1." in gglobs.GMCDeviceDetected:
        #######################################################################
        # new counter "GMC-300SRe 1.03" as of 2023-02-23
        #######################################################################
        GMC_memory               = 2**16
        GMC_SPIRpage             = 4096
        GMC_SPIRbugfix           = True
        GMC_configsize           = 256
        GMC_voltagebytes         = 1
        GMC_endianness           = "little"
        GMC_Variables            = "CPM1st, CPS1st"
        GMC_Bytes                = 2
        GMC_baudrate             = 57600
        GMC_FETenabled           = True
        # GMC_WifiIndex            = 5
        GMC_WifiIndex            = None            # to not show WiFi

    elif "GMC-300" in gglobs.GMCDeviceDetected:
        #######################################################################
        # last resort for GMC-300 anything counters
        #######################################################################
        showUnknownDeviceMsg(gglobs.GMCDeviceDetected)

        GMC_memory               = 2**16
        GMC_SPIRpage             = 2048
        GMC_SPIRbugfix           = True
        GMC_configsize           = 256
        GMC_voltagebytes         = 1
        GMC_endianness           = 'little'
        GMC_Variables            = "CPM1st, CPS1st"
        GMC_Bytes                = 2
        GMC_WifiIndex            = None
        GMC_baudrate             = 57600


    elif "GMC-320Re 3." in gglobs.GMCDeviceDetected:
        #######################################################################
        #
        #######################################################################
        GMC_memory               = 2**20
        GMC_SPIRpage             = 4096
        GMC_SPIRbugfix           = False
        GMC_configsize           = 256
        GMC_voltagebytes         = 1
        GMC_endianness           = 'little'
        GMC_Variables            = "CPM1st, CPS1st"
        GMC_Bytes                = 2
        GMC_WifiIndex            = None  # WiFi is invalid


    elif "GMC-320Re 4." in gglobs.GMCDeviceDetected:
        #######################################################################
        # GMC-320Re 4.19 : kein Fast Estimate Time
        #######################################################################
        GMC_memory               = 2**20
        GMC_SPIRpage             = 4096
        GMC_SPIRbugfix           = True
        GMC_configsize           = 256
        GMC_voltagebytes         = 1
        GMC_endianness           = 'little'
        GMC_Variables            = "CPM1st, CPS1st"
        GMC_Bytes                = 2
        GMC_WifiIndex            = None  # WiFi is invalid


    elif "GMC-320Re 5." in gglobs.GMCDeviceDetected:
        #######################################################################
        # 320v5 device with WiFi
        #######################################################################
        GMC_memory               = 2**20
        GMC_SPIRpage             = 4096
        GMC_SPIRbugfix           = True
        GMC_configsize           = 256
        GMC_voltagebytes         = 1
        GMC_endianness           = 'little'
        GMC_Variables            = "CPM1st, CPS1st"
        GMC_Bytes                = 2
        GMC_WifiIndex            = 2


    elif "GMC-320+V5" in gglobs.GMCDeviceDetected:
        #######################################################################
        # "b'GMC-320+V5\x00RRe 5.73'"  # from Tom Johnson's new GMC-320
        # see: https://sourceforge.net/p/geigerlog/discussion/general/thread/d3c228ff79/
        #######################################################################
        GMC_memory               = 2**20
        GMC_SPIRpage             = 4096
        GMC_SPIRbugfix           = True
        GMC_configsize           = 256
        GMC_voltagebytes         = 1
        GMC_endianness           = 'little'
        GMC_Variables            = "CPM1st, CPS1st"
        GMC_Bytes                = 2
        GMC_WifiIndex            = 2    # 320v5 device with WiFi


    elif "GMC-320SRe 1." in gglobs.GMCDeviceDetected:
        #######################################################################
        # guessing:  new counter "GMC-320SRe 1.03" as of 2023-02-23
        #######################################################################
        GMC_memory               = 2**20
        GMC_SPIRpage             = 4096
        GMC_SPIRbugfix           = True
        GMC_configsize           = 256
        GMC_voltagebytes         = 1
        GMC_endianness           = "little"
        GMC_Variables            = "CPM1st, CPS1st"
        GMC_Bytes                = 2
        GMC_baudrate             = 57600
        GMC_FETenabled           = True
        # GMC_WifiIndex            = 5
        GMC_WifiIndex            = None            # to not show WiFi


    elif "GMC-320" in gglobs.GMCDeviceDetected:
        #######################################################################
        # Last Resort for GMC-320 anything counters
        #######################################################################
        showUnknownDeviceMsg(gglobs.GMCDeviceDetected)

        GMC_memory               = 2**20
        GMC_SPIRpage             = 4096
        GMC_SPIRbugfix           = True
        GMC_configsize           = 256
        GMC_voltagebytes         = 1
        GMC_endianness           = 'little'
        GMC_Variables            = "CPM1st, CPS1st"
        GMC_Bytes                = 2
        GMC_WifiIndex            = None     # avoiding any wifi problems; just in case;
                                            # can be overrun in config

    # OHNE "PLUS" !!!
    elif "GMC-500Re 1." in gglobs.GMCDeviceDetected:
        #######################################################################
        # 500 - OHNE '+'
        # GMC-500Re 1.08 : No '+' but 2 tubes, kein Fast Estimate Time (von user the_mike)
        #######################################################################
        GMC_memory               = 2**20
        GMC_SPIRpage             = 2048   # ist bug jetzt behoben oder auf altem Stand? erstmal auf 2048 bytes
        GMC_SPIRbugfix           = False
        GMC_configsize           = 512
        GMC_voltagebytes         = 5
        GMC_endianness           = 'big'
        GMC_Variables            = "CPM1st, CPS1st, CPM2nd, CPS2nd"
        GMC_Bytes                = 2
        GMC_DualTube             = True
        GMC_WifiIndex            = 3      # 500er, 600er


    # MIT "PLUS" !!!
    elif "GMC-500+Re 1.18" in gglobs.GMCDeviceDetected:
        #######################################################################
        # Yields 4 bytes on all CPx calls!
        # Has a firmware bug: on first call to GETVER gets nothing returned.
        # WORK AROUND: must cycle connection ON->OFF->ON. then ok
        # Has no FET
        #######################################################################
        GMC_memory               = 2**20
        GMC_SPIRpage             = 2048   # ist bug jetzt behoben oder auf altem Stand??? erstmal auf 2048 bytes
        GMC_SPIRbugfix           = False
        GMC_configsize           = 512
        GMC_voltagebytes         = 5
        GMC_endianness           = 'big'
        GMC_Variables            = "CPM1st, CPS1st, CPM2nd, CPS2nd"
        GMC_Bytes                = 4
        GMC_DualTube             = True   # 500+ with 2 tubes
        GMC_WifiIndex            = 3      # 500er, 600er


    # to cover 1.2ff
    elif "GMC-500+Re 1.2" in gglobs.GMCDeviceDetected:
        #######################################################################
        # Yields 4 bytes on all CPx calls!
        # Firmware bug from 'GMC-500+Re 1.18' is corrected
        # Has no FET
        #######################################################################
        GMC_memory               = 2**20
        GMC_SPIRpage             = 4096  # ist bug jetzt behoben oder auf altem Stand???
        GMC_SPIRbugfix           = False
        GMC_configsize           = 512
        GMC_voltagebytes         = 5
        GMC_endianness           = 'big'
        GMC_Variables            = "CPM1st, CPS1st, CPM2nd, CPS2nd"
        GMC_Bytes                = 4
        GMC_DualTube             = True  # 500+ with 2 tubes
        GMC_WifiIndex            = 3     # 500er, 600er


    elif "GMC-500+Re 1." in gglobs.GMCDeviceDetected:
        #######################################################################
        # last resort if not caught in 1.18, 1.21, 1.22
        # assuming no FET
        #######################################################################
        GMC_memory               = 2**20
        GMC_SPIRpage             = 2048   # Workaround erstmal auf 2048 bytes
        GMC_SPIRbugfix           = False
        GMC_configsize           = 512
        GMC_voltagebytes         = 5
        GMC_endianness           = 'big'
        GMC_Variables            = "CPM1st, CPS1st, CPM2nd, CPS2nd"
        GMC_Bytes                = 4
        GMC_DualTube             = True   # 500+ with 2 tubes
        GMC_WifiIndex            = 3      # 500er, 600er


    # to cover 2.40ff
    elif "GMC-500+Re 2.4" in gglobs.GMCDeviceDetected:
        #######################################################################
        # GMC-500+Re 2.40   latest as of 2022-08
        #######################################################################
        # found in: GMC-500+Re 2.40 as reported by Quaxo76, see:
        # http://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=9910, Reply #5
        # Calibration points read out from firmware:
        # Device Calibration Points:        CPM  =   µSv/h   CPM / (µSv/h)      µSv/h/CPM
        # Calibration Point          #1:    100  =   0.650       153.85          0.00650
        # Calibration Point          #2:  30000  = 195.000       153.85          0.00650
        # Calibration Point          #3:   1000  =  46.800        21.37          0.04680
        #
        # timing data:  see gsub_config  @GMC_Device GMC_SPIRpage
        #######################################################################
        GMC_memory               = 2**20
        GMC_SPIRpage             = 4096     # chosen default for now
        GMC_SPIRbugfix           = False
        GMC_configsize           = 512
        GMC_voltagebytes         = 5
        GMC_endianness           = 'big'
        GMC_Variables            = "CPM1st, CPS1st, CPM2nd, CPS2nd"
        GMC_Bytes                = 4
        GMC_DualTube             = True     # 500+ with 2 tubes, 2nd tube wrapped in plastic
        GMC_sensitivity2nd       = 21.4     # unknown tube, wrapped completely in black plastic
        GMC_WifiIndex            = 4
        GMC_FETenabled           = True


    # to cover 2.00ff
    elif "GMC-500+Re 2." in gglobs.GMCDeviceDetected:
        #######################################################################
        # GMC-500+Re 2.28   latest as of 2021-10-20
        #######################################################################
        # original found in: GMC-500+Re 1.2.
        # Calibration points read out from firmware:
        # Calibration Points:     CPM  =  µSv/h   CPM / (µSv/h)   µSv/h / CPM
        # Calibration Point 1:    100  =   0.65       153.8          0.0065
        # Calibration Point 2:  30000  = 195.00       153.8          0.0065
        # Calibration Point 3:     25  =   4.85         5.2          0.1940
        #
        # timing data:  see gsub_config  @GMC_Device GMC_SPIRpage
        #######################################################################
        GMC_memory               = 2**20
        GMC_SPIRpage             = 4096     # chosen default for now
        GMC_SPIRbugfix           = False
        GMC_configsize           = 512
        GMC_voltagebytes         = 5
        GMC_endianness           = 'big'
        GMC_Variables            = "CPM1st, CPS1st, CPM2nd, CPS2nd"
        GMC_Bytes                = 4
        GMC_DualTube             = True   # 500+ with 2 tubes
        GMC_WifiIndex            = 4      # 500+ version 2.24
        GMC_FETenabled           = True


    elif "GMC-500" in gglobs.GMCDeviceDetected:
        #######################################################################
        # last resort for GMC-500 (plus or no plus) anything
        #######################################################################
        showUnknownDeviceMsg(gglobs.GMCDeviceDetected)

        GMC_memory               = 2**20
        GMC_SPIRpage             = 4096
        GMC_SPIRbugfix           = False
        GMC_configsize           = 512
        GMC_voltagebytes         = 5
        GMC_endianness           = 'big'
        GMC_Variables            = "CPM1st, CPS1st, CPM2nd, CPS2nd"
        GMC_Bytes                = 4
        GMC_DualTube             = True   # 500+ with 2 tubes
        GMC_WifiIndex            = 4      # 500+ version 2.24
        GMC_FETenabled           = True


    elif "GMC-510+" in gglobs.GMCDeviceDetected:
        #######################################################################
        # reported by dishemesdr:
        # https://sourceforge.net/p/geigerlog/discussion/general/thread/48ffc25514/
        # Connected Device: GMC-510Re 1.04
        # tube: M4011  (only 1 tube)
        # https://www.gqelectronicsllc.com/support/GMC_Selection_Guide.htm
        # assuming no FET
        #######################################################################
        GMC_memory               = 2**20
        GMC_SPIRpage             = 2048   # ist bug jetzt behoben oder auf altem Stand?; erstmal auf 2048 bytes
        GMC_SPIRbugfix           = False
        GMC_configsize           = 512
        GMC_voltagebytes         = 1      # strange but working
        GMC_endianness           = 'big'
        GMC_Variables            = "CPM1st, CPS1st"
        GMC_Bytes                = 4
        GMC_WifiIndex            = 3      # 500er, 600er


    # this absorbs all 600 calls!!! should have come last
    # # WITHOUT "PLUS"
    # elif "GMC-600" in gglobs.GMCDeviceDetected:
    #     #######################################################################
    #     # sensitivity: using LND's 348, not GQ's 379; see note in ceigerlog.cfg
    #     #######################################################################
    #     GMC_memory               = 2**20
    #     GMC_SPIRpage             = 2048   # ist bug jetzt behoben oder auf altem Stand? erstmal auf 2048 bytes
    #     GMC_SPIRbugfix           = False
    #     GMC_configsize           = 512
    #     GMC_sensitivityDef       = 348    # CPM/(µSv/h)
    #     GMC_sensitivity1st       = 348    # CPM/(µSv/h)
    #     GMC_voltagebytes         = 5
    #     GMC_endianness           = 'big'
    #     GMC_Variables            = "CPM1st, CPS1st"
    #     GMC_Bytes                = 2
    #     GMC_WifiIndex            = 3      # 500er, 600er
    #     GMC_FETenabled           = True   # does it have?


    # WITH "PLUS"
    elif "GMC-600+Re 1." in gglobs.GMCDeviceDetected:
        #######################################################################
        # sensitivity: using LND's 348, not GQ's 379; see note in ceigerlog.cfg
        #######################################################################
        GMC_memory               = 2**20
        GMC_SPIRpage             = 2048   # ist bug jetzt behoben oder auf altem Stand? erstmal auf 2048 bytes
        GMC_SPIRbugfix           = False
        GMC_configsize           = 512
        GMC_sensitivityDef       = 348    # CPM/(µSv/h)
        GMC_sensitivity1st       = 348    # CPM/(µSv/h)
        GMC_voltagebytes         = 5
        GMC_endianness           = 'big'
        GMC_Variables            = "CPM1st, CPS1st"
        GMC_Bytes                = 2
        GMC_WifiIndex            = 3      # 500er, 600er
        GMC_FETenabled           = True


    # WITH "PLUS"
    elif "GMC-600+Re 2." in gglobs.GMCDeviceDetected:
        #######################################################################
        # sensitivity: using LND's 348, not GQ's 379; see note in ceigerlog.cfg
        # firmware version 2.26 as some of the last,
        # see: http://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=9961
        #######################################################################
        GMC_memory               = 2**20
        GMC_SPIRpage             = 4096
        GMC_SPIRbugfix           = False
        GMC_configsize           = 512
        GMC_sensitivityDef       = 348    # CPM/(µSv/h)
        GMC_sensitivity1st       = 348    # CPM/(µSv/h)
        GMC_voltagebytes         = 5
        GMC_endianness           = 'big'
        GMC_Variables            = "CPM1st, CPS1st"
        GMC_Bytes                = 4
        GMC_WifiIndex            = 4      # 600+ version 2.22 is version from Ihab, 2.26 from user "1967"
        GMC_FETenabled           = True


    elif "GMC-600" in gglobs.GMCDeviceDetected:
        #######################################################################
        # last resort for GMC-600 anything
        #######################################################################
        showUnknownDeviceMsg(gglobs.GMCDeviceDetected)

        GMC_memory               = 2**20
        GMC_SPIRpage             = 4096
        GMC_SPIRbugfix           = False
        GMC_configsize           = 512
        GMC_sensitivityDef       = 348    # CPM/(µSv/h)
        GMC_sensitivity1st       = 348    # CPM/(µSv/h)
        GMC_voltagebytes         = 5
        GMC_endianness           = 'big'
        GMC_Variables            = "CPM1st, CPS1st"
        GMC_Bytes                = 4
        GMC_WifiIndex            = 4
        GMC_FETenabled           = True


    else:
        #######################################################################
        # If none of the above match, then this place will be reached.
        # Allows integrating as of now unknown new (or old) devices
        #######################################################################
        showUnknownDeviceMsg(gglobs.GMCDeviceDetected)

        GMC_memory               = 2**20        # 1 MByte
        GMC_SPIRpage             = 2048
        GMC_SPIRbugfix           = False
        GMC_configsize           = 512
        GMC_voltagebytes         = 4            # like in 500 series
        GMC_endianness           = 'big'        # like in 500 series
        GMC_Variables            = "CPM1st, CPS1st"
        GMC_Bytes                = 4            # like in 500 series
        GMC_WifiIndex            = 3            # like older 500 series
        GMC_FETenabled           = False        # what to chose?


    # overwrite any "auto" values with defaults
    if gglobs.GMC_memory        == 'auto':  gglobs.GMC_memory       = GMC_memory
    if gglobs.GMC_SPIRpage      == 'auto':  gglobs.GMC_SPIRpage     = GMC_SPIRpage
    if gglobs.GMC_SPIRbugfix    == 'auto':  gglobs.GMC_SPIRbugfix   = GMC_SPIRbugfix
    if gglobs.GMC_configsize    == 'auto':  gglobs.GMC_configsize   = GMC_configsize
    if gglobs.GMC_voltagebytes  == 'auto':  gglobs.GMC_voltagebytes = GMC_voltagebytes
    if gglobs.GMC_endianness    == 'auto':  gglobs.GMC_endianness   = GMC_endianness
    if gglobs.GMC_Bytes         == 'auto':  gglobs.GMC_Bytes        = GMC_Bytes
    if gglobs.GMC_Variables     == 'auto':  gglobs.GMC_Variables    = GMC_Variables
    if gglobs.GMC_locationBug   == 'auto':  gglobs.GMC_locationBug  = GMC_locationBug
    if gglobs.GMC_WifiIndex     == 'auto':  gglobs.GMC_WifiIndex    = GMC_WifiIndex
    if gglobs.GMC_DualTube      == 'auto':  gglobs.GMC_DualTube     = GMC_DualTube
    if gglobs.GMC_baudrate      == 'auto':  gglobs.GMC_baudrate     = GMC_baudrate
    if gglobs.GMC_FETenabled    == "auto":  gglobs.GMC_FETenabled   = GMC_FETenabled
    if gglobs.GMC_FastEstTime   == "auto":  gglobs.GMC_FastEstTime  = GMC_FastEstTime

    if gglobs.Sensitivity[0]    == 'auto':  gglobs.Sensitivity[0]   = GMC_sensitivityDef
    if gglobs.Sensitivity[1]    == 'auto':  gglobs.Sensitivity[1]   = GMC_sensitivity1st
    if gglobs.Sensitivity[2]    == 'auto':  gglobs.Sensitivity[2]   = GMC_sensitivity2nd

    # GMC_WifiEnabled only when GMC_WifiIndex is not None
    if gglobs.GMC_WifiIndex == None: gglobs.GMC_WifiEnabled  = False
    else:                            gglobs.GMC_WifiEnabled  = True

    # clean up locationBug to avoid crash due to any wrong user entry;
    # on Exception resort to default setting
    try:    ts = gglobs.GMC_locationBug.split(",")
    except: ts =        GMC_locationBug.split(",")
    for i in range(0, len(ts)): ts[i] = ts[i].strip()
    gglobs.GMC_locationBug = ts     # is list like: ['GMC-500+Re 1.18', 'GMC-500+Re 1.21']

    dprint("GMC_baudrate     : ", gglobs.GMC_baudrate)
    dprint("GMC_DualTube     : ", gglobs.GMC_DualTube)
    dprint("GMC_Bytes        : ", gglobs.GMC_Bytes)
    dprint("GMC_configsize   : ", gglobs.GMC_configsize)
    dprint("GMC_memory       : ", gglobs.GMC_memory)
    dprint("GMC_SPIRpage     : ", gglobs.GMC_SPIRpage)
    dprint("GMC_SPIRbugfix   : ", gglobs.GMC_SPIRbugfix)
    dprint("GMC_voltagebytes : ", gglobs.GMC_voltagebytes)
    dprint("GMC_endianness   : ", gglobs.GMC_endianness)
    dprint("GMC_locationBug  : ", gglobs.GMC_locationBug)
    dprint("GMC_WifiIndex    : ", gglobs.GMC_WifiIndex)
    dprint("GMC_WifiEnabled  : ", gglobs.GMC_WifiEnabled)
    dprint("GMC_FETenabled   : ", gglobs.GMC_FETenabled)
    dprint("GMC_FastEstTime  : ", gglobs.GMC_FastEstTime)
    dprint("GMC_Variables    : ", gglobs.GMC_Variables)

    dprint("Sensitivity[0]   : ", gglobs.Sensitivity[0])
    dprint("Sensitivity[1]   : ", gglobs.Sensitivity[1])
    dprint("Sensitivity[2]   : ", gglobs.Sensitivity[2])

    setIndent(0)

#### end getGMC_DeviceProperties ##############################################
###############################################################################
###############################################################################

def getResponseAT(command):
    """communication with the ESP8266 chip in the counter"""

    fncname = "getResponseAT: "

    print()
    dprint(fncname + "for command: {}".format(command))
    setIndent(1)

    rec = gglobs.GMCser.write(command)  # rec = no of bytes written
    # print("bytes written: ", rec, "for command:", command)

    t0 = time.time()
    print("waiting for response ", end="", flush=True)
    while gglobs.GMCser.in_waiting == 0:
        print(".", end="", flush=True)
        time.sleep(0.2)
    print(" received after {:0.1f} sec".format(time.time() - t0))    #  ca 5 sec

    rec = b''
    t0 = time.time()
    while gglobs.GMCser.in_waiting > 0 or time.time() - t0 < 2:
        bw = gglobs.GMCser.in_waiting
        if bw > 0:
            # print("reading {:3d} bytes".format(bw), end="  ")
            newrec = gglobs.GMCser.read(bw)
            # print(newrec)
            rec += newrec
        else:
            print(".", end="", flush=True)
        time.sleep(0.2)
    print("\nfinal rec: ({} bytes) {}".format(len(rec), rec))

    setIndent(0)

