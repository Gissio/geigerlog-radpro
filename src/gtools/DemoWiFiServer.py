#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
DemoWifiServer -
                A Python webserver running as a GeigerLog WiFiServer device
                enabling various external devices to send data by WiFi.

                It responds with 12 vars of random values from a Poisson distrib
                like: 12, 0, 117, 2, 207, 2, 309, 3, 12, 988, 79, 48

Start with: path/to/DemoWifiServer.py
Stop  with: CTRL-C

Requires Python 3.7 or later (threading HTTP-Server)
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
#
## Port Number
#  On which Port number shall the WiFiServer listen
#  Options:      1024 ... 65535
#  Default     = 4000
WiFiServerPort = 4000

## Display name
DisplayName    = "GeigerLog DemoWiFiServer"

# Filename of log file
Logfile        = ""                       # if left empty a log file will NOT be written
# Logfile      = "DemoWifiServer.log"     # the log file will be in the directory from
                                          # where you started DemoWifiServer
#
####################   END of CUSTOMIZATION   ##################################
################## NO USER CHANGES BELOW THIS LINE ! ###########################



import sys, os, io, time, datetime              # basic modules
import traceback
import platform                                 # to find OS
import socket                                   # finding IP Adress
import http.server                              # web server
import urllib.parse                             # to parse queries
import threading                                # higher-level threading interfaces
import numpy                as np               # for fudging some numbers


__author__              = "ullix"
__copyright__           = "Copyright 2016, 2017, 2018, 2019, 2020, 2021, 2022"
__credits__             = [""]
__license__             = "GPL3"
__version__             = "1.0"                       # of this script
__script__              = os.path.basename(__file__)  # exclude the path, give just the filename


# colors for Linux terminal
TDEFAULT                = '\033[0m'             # default, i.e greyish
TYELLOW                 = '\033[93m'            # yellow

if "WINDOWS" in platform.platform().upper():    # Windows does not support terminal colors
    TDEFAULT            = ""
    TYELLOW             = ""

# Default settings
NAN                     = float('nan')          # 'not-a-number'; used as 'missing value'
debug                   = True                  #
verbose                 = True                  #
PrintIndent             = ""                    # indentation of log msg
xprintcounter           = 0                     # the count of dprint, vprint, wprint, xdprint commands

# GeigerLog's vars
VarNames                = ['CPM', 'CPS', 'CPM1st', 'CPS1st', 'CPM2nd', 'CPS2nd', 'CPM3rd', 'CPS3rd', 'Temp', 'Press', 'Humid', 'Xtra']

# WiFi Server
dogetmsg                = ""                    # web server msg
color                   = TDEFAULT              # used also as flag for color printout in Linux terminal
index                   = 0                     # number of WiFi calls
WiFiServer              = None                  # the HTTP Web server
WiFiServerThread        = None                  # thread handle
WiFiServerThreadStop    = None                  # flag to stop thread


def longstime():
    """Return current time as YYYY-MM-DD HH:MM:SS.mmm, (mmm = millisec)"""

    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] # ms resolution


def commonPrint(ptype, *args):
    """Printing function
    ptype : DEBUG, VERBOSE, werbose, ERROR
    args  : anything to be printed
    return: nothing
    """

    global xprintcounter

    xprintcounter += 1

    tag = "{:23s} {:7s}: {:.>6d} ".format(longstime(), ptype, xprintcounter) + PrintIndent
    for arg in args: tag += str(arg)
    if ptype == "ERROR":    print(TYELLOW + tag + TDEFAULT)
    else:                   print(tag)


def dprint(*args):
    """Print args as single line"""

    if debug:   commonPrint("DEBUG", *args)


def edprint(*args):
    """Print args as single line"""

    if debug:   commonPrint("ERROR", *args)


def vprint(*args):
    """Print args as single line"""

    if verbose: commonPrint("VERBOSE", *args)


def exceptPrint(e, srcinfo):
    """Print exception details (errmessage, file, line no)"""

    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname                     = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]    # which file?

    dprint(TYELLOW + "EXCEPTION: {} ({}) in file: {} in line: {}".format(srcinfo, e, fname, exc_tb.tb_lineno), TDEFAULT)
    # dprint(traceback.format_exc())



def getMyIP():
    """get the IP of the computer running this program"""

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


def initWiFiServer():
    """Initialize WiFiServer"""

    global WiFiServer, WiFiServerThread, WiFiServerThreadStop

    fncname = "initWiFiServer: "

    # detect IP; use Port as set in header
    WiFiServerIP = getMyIP()

    # create the web server
    try:
        # 'ThreadingHTTPServer': New in version Py 3.7. Not compatible with 3.6
        # non-threading may have been cause for crashing on double requests!
        # WiFiServer = http.server.HTTPServer((WiFiServerIP, WiFiServerPort), MyServer)
        WiFiServer = http.server.ThreadingHTTPServer((WiFiServerIP, WiFiServerPort), MyServer)
        WiFiServer.timeout = 1
        # msg = (True, "Ok, listening at: http://%s:%s" % (WiFiServerIP, WiFiServerPort))
        msg = (True, "Ok, listening at: http://{}:{}".format(WiFiServerIP, WiFiServerPort))

    except OSError as e:
        exceptPrint(e, "")
        msg0 = "WiFiServer could not be started, because "
        if e.errno == 98:   msg = (False, msg0 + "Port number {} is already in use".format(WiFiServerPort))
        else:               msg = (False, msg0 + "of OS.Error: {}".format(e.errno))

    except Exception as e:
        msg = (False, "Unexpected Failure - WiFiServer could not be started")
        exceptPrint(e, msg)

    WiFiServerThreadStop        = False
    WiFiServerThread            = threading.Thread(target = WiFiServerThreadTarget)
    WiFiServerThread.daemon     = True   # must come before daemon start: makes threads stop on exit!
    WiFiServerThread.start()

    return msg


def WiFiServerThreadTarget():
    """Thread constantly triggers web readings"""

    fncname = "WiFiServerThreadTarget: "

    while not WiFiServerThreadStop:
        WiFiServer.handle_request()
        # time.sleep(0.005)
        time.sleep(0.01)


def terminateWiFiServer():
    """stop and close Web server"""

    global WiFiServerThreadStop

    fncname = "terminateWiFiServer: "

    WiFiServerThreadStop = True
    WiFiServer.server_close()

    return "Terminate WiFiServer: Done"


class MyHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        """replacing the log_message function"""

        global dogetmsg, color

        # output:  ... LogMsg: GET /?ID=GeigerLog&M=10&S=11&M1=12&S1=13&M2=14&S2=15&M3=16&S3=17&T=18&P=19&H=20&X=21 HTTP/1.1, 302, -
        strarg = ", ".join(args)    # count(args) = 3 (except on errors)

        if color == TYELLOW:    dprint("WiFiServer LogMsg: ", strarg, dogetmsg)


class MyServer(MyHandler):

    def do_GET(self):
        """'do_GET' overwrites class function"""

        global dogetmsg, color

        fncname  = "WiFiServer do_GET: "
        dogetmsg = ""
        color    = TDEFAULT

        # dprint(fncname + "self.path: ", self.path)

        # if thread stopped this is the last dummy call to close the server
        if WiFiServerThreadStop:
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
            # same as lastdata
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
            answer      = "{} {}".format(DisplayName, __version__)
            bdata       = bytes(answer, "UTF-8")

            myheader    = "Content-type", "text/plain; charset=utf-8"
            mybytes     = bdata
            myresponse  = 200


        # reset
        elif self.path == "/GL/reset":
            answer      = resetDevices()
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

        # page not found 404 error
        else:
            # get calling system from self.headers["User-Agent"]:
            #   self.headers["User-Agent"] from Python:      BaseHTTP/0.6 Python/3.9.4
            #   self.headers["User-Agent"] from GMC counter: None
            #   self.headers["User-Agent"] from Firefox:     Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0
            #   self.headers["User-Agent"] from Chromium:    Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36
            # dprint("self.headers['User-Agent']: ", self.headers["User-Agent"])

            color    = TYELLOW
            if self.headers["User-Agent"] is None or "Python" in self.headers["User-Agent"]:
                answer   = "404 Page not found"
                myheader = 'Content-Type', "text/plain" # PLAIN

            else:
                answer   = "<!DOCTYPE html><style>html{text-align:center;}</style><h1>404 Page not found</h1>"
                myheader = 'Content-Type', "text/html"  # HTML

            dogetmsg   = "{} | {}{} {}".format(color, fncname, answer, TDEFAULT)

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
    get the data as byte sequence in the CSV form needed by GeigerLog
    avg   : The data as average over the last avg seconds; avg > 0
    return: data as CSV: M, S, M1, S1, M2, S2, M3, S3, T, P, H, X (must have 11 commas)
      like:              b'1733.0,36.0,1884.7,30.2,34.0,34.2,34.0,0.0,34.0,32.3,32.0,2.0'
    """
    # NOTE: avg is ignored in this demo

    global index

    start    = time.time()
    fncname  = "getDataCSV: "
    index   += 1

    lastrec = ""
    for vname in VarNames:
        # all poisson values are integer
        if   vname == "CPM":    value = np.random.poisson(10)
        elif vname == "CPS":    value = np.random.poisson(10/60)
        elif vname == "CPM1st": value = np.random.poisson(100)
        elif vname == "CPS1st": value = np.random.poisson(100/60)
        elif vname == "CPM2nd": value = np.random.poisson(200)
        elif vname == "CPS2nd": value = np.random.poisson(200/60)
        elif vname == "CPM3rd": value = np.random.poisson(300)
        elif vname == "CPS3rd": value = np.random.poisson(300/60)
        elif vname == "Temp":   value = np.random.poisson(20)
        elif vname == "Press":  value = np.random.poisson(1000)
        elif vname == "Humid":  value = np.random.poisson(90)
        elif vname == "Xtra":   value = np.random.poisson(55)

        lastrec += "{:8.8g}, ".format(value)

    lastrec = lastrec[:-2]                  # remove final ", "

    duration = 1000 * (time.time() - start) # ms
    appendLogfile("{:7d}, {:23s}, {}, {:8.3f}\n".format(index, longstime(), lastrec, duration))

    vprint("DemoWiFiServer: {:125s}  dur:{:0.2f} ms".format(lastrec, duration))
    lastrec = lastrec.replace(" ", "")      # remove all blanks

    return bytes(lastrec, "UTF-8")          # no comma at the end!


def resetDevices():
    """resets devices"""

    msg = "Fake Reset Done"
    vprint(msg)
    return msg


def writeLogfile(msg):
    """Make new file, or empty old one, then write msg to file"""

    if Logfile == "":
        # no writing if filename is empty
        dprint("{:33s} : {}".format("Init Logfile", "Logfile will NOT be written"))

    else:
        # make logfile if filename is defined
        try:
            with open(Logfile, 'w') as log:
                log.write(msg)
            dprint("{:33s} : {}".format("Init Logfile",  "Ok, Logfile is: '{}'".format(Logfile)))

        except Exception as e:
            exceptPrint(e, "")
            msg = "Logfile '{}': Could NOT be written!".format(Logfile)
            dprint(msg)


def appendLogfile(msg):
    """append msg to the end of file"""

    if Logfile > "":  # no writing if filename is empty
        try:
            with open(Logfile, 'a') as log:
                log.write(msg)
        except:
            pass


def main():

    # verify Python version is >= v3.7 (needed for HTTP server)
    svi = sys.version_info
    if svi < (3, 7):
        print("This software requires Python Version 3.7 or later.")
        print("Your Python version is Version {}.{}.{} .".format(svi[0], svi[1], svi[2]))
        print("Cannot continue, will exit.")
        return

    # print system docu
    print("=" * 150)
    dprint("{:33s} : {}".format("Version of {}".format(__script__), __version__))
    dprint("{:33s} : {}".format("Version of Python", sys.version.split(" ")[0]))
    dprint("{:33s} : {}".format("Version of Operating System", platform.platform()))
    dprint("{:33s} : {}, {}".format("Machine, Architecture", platform.machine(), platform.architecture()[0]))

    # init the WiFi Server
    WSsuccess, WSresponse = initWiFiServer()
    if WSsuccess:
        dprint("{:33s} : {}".format("Init WiFi Server",        WSresponse))
    else:
        dprint("{:33s} : {}".format("Init WiFi Server FAILED", WSresponse))
        return

    # init logfile
    msg  = "# Log file created with: '{}', Version: {}\n".format(__script__, __version__)
    msg += "# Python Version:   {}\n".format(sys.version.replace('\n', ""))
    msg += "# Operating System: {}\n".format(platform.platform())
    msg += "# Machine, Arch:    {}, {}\n".format(platform.machine(), platform.architecture()[0])
    msg += "# Index,                DateTime,      CPM,      CPS,   CPM1st,   CPS1st,   CPM2nd,   CPS2nd,   CPM3rd,   CPS3rd,     Temp,    Press,    Humid,     Xtra,   Duration[ms]\n"
    writeLogfile(msg)
    print()

    # Loop until CTRL-C
    while True:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            print()
            dprint(terminateWiFiServer())
            return


if __name__ == '__main__':
    main()
    dprint("Exiting {}".format(__script__))

    print()
