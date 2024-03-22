#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
GLWifiServer:
                A Python webserver running as a 'GeigerLog WiFiServer Device'
                enabling various external devices to send data by WiFi.
                Supported hardware devices:
                    GMC counter                 via GMC (by USB connection)
                    I2C Sensors                 via I2C (by GPIO)
                        Supported I2C Sensors:
                        - LM75B     temperature
                        - BH1750    visible light intensity in Lux
                        - GDK101    Geiger count rate
                    Pulse counter               via Pulse (by GPIO)
                        e.g. CAJOE counter
                To use the devices and sensors they must be started as option
                on the command line and may need configuration in the CUSTOMIZE
                section. They can all be run simultaneously.

Requires Python 3.7 or later.

Start with:     path/to/GLWifiServer.py <one or all of: GMC, I2C, Pulse>
   Example:     To start GMC and I2C but not Pulse: GLWifiServer.py GMC I2C
Stop  with:     CTRL-C
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


###############################################################################
####################       CUSTOMIZE HERE        ##############################
###############################################################################
#
# Lines beginning with '#' are comments and will be ignored
#
## Port Number on which this WiFiServer will listen
#  NOTE: make sure, nothing else is using the port, otherwise connection fails
#        Use nmap to scan; available for Lin, Win, Mac, Raspi: https://nmap.org/
#        command is:   nmap  <IP of computer running GLWifiServer> -p1-65535
#              like:   nmap 10.0.0.100 -p1-65535
#
#  Select from:  1024 ... 65535
cWiFiServerPort = 4000

## Display name for this WiFiServer
cDisplayName    = "GeigerLog WiFiServer"

## Filenames of log files
# the log files will be saved into the directory from where you started GLWifiServer
cDataLogFile    = "GLWiFiServer"            # this saves the data as a CSV file with extension ".datalog"
# cDataLogFile  = ""                        # if set to empty this log file will NOT be written

cProgLogFile    = "GLWiFiServer"            # this saves the program's output to file
# cProgLogFile  = ""                        # if set to empty this log file will NOT be written
                                            # 2 files will be generated with different extensions:
                                            # - extension: '.startlog' : output during the startup phase
                                            # -            '.runlog'   : output during the run phase
                                            #                            this file will be overwritten when a certain size is reached

##
## GMC counter specific settings
##
#  The GMC counter should work properly with port, baudrate settings on 'auto'.
#  If it doesn't, please report as bug and try defining the settings manually.
cGMCport      = "auto"                      # on Raspi:    likely port is '/dev/ttyUSB0'
                                            # on Linux:    likely port is '/dev/ttyUSB0'
                                            # on Windows:  likely port is 'COM3'
cGMCbaudrate  = "auto"                      # baudrate;    for the GMC 300 series:        57600
                                            #              for GMC 320, 5XX, 6XX series: 115200

cGMCvariables = "auto"                      # select one or all from "CPM, CPS, CPM1st, CPS1st, CPM2nd, CPS2nd"
                                            # "auto" defaults to "CPM1st, CPS1st, CPM2nd, CPS2nd"
cGMCvariables = "CPM1st"                    # custom selection (overrides default "auto")


##
## I2C Sensor specific settings
##
# Supported I2C Sensors:
#   - LM75B     temperature in °C
#   - BH1750    visible light intensity in Lux
#   - GDK101    Geiger count rate in CPM
#
cI2Cusage_LM75B     = True                  # use (True) or not use (False) this sensor
cI2Cusage_BH1750    = True                  # use (True) or not use (False) this sensor
cI2Cusage_GDK101    = True                  # use (True) or not use (False) this sensor

cI2Caddress_LM75B   = 0x48                  # hardware options: 0x48 | 0x49 | 0x4A | 0x4B | 0x4C | 0x4D | 0x4E | 0x4F
cI2Caddress_BH1750  = 0x23                  # hardware options: 0x23 | 0x5C
cI2Caddress_GDK101  = 0x18                  # hardware options: 0x18 | 0x19 | 0x1A | 0x1B

# configure sensors: {"<GeigerLog target variable>" : <avg period in sec 1 ... 60> [, ...] }
#   - <GeigerLog target variable>   : Can be any of GeigerLog's 12 variables:
#                                     CPM,CPS,CPM1st,CPS1st,CPM2nd,CPS2nd,CPM3rd,CPS3rd, Temp,Press,Humid,Xtra
#   - <avg period in sec 1 ... 60>  : The returned data will have been averaged over the given period in seconds
#                                     On "1" the very last measured single data will be returned
#   - Can be repeated to use multiple averages, like: cI2Cvars_LM75B = {"Temp" : 60, "Press" : 20, "Humid" : 5}
#
#                      VarName  Avg
cI2Cvars_LM75B      = {"Temp" :  60}        # at least 10 sec avg needed; 60 is better
cI2Cvars_BH1750     = {"Xtra" :  10}        # 5 sec avg seems to be sufficient
cI2Cvars_GDK101     = {"CPM"  :   0}        # any target variable will get same value; avg will be ignored


##
## Pulse specific settings
##
cPulseCountPin      = 17                    # the GPIO pin in BCM mode to be used for pulse counting
                                            # allowed: 5 ... 26;   VERIFY NO CONFLICTING OTHER USAGE OF THIS PIN !!!
                                            # BCM-Pin=17 is on BOARD-Pin=11
cPulseVariables     = "auto"                # select one or all from "CPM,CPS,CPM1st,CPS1st,CPM2nd,CPS2nd,CPM3rd,CPS3rd",
                                            # but no more than one CPM* and one CPS* are meaningful, because all
                                            # CPM* and CPS*, resp., will be the same!
                                            # i.e.: CPM = CPM1st = CPM2nd = CPM3rd and CPS = CPS1st = CPS2nd = CPS3rd
                                            # "auto" defaults to "CPM, CPS"
cPulseVariables     = "CPM3rd, CPS3rd"      # custom selection (overrides default "auto")


###############################################################################
####################   END of CUSTOMIZATION   #################################
################## NO USER CHANGES BELOW THIS LINE ! ##########################
###############################################################################

# NOTE: Using a Headless Raspi (no monitor, no keyboard, no mouse)
# Recommended: use 'no-vnc' connection to Raspi
# see: https://forums.raspberrypi.com/viewtopic.php?t=333132
# see post on dumping mutter: https://forums.raspberrypi.com/viewtopic.php?t=333132#p2040420
# Remote call Raspi from browser: http://raspberrypi.local/
# don't forget to configure Port under: Extended -> WebSocket to 5900 (is 80 by default)

# NOTE: sound output from Raspi:
# http://cool-web.de/raspberry/raspberry-pi-lautsprecher-sirene.htm

# NOTE: PWM on Raspi
# https://www.raspberry-pi-geek.de/ausgaben/rpg/2020/04/grundlagen-der-pulsweitenmodulation/

# NOTE: Using Raspi's 'i2cdetect' in terminal:
# scan I2c: i2cdetect -y 1
# list I2c: i2cdetect -l

# NOTE: it looks like the GDK101 does need a 5V supply! At 3.3V it appears to
# be working, but count rate comes out as way too high!


import sys, os, io, time, datetime              # basic modules
import traceback                                # more details on crashes
import platform                                 # to find OS
import socket                                   # finding IP Adress
import http.server                              # web server
import urllib.parse                             # to parse queries
import threading                                # higher-level threading interfaces
import random                                   # to fudge some numbers
import math                                     # to calculate SQRT

from collections import deque                   # becomes fixed-size buffer


__author__              = "ullix"
__copyright__           = "Copyright 2016, 2017, 2018, 2019, 2020, 2021, 2022"
__credits__             = [""]
__license__             = "GPL3"
__version__             = "3.4"                       # of this script
__script__              = os.path.basename(__file__)  # exclude the path, get just the filename


#
# Variables which MUST NOT be changed in code!
#
# colors for Linux terminal
TDEFAULT                = '\033[0m'             # default, i.e greyish
TYELLOW                 = '\033[93m'            # yellow
BOLDRED                 = '\033[91;1m'          # bold red
BOLDGREEN               = '\033[92;1m'          # bold green
BOLDCYAN                = '\033[96;1m'          # bold cyan
if "WINDOWS" in platform.platform().upper():    # Windows does not support terminal colors
    TDEFAULT            = ""
    TYELLOW             = ""
    BOLDRED             = ""
    BOLDGREEN           = ""
    BOLDCYAN            = ""

# Generics and Admin
NAN                     = float('nan')          # 'not-a-number'; used as 'missing value'
debug                   = True                  # print output as debug
verbose                 = True                  # print output as verbose
tracebackFlag           = False                 # if true then print traceback info on exception

# GeigerLog's 12 vars
GLVarNames              = ['CPM', 'CPS', 'CPM1st', 'CPS1st', 'CPM2nd', 'CPS2nd', 'CPM3rd', 'CPS3rd',
                           'Temp', 'Press', 'Humid', 'Xtra']

#
# All Python variables handled as GLOBAL in all functions
#
class globs():

    WiFiServerPort          = cWiFiServerPort       # allowed from:  1024 ... 65535 (incl.)
    DisplayName             = cDisplayName          # display name for this WiFiServer

    # log files
    DataLogFile             = cDataLogFile + ".datalog"     # saves the data as a CSV file
    DataLogFileWOK          = True                          # WOK: Writing OK; no further writing on False
    DataLogFileMax          = 1E7                           # max size of DataLogFile in bytes
    DataLogFileMaxMsg       = "DataLogFile has reached maximum size of {:3,.0f} bytes - No further data will be written\n".format(DataLogFileMax)

    ProgLogFileStart        = cProgLogFile + ".startlog"    # saves the program's output for the start phase
    ProgLogFileStartWOK     = True                          # WOK: Writing OK; no further writing on False
    ProgLogFileStartMax     = 1E4                           # max size of ProgLogFileStart in bytes
    ProgLogFileStartMaxMsg  = "Logfile has reached maximum size of {:3,.0f} bytes - Next data will be written to Logfile 'Run'\n".format(ProgLogFileStartMax)

    ProgLogFileRun          = cProgLogFile + ".runlog"      # saves the program's output for the run phase
    ProgLogFileRunWOK       = False                         # WOK: Writing OK; no further writing on False
    ProgLogFileRunMax       = 1E5                           # max size of ProgLogFileRun in bytes
    ProgLogFileRunMaxMsg    = "ProgLogFileRun has reached maximum size of {:3,.0f} bytes - Resetting Log\n".format(ProgLogFileRunMax)

    # printing
    PrintIndent             = ""                    # indentation of log msg
    PrintCounter            = 0                     # the count of dprint, vprint, xdprint commands

    # hardware
    computer                = None                  # becomes "Raspi ..." or "Unknown (Not a Raspi Computer)"
    isRaspberryPi           = False                 # to be set in main()
    hardware                = []                    # compare with hardwareChoice; set in main
    hardwareChoice          = ["GMC","I2C","PULSE"] # supported devices

    # WiFi Server
    WiFiIndex               = 0                     # number of WiFi calls
    WiFigetmsg              = ""                    # web server msg
    WiFiColor               = TDEFAULT              # used also as flag for color printout in Linux terminal
    WiFiServer              = None                  # the HTTP Web server
    WiFiServerThread        = None                  # thread handle
    WiFiServerThreadStop    = None                  # flag to stop thread

    # GMC
    GMCinit                 = False                 # true if initialized
    GMCser                  = None                  # handle
    GMCcounterversion       = "Undefined"           # becomes like: 'GMC-300Re 4.54'
    GMCtimeout              = "auto"                # timeout in sec for the serial port; default is 3 sec
    GMCbytes                = 0                     # 2 or 4 bytes returned on CPM*/CPS* calls; set in init
    GMCvarsAll              = GLVarNames[0:6]       # only the first 6 vars can be used for GMC counter
    GMCport                 = "auto"                # on Raspi:    likely port is '/dev/ttyUSB0'
                                                    # on Linux:    likely port is '/dev/ttyUSB0'
                                                    # on Windows:  likely port is 'COM3'
    GMCbaudrate             = "auto"                # baudrate;    for the GMC 300 series: 57600
                                                    #              for GMC 320, 5XX, 6XX series: 115200
    GMCvariables            = []                    # one or all from ['CPM', 'CPS', 'CPM1st', 'CPS1st', 'CPM2nd', 'CPS2nd']
                                                    # "auto" defaults to ['CPM1st', 'CPS1st', 'CPM2nd', 'CPS2nd']

    # I2C
    I2Cinit                 = False                 # true if initialized
    I2ConRaspi              = False                 # Flag to signal I2C running on Raspi (True) or Simulation (False)
    I2Chandle               = None                  # handle
    I2Csensor               = ""                    # will be set to e.g. LM75B, BH1750, GDK101
    I2CstoreLux             = deque([], 60)         # queue for max of 60 values of Light
    I2CstoreTemp            = deque([], 60)         # queue for max of 60 values of Temperature

    # Pulse
    PulseInit               = False                 # true if initialized
    PulseOnRaspi            = False                 # Flag to signal Pulse running on Raspi (True) or Simulation (False)
    PulseStore              = deque([], 60)         # empty queue for max of 60 values for last 60 sec of CPS
    PulseCount              = 0                     # holds counts within 1 sec period
    PulseCountTotal         = 0                     # sum of all counts since start or reset
    PulseCountStart         = time.time()           # time of start or reset
    PulseVarsAll            = GLVarNames[0:8]       # only the first 8 CP* vars can be used for Pulse counter
    PulseCountPin           = 17                    # the GPIO pulse counting pin in BCM mode used for counting;
                                                    # allowed: 5 ... 26;   VERIFY NO CONFLICTING OTHER USAGE ON THIS PIN !!!
                                                    # BCM pin=17 is on BOARD pin=11
    PulseVariables          = []                    # one or all from ['CPM', 'CPS', 'CPM1st', 'CPS1st', 'CPM2nd', 'CPS2nd', 'CPM3rd', 'CPS3rd']
                                                    # but note that all CPM* and CPS*, resp., will be the same!
                                                    # i.e.: CPM = CPM1st = CPM2nd = CPM3rd and CPS = CPS1st = CPS2nd = CPS3rd
                                                    # "auto" defaults to ['CPM', 'CPS']

    # PWM
    # to use Raspi PWM output as a fake source for Pulse counting,
    # connect BOARD pin 33 (PWM output) with BOARD pin 11 (Pulse counting input)
    PWMHandle               = None                  # the handle for the PWM settings
    PWMPin                  = 13                    # the GPIO pin in BCM mode used for generating PWM signal
                                                    # BCM pin=13 is on BOARD pin=33
    PWMDutyCycle            = 10                    # [%]  Duty cycle 0 ... 100 %
    PWMFreq                 = 10                    # [Hz] must be > 1.0! start with 10 Hz -> CPS=10 -> CPM=600


##### pre-main() ACTIONS ###################################
# randomness
random.seed(66666)                                  # seed with a develish sequence

# instantiate globals
g = globs()                                         # activate all the "global" variables



def stime():
    """Return current time as YYYY-MM-DD HH:MM:SS"""

    return longstime()[:-4]


def longstime():
    """Return current time as YYYY-MM-DD HH:MM:SS.mmm, (mmm = millisec)"""

    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] # ms resolution


def setIndent(arg):
    """increases or decreased the indent of prints"""

    if arg > 0:  g.PrintIndent += "   "
    else:        g.PrintIndent  = g.PrintIndent[:-3]


def commonPrint(ptype, *args):
    """Printing and saving
    ptype : DEBUG, VERBOSE, ERROR, ALERT
    args  : anything to be printed and saved to file
    return: nothing
    """

    g.PrintCounter += 1

    tag = ""
    for arg in args: tag += str(arg)

    if tag > "":
        tag = "{:23s} {:7s}: {:.>6d} ".format(longstime(), ptype, g.PrintCounter) + g.PrintIndent + tag
        if   ptype == "ERROR":    print(TYELLOW   + tag + TDEFAULT)
        elif ptype == "ALERT":    print(BOLDRED   + tag + TDEFAULT)
        elif ptype == "OK":       print(BOLDGREEN + tag + TDEFAULT)
        elif ptype == "TECH":     print(BOLDCYAN  + tag + TDEFAULT)
        else:                     print(tag)
    else:
        print("")

    appendProgLogFile(tag + "\n")


def dprint(*args):
    """Print args as single line"""

    if debug:   commonPrint("DEBUG", *args)


def vprint(*args):
    """Print args as single line"""

    if verbose: commonPrint("VERBOSE", *args)


def edprint(*args):
    """Print args as single line in yellow"""

    if debug:   commonPrint("ERROR", *args)


def rdprint(*args):
    """Print args as single line in red"""

    if debug:   commonPrint("ALERT", *args)


def gdprint(*args):
    """Print args as single line in green"""

    if debug:   commonPrint("OK", *args)


def cdprint(*args):
    """Print args as single line in cyan"""

    if debug:   commonPrint("TECH", *args)


def exceptPrint(e, srcinfo):
    """Print exception details (errmessage, file, line no)"""

    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname                     = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]    # which file?

    edprint("EXCEPTION: {} ({}) in file: {} in line: {}".format(srcinfo, e, fname, exc_tb.tb_lineno))
    if tracebackFlag: edprint(traceback.format_exc())


def clamp(value, smallest, largest):
    """return value between smallest, largest, both inclusive;
    round to interger value, return as float"""

    return round(max(smallest, min(value, largest)), 0)


def getMyIP():
    """get the IP of the computer currently running this program"""

    st = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        st.connect(('10.255.255.255', 1))
        IP = st.getsockname()[0]
    except Exception as e:
        IP = '127.0.0.1'
        srcinfo = "Bad socket connect, IP:" + IP
        exceptPrint(fncname + str(e), srcinfo)
    finally:
        st.close()

    return IP


def CheckRaspberryPi():
    """check if it is a Raspberry Pi computer"""
    # my Raspi: Raspberry Pi 4 Model B Rev 1.1
    # CAREFUL:  'model' has a 'C' string - ends with 0x00 !!!

    fncname = "CheckRaspberryPi: "

    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
            compmodel = m.read().replace("\x00", "")
    except Exception as e:
        # exceptPrint(e, fncname)
        compmodel = ""

    if 'raspberry pi' in compmodel.lower():
        g.isRaspberryPi = True
        g.computer      = compmodel
    else:
        g.isRaspberryPi = False
        g.computer      = "Unknown (Not a Raspi Computer)"


##
## WiFiServer
##
def initWiFiServer():
    """Initialize WiFiServer"""

    fncname = "initWiFiServer: "

    # check customization of WiFiServerPort
    if 1024 <= int(cWiFiServerPort) <= 65535:
        g.WiFiServerPort = cWiFiServerPort
    else:
        edprint("ERROR: WiFiServerPort {} is not allowed. Valid range is: 1024 ... 65535 (inclusive)".format(cWiFiServerPort))
        return (False, "ERROR")

    # use IP as detected
    WiFiServerIP = getMyIP()

    # create the web server
    try:
        # 'ThreadingHTTPServer': New in version Py 3.7. Not compatible with 3.6
        # non-threading may have been cause for crashing on double requests!
        # g.WiFiServer = http.server.HTTPServer((WiFiServerIP, g.WiFiServerPort), MyServer)
        g.WiFiServer = http.server.ThreadingHTTPServer((WiFiServerIP, g.WiFiServerPort), MyServer)
        g.WiFiServer.timeout = 1
        tmsg = (True, "Ok, listening at: http://{}:{}".format(WiFiServerIP, g.WiFiServerPort))

    except OSError as e:
        exceptPrint(e, "")
        msg = "WiFiServer could not be started, because "
        if e.errno == 98:   tmsg = (False, msg + "Port number {} is already in use".format(g.WiFiServerPort))
        else:               tmsg = (False, msg + "of OS.Error: {}".format(e.errno))

    except Exception as e:
        tmsg = (False, "Unexpected Failure - WiFiServer could not be started")
        exceptPrint(e, tmsg)

    # make thread only on successful creation of WiFiServer
    if tmsg[0]:
        g.WiFiServerThreadStop        = False
        g.WiFiServerThread            = threading.Thread(target = WiFiServerThreadTarget)
        g.WiFiServerThread.daemon     = True   # must come before start(): makes threads stop on exit!
        g.WiFiServerThread.start()

    return tmsg


def WiFiServerThreadTarget():
    """Thread constantly triggers web readings"""

    fncname = "WiFiServerThreadTarget: "

    while not g.WiFiServerThreadStop:
        g.WiFiServer.handle_request()
        # time.sleep(0.01)
        time.sleep(0.05)


def terminateWiFiServer():
    """stop and close Web server"""

    fncname = "terminateWiFiServer: "

    g.WiFiServerThreadStop = True
    g.WiFiServer.server_close()

    return "Terminate WiFiServer: Done"


class MyHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        """replacing the log_message function"""

        # output:  ... LogMsg: GET /?ID=GeigerLog&M=10&S=11&M1=12&S1=13&M2=14&S2=15&M3=16&S3=17&T=18&P=19&H=20&X=21 HTTP/1.1, 302, -
        strarg = ", ".join(args)    # count(args) = 3 (except on errors)

        if g.WiFiColor == TYELLOW:  edprint("WiFiServer LogMsg: ", strarg, g.WiFigetmsg)


class MyServer(MyHandler):

    def do_GET(self):
        """'do_GET' overwrites class function"""

        fncname  = "WiFiServer do_GET: "

        g.WiFigetmsg = ""
        g.WiFiColor  = TDEFAULT

        # dprint(fncname + "self.path: ", self.path)

        # if thread stopped this is the last dummy call to close the server
        if g.WiFiServerThreadStop:
            self.send_response(200)
            self.end_headers()
            dprint("WiFiServerThreadStop is True") # never reached?
            return


        # lastdata
        if   self.path.startswith("/GL/lastdata"):
            # CSV values of all 12 vars; like:
            # 6.500, 994.786, 997.429, 907.214, 983.857, 892.071, 154,  154,  2.08,  154, 0.9, 6.0
            bdata       = getDataCSV(1)  # for 1 sec = 1 single record

            myheader    = "Content-type", "text/plain; charset=utf-8"
            mybytes     = bdata
            myresponse  = 200

        # lastavg
        elif self.path.startswith("/GL/lastavg"):
            # like lastdata, except for DeltaT option
            DeltaT      = 1     # default
            query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if "chunk" in query_components: DeltaT = int(query_components["chunk"] [0])
            DeltaTsec   = DeltaT * 60                        # DeltaT is in minutes; but need sec
            DeltaTsec   = DeltaTsec if DeltaTsec > 0 else 1  # at least == 1
            # print("DeltaT, DeltaTsec", DeltaT, DeltaTsec)
            bdata       = getDataCSV(DeltaTsec)

            myheader    = "Content-type", "text/plain; charset=utf-8"
            mybytes     = bdata
            myresponse  = 200

        # id
        elif self.path == "/GL/id":
            answer      = "{} {}".format(cDisplayName, __version__)
            bdata       = bytes(answer, "UTF-8")

            myheader    = "Content-type", "text/plain; charset=utf-8"
            mybytes     = bdata
            myresponse  = 200

        # reset
        elif self.path == "/GL/reset":
            answer      = resetDevices("All")
            bdata       = bytes(answer, "UTF-8")

            myheader    = "Content-type", "text/plain; charset=utf-8"
            mybytes     = bdata
            myresponse  = 200


        # favicon
        elif "favicon.ico" in self.path:
            bdata       = b""                           # empty; no icon

            myheader    = "Content-type", "image/png"   # png image
            mybytes     = bdata
            myresponse  = 200

        # root
        elif self.path == '/GL/':
            answer      = "<!DOCTYPE html><style>html{text-align:center;</style><h1>Welcome to<br>WiFiServer</h1>"
            answer     += "<b>Supported Requests:</b><br>/id<br>/lastdata<br>/lastavg<br>"
            bdata       = bytes(answer, "UTF-8")

            myheader    = 'Content-Type', "text/html"  # HTML
            mybytes     = bdata
            myresponse  = 200

        # page not found (404 error)
        else:
            # get calling system from self.headers["User-Agent"]:
            #   self.headers["User-Agent"] from Python:      BaseHTTP/0.6 Python/3.9.4
            #   self.headers["User-Agent"] from GMC counter: None
            #   self.headers["User-Agent"] from Firefox:     Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0
            #   self.headers["User-Agent"] from Chromium:    Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36
            # dprint("self.headers['User-Agent']: ", self.headers["User-Agent"])

            g.WiFiColor    = TYELLOW
            if self.headers["User-Agent"] is None or "Python" in self.headers["User-Agent"]:
                answer   = "404 Page not found"
                myheader = 'Content-Type', "text/plain" # PLAIN

            else:
                answer   = "<!DOCTYPE html><style>html{text-align:center;}</style><h1>404 Page not found</h1>"
                myheader = 'Content-Type', "text/html"  # HTML

            g.WiFigetmsg = "{} | {}{} {}".format(g.WiFiColor, fncname, answer, TDEFAULT)

            mybytes    = bytes(answer, "UTF-8")
            myresponse = 404

        self.send_response(myresponse)
        self.send_header(*myheader)
        self.end_headers()

        try:
            self.wfile.write(mybytes)
        except Exception as e:
            exceptPrint(e, fncname + "Writing bytes to net")


def getDataCSV(avg):
    """
    get the data as byte sequence in the form needed by GeigerLog
    parameter:  avg: get the data as average over the last avg seconds; avg > 0
    return:     data as a CSV list (as bytes): M, S, M1, S1, M2, S2, M3, S3, T, P, H, X (must have 11 commas)
      like:                                  b'1733.0,36.0,1884.7,30.2,34.0,34.2,34.0,0.0,34.0,32.3,32.0,2.0'
    """
    # NOTE: parameter avg is not used

    start    = time.time()

    fncname  = "getDataCSV: "

    dprint() # empty line

    # Merging the Dicts:
    # -  In Python 3.9.0 or greater: z = x | y
    # -  In Python 3.5 or greater:   z = {**x, **y}
    rawDict = {}
    if g.GMCinit:   rawDict = {**rawDict, **getDataGMC()}
    if g.I2Cinit:   rawDict = {**rawDict, **getDataI2C()}
    if g.PulseInit: rawDict = {**rawDict, **getDataPulse()}

    # sort into proper GL variable order
    DataDict = {}
    for vname in GLVarNames:
        if vname in rawDict:  DataDict.update({vname : rawDict[vname]})

    # create the CSV record string to send to web
    WebRecord = ""
    for vname in GLVarNames:
        if vname in DataDict:  value = DataDict[vname]
        else:                  value = NAN
        WebRecord += "{:8.7g}, ".format(value)
    WebRecord = WebRecord[:-2]                  # remove final ", "

    dur = 1000 * (time.time() - start) # ms

    g.WiFiIndex += 1
    appendDataLogFile("{:7d}, {:23s}, {}, {:8.3f}\n".format(g.WiFiIndex, longstime(), WebRecord, dur))

    # prints like: 'getDataCSV:   {'Temp': 20.9, 'Xtra': 471, 'CPM': 618.0, 'CPS': 12}  dur: 0.136 ms'
    dprint(fncname + "  {}  dur:{:0.3f} ms".format(DataDict, dur))

    WebRecord = WebRecord.replace(" ", "")      # remove blanks for web

    # prints like: 'getDataCSV: WebRecord: 105,nan,112,nan,nan,nan,nan,nan,51,51.125,nan,nan'
    vprint(fncname + "  WebRecord: ", WebRecord)

    return bytes(WebRecord, "UTF-8")


############################################################################
# Hardware functions for GMC devices  ######################################
############################################################################

def initGMC():
    """Initialize GMC"""

    # needed for GMC: module pyserial
    try:
        import serial                           # communication with serial port
        import serial.tools.list_ports          # allows listing of serial ports
    except ImportError as ie:
        msg  = "The module 'pyserial' was not found, but is required for using a GMC counter."
        exceptPrint(ie, msg)
        msg += "\nInstall with 'python -m pip install -U pyserial'."
        return msg
    except Exception as e:
        msg = "Unexpected Failure importing 'serial'. Cannot use GMC counter. Exiting."
        exceptPrint(e, msg)
        return msg + str(e)

    fncname = "initGMC: "
    dprint(fncname)
    setIndent(1)

    if cGMCport         == "auto" : g.GMCport      = "auto"
    else:                           g.GMCport      = cGMCport

    if cGMCbaudrate     == "auto" : g.GMCbaudrate  = "auto"
    else:                           g.GMCbaudrate  = cGMCbaudrate

    if g.GMCtimeout     == "auto":  g.GMCtimeout   = 3

    if cGMCvariables    == "auto" : pv = "CPM1st, CPS1st, CPM2nd, CPS2nd"
    else:                           pv = cGMCvariables
    for vname in pv.split(","):
        pvar = vname.strip()
        if pvar in g.GMCvarsAll:
            g.GMCvariables.append(pvar)
        else:
            edprint("ERROR: '{}' is not a possible variable for GMC.".format(pvar))
            edprint("Allowed is: {}".format(g.GMCvarsAll))
            setIndent(0)
            return "ERROR"


    # finding USB-to-Serial port for GMC
    if g.GMCport != "auto":
        # GMCport was set manually; do not change
        pass

    else:
        # GMCport is "auto". Search for ports on this system
        dprint("Searching for USB-to-Serial Ports - found these:")
        GMCports = serial.tools.list_ports.comports()
        if len(GMCports) == 0:
            dprint("No USB-to-Serial Ports found on this system - Cannot run without one. Exiting.")
            setIndent(0)
            return "Failure"

        # check for a port with chip CH340
        foundport = False
        setIndent(1)
        for port in GMCports :
            dprint (str(port))
            if  port.vid == 0x1a86 and port.pid == 0x7523:
                foundport = True
                g.GMCport = port.device
                break
        setIndent(0)
        if not foundport:
            dprint("No USB-to-Serial Ports for GMC counters found on this system - Cannot run without one. Exiting.")
            setIndent(0)
            return "Failure"
    # dprint("   Selected Port: " + g.GMCport)

    # setting baudrate
    if g.GMCbaudrate != "auto":
        # g.GMCbaudrate was set manually; do not change
        pass
    else:
        # GMCbaudrate is "auto". Find the baudrate; begin at higest
        testbr = (115200, 57600)
        for tbr in testbr:
            try:
                testser = serial.Serial(g.GMCport, tbr, timeout=3)
                # print("testser: ", testser)
                bwrt = testser.write(b'<GETVER>>')
                trec = testser.read(14) # may leave bytes in the pipeline, if GETVER has
                                        # more than 14 bytes as may happen in newer counters
                while True:
                    cnt = testser.in_waiting
                    if cnt == 0: break
                    trec += testser.read(cnt)
                    time.sleep(0.1)

                testser.close()

                if trec.startswith(b"GMC"):
                    g.GMCbaudrate = tbr
                    # dprint("Baudrate: Success with {}".format(g.GMCbaudrate))
                    g.GMCcounterversion = trec.decode("UTF-8")
                    break

            except Exception as e:
                exceptPrint(e, fncname + "ERROR: Serial communication error on finding baudrate")
                baudrate = None
                break

    # dprint("   Selected Baudrate: {}".format(g.GMCbaudrate))
    if g.GMCbaudrate == "auto":
        dprint("Could not establish communication with a counter. Is it connected? Will exit.")
        setIndent(0)
        return "Failure"

    # open the serial port with selected settings
    try:
        g.GMCser  = serial.Serial(g.GMCport, g.GMCbaudrate, timeout=g.GMCtimeout)
    except Exception as e:
        exceptPrint(e, fncname + "FAILURE connecting to GMC counter. Cannot continue.")
        return "Failure"

    # set GMCbytes
    if   "GMC-3"         in g.GMCcounterversion:   g.GMCbytes  = 2    # all 3XX
    elif "GMC-500Re 1."  in g.GMCcounterversion:   g.GMCbytes  = 2    # perhaps Mike is only user
    elif "GMC-5"         in g.GMCcounterversion:   g.GMCbytes  = 4    # all 500+ and 510
    elif "GMC-6"         in g.GMCcounterversion:   g.GMCbytes  = 4    # all 600
    else:                                          g.GMCbytes  = 4    # everything else

    # print settings
    dprint("GMC Settings:")
    dprint("   {:24s} : {}".format("GMC Counter Version"      , g.GMCcounterversion))
    dprint("   {:24s} : {}".format("GMC Serial Port"          , g.GMCport))
    dprint("   {:24s} : {}".format("GMC Serial Baudrate"      , g.GMCbaudrate))
    dprint("   {:24s} : {}".format("GMC Serial Timeout (sec)" , g.GMCtimeout))
    dprint("   {:24s} : {}".format("GMC Counter Byte Counts"  , g.GMCbytes))
    dprint("   {:24s} : {}".format("GMC Variables"            , g.GMCvariables))

    g.GMCinit = True

    setIndent(0)
    return "Ok"


def terminateGMC():
    """shuts down the counter"""

    fncname = "terminateGMC: "

    if g.GMCser is not None:
        try:
            g.GMCser.close()
        except Exception as e:
            msg = "Unexpected Failure closing GMC Serial connection"
            exceptPrint(e, msg)
    g.GMCser = None

    return "Terminate GMC: Done"


def getDataGMC():
    """get the data from a GMC Geiger counter"""

    ## local functions ####################################
    def getGMCCounts(vname):
        """get values for the variable vname"""

        if   vname == "CPM"   : value = getCPM()
        elif vname == "CPS"   : value = getCPS()
        elif vname == "CPM1st": value = getCPM1st()
        elif vname == "CPS1st": value = getCPS1st()
        elif vname == "CPM2nd": value = getCPM2nd()
        elif vname == "CPS2nd": value = getCPS2nd()
        else:                   value = NAN

        return value
    #######################################################

    start   = time.time()
    fncname = "getDataGMC: "
    GMCdict = {}
    for vname in g.GMCvarsAll:
        # edprint(fncname, "vname: ", vname)
        if vname in g.GMCvariables:
            GMCdict.update({vname: getGMCCounts(vname)})

    dur     = 1000 * (time.time() - start)
    dprint(fncname + "  {}  dur: {:0.1f} ms".format(GMCdict, dur))

    return GMCdict


def getCPM():
    """the normal CPM call; might get CPM as sum of both tubes'"""
    return getValGMC(wcommand=b'<GETCPM>>', rlength=g.GMCbytes)


def getCPS():
    """the normal CPS call; might be the sum of High- and Low- sensitivity tube"""
    return getValGMC(wcommand=b'<GETCPS>>', rlength=g.GMCbytes, maskHighBit=True)


def getCPM1st():
    """get CPM from High Sensitivity tube; that should be the 'normal' tube"""
    return getValGMC(wcommand=b'<GETCPML>>', rlength=g.GMCbytes)


def getCPS1st():
    """get CPS from High Sensitivity tube; that should be the 'normal' tube"""
    return getValGMC(wcommand=b'<GETCPSL>>', rlength=g.GMCbytes, maskHighBit=True)


def getCPM2nd():
    """get CPM from Low Sensitivity tube; that should be the 2nd tube in the 500+"""
    return getValGMC(wcommand=b'<GETCPMH>>', rlength=g.GMCbytes)


def getCPS2nd():
    """get CPS from Low Sensitivity tube; that should be the 2nd tube in the 500+"""
    return getValGMC(wcommand=b'<GETCPSH>>', rlength=g.GMCbytes, maskHighBit=True)


def getValGMC(wcommand, rlength, maskHighBit=False):
    """Write to and read from device and convert to value; return value"""
    # on Raspi: duration 3.3 ... typical 3.5 ... >100 ms

    start   = time.time()
    fncname = "getValGMC: "

    for i in range(5):  # try up to 5 times
        brec = b""
        if time.time() - start > 0.5:
            msg = "# {} 'takes too long; giving up in trial #{}\n".format(fncname, i)
            edprint(msg)
            appendDataLogFile(msg)
            break

        try:
            bwrt = g.GMCser.write(wcommand)                           # bytes-written (type int)
            brec = g.GMCser.read(rlength)                             # rec received  (type bytes)
            # dprint(fncname + "bwrt: ", bwrt, "  brec: ", brec)
            break
        except Exception as e:
            exceptPrint(e, fncname)
            msg = "# EXCEPTION: {} '{}' trial #{}\n".format(fncname, str(e), i)
            edprint(msg)
            appendDataLogFile(msg)

    if len(brec) == g.GMCbytes:
        # ok, got expected number of bytes
        if   g.GMCbytes == 4:
            value = ((brec[0]<< 8 | brec[1]) << 8 | brec[2]) << 8 | brec[3]
        elif g.GMCbytes == 2:
            value = brec[0] << 8 | brec[1]
            if maskHighBit : value = value & 0x3fff     # mask out high bits,
                                                        # applies only to CPS* calls on 300 series counters
    else:
        # Fail, bytes missing or too many
        msg = "# ERROR in byte count, got {} bytes, expected {}!".format(len(brec), g.GMCbytes)
        dprint(msg)
        appendDataLogFile(msg + "\n")
        value = NAN

    dur = 1000 * (time.time() - start)
    strcmd = wcommand.decode("UTF-8")
    vprint("- {:13s}{:10s}{:5.0f}   Bytes:{:1d} maskHighBit:{:5s} brec:{:20s} dur:{:0.1f} ms"\
                 .format(fncname, strcmd, value, rlength, str(maskHighBit), str(brec), dur))

    return value


############################################################################
# End Hardware functions for GMC devices  ##################################
############################################################################


############################################################################
# Hardware functions for I2C Device ########################################
############################################################################

def initI2C():
    """Initialize I2C"""

    fncname = "initI2C: "
    dprint(fncname)
    setIndent(1)

    if g.isRaspberryPi:
        # on Raspi
        try:
            import smbus
            # import smbus2 as smbus
            g.I2ConRaspi = True
        except ImportError as ie:
            msg  = "The module 'smbus' could not be imported, but is required. Cannot continue."
            exceptPrint(ie, msg)
            msg  = "\n\n" + msg + "\nOn Raspberry Pi install with: 'sudo apt install Python-smbus'."
            msg += "\nOn other computers install with 'python3 -m pip install -U smbus'."
            return msg
        except Exception as e:
            msg = str(e)
            exceptPrint(e, "")
            return msg

        # use I2C-Bus #1
        g.I2Chandle = smbus.SMBus(1)

        # do a bus scan
        scanI2C()

        # assemble sensor names and do first reads
        g.I2Csensor = ""
        if cI2Cusage_LM75B:
            g.I2Csensor += "LM75B "
            getValTemp()                                # dump first value
            g.I2CstoreTemp.append(getValTemp())         # fill first value

        if cI2Cusage_BH1750:
            g.I2Csensor += "BH1750 "
            getValLux()                                 # dump first value
            g.I2CstoreLux.append(getValLux())           # fill first value

        if cI2Cusage_GDK101:
            # store not needed; will always call "fresh" data
            g.I2Csensor += "GDK101 "
            getValGDK("OneMin")                         # dump value
            getValGDK("TenMin")                         # dump value

            fw = getGDK101Firmware()
            cdprint("GDK101 Firmware Version: ", fw)    # print the firmware version

    else:
        # NOT on Raspi
        g.I2Csensor  = "Simulation - it is not a Raspi Computer"

    dprint("I2C Settings:")
    dprint("   {:24s} : {}".format("I2C Sensors", g.I2Csensor))

    g.I2Cinit = True

    setIndent(0)

    return "Ok"


def terminateI2C():
    """closes I2C"""

    fncname = "terminateI2C: "

    if g.I2ConRaspi:
        try:                    g.I2Chandle.close()
        except Exception as e:  exceptPrint(e, "I2C connection is not available")
    else:
        # no action needed
        pass

    return "Terminate I2C: Done"


def scanI2C():
    """scans the I2C bus for I2C devices"""

    start = time.time()

    fncname = "scanI2C: "
    scanfmt = "0x{:02X}  "
    scan    = "       0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F"
    devcnt  = 0

    cdprint("Scanning I2C Bus:")
    cdprint(scan)
    scan    = scanfmt.format(0) + "-- "
    for addr in range(1, 128):
        if addr % 16  == 0:
            cdprint(scan)
            scan   = scanfmt.format(addr)
        try:
            g.I2Chandle.read_byte(addr)
            scan   += "{:02X} ".format(addr)
            devcnt += 1
        except Exception as e:
            scan   += "-- "

    dur = 1000 * (time.time() - start)
    scan += "\n\nFound a total of {} I2C device(s) in {:0.1f} ms\n".format(devcnt, dur)
    cdprint(scan)


def getI2CBytes(device, addr, reg, rbytes):
    """Read rbytes from reg at addr"""

    # on Raspi takes 0.5 ms typical, (0.5 ... 1.2 ms)

    # start   = time.time()

    fncname = "getI2CBytes: "

    for i in range(5):  # try up to 5 times
        try:
            raw = g.I2Chandle.read_i2c_block_data(addr, reg, rbytes)
            # raise Exception("test " + fncname)
            break                                                   # break on first success
        except Exception as e:
            exceptPrint(e, fncname + "{}  FAILURE I2C read: addr:{}, reg:{}, rbytes:{}".
                               format(device, hex(addr), hex(reg), rbytes))
            raw = b"Fail"
            edprint(fncname + "Fail in trial #{}, trying again".format(i))

    # dur = 1000 * (time.time() - start)
    # rdprint(fncname + "  raw:{} dur: {:0.2f} ms".format(raw, dur))

    return raw


def getDataI2C():
    """get the data for the I2C device"""

    # LM75B     has a single Temp value
    # BH1750    has a single Lux value
    # GDK101    has 2 values: a OneMin (1min) value and a TenMin (10min avg)
    #           value, but only OneMin is used here

    start   = time.time()
    fncname = "getDataI2C: "
    I2CDict = {}

    # get Temp
    if cI2Cusage_LM75B:
        for vname, vavg in cI2Cvars_LM75B.items():
            # rdprint(fncname, "vname, vavg: ", vname, "  ", vavg)
            # rdprint("g.I2CstoreTemp: ", g.I2CstoreTemp)
            if vavg == 1:
                # get the last value read from sensor
                value = g.I2CstoreTemp[-1]
            else:
                # get avg of last vavg values
                vavg     = clamp(vavg, 2, 60)
                lenStore = len(g.I2CstoreTemp)      # number of values in queue
                Navg     = min(lenStore, vavg)      # number of values to avg

                newStore = list(g.I2CstoreTemp)
                value    = sum(newStore[-Navg:])
                if Navg > 0:    value = round(value / Navg, 3)
                else:           value = NAN

            I2CDict.update({vname: value})


    # get Lux
    if cI2Cusage_BH1750:
        for vname, vavg in cI2Cvars_BH1750.items():
            if vavg == 1:
                # the last value read from sensor
                value = g.I2CstoreLux[-1]
            else:
                # get avg of last vavg values
                vavg     = clamp(vavg, 2, 60)
                lenStore = len(g.I2CstoreLux)         # number of values in queue
                Navg     = min(lenStore, vavg)        # number of values to avg

                newStore = list(g.I2CstoreLux)
                value    = sum(newStore[-Navg:])
                if Navg > 0:    value = round(value / Navg, 3)
                else:           value = NAN

            I2CDict.update({vname: value})


    # get Solid State CPM
    if cI2Cusage_GDK101:
        # there is no avg for this sensor,
        # it always produces the 'last' value
        for vname, vavg in cI2Cvars_GDK101.items():
            # rdprint(fncname, vname, vavg)
            I2CDict.update({vname:    getValGDK("OneMin")})           # CPM (1 min)
            # getValGDK("TenMin")                                     # CPM avg over 10 min

            # MT = getGDK101MeasTime()                                # wofür ist das gut???
            # # rdprint("Meas.Time: ",    "{:6.3f}".format(MT))       # print the Measurement Time


    duration = 1000 * (time.time() - start)
    dprint(fncname + "  {} dur: {:0.1f} ms".format(I2CDict, duration))

    return I2CDict


#
# I2C for LM75B ################################################################
#
def getValTemp():
    """get Temp from I2C connected LM75B"""

    # running on Raspi: takes 0.55 ms typical, range: 0.5 ... 1.5 ms

    start = time.time()

    fncname = "getValTemp:  "

    if g.I2ConRaspi == False:
        # not running on Raspi
        # just fudge some random float numbers around 20
        raw  = b"Simul"
        Temp = random.uniform(15, 25)

    else:
        # running on Raspi:
        device   = "LM75B"
        addr     = cI2Caddress_LM75B
        register = 0x00
        rbytes   = 2
        raw      = getI2CBytes(device, addr, register, rbytes)

        if len(raw) == rbytes:
            temp1    = ((raw[0] << 8 | raw[1] ) >> 5)   # assuming LM75B with 11bit Temp resolution
            if temp1 & 0x400: temp1 = temp1 - 0x800     # 0x400 == 0b0100 0000 0000, 0x800 == 0b1000 0000 0000
            Temp     = temp1 * 0.125                    # deg Celsius for LM75B; +/- 128°C @11 bit => 0.125 °C per step
        else:
            Temp     = NAN

    dur = 1000 * (time.time() - start)
    vprint("- {:13s}Temp: {:8.3f}  raw:{:10s}  dur:{:0.3f} ms".format(fncname, Temp, str(raw), dur)) # vprint takes 0.1 ... 0.3 ms

    return Temp


def getResetLM75B():
    """Pseudo reset - makes just one regular data call + deque reset!"""

    fncname = "getResetLM75B: "

    if g.I2ConRaspi == False:
        # not running on Raspi
        resetresp = "Ok(not a Raspi)"
        raw       = b"Simul"

    else:
        # running on Raspi:
        resetresp = "Ok"
        raw       = b"Dummy"

    g.I2CstoreTemp = deque([], 60)                    # space for 60 sec data; used for averaging
    getValTemp()                                      # dump first value
    g.I2CstoreTemp.append(getValTemp())               # fill first value

    return resetresp


#
# I2C for BH1750 (= GY-30) ###########################################################
#
def getValLux():
    """get Light intensity in Lux from I2C connected BH1750
    using the sensor's 'One Time L-Resolution Mode'"""

    # running on Raspi: takes 0.53 ms typical, range: 0.5 ... 1.5 ms

    start = time.time()

    fncname = "getValLux:  "

    if g.I2ConRaspi == False:
        # not running on Raspi
        # just fudge some random float numbers around 500 (= standard Lux for lighting in office)
        Lux = round(random.uniform(470, 530), 3)
        raw = b"Simul"

    else:
        # running on Raspi:
        device   = "BH1750"
        addr     = cI2Caddress_BH1750
        register = 0x23
        rbytes   = 2
        raw      = getI2CBytes(device, addr, register, rbytes)

        if len(raw) == rbytes:
            # official data: divide by 1.2, not by 1.0!
            Lux      = round((raw[0] << 8 | raw[0]) / 1.0, 3)
        else:
            Lux = NAN

    dur = 1000 * (time.time() - start)
    vprint("- {:13s}Lux: {:9.3f}  raw:{:10s}  dur:{:0.3f} ms".format(fncname, Lux, str(raw), dur)) # vprint takses 0.1 ... 0.2 ms

    return Lux


def getResetBH1750():
    """Reset the data register and clears deque"""

    # start   = time.time()
    fncname = "getResetBH1750: "

    if g.I2ConRaspi == False:
        # not running on Raspi
        resetresp = "Ok(not a Raspi)"
        raw       = b"Simul"

    else:
        # running on Raspi:
        device   = "BH1750"
        addr     = cI2Caddress_BH1750
        register = 0x07
        rbytes   = 0
        raw      = getI2CBytes(device, addr, register, rbytes)

        if len(raw) > 0:    resetresp = "FAILURE"
        else:               resetresp = "Ok"

    g.I2CstoreLux = deque([], 60)                     # space for 60 sec data; used for averaging
    getValLux()                                       # dump first value
    g.I2CstoreLux.append(getValLux())                 # fill first value

    # # dur = 1000 * (time.time() - start)
    # vprint(fncname + " Resp:{}  raw:{:10s}  dur:{:0.3f} ms".format(resetresp, str(raw), dur))

    return resetresp


#
# I2C for GDK101 ##########################################################
#
def getValGDK(ctype):
    """get data from GDK101
    - ctype is: "OneMin" => 0xB3: Counts per 1 min
    -       or: "TenMin" => 0xB2: Counts per 1 min derived from counting 10 min
    return: count rate in CPM terms"""

    start = time.time()

    fncname = "getValGDK: "

    if g.I2ConRaspi == False:
        # NOT running on Raspi
        # just fudge some random integer numbers
        if ctype == "TenMin":   cpmvalue = random.randint(110, 120)     # CPM as 10 min avg
        else:                   cpmvalue = random.randint(100, 130)     # OneMin (=1 min avg)  as default
        raw      = b"Simul"
        usvvalue = NAN

    else:
        # running on Raspi:
        device   = "GDK101"
        addr     = cI2Caddress_GDK101
        register = 0xB2 if ctype == "TenMin" else 0xB3                 # default is 1 min == 0xB3
        rbytes   = 2
        raw      = getI2CBytes(device, addr, register, rbytes)

        #
        # # Vibration does not seem to have any effect on read-out value???
        #
        # if getGDK101Status()[1] == 1:
        #     # detected vibration
        #     rdprint("saw vibration, reading anyway", )
        #     raw  = getI2CBytes(device, addr, register, rbytes)
        #     rdprint("saw vibration, raw: ", raw)
        #     raw  = b"Vibrate"
        #
        # else:
        #     # no vibration, valid data
        #     raw  = getI2CBytes(device, addr, register, rbytes)
        #     rdprint("without vibration, raw: ", raw)

        if len(raw) == rbytes:
            # Problem: double zero can be correct value, but also happens as erroneous reading
            # how to distinguish?
            usvvalue = raw[0] + (raw[1] / 100)
            cpmvalue = round(usvvalue * 8.33, 3)
        else:
            edprint(fncname + "raw does not have length of 2: {}".format(raw))
            usvvalue = NAN
            cpmvalue = NAN

    dur = 1000 * (time.time() - start)
    vprint("- {:13s}{:5s}:{:7.3f}  raw:{:10s}  dur:{:0.3f} ms  usv:{}".format(fncname, ctype, cpmvalue, str(raw), dur, usvvalue))

    return cpmvalue


def getGDK101MeasTime():
    """get measurement time from GDK101; goes from 0 ... 11, then cycles within 10 ... 11.
    return: time in minutes"""

    start = time.time()

    fncname = "getGDK101MeasTime: "

    ctype = "MTime"

    if g.I2ConRaspi == False:
        # not running on Raspi
        # just fudge some random float numbers
        value = round(random.uniform(10, 11), 3)
        raw   = b"Simul"

    else:
        # running on Raspi:
        device   = "GDK101"
        addr     = cI2Caddress_GDK101
        register = 0xB1
        rbytes   = 2
        raw      = getI2CBytes(device, addr, register, rbytes)

        if len(raw) == rbytes:
            value    = round((raw[0] * 60 + raw[1]) / 60, 3)          # (minutes * 60 + seconds) / 60 ==> minutes
        else:
            edprint(fncname + "raw:{} does not have length of {}".format(raw, rbytes))
            value = NAN

    dur = 1000 * (time.time() - start)
    dprint("{:20s}{:6s}  raw:{:10s}  value:{:6.3f}  dur:{:0.2f} ms".format(fncname, ctype, str(raw), value, dur))

    return value


def getGDK101Firmware():
    """get firmware from GDK101
    return: major.minor firmware"""

    start = time.time()

    fncname = "getGDK101Firmware: "
    ctype   = "FirmW"

    if g.I2ConRaspi == False:
        # not running on Raspi
        firmw = "Simul"
        raw   = b"Simul"

    else:
        # running on Raspi:
        device   = "GDK101"
        addr     = cI2Caddress_GDK101
        register = 0xB4
        rbytes   = 2
        raw      = getI2CBytes(device, addr, register, rbytes)

        if len(raw) == rbytes:
            firmw = "{}.{}".format(*raw)
        else:
            edprint(fncname + "raw does not have length of {}: {}".format(rbytes, raw))
            firmw = "Failure"

    dur = 1000 * (time.time() - start)
    dprint("{:20s}{:6s}  raw:{:10s}  FirmW:{}  dur:{:0.2f} ms".format(fncname, ctype, str(raw), firmw, dur))

    return firmw


def getGDK101Status():
    """get status and vibration status from GDK101
    return: tuple: (status, vibratestatus)"""

    start = time.time()

    fncname = "getGDK101Status: "
    ctype   = "Status"

    if g.I2ConRaspi == False:
        # not running on Raspi
        status = (NAN, NAN)
        raw    = b"Simul"

    else:
        # running on Raspi
        device   = "GDK101"
        addr     = cI2Caddress_GDK101
        register = 0xB0
        rbytes   = 2
        raw      = getI2CBytes(device, addr, register, rbytes)

        if len(raw) == rbytes:
            status   = (raw[0], raw[1])
        else:
            edprint(fncname + "raw does not have length of {}: {}".format(raw, rbytes))
            status = (NAN, NAN)

    dur = 1000 * (time.time() - start)
    dprint("-- {:20s}{:6s}  raw:{:10s}  dur:{:0.2f} ms".format(fncname, ctype, str(raw), dur))

    return status


def getResetGDK101():
    """make a reset of the GDK101
    return: resetresp"""

    # start = time.time()

    fncname = "getResetGDK101: "

    if g.I2ConRaspi == False:
        # not running on Raspi
        raw       = b""
        resetresp = "Ok(not a Raspi)"

    else:
        # running on Raspi:
        device   = "GDK101"
        addr     = cI2Caddress_GDK101
        register = 0xA0
        rbytes   = 2
        raw      = getI2CBytes(device, addr, register, rbytes)

        if len(raw) == rbytes:
            if raw[0] == 1: resetresp = "Ok"    # check msb only
            else:           resetresp = "FAIL"
        else:
            edprint(fncname + "raw does not have length of {}: {}".format(rbytes, raw))
            resetresp = "FAIL"

    getValGDK("OneMin")                             # dump value
    getValGDK("TenMin")                             # dump value

    # dur = 1000 * (time.time() - start)
    # vprint("{:20s} raw:{:10s}  Reset:{}  dur:{:0.2f} ms".format(fncname, str(raw), resetresp, dur))

    return resetresp


############################################################################
# End Hardware functions for I2C device  ###################################
############################################################################


############################################################################
# Hardware functions for Raspi Pulse Counter  ##############################
############################################################################

def initPulse():
    """Initialize Pulse Counter"""

    global GPIO     # needed in terminatePulse

    fncname = "initPulse: "
    dprint(fncname)
    setIndent(1)

    # check cPulseCountPin
    cPCP = int(cPulseCountPin)
    if 5 <= cPCP <= 26 : g.PulseCountPin = cPCP
    else:
        edprint("ERROR: '{}' is not a possible value for cPulseCountPin.".format(cPulseCountPin))
        edprint("Allowed is 5 ... 26. But verify no other comflicting uses of the chosen pin!")
        setIndent(0)
        return "ERROR"

    # check PulseVariables
    if cPulseVariables == "auto" : pv = "CPM, CPS"
    else:                          pv = cPulseVariables
    for vname in pv.split(","):
        pvar = vname.strip()
        if pvar in g.PulseVarsAll:
            g.PulseVariables.append(pvar)
        else:
            edprint("ERROR: '{}' is not a possible variable for Pulse.".format(pvar))
            edprint("Allowed is: {}".format(g.PulseVarsAll))
            setIndent(0)
            return "ERROR"

    if g.isRaspberryPi:
        # on a Raspi
        try:
            import RPi.GPIO as GPIO         # can be imported ONLY on Raspi, fails elsewhere
            g.PulseOnRaspi = True           # True only if on Raspi AND did load GPIO!
        except ImportError as ie:
            msg  = "The module 'RPi.GPIO' was not found but is required."
            msg += "\nInstall with: 'python3 -m pip install -U RPi.GPIO'"
            exceptPrint(ie, msg)
            setIndent(0)
            return msg
        except Exception as e:
            msg = "Unexpected Failure on Importing 'RPi.GPIO'"
            exceptPrint(e, msg)
            setIndent(0)
            return msg

        # to eliminate warnings on "already in use channel"
        # when, due to an exception, crash cleanup had not been done
        GPIO.setwarnings(False)

        # using BCM mode; use GPIO.setmode(GPIO.BOARD) for boardpin usage
        GPIO.setmode(GPIO.BCM)

        # configure PWM
        GPIO.setup(g.PWMPin, GPIO.OUT)                      # define PWMPin as output
        g.PWMHandle = GPIO.PWM(g.PWMPin, g.PWMFreq)         # set PWM at pin and freq; PWM is not precise
        g.PWMHandle.start(g.PWMDutyCycle)                   # start, includes setting duty cycle
        # g.PWMHandle.ChangeDutyCycle(10)                   # (0.0 ... 100.0)
        # g.PWMHandle.ChangeFrequency(freq)                 # frequency (min: > 1.0; max: is ???)

        # configure Pulse counting
        ## set falling edge
        ## GPIO.setup(g.PulseCountPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        ## GPIO.add_event_detect(g.PulseCountPin, GPIO.FALLING, callback=incrementPulseCounts)
        #
        # set rising edge
        GPIO.setup(g.PulseCountPin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
        GPIO.add_event_detect(g.PulseCountPin, GPIO.RISING, callback=incrementPulseCounts)   # counting starts!

        # add first CPS value to 60 sec store
        time.sleep(1)                                   # let counts accumulate for 1 sec, before ...
        g.PulseStore.append(getValPulse())              # ... filling first value

        dprint("Pulse Settings:")
        dprint("   {:24s} : {}"   .format("Pin Mode"               , "GPIO.BCM"))
        dprint("   {:24s} : {}"   .format("Pulse BCM Pin #"        , g.PulseCountPin))
        dprint("   {:24s} : {}"   .format("Pulse Pull up / down"   , "GPIO.PUD_DOWN"))
        dprint("   {:24s} : {}"   .format("Pulse Edge detection"   , "GPIO.RISING"))
        dprint("   {:24s} : {}"   .format("PWM Pin "               , g.PWMPin))
        dprint("   {:24s} : {} %" .format("PWM Duty Cycle "        , g.PWMDutyCycle))
        dprint("   {:24s} : {} Hz".format("PWM Frequency "         , g.PWMFreq))

    else:
        # NOT on a Raspi
        g.PulseOnRaspi = False
        g.PulseStore.append(getValPulse())              # ... filling first simul value

        dprint("Pulse Settings:")
        dprint("   {:24s} : {}".format("Pulse Mode"             , "Simulation - it is not a Raspi Computer"))

    g.PulseInit = True

    setIndent(0)

    return "Ok"


def terminatePulse():
    """shuts down the pulse counter; cleanup is important!"""

    fncname = "terminatePulse: "

    if g.PulseOnRaspi:
        # on Raspi
        try:
            GPIO.remove_event_detect(g.PulseCountPin)
            g.PWMHandle.stop()
            GPIO.cleanup()  # cleans up only the channels used by THIS program
        except Exception as e:
            exceptPrint(e, fncname + "Failure in GPIO actions")
    else:
        # not on Raspi
        # does not need any action
        pass

    return "Terminate Pulse: Done"


def getResetPulse():
    """reset the Pulse counter"""

    if g.PulseOnRaspi:
        # on Raspi
        resetresp = "Ok"
    else:
        # not on Raspi
        resetresp = "Ok(not a Raspi)"

    g.PulseCountStart = time.time()
    g.PulseStore      = deque([], 60)                     # space for 60 sec data; used for summing up to get CPM
    g.PulseCountTotal = 0
    g.PulseCount      = 0

    # get the first value to store
    time.sleep(1)                                         # wait for 1 sec to collect pulses, before ...
    g.PulseStore.append(getValPulse())                    # ... filling first value

    return resetresp


def incrementPulseCounts(BCMpin):
    """increment Pulse counter"""
    # NOTE: BCMpin is the PulseCountPin as BCM pin number (e.g.: 17)

    # print("incrementPulseCounts called, PulseCount: ", g.PulseCount)
    # print("incrementPulseCounts called, BCMpin: ", BCMpin)

    g.PulseCount += 1


def getValPulse():
    """gets the CPS Pulses when on Raspi and reset to zero, otherwise fudges a PulseCount"""
    # not on Raspi: 10 ... 50 mikro sec
    # on Raspi:      3 ...  5 mikro sec (!)

    start   = time.time()

    fncname = "getValPulse: "

    if g.PulseOnRaspi:
        # on a Raspi
        lcl_PulseCount = g.PulseCount
        g.PulseCount     = 0
        raw            = b"Pulse"
    else:
        # NOT on a Raspi
        # fudge some random counts of CPS around PWMFreq(=10)
        lcl_PulseCount = round(max(0.1, random.normalvariate(g.PWMFreq, math.sqrt(g.PWMFreq))), 0)
        raw            = b"Simul"

    g.PulseCountTotal += lcl_PulseCount

    dur = 1000 * (time.time() - start)
    vprint("- {:13s}CPS: {:9.0f}  raw:{:10s}  dur:{:0.3f} ms".format(fncname, lcl_PulseCount, str(raw), dur)) # vprint takses 0.1 ... 0.3 ms

    return lcl_PulseCount


def getPulseCPS():
    """get last CPS counts and return as value"""

    return g.PulseStore[-1]


def getPulseCPM():
    """get CPM counts and return as value"""

    # rdprint("getPulseCPM: ", len(g.PulseStore), "  ", g.PulseStore)
    lenstore = len(g.PulseStore)
    if lenstore <= 3:
        CPM = NAN
    else:
        CPM = sum(g.PulseStore)
        CPM = int(round(CPM / lenstore * 60, 0)) # estimate CPM from less than 60 CPS for the first 1 min
                                                 # but only if there are more than 3 CPS values

    return CPM


def getDataPulse():
    """get the data from Pulse"""

    start     = time.time()
    fncname   = "getDataPulse: "
    PulseDict = {}
    M         = getPulseCPM()
    S         = getPulseCPS()
    for vname in g.PulseVarsAll:
        # edprint(fncname, "vname: ", vname)
        if vname in g.PulseVariables:
            # rdprint(fncname, "vname: ", vname)
            if   "CPM" in vname:  PulseDict.update({vname: M})
            elif "CPS" in vname:  PulseDict.update({vname: S})

            # ##testing
            # elif vname == "Temp":  PulseDict.update({vname: round(time.time() - g.PulseCountStart, 3)})
            # elif vname == "Press": PulseDict.update({vname: g.PulseCountTotal})
            # #########

    dur = 1000 * (time.time() - start)
    dprint(fncname + "{}  dur: {:0.3f} ms".format(PulseDict, dur))

    return PulseDict


############################################################################
# End Hardware functions for Raspi Pulse Counter  ##########################
############################################################################



def writeDataLogFile(msg):
    """Make new file, or empty old one, then write msg to file"""

    if cDataLogFile == "":
        # no writing if filename is empty
        g.DataLogFileWOK = False
        dprint("{:33s} : {}".format("Init DataLogFile", "DataLogFile will NOT be written"))
        return

    try:
        with open(g.DataLogFile, 'w') as log:
            log.write(msg)
        dprint("{:33s} : {}".format("Init DataLogFile", "Ok, filename: '{}'".format(g.DataLogFile)))
    except Exception as e:
        msg = "{:33s} : {}".format("Init DataLogFile", "FAILURE: DataLogFile '{}' Could NOT be written!".format(g.DataLogFile))
        exceptPrint(e, "")
        dprint(msg)


def writeProgLogFile(msg):
    """Make new file, or empty old one, then write msg to file"""

    if cProgLogFile == "":
        # no writing if filename is empty
        g.ProgLogFileStartWOK = False
        g.ProgLogFileRunWOK   = False
        dprint("{:33s} : {}".format("Init ProgLogFile", "ProgLogFile will NOT be written"))
        return

    # Log File: ProgLogFileStart
    try:
        with open(g.ProgLogFileStart, 'w') as log:
            log.write(msg)
        dprint("{:33s} : {}".format("Init ProgLogFileStart", "Ok, filename: '{}'".format(g.ProgLogFileStart)))
    except Exception as e:
        msg = "{:33s} : {}".format("Init ProgLogFileStart", "FAILURE: ProgLogFileStart '{}' Could NOT be written!".format(g.ProgLogFileStart))
        exceptPrint(e, "")
        dprint(msg)

    # Log File: ProgLogFileRun
    try:
        with open(g.ProgLogFileRun, 'w') as log:
            log.write("No data yet\n")
        dprint("{:33s} : {}".format("Init ProgLogFileRun", "Ok, filename: '{}'".format(g.ProgLogFileRun)))
    except Exception as e:
        msg = "{:33s} : {}".format("Init ProgLogFileRun", "FAILURE: ProgLogFileRun '{}' Could NOT be written!".format(g.ProgLogFileRun))
        exceptPrint(e, "")
        dprint(msg)


def appendDataLogFile(msg):
    """append msg to the end of file"""

    if g.DataLogFileWOK == False: return # no writing

    try:
        with open(g.DataLogFile, 'a') as log:
            if log.tell() < g.DataLogFileMax:
                log.write(msg)
            else:
                log.write(g.DataLogFileMaxMsg)
                g.DataLogFileWOK = False
    except: pass


def appendProgLogFile(msg):
    """append msg to the end of file"""

    # Log File: ProgLogFileStart
    if g.ProgLogFileStartWOK == True:
        try:
            with open(g.ProgLogFileStart, 'a') as log:
                if log.tell() < g.ProgLogFileStartMax:
                    log.write(msg)
                else:
                    log.write(g.ProgLogFileStartMaxMsg)
                    g.ProgLogFileStartWOK = False
                    g.ProgLogFileRunWOK   = True
        except: pass

    # Log File: ProgLogFileRun
    if g.ProgLogFileRunWOK == True:
        LogOverwrite = False
        try:
            with open(g.ProgLogFileRun, 'a') as log:
                if log.tell() < g.ProgLogFileRunMax:
                    log.write(msg)
                else:
                    LogOverwrite = True
        except: pass

        if LogOverwrite:
            try:
                with open(g.ProgLogFileRun, 'w') as log:
                    log.write("")
                dprint("{:33s} : {}".format("ProgLogFileRun was overwritten", "Ok, filename: '{}'".format(g.ProgLogFileRun)))
            except Exception as e:
                msg = "{:33s} : {}".format("ProgLogFileRun overwriting", "FAILURE: ProgLogFileRun '{}' Could NOT be written!".format(g.ProgLogFileRun))
                exceptPrint(e, "")
                dprint(msg)


def resetDevices(device = "All"):
    """resets devices; device = 'All' | 'GMC' | 'Pulse' | 'I2C' """

    fncname     = "resetDevices: "
    dprint(fncname)
    setIndent(1)

    DEVICE      = device.upper()
    resetresp   = ""

    # GMC
    if DEVICE == "ALL" or DEVICE == "GMC" :
        # nothing to reset
        resetresp      += "GMC Ok, "

    # I2C
    if DEVICE == "ALL" or DEVICE == "I2C" :
        if cI2Cusage_LM75B:  resetresp += "LM75B {}, " .format(getResetLM75B())
        if cI2Cusage_BH1750: resetresp += "BH1750 {}, ".format(getResetBH1750())
        if cI2Cusage_GDK101: resetresp += "GDK101 {}, ".format(getResetGDK101()) # will reset counter,
                                                                                 # -> takes 1 min to get new read >0!

    # Pulse
    if DEVICE == "ALL" or DEVICE == "PULSE" :
        resetresp  += "Pulse {}, ".format(getResetPulse())

    resetresp = resetresp[:-2]   # remove last ", "

    vprint("{} {}".format(fncname, resetresp))

    setIndent(0)
    return resetresp


def main():
    """begin here"""

    #### local################################################
    def initHardware(hw):
        if   hw.upper() == "GMC":   initresp = initGMC()
        elif hw.upper() == "I2C":   initresp = initI2C()
        elif hw.upper() == "PULSE": initresp = initPulse()
        else:                       initresp = "Unknown Device"

        return initresp


    def terminateHW(hw):
        if   hw.upper() == "GMC":   dprint(terminateGMC())
        elif hw.upper() == "I2C":   dprint(terminateI2C())
        elif hw.upper() == "PULSE": dprint(terminatePulse())

    ##########################################################

    # verify Python version is >= v3.7
    svi = sys.version_info
    if svi < (3, 7):
        print("This software requires Python Version 3.7 or later")                     # wg HTTP server
        print("Your Python version is Version {}.{}.{}".format(svi[0], svi[1], svi[2]))
        print("Cannot continue, will exit.")
        return

    # check if computer is Raspi
    CheckRaspberryPi()

    # print system docu
    print("=" * 150)
    sysdoc  = ""
    sysdoc += "# {:28s} : {}\n".format("Version of {}".format(__script__), __version__)
    sysdoc += "# {:28s} : {}\n".format("Version of Python", sys.version.split(" ")[0])
    sysdoc += "# {:28s} : {}\n".format("Version of Operating System", platform.platform())
    sysdoc += "# {:28s} : {}, {}\n".format("Machine, Architecture", platform.machine(), platform.architecture()[0])
    sysdoc += "# {:28s} : {}\n".format("Computer Model", g.computer)
    sysdoc += "# {:28s} : {}\n".format("Command Line", sys.argv)
    sysdoc += "# {:28s} : {}\n".format("Working Directory", os.getcwd())
    sysdoc += "# {:28s} : {}\n".format("LogFile Data", g.DataLogFile)
    sysdoc += "# {:28s} : {}\n".format("LogFile Prog @Start", g.ProgLogFileStart)
    sysdoc += "# {:28s} : {}\n".format("LogFile Prog @Run", g.ProgLogFileRun)
    sysdoc += "# {:28s} : {}\n".format("Supported Devices", "GMC, I2C, Pulse")
    sysdoc += "\n"

    # init ProgLogFile (must come BEFORE init DataLogFile!)
    msg  = "# ProgLogFile created with: '{}', Version: {}\n".format(__script__, __version__)
    writeProgLogFile(msg)

    # init DataLogFile
    msg  = "# DataLogFile created with: '{}', Version: {}\n".format(__script__, __version__)
    msg += sysdoc
    msg += "# Index,                DateTime,      CPM,      CPS,   CPM1st,   CPS1st,   CPM2nd,   CPS2nd,   CPM3rd,   CPS3rd,     Temp,    Press,    Humid,     Xtra,   Duration[ms]\n"
    writeDataLogFile(msg)

    dprint("System Documentation: \n" + sysdoc)

    # check if any hardware is requested
    if len(sys.argv) == 1:
        dprint("No hardware given on command line")
        dprint("   Start with: GLWifiServer <one or all of: GMC, I2C, Pulse>")
        dprint("   EXAMPLE   : GLWifiServer GMC I2C Pulse")
        return

    # check the hardware args
    hardwareargs   = sys.argv[1:]
    hwDevs         = ""
    for i, device in enumerate(hardwareargs):
        if device.upper() in g.hardwareChoice:
            hardwareargs[i] = device.upper().strip()
            hwDevs         += device + ", "
        else:
            edprint("{:33s} : {}".format("Unavailable Device '{}' Requested".format(device), "Cannot continue"))
            return
    dprint("{:33s} : {}".format("Requested Devices", hwDevs[:-2]))

    # init all hardware
    dprint("{:33s} : {}".format("Inititalize requested devices", ""))
    setIndent(1)
    for hw in hardwareargs:
        hwInitResp = initHardware(hw)
        hmsg       = "   {:27s} : {}".format("Init {} Devices:".format(hw), hwInitResp)
        if hwInitResp == "Ok":
            g.hardware.append(hw)
            gdprint(hmsg)
        else:
            edprint(hmsg)
            return

    gdprint("{:30s} : {}".format("Devices initialized", g.hardware))
    setIndent(0)

    dprint()

    # init WiFi Server
    WSsuccess, WSresponse = initWiFiServer()
    if WSsuccess:
        gdprint("{:33s} : {}".format("Init WiFi Server", WSresponse))
    else:
        edprint("{:33s} : {}".format("Init WiFi Server", WSresponse))
        return

    dprint()

    # Loop forever; break with CTRL-C
    # Use simple timer to create 1 sec intervals
    # for getting Temp, Lux, Counts to use for avg
    try:
        next = time.time() + 1                                  # add 1 sec
        time.sleep(max(0, next - time.time() - 0.002))          # sleep until 2 ms before next cycle
        while True:
            if time.time() >= next:
                # for I2C
                if "I2C" in g.hardware:
                    # for I2C Temperature
                    g.I2CstoreTemp.append(getValTemp())

                    # for I2C Light intensity
                    g.I2CstoreLux .append(getValLux())

                # for Pulse
                if "PULSE" in g.hardware:
                    g.PulseStore.append(getValPulse())

                    # ### Testing #####
                    # # change freq by Normal distribution around PWMFreq
                    # rfreq = max(1.000001, random.normalvariate(g.PWMFreq, math.sqrt(g.PWMFreq))) freq > 1.0 !
                    # # rdprint("rfreq: ", rfreq)
                    # if g.PWMHandle is not None: g.PWMHandle.ChangeFrequency(rfreq)
                    # #################

                next   = time.time() + 1                        # start a new 1 sec period
                deltat = max(0, next - time.time() - 0.0015)    # how long to sleep (not negative!)
                time.sleep(deltat)                              # allow for some cycles in while loop

    except KeyboardInterrupt:
        dprint()
        dprint(terminateWiFiServer())
        for hw in g.hardware:
            terminateHW(hw)


if __name__ == '__main__':
    main()
    dprint("Exiting {}".format(__script__))
    print()
