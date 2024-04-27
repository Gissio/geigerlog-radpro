#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
gsup_utils.py - GeigerLog utilities with imports

include in programs with:
    from gsup_utils include *
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


# Function names:
# print(fncname)
# print(__name__) # gibt modul namen, like 'util'
# print(sys._getframe().f_code.co_name) # gibt korrekten Namen der Funktion

# get extensive output on crashes
# python3 -q -X faulthandler

# grep -inRsH "Text to be searched"  /path/to/dir (it can be '.')
#     i stands for ignore case distinctions
#     R stands for recursive and it also include symlinks. Better to use 'R' instead 'r'
#     n stands for "it will print line number".
#     s stands for "suppress error messages"
#     H stands for "it will print the file name for each match"

# install Python from source
# https://docs.rstudio.com/resources/install-python-source/

# "I wrote a Python script to automatically convert short-form PyQt5-style enums into
# fully qualified names. I thought it could be interesting to share:"
# https://stackoverflow.com/a/72658216/6178507


#
# modules - available in std Python
#
import sys, os, io, time, datetime  # basic modules
import zipfile                      # creation of zip files
import warnings                     # warning messages
import platform                     # info on OS, machine, architecture, ...
import traceback                    # for traceback on error; used in: exceptPrint
import inspect                      # finding origin of f'on calls
import copy                         # make shallow and deep copies
import threading                    # higher-level threading interfaces
import queue                        # queue for threading
import re                           # regex
import configparser                 # parse configuration file geigerlog.cfg
import urllib.request               # for web requests(AmbioMon, Radiation World Map, WiFiServer, ...)
import urllib.parse                 # for use with Radiation World Map
import urllib.error                 # needed extra?
import struct                       # packing numbers into chars (needed by gdev_gmc.py)
import sqlite3                      # sudo -H pip3 install  pysqlite3; but should be part of python3 (needed by gsup_sql.py)
import getopt                       # parse command line for options and commands
import signal                       # handling signals like CTRL-C and other
import subprocess                   # to allow terminal commands tput rmam / tput smam
import socket                       # finding IP Adress
import http.server                  # web server
import ssl                          # for secure SSL server used in MonServer
import shutil                       # for copying files

from collections import deque       # used for queuing log data
# from pathlib import Path            # contains "touch" used for autostart options

#
# modules - requiring installation via pip
#
import serial                       # make it a required installation, since serial.tools.list_ports is anyway
import serial.tools.list_ports      # allows listing of serial ports and searching within; needed by *getSerialConfig, getPortList
import sounddevice       as sd      # sound output & input
import soundfile         as sf      # handling sound files; can read and write
import numpy             as np      # scientific computing with Python
import scipy                        # all of scipy
import scipy.signal                 # a subpackage of scipy; needs separate import
import scipy.stats                  # a subpackage of scipy; needs separate import
import scipy.optimize               # needed for deadtime correction with paralysation

try:    import psutil               # to get CPU info
except: pass


# PyQt - install via pip, but sometimes must use distribution package manager
from PyQt5.QtWidgets                import *
from PyQt5.QtGui                    import *
from PyQt5.QtCore                   import *
from PyQt5.QtPrintSupport           import *


# matplotlib importing and settings
import matplotlib                               # Visualization with Python
matplotlib.use('Qt5Agg', force=False)           # use Qt5Agg, not the default TkAgg
import matplotlib.backends.backend_qt5agg       # MUST be done BEFORE importing pyplot! requires PyQt!
from   matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg    as FigureCanvas
from   matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import matplotlib.pyplot    as plt              # MUST import AFTER 'matplotlib.use()'
import matplotlib.dates     as mpld
import matplotlib.animation as mplanim
import matplotlib.patches   as mpat


# next lines are better done in other code,
# matplotlib.pyplot.figure(num=None, figsize=None, dpi=None, ...)
# dpi ersetzen mit dpi of current screen, see gmain.py lines HiDPI et al.

#~matplotlib.rcParams['figure.figsize']     = [8.0, 6.0]
#~matplotlib.rcParams['figure.dpi']         = 50
#~matplotlib.rcParams['savefig.dpi']        = 100
#~matplotlib.rcParams['font.size']          = 12
#~matplotlib.rcParams['legend.fontsize']    = 'large'
#~matplotlib.rcParams['figure.titlesize']   = 'medium'

#~print(matplotlib.rcParams['figure.figsize'])
#~print(matplotlib.rcParams['figure.dpi'])
#~print(matplotlib.rcParams['savefig.dpi'])
#~print(matplotlib.rcParams['font.size'])
#~print(matplotlib.rcParams['legend.fontsize'])
#~print(matplotlib.rcParams['figure.titlesize'])

import gglobs                               # all global vars


#
# Getting Version numbers
#
# # Getting the version numbers of Qt, SIP and PyQt:
# # https://wiki.python.org/moin/PyQt/Getting%20the%20version%20numbers%20of%20Qt%2C%20SIP%20and%20PyQt
#     from PyQt4.QtCore     import QT_VERSION_STR
#     from PyQt4.Qt         import PYQT_VERSION_STR
#     from sip              import SIP_VERSION_STR
#     print("Qt version:",  QT_VERSION_STR)
#     print("SIP version:", SIP_VERSION_STR)
#     print("PyQt version:",PYQT_VERSION_STR)
#
# sqlite3.version:                The version number of this module, as a string. This is not the version of the SQLite library.
# sqlite3.version_info:           The version number of this module, as a tuple of integers. This is not the version of the SQLite library.
# sqlite3.sqlite_version:         The version number of the run-time SQLite library, as a string.
# sqlite3.sqlite_version_info:    The version number of the run-time SQLite library, as a tuple of integers.
#
# Use of pkg_resources is discouraged in favor of importlib.resources, importlib.metadata,
# and their backports (resources, metadata).
#   import pkg_resources
#   setuptools_version = pkg_resources.get_distribution('setuptools').version

notfound            = "Not found"
pyqt5sip_version    = notfound
ntplib_version      = notfound
setuptools_version  = notfound
pip_version         = notfound

if sys.version_info >= (3, 8):    # only Python version >= v3.8
    import importlib.metadata

    try:    pyqt5sip_version    = importlib.metadata.version('PyQt5-sip')
    except: pass

    try:    ntplib_version      = importlib.metadata.version('ntplib')
    except: pass

    try:    setuptools_version  = importlib.metadata.version('setuptools')
    except: pass

    try:    pip_version         = importlib.metadata.version('pip')
    except: pass

else:
    from pip            import __version__          as pip_version


from sip import SIP_VERSION_STR

gglobs.versions                         = {}
gglobs.versions["GeigerLog"]            = gglobs.__version__
gglobs.versions["Python"]               = sys.version.replace('\n', "")
gglobs.versions["pip"]                  = pip_version
gglobs.versions["setuptools"]           = setuptools_version

gglobs.versions["PyQt"]                 = PYQT_VERSION_STR
gglobs.versions["PyQt-Qt"]              = QT_VERSION_STR
gglobs.versions["PyQt-sip"]             = pyqt5sip_version
gglobs.versions["SIP"]                  = SIP_VERSION_STR

gglobs.versions["matplotlib"]           = matplotlib.__version__
gglobs.versions["matplotlib backend"]   = matplotlib.get_backend()
gglobs.versions["numpy"]                = np.__version__
gglobs.versions["numpy float-errors"]   = np.geterr()                       # Get the current way of handling floating-point errors.
gglobs.versions["scipy"]                = scipy.__version__

gglobs.versions["sqlite3 module"]       = sqlite3.version
gglobs.versions["sql3lib library"]      = sqlite3.sqlite_version

gglobs.versions["sounddevice"]          = sd.__version__
gglobs.versions["SoundFile"]            = sf.__version__
gglobs.versions["PortAudio"]            = sd.get_portaudio_version()
gglobs.versions["pyserial"]             = serial.__version__

udul = "undefined until loaded"

gglobs.versions["paho-mqtt"]            = udul    # paho.mqtt.__version__
gglobs.versions["LabJackPython"]        = udul    # LabJackPython.__version__
gglobs.versions["U3"]                   = udul    # this has no version!
gglobs.versions["EI1050"]               = udul    # ei1050.__version__
gglobs.versions["ntplib"]               = udul    # ntplib_version


# colors for the terminal (do not put in gglobs, as this would require 'gglobs.' prefix!)
# https://gist.github.com/vratiu/9780109
# https://stackoverflow.com/questions/5947742/how-to-change-the-output-color-of-echo-in-linux
# '90' values are supposed to be high intensity
TDEFAULT            = '\033[0m'             # default, i.e greyish
TRED                = '\033[91m'            # red
TGREEN              = '\033[92m'            # light green
TYELLOW             = '\033[93m'            # yellow
TBLUE               = '\033[94m'            # blue (dark)
TMAGENTA            = '\033[95m'            # magenta
TCYAN               = '\033[96m'            # cyan
TWHITE              = '\033[97m'            # high intensity white

INVMAGENTA          = '\033[45m'            # invers magenta looks ok
INVBOLDMAGENTA      = '\033[45;1m'          # invers magenta with bold white

# BOLDxyz are brighter colors
BOLDRED             = '\033[91;1m'          # bold red
BOLDGREEN           = '\033[92;1m'          # bold green
BOLDYELLOW          = '\033[93;1m'          # bold yellow
BOLDBLUE            = '\033[94;1m'          # bold blue
BOLDMAGENTA         = '\033[95;1m'          # bold magenta
BOLDCYAN            = '\033[96;1m'          # bold cyan
BOLDWHITE           = '\033[97;1m'          # bold white

# UNDERLINE         = '\033[4m'             # underline
# BOLDREDUL         = '\033[31;1;4m'        # bold, red, underline, low intens?
# BOLDREDUL         = '\033[91;1;4m'        # bold, red, underline, high intens?
# BOLDRED           = '\033[31;1m'          # bold, red, (low intens?)

if "WINDOWS" in platform.platform().upper():# no terminal colors on Windows
    TDEFAULT        = ""                    # normal printout
    TRED            = ""                    # (dark) red
    TGREEN          = ""                    # hilite message
    TYELLOW         = ""                    # error message
    TBLUE           = ""                    #
    TMAGENTA        = ""                    # devel message
    TCYAN           = ""                    # devel message
    TWHITE          = ""                    # unused

    INVMAGENTA      = ""                    # devel message
    INVBOLDMAGENTA  = ""                    # unused

    BOLDRED         = ""                    # devel message
    BOLDGREEN       = ""                    # devel message
    BOLDYELLOW      = ""                    #
    BOLDBLUE        = ""                    #
    BOLDMAGENTA     = ""                    # unused
    BOLDCYAN        = ""                    #
    BOLDWHITE       = ""                    #

gglred              = gglobs.GooColors[0]   # Google colors
gglyellow           = gglobs.GooColors[1]
gglgreen            = gglobs.GooColors[2]
gglblue             = gglobs.GooColors[3]


# Devices columns naming - doing it here allows for shorter names w/o 'gglobs'
DNAME               = gglobs.DNAME          # = 0 : Device Name as Detected
VNAME               = gglobs.VNAME          # = 1 : Variables associated with this device
ACTIV               = gglobs.ACTIV          # = 2 : Device is activated in config
CONN                = gglobs.CONN           # = 3 : Device is connected

# seed the random number generator with a develish sequence
np.random.seed(666666)

# define the queus
gglobs.logMemDataDeque = deque()            # datalist to be saved to memory
gglobs.logLogPadDeque  = deque()            # text to be shown on LogPad after a Log roll


def getProgName():
    """Return program_base, i.e. 'geigerlog' even if named 'geigerlog.py' """

    progname          = os.path.basename(sys.argv[0])
    progname_base     = os.path.splitext(progname)[0]

    return progname_base


def getProgPath():
    """Return full path of the program directory"""

    # +++ TEST
    # Patch for packaging geigerlog with pyinstaller:
    #
    # dp = os.path.dirname(os.path.realpath(__file__))
    #
    dp = os.getcwd()
    # +++ TEST
    return dp


def getDataPath():
    """Return full path of the data directory"""

    dp = os.path.join(getProgPath(), gglobs.dataDirectory)
    return dp


def getGresPath():
    """Return full path of the resource (icons, sounds) directory"""

    dp = os.path.join(getProgPath(), gglobs.gresDirectory)
    return dp


def getWebPath():
    """Return full path of the web (html, js) directory"""

    dp = os.path.join(getProgPath(), gglobs.webDirectory)
    return dp


def getProglogPath():
    """Return full path of the geigerlog.proglog file"""

    dp = os.path.join(gglobs.dataPath, gglobs.progName + ".proglog")
    return dp


def getStdlogPath():
    """Return full path of the geigerlog.stdlog file"""

    dp = os.path.join(gglobs.dataPath, gglobs.progName + ".stdlog")
    return dp


def getConfigPath():
    """Return full path of the geigerlog.cfg file"""

    dp = os.path.join(gglobs.progPath, gglobs.progName + ".cfg")
    return dp


def stime():
    """Return current time as YYYY-MM-DD HH:MM:SS"""

    # sollte beides gehen:
    #       return time.strftime("%Y-%m-%d %H:%M:%S")
    #       return longstime()[:-4]

    return time.strftime("%Y-%m-%d %H:%M:%S")                               # 1 sec resolution


def medstime():
    """Return current time as HH:MM:SS.m, (m= 100 millisec)"""

    return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-5]             # 100 ms resolution


def longstime():
    """Return current time as YYYY-MM-DD HH:MM:SS.mmm, (mmm=millisec)"""

    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]    # 1 ms resolution


def datestr2num(string_date):
    """convert a Date&Time string in the form YYYY-MM-DD HH:MM:SS to a Unix timestamp in sec"""

    #print("datestr2num: string_date", string_date)
    try:    dt=time.mktime(datetime.datetime.strptime(string_date, "%Y-%m-%d %H:%M:%S").timetuple())
    except: dt = 0

    return dt


def num2datestr(timestamp):
    """convert a Unix timestamp in sec to a Date&Time string in the form YYYY-MM-DD HH:MM:SS"""

    dt = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    # print("num2datestr: timestamp", timestamp, ", dt: ", dt)

    return dt


def sortDict(myDict):
    """sorts a dict by key"""

    return dict(sorted(myDict.items()))


def clamp(n, minn, maxn):
    """limit return value to be within minn and maxn, including"""

    return min(max(n, minn), maxn)


def IntToChar(intval):

    if intval < 128 and intval > 31:    char = chr(intval)
    else:                               char = " "

    return char


def BytesAsASCII(bytestring):
    """convert a bytes string into a string which has ASCII characters when
    printable and '.' else, with spaces every 10 bytes"""

    if bytestring is None: return ""

    asc = ""
    for i in range(0, len(bytestring)):
        a = bytestring[i]
        if a < 128 and a > 31:  asc += chr(bytestring[i])
        else:                   asc += "."

        if ((i + 1) % 10) == 0: asc += "  "
        if ((i + 1) % 50) == 0: asc += "\n"

    return asc


def BytesAsASCIIFF(bytestring):
    """convert a bytes string into a string which has ASCII characters when
    printable and '.' else, with spaces every 10 bytes"""

    if bytestring is None: return ""

    asc = "  0:0x000   "
    for i in range(0, len(bytestring)):
        a = bytestring[i]
        if   a < 128 and a > 31:    asc += chr(bytestring[i])
        elif a == 255:              asc += "F"
        else:                       asc += "."

        if ((i + 1) % 10) == 0: asc += "    "
        if ((i + 1) % 50) == 0: asc += "\n{:3d}:0x{:03X}   ".format(i + 1, i + 1)

    return asc


def BytesAsHex(bytestring):
    """convert a bytes string into a str of Hex values, with dash spaces
    every 10 bytes and LF every 50"""

    bah = ""
    if bytestring is None: return bah

    bah += "{:3n}:0x{:03X}  ".format(0, 0)
    for i in range(0, len(bytestring)):
        bah += "{:02X} ".format(bytestring[i])

        if   ((i + 1) % 50) == 0 :
            bah += "\n"  # no '- '
            bah += "{:3n}:0x{:03X}  ".format(i + 1, i + 1)
        elif ((i + 1) % 10) == 0 :
            bah += "- "

    return bah


def BytesAsDec(bytestring):
    """convert a bytes string into a str of Dec values, with dash spaces
    every 10 bytes and LF every 50"""

    bad = ""
    if bytestring is None: return bad

    bad += "         |" + ("-"*39 + "|") * 5 + "\n"
    bad += "{:3n}:0x{:03X} ".format(0, 0)
    for i in range(0, len(bytestring)):
        bad += "{:3d} ".format(bytestring[i])
        if   ((i + 1) % 50) == 0 :
            bad += "\n"  # no '- '
            bad += "{:3n}:0x{:03X} ".format(i + 1, i + 1)
        elif ((i + 1) % 10) == 0 :
            bad += ""

    return bad


def convertB2Hex(bseq):
    """Convert bytes sequence to Hex string"""

    return "{:25s} == ".format(str(bseq)) + "".join("{:02X} ".format(arg) for arg in bseq)


def orig(thisfile):
    """Return name of calling program and line number of call
    requires that this routine is called by orig(__file__)"""

    lineno = inspect.currentframe().f_back.f_lineno     # get the current line number
    fn     = os.path.basename(thisfile)

    #print "orig:", inspect.currentframe().__name__
    #print "orig:", inspect.getmembers()
    #print "orig:", sys._getframe(1).f_code.co_name

    return fn, sys._getframe(1).f_code.co_name, lineno


def header(txt):
    """position txt within '==...==' string"""

    return "<br>==== {} {}".format(txt, "=" * max(1, (80 - len(txt))))


def logPrint(arg):
    """print arg into logPad"""

    gglobs.logPad.append(arg)


def efprint(*args, debug=False):
    """error fprint with err sound"""

    fprint(*args, error="ERR", errsound=True)


def qefprint(*args, debug=False):
    """quiet error fprint, error color but no errsound"""

    fprint(*args, error="ERR", errsound=False)


#xyz
def fprintInColor(text, color):
    """print to notepad a single line text in color using implied HTML coding"""

    # use allowed colors only
    colortuple = ("black", "red", "orange", "yellow", "green", "blue", "magenta", "purple", "violet", gglred, gglgreen, gglyellow, gglblue)
    if not color in colortuple:  color = "black"

    newtext = "<span style='color:{};'>{}</span>".format(color, text)

    gglobs.notePad.append(newtext)


def fprint(*args, error="", errsound=False):
    """print all args into the notePad; print in red on error"""

    #### local    #######################################################
    def getColorText(item):
        if   "<blue>"  in item: color = "blue"
        elif "<red>"   in item: color = "red"
        elif "<green>" in item: color = "green"
        else:                   color = "black"

        # text = item.replace(f"<{color}>", "").replace(f"</{color}>", "")
        text = item.replace("<{}>".format(color), "").replace("</{}>".format(color), "")
        text = "{:30s}".format(text).replace(" ", "&nbsp;")

        return (color, text)
    #### end local #######################################################

    if errsound:  playWav("err")

    # handle the leftmost arg
    arg0      = str(args[0])
    splitarg0 = arg0.strip("\n").split("\n")

    if len(splitarg0) == 1:
        # the arg0 is only a single line item, perhaps followed
        # by other args for printing in the same line
        for item in splitarg0:
            color, text = getColorText(item)
            if error == "ERR":      color = "red"   # override the color on errorflag

        # add any other args beyond arg0
        for s in range(1, len(args)):   text += str(args[s]).replace(" ", "&nbsp;")

        # print 1 full line in all same color
        fprintInColor(text, color)

    else:
        # when arg0 is multiline, there MUST NOT be any other args following!
        for item in splitarg0:
            color, text = getColorText(item)
            if error == "ERR":      color = "red"   # override the color on errorflag

            # print each line individually in its color
            fprintInColor(text, color)              # complete line all in same color

    # gglobs.notePad.ensureCursorVisible()      # works by moving text to left, so that
                                                # cursor on right-most position becomes visible.
                                                # then requires moving text to left; not helpful
                                                # also: when text is scrolled upwards, new text
                                                # does not become visible!

    # jump to the end of text --> new text will always become visible
    gglobs.notePad.verticalScrollBar().setValue(gglobs.notePad.verticalScrollBar().maximum())


def commonPrint(ptype, *args, error=""):
    """Printing function to dprint, vprint, wprint, and xdprint
    ptype : DEBUG, VERBOSE, werbose, DEVEL
    args  : anything to be printed
    error : "" or ERR or color codeword
    return: nothing
    """

    if ptype == "DEVEL" and not gglobs.devel: return  # no printing DEVEL unless gglobs.devel is true

    gglobs.xprintcounter += 1                         # the count of dprint, vprint, wprint, xdprint commands
    tag = ""
    for arg in args: tag += str(arg)

    # if args is empty, write blank line to terminal and log file
    # and return
    if tag == "":
        writeFileA(gglobs.proglogPath, "")
        print()
        return

    tag0 = "{:23s} {:7s}: {:.>6d} ".format(longstime(), ptype, gglobs.xprintcounter) + gglobs.debugIndent
    tag  = tag0 + tag

    # last resort: any "\x00" in text files results in geany (and others)
    # not being able to open the file
    # replace with "?"
    if "\x00" in tag: tag = tag.replace("\x00", "?")

    # shorttag = tag[8:]   # for the terminal shorten the datetime to show day + time only
    if   error == "":         col = ("",            "")
    elif error == "ERR":      col = (TYELLOW,       TDEFAULT)
    elif error == "yellow":   col = (TYELLOW,       TDEFAULT)
    elif error == "green":    col = (TGREEN,        TDEFAULT)
    elif error == "cyan":     col = (TCYAN,         TDEFAULT)
    elif error == "magenta":  col = (INVMAGENTA,    TDEFAULT)
    elif error == "red":      col = (BOLDRED,       TDEFAULT)    # TRED  ist zu dunkel
    else:                     col = (TDEFAULT,      "")

    # colend = "" if col == "" else TDEFAULT
    print(col[0] + tag[8:] + col[1])   # for the terminal shorten the datetime to show day + time only

    # remove any color code from the tag to be written to file
    # \x1B = ESC, codes like:  ['\x1B[0m', '\x1B[96m', ...
    if "\x1B" in tag:
        codes = ['[0m', '[96m', "[92;1m41", "[92;1m30", "[92m", "[91;1m41", "[91;1m30", "[91m", "[91;1m", ]
        for c in codes:     tag = tag.replace("\x1B" + c, "")

    # append to file *.proglog
    writeFileA(gglobs.proglogPath, tag)


def wprint(*args, forcewerbose=False):
    """werbose print:
    if werbose is true then:
    - Write timestamp and args as a single line to progname.proglog file
    - Print args as single line
    else
    - do nothing
    """
    if forcewerbose or gglobs.werbose: commonPrint("werbose", *args)


def vprint(*args, forceverbose=False):
    """verbose print: if forceverbose or gglobs.verbose is true then:
            - Write timestamp and args as a single line to progname.proglog file
            - Print args as single line
    else
            - do nothing
    """
    if forceverbose or gglobs.verbose: commonPrint("VERBOSE", *args)


def dprint(*args, debug=False ):
    """debug print:
    if debug or gglobs.debug is true then:
    - Write timestamp and args as a single line to progname.proglog file
    - Print args as single line
    else
    - do nothing
    """
    if debug or gglobs.debug: commonPrint("DEBUG", *args)


#print as debug error yellow
def edprint(*args, debug=True):
    """debug print in error yellow"""

    commonPrint("DEBUG", *args, error="ERR")


#print in yellow
def ydprint(*args, debug=True):
    """debug print"""

    commonPrint("DEVEL", *args, error="yellow")


# print in green
def gdprint(*args, debug=True):
    """debug print"""

    commonPrint("DEVEL", *args, error="green")


# print in cyan
def cdprint(*args, debug=True):
    """debug print"""

    commonPrint("DEVEL", *args, error="cyan")


# print in magenta
def mdprint(*args, debug=True):
    """debug print"""

    commonPrint("DEVEL", *args, error="magenta")


# print in red
def rdprint(*args, debug=True):
    """debug print"""

    commonPrint("DEVEL", *args, error="red")


# print into print queue
def Queueprint(text):
    """print into print queue; printing occurs in runCheckCycle(self)"""

    gglobs.ThreadMsg += text + "\n"


def arrprint(text, array):
    """ prints an array """

    print(text)
    for a in array: print("{:10s}: ".format(a), array[a])


def exceptPrint(e, srcinfo):
    """Print exception details (errmessage, file, line no)"""

    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname                     = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]    # which file?

    edprint("EXCEPTION: {} ({}) in file: {} in line: {}".format(srcinfo, e, fname, exc_tb.tb_lineno))
    if gglobs.traceback:
        ydprint(traceback.format_exc(), debug=True) # print on devel plus trace only


def setIndent(arg):
    """increases or decreased the indent of debug/verbose print"""

    if arg > 0:  gglobs.debugIndent += "   "
    else:        gglobs.debugIndent  = gglobs.debugIndent[:-3]


def cleanHTML(text):
    """replace < and > with printable chars"""

    return str(text).replace("<", "&lt;").replace(">", "&gt;")


def clearProgramLogFile():
    """To clear the ProgramLogFile at the beginning of each run"""

    # delete the geigerlog.proglog file
    try:    os.remove(gglobs.proglogPath)
    except: pass

    # delete the geigerlog.proglog.zip file
    try:    os.remove(gglobs.proglogPath + ".zip")
    except: pass

    # make 1st line
    # "Mµßiggang ist auch ein ° von Läßterei"
    tag  = "{:23s} PROGRAM: pid:{:d} ########### {:s}  ".format(longstime(), os.getpid(), "GeigerLog {} -- mit no meh pfupf underm füdli !".format(gglobs.__version__))
    line = tag + "#" * 30

    # print and log 1st line
    # create geigerlog.proglog file only on debug or devel
    if gglobs.debug or gglobs.devel:
        writeFileW(gglobs.proglogPath, line )    # goes to *.proglog
        print(TGREEN + line + TDEFAULT)          # goes to terminal; in green if Linux


def readBinaryFile(path):
    """Read all of the file into data; return data as bytes"""

    fncname = "readBinaryFile: "
    # print(fncname + "path: {} ".format(path))

    try:
        with open(path, 'rb') as f:
            data = f.read()
    except Exception as e:
        data = b''
        srcinfo = "ERROR reading file"
        exceptPrint(fncname + str(e), srcinfo)
        data = b"ERROR: Could not read file: " + str.encode(path)

    vprint(fncname + "len:{}, data[:30]: ".format(len(data)), data[0:30])

    return data


def writeBinaryFile(path, data):
    """Create file and write data to it as binary"""

    fncname = "writeBinaryFile: "

    # print(fncname + "path: {}".format(path))

    try:
        with open(path, 'wb') as f:
            f.write(data)
    except Exception as e:
        exceptPrint(e, fncname + "FAILURE when writing file")


def writeFileW(path, writestring, linefeed=True):
    """Force a new file creation, emptying it if already existing, then write
    to it if writestring is not empty; add linefeed unless linefeed=False"""

    fncname = "writeFileW: "

    # print(fncname + "path: {}  writestring: {}  linefeed: {}".format(path, writestring, linefeed))

    try:
        with open(path, 'wt', encoding="UTF-8", errors='replace', buffering = 1) as f:
            if writestring > "":
                if linefeed: writestring += "\n"
                f.write(writestring)
    except Exception as e:
        exceptPrint(e, fncname + "Failure when writing file")


#xyz
def writeFileA(path, writestring):
    """Append data to file after adding linefeed; add to a zip file if exceeding certain file size"""

    fncname = "writeFileA: "

    # print(fncname + "path:        {}\n            writestring: {}".format(path, writestring))

    # the blocking period happens about once per day and lasts for under 1 ms
    blockstart = time.time()
    while gglobs.LogFileAppendBlocked:
        if gglobs.devel:
            fulltime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f") # with microsec
            msg = fulltime + " " + fncname + "Waiting for Block-release"
            Queueprint("DVL " +  msg)
            try:
                with open(path, 'at', encoding="UTF-8", errors='replace', buffering=-1) as f:
                    f.write(msg + "\n")
            except Exception as e:
                print(TYELLOW + "EXCEPTION: " + msg, e, TDEFAULT)
                # playSingleSine(3)

        maxBlockTime = 0.1
        if time.time() - blockstart > maxBlockTime:
            msg = longstime() + " " + fncname + "Waiting for Block-release takes too long; broke after {} sec".format(maxBlockTime)
            try:
                with open(path, 'at', encoding="UTF-8", errors='replace', buffering=-1) as f:
                    f.write(msg + "\n")
            except Exception as e:
                print(TYELLOW + "EXCEPTION: " + msg, e, TDEFAULT)

            return
        time.sleep(0.001)

    # append writestring to file
    #   duration of append: less than 0.5 ms
    try:
        with open(path, 'at', encoding="UTF-8", errors='replace', buffering=-1) as f:
            f.write(writestring + "\n")
    except Exception as e:
        print(TYELLOW + longstime()[8:], "EXCEPTION in WriteFileA appending: ", e, TDEFAULT)

    # get file size
    try:
        FileSize = os.path.getsize(path)
    except Exception as e:
        print(TYELLOW + longstime()[8:], "EXCEPTION in WriteFileA getsize of file: ", e, TDEFAULT)
        FileSize = 0

    # ZIP file and append to ZIP archive when file reaches limit
    # LimitFileSize = 500000
    LimitFileSize = 1E6
    if FileSize > LimitFileSize:
        try:
            duration = saveZIPfile(path)
        except Exception as e:
            print(TYELLOW + longstime()[8:], "EXCEPTION in WriteFileA saveZIPfile: ", e, TDEFAULT)
            duration = 0

        msg = longstime() + " " * 7 + fncname + "ZIP duration: {:0.3f} ms".format(duration)
        print(BOLDRED + msg + TDEFAULT)

        # write ZIP duration msg to fresh log file
        writeFileA(path, msg + "\n")


def saveZIPfile(path):
    """creates a ZIP file of the current geigerlog.proglog file, and
    appends it to any existing geigerlog.proglog.zip file"""

    # duration of saving ZIP file:
    #  1 ...  3 ms für  10k portions; avg ~ 1.2 ms
    #  1 ...  4 ms für  15k portions; avg ~ 1.3 ms
    #  3 ...  7 ms für  50k portions; avg ~ 4 ms
    #  7 ... 17 ms für 100k portions; avg ~12 ms
    # 30 ... 40 ms für 500k portions; avg ~34 ms
    # 30 ...125 ms für 500k portions; avg ~38 ms StdDev=12 ms

    zipstart = time.time()

    fncname = "saveZIPfile: "

    # flush, copy, and reset
    #   flush buffer into geigerlog.proglog,
    #   copy to tmp file,
    #   reset proglog file.
    #   all takes 0.5 ... 2 ms, avg=1 ms
    gglobs.LogFileAppendBlocked = True
    #
    tmppath = path + ".tmp"
    with open(path, 'at') as f: f.flush()       # flush proglog file
    shutil.copyfile(path, tmppath)              # copy  proglog file to tmp file
    writeFileW(path, "", linefeed=True)         # reset proglog file
    #
    gglobs.LogFileAppendBlocked = False

    # zip
    #   the tmppath file, and append to zipped log archive
    #   A value of 1 (Z_BEST_SPEED) is fastest and produces the least compression, while
    #   a value of 9 (Z_BEST_COMPRESSION) is slowest and produces the most compression.
    #   Write the file named tmppath to the archive, giving it the archive name arcname
    timestamp = stime().replace(":", "-").replace(" ", "_")     # short timestamp
    arcname   = "geigerlog.proglog-{}.log".format(timestamp)    # geigerlog.prolog portions separated by arcname in archive
    zippath   = path + ".zip"                                   # the archive file to be created
    with zipfile.ZipFile(zippath, 'a', zipfile.ZIP_DEFLATED, compresslevel=9) as zipObj:
        zipObj.write(tmppath, arcname=arcname)

    # remove tmp file
    try:    os.remove(tmppath)
    except: pass

    duration  = 1000 * (time.time() - zipstart)

    return duration


def isFileReadable(filepath):
    """is filepath readable"""

    #print("isFileReadable: filepath: {}".format(filepath))

    if not os.access(filepath, os.R_OK) :
        Queueprint("File  {} exists but cannot be read - check file permission".format(filepath))
        return False
    else:
        return True


def isFileWriteable(filepath):
    """As the dir can be written to, this makes only sense for existing files"""

    #print("isFileWriteable: filepath: {}".format(filepath))

    if os.path.isfile(filepath) and not os.access(filepath, os.W_OK) :
        Queueprint("File {} exists but cannot be written to - check permission of file".format(filepath))
        return False
    else:
        return True


def addMenuTip(var, text):
    """add both menu tip and status tip to an action"""

    # e.g.:   PlotLogAction.setStatusTip('Plot the Log file')
    #         PlotLogAction.setToolTip  ('Plot the Log file')
    #     --> addMenuTip(PlotLogAction, 'Plot the Log file')

    #print("addMenuTip:", var, text)
    var.setStatusTip(text)
    var.setToolTip(text)


def strFontInfo(origin, fi):
    """formats font information, returns string"""

    fontinfo = "Family:{}, fixed:{}, size:{}, style:{}, styleHint:{}, styleName:{}, weight:{}, exactMatch:{}"\
    .format(fi.family(), fi.fixedPitch(), fi.pointSize(), fi.style(), fi.styleHint(), fi.styleName(), fi.weight(), fi.exactMatch())

    return fontinfo


def printVarsStatus():
    """Print the current value of variables"""

    print(TDEFAULT) # reset to white color
    print( "\n============================================ Globals " + "-" * 100)
    g = globals()
    for name in g:
        if name[0] != "Q": # exclude Qt stuff
            print("name:     {:35s} =    {}".format(name, eval(name)))
    print(TDEFAULT) # reset to white color

    # gives only the locals in this printVarsStatus function
    #~print( "\n============================================= Locals " + "-" * 100)
    #~g = locals()
    #~for name in g:
        #~if name[0] != "Q":
            #~print("name:     {:35s} =    {}".format(name, eval(name)))
    #~print(TDEFAULT) # reset to white color


def html_escape(text):
    """Produce entities within text."""

    # when printing in error mode the < and > chars in the GMC commands may be
    # interpreted as HTML such that an b'<GETCPML>>' becomes a b'>' !

    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&apos;",
        ">": "&gt;",
        "<": "&lt;",
        }

    return "".join(html_escape_table.get(c, c) for c in text)


# def getOrderedVars(varlist):
#     """Prints a dict in the right order"""

#     ret = ""
#     for vname in gglobs.varsCopy:
#         ret += "{:>8s}:{:5s}".format(vname, str(varlist[vname])).strip() + "  "

#     return ret


def getNameSelectedVar():
    """Get the name of the variable currently selected in the drop-down box in
    the graph options"""

    vindex      = gglobs.exgg.select.currentIndex()
    vnameselect = list(gglobs.varsCopy)[vindex]
    #print("getNameSelectedVar: vindex, vnameselect:", vindex, vnameselect)

    return vnameselect


def playWav(wtype = "ok"):
    """Play a wav message, 'ok' --> Bip sound, everything else --> Burp sound"""

    fncname = "playWav: "

    if    wtype.lower() == "ok": path = os.path.join(gglobs.gresPath, 'bip2.wav') # wtype = "ok"
    else:                        path = os.path.join(gglobs.gresPath, 'burp.wav') # wtype = "err" or anything else

    # Play
    try:
        data, samplerate = sf.read(path)
        #print("samplerate: ", samplerate)
        sd.play(data, samplerate, latency='low')
        status = sd.wait()                          # may result in scratches when missing!
    except Exception as e:
        exceptPrint(e, "playWav failed")


def playSingleSine(duration):
    """play a single sine wave for duration sec"""

    # play sine wave
    samplerate = 44100          # samples per sec
    sounddur   = duration       # seconds
    soundfreq  = 27.5           # Kammerton A abgeleitet (27.5 *sqrt(256) = 440)
    soundamp   = 1              # amplitude; mit steigender Amplitude Verzerrungen

    # create the time base
    t = (np.arange(samplerate * sounddur)) / samplerate
    #~print("t: ", t)

    # create the data
    freq = soundfreq * (np.sqrt(256))
    # print("Freq: {:9.4f}".format(freq))
    outdata = soundamp * np.sin(2 * np.pi * freq * t)
    #~print("outdata raw: ", outdata)
    sd.play(outdata, samplerate * 2, latency='low')
    status = sd.wait()  # without wait it becomes scratchy!


def playSineScale():
    """play sine wave scale"""

    samplerate = 44100          # samples per sec
    sounddur   = 0.3            # seconds
    soundfreq  = 27.5           # Kammerton A abgeleitet (27.5 *sqrt(256) = 440)
    soundamp   = 1              # amplitude; mit steigender Amplitude Verzerrungen

    # create the time base
    t = (np.arange(samplerate * sounddur)) / samplerate
    #~print("t: ", t)

    # create the data
    for i in list(range(0, 15)) + list(range(15, -1, -1)):
        freq = soundfreq * (np.sqrt(2) **i)
        print("Freq: {:9.4f}".format(freq))
        outdata = soundamp * np.sin(2 * np.pi * freq * t)   # Tonleiter
        #~print("outdata raw: ", outdata)
        sd.play(outdata, samplerate * 2, latency='low')
        status = sd.wait()
        time.sleep(0.1)


# def playLongClick():
#     """play a long click"""

#     # play sine wave
#     samplerate = 44100              # samples per sec
#     sounddur   = 0.1                # seconds
#     soundfreq  = 1000               # 440Hz = Kammerton A
#     soundamp   = 0.1                # amplitude; mit steigender Amplitude Verzerrungen 1.0 may be max?

#     # create the time base
#     t = (np.arange(samplerate * sounddur)) / samplerate
#     #print("t: len:", len(t))

#     # create the data
#     outdata = soundamp * (np.sin(2 * np.pi * soundfreq * t))
#     sd.play(outdata, samplerate, latency=0.05)
#     # status = sd.wait() # if called then block until completion


def playGeigerClick():
    """play a single Geiger counter like click sound as a sine wave"""

    samplerate = 44100              # samples per sec
    sounddur   = 0.05               # seconds
    soundfreq  = 440                # 440Hz = Kammerton A
    soundamp   = 0.1                # amplitude; mit steigender Amplitude Verzerrungen 1.0 may be max?

    # create the time base
    t = (np.arange(samplerate * sounddur)) / samplerate
    #print("t: len:", len(t))

    # create the data
    outdata = soundamp * (np.sin(2 * np.pi * soundfreq * t))
    sd.play(outdata, samplerate, latency=0.05)
    status = sd.wait()              # block until completion


def playGeigerCounter():
    """play Geiger counter with increasing mean count rate"""

    duration = 3
    for mean in [0.3, 1, 3, 10, 30, 100, 300, 1000, 3000]:
        print("mean: ", mean)
        counts   = 0
        ttot     = 0
        start    = time.time()
        while time.time() < (start + duration):
            t = np.random.exponential(1 / mean)
            #print("mean= {:0.0f}, t= {:0.3f} ttot= {:0.3f}  counts= {:0.0f}".format(mean, t, ttot, counts))
            time.sleep(t)
            playGeigerClick()
            ttot += t
            counts += 1

    print("finished")


def makePicFromGraph():
    """get and save the pic into memory"""

    # prepare pic in memory
    #
    # prepare a JPG in memory
    # gglobs.picbytes = io.BytesIO()
    # plt.savefig(gglobs.picbytes, format="jpg")

    # matplotlib offers some optional export options that are only available to
    # .jpg files. For example, quality (default 95), optimize (default: false),
    # and progressive (default: false):
    #   plt.savefig('line_plot.jpg', dpi=300, quality=80, optimize=True, progressive=True)
    #
    # MatplotlibDeprecationWarning: The 'quality' parameter of print_jpg() was
    # deprecated in Matplotlib 3.3 and will be removed two minor releases later. Use
    # pil_kwargs={'quality': ...} instead. If any parameter follows 'quality', they
    # should be passed as keyword, not positionally.

    # gglobs.picbytes = io.BytesIO()
    # plt.savefig(gglobs.picbytes, format="jpg", pil_kwargs={'quality':80})

    # prepare a PNG, SVG, JPG in memory
    # with a MiniMon File of 20MB, 665000 records!
    # DEBUG  : ...232 runCheckCycle: Make JPG:   915.4 ms
    # DEBUG  : ...233 runCheckCycle: Make SVG: 36627.4 ms  # using SVG makes the generation time explode!
    # DEBUG  : ...234 runCheckCycle: Make PNG:   933.0 ms
    # DEBUG  : ...233 runCheckCycle: Make JPG:   945.2 ms  # Qual=80; quality reduction bringt nichts:

    # mit 720 records:
    # Vorteil PNG über SVG bleibt
    # DEBUG  : ...268 runCheckCycle: Make JPG:  85.9 ms
    # DEBUG  : ...269 runCheckCycle: Make SVG: 152.2 ms
    # DEBUG  : ...270 runCheckCycle: Make PNG:  99.3 ms
    # DEBUG  : ...244 runCheckCycle: Make JPG:  90.4 ms    # Qual=80; quality reduction bringt nichts

    fncname = "makePicFromGraph: "

    # startpng = time.time()

    gglobs.picbytes = io.BytesIO()
    plt.savefig(gglobs.picbytes, format="png")

    # duration = (time.time() - startpng) * 1000 # ms
    # rdprint(fncname + "PNG: size:{} duration:{:0.1f} ms".format(sys.getsizeof(gglobs.picbytes), duration))


def scaleVarValues(variable, value, scale):
    """
    Apply the 'Scaling' declared in configuration file geigerlog.cfg. Can be
    used both for value scaling as for graph scaling.
    Return: the scaled value (or original in case of error)
    NOTE:   scale is in upper-case, but may be empty or NONE
    """

    fncname = "scaleVarValues: "
    #print(fncname + "scaling variable:'{}' value:'{}', scale: {}".format(variable, value, scale))

    scale = scale.strip().upper()             # make sure it is upper

    if scale == "VAL" or scale == "" or scale == "NONE": return value

    # example: scale: LOG(VAL)+1000           # orig
    # becomes: ls   : np.log(value)+1000      # mod
    ls = scale
    ls = ls.replace("VAL",    "value")        # the data of that column
    ls = ls.replace("LOG",    "np.log")       # Log to base e; natural log
    ls = ls.replace("LOG10",  "np.log10")     # Log to base 10
    ls = ls.replace("LOG2",   "np.log2")      # Log to base 2
    ls = ls.replace("SIN",    "np.sin")       # sine
    ls = ls.replace("COS",    "np.cos")       # cosine
    ls = ls.replace("TAN",    "np.tan")       # tangent
    ls = ls.replace("SQRT",   "np.sqrt")      # square root
    ls = ls.replace("CBRT",   "np.cbrt")      # cube root
    ls = ls.replace("ABS",    "np.absolute")  # absolute value
    ls = ls.replace("INT",    "np.int")       # integer value
    # ls = ls.replace("PADEC",  "PADEC")        # Paralyzing Dead Time Correction       # is upper-case anyway
    # ls = ls.replace("NOPADEC","NOPADEC")      # Non-Paralyzing Dead Time Correction   # is upper-case anyway

    try:
        scaledValue = eval(ls)

    except Exception as e:
        msg  = "ERROR scaling Values: variable:'{}'\n".format(variable)
        msg += "ERROR scaling Values: formula: '{}'\n".format(scale)
        msg += "ERROR scaling Values: errmsg:  '{}'\n".format(e)
        msg += "Continuing with original value"
        exceptPrint(e, msg)
        Queueprint(msg)
        scaledValue = value

    # print(fncname + "variable:'{}', orig scale:'{}', mod scale:'{}', value:{}, v-scaled:{}".format(variable, scale, ls, value, scaledValue))

    return scaledValue


def DeadTimeBalance(N, *args):
    """
    The difference between M (observed counts) and formula for Calculation of M from N (True counts)
    -> CPM_obs = CPM_true * exp(- CPM_true * deadtime)
    """

    M       = args[0]
    tau     = args[1]

    # balance = np.log(M) - (np.log(N) - N * tau)       # based on the log version of the equation
    balance = M - (N * np.exp(-N * tau))                # based on the exp
    # print("M:{}, tau:{}, N:{:0.0f} balance:{:0.6f}".format(M, tau, N, balance))

    return balance


def NOPADEC(cps, deadtime):
    """
    Non-Paralyzing Deadtime correction (analytical solution)
    in GeigerLog notation: # localValueScale = "VAL / (1 - VAL * {})".format(dt)
    cps:        cps_observed,
    deadtime:   deadtime of tube in microsecond
    Formula:    CPS_true = CPS_obs / (1 - CPS_obs * deadtime[s])
    """

    fncname = "nopadec: "

    tau = deadtime / 1E6    # we need deadtime in second
    N   = cps / (1 - cps * tau)

    # print(fncname + "cps:{}, deadtime:{} retval:{:0.3f}".format(cps, deadtime, N))

    return N


def PADEC(cps, deadtime):
    """
    Paralyzing Deadtime correction (iterative solution)
    cps:        cps_observed,
    deadtime:   deadtime of tube in microsecond
    Formula:    CPS_obs = CPS_true * exp(- CPS_true * deadtime)
    """

    fncname = "PADEC: "

    tau     = deadtime / 1E6    # we need deadtime in second

    try:
        lower_bracket = 0
        upper_bracket = 1 / tau     # the count rate limit is 1/tau; (e.g. at 125µs max CPS=8000)
        res = scipy.optimize.root_scalar(DeadTimeBalance, args=(cps, tau), x0=cps, x1=cps*2, xtol=0.1, method='bisect', bracket=[lower_bracket, upper_bracket] )
        # print(fncname + "vars(res):{}, Ratio N/M:{:0.2f}".format(vars(res), res.root/cps))
        if res.converged:   retval = res.root
        else:               retval = gglobs.NAN

    except Exception as e:
        msg = fncname + "Iteration failure with: cps:{}, deadtime:{}".format(cps, deadtime)
        Queueprint("Deadtime Correction with " + msg)
        exceptPrint(e, msg)
        retval = gglobs.NAN

    # print(fncname + "cps:{}, deadtime:{} retval:{:0.3f} Ratio retval/cps:{:0.2f}".format(cps, deadtime, retval, retval/cps))

    return retval


class ClickLabel(QLabel):
    """making a label click-sensitive"""

    def __init__(self, parent):
        QLabel.__init__(self, parent)

    def mousePressEvent(self, event):
        colorPicker()


def colorPicker():
    """Changes color of the selected variable.
    Called by the color picker button in the graph options. """

    if gglobs.currentConn == None: return # no color change unless something is loaded

    colorDial   = QColorDialog()
    color       = colorDial.getColor()
    if color.isValid():
        vprint("colorPicker: new color picked:", color.name())
        gglobs.exgg.btnColor.setStyleSheet("QLabel { border: 1px solid silver;  border-radius: 3px; background-color: %s ; }" % color.name())
        addMenuTip(gglobs.exgg.btnColor, gglobs.exgg.btnColorText + str(color.name()))
        gglobs.exgg.btnColor.setText("")

        vname = getNameSelectedVar()
        gglobs.varsCopy[vname][3] = color.name()
        gglobs.exgg.applyGraphOptions()

    gglobs.exgg.notePad.setFocus()


def printProgError(*args):
    print("PROGRAMMING ERROR !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    dprint(*args, debug=True)
    setNormalCursor()
    sys.exit(-1)


def QtUpdate():
    """updates the Qt window"""

    QApplication.processEvents()


def executeTPUT(action = 'allow_line_wrapping'):
    """
    set terminal output with or without linebreaks; works in Linux only
    use action = 'allow_line_wrapping' or 'no_line_wrapping'
    """
    # For generic non full screen applications, you can turn off line wrapping by
    # sending an appropriate escape sequence to the terminal:
    #   tput rmam
    # This mode can be cancelled with a similar escape:
    #   tput smam
    # also: https://tomayko.com/blog/2004/StupidShellTricks

    if not "LINUX" in platform.platform().upper(): return

    if action == 'allow_line_wrapping' or gglobs.forcelw:
        tputcommand = "rmam"                # tput rmam: no line break on lines longer than screen
        tputmsg     = "(line wrapping turned OFF)"

    else:   # 'no_line_wrapping'
        tputcommand = "smam"                # tput smam: do line break on lines longer than screen
        tputmsg     = "(line wrapping turned ON)"

    try:
        # raise Exception("tput command")
        subprocess.call(["tput", tputcommand])
        dprint("{:28s}: {}".format("LineWrapping (Linux)", "SUCCESS executing tput {} - {}".format(tputcommand, tputmsg)))
    except Exception as e:
        msg = ""
        exceptPrint(e, msg)
        edprint("{:28s}: {}".format("LineWrapping (Linux)", "FAILURE executing tput {} - {}".format(tputcommand, tputmsg)), debug=True)


def openManual():
    """Show the GeigerLog Manual, first try a local version, but if not
    present, then try the version on SourceForge"""

    fncname = "openManual: "
    manual_file = None

    if gglobs.manual_filename != 'auto':
        # if filename is defined in config file, use that name. File does exist,
        # because if not, gglobs.manual_filename would have been
        # overwritten with 'auto' when reading the config
        manual_file = getProgPath() + "/" + gglobs.manual_filename
    else:
        # if NOT defined in config file, use first found file which begins
        # with 'GeigerLog-Manual'
        path = getProgPath() + "/"
        for filename in os.listdir(path):
            #print("filename: ", filename)
            if re.match("GeigerLog-Manual", filename):
                #print "filename", filename
                manual_file = getProgPath() + "/" + filename
                break                   # manual found, exit for loop

    if manual_file == None:
        efprint ("The file 'GeigerLog-Manual-xyz', with xyz being a version number, is missing")
        qefprint("from the GeigerLog working directory 'geigerlog'.")
        fprint  ("Now trying to find the file online.")
    else:
        dprint("Using Manual_file: ", manual_file)

    if manual_file != None:
        try:
            if sys.platform.startswith('linux'):
                # xdg-open command in the Linux system is used to open a file
                # or URL in the user’s preferred application.
                subprocess.call(["xdg-open", manual_file])
                dprint("Showing '{}' via xdg-open on Linux".format(manual_file))
            else:
                os.startfile(manual_file)
                dprint("Showing '{}' via os.startfile on other OS".format(manual_file))

            return

        except Exception as e:
            msg = "Failure Showing '{}' via xdg-open on Linux or via os.startfile on other OS".format(manual_file)
            #print(sys.exc_info())
            exceptPrint(fncname + str(e), msg)
            dprint(msg)

        try:
            if sys.platform.startswith('linux'):
                subprocess.call(["firefox", manual_file])
                dprint("Showing '{}' via firefox on Linux".format(manual_file))
            else:
                os.startfile(manual_file)
                dprint("Showing '{}' via os.startfile on other OS".format(manual_file))

            return

        except Exception as e:
            msg = "Failure Showing '{}' via firefox on Linux or via os.startfile on other OS".format(manual_file)
            #print(sys.exc_info())
            exceptPrint(fncname + str(e), msg)
            dprint(msg)

        try:
            import webbrowser
            webbrowser.open(manual_file)
            dprint("Showing '{}' via import webbrowser".format(manual_file))

            return

        except Exception as e:
            msg = "Failure Showing '{}' via import webbrowser".format(manual_file)
            #print(sys.exc_info())
            exceptPrint(fncname + str(e), msg)
            dprint(msg)


    try:
        shortv = gglobs.__version__.split("pre")[0]   # use only the version part before 'pre'
        #shortv: "1.0.1pre9" --> "1.0.1"
        print("shortv: ", shortv)

        url = QUrl('https://sourceforge.net/projects/geigerlog/files/GeigerLog-Manual-v{}.pdf'.format(shortv))
        if QDesktopServices.openUrl(url):
            dprint("Showing QUrl '{}'".format(url))
        else:
            QMessageBox.warning(gglobs.exgg, 'GeigerLog Manual', 'Could not open GeigerLog Manual')
            dprint("Failure Showing manual with QUrl '{}'".format(url))
        return
    except Exception as e:
        msg = "Failure Showing manual with QUrl"
        exceptPrint("openManual: " + str(e), msg)

    efprint("Could not find GeigerLog-Manual, neither locally nor online!")


def showSystemInfo():
    """System Info on the Devel Menu"""

    fncname = "showSystemInfo: "

    screen           = QDesktopWidget().screenGeometry()
    screen_available = QDesktopWidget().availableGeometry()
    geom             = gglobs.exgg.geometry()
    geom_frame       = gglobs.exgg.frameGeometry()

    fmt              = "{:35s}{}\n"
    si               = ""

    # user
    si += fmt.format("Username:",                        "{}".format(os.environ.get('USER')))

    # platform
    si += fmt.format("\nPlatform:",                      "")
    si += fmt.format("  Operating System:",              "{}".format(platform.platform()))
    si += fmt.format("  Machine:",                       "{}, {}".format(platform.machine(), platform.architecture()[0]))
    si += fmt.format("  Byte Order:",                    "{}".format(sys.byteorder))

    # status
    try:
        if gglobs.devel:
            gib = 2**30
            si += fmt.format("\nSystem Info:",               "")
            si += fmt.format("  CPU cores:",                 "{} "          .format(psutil.cpu_count(logical=False)))
            si += fmt.format("  CPU logical cores:",         "{} "          .format(psutil.cpu_count(logical=True )))
            si += fmt.format("  CPU Frequency:",             "{} "          .format(psutil.cpu_freq()))
            si += fmt.format("  CPU Load Avg:",              "{} (last 1, 5 and 15 minutes)".format(psutil.getloadavg()))
            si += fmt.format("  CPU Usage:",                 "{:4.2f} %"    .format(psutil.cpu_percent()))
            si += fmt.format("  Memory Total:",              "{:4.2f} GiB"  .format(psutil.virtual_memory().total / gib))
            si += fmt.format("  Memory Usage:",              "{:4.2f} %"    .format(psutil.virtual_memory().percent))
    except Exception as e:
        exceptPrint(e, "psutil missing?")
        si += fmt.format("\nSystem Info:",               "n.a., missing psutil")

    # versions
    si += fmt.format("\nVersion status:",                "")
    for ver in gglobs.versions:
        si += fmt.format( "  " + ver,                    gglobs.versions[ver])

    # runtime
    si += fmt.format("\nRuntime settings:",              "")
    si += fmt.format("  Flag DEBUG:",                    str(gglobs.debug))
    si += fmt.format("  Flag VERBOSE:",                  str(gglobs.verbose))
    si += fmt.format("  Flag werbose:",                  str(gglobs.werbose))
    si += fmt.format("  Flag KeepFF:",                   str(gglobs.keepFF))
    si += fmt.format("  Flag Devel:",                    str(gglobs.devel))
    si += fmt.format("  Flag Testing:",                  str(gglobs.testing))
    si += fmt.format("  Flag Timing:",                   str(gglobs.timing))
    si += fmt.format("  Flag gstesting:",                str(gglobs.gstesting))
    si += fmt.format("  Flag ForceLineWrapping:",        str(gglobs.forcelw))

    si += fmt.format("  Flag autoLogFile:",              str(gglobs.autoLogFile))
    si += fmt.format("  Flag autoDevConnect:",           str(gglobs.autoDevConnect))
    si += fmt.format("  Flag autoLogStart:",             str(gglobs.autoLogStart))
    si += fmt.format("  Flag autoLogLoad:",              str(gglobs.autoLogLoad))
    si += fmt.format("  Flag autoQuickStart:",           str(gglobs.autoQuickStart))

    si += fmt.format("  GeigerLog Program Directory:",   str(getProgPath()))
    si += fmt.format("  GeigerLog Data Directory:",      str(gglobs.dataPath))
    si += fmt.format("  GeigerLog Resource Directory:",  str(gglobs.gresPath))
    si += fmt.format("  GeigerLog Manual:",              str(gglobs.manual_filename))

    # GUI
    si += fmt.format("\nGUI:",                           "")
    si += fmt.format("  Monitor:",                       "")
    si += fmt.format("   Screen size - Hardware:",       "{}x{}".format(screen.width(), screen.height()))
    si += fmt.format("   Screen size - Available:",      "{}x{}, at position: x={}, y={}".format(screen_available.width(), screen_available.height(), screen_available.x(), screen_available.y()))
    si += fmt.format("   Current window size:",          "{}x{} including window frame (w/o frame: {}x{})".format(geom_frame.width(), geom_frame.height(), geom.width(), geom.height()))
    si += fmt.format("  Styles:",                        "")
    si += fmt.format("   Styles available on System:",   QStyleFactory.keys())
    si += fmt.format("   Active Style (internal name):", str(gglobs.app.style().metaObject().className()))
    si += fmt.format("  Fonts:",                         "")
    si += fmt.format("   Active Font - Application:",    strFontInfo("", gglobs.app.font()))
    si += fmt.format("   Active Font - Menubar:",        strFontInfo("", gglobs.exgg.menubar.fontInfo()))
    si += fmt.format("   Active Font - NotePad:",        strFontInfo("", gglobs.exgg.notePad.fontInfo()))
    si += fmt.format("   Active Font - LogPad:",         strFontInfo("", gglobs.exgg.logPad.fontInfo()))


    si += "\n"
    si += fmt.format("Devices:",                         "Activated Connected Model")
    for i, DevName in enumerate(gglobs.Devices):
        si += fmt.format("   {:2n} {}".format(i + 1, DevName), "{:9s} {:9s} {}".format(str(gglobs.Devices[DevName][ACTIV]), str(gglobs.Devices[DevName][CONN]), str(gglobs.Devices[DevName][DNAME])))

    # Serial Ports
    si += fmt.format("\nUSB-to-Serial Port Settings:",   "")

    # GMC USB port
    si += fmt.format("  GMC Serial (USB) Port Settings:",  "")
    si += fmt.format("   Port:",                          str(gglobs.GMC_usbport))
    si += fmt.format("   Baudrate:",                      str(gglobs.GMC_baudrate))
    si += fmt.format("   Timeout: (Read)",                str(gglobs.GMC_timeoutR))
    si += fmt.format("   Timeout: (Write)",               str(gglobs.GMC_timeoutW))

    # I2C USB port
    si += fmt.format("  I2C Serial (USB) Port Settings:",  "")
    si += fmt.format("   Port:",                          str(gglobs.I2Cusbport))
    si += fmt.format("   Baudrate:",                      str(gglobs.I2Cbaudrate))
    si += fmt.format("   Timeout: (Read)",                str(gglobs.I2CtimeoutR))
    si += fmt.format("   Timeout: (Write)",               str(gglobs.I2CtimeoutW))

    # GS USB port
    si += fmt.format("  GS Serial (USB) Port Settings:",  "")
    si += fmt.format("   Port:",                          str(gglobs.GSusbport))
    si += fmt.format("   Baudrate:",                      str(gglobs.GSbaudrate))
    si += fmt.format("   Timeout: (Read)",                str(gglobs.GStimeoutR))
    si += fmt.format("   Timeout: (Write)",               str(gglobs.GStimeoutW))

    # worldmaps
    si += fmt.format("\nWorldmaps Settings:", "")
    si += fmt.format("  SSID",                            gglobs.WiFiSSID)
    si += fmt.format("  Password",                        gglobs.WiFiPassword)
    si += fmt.format("  Website",                         gglobs.gmcmapWebsite)
    si += fmt.format("  URL",                             gglobs.gmcmapURL)
    si += fmt.format("  UserID",                          gglobs.gmcmapUserID)
    si += fmt.format("  CounterID",                       gglobs.gmcmapCounterID)
    si += fmt.format("  Period",                          gglobs.gmcmapPeriod)
    si += fmt.format("  WiFi",                            "ON" if gglobs.gmcmapWiFiSwitch else "OFF")

    lsysinfo = QTextBrowser()                             # to hold the text; allows copy
    lsysinfo.setLineWrapMode(QTextEdit.WidgetWidth)
    lsysinfo.setText(si)

    dlg = QDialog()
    dlg.setWindowIcon(gglobs.iconGeigerLog)
    dlg.setWindowTitle("Help - System Info")
    dlg.setFont(gglobs.fontstd)
    dlg.setWindowModality(Qt.WindowModal)
    dlg.setMinimumWidth(1200)
    dlg.setMinimumHeight(690)

    bbox = QDialogButtonBox()
    bbox.setStandardButtons(QDialogButtonBox.Ok)
    bbox.accepted.connect(lambda: dlg.done(100))

    layoutV = QVBoxLayout(dlg)
    layoutV.addWidget(lsysinfo)
    layoutV.addWidget(bbox)

    dlg.exec()


def setNormalCursor():

    gglobs.exgg.setNormalCursor()


def setBusyCursor():

    gglobs.exgg.setBusyCursor()


def showStatusMessage(msg):

    gglobs.exgg.showStatusMessage(msg)


def cleanupDevices(ctype):
    """ctype is 'before' or 'after'; so far only for GMC"""

    for DevName in gglobs.Devices:
        if DevName == "GMC":
            from gdev_gmc import cleanupGMC
            cleanupGMC(ctype)
        else:
            pass                # so far no other device needs cleaning


def setLoggableVariables(device, DeviceVariables):
    """set the loggable variables as list, making sure there is no whitspace"""

    fncname = "setLoggableVariables: "

    if DeviceVariables is not None:
        DevVars = DeviceVariables.split(",")
        for i in range(len(DevVars)):
            DevVars[i] = DevVars[i].strip()           # remove all white space from all variable names
        gglobs.Devices[device][VNAME] = DevVars
        # edprint(fncname + "Device: ", device, ", Variables:", gglobs.Devices[device][VNAME])


def getTubeSensitivities(DeviceVariables):
    """get the sensitivity for the device's tube according to the defined variables"""

    fncname = "getTubeSensitivities: "

    if DeviceVariables == None: return  ""  # could be None if user enters wrong values

    Tubeheader = "Applicable Tube Sensitivity:\n"
    TubeList   = ""
    ttmplt     = "   {:27s}{} CPM / (µSv/h)\n"
    devvar     = DeviceVariables.split(",")
    CPX        = [False] * 4
    for a in devvar:
        a = a.strip()
        if   a == "CPM"    or a == "CPS" :      CPX[0] = True
        elif a == "CPM1st" or a == "CPS1st":    CPX[1] = True
        elif a == "CPM2nd" or a == "CPS2nd":    CPX[2] = True
        elif a == "CPM3rd" or a == "CPS3rd":    CPX[3] = True

    if CPX[0]: TubeList += ttmplt.format("CPM / CPS:",       gglobs.Sensitivity[0])
    if CPX[1]: TubeList += ttmplt.format("CPM1st / CPS1st:", gglobs.Sensitivity[1])
    if CPX[2]: TubeList += ttmplt.format("CPM2nd / CPS2nd:", gglobs.Sensitivity[2])
    if CPX[3]: TubeList += ttmplt.format("CPM3rd / CPS3rd:", gglobs.Sensitivity[3])

    if TubeList == "": TubeList = "   No Tube-supporting Variables defined"

    TubeList = Tubeheader + TubeList

    cdprint(fncname + "DeviceVariables: ", DeviceVariables)
    cdprint(fncname + "TubeList:",   TubeList)

    return TubeList


def getLoggedValuesHeader():
    """get header for logged values"""

    # header is:
    # ......................... Dur[ms]   CPM       CPS       CPM1st    CPS1st    CPM2nd    CPS2nd    CPM3rd    CPS3rd    Temp      Press     Humid     Xtra

    text  = "{:<25s} {:<10s} ".format("." * 25, "Dur[ms]")
    for a in gglobs.varsCopy:   text += "{:<10s}".format(a)

    return text


def vprintLoggedValues(rfncname, varlist, alldata, duration=None, forceprint=False):
    """vprint formatted logged values for a SINGLE device"""

    # print like:
    # getValuesGMC:           176.00    4.00      176.00    4.00      0.00      0.00      -         -         -         -         -         -
    # getValuesAudio:          -         -         -         -         -         -         0.00      0.00      -         -         -         -

    text = "{:<21s}".format(rfncname)

    if duration is not None: text += "{:8.3f}       ".format(duration)
    else:                    text += "{:<10s} ".format(" --- ")

    for vname in gglobs.varsCopy:
        if   vname in alldata:
            if alldata[vname] is not None:  text += "{:<10.3f}".format(alldata[vname])
        else:
            text += "{:<10s}".format("-")

    vprint(text, forceverbose=forceprint)


def getDeltaTimeMessage(deltatime, deviceDateTime):
    """determines difference between times of computer and device and gives message"""

    DTM  = ""
    dtxt = ""
    # dtfd = "{:30s}".format("Date & Time from Device:")
    # dtfg = "{:30s}".format("Date & Time from GeigerLog:")
    dtfd = "{:30s}".format("Device Date & Time:")
    dtfg = "{:30s}".format("Computer Date & Time:")

    if   np.isnan(deltatime):    dtxt += "Device clock cannot be read"                                           # clock defect?
    elif abs(deltatime) <= 1:    dtxt += "Device clock is same as computer clock within 1 sec"                   # uncertainty 1 sec
    elif deltatime >= +1:        dtxt += "Device is slower than computer by {:0.1f} sec".format(deltatime)       # delta positiv
    elif deltatime <= -1:        dtxt += "Device is faster than computer by {:0.1f} sec".format(abs(deltatime))  # delta negativ

    if   np.isnan(deltatime):
    # no clock
            DTM += "<red>" + dtfd + dtxt + "\n"

    elif abs(deltatime) > 5:
    # big difference
            DTM += dtfg + str(longstime()) + "\n"               # new line, not in red
            DTM += "<red>" +dtfd + str(deviceDateTime) + "\n"   # in red
            DTM += "<red>" + " "*30 + dtxt + "\n"               # in red

    else:
    # all ok
            DTM += dtfd + str(deviceDateTime) + "\n"
            DTM += " " * 30 + dtxt + "\n"

    return DTM


def correctVariableCaps(devicevars):
    """correct any small caps in variables"""

    fncname = "correctVariableCaps: "

    newt = ""
    for uppvname in devicevars.upper().split(","):
        a = uppvname.strip()
        if   a == "CPM"   :   newt += "CPM, "
        elif a == "CPS"   :   newt += "CPS, "
        elif a == "CPM1ST":   newt += "CPM1st, "
        elif a == "CPS1ST":   newt += "CPS1st, "
        elif a == "CPM2ND":   newt += "CPM2nd, "
        elif a == "CPS2ND":   newt += "CPS2nd, "
        elif a == "CPM3RD":   newt += "CPM3rd, "
        elif a == "CPS3RD":   newt += "CPS3rd, "
        elif a == "TEMP"  :   newt += "Temp, "
        elif a == "PRESS" :   newt += "Press, "
        elif a == "HUMID" :   newt += "Humid, "
        elif a == "XTRA"  :   newt += "Xtra, "
        elif a == "NONE"  :   newt += "None, "      # oh, oh
        else:                 pass                  # if it does not fit, ignore it
        # rdprint(fncname + "a: ", a, "newt: ", newt)

    newt = newt[:-2]    # remove ", " at end

    # on wrong entries newt will be empty
    if newt == "": newt = "auto"

    return newt


def ping(host):
    """
    Returns (True, Time=...) if host responds to a ping request
    (False, Time not found) otherwise.
    Remember that a host may not respond to a ping (ICMP) request
    even if the host name is valid!
    """

    # Option for the number of packets as a function of operating system
    param = '-n' if platform.system().lower()=='windows' else '-c'

    command     = ['ping', param, '1', host]    # Building the command. Ex: "ping -c 1 google.com"
    popen       = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    popencomm   = popen.communicate()
    psuccess    = (popen.returncode == 0)       # MUST come after communicate() !
    popencout   = popencomm[0].decode("utf-8")  # use stdout
    popencerr   = popencomm[1].decode("utf-8")  # use stderr
    ptime       = "time not found"
    for a in popencout.split("\n"):
        if "time=" in a: ptime = a[a.find("time="):]

    vprint("Ping stdout:\n", popencout)
    vprint("Ping stderr:\n", popencerr)

    return psuccess, ptime


def fixGarbledAudio():
    """On Linux only: fix garbled audio sound"""

    # Linux       with garbled sound and message in the terminal:
    #                 "ALSA lib pcm.c:7963:(snd_pcm_recover) underrun occurred"
    #             execute 'pulseaudio -k' as regular user (not sudo!) this should solve it

    if not "LINUX" in platform.platform().upper():
        fprint("Applicable only under Linux")
        return

    fncname = "fixGarbledAudio: "

    fprint(header("Fix Garbled Audio"))
    try:
        subprocess.call(["pulseaudio", "-k"])
        time.sleep(0.03)    # needs a moment to settle
        msg = "Executed: 'pulseaudio -k'"
        dprint(fncname + msg)
        fprint(msg)
        # raise Exception("test fixGarbledAudio")
    except Exception as e:
        msg = "FAILURE: Exception when fixing garbled audio with 'subprocess.call(pulseaudio -k)'"
        exceptPrint(e, fncname + msg)
        efprint(msg)


def getTimeCourseInLimits(varname, DeltaT):
    """get the (time, value) pairs for the last DeltaT minutes for variable varname"""

    fncname = "getTimeCourseInLimits: "
    # edprint(fncname + "varname: ", varname)

    DBData = gglobs.logDBData

    if np.all(DBData) == None : return [gglobs.NAN, gglobs.NAN, gglobs.NAN]   # no database

    # NOTE: (see gup_plot.py for explanation of correction)
    TimeBaseCorrection  = mpld.date2num(np.datetime64('0000-12-31'))    # = -719163.0
    #print(fncname + "TimeBaseCorrection: ", TimeBaseCorrection)
    logTime             = DBData[:,0] + TimeBaseCorrection              # time data of total file

    DeltaT_Days = DeltaT / 60 / 24                                      # DeltaT in minutes => days

    plotTimeDelta = (logTime[-1] - logTime[0]) * 24 * 60  # Delta in min
    if plotTimeDelta > DeltaT:  plotTimeDelta = DeltaT

    # split multi-dim np.array into 12 single-dim np.arrays like log["CPM"] = [<var data>]
    log = {}
    for i, vname in enumerate(gglobs.varsCopy):
        log[vname] = DBData[:, i + 1]
        # print("{}: log[{}]: {}".format(i, vname, log[vname]))

    # confine limits
    Xleft  = max(logTime.max() - DeltaT_Days, logTime.min())

    # find the record, where the left time limit applies
    recmin = np.where(logTime >= Xleft )[0][0]
    # print("recmin: ", recmin)

    # slice the array
    vardata  = log[varname] [recmin : ]
    timedata = logTime      [recmin : ]
    # print(vardata)

    varmask  = np.isfinite(vardata)         # mask for nan values
    vardata  = vardata[varmask]             # remove the nan values
    timedata = timedata[varmask]            # remove the nan values

    return (timedata, vardata, plotTimeDelta)


def getGeigerLogIP():
    """get the IP of the computer running GeigerLog"""

    fncname = "getGeigerLogIP: "

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


# is a socket open or not?
        # import socket
        # location = (GeigerLogIP, MonServerPort)
        # a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # result_of_check = a_socket.connect_ex(location)
        # if result_of_check == 0:
        #     print("mid: Port is open")
        #     a_socket.close()
        #     # a_socket.shutdown(socket.SHUT_RDWR)
        # else:
        #     print("mid Port is not open")
        #     a_socket.close()


def blendColor(color1, color2, f):

    return 10, 100, 200

    fncname = "blendColor: "
    print(fncname + "c1, c2, f:  ", color1, color2, f)

    r1 = int(color1[1 : 3], 16)
    g1 = int(color1[3 : 5], 16)
    b1 = int(color1[5 : 7], 16)

    r2 = int(color2[1 : 3], 16)
    g2 = int(color2[3 : 5], 16)
    b2 = int(color2[5 : 7], 16)

    r = r1 + (r2 - r1) * f
    g = g1 + (g2 - g1) * f
    b = b1 + (b2 - b1) * f
    return r, g, b


def getEasyDictPrint(mydict):

    return str(mydict).replace(" ", "").replace("'", "").replace(",", " ").replace("True", TYELLOW + "True " + TGREEN)


def printLoggable(msg = ""):
    if msg > "": gdprint(msg)
    gdprint("varsSetForLog     ",     getEasyDictPrint(gglobs.varsSetForLog))
    gdprint("varsSetForHis     ",     getEasyDictPrint(gglobs.varsSetForHis))
    gdprint("varsSetForCurrent ",     getEasyDictPrint(gglobs.varsSetForCurrent))


def saveGraphToFile():
    """save the main graph to a (png) file"""

    figpath = gglobs.currentDBPath
    if figpath is None:
        gglobs.exgg.showStatusMessage("No data available")
        return

    while gglobs.plotIsBusy:
        print("Wait", end=" ", flush=True)
        pass

    pngpath = figpath + ("_" + stime() + ".png").replace(" ", "_").replace(":", "_") # change blank and : to underscore (for Windows)
    plt.savefig(pngpath)
    fprint(header("Save Graph to File"))
    msg = "The current graph was saved to file: "
    fprint(msg + "\n", pngpath)
    dprint(msg       , pngpath)


def showResultCRC8():
    """Enter 2 bytes and print CRC8 checksum"""

    fncname = "showResultCRC8: "

    crcbytes, okPressed = QInputDialog.getText(None, "Show CRC8 Result","Enter 2 Byte values, separeted by comma\nlike: {}".format("123, 234"))
    if okPressed:
        fprint(header("CRC8 Result"))
        try:
            crcbytelist = crcbytes.split(",")
            if len(crcbytelist) >= 2:
                crcbyte0    = int(float(crcbytelist[0]))
                crcbyte1    = int(float(crcbytelist[1]))
                crctest     = (crcbyte0, crcbyte1)
                msg         = "Bytes: {}  =>  CRC8: {} ".format(crcbytes, getCRC8(crctest))
                fprint(msg)
                dprint(fncname + msg)
            else:
                msg = "Please enter 2 Byte values, separated by comma; you entered: '{}'".format(crcbytes)
                efprint(msg)
                edprint(fncname + msg)

        except Exception as e:
            exceptPrint(e, "showResultCRC8: " + crcbytes)


def getCRC8(data):
    """
    calculates 8-Bit checksum as defined by Sensirion
    data:   tuple of 2 bytes
    return: CRC8 of data
    """

    # Adapted from Sensirion code - must clip crc to 8 bit (uint8)
    # in depth: https://barrgroup.com/embedded-systems/how-to/crc-calculation-c-code
    # // Original Sensirion C code:
    # // Example:       CRC(0xBEEF) = 0x92  (dec:146)
    # // my examples:   CRC(0x0000) = 0x81  (dec:129)
    # //
    # #define CRC8_POLYNOMIAL 0x31
    # #define CRC8_INIT 0xFF

    # uint8_t sensirion_common_generate_crc(const uint8_t* data, uint16_t count) {
    #     uint16_t    current_byte;
    #     uint8_t     crc = CRC8_INIT;
    #     uint8_t     crc_bit;
    #     /* calculates 8-Bit checksum with given polynomial */
    #     for (current_byte = 0; current_byte < count; ++current_byte) {
    #         crc ^= (data[current_byte]);
    #         for (crc_bit = 8; crc_bit > 0; --crc_bit) {
    #             if (crc & 0x80)
    #                 crc = (crc << 1) ^ CRC8_POLYNOMIAL;
    #             else
    #                 crc = (crc << 1);
    #         }
    #     }
    #     return crc;
    # }

    CRC8_POLYNOMIAL = 0x31
    CRC8_INIT       = 0xFF

    count           = len(data)
    crc             = CRC8_INIT
    for dbyte in data:
        # print("dbyte: ", dbyte)
        crc = (crc ^ dbyte) & 0xFF                                  # limit to uint8
        for i in range(0, 8):
            if crc & 0x80:  crc = (crc << 1) ^ CRC8_POLYNOMIAL
            else:           crc = crc << 1
            crc = crc & 0xFF                                        # limit to uint8
            # print("i: ", i, ", crc: ", crc)

    return crc


def getPortList(symlinks=True):
    """
    print serial port details. Include symlinks or not
    return: list of ports
    """

    # Pyserial:
    # 'include_links (bool)' – include symlinks under /dev when they point to a serial port
    # symlinks=False: symlinks NOT shown, default
    # symlinks=True:  symlinks shown, like /dev/geiger
    # https://github.com/pyserial/pyserial/blob/master/documentation/tools.rst

    # #
    # # on Linux
    # #
    # # GMC-300E+
    # /dev/ttyUSB0 - USB Serial
    #     p.name           : ttyUSB0
    #     p.hwid           : USB VID:PID=1A86:7523 LOCATION=3-1
    #     p.device         : /dev/ttyUSB0
    #     p.description    : USB Serial
    #     p.serial_number  : None
    #     p.location       : 3-1
    #     p.manufacturer   : None
    #     p.product        : USB Serial
    #     p.interface      : None
    #     p.vid            :  6790 (0x1A86)
    #     p.pid            : 29987 (0x7523)

    # # GMC-500+
    # /dev/ttyUSB1 - USB2.0-Serial
    #     p.name           : ttyUSB1
    #     p.hwid           : USB VID:PID=1A86:7523 LOCATION=3-1
    #     p.device         : /dev/ttyUSB1
    #     p.description    : USB2.0-Serial
    #     p.serial_number  : None
    #     p.location       : 3-1
    #     p.manufacturer   : None
    #     p.product        : USB2.0-Serial
    #     p.interface      : None
    #     p.vid            :  6790 (0x1A86)
    #     p.pid            : 29987 (0x7523)

    # # UBS-ISS
    # /dev/ttyACM0 - USB-ISS.
    #     p.name           : ttyACM0
    #     p.hwid           : USB VID:PID=04D8:FFEE SER=00027171 LOCATION=3-11:1.0
    #     p.device         : /dev/ttyACM0
    #     p.description    : USB-ISS.
    #     p.serial_number  : 00027171
    #     p.location       : 3-11:1.0
    #     p.manufacturer   : Devantech Ltd.
    #     p.product        : USB-ISS.
    #     p.interface      : None
    #     p.vid            :  1240 (0x04D8)
    #     p.pid            : 65518 (0xFFEE)

    # # ELV
    # /dev/ttyUSB0 - ELV USB-I2C-Interface - ELV USB-I2C-Interface
    #     p.name           : ttyUSB0
    #     p.hwid           : USB VID:PID=10C4:EA60 SER=TL4E6D5KBAHDFQF0 LOCATION=3-1
    #     p.device         : /dev/ttyUSB0
    #     p.description    : ELV USB-I2C-Interface - ELV USB-I2C-Interface
    #     p.serial_number  : TL4E6D5KBAHDFQF0
    #     p.location       : 3-1
    #     p.manufacturer   : Silicon Labs
    #     p.product        : ELV USB-I2C-Interface
    #     p.interface      : ELV USB-I2C-Interface
    #     p.vid            :  4292 (0x10C4)
    #     p.pid            : 60000 (0xEA60)

    # #
    # # on windows
    # #
    # # gmc-500+
    # COM3 - USB-SERIAL CH340 (COM3)
    #     p.name           : COM3
    #     p.hwid           : USB VID:PID=1A86:7523 SER= LOCATION=1-1.4
    #     p.device         : COM3
    #     p.description    : USB-SERIAL CH340 (COM3)
    #     p.serial_number  :
    #     p.location       : 1-1.4
    #     p.manufacturer   : wch.cn
    #     p.product        : None
    #     p.interface      : None
    #     p.vid            :  6790 (0x1A86)
    #     p.pid            : 29987 (0x7523)

    # # gmc-300E+
    # COM3 - USB-SERIAL CH340 (COM3)
    #     p.name           : COM3
    #     p.hwid           : USB VID:PID=1A86:7523 SER= LOCATION=1-1.4
    #     p.device         : COM3
    #     p.description    : USB-SERIAL CH340 (COM3)
    #     p.serial_number  :
    #     p.location       : 1-1.4
    #     p.manufacturer   : wch.cn
    #     p.product        : None
    #     p.interface      : None
    #     p.vid            :  6790 (0x1A86)
    #     p.pid            : 29987 (0x7523)

    # # ELV
    # COM7 - Silicon Labs CP210x USB to UART Bridge (COM7)
    #     p.name           : COM7
    #     p.hwid           : USB VID:PID=10C4:EA60 SER=TL4E6D5KBAHDFQF0 LOCATION=1-1.4
    #     p.device         : COM7
    #     p.description    : Silicon Labs CP210x USB to UART Bridge (COM7)
    #     p.serial_number  : TL4E6D5KBAHDFQF0
    #     p.location       : 1-1.4
    #     p.manufacturer   : Silicon Labs
    #     p.product        : None
    #     p.interface      : None
    #     p.vid            :  4292 (0x10C4)
    #     p.pid            : 60000 (0xEA60)

    # # USB-ISS
    # COM8 - Serielles USB-Gerät (COM8)
    #     p.name           : COM8
    #     p.hwid           : USB VID:PID=04D8:FFEE SER=00027171 LOCATION=1-1.2
    #     p.device         : COM8
    #     p.description    : Serielles USB-Gerät (COM8)
    #     p.serial_number  : 00027171
    #     p.location       : 1-1.2
    #     p.manufacturer   : Microsoft
    #     p.product        : None
    #     p.interface      : None
    #     p.vid            :  1240 (0x04D8)
    #     p.pid            : 65518 (0xFFEE)


    if symlinks:    msg = "(with symlinks)"
    else:           msg = "(without symlinks)"

    fncname = "getPortList: {} : ".format(msg)
    dprint(fncname)
    setIndent(1)

    # listofports example:
    #       [<serial.tools.list_ports_linux.SysFS object at 0x7f55fe582080>,
    #        <serial.tools.list_ports_linux.SysFS object at 0x7f55fe5826b0>]
    #
    # port attributes = ["name", "hwid", "device", "description", "serial_number",
    #                    "location", "manufacturer", "product", "interface", "vid", "pid"]

    lp = []
    try:
        lp = serial.tools.list_ports.comports(include_links=symlinks)
        # edprint(fncname + "listofports: ", lp)
    except Exception as e:
        msg = fncname + "lp: {}".format(lp)
        exceptPrint(e, msg)
    lp.sort()                 # sorted by device
    # lp.sort(reverse=True)       # sorted by device, reverse
    # edprint(fncname + "listofports: ", lp)

    ######## TESTING only ##############
    #    lp.append("/dev/ttyS0 - ttyS0")    # add a ttyS* to the list of ports
    ####################################

    dprint("Ports detected:")
    if len(lp) == 0:
        dprint("   None")
    else:
        # example output:
        #   Ports detected:
        #       /dev/ttyACM0 - USB-ISS.
        #       /dev/ttyUSB0 - USB2.0-Serial
        for p in lp:    dprint("   ",  p)

    # only devel printout
    if gglobs.devel and len(lp) > 0:
        cdprint("Ports detailed:")
        setIndent(1)
        # complete list of attributes for serial.tools.list_ports.comports()
        lpAttribs = ["device", "name", "hwid", "description", "serial_number", "location", "manufacturer", "product", "interface", "vid", "pid"]
        try:
            for p in lp:
                cdprint(p)
                for pA in lpAttribs:
                    if pA == "vid" or pA == "pid":
                        x = getattr(p, pA, 0)
                        if x is None:   cdprint("   {:16s} : None".format("p." + pA))
                        else:           cdprint("   {:16s} : {:5d} (0x{:04X})".format("p." + pA, x, x))
                    else:
                        cdprint("   {:16s} : {}".format("p." + pA, getattr(p, pA, "None")))
                cdprint()
        except Exception as e:
            msg = fncname + "lp: {}".format(lp)
            exceptPrint(e, msg)
        setIndent(0)

    setIndent(0)
    return lp


def getSerialPortListing():
    """get Port Listing in HTML Format and as list"""
    # NOTE: see: getPortList() for list of attributes to Portlist

    fncname = "getSerialPortListing: "

    selection_ports    = []

    lp = getPortList(symlinks=True) # ist in gsup_utils.py
    # print("-----------------lp:          : ", lp)

    hsp = "<b>Available Ports:</b><pre>"
    hsp += "\n{:15s} {:30s}  {:14s}   {:s}\n{}\n".format("Port",
                                                            "Name of USB-to-Serial Hardware",
                                                            "Linked to Port",
                                                            "VID :PID",
                                                            "-" * 74)

    if len(lp) == 0:
        errmessage = "FAILURE: No Available Ports found"
        dprint(fncname + errmessage, debug=True)
        hsp += "<span style='color:red;'>" + errmessage + "\nIs any device connected? Check cable and plugs! Re-run in a few seconds.</span>" + "\n\n\n"
        # enableSelections = False
    else:
        for p in lp:
            #~print("\np: ", p)
            try:
                # link = "No Link"
                link = "Not a Link"
                if hasattr(p, "hwid") and "LINK=" in p.hwid:
                    link1 = p.hwid.find("LINK=")
                    link2 = p.hwid.find("LINK=", link1 + 5)
                    #~print("device:", p.device, ",   hwid:", p.hwid)
                    #~print("link1: ", link1, ", link2: ", link2)
                    if link2 > 0:   link = p.hwid[link1 + 5 : link2]
                    else:           link = p.hwid[link1 + 5 : ]

                p_device        = getattr(p, "device",      "None")
                p_description   = getattr(p, "description", "None")
                #~print("p_description: ", p_description)
                if len(p_description) > 28: p_description = p_description[:27] + "..." # do not show complete length
                #~print("p_device:      ", p_device)
                #~print("p_description: ", p_description)

                p_vid           = getattr(p, "vid",         0)
                if p_vid is None:   strp_vid = "None"
                else:               strp_vid = "{:04X}".format(p_vid)

                p_pid           = getattr(p, "pid",         0)
                if p_pid is None:   strp_pid = "None"
                else:               strp_pid = "{:04X}".format(p_pid)

                if p_device != "None":
                    selection_ports.append(p.device)
                    hsp += "{:15s} {:30s}  {:14s}   {}:{}\n".format(p_device, p_description, link, strp_vid, strp_pid)

            except Exception as e:
                dprint(fncname + "Exception: {}  list_port: {}".format(e, p))
                # enableSelections = False

    hsp += "</pre>"

    return (hsp, selection_ports)


def setDeviceSerialPort(DevName, USBport):
    """sets the GMC Device Serial Port and its Baud rate"""

    fncname = "setDeviceSerialPort: "

    dprint(fncname)
    setIndent(1)

    hsp1, selection_ports = getSerialPortListing()

    # ComboBox Ports
    portCbBoxGMC = QComboBox()
    portCbBoxGMC.addItems(["auto"])
    portCbBoxGMC.addItems(selection_ports)
    portCbBoxGMC.setToolTip("Select the USB-to-Serial port for device '{}'".format(DevName))
    portCbBoxGMC.setMaximumWidth(200)

    if portCbBoxGMC.findText(USBport) == -1:    portCbBoxGMC.setCurrentIndex(0)
    else:                                       portCbBoxGMC.setCurrentIndex(portCbBoxGMC.findText(USBport))

    # hsp1label: Ports Listing Text
    hsp1label = QLabel()
    hsp1label.setText(hsp1)
    hsp1label.setWordWrap(True)

    # hsp2label
    hsp2  = "<p><br>Select the Serial (USB) port for your device. \
                GeigerLog's current settings are pre-selected <b>if available</b>.<br>"
    hsp2label = QLabel()
    hsp2label.setText(hsp2)
    hsp2label.setWordWrap(True)

    # H-Layout
    cblayoutGMC = QHBoxLayout()
    cblayoutGMC.addWidget(hsp2label)
    cblayoutGMC.addWidget(portCbBoxGMC)

    # hsp3label
    hsp3text = "<p>After pressing OK all of GeigerLog's devices will become disconnected.\
                (Re-)connect and (re-)start logging after all port settings are completed.\
                <p>Press Cancel to close without making any changes. "
    hsp3label = QLabel()
    hsp3label.setText(hsp3text)
    hsp3label.setWordWrap(True)

    # Dialog Box
    title = "Set Serial Port of Device '{}'".format(DevName)
    d = QDialog()
    d.setWindowIcon(gglobs.exgg.iconGeigerLog)
    d.setWindowTitle(title)
    d.setWindowModality(Qt.WindowModal)

    # Button Box
    bbox = QDialogButtonBox()
    bbox.setStandardButtons(QDialogButtonBox.Ok| QDialogButtonBox.Cancel)   # set Ok + Cancel button
    bbox.accepted.connect(lambda: d.done(1))     # ok
    bbox.rejected.connect(lambda: d.done(0))     # cancel, same for ESC, close window

    # dialog layout
    layoutV = QVBoxLayout(d)
    layoutV.addWidget(hsp1label)
    layoutV.addLayout(cblayoutGMC)
    layoutV.addWidget(hsp3label)
    layoutV.addWidget(bbox)

    retval = d.exec()               # returns 1 for Ok, 0 for Cancel, ESC, window close
    # print("---retval=",retval)

    if retval != 1:
        vprint(fncname + "cancelled by user")
        USBport = None

    else:
        gglobs.exgg.switchAllConnections(new_connection = "OFF")

        fprint(header(title))

        USBport = portCbBoxGMC.currentText()
        msg = ("New Serial Port:", "{}".format(USBport))
        dprint(fncname, *msg)
        fprint(*msg)
        fprint("<br><blue><b>INFO:</b> all devices are now disconnected.")

        if   DevName == "GMC":          gglobs.GMC_usbport = USBport
        elif DevName == "I2C":          gglobs.I2Cusbport  = USBport
        elif DevName == "GammaScout":   gglobs.GSusbport   = USBport

    setIndent(0)


def showPortSettings():
    """Show Settings of Serial Ports for all activated devices using Serial port"""

    fprint(header("Device Port Settings"))
    fprint("Port configuration of all activated devices using a serial port:")

    devtmplt   = "Device: {}  Port: {:15s}  Baudrate: {}\n"
    devsetting = ""
    devcount   = 0
    for devname in ["GMC", "I2C", "GammaScout"]:
        if gglobs.Devices[devname][ACTIV]:
            devcount += 1
            if   devname == "GMC":          devsetting += devtmplt.format(devname, gglobs.GMC_usbport, gglobs.GMC_baudrate)
            elif devname == "I2C":          devsetting += devtmplt.format(devname, gglobs.I2Cusbport,  gglobs.I2Cbaudrate)
            elif devname == "GammaScout":   devsetting += devtmplt.format(devname, gglobs.GSusbport,   gglobs.GSbaudrate)

    if devcount == 0: devsetting = "There are no devices using the Serial Port"
    fprint(devsetting)
    edprint(devsetting)


def initLogThread():
    """initialize and start the Log Thread"""

    fncname = "initLogThread: "

    dprint(fncname)
    setIndent(1)

    gglobs.LogThreadStopFlag = False
    gglobs.LogThreadStartTime = time.time()

    gglobs.LogThread = threading.Thread(target = LogThreadTarget)
    dprint("LogThread.daemon:      ", gglobs.LogThread.daemon)
    gglobs.LogThread.start()
    dprint("LogThread.is_alive:    ", gglobs.LogThread.is_alive())

    setIndent(0)


def terminateLogThread():
    """end the Log thread"""

    fncname = "terminateLogThread: "

    # cdprint(fncname)
    start = time.time()

    gglobs.LogThreadStopFlag = True
    gglobs.LogThread.join()
    while gglobs.LogThread.is_alive() and time.time() < start + 5:
        dprint("LogThread alive?    ", gglobs.LogThread.is_alive())
        time.sleep(0.01)

    dprint(fncname + "done ({:0.3f} ms)".format(1000 * (time.time() - start)))


def LogThreadTarget():
    """The Target function for the logging thread"""

    fncname  = "LogThreadTarget: "

    nexttime = time.time() + 0.01       # allows to skip first 10 msec to let printouts finish
    while not gglobs.LogThreadStopFlag:
        if time.time() >= nexttime:
            nexttime += gglobs.logCycle
            runLogCycle()
        time.sleep(0.010)               # gives a 10 ms precision of calling the runLogCycle


#xyz
def runLogCycle():
    """run 1 cycle of fetch, save, request flags setting"""

    # request logCycle button Off (during data fetching and saving) as early as possible
    gglobs.logCycleButtonFlag = "Off"

    fncname   = "runLogCycle: "

    rLC_start = time.time()
    msgfmt    = "{:<25s}  {:6.2f} "
    fetchDur  = gglobs.NAN
    saveDur   = gglobs.NAN
    totalDur  = gglobs.NAN

    if gglobs.verbose: print("")                                              # print empty line
    vprint(fncname + "saving to:", gglobs.logDBPath)
    setIndent(1)

# update index (=LogReadings)
    gglobs.LogReadings += 1

# set the timestamps for this record
    timeJulian = gglobs.JULIANUNIX + (time.time() + 3600) / 86400   # why the extra hour?

    # For LogPad use no date, only time with 100 ms:  '2018-07-14 12:00:52.342' --> '12:00:52.3'
    msgLogPad  = "{:10s} ".format(medstime())
    # edprint(fncname + "timeJulian: ", timeJulian, "  time Logpad: ", msgLogPad)


# fetch the data from all devices
    # Example logvalues:
    #       {'CPM': 18110.0, 'CPS': 297.0, 'CPM1st': nan, 'CPS1st': nan, 'CPM2nd': nan, 'CPS2nd': nan,
    #        'CPM3rd': nan, 'CPS3rd': nan, 'Temp': 295, 'Press': 293.8, 'Humid': 277, 'Xtra': 18}
    s1        = time.time()
    logValues = gglobs.exgg.fetchLogValues()
    fetchDur  = 1000 * (time.time() - s1)


# save Log values - but only if at least one value is non-nan
    # check for NAN, and update all "lastLogValues" with new logValues, but only if new value is not NAN
    nanOnly = True
    for vname in gglobs.varsCopy:
        # edprint(fncname + "vname: ", vname)
        if not np.isnan(logValues[vname]):
            nanOnly                     = False
            gglobs.lastLogValues[vname] = logValues[vname]

    if nanOnly:
        # all are NAN - no saving, no display, no graph, but LogPad
        msgLogPad += "     No data"
        gglobs.logLogPadDeque.append((msgLogPad, logValues))
    else:
        # at least one value is not nan - update database
        s1       = time.time()
        save_msg = saveLogValuesToDB(timeJulian, logValues)
        saveDur  = 1000 * (time.time() - s1)


# request update queue for mem (takes under 1 ms)
        saveLogValuesToQueue(timeJulian, logValues)


# request update Displays
        gglobs.needDisplayUpdate = True


# request update LogPad queue
        gglobs.logLogPadDeque.append((msgLogPad, logValues))


# request check of duration against cycle
    totalDur = 1000 * (time.time() - rLC_start)                 # in millisec
    gglobs.runLogCycleDurs = [fetchDur, saveDur, totalDur]      # list of durs


# printout
    vprint(msgfmt.format("getValues Total:",    fetchDur))
    vprint(msgfmt.format("saveToDB:",           saveDur ))
    vprint(msgfmt.format("runLogCycle Total:",  totalDur))

    setIndent(0)


# request logCycle button On (as late as possible)
    gglobs.logCycleButtonFlag = "On"


def saveLogValuesToDB(timeJulian, logValues):
    """Save data to database"""

    # in >50000 writes average was 15.6 ms, Stddev = 3.0, maximum 300ms(!)

    fncname = "saveLogValuesToDB: "

    datalist     = [None] * (gglobs.datacolsDefault + 2)        # (13 + 2) x None; 2 wg index + extra for Julianday
    datalist[0]  = gglobs.LogReadings                           # store the index
    datalist[1]  = "NOW"                                        # time stamp
    datalist[2]  = "localtime"                                  # modifier for time stamp

    for i, vname in enumerate(gglobs.varsCopy):
        datalist[3 + i] = logValues[vname]                      # data into datalist[3 + following]

    # Write to database file
    from gsup_sql import DB_insertData
    DB_insertData(gglobs.logConn, [datalist])

    # edprint(fncname + "saving done", " logvalues: ", logValues)


def saveLogValuesToQueue(timeJulian, logValues):
    """Save data to memory"""

    fncname = "saveLogValuesToQueue: "

    datalist = [
                                                    # no index
                timeJulian - gglobs.JULIAN111,      # time is set to matplotlib time
                logValues["CPM"],
                logValues["CPS"],
                logValues["CPM1st"],
                logValues["CPS1st"],
                logValues["CPM2nd"],
                logValues["CPS2nd"],
                logValues["CPM3rd"],
                logValues["CPS3rd"],
                logValues["Temp"],
                logValues["Press"],
                logValues["Humid"],
                logValues["Xtra"],
                ]

    # append to deque queue
    gglobs.logMemDataDeque.append(datalist)


# is not used
def get_julian_datetime(date):
    """
    Convert a datetime object into julian float.
    Args:
        date: datetime-object of date in question

    Returns: float - Julian calculated datetime.
    Raises:
        TypeError : Incorrect parameter type
        ValueError: Date out of range of equation
    """

    # from: https://stackoverflow.com/questions/31142181/calculating-julian-date-in-python/52431241#52431241

    import math

    # usage:
    # mydatetime = datetime.datetime.now()
    # timeJulian, timetag = get_julian_datetime(mydatetime), mydatetime.strftime("%Y-%m-%d %H:%M:%S")
    # print("timeJulian, timetag: ", timeJulian, timetag)

    # Ensure correct format
    if not isinstance(date, datetime.datetime):
        raise TypeError('Invalid type for parameter "date" - expecting datetime')
    elif date.year < 1801 or date.year > 2099:
        raise ValueError('Datetime must be between year 1801 and 2099')

    # Perform the calculation
    julian_datetime = 367 * date.year - int((7 * (date.year + int((date.month + 9) / 12.0))) / 4.0) + int(
        (275 * date.month) / 9.0) + date.day + 1721013.5 + (
                          date.hour + date.minute / 60.0 + date.second / math.pow(60,2)) / 24.0 - 0.5 * math.copysign(
        1, 100 * date.year + date.month - 190002.5) + 0.5

    return julian_datetime


def is_raspberrypi():
    """check if it is a Raspberry Pi computer"""

    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
            if 'raspberry pi' in m.read().lower(): return True
    except Exception: pass
    return False


def printColorCodesToTerminal():

    #   TBLUE               = '\033[94m'            # blue (dark)
    #   BOLDRED             = '\033[91;1m'          # bold, red

    # for i in range(0, 108): # all same plain white text AND black background from 108 onwards
    #     print("\033["+ str(i) + "m", end="")
    #     print("'\\033[{:n}m'    Der süße Björn macht ständig Ärger".format(i), TDEFAULT)

    # print(TDEFAULT + "Now with ;1m -------------------")
    # for i in range(0, 108):  # all same plain white text AND black background from 108 onwards
    #     print("\033["+ str(i) + ";1m", end="")
    #     print("'\\033[{:n};1m'    Der süße Björn macht ständig Ärger".format(i), TDEFAULT)

    # alle ';1m' sind heller, da bold
    # 41 ... 47 (7x) und 100 ... 107 (8x) alles weisse Schrift auf Farbe
    for i in range(0, 108): # all the same plain white text AND black background from 108 onwards
        print("\033["+ str(i) + "m", end="")
        print("'\\033[{:n}m'      Der süße Björn macht ständig Ärger".format(i), TDEFAULT)

        print("\033["+ str(i) + ";1m", end="")
        print("'\\033[{:n};1m'    Der süße Björn macht ständig Ärger".format(i), TDEFAULT)
