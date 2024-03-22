#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gmain.py - GeigerLog main entry file

include in programs with:
    import gmain
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


from   gsup_utils            import *   # includes import of gglobs



def verifyPythonVersion():
    """Verify proper Python version"""

    # currently at least 3.7 is needed

    # Python 3.5
    #   Python 3.5 reached end of life on September 13th, 2020.
    #   pip 21.0 will drop support for Python 3.5 in January 2021.
    #   Python 3.5 does NOT support ordered dicts, resulting in major problems!
    # Python 3.6
    #   Python 3.6 reached end of life on 23 Dec 2021
    #   Python 3.6 has no threading HTTP server

    # Python 3.7  will reach end of life on 27 Jun 2023
    # Python 3.8  will reach end of life on 14 Oct 2024
    # Python 3.9  will reach end of life on 05 Oct 2025
    # Python 3.10 will reach end of life on 04 Oct 2026
    #

    svi              = sys.version_info
    currentPyVersion = "{}.{}.{}".format(svi[0], svi[1], svi[2])

    if svi < (3, 7):    # Python version >= v3.7 is required.
        msg = """
            GeigerLog V{} requires<br><br><b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Python in version 3.7 or later,</b><br><br>
            but your Python version is only: {}.<br><br>
            See chapter "Appendix I – Installation" in the GeigerLog manual for upgrade options.
            <br><br>
            Cannot continue, will exit.
            """.format(gglobs.__version__, currentPyVersion)

    else: # Python has proper version
        msg = ""

    return msg


def main():
    """GeigerLog Main File"""

# proper Python version?
    gglobs.python_version = verifyPythonVersion()   # result will be handled in ggeiger.py


# set directories and file names
    gglobs.progName         = getProgName   ()
    gglobs.progPath         = getProgPath   ()
    gglobs.gresPath         = getGresPath   ()
    gglobs.webPath          = getWebPath    ()
    gglobs.dataPath         = getDataPath   ()
    gglobs.proglogPath      = getProglogPath()
    gglobs.stdlogPath       = getStdlogPath ()
    gglobs.configPath       = getConfigPath ()
    gglobs.fileDialogDir    = getDataPath   ()

# set GeigerLog's IP
    gglobs.GeigerLogIP      = getGeigerLogIP()

# data directory: Make sure it exists; create it if needed
    # exit if it cannot be made or is not writable
    if os.access(gglobs.dataPath , os.F_OK): # test for file exists
        # dir exists, ok
        if not os.access(gglobs.dataPath , os.W_OK):
            # dir exists, but is not writable
            print("ERROR: main: Data directory '{}' exists, but is not writable".format(gglobs.dataDirectory))
            return 1
    else:
        # dir does not exist; make it
        try:
            os.mkdir(gglobs.dataPath )
        except Exception as e:
            # dir cannot be made
            print("ERROR: main: Could not make data directory '{}'".format(gglobs.dataDirectory))
            return 1

# gres directory: Make sure it exists and is readable
    if os.access(gglobs.gresPath , os.F_OK):
        # dir exists, ok
        if not os.access(gglobs.dataPath , os.R_OK):
            # dir exists, but is not readable
            print("ERROR: main: GeigerLog resource directory {} exists but is not readable".format(gglobs.gresPath))
            return 1
    else:
        print("ERROR: main: GeigerLog resource directory {} does not exist. You may have to reinstall GeigerLog".format(gglobs.gresPath))
        return 1

# gweb directory: Make sure it exists and is readable
    if os.access(gglobs.webPath , os.F_OK):
        # dir exists, ok
        if not os.access(gglobs.dataPath , os.R_OK):
            # dir exists, but is not readable
            print("ERROR: main: GeigerLog web directory {} exists but is not readable".format(gglobs.webPath))
            return 1
    else:
        print("ERROR: main: GeigerLog web directory {} does not exist. You may have to reinstall GeigerLog".format(gglobs.webPath))
        return 1

# parse command line options
    try:
        # sys.argv[0] is progname
        opts, args = getopt.getopt(sys.argv[1:], "hdvwl:VPs:", ["help", "debug", "verbose", "logfile=", "werbose", "Version", "Portlist", "style="])
    except getopt.GetoptError as e :
        # print info like "option -x not recognized", then exit
        msg = "For Help use: './geigerlog -h'"
        exceptPrint(e, msg)
        return 1

    # processing the options
    for opt, optval in opts:
        # NOTE: option "-s, --style" is handled below, see: # Style

        if   opt in ("-h", "--help"):
            print (gglobs.helpOptions)
            return 0

        elif opt in ("-V", "--Version"):    # show the GeigerLog and modules versions
            print("Version status:")
            for ver in gglobs.versions: print("   {:25s}: {}".format(ver, gglobs.versions[ver]))
            return 0

        elif opt in ("-P", "--Portlist"):   # which ports are available?
            lp = serial.tools.list_ports.comports(include_links=True)  # default; include_links=True also shows symlinks
            print("\nAvailable USB-to-Serial ports with symlinks:")
            for p in lp:     print("   ", p)
            if len(lp) == 0: print("   ", "None")
            return 0

        elif opt in ("-d", "--debug"):
            gglobs.debug    = True

        elif opt in ("-v", "--verbose"):
            gglobs.verbose  = True
            gglobs.debug    = True          # giving verbose implies debug

        elif opt in ("-w", "--werbose"):
            gglobs.werbose  = True
            gglobs.verbose  = True          # giving werbose implies verbose
            gglobs.debug    = True          # giving verbose implies debug

        elif opt in ("-s", "--style"):      # style can only be set AFTER QApplication is defined, see below
            pass

        elif opt in ("-l", "--logfile"):
            gglobs.autoLogFile = optval.strip().replace(" ", "") + ".logdb"  # remove any space


    # processing the args
    for arg in args:
        if arg.lower() == "showstyles":
            print("Styles found on system: ")
            for a in QStyleFactory.keys():  print("   " + a)
            return 0

        elif arg.lower() == "devel":      gglobs.devel                = True
        elif arg.lower() == "trace":      gglobs.traceback            = True  # to printout traceback info

        elif arg.lower() == "connect":    gglobs.autoDevConnect       = True  # autostart stuff
        elif arg.lower() == "load":       gglobs.autoLogLoad          = True
        elif arg.lower() == "start":      gglobs.autoLogStart         = True
        elif arg.lower() == "quick":      gglobs.autoQuickStart       = True

        elif arg.lower() == "fullhist":   gglobs.fullhist             = True
        elif arg.lower() == "keepff":     gglobs.keepFF               = True
        elif arg.lower() == "forcelw":    gglobs.forcelw              = True  # force Linebreak on lines longer than screen
        elif arg.lower() == "testing":    gglobs.testing              = True
        elif arg.lower() == "timing":     gglobs.timing               = True
        elif arg.lower() == "osterei":    gglobs.AudioOei             = True
        elif arg.lower() == "graphemph":  gglobs.graphemph            = True  # thick lines for all vars
        elif arg.lower() == "stattest":   gglobs.stattest             = True
        elif arg.lower() == "gstesting":  gglobs.gstesting            = True  # required for GammaScout as simulation

        elif arg.lower() == "test1":      gglobs.test1                = True
        elif arg.lower() == "test2":      gglobs.test2                = True
        elif arg.lower() == "test3":      gglobs.test3                = True
        elif arg.lower() == "test4":      gglobs.test4                = True

        elif arg.lower() == "gmc":        gglobs.Devices["GMC"]         [ACTIV] = True
        elif arg.lower() == "audio":      gglobs.Devices["Audio"]       [ACTIV] = True
        elif arg.lower() == "radmon":     gglobs.Devices["RadMon"]      [ACTIV] = True
        elif arg.lower() == "ambio":      gglobs.Devices["AmbioMon"]    [ACTIV] = True
        elif arg.lower() == "gscout":     gglobs.Devices["GammaScout"]  [ACTIV] = True
        elif arg.lower() == "i2c":        gglobs.Devices["I2C"]         [ACTIV] = True
        elif arg.lower() == "labjack":    gglobs.Devices["LabJack"]     [ACTIV] = True
        elif arg.lower() == "minimon":    gglobs.Devices["MiniMon"]     [ACTIV] = True
        elif arg.lower() == "simul":      gglobs.Devices["Simul"]       [ACTIV] = True
        elif arg.lower() == "wific":      gglobs.Devices["WiFiClient"]  [ACTIV] = True
        elif arg.lower() == "wifis":      gglobs.Devices["WiFiServer"]  [ACTIV] = True
        elif arg.lower() == "ri2c":       gglobs.Devices["RaspiI2C"]    [ACTIV] = True
        elif arg.lower() == "rpulse":     gglobs.Devices["RaspiPulse"]  [ACTIV] = True
        elif arg.lower() == "manu":       gglobs.Devices["Manu"]        [ACTIV] = True
        elif arg.lower() == "radpro":     gglobs.Devices["Rad Pro"]     [ACTIV] = True

        # activate all devices
        elif arg.lower() == "all":
            for key in gglobs.Devices:    gglobs.Devices[key]           [ACTIV] = True


    if gglobs.devel:
        # under devel show all warnings always
        # print("sys.warnoptions: ", sys.warnoptions) # is always: sys.warnoptions:  []
        if not sys.warnoptions:
            # warnings.simplefilter("default")         # Change the filter in this process
            warnings.simplefilter("always")            # Change the filter in this process
            os.environ["PYTHONWARNINGS"] = "default"   # Also affect subprocesses; print with comannd: printenv
    else:
        # hide all warnings when in regular use, i.e. non-devel use
        if not sys.warnoptions:
            warnings.simplefilter("ignore")

# clear and initialize the program log files: 'geigerlog.proglog' and 'geigerlog.proglog.zip'
    clearProgramLogFile()

# set terminal output with or without line wrapping (works in Linux only)
    executeTPUT(action = 'no_line_wrapping')

# Signal handlers
    # Attention on Windows:
    # see: https://docs.microsoft.com/en-us/previous-versions/xdkz3x12(v=vs.140)
    # SIGINT :  CTRL+C signal, but: "SIGINT is not supported for any Win32 application."
    # SIGTSTP:  CTRL-Z signal, NOT supported on Windows!!!
    #
    #~print("signal.SIG_DFL: {:2d}  ".format(signal.SIG_DFL), signal.SIG_DFL) # 0
    #~print("signal.SIGINT:  {:2d}  ".format(signal.SIGINT),  signal.SIGINT ) # 2
    #~print("signal.SIGTERM: {:2d}  ".format(signal.SIGTERM), signal.SIGTERM) # 15
    #~print("signal.SIGTSTP: {:2d}  ".format(signal.SIGTSTP), signal.SIGTSTP) # 20

    #~print("SIGINT  handler before:    SIGINT : {:2d}, getsignal(SIGINT) : {}".format(signal.SIGINT,  signal.getsignal(signal.SIGINT )))
    #~print("SIGTSTP handler before:    SIGTSTP: {:2d}, getsignal(SIGTSTP): {}".format(signal.SIGTSTP, signal.getsignal(signal.SIGTSTP)))
    try:
        signal.signal(signal.SIGINT,  signal.SIG_DFL) # to allow shut down with ctrl-c when IN THE TERMINAL
        dprint("{:28s}: SIGINT : {:2d}, getsignal(SIGINT) : {}".format("SIGNAL SIGINT  set default", signal.SIGINT,  signal.getsignal(signal.SIGINT)))
    except Exception as e:
        exceptPrint(e, "SIGNAL SIGINT setting failed on platform: '{}'".format(platform.platform()))

    if "LINUX" in platform.platform().upper():
        try:
            signal.signal(signal.SIGTSTP, signal.SIG_IGN) # CTRL-Z signal will be ignored
            dprint("{:28s}: SIGTSTP: {:2d}, getsignal(SIGTSTP): {}".format("SIGNAL SIGTSTP set ignored", signal.SIGTSTP, signal.getsignal(signal.SIGTSTP)))
        except Exception as e:
            exceptPrint(e, "SIGNAL SIGTSTP setting failed on platform: '{}'".format(platform.platform()))
    #~print("SIGINT  handler after :    SIGINT:  {:2d}, getsignal(SIGINT) : {}".format(signal.SIGINT, signal.getsignal(signal.SIGINT)))
    #~print("SIGTSTP handler after :    SIGTSTP: {:2d}, getsignal(SIGTSTP): {}".format(signal.SIGTSTP, signal.getsignal(signal.SIGTSTP)))

    # test what the signals are connected to
    # for i in range(0, 95): # fails with i=0 and i>64
    #     try:
    #         print(": i: {:3d}, signal.getsignal(i): {}".format(i, signal.getsignal(i)))
    #     except ValueError as e:
    #         print(": i: {:3d}, signal.getsignal(i): {}   ValueError".format(i, e))
    #     except Exception as e:
    #         print(": i: {:3d}, signal.getsignal(i): {}   Exception".format(i, e))

# Command line
    dprint("{:28s}: sys.argv: {}".format("Command line", sys.argv))
    dprint("{:28s}: options: {}, commands: {}".format("Options, Commands", opts, args))

# Platform, machine
    dprint("{:28s}: {}".format("Operating System", platform.platform()))
    dprint("{:28s}: {}, {}".format("Machine", platform.machine(), platform.architecture()[0]))

# Versions
    dprint("Version status: ")
    for ver in gglobs.versions: dprint("   {:25s}: {}".format(ver, gglobs.versions[ver]))

# Python Search Path
    dprint("Python Search Paths:")
    # sys.path.append('pfad/zu/irgend/was') # to extend the search path
    for a in sys.path:
        dprint("   {:25s}: {}".format("sys.path", a))

# Program Paths
    dprint("Program Paths:")
    dprint("   {:25s}: {}".format("progName",       gglobs.progName))
    dprint("   {:25s}: {}".format("progPath",       gglobs.progPath))
    dprint("   {:25s}: {}".format("dataPath",       gglobs.dataPath))
    dprint("   {:25s}: {}".format("gresPath",       gglobs.gresPath))
    dprint("   {:25s}: {}".format("webPath",        gglobs.webPath))
    dprint("   {:25s}: {}".format("proglogPath",    gglobs.proglogPath))
    dprint("   {:25s}: {}".format("configPath",     gglobs.configPath))

# Read the configuration file
    # - these settings will override defaults in gglobs.py
    # - command line options may override these settings
    import gsup_config
    gsup_config.readGeigerLogConfig()   # geigerlog.cfg file MUST be present
    gsup_config.readPrivateConfig()     # ../private.cfg file may be present or not


###############################################################################
# Starting PyQt

# QT_STYLE_OVERRIDE
    # app = QApplication([]) -> results in message: (only on PyQt5, not on PyQt4!)
    #    QApplication: invalid style override passed, ignoring it.
    #            Available styles: Windows, Fusion
    # unless a '-style <valid style>' is in sys.argv.
    #   app = QApplication([None, "-style", "Windows"])   # ok!
    #   app = QApplication([None, "-style", "Fusion"])    # ok!
    #   app = QApplication([None, "-style", ""])          # ok!
    #
    # This results from the setting of:  QT_STYLE_OVERRIDE="gtk" in the OS. (printenv | grep QT)
    # Can be removed on the shell:  export QT_STYLE_OVERRIDE="" -> then the message disappears
    # preferred: remove from within Python:
    os.environ["QT_STYLE_OVERRIDE"] = ""

# HiDPI screen
    # MUST be done before QApplication is started!
    # see my article: HOWTO - Using PyQt5 and matplotlib on HiDPI monitors (Python3).pdf
    #
    # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    # !!!! im Raspi führte diese Anweisung zu einer Bildschirmgröße von 960x540,
    # !!!! obwohl Bildschirm auf 1920x1080 steht! -->unbrauchbar für Raspi
    #
    dprint("{:28s}".format("High DPI Scaling:"))
    if gglobs.hidpiActivation == "auto" or gglobs.hidpiActivation == "yes" :
        ehds = "EnableHighDpiScaling"
        uhdp = "UseHighDpiPixmaps"
        try:
            if hasattr(Qt, 'AA_EnableHighDpiScaling'):
                QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
                dprint("   {:25s}: {}".format(ehds, "Enabled"))
            else:
                edprint("   {:25s}: {}".format(ehds, "Attribute not available"))
        except Exception as e:
            edprint("   {:25s}: {} Exception: {}".format(ehds, "Failure!", e))

        try:
            if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
                QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
                dprint("   {:25s}: {}".format(uhdp, "Enabled"))
            else:
                edprint("   {:25s}: {}".format(uhdp, "Attribute not available"))
        except Exception as e:
            edprint("   {:25s}: {} Exception: {}".format(uhdp, "Failure!", e))
    else:
        dprint("   {:25s}: {}".format("High DPI Scaling", "Deselected"))

# Locale setting
    # if the system's local is used, then e.g. Germany's local is used
    # this makes the double validator use komma as period !!
    #
    # QLocale.OmitGroupSeparator        0x01
    # If this option is set, the number-to-string functions will not insert group
    # separators in their return values. The default is to insert group separators.
    # QLocale.RejectGroupSeparator  0x02
    # If this option is set, the string-to-number functions will fail if they
    # encounter group separators in their input. The default is to accept numbers
    # containing correctly placed group separators.
    mylocal = QLocale()
    mylocal.setDefault(QLocale(QLocale.English, QLocale.UnitedStates));
    mylocal.setNumberOptions(QLocale.OmitGroupSeparator | QLocale.RejectGroupSeparator);
    #print("QLocale.numberOptions (self): ", mylocal.numberOptions()) # is an object :-(


# QApplication
    # app = QApplication(sys.argv)   # conflicts in syntax with getopt (single vs double dash)
    gglobs.app = QApplication([])
    gglobs.app.setWindowIcon           (QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_geigerlog.png')))) # sets the icon for the whole app
    gglobs.app.setApplicationName      ("GeigerLog")               # sets the name 'GeigerLog' as the application name
    gglobs.app.setApplicationVersion   (gglobs.__version__)        # sets the GL version
    gglobs.app.setFont                 (QFont("Sans", 10))         # setting the application font size (default looks close to 11)

    # allows copy&Paste also on Win, but makes all Messageboxes as HTML coding
    # cumbersome with using space and tabs for formatting; do not use
    # gglobs.app.setStyleSheet("QMessageBox { messagebox-text-interaction-flags: 5; }")

    dprint("QCore Application:")
    dprint("   {:25s}: {}".format("applicationName()"     , QCoreApplication.applicationName()))
    dprint("   {:25s}: {}".format("applicationVersion()"  , QCoreApplication.applicationVersion()))
    dprint("   {:25s}: {}".format("applicationDirPath()"  , QCoreApplication.applicationDirPath()))
    dprint("   {:25s}: {}".format("applicationFilePath()" , QCoreApplication.applicationFilePath()))

# Library paths
    dprint("QCore Library paths:")
    #QCoreApplication.addLibraryPath(gglobs.progPath + "/custom_libs/") # will be listed only if folder exists
    #QCoreApplication.addLibraryPath("./");
    # needed? -> https://stackoverflow.com/questions/21268558/application-failed-to-start-because-it-could-not-find-or-load-the-qt-platform-pl
    libPaths    = QCoreApplication.libraryPaths()
    libPathStr  = "libraryPaths()"
    if len(libPaths) == 0:
        dprint("   {:25s}: {}".format(libPathStr, "No Library Paths"))
    else:
        for a in libPaths: dprint("   {:25s}: {}".format(libPathStr, a))

# QScreen
    # see: https://doc.qt.io/qt-5/qscreen.html#physicalDotsPerInch-prop
    # requires app.primaryScreen(), which is only available after app was started
    gaps = gglobs.app.primaryScreen()
    dprint("Connected Screen:")
    dprint("   {:25s}: {}".format("manufacturer",           QScreen.manufacturer        (gaps)))
    dprint("   {:25s}: {}".format("model       ",           QScreen.model               (gaps)))
    dprint("   {:25s}: {}".format("name        ",           QScreen.name                (gaps)))
    dprint("   {:25s}: {}".format("size        ",           QScreen.size                (gaps)))
    dprint("   {:25s}: {}".format("geometry    ",           QScreen.geometry            (gaps)))
    dprint("   {:25s}: {}".format("depth       ",           QScreen.depth               (gaps)))
    dprint("   {:25s}: {}".format("physicalSize",           QScreen.physicalSize        (gaps)))
    dprint("   {:25s}: {}".format("physicalDotsPerInch",    QScreen.physicalDotsPerInch (gaps)))
    dprint("   {:25s}: {}".format("physicalDotsPerInchX",   QScreen.physicalDotsPerInchX(gaps)))
    dprint("   {:25s}: {}".format("physicalDotsPerInchY",   QScreen.physicalDotsPerInchY(gaps)))
    dprint("   {:25s}: {}".format("orientation ",           QScreen.orientation         (gaps)))
    dprint("   {:25s}: {}".format("devicePixelRatio",       QScreen.devicePixelRatio    (gaps)))
    dprint("   {:25s}: {}".format("refreshRate ",           QScreen.refreshRate         (gaps)))

# matplotlib HiDPI adjustment
    dprint("HiDPI MPL Scale:")
    if gglobs.hidpiScaleMPL == "auto":
        gglobs.hidpiScaleMPL = 100 / int(QScreen.devicePixelRatio(gaps))
    dprint("   {:25s}: {}".format("HiDPI MPL Scale",      gglobs.hidpiScaleMPL))

# Style
    # latest news for PyQt5:
    # https://blog.qt.io/blog/2012/10/30/cleaning-up-styles-in-qt5-and-adding-fusion/
    # Summary: Default Qt5 has removed all styles except Windows (maybe) and added Fusion
    #
    # QStyleFactory::keys() returns a list of valid keys;
    # order of my preference; first is best: PyQt5: ['Fusion', 'Windows'] (PyQt5 has only 2)

    dprint("Styles:")
    dprint("   {:25s}: {}".format("Default",                gglobs.app.style().metaObject().className()))
    dprint("   {:25s}: {}".format("Styles found on system", QStyleFactory.keys()))
    for opt, optval in opts:
        if opt in ("-s", "--style"):
            available_styles = QStyleFactory.keys()
            if optval in available_styles:
                gglobs.windowStyle = optval
                dprint("   {:25s}: '{}' - overrides default".format("Style per command line", gglobs.windowStyle))
            else:
                gglobs.windowStyle = "auto"
                dprint("   {:25s}: '{}' - Style not available (check spelling, capitalization); ignoring".format("Style per command line", optval))

    if gglobs.windowStyle != "auto":    # existence of style had been verified
        result = gglobs.app.setStyle(gglobs.windowStyle)
        if result is None:  dprint("   Selected Style '{}' could not be applied".format(gglobs.windowStyle))
    dprint("   {:25s}: {}".format("Active Style is", gglobs.app.style().metaObject().className()))

# get the GUI
    from  ggeiger import ggeiger

# starting the GUI
    dprint(TCYAN + "Starting the GUI " + "-" * 110 + TDEFAULT)
    ex     = ggeiger()              # an instance of ggeiger; runs init and draws window
    status = gglobs.app.exec()      # starts the QApplication([]); run the GUI until closure
    gdprint("Exited GUI with status of: {} ".format(status) + "-" * 97)

# cleanup
    executeTPUT(action = 'allow_line_wrapping')

    return status

