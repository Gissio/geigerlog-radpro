#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GLpipcheck.py - To check Pip version status of GeigerLog requirements
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

"""
using pip venv in Windows: https://discuss.python.org/t/pip-missing-from-my-python-download/13750

# requirements.txt
# possible content of a requirements.txt file:
# install with:
#       python -m pip install -r requirements.txt
# requirements.txt:
    pip         >=  21.0.1
    setuptools  >=  54.0.0
    pyqt5       >=  5.15.3
    PyQt5-Qt    >=  5.15.2
    pyqt5-sip   >=  12.8.1
    matplotlib  >=  3.3.4
    numpy       >=  1.20.1
    scipy       >=  1.6.1
    pyserial    >=  3.5
    paho-mqtt   >=  1.5.1
    sounddevice >=  0.4.1
    soundfile   >=  0.10.3.post1
    pip-check   >=  2.6


# February 2021:
    GeigerLog installed REQUIRED packages and their version status
       pip                21.0.1            OK
       setuptools         53.0.0            OK
       PyQt5              5.15.2            OK
       PyQt5-sip          12.8.1            OK
       numpy              1.20.0            OK
       scipy              1.6.0             OK
       matplotlib         3.3.4             OK
       sounddevice        0.4.1             OK
       SoundFile          0.10.3.post1      OK

    GeigerLog installed OPTIONAL packages and their version status
       pyserial           3.5               OK         REQUIRED for GMC, GS, I2C Series
       paho-mqtt          1.5.1             OK         REQUIRED for RadMon Series
       LabJackPython      2.0.0             OK         REQUIRED for LabJack Series
       pip-check          2.6               OK         recommended Pip tool

    GeigerLog REQUIRED packages having upgrades available:
       Package            Version           Latest     Type
       None

    GeigerLog OPTIONAL packages having upgrades available:
       Package            Version           Latest     Type
       LabJackPython      2.0.0             2.0.4      wheel
"""


__author__          = "ullix"
__copyright__       = "Copyright 2016, 2017, 2018, 2019, 2020, 2021, 2022"
__credits__         = [""]
__license__         = "GPL3"
__version__         = "1.4"


import sys, subprocess
import getopt                       # parse command line for options and commands

# Apparently this got reverted back to the original:
# Find    all available versions of package 'anypackage':      python3 -m pip --use-deprecated=legacy-resolver install anypackage==
# now again works as:
# Find    all available versions of package 'anypackage':      python3 -m pip install anypackage==

howto = """
Mini-HOWTO: --------------------------------------------------------------------------------------------------------------------
for using 'pip':
NOTE:   when 'pip' itself or 'setuptools' can be upgraded, upgrade 'pip' first, then 'setuptools', then any others
NOTE:   when using '=', '==', '>', '<' for version definition you need to use quotation marks around package designation
        like: "anypackage == 1.2.3",  "anypackage >=1, <2"

Install and/or update package 'anypackage':                  python3 -m pip install -U anypackage

Install and/or update multiple packages at once:             python3 -m pip install -U anypackage 2ndpackage 3rdpackage ...
        NOTE:
        If command fails, nothing at all may have been installed!
        Continue with single-package installations.

Install package 'anypackage' in exactly version 1.2.3:       python3 -m pip install "anypackage == 1.2.3"

Install package 'anypackage' in version of
        at least 1 but not 2 or later:                       python3 -m pip install "anypackage >=1, <2"

Install all packages as specified in GLrequirements.txt      python3 -m pip install -r GLrequirements.txt
        Format of GLrequirements.txt is:
            pip         ==  21.3.1
            setuptools  ==  60.5.0
            pyqt5       ==  5.15.6
            pyqt5-sip   ==  12.9.0
            ...

Remove  package 'anypackage':                                python3 -m pip uninstall anypackage

Find    all available versions of package 'anypackage':      python3 -m pip install anypackage==


---------------------------------------------------------------------------------------------------------------------------------
"""

req_installs = {
                "pip"           : ["latest"     , "", False],
                "setuptools"    : ["latest"     , "", False],
                "PyQt5"         : ["latest"     , "", False],
                #"PyQt5-Qt"      : ["latest"     , "Missing is ok if PyQt5-Qt5 is present", False],
                #"PyQt5-Qt5"     : ["latest"     , "", False],
                "PyQt5-sip"     : ["latest"     , "", False],
                "numpy"         : ["latest"     , "", False],
                "scipy"         : ["latest"     , "", False],
                "matplotlib"    : ["latest"     , "", False],
                "sounddevice"   : ["latest"     , "", False],
                "SoundFile"     : ["latest"     , "", False],
                "pyserial"      : ["latest"     , "", False],
               }

opt_installs = {
                "RPi.GPIO"              : ["latest"     , "REQUIRED for RaspiPulse Series"              , False],
                "smbus"                 : ["latest"     , "REQUIRED for RaspiI2C Series"                , False],
                "paho-mqtt"             : ["latest"     , "REQUIRED for RadMon Series"                  , False],
                "LabJackPython"         : ["latest"     , "REQUIRED for LabJack Series"                 , False],
                # "python-telegram-bot"   : ["latest"     , "REQUIRED for Telegram Messenger"           , False],
                "psutil"                : ["latest"     , "REQUIRED for Devel Mode System monitoring"   , False],
                "pip-check"             : ["latest"     , "Recommended Pip tool"                        , False],
               }

req_install             = []
req_upgrade             = []
opt_install             = []
opt_upgrade             = []
need_pip_upgrade        = False
need_setuptools_upgrade = False


def removeSpaces(text):
    """no more than single space allowed"""

    while True:
        text2 = text.replace("  ", " ")           # replace 2 space with 1 space
        if len(text2) < len(text): text = text2
        else:                      return text2


def showPipList(piplist):
    """prints all from 'pip list'output"""

    print("Listing of all Pip-found packages:")

    for pl in piplist:  print("  ", pl)


def showPackages(ptype):    # ptype = "OPTIONAL" or "REQUIRED"
    """call pip list and search for required or optional packages and their
    version, and install status"""

    global req_install, opt_install

    print("\nGeigerLog installed {} packages and their version status".format(ptype))

    if ptype == "REQUIRED":  installs = req_installs
    else:                    installs = opt_installs

    pf = "   {:19s} {:16s}  {:10s} {}"
    for ins in installs:
        #print("ins: ", ins)
        if ins in pipdict:
            print(pf.format(ins, pipdict[ins], "OK",      installs[ins][1]))
        else:
            print(pf.format(ins, ""          , "MISSING", installs[ins][1]))
            if ptype == "REQUIRED":     req_install.append(ins)
            else:                       opt_install.append(ins)


def showVersionFromPipOutdatedList(ptype): # ptype = "OPTIONAL" or "REQUIRED"
    """Call 'pip list --outdated' """

    """
    Example output of call 'pip list --outdated':
    Package Version Latest Type
    ------- ------- ------ -----
    cffi    1.14.2  1.14.4 wheel
    idna    2.10    3.1    wheel
    """

    global req_upgrade, opt_upgrade, need_pip_upgrade, need_setuptools_upgrade

    msg = "\nGeigerLog installed {} packages having upgrades available:".format(ptype)

    if ptype == "REQUIRED":  installs = req_installs
    else:                    installs = opt_installs

    pf       = "   {:19s} {:16s}  {:10s} {}"
    counter  = 0
    ins      = "Package"
    print(msg)
    #print("len(pipODdict): ", len(pipODdict), pipODdict)
    if len(pipODdict) > 0:
        print(pf.format(ins, pipODdict[ins][0], pipODdict[ins][1], pipODdict[ins][2]))
        for ins in installs:
            #print("ins: ", ins)
            if ins in pipODdict:
                print(pf.format(ins, pipODdict[ins][0], pipODdict[ins][1], pipODdict[ins][2]))
                counter += 1
                if ptype == "REQUIRED":
                    if      ins == "pip":           need_pip_upgrade = True
                    elif    ins == "setuptools":    need_setuptools_upgrade = True
                    else:                           req_upgrade.append(ins)
                else:
                    opt_upgrade.append(ins)

        if counter == 0: print("   <None>")
    else:
        print("   -N.A.-")

###############################################################################

def main():

    global req_installs, opt_installs, pipdict, pipODdict, req_upgrade, req_install, opt_upgrade, opt_install

    print("\n---------------------- GLpipcheck.py ------------------------------------------")

    # parse command line options
    # sys.argv[0] is progname
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hV", ["help", "Version"])
    except getopt.GetoptError as e :
        # print info like "option -a not recognized", then exit
        msg = "\nFor Help use: 'GLpipcheck -h'"
        print("ERROR: ", e, msg)
        return 1

    # processing the options
    for opt, optval in opts:
        if   opt in ("-h", "--help"):
            print(howto)
            return 0

        elif opt in ("-V", "--Version"):
            print("Version: ", __version__)
            return 0

    #print("************ Print Mini-HOWTO by starting with: 'GLpipcheck -h' ***************\n")
    print("GLpipcheck Version: ", __version__)
    print("Python Executable:  ", sys.executable)
    print("Python Version:     ", sys.version.replace('\n', " "))
    print()

    # create the 'pip list'
    pip_output = subprocess.check_output([sys.executable, '-m', 'pip', 'list'])
    piplist    = pip_output.decode('UTF-8').strip().split("\n")
    #print("piplist: \n", piplist)
    showPipList(piplist)

    pipdict = {}
    for pl in piplist:
        snr = removeSpaces(pl).split(" ", 1)
        # print("snr: ", snr)
        if len(snr) > 1: pipdict.update({snr[0].strip(): snr[1].strip()})

    showPackages("REQUIRED")
    showPackages("OPTIONAL")

    print()
    print("Checking for updates ... ", end="", flush=True)

    # create the OD:  'pip list --outdated'
    pipOD_output = subprocess.check_output([sys.executable, '-m', 'pip', 'list', '--outdated'])
    #print("pipOD_output:", len(pipOD_output), pipOD_output)

    pipODlist = pipOD_output.decode('UTF-8').strip().split("\n")
    #print("pipODlist:", len(pipODlist), pipODlist)

    pipODdict = {}
    for pl in pipODlist:
        snr = removeSpaces(pl).split(" ", 4)
        #print("snr: ", snr, "len(snr): ", len(snr))
        if len(snr) > 1:
            pipODdict.update({snr[0].strip(): [snr[1].strip(), snr[2].strip(), snr[3].strip()]})

    print("Done")

    showVersionFromPipOutdatedList("REQUIRED")
    showVersionFromPipOutdatedList("OPTIONAL")

    print()
    print(howto)


if __name__ == '__main__':
    main()
