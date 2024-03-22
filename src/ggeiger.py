#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
class ggeiger - A part of GeigerLog - cannot be used on its own
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

from   gsup_utils  import *

import gsup_sql
import gsup_tools
import gsup_plot

import gweb_monserv
import gweb_radworld

import gstat_poisson
import gstat_fft
import gstat_convfft
import gstat_synth

if gglobs.Devices["GMC"]        [ACTIV]: import gdev_gmc         # both needed
if gglobs.Devices["GMC"]        [ACTIV]: import gdev_gmc_hist    # both needed
if gglobs.Devices["Audio"]      [ACTIV]: import gdev_audio       #
if gglobs.Devices["RadMon"]     [ACTIV]: import gdev_radmon      # RadMon -  then imports "paho.mqtt.client as mqtt"
if gglobs.Devices["AmbioMon"]   [ACTIV]: import gdev_ambiomon    #
if gglobs.Devices["GammaScout"] [ACTIV]: import gdev_gscout      #
if gglobs.Devices["I2C"]        [ACTIV]: import gdev_i2c         # I2C  -    then imports dongles and sensor modules
if gglobs.Devices["LabJack"]    [ACTIV]: import gdev_labjack     # LabJack - then imports the LabJack modules
if gglobs.Devices["Simul"]      [ACTIV]: import gdev_simul       #
if gglobs.Devices["MiniMon"]    [ACTIV]: import gdev_minimon     #
if gglobs.Devices["WiFiClient"] [ACTIV]: import gdev_wificlient  #
if gglobs.Devices["WiFiServer"] [ACTIV]: import gdev_wifiserver  #
if gglobs.Devices["RaspiI2C"]   [ACTIV]: import gdev_raspii2c    #
if gglobs.Devices["RaspiPulse"] [ACTIV]: import gdev_raspipulse  #
if gglobs.Devices["Manu"]       [ACTIV]: import gdev_manu        #
if gglobs.Devices["Rad Pro"]    [ACTIV]: import gdev_radpro      #


# Modality
# Qt: A modal dialog is a dialog that blocks input to other visible windows in the same application.
#
# Modale Dialoge sperren den Rest der Anwendung (oder sogar der Benutzeroberfläche), solange der Dialog angezeigt wird.
# Nichtmodale Dialoge erlauben auch Eingaben in der Applikation außerhalb des Dialogs.
#
# vergleiche Menu Show IP und MonServer: gleiche Programmierung, anderes Verhalten???
#
#   d.setWindowModality(Qt.WindowModal)
#   d.setWindowModality(Qt.ApplicationModal)    # The window is modal to the application and blocks input to all windows.
#   d.setWindowModality(Qt.NonModal)            # The window is not modal and does not block input to other windows.

class ggeiger(QMainWindow):

    def __init__(self):
        """init the ggeiger class"""

        fncname = "ggeiger__init__: "

        # super(ggeiger, self).__init__()   # needed for Py2
        super().__init__()                  # ok for Py3
        gglobs.exgg = self

        # hold the updated variable values in self.updateDisplayVariableValue()
        self.vlabels  = [None] * len(gglobs.varsCopy)
        self.svlabels = [None] * len(gglobs.varsCopy)

        #
        # getting font(s)
        #
        #
        # default font type
        # custom_font = QFont()
        # custom_font.setWeight(18);
        # QApplication.setFont(custom_font, "QLabel")
        # set the font for the top level window (and any of its children):
        # self.window().setFont(someFont)
        # # set the font for *any* widget created in this QApplication:
        # QApplication.instance().setFont(QFont("Deja Vue"))
        # QApplication.instance().setFont(QFont("Helvetica"))
        #
        # edprint(QFont.family())
        # edprint(QApplication.instance().font())
        # edprint(QApplication.font())
        self.window().setFont(QFont("Sans Serif"))
        #
        # platform dependent!
        # cdprint("Platform: ", platform.platform())
            # Raspi: Bullseye      Platform: Linux-5.15.32-v8+-aarch64-with-glibc2.31
            # Intel: Ubuntu 16.04: Platform: Linux-4.15.0-142-generic-x86_64-with-glibc2.23

        if "WINDOWS" in platform.platform().upper():
            dprint("WINDOWS: Setting QFontDatabase.FixedFont")
            self.fontstd = QFontDatabase.systemFont(QFontDatabase.FixedFont) # worked! got Courier New
            #self.fontstd = QFont("Consolas", 10) # alternative

        elif "LINUX" in platform.platform().upper():
            dprint("LINUX: Setting QFontDatabase.FixedFont")
            self.fontstd = QFont("Mono", 9)
            # self.fontstd = QFont("Mono", 10)

        else:
            dprint("Other System: Setting QFontDatabase.FixedFont")
            self.fontstd = QFontDatabase.systemFont(QFontDatabase.FixedFont) # result ?
            #self.fontstd = QFont("Courier New") # alternative

        #
        # # font standard
        #         #self.fontstd = QFont()
        #         #self.fontstd = QFont("Deja Vue", 10)
        #         #self.fontstd = QFont("pritzelbmpr", 10)
        #         #self.fontstd = QFont("Courier New", 10)
        #         #self.fontstd.setFamily('Monospace')         # options: 'Lucida'
        #         #self.fontstd.StyleHint(QFont.TypeWriter)    # options: QFont.Monospace, QFont.Courier
        #         #self.fontstd.StyleHint(QFont.Monospace)     # options: QFont.Monospace, QFont.Courier
        #         #self.fontstd.setStyleStrategy(QFont.PreferMatch)
        #         #self.fontstd.setFixedPitch(True)
        #         #self.fontstd.setPointSize(11) # 11 is too big
        #         #self.fontstd.setWeight(60)                  # options: 0 (thin) ... 99 (very thick); 60:ok, 65:too fat
        #         gglobs.fontstd = self.fontstd
        #
        # self.fontstd = QFontDatabase.systemFont(QFontDatabase.FixedFont) # did NOT work on Raspi!
        self.fontstd.setFixedPitch(True)
        self.fontstd.setWeight(45)          # "Qt uses a weighting scale from 0 to 99" NOTE: >60 wirkt matschig
                                            # options: 0 (thin) ... 99 (very thick); 60:ok, 65:fat
        gglobs.fontstd = self.fontstd

        # self.fatfont used for HEADINGS: Data, Device, Graph
        self.fatfont = QFont("Deja Vue")
        self.fatfont.setWeight(65)
        self.fatfont.setPointSize(11)

    # window
    # icon
        iconpath = os.path.join(gglobs.gresPath, 'icon_geigerlog.png')
        self.iconGeigerLog    = QIcon(QPixmap(iconpath))
        gglobs.iconGeigerLog  = self.iconGeigerLog
        self.setWindowIcon(gglobs.iconGeigerLog)

        # this is used for Web sites
        try:
            with open(iconpath, 'rb') as file_handle:
                gglobs.iconGeigerLogWeb = file_handle.read()
        except Exception as e:
            exceptPrint(e, fncname + "reading binary from iconpath")

    #title
        wtitle = "GeigerLog v{}".format(gglobs.__version__)
        if gglobs.devel: wtitle += "  Python: {}  sys.argv: {}".format(sys.version[:6], sys.argv)
        self.setWindowTitle(wtitle)

    # screen
        screen_available = QDesktopWidget().availableGeometry()
        # sw = min(gglobs.window_width  -   2, screen_available.width() )   # Frame of 1 pixel left and right
        # sw = min(gglobs.window_width  -  10, screen_available.width() )   # Frame of 5 pixel left and right
        sw = min(gglobs.window_width  - 12, screen_available.width() )      # Frame of 6 pixel left and right
        sh = min(gglobs.window_height - 29, screen_available.height())      # Frame top + bottom + Window bar of 29 pixel
        xpos  = max(screen_available.width() - sw, 0)                       # should be >0 anyway
        ypos  = screen_available.y()

        if "WINDOWS" in platform.platform().upper(): ypos += 33             # some correction needed at least on Virtual Win8.1
        if "ARMV"    in platform.platform().upper(): ypos += 33             # some correction needed at least on Manu 4
        if "AARCH64" in platform.platform().upper(): ypos += 33             # some correction needed at least on Raspi64

        self.setGeometry(xpos, ypos, sw, sh)                                # position window in upper right corner of screen

#         edprint("Screen Geometry: ", QDesktopWidget().screenGeometry())    # total hardware screen
#         edprint("Screen Available:", QDesktopWidget().availableGeometry()) # available screen
#         edprint("Screen as set: ", (x, y, sw, sh)  )
#
#         geom             = self.geometry()
#         geom_frame       = self.frameGeometry()
#         edprint("Current window size:", "{}x{} including window frame (w/o frame: {}x{})".format(geom_frame.width(), geom_frame.height(), geom.width(), geom.height()))

    #figure and its toolbar
        # a figure instance to plot on
        # figsize=(18, 18) in plt.figure() hat keine Auswirkungen
        # self.figure = plt.figure(facecolor = "#DFDEDD", edgecolor='lightgray',  linewidth = 0.0, dpi=gglobs.hidpiScaleMPL) # lighter grayface
        self.figure = plt.figure(facecolor = "#DFDEDD", edgecolor='#b8b8b8',  linewidth = 0.1, dpi=gglobs.hidpiScaleMPL) # lighter grayface
        #self.figure, self.ax1 = plt.subplots(facecolor='#DFDEDD') # lighter gray
        #plt.subplots(facecolor='#DFDEDD') # lighter gray
        plt.clf()  # must be done - clear figure or it will show an empty figure !!

        # canvas - this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        # next command creates: Attribute Qt::AA_EnableHighDpiScaling must be set before QCoreApplication is created.
        self.canvas = FigureCanvas(self.figure)
        self.canvas.mpl_connect('motion_notify_event', self.updatecursorposition) # where the cursor is
        self.canvas.mpl_connect('button_press_event' , self.onclick)              # send a mouse click
        self.canvas.setContentsMargins(10,10,10,10)
        self.canvas.setMinimumHeight(450)

        # this is the figure Navigation widget; it takes the Canvas widget and a parent
        self.navtoolbar = NavigationToolbar(self.canvas, self)
        self.navtoolbar.setToolTip("Graph Toolbar")
        self.navtoolbar.setIconSize(QSize(32,32))
        #print("self.navtoolbar.iconSize()", self.navtoolbar.iconSize())

    #self.menubar and statusbar and toolbar
        self.menubar = self.menuBar()
        self.menubar.setFocus()

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        toolbar = self.addToolBar('File')
        toolbar.setToolTip("File Toolbar")
        toolbar.setOrientation(Qt.Horizontal) # is default; alt: Qt.Vertical
        toolbar.setIconSize(QSize(32,32))  # standard size is too small
        #print("toolbar.iconSize()", toolbar.iconSize())

#file menu

    #clearNotePad
        clearNPAction = QAction("Clear NotePad", self)
        addMenuTip(clearNPAction, "Delete all content of the NotePad")
        clearNPAction.triggered.connect(self.clearNotePad)

    #searchNotePad
        SearchNPAction = QAction("Search NotePad ...", self)
        SearchNPAction.setShortcut('Ctrl+F')
        addMenuTip(SearchNPAction, "Search NotePad for occurence of a text (Shortcut: CTRL-F)")
        SearchNPAction.triggered.connect(self.searchNotePad)

    #saveNotePad
        SaveNPAction = QAction("Save NotePad to File", self)
        addMenuTip(SaveNPAction, "Save Content of NotePad as text file named <current filename>.notes")
        SaveNPAction.triggered.connect(self.saveNotePad)

    #printNotePad
        PrintNPAction = QAction("Print NotePad ...", self)
        addMenuTip(PrintNPAction, "Print Content of NotePad to Printer or  PDF-File")
        PrintNPAction.triggered.connect(self.printNotePad)

    # exit
        exitAction = QAction('Exit', self)
        exitAction.setIcon(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_exit.png')))) # Flat icon
        exitAction.setShortcut('Ctrl+Q')
        addMenuTip(exitAction, 'Exit the GeigerLog program')
        exitAction.triggered.connect(self.close)

        fileMenu = self.menubar.addMenu('&File')
        fileMenu.setToolTipsVisible(True)

        fileMenu.addAction(clearNPAction)
        fileMenu.addAction(SearchNPAction)
        fileMenu.addAction(SaveNPAction)
        fileMenu.addAction(PrintNPAction)

        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)
        #fileMenu.triggered[QAction].connect(self.processtrigger)

        toolbar.addAction(exitAction)

# Device menu
        self.toggleDeviceConnectionAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_plug_open.png'))), 'Connect / Disconnect Devices', self)
        addMenuTip(self.toggleDeviceConnectionAction, 'Toggle connection of GeigerLog with the devices')
        self.toggleDeviceConnectionAction.triggered.connect(self.toggleDeviceConnection)

        self.DeviceConnectAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_plug_open.png'))), 'Connect Devices', self)
        self.DeviceConnectAction.setShortcut('Ctrl+C')
        addMenuTip(self.DeviceConnectAction, 'Connect the computer to the devices')
        self.DeviceConnectAction.triggered.connect(lambda : self.switchAllConnections("ON"))

        self.DeviceDisconnectAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_plug_closed.png'))), 'Disconnect Devices', self, enabled = False)
        self.DeviceDisconnectAction.setShortcut('Ctrl+D')
        addMenuTip(self.DeviceDisconnectAction, 'Disconnect the computer from the devices')
        self.DeviceDisconnectAction.triggered.connect(lambda : self.switchAllConnections("OFF"))

        self.DeviceMappingAction = QAction('Show Device Mappings', self, enabled = True)
        addMenuTip(self.DeviceMappingAction, 'Show the mapping of variables of the activated devices')
        self.DeviceMappingAction.triggered.connect(self.showDeviceMappings)

        self.DevicePortSettingAction = QAction('Show Device Port Settings', self, enabled = True)
        addMenuTip(self.DevicePortSettingAction, 'Show the port settings for all activated devices')
        self.DevicePortSettingAction.triggered.connect(lambda : showPortSettings())

        self.DeviceCalibAction = QAction("Geiger Tubes ...", self, enabled = True)
        addMenuTip(self.DeviceCalibAction, "Set sensitivities for all Geiger tubes temporarily")
        self.DeviceCalibAction.triggered.connect(self.setTemporaryTubeSensitivities)

    # build the Device menu
        deviceMenu = self.menubar.addMenu('&Device')
        deviceMenu.setToolTipsVisible(True)

    # all devices
        deviceMenu.addAction(self.DeviceConnectAction)
        deviceMenu.addAction(self.DeviceDisconnectAction)

        deviceMenu.addSeparator()
        deviceMenu.addAction(self.DeviceMappingAction)
        deviceMenu.addAction(self.DevicePortSettingAction)
        deviceMenu.addAction(self.DeviceCalibAction)

        deviceMenu.addSeparator()

    # now following all device specific submenus

    # submenu GMC
        if gglobs.Devices["GMC"][ACTIV]  :

            self.GMCInfoAction = QAction('Show Info', self, enabled=True)
            addMenuTip(self.GMCInfoAction, 'Show basic info on GMC device')
            self.GMCInfoAction.triggered.connect(lambda: self.fprintDeviceInfo("GMC", extended = False))

            self.GMCInfoActionExt = QAction('Show Extended Info', self, enabled=False)
            addMenuTip(self.GMCInfoActionExt, 'Show extended info on GMC device')
            self.GMCInfoActionExt.triggered.connect(lambda: self.fprintDeviceInfo("GMC", extended = True))

            self.GMCConfigEditAction = QAction("Set GMC Configuration ...", self, enabled=False)
            addMenuTip(self.GMCConfigEditAction, 'View, Edit and Set the GMC device configuration')
            self.GMCConfigEditAction.triggered.connect(lambda: gdev_gmc.editGMC_Configuration())

            self.GMCConfigMemoryAction = QAction('Show Configuration Memory', self, enabled=False)
            addMenuTip(self.GMCConfigMemoryAction, 'Show the GMC device configuration memory as binary in human readable format')
            self.GMCConfigMemoryAction.triggered.connect(gdev_gmc.fprintGMC_ConfigMemory)

            self.GMCONAction = QAction('Switch Power ON', self, enabled=False)
            addMenuTip(self.GMCONAction, 'Switch the GMC device power to ON')
            self.GMCONAction.triggered.connect(lambda: self.switchGMCPower("ON"))

            self.GMCOFFAction = QAction('Switch Power OFF', self, enabled=False)
            addMenuTip(self.GMCOFFAction, 'Switch the GMC device power to OFF')
            self.GMCOFFAction.triggered.connect(lambda: self.switchGMCPower("OFF"))

            # self.GMCAlarmONAction = QAction('Switch Alarm ON', self, enabled=False)
            # addMenuTip(self.GMCAlarmONAction, 'Switch the GMC device alarm ON')
            # self.GMCAlarmONAction.triggered.connect(lambda: gdev_gmc.switchGMC_DeviceAlarm("ON"))

            # self.GMCAlarmOFFAction = QAction('Switch Alarm OFF', self, enabled=False)
            # addMenuTip(self.GMCAlarmOFFAction, 'Switch the GMC device alarm OFF')
            # self.GMCAlarmOFFAction.triggered.connect(lambda: gdev_gmc.switchGMC_DeviceAlarm("OFF"))

            # self.GMCSpeakerONAction = QAction('Switch Speaker ON', self, enabled=False)
            # addMenuTip(self.GMCSpeakerONAction, 'Switch the GMC device speaker ON')
            # self.GMCSpeakerONAction.triggered.connect(lambda: gdev_gmc.switchGMC_DeviceSpeaker("ON"))

            # self.GMCSpeakerOFFAction = QAction('Switch Speaker OFF', self, enabled=False)
            # addMenuTip(self.GMCSpeakerOFFAction, 'Switch the GMC device speaker OFF')
            # self.GMCSpeakerOFFAction.triggered.connect(lambda: gdev_gmc.switchGMC_DeviceSpeaker("OFF"))

            # self.GMCSavingStateAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, ''))), 'Set History Saving Mode ...', self, enabled=False)
            # addMenuTip(self.GMCSavingStateAction, 'Set History Saving Mode of GMC device to OFF, CPS, CPM, and CPM hourly average')
            # self.GMCSavingStateAction.triggered.connect(gdev_gmc.setGMC_HistSaveMode)

            self.GMCSetTimeAction = QAction('Set Date+Time', self, enabled=False)
            addMenuTip(self.GMCSetTimeAction, 'Set the Date + Time of the GMC device to the computer time')
            self.GMCSetTimeAction.triggered.connect(gdev_gmc.GMCsetDateTime)

            self.GMCEraseSavedDataAction = QAction('Erase Saved Data ...', self, enabled=False)
            addMenuTip(self.GMCEraseSavedDataAction, 'Erase all data from the History memory of the GMC device')
            self.GMCEraseSavedDataAction.triggered.connect(lambda: gdev_gmc.doEraseSavedData())

            self.GMCREBOOTAction = QAction('Reboot ...', self, enabled=False)
            addMenuTip(self.GMCREBOOTAction, 'Reboot the GMC device')
            self.GMCREBOOTAction.triggered.connect(lambda: gdev_gmc.doREBOOT(False))

            self.GMCFACTORYRESETAction = QAction('FACTORYRESET ...', self, enabled=False)
            addMenuTip(self.GMCFACTORYRESETAction, 'Reset the GMC device to factory configuration')
            self.GMCFACTORYRESETAction.triggered.connect(lambda: gdev_gmc.doFACTORYRESET(False))

            self.GMCSerialAction = QAction('Set Serial Port ...', self, enabled=True)
            addMenuTip(self.GMCSerialAction, 'Manually set the serial port of the GMC device')
            self.GMCSerialAction.triggered.connect(lambda: setDeviceSerialPort("GMC", gglobs.GMC_usbport))


            self.GMCREBOOT_forceAction = QAction('DVL Force Reboot', self, enabled=True)
            addMenuTip(self.GMCREBOOT_forceAction, 'Force a Reboot of the GMC device')
            self.GMCREBOOT_forceAction.triggered.connect(lambda: gdev_gmc.doREBOOT(True))

            self.GMCFACTORYRESET_forceAction = QAction('DVL Force FACTORYRESET', self, enabled=True)
            addMenuTip(self.GMCFACTORYRESET_forceAction, 'Force a Reset of the GMC device to factory configuration')
            self.GMCFACTORYRESET_forceAction.triggered.connect(lambda: gdev_gmc.doFACTORYRESET(True))

            deviceSubMenuGMC = deviceMenu.addMenu("GMC Series")
            deviceSubMenuGMC.setToolTipsVisible(True)
            deviceSubMenuGMC.addAction(self.GMCInfoAction)
            deviceSubMenuGMC.addAction(self.GMCInfoActionExt)
            deviceSubMenuGMC.addAction(self.GMCConfigEditAction)
            deviceSubMenuGMC.addAction(self.GMCConfigMemoryAction)
            deviceSubMenuGMC.addAction(self.GMCSetTimeAction)
            deviceSubMenuGMC.addAction(self.GMCEraseSavedDataAction)
            deviceSubMenuGMC.addAction(self.GMCONAction)
            deviceSubMenuGMC.addAction(self.GMCOFFAction)
            deviceSubMenuGMC.addAction(self.GMCREBOOTAction)
            deviceSubMenuGMC.addAction(self.GMCFACTORYRESETAction)
            deviceSubMenuGMC.addAction(self.GMCSerialAction)

            if gglobs.devel:    # on devel allow Factory Reset without checking
                deviceSubMenuGMC.addAction(self.GMCREBOOT_forceAction)
                deviceSubMenuGMC.addAction(self.GMCFACTORYRESET_forceAction)

            # if 0 and gglobs.devel:
            #     # do not use
            #     deviceSubMenuGMC.addAction(self.GMCONAction)
            #     deviceSubMenuGMC.addAction(self.GMCOFFAction)
            #     deviceSubMenuGMC.addAction(self.GMCAlarmONAction)
            #     deviceSubMenuGMC.addAction(self.GMCAlarmOFFAction)
            #     deviceSubMenuGMC.addAction(self.GMCSpeakerONAction)
            #     deviceSubMenuGMC.addAction(self.GMCSpeakerOFFAction)
            #     deviceSubMenuGMC.addAction(self.GMCSavingStateAction)

            #deviceMenu.triggered[QAction].connect(self.processtrigger)

    # submenu AudioCounter
        if gglobs.Devices["Audio"][ACTIV] :

            self.AudioInfoAction = QAction('Show Info', self, enabled=True)
            addMenuTip(self.AudioInfoAction, 'Show basic info on AudioCounter device')
            self.AudioInfoAction.triggered.connect(lambda: self.fprintDeviceInfo("Audio", extended = False))

            self.AudioInfoActionExt = QAction('Show Extended Info', self, enabled=False)
            addMenuTip(self.AudioInfoActionExt, 'Show extended info on AudioCounter device')
            self.AudioInfoActionExt.triggered.connect(lambda: self.fprintDeviceInfo("Audio", extended = True))

            self.AudioPlotAction = QAction("Plot Pulse", self, enabled=False)
            addMenuTip(self.AudioPlotAction, 'Plot the audio pulse recordings of the AudioCounter Device')
            self.AudioPlotAction.triggered.connect(lambda: gdev_audio.reloadAudioData("Recording"))

            self.AudioSignalAction = QAction("Show Live Audio Signal", self, enabled=False)
            addMenuTip(self.AudioSignalAction, 'Show the live, raw audio signal as received by the audio input')
            self.AudioSignalAction.triggered.connect(lambda: gdev_audio.showLiveAudioSignal())

            self.AudioEiaAction = QAction("Eia", self, enabled=False)
            self.AudioEiaAction.triggered.connect(lambda: gdev_audio.showAudioEia())

            deviceSubMenuAudio  = deviceMenu.addMenu("AudioCounter Series")
            deviceSubMenuAudio.setToolTipsVisible(True)
            deviceSubMenuAudio.addAction(self.AudioInfoAction)
            deviceSubMenuAudio.addAction(self.AudioInfoActionExt)
            deviceSubMenuAudio.addAction(self.AudioPlotAction)
            if gglobs.devel:
                deviceSubMenuAudio.addAction(self.AudioSignalAction)
            if gglobs.AudioOei:
                deviceSubMenuAudio.addAction(self.AudioEiaAction)

    # submenu RadMon
        if gglobs.Devices["RadMon"][ACTIV]  :

            self.RMInfoAction = QAction('Show Info', self, enabled=True)
            addMenuTip(self.RMInfoAction, 'Show basic info on RadMon device')
            self.RMInfoAction.triggered.connect(lambda: self.fprintDeviceInfo("RadMon", extended=False))

            self.RMInfoActionExt = QAction('Show Extended Info', self, enabled=False)
            addMenuTip(self.RMInfoActionExt, 'Show extended info on RadMon device')
            self.RMInfoActionExt.triggered.connect(lambda: self.fprintDeviceInfo("RadMon", extended = True))

            deviceSubMenuRM  = deviceMenu.addMenu("RadMon Series")
            deviceSubMenuRM.setToolTipsVisible(True)
            deviceSubMenuRM.addAction(self.RMInfoAction)
            deviceSubMenuRM.addAction(self.RMInfoActionExt)

    # submenu AmbioMon
        if gglobs.Devices["AmbioMon"][ACTIV]  :

            self.AmbioInfoAction = QAction('Show Info', self, enabled=True)
            addMenuTip(self.AmbioInfoAction, 'Show basic info on AmbioMon device')
            self.AmbioInfoAction.triggered.connect(lambda: self.fprintDeviceInfo("AmbioMon", extended=False))

            self.AmbioInfoActionExt = QAction('Show Extended Info', self, enabled=False)
            addMenuTip(self.AmbioInfoActionExt, 'Show extended info on AmbioMon device')
            self.AmbioInfoActionExt.triggered.connect(lambda: self.fprintDeviceInfo("AmbioMon", extended = True))

            self.AmbioSetServerIP = QAction('Set AmbioMon Device IP ...', self, enabled=True)
            addMenuTip(self.AmbioSetServerIP, 'Set the IP Adress or Domain Name of the AmbioMon device')
            self.AmbioSetServerIP.triggered.connect(gdev_ambiomon.setAmbioServerIP)

            self.AmbioDataModeAction = QAction('Select AmbioMon Data Type Mode ...', self, enabled=False)
            addMenuTip(self.AmbioDataModeAction, "Select what type of data the AmbioMon device sends during logging: 'LAST' for last available data value, or 'AVG' for last 1 minute average of values")
            self.AmbioDataModeAction.triggered.connect(gdev_ambiomon.setAmbioLogDatatype)

            AmbioPingAction = QAction("Ping AmbioMon Server", self)
            addMenuTip(AmbioPingAction, 'Ping AmbioMon Server and report success or failure')
            AmbioPingAction.triggered.connect(lambda: gdev_ambiomon.pingAmbioServer())

            AmbioSerialAction = QAction("Send Message to AmbioMon via Serial", self)
            addMenuTip(AmbioSerialAction, "Send Message to AmbioMon via a USB-To-Serial Connection  ")
            AmbioSerialAction.triggered.connect(lambda: gdev_ambiomon.sendToSerial())

            deviceSubMenuAmbio  = deviceMenu.addMenu("Ambiomon Series")
            deviceSubMenuAmbio.setToolTipsVisible(True)
            deviceSubMenuAmbio.addAction(self.AmbioInfoAction)
            deviceSubMenuAmbio.addAction(self.AmbioInfoActionExt)
            deviceSubMenuAmbio.addAction(self.AmbioSetServerIP)
            deviceSubMenuAmbio.addAction(self.AmbioDataModeAction)
            deviceSubMenuAmbio.addAction(AmbioPingAction)
            deviceSubMenuAmbio.addAction(AmbioSerialAction)

    # submenu Gamma-Scout counter
        if gglobs.Devices["GammaScout"][ACTIV]  :

            self.GSInfoAction = QAction('Show Info', self, enabled=True)
            addMenuTip(self.GSInfoAction, 'Show basic info on GS device')
            self.GSInfoAction.triggered.connect(lambda: self.fprintDeviceInfo("GammaScout", extended = False))

            self.GSInfoActionExt = QAction('Show Extended Info', self, enabled=False)
            addMenuTip(self.GSInfoActionExt, 'Show extended info on GS device')
            self.GSInfoActionExt.triggered.connect(lambda: self.fprintDeviceInfo("GammaScout", extended = True))

            self.GSResetAction = QAction('Set to Normal Mode', self, enabled=False)
            addMenuTip(self.GSResetAction, 'Set the Gamma-Scout counter to its Normal Mode')
            self.GSResetAction.triggered.connect(lambda: gdev_gscout.GSsetMode("Normal"))

            self.GSSetPCModeAction = QAction('Set to PC Mode', self, enabled=False)
            addMenuTip(self.GSSetPCModeAction, 'Set the Gamma-Scout counter to its PC Mode')
            self.GSSetPCModeAction.triggered.connect(lambda: gdev_gscout.GSsetMode("PC"))

            self.GSDateTimeAction = QAction('Set Date+Time', self, enabled=False)
            addMenuTip(self.GSDateTimeAction, 'Set the Gamma-Scout counter clock to the computer time')
            self.GSDateTimeAction.triggered.connect(lambda: gdev_gscout.setGSDateTime())

            self.GSSetOnlineAction = QAction('Set to Online Mode ...', self, enabled=False)
            addMenuTip(self.GSSetOnlineAction, "Set the Gamma-Scout counter to its Online Mode\nAvailable only for 'Online' models")
            self.GSSetOnlineAction.triggered.connect(lambda: gdev_gscout.GSsetMode("Online"))

            self.GSRebootAction = QAction('Reboot', self, enabled=False)
            addMenuTip(self.GSRebootAction, "Do a Gamma-Scout reboot as warm-start\nAvailable only for 'Online' models")
            self.GSRebootAction.triggered.connect(lambda: gdev_gscout.GSreboot())

            self.GSSerialAction = QAction('Set Serial Port ...', self, enabled=True)
            addMenuTip(self.GSSerialAction, 'Manually set the serial port of the I2C device')
            # self.GSSerialAction.triggered.connect(lambda: gdev_gscout.setGS_SerialPort())
            self.GSSerialAction.triggered.connect(lambda: setDeviceSerialPort("GammaScout", gglobs.GSusbport))

            deviceSubMenuGS  = deviceMenu.addMenu("Gamma-Scout Series")
            deviceSubMenuGS.setToolTipsVisible(True)
            deviceSubMenuGS.addAction(self.GSInfoAction)
            deviceSubMenuGS.addAction(self.GSInfoActionExt)
            deviceSubMenuGS.addAction(self.GSDateTimeAction)
            deviceSubMenuGS.addAction(self.GSResetAction)
            deviceSubMenuGS.addAction(self.GSSetPCModeAction)
            deviceSubMenuGS.addAction(self.GSSetOnlineAction)
            deviceSubMenuGS.addAction(self.GSRebootAction)
            deviceSubMenuGS.addAction(self.GSSerialAction)

    # submenu I2C
        if gglobs.Devices["I2C"][ACTIV] :

            self.I2CInfoAction = QAction('Show Info', self, enabled=True)
            addMenuTip(self.I2CInfoAction, 'Show basic info on I2C device')
            self.I2CInfoAction.triggered.connect(lambda: self.fprintDeviceInfo("I2C", extended = False))

            self.I2CInfoActionExt = QAction('Show Extended Info', self, enabled=False)
            addMenuTip(self.I2CInfoActionExt, 'Show extended info on I2C device')
            self.I2CInfoActionExt.triggered.connect(lambda: self.fprintDeviceInfo("I2C", extended = True))

            self.I2CForceCalibAction = QAction('Calibrate CO2 Sensor', self, enabled=False)
            addMenuTip(self.I2CForceCalibAction, 'Force a CO2 calibration of the SCD41 sensor')
            self.I2CForceCalibAction.triggered.connect(lambda: gdev_i2c.forceCalibration())

            self.I2CScanAction = QAction('Scan I2C Bus', self, enabled=False)
            addMenuTip(self.I2CScanAction, 'Scan I2C bus for any sensors and report to NotePad (only when not-logging)')
            self.I2CScanAction.triggered.connect(lambda: gdev_i2c.scanI2CBus())

            self.I2CResetAction = QAction('Reset System', self, enabled=False)
            addMenuTip(self.I2CResetAction, 'Reset the I2C ELV dongle and attached sensors (only when not-logging)')
            self.I2CResetAction.triggered.connect(lambda: gdev_i2c.resetI2C())

            self.I2CSerialAction = QAction('Set Serial Port ...', self, enabled=True)
            addMenuTip(self.I2CSerialAction, 'Manually set the serial port of the I2C device')
            self.I2CSerialAction.triggered.connect(lambda: setDeviceSerialPort("I2C", gglobs.I2Cusbport))

            deviceSubMenuI2C  = deviceMenu.addMenu("I2C Series")
            deviceSubMenuI2C.setToolTipsVisible(True)
            deviceSubMenuI2C.addAction(self.I2CInfoAction)
            deviceSubMenuI2C.addAction(self.I2CInfoActionExt)
            deviceSubMenuI2C.addAction(self.I2CForceCalibAction)
            deviceSubMenuI2C.addAction(self.I2CScanAction)
            deviceSubMenuI2C.addAction(self.I2CResetAction)
            deviceSubMenuI2C.addAction(self.I2CSerialAction)


    # submenu LabJack
        if gglobs.Devices["LabJack"][ACTIV]  :

            self.LJInfoAction = QAction('Show Info', self, enabled=True)
            addMenuTip(self.LJInfoAction, 'Show basic info on LabJack device')
            self.LJInfoAction.triggered.connect(lambda: self.fprintDeviceInfo("LabJack", extended = False))

            self.LJInfoActionExt = QAction('Show Extended Info', self, enabled=False)
            addMenuTip(self.LJInfoActionExt, 'Show extended info on LabJack device')
            self.LJInfoActionExt.triggered.connect(lambda: self.fprintDeviceInfo("LabJack", extended = True))

            deviceSubMenuLJ  = deviceMenu.addMenu("LabJack Series")
            deviceSubMenuLJ.setToolTipsVisible(True)
            deviceSubMenuLJ.addAction(self.LJInfoAction)
            deviceSubMenuLJ.addAction(self.LJInfoActionExt)


    # submenu MiniMon
        if gglobs.Devices["MiniMon"][ACTIV] :

            self.MiniMonInfoAction = QAction('Show Info', self, enabled=True)
            addMenuTip(self.MiniMonInfoAction, 'Show basic info on MiniMon device')
            self.MiniMonInfoAction.triggered.connect(lambda: self.fprintDeviceInfo("MiniMon", extended = False))

            deviceSubMenuMiniMon  = deviceMenu.addMenu("MiniMon Series")
            deviceSubMenuMiniMon.setToolTipsVisible(True)
            deviceSubMenuMiniMon.addAction(self.MiniMonInfoAction)


    # submenu Simul Device
        if gglobs.Devices["Simul"][ACTIV] :

            self.SimulInfoAction = QAction('Show Info', self, enabled=True)
            addMenuTip(self.SimulInfoAction, 'Show basic info on Simul device')
            self.SimulInfoAction.triggered.connect(lambda: self.fprintDeviceInfo("Simul", extended = False))

            self.SimulInfoActionExt = QAction('Show Extended Info', self, enabled=False)
            addMenuTip(self.SimulInfoActionExt, 'Show extended info on Simul device')
            self.SimulInfoActionExt.triggered.connect(lambda: self.fprintDeviceInfo("Simul", extended = True))

            self.SimulSettings = QAction("Set Properties ...", self, enabled=False)
            addMenuTip(self.SimulSettings, 'Set Simul Device Parameters for Meand and Prediction Limit')
            self.SimulSettings.triggered.connect(gdev_simul.getSimulProperties)

            deviceSubMenuSimul  = deviceMenu.addMenu("Simul Device Series")
            deviceSubMenuSimul.setToolTipsVisible(True)
            deviceSubMenuSimul.addAction(self.SimulInfoAction)
            deviceSubMenuSimul.addAction(self.SimulSettings)


    # submenu Manu
        if gglobs.Devices["Manu"][ACTIV]  :

            self.ManuInfoAction = QAction('Show Info', self, enabled=True)
            addMenuTip(self.ManuInfoAction, 'Show basic info on Manu device')
            self.ManuInfoAction.triggered.connect(lambda: self.fprintDeviceInfo("Manu", extended = False))

            # self.ManuInfoActionExt = QAction('Show Extended Info', self, enabled=False)
            # addMenuTip(self.ManuInfoActionExt, 'Show extended info on Manu device')
            # self.ManuInfoActionExt.triggered.connect(lambda: self.fprintDeviceInfo("Manu", extended = True))

            self.ManuValAction = QAction('Enter Values Manually', self, enabled=False)
            addMenuTip(self.ManuValAction, "Enter Values Manually")
            self.ManuValAction.triggered.connect(gdev_manu.setManuValue)

            deviceSubMenuManu  = deviceMenu.addMenu("Manu Series")
            deviceSubMenuManu.setToolTipsVisible(True)
            deviceSubMenuManu.addAction(self.ManuInfoAction)
            #deviceSubMenuManu.addAction(self.ManuInfoActionExt)
            deviceSubMenuManu.addAction(self.ManuValAction)


    # submenu WiFiServer
        if gglobs.Devices["WiFiServer"][ACTIV] :

            self.WiFiInfoAction = QAction('Show Info', self, enabled=True)
            addMenuTip(self.WiFiInfoAction, 'Show basic info on WiFiServer device')
            self.WiFiInfoAction.triggered.connect(lambda: self.fprintDeviceInfo("WiFiServer", extended=False))

            self.WiFiInfoActionExt = QAction('Show Extended Info', self, enabled=False)
            addMenuTip(self.WiFiInfoActionExt, 'Show extended info on WiFiServer device')
            self.WiFiInfoActionExt.triggered.connect(lambda: self.fprintDeviceInfo("WiFiServer", extended = True))

            self.WiFiPingAction = QAction("Ping WiFiServer Device", self)
            addMenuTip(self.WiFiPingAction, 'Ping WiFiServer Device and report success or failure')
            self.WiFiPingAction.triggered.connect(lambda: gdev_wifiserver.pingWiFiServer())

            self.WiFiSettingsAction = QAction('Set WiFiServer Data Type ...', self, enabled=True)
            addMenuTip(self.WiFiSettingsAction, "Set data type LAST or AVG")
            self.WiFiSettingsAction.triggered.connect(gdev_wifiserver.setWiFiServerProperties)

            self.WiFiResetAction = QAction("Reset WiFiServer Device", self)
            addMenuTip(self.WiFiResetAction, 'Reset WiFiServer Device')
            self.WiFiResetAction.triggered.connect(lambda: gdev_wifiserver.resetWiFiServer())

            deviceSubMenuWiFi  = deviceMenu.addMenu("WiFiServer Series")
            deviceSubMenuWiFi.setToolTipsVisible(True)
            deviceSubMenuWiFi.addAction(self.WiFiInfoAction)
            deviceSubMenuWiFi.addAction(self.WiFiInfoActionExt)
            deviceSubMenuWiFi.addAction(self.WiFiPingAction)
            deviceSubMenuWiFi.addAction(self.WiFiSettingsAction)
            deviceSubMenuWiFi.addAction(self.WiFiResetAction)


    # submenu WiFiClient
        if gglobs.Devices["WiFiClient"][ACTIV]  :

            self.WiFiClientInfoAction = QAction('Show Info', self, enabled=True)
            addMenuTip(self.WiFiClientInfoAction, 'Show basic info on WiFiClient device')
            self.WiFiClientInfoAction.triggered.connect(lambda: self.fprintDeviceInfo("WiFiClient", extended=False))

            # self.WiFiClientInfoActionExt = QAction('Show Extended Info', self, enabled=False)
            # addMenuTip(self.WiFiClientInfoActionExt, 'Show extended info on WiFiClient device')
            # self.WiFiClientInfoActionExt.triggered.connect(lambda: self.fprintDeviceInfo("WiFiClient", extended = True))

            # self.WiFiClientSettingsAction = QAction('Set WiFiClient Properties ...', self, enabled=True)
            # addMenuTip(self.WiFiClientSettingsAction, "Set properties like IP and data type")
            # self.WiFiClientSettingsAction.triggered.connect(gdev_wificlient.setWiFiClientProperties)

            deviceSubMenuWiFiClient  = deviceMenu.addMenu("WiFiClient Series")
            deviceSubMenuWiFiClient.setToolTipsVisible(True)
            deviceSubMenuWiFiClient.addAction(self.WiFiClientInfoAction)
            # deviceSubMenuWiFiClient.addAction(self.WiFiClientInfoActionExt)       # presently no extended info
            # deviceSubMenuWiFiClient.addAction(self.WiFiClientSettingsAction)


    # submenu RaspiPulse
        if gglobs.Devices["RaspiPulse"][ACTIV]  :

            self.RaspiPulseInfoAction = QAction('Show Info', self, enabled=True)
            addMenuTip(self.RaspiPulseInfoAction, 'Show basic info on RaspiPulse device')
            self.RaspiPulseInfoAction.triggered.connect(lambda: self.fprintDeviceInfo("RaspiPulse", extended=False))

            self.RaspiPulseInfoActionExt = QAction('Show Extended Info', self, enabled=False)
            addMenuTip(self.RaspiPulseInfoActionExt, 'Show extended info on RaspiPulse device')
            self.RaspiPulseInfoActionExt.triggered.connect(lambda: self.fprintDeviceInfo("RaspiPulse", extended = True))

            self.RaspiPulseResetAction = QAction("Reset RaspiPulse Device", self)
            addMenuTip(self.RaspiPulseResetAction, 'Reset RaspiPulse Device')
            self.RaspiPulseResetAction.triggered.connect(lambda: gdev_raspipulse.resetRaspiPulse())

            deviceSubMenuRaspiPulse  = deviceMenu.addMenu("RaspiPulse Series")
            deviceSubMenuRaspiPulse.setToolTipsVisible(True)
            deviceSubMenuRaspiPulse.addAction(self.RaspiPulseInfoAction)
            deviceSubMenuRaspiPulse.addAction(self.RaspiPulseInfoActionExt)
            deviceSubMenuRaspiPulse.addAction(self.RaspiPulseResetAction)


    # submenu RaspiI2C
        if gglobs.Devices["RaspiI2C"][ACTIV]  :

            self.RaspiI2CInfoAction = QAction('Show Info', self, enabled=True)
            addMenuTip(self.RaspiI2CInfoAction, 'Show basic info on RaspiI2C device')
            self.RaspiI2CInfoAction.triggered.connect(lambda: self.fprintDeviceInfo("RaspiI2C", extended=False))

            self.RaspiI2CInfoActionExt = QAction('Show Extended Info', self, enabled=False)
            addMenuTip(self.RaspiI2CInfoActionExt, 'Show extended info on RaspiI2C device')
            self.RaspiI2CInfoActionExt.triggered.connect(lambda: self.fprintDeviceInfo("RaspiI2C", extended = True))

            self.RaspiI2CResetAction = QAction("Reset RaspiI2C Device", self)
            addMenuTip(self.RaspiI2CResetAction, 'Reset RaspiI2C Device')
            self.RaspiI2CResetAction.triggered.connect(lambda: gdev_raspii2c.resetRaspiI2C())

            deviceSubMenuRaspiI2C  = deviceMenu.addMenu("RaspiI2C Series")
            deviceSubMenuRaspiI2C.setToolTipsVisible(True)
            deviceSubMenuRaspiI2C.addAction(self.RaspiI2CInfoAction)
            deviceSubMenuRaspiI2C.addAction(self.RaspiI2CInfoActionExt)
            deviceSubMenuRaspiI2C.addAction(self.RaspiI2CResetAction)


    # submenu RadPro
        if gglobs.Devices["Rad Pro"][ACTIV] :

            self.RadProInfoAction = QAction('Show Info', self, enabled=True)
            addMenuTip(self.RadProInfoAction, 'Show basic info on Rad Pro device')
            self.RadProInfoAction.triggered.connect(lambda: self.fprintDeviceInfo("Rad Pro", extended = True))

            self.RadProSetSerialPortAction = QAction('Set Serial Port ...', self, enabled=True)
            addMenuTip(self.RadProSetSerialPortAction, 'Manually set the serial port of the Rad Pro device')
            self.RadProSetSerialPortAction.triggered.connect(lambda: setDeviceSerialPort("Rad Pro", gglobs.RadProPort))

            deviceSubMenuRadPro  = deviceMenu.addMenu("Rad Pro Series")
            deviceSubMenuRadPro.setToolTipsVisible(True)
            deviceSubMenuRadPro.addAction(self.RadProInfoAction)
            deviceSubMenuRadPro.addAction(self.RadProSetSerialPortAction)



    # widgets for device in toolbar
        devBtnSize = 65

        #  '#00C853',        # Google color green
        #  '#ffe500',        # Google color yellow
        #  '#EA4335',        # Google color red
        # !!! MUST NOT have a colon ':' after QPushButton !!!
        # self.dbtnStyleSheetON    = "QPushButton {margin-right:5px; background-color: #12cc3d; border-radius: 2px; border:1px solid silver; color: black; font-size:14px; font-weight:bold}"
        # self.dbtnStyleSheetOFF   = "QPushButton {margin-right:5px;  }"
        # self.dbtnStyleSheetError = "QPushButton {margin-right:5px; background-color: #ff3333; border-radius: 2px; border:1px solid silver; color: black; font-size:14px; font-weight:bold}"
        # self.dbtnStyleSheetSimul = "QPushButton {margin-right:5px; background-color: #FFF373; border-radius: 2px; border:1px solid silver; color: black; font-size:14px; font-weight:bold}"

        self.dbtnStyleSheetOFF   = "QPushButton {margin-right:5px;  }"
        self.dbtnStyleSheetError = "QPushButton {margin-right:5px; background-color: #EA4335; border-radius: 2px; border:1px solid silver; color: black; font-size:14px; font-weight:bold}"
        self.dbtnStyleSheetSimul = "QPushButton {margin-right:5px; background-color: #ffe500; border-radius: 2px; border:1px solid silver; color: black; font-size:14px; font-weight:bold}"
        self.dbtnStyleSheetON    = "QPushButton {margin-right:5px; background-color: #00C853; border-radius: 2px; border:1px solid silver; color: black; font-size:14px; font-weight:bold}"

        # Power button (for GMC only)
        self.dbtnGMCPower = QPushButton()
        self.dbtnGMCPower.setIcon(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_power-round_off.png'))))
        self.dbtnGMCPower.setFixedSize(32, 33)
        self.dbtnGMCPower.setEnabled(False)
        self.dbtnGMCPower.setStyleSheet("QPushButton {margin-right:1px; border:0px; }")
        self.dbtnGMCPower.setIconSize(QSize(31, 31))
        self.dbtnGMCPower.setToolTip ('Toggle GMC Device Power ON / OFF')
        self.dbtnGMCPower.setAutoFillBackground(True) # This is important!! Why???
        self.dbtnGMCPower.clicked.connect(lambda: self.toggleGMCPower())

        self.connectTextGMC = 'GMC'
        self.dbtnGMC = QPushButton(self.connectTextGMC)
        self.dbtnGMC.setFixedSize(devBtnSize, 32)
        self.dbtnGMC.setToolTip("GMC Device - Click for Device Info")
        self.dbtnGMC.setStyleSheet(self.dbtnStyleSheetOFF)
        self.dbtnGMC.setAutoFillBackground(True) # This is important!! Why???
        self.dbtnGMC.clicked.connect(lambda: self.fprintDeviceInfo("GMC", extended=False))

        self.connectTextAudio = 'Audio'
        self.dbtnAudio = QPushButton(self.connectTextAudio)
        self.dbtnAudio.setFixedSize(devBtnSize, 32)
        self.dbtnAudio.setToolTip("AudioCounter Device - Click for Device Info")
        self.dbtnAudio.setStyleSheet(self.dbtnStyleSheetOFF)
        self.dbtnAudio.setAutoFillBackground(True)
        self.dbtnAudio.clicked.connect(lambda: self.fprintDeviceInfo(self.connectTextAudio, extended = False))

        self.connectTextRM = 'RadM'
        self.dbtnRM =  QPushButton(self.connectTextRM)
        self.dbtnRM.setFixedSize(devBtnSize,32)
        self.dbtnRM.setToolTip("RadMon Device - Click for Device Info")
        self.dbtnRM.setStyleSheet(self.dbtnStyleSheetOFF)
        self.dbtnRM.setAutoFillBackground(True)
        self.dbtnRM.clicked.connect(lambda: self.fprintDeviceInfo("RadMon"))

        self.connectTextAmbio = 'Ambio'
        self.dbtnAmbio =  QPushButton(self.connectTextAmbio)
        self.dbtnAmbio.setFixedSize(devBtnSize, 32)
        self.dbtnAmbio.setToolTip("Manu Device - Click for Device Info")
        self.dbtnAmbio.setStyleSheet(self.dbtnStyleSheetOFF)
        self.dbtnAmbio.setAutoFillBackground(True)
        self.dbtnAmbio.clicked.connect(lambda: self.fprintDeviceInfo("AmbioMon"))

        self.connectTextGS = 'GScout'
        self.dbtnGS =  QPushButton(self.connectTextGS)
        self.dbtnGS.setFixedSize(devBtnSize, 32)
        self.dbtnGS.setToolTip("GammaScout Device - Click for Device Info")
        self.dbtnGS.setStyleSheet(self.dbtnStyleSheetOFF)
        self.dbtnGS.setAutoFillBackground(True)
        self.dbtnGS.clicked.connect(lambda: self.fprintDeviceInfo("GammaScout"))

        self.connectTextI2C = 'I2C'
        self.dbtnI2C =  QPushButton(self.connectTextI2C)
        self.dbtnI2C.setFixedSize(devBtnSize, 32)
        self.dbtnI2C.setToolTip("I2C Device - Click for Device Info")
        self.dbtnI2C.setStyleSheet(self.dbtnStyleSheetOFF)
        self.dbtnI2C.setAutoFillBackground(True)
        self.dbtnI2C.clicked.connect(lambda: self.fprintDeviceInfo("I2C" ))

        self.connectTextLJ = 'LabJck'
        self.dbtnLJ =  QPushButton(self.connectTextLJ)
        self.dbtnLJ.setFixedSize(devBtnSize, 32)
        self.dbtnLJ.setToolTip("LabJack Device - Click for Device Info")
        self.dbtnLJ.setStyleSheet(self.dbtnStyleSheetOFF)
        self.dbtnLJ.setAutoFillBackground(True)
        self.dbtnLJ.clicked.connect(lambda: self.fprintDeviceInfo("LabJack"))

        self.connectTextMiniMon = 'MiniM'
        self.dbtnMiniMon = QPushButton(self.connectTextMiniMon)
        self.dbtnMiniMon.setFixedSize(devBtnSize, 32)
        self.dbtnMiniMon.setToolTip("MiniMon Device - Click for Device Info")
        self.dbtnMiniMon.setStyleSheet(self.dbtnStyleSheetOFF)
        self.dbtnMiniMon.setAutoFillBackground(True)
        self.dbtnMiniMon.clicked.connect(lambda: self.fprintDeviceInfo("MiniMon"))

        self.connectTextSimul = 'Simul'
        self.dbtnSimul =  QPushButton(self.connectTextSimul)
        self.dbtnSimul.setFixedSize(devBtnSize, 32)
        self.dbtnSimul.setToolTip("Simul Device - Click for Device Info")
        self.dbtnSimul.setStyleSheet(self.dbtnStyleSheetOFF)
        self.dbtnSimul.setAutoFillBackground(True)
        self.dbtnSimul.clicked.connect(lambda: self.fprintDeviceInfo(self.connectTextSimul))

        self.connectTextWiFiClient = 'WiFiC'
        self.dbtnWClient = QPushButton(self.connectTextWiFiClient)
        self.dbtnWClient.setFixedSize(devBtnSize, 32)
        self.dbtnWClient.setToolTip("WiFiClient Device - Click for Device Info")
        self.dbtnWClient.setStyleSheet(self.dbtnStyleSheetOFF)
        self.dbtnWClient.setAutoFillBackground(True)
        self.dbtnWClient.clicked.connect(lambda: self.fprintDeviceInfo("WiFiClient"))

        self.connectTextWiFiServer = 'WiFiS'
        self.dbtnWServer = QPushButton(self.connectTextWiFiServer)
        self.dbtnWServer.setFixedSize(devBtnSize, 32)
        self.dbtnWServer.setToolTip("WiFiServer Device - Click for Device Info")
        self.dbtnWServer.setStyleSheet(self.dbtnStyleSheetOFF)
        self.dbtnWServer.setAutoFillBackground(True)
        self.dbtnWServer.clicked.connect(lambda: self.fprintDeviceInfo("WiFiServer"))

        self.connectTextRaspiI2C = 'RI2C'
        self.dbtnRI2C = QPushButton(self.connectTextRaspiI2C)
        self.dbtnRI2C.setFixedSize(devBtnSize, 32)
        self.dbtnRI2C.setToolTip("Raspi I2C Device - Click for Device Info")
        self.dbtnRI2C.setStyleSheet(self.dbtnStyleSheetOFF)
        self.dbtnRI2C.setAutoFillBackground(True)
        self.dbtnRI2C.clicked.connect(lambda: self.fprintDeviceInfo("RaspiI2C"))

        self.connectTextRaspiPulse = 'RPuls'
        self.dbtnRPulse = QPushButton(self.connectTextRaspiPulse)
        self.dbtnRPulse.setFixedSize(devBtnSize, 32)
        self.dbtnRPulse.setToolTip("Raspi Pulse Device - Click for Device Info")
        self.dbtnRPulse.setStyleSheet(self.dbtnStyleSheetOFF)
        self.dbtnRPulse.setAutoFillBackground(True)
        self.dbtnRPulse.clicked.connect(lambda: self.fprintDeviceInfo("RaspiPulse"))

        self.connectTextManu = 'Manu'
        self.dbtnManu = QPushButton(self.connectTextManu)
        self.dbtnManu.setFixedSize(devBtnSize, 32)
        self.dbtnManu.setToolTip("Manu Device - Click for Device Info")
        self.dbtnManu.setStyleSheet(self.dbtnStyleSheetOFF)
        self.dbtnManu.setAutoFillBackground(True)
        self.dbtnManu.clicked.connect(lambda: self.fprintDeviceInfo("Manu"))

        self.connectTextRadPro = "Rad Pro"
        self.dbtnRadPro =  QPushButton(self.connectTextRadPro)
        self.dbtnRadPro.setFixedSize(devBtnSize, 32)
        self.dbtnRadPro.setToolTip("Rad Pro Device - Click for Device Info")
        self.dbtnRadPro.setStyleSheet(self.dbtnStyleSheetOFF)
        self.dbtnRadPro.setAutoFillBackground(True)
        self.dbtnRadPro.clicked.connect(lambda: self.fprintDeviceInfo("Rad Pro"))


    # toolbar Devices
        toolbar = self.addToolBar('Devices')
        toolbar.setToolTip("Devices Toolbar")
        toolbar.setIconSize(QSize(32,32))                       # standard size is too small

        toolbar.addAction(self.toggleDeviceConnectionAction)    # Connect icon
        toolbar.addWidget(QLabel("   "))                        # spacer

        if gglobs.Devices["GMC"][ACTIV]         : toolbar.addWidget(self.dbtnGMCPower)        # GMC power icon
        if gglobs.Devices["GMC"][ACTIV]         : toolbar.addWidget(self.dbtnGMC)             # GMC device display
        if gglobs.Devices["Audio"][ACTIV]       : toolbar.addWidget(self.dbtnAudio)           # AudioCounter device display
        if gglobs.Devices["RadMon"][ACTIV]      : toolbar.addWidget(self.dbtnRM)              # RadMon device display
        if gglobs.Devices["AmbioMon"][ACTIV]    : toolbar.addWidget(self.dbtnAmbio)           # Manu device display
        if gglobs.Devices["GammaScout"][ACTIV]  : toolbar.addWidget(self.dbtnGS)              # Gamma-Scout device display
        if gglobs.Devices["I2C"][ACTIV]         : toolbar.addWidget(self.dbtnI2C)             # I2C device display
        if gglobs.Devices["LabJack"][ACTIV]     : toolbar.addWidget(self.dbtnLJ)              # LabJack device display
        if gglobs.Devices["MiniMon"][ACTIV]     : toolbar.addWidget(self.dbtnMiniMon)         # MiniMon device display
        if gglobs.Devices["Simul"][ACTIV]       : toolbar.addWidget(self.dbtnSimul)           # Simul device display
        if gglobs.Devices["WiFiClient"][ACTIV]  : toolbar.addWidget(self.dbtnWClient)         # WiFiClient device display
        if gglobs.Devices["WiFiServer"][ACTIV]  : toolbar.addWidget(self.dbtnWServer)         # WiFiServer device display
        if gglobs.Devices["RaspiI2C"][ACTIV]    : toolbar.addWidget(self.dbtnRI2C)            # RaspiI2C device display
        if gglobs.Devices["RaspiPulse"][ACTIV]  : toolbar.addWidget(self.dbtnRPulse)          # RaspiPulse device display
        if gglobs.Devices["Manu"][ACTIV]        : toolbar.addWidget(self.dbtnManu)            # Manu device display
        if gglobs.Devices["Rad Pro"][ACTIV]     : toolbar.addWidget(self.dbtnRadPro)          # Rad Pro device display

#Log Menu
        self.logLoadFileAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_Log_DB.svg.png'))), 'Get Log from Database or Create New One ...', self)
        self.logLoadFileAction.setShortcut('Ctrl+L')
        addMenuTip(self.logLoadFileAction, 'Load or Create database for logging, and plot')
        self.logLoadFileAction.triggered.connect(lambda: self.getFileLog(source="Database"))

        self.logLoadCSVAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_Log_CSV.svg.png'))), 'Get Log from CSV File ...', self)
        addMenuTip(self.logLoadCSVAction, 'Load existing *.log or other CSV file, convert to database, and plot')
        self.logLoadCSVAction.triggered.connect(lambda: self.getFileLog(source="CSV File"))

        self.startloggingAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_log_start.png'))), 'Start Logging', self, enabled=False)
        addMenuTip(self.startloggingAction, 'Start logging from devices')
        self.startloggingAction.triggered.connect(self.startLogging)

        self.stoploggingAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_log_stop.png'))), 'Stop Logging', self, enabled=False)
        addMenuTip(self.stoploggingAction, 'Stop logging from devices')
        self.stoploggingAction.triggered.connect(self.stopLogging)

        # add comment
        self.addCommentAction = QAction('Add Comment to Log ...', self, enabled=False)
        addMenuTip(self.addCommentAction, 'Add a comment to the current log')
        self.addCommentAction.triggered.connect(lambda: self.addComment("Log"))

        # clear Log File
        self.clearLogfileAction = QAction('Clear Log File ...', self, enabled=True)
        addMenuTip(self.clearLogfileAction, 'Set the log file to empty state')
        self.clearLogfileAction.triggered.connect(lambda: self.clearLogfile())

        self.showLogDataAction = QAction('Show Log Data', self)
        addMenuTip(self.showLogDataAction, 'Show all records from current log')
        self.showLogDataAction.triggered.connect(lambda: self.showData("Log", full=True))

        self.showLogTagsAction = QAction('Show Log Data Tags/Comments', self)
        addMenuTip(self.showLogTagsAction, 'Show only records from current log containing tags or comments')
        self.showLogTagsAction.triggered.connect(lambda: self.showDBTags("Log"))

        self.showLogExcerptAction = QAction('Show Log Data Excerpt', self)
        addMenuTip(self.showLogExcerptAction, 'Show first and last few records of current log')
        self.showLogExcerptAction.triggered.connect(lambda: self.showData("Log", full=False))

        self.quickLogAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_quick_log.png'))), 'Quick Log', self, enabled=False)
        addMenuTip(self.quickLogAction, 'One-click log. Saves always into database default.logdb; will be overwritten on next Quick Log click')
        self.quickLogAction.triggered.connect(self.quickLog)

        self.logSnapAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_log_snap.png'))), 'Snap a new log record', self, enabled=False)
        addMenuTip(self.logSnapAction, 'Get a new log record immediately')
        self.logSnapAction.triggered.connect(self.snapLogValue)

        self.setLogTimingAction = QAction('Set Log Cycle ...', self, enabled=True)
        self.setLogTimingAction.setIcon(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_log_options.png'))))
        addMenuTip(self.setLogTimingAction, 'Set Log Cycle in seconds')
        self.setLogTimingAction.triggered.connect(self.setLogCycle)

        self.logSaveCSVAction = QAction('Save Log Data into CSV file', self)
        addMenuTip(self.logSaveCSVAction, "Save all records from current log into a CSV file with extension 'csv'")
        self.logSaveCSVAction.triggered.connect(lambda: gsup_sql.saveDataToCSV("Log", full= True))

        loggingMenu = self.menubar.addMenu('&Log')
        loggingMenu.setToolTipsVisible(True)
        loggingMenu.addAction(self.logLoadFileAction)
        loggingMenu.addAction(self.logLoadCSVAction)
        loggingMenu.addAction(self.addCommentAction)
        loggingMenu.addAction(self.clearLogfileAction)

        loggingMenu.addSeparator()
        loggingMenu.addAction(self.setLogTimingAction)
        loggingMenu.addAction(self.startloggingAction)
        loggingMenu.addAction(self.stoploggingAction)
        loggingMenu.addAction(self.quickLogAction)

        loggingMenu.addSeparator()
        loggingMenu.addAction(self.showLogDataAction)
        loggingMenu.addAction(self.showLogExcerptAction)
        loggingMenu.addAction(self.showLogTagsAction)

        loggingMenu.addSeparator()
        loggingMenu.addAction(self.logSaveCSVAction)

        # loggingMenu.triggered[QAction].connect(self.processtrigger) # just for testing; no action done

        toolbar = self.addToolBar('Log')
        toolbar.setToolTip("Log Toolbar")
        toolbar.setIconSize(QSize(32,32))  # standard size is too small
        toolbar.addAction(self.logLoadFileAction)
        # toolbar.addAction(self.logLoadCSVAction)
        toolbar.addAction(self.startloggingAction)
        toolbar.addAction(self.quickLogAction)
        toolbar.addAction(self.logSnapAction)
        toolbar.addAction(self.stoploggingAction)


#History Menu
        # load from DB
        self.loadHistDBAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_hist_DB_active.svg.png'))), 'Get History from Database ...', self)
        self.loadHistDBAction.setShortcut('Ctrl+H')
        addMenuTip(self.loadHistDBAction, 'Load history data from database and plot')
        self.loadHistDBAction.triggered.connect(lambda: self.getFileHistory("Database"))

        # load from CSV file
        self.loadHistHisAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_hist_CSV.svg.png'))), 'Get History from CSV File ...', self)
        addMenuTip(self.loadHistHisAction, 'Load existing *.his or other CSV file, convert to database file, and plot')
        self.loadHistHisAction.triggered.connect(lambda: self.getFileHistory("Parsed File"))

        # add comment
        self.addHistCommentAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, ''))), 'Add Comment to History ...', self, enabled=False)
        addMenuTip(self.addHistCommentAction, 'Add a comment to the current history')
        self.addHistCommentAction.triggered.connect(lambda: self.addComment("His"))

        historyMenu = self.menubar.addMenu('&History')
        historyMenu.setToolTipsVisible(True)

        historyMenu.addAction(self.loadHistDBAction)
        historyMenu.addAction(self.loadHistHisAction)
        historyMenu.addAction(self.addHistCommentAction)

        historyMenu.addSeparator()


### begin device specific History actions #########################

    # valid for GMC only
        if gglobs.Devices["GMC"][ACTIV] :
            # get his from device
            self.histGMCDeviceAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_hist_device_active.png'))), 'Get History from Device ...', self, enabled=False)
            addMenuTip(self.histGMCDeviceAction, 'Load history data from any GMC device, create database, and plot\n(when NOT logging)')
            self.histGMCDeviceAction.triggered.connect(lambda: self.getFileHistory("Device"))

            # get his from bin file
            self.loadHistBinAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_hist_bin_active.png'))), 'Get History from GMC Binary File ...', self)
            addMenuTip(self.loadHistBinAction, 'Load history data from a GMC format binary file and plot')
            self.loadHistBinAction.triggered.connect(lambda: self.getFileHistory("Binary File"))

            # show bin data bytecount
            self.showHistBinDataDetailAction = QAction('Show History Binary Data Bytecount', self)
            addMenuTip(self.showHistBinDataDetailAction, 'Show counts of bytes in history binary data')
            self.showHistBinDataDetailAction.triggered.connect(lambda: gdev_gmc_hist.fprintHistDetails())

            # show bin data
            self.showHistBinDataAction = QAction('Show History Binary Data', self)
            addMenuTip(self.showHistBinDataAction, 'Show history binary data in human readable form')
            self.showHistBinDataAction.triggered.connect(lambda: self.showData("HisBin"))

            # show bin data excerpt
            self.showHistBinDataExcerptAction = QAction('Show History Binary Data Excerpt', self)
            addMenuTip(self.showHistBinDataExcerptAction, 'Show first and last few lines of history binary data in human readable form')
            self.showHistBinDataExcerptAction.triggered.connect(lambda: self.showData("HisBin", full=False))

            # show AA / FF map
            self.historyFFAction = QAction("Show History Binary Data as AA / FF Map", self)
            addMenuTip(self.historyFFAction, "Show History Binary Data as a map highlighting the locations of bytes with FF value (FF=empty value)")
            self.historyFFAction.triggered.connect(lambda: gsup_sql.createByteMapFromDB(0xFF))

            # save bin data to bin file
            self.showHistBinDataSaveAction = QAction('Save History Binary Data to File', self)
            addMenuTip(self.showHistBinDataSaveAction, 'Save the history binary data as a *.bin file')
            self.showHistBinDataSaveAction.triggered.connect(lambda: gdev_gmc_hist.saveHistBinaryData())

            historySubMenuGMC = historyMenu.addMenu("GMC Series")
            historySubMenuGMC.setToolTipsVisible(True)

            historySubMenuGMC.addAction(self.histGMCDeviceAction)
            historySubMenuGMC.addAction(self.loadHistBinAction)

            historySubMenuGMC.addSeparator()
            historySubMenuGMC.addAction(self.showHistBinDataDetailAction) # bytecount
            historySubMenuGMC.addAction(self.showHistBinDataAction)
            historySubMenuGMC.addAction(self.showHistBinDataExcerptAction)
            historySubMenuGMC.addAction(self.historyFFAction)

            historySubMenuGMC.addSeparator()
            historySubMenuGMC.addAction(self.showHistBinDataSaveAction)
            #historyMenu.triggered[QAction].connect(self.processtrigger)


    # valid for Gamma-Scout only
        if gglobs.Devices["GammaScout"][ACTIV]:
            self.histGSDeviceAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_hist_device_active.png'))), 'Get History from Device ...', self, enabled=False)
            addMenuTip(self.histGSDeviceAction, 'Load history data from any Gamma-Scout device, create database, and plot\n(when NOT logging)')
            self.histGSDeviceAction.triggered.connect(lambda: self.getFileHistory("GSDevice"))

            self.histGSDatFileAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_hist_device_active.png'))), 'Get History from Gamma-Scout Dat File ...', self)
            addMenuTip(self.histGSDatFileAction, 'Load history data from a Gamma-Scout dat file, create database, and plot')
            self.histGSDatFileAction.triggered.connect(lambda: self.getFileHistory("GSDatFile"))

            self.showHistDatDataAction = QAction('Show History Dat Data', self)
            addMenuTip(self.showHistDatDataAction, 'Show the history data in Gamma-Scout like *.dat file')
            self.showHistDatDataAction.triggered.connect(lambda: gdev_gscout.GSshowDatData())

            self.showHistDatDataSaveAction = QAction('Save History Data to Dat File', self)
            addMenuTip(self.showHistDatDataSaveAction, 'Save the history data as Gamma-Scout *.dat format')
            self.showHistDatDataSaveAction.triggered.connect(lambda: gdev_gscout.GSsaveDatDataToDatFile())

            historySubMenuGS = historyMenu.addMenu("Gamma Scout Series")
            historySubMenuGS.setToolTipsVisible(True)

            historySubMenuGS.addAction(self.histGSDeviceAction)
            historySubMenuGS.addAction(self.histGSDatFileAction)

            historySubMenuGS.addSeparator()
            historySubMenuGS.addAction(self.showHistDatDataAction)

            historySubMenuGS.addSeparator()
            historySubMenuGS.addAction(self.showHistDatDataSaveAction)


    # valid for AmbioMon only
        if gglobs.Devices["AmbioMon"][ACTIV] :
            self.histAMDeviceCAMAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_hist_device_active.png'))), 'Get History Binary CAM data from Device', self, enabled=False)
            addMenuTip(self.histAMDeviceCAMAction, 'Load Counter & Ambient history data from AmbioMon device, create database, and plot')
            self.histAMDeviceCAMAction.triggered.connect(lambda: self.getFileHistory("AMDeviceCAM"))

            self.histAMDeviceCPSAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_hist_device_active.png'))), 'Get History Binary CPS data from Device', self, enabled=False)
            addMenuTip(self.histAMDeviceCPSAction, 'Load Counts Per Second history data from AmbioMon device, create database, and plot')
            self.histAMDeviceCPSAction.triggered.connect(lambda: self.getFileHistory("AMDeviceCPS"))

            self.histAMCAMFileAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_hist_device_active.png'))), 'Get History Binary CAM data from File ...', self)
            addMenuTip(self.histAMCAMFileAction, 'Load history data from an AmbioMon CAM file, create database, and plot')
            self.histAMCAMFileAction.triggered.connect(lambda: self.getFileHistory("AMFileCAM"))

            self.histAMCPSFileAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_hist_device_active.png'))), 'Get History Binary CPS data from File ...', self)
            addMenuTip(self.histAMCPSFileAction, 'Load history data from an AmbioMon CPS file, create database, and plot')
            self.histAMCPSFileAction.triggered.connect(lambda: self.getFileHistory("AMFileCPS"))

            #~ self.showHistDatDataAction = QAction('Show History Raw Data', self)
            #~ addMenuTip(self.showHistDatDataAction, 'Show the history data in Manu like *.dat file')
            #~ self.showHistDatDataAction.triggered.connect(gdev_ambiomon.AMshowDatData)

            #~ self.showHistDatDataSaveAction = QAction('Save History Raw Data to .csv File', self)
            #~ addMenuTip(self.showHistDatDataSaveAction, 'Save the history data as AmbioMon *.csv format')
            #~ self.showHistDatDataSaveAction.triggered.connect(gdev_ambiomon.AMsaveHistDatData)

            historySubMenuAM = historyMenu.addMenu("AmbioMon Series")
            historySubMenuAM.setToolTipsVisible(True)

            historySubMenuAM.addAction(self.histAMDeviceCAMAction)
            historySubMenuAM.addAction(self.histAMDeviceCPSAction)
            historySubMenuAM.addAction(self.histAMCAMFileAction)
            historySubMenuAM.addAction(self.histAMCPSFileAction)

            #~ historySubMenuAM.addSeparator()
            #~ historySubMenuAM.addAction(self.showHistDatDataAction)

            #~ historySubMenuAM.addSeparator()
            #~ historySubMenuAM.addAction(self.showHistDatDataSaveAction)


    # valid for Rad Pro only
        if gglobs.Devices["Rad Pro"][ACTIV] :
            # get history from device
            self.histRadProLoadNewAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_hist_device_active.png'))), 'Get New History from Device ...', self, enabled=False)
            addMenuTip(self.histRadProLoadNewAction, 'Load new history data from any Rad Pro device, create database, and plot\n(when NOT logging)')
            self.histRadProLoadNewAction.triggered.connect(lambda: self.getFileHistory("Rad Pro Device (new)"))

            self.histRadProLoadAllAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_hist_device_active.png'))), 'Get All History from Device ...', self, enabled=False)
            addMenuTip(self.histRadProLoadAllAction, 'Load all history data from any Rad Pro device, create database, and plot\n(when NOT logging)')
            self.histRadProLoadAllAction.triggered.connect(lambda: self.getFileHistory("Rad Pro Device (all)"))

            historySubMenuRadPro = historyMenu.addMenu("Rad Pro Series")
            historySubMenuRadPro.setToolTipsVisible(True)

            historySubMenuRadPro.addAction(self.histRadProLoadNewAction)
            historySubMenuRadPro.addAction(self.histRadProLoadAllAction)


##### end device specific ##############


        # show his data
        self.showHistHisDataAction = QAction('Show History Data', self)
        addMenuTip(self.showHistHisDataAction, 'Show history data as parsed from binary data')
        self.showHistHisDataAction.triggered.connect(lambda: self.showData("His", full=True))

        # show his data excerpt
        self.showHistHisDataExcerptAction = QAction('Show History Data Excerpt', self)
        addMenuTip(self.showHistHisDataExcerptAction, 'Show first and last few records of history data parsed from binary data')
        self.showHistHisDataExcerptAction.triggered.connect(lambda: self.showData("His", full=False))

        # show tags/comments
        self.showHistHisTagsAction = QAction('Show History Data Tags/Comments', self)
        addMenuTip(self.showHistHisTagsAction, 'Show only records from history containing tags or comments')
        self.showHistHisTagsAction.triggered.connect(lambda: self.showDBTags("History"))

        # show with parse
        self.showHistParseAction = QAction("Show History Data with Parse Comments", self)
        addMenuTip(self.showHistParseAction, "Show History Data including extended Parse Comments")
        self.showHistParseAction.triggered.connect(lambda: self.showData("HisParse", full=True))

        # show with parse excerpt
        self.showHistParseExcerttAction = QAction("Show History Data with Parse Comments Excerpt", self)
        addMenuTip(self.showHistParseExcerttAction, "Show first and last few records of history Data including extended Parse Comments")
        self.showHistParseExcerttAction.triggered.connect(lambda: self.showData("HisParse", full=False))

        # save his data to csv file
        self.histSaveCSVAction = QAction('Save History Data into CSV file', self)
        addMenuTip(self.histSaveCSVAction, "Save all records from current history into a CSV file with extension 'csv'")
        self.histSaveCSVAction.triggered.connect(lambda: gsup_sql.saveDataToCSV("His", full=True))

        historyMenu.addSeparator()
        historyMenu.addAction(self.showHistHisDataAction)
        historyMenu.addAction(self.showHistHisDataExcerptAction)
        historyMenu.addAction(self.showHistHisTagsAction)
        historyMenu.addAction(self.showHistParseAction)
        historyMenu.addAction(self.showHistParseExcerttAction)

        historyMenu.addSeparator()
        historyMenu.addAction(self.histSaveCSVAction)

        toolbar = self.addToolBar('History')
        toolbar.setToolTip("History Toolbar")
        toolbar.setIconSize(QSize(32,32))  # standard size is too small
        toolbar.addAction(self.loadHistDBAction)
        # toolbar.addAction(self.loadHistHisAction)

# Web menu
        # menu entry and toolbar button for Show IP Address
        self.IPAddrAction = QAction('Show IP Status', self, enabled=True)
        self.IPAddrAction.setIcon(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_ip_address.png'))))
        addMenuTip(self.IPAddrAction, "Show GeigerLog's current IP Address and Ports usage")
        self.IPAddrAction.triggered.connect(lambda: self.showIPStatus())

        # menu entry and toolbar button for Web Server access
        self.MonServerAction = QAction('Set up Monitor Server ...', self, enabled=True)
        self.MonServerAction.setIcon(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_monserver_inactive.png'))))
        addMenuTip(self.MonServerAction, "Set Properties of Monitor Server")
        self.MonServerAction.triggered.connect(lambda: gweb_monserv.initMonServer())

        # # menu entry and toolbar button for Telegram access
        # self.TelegramAction = QAction(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_Telegram_inactive.png'))), 'Set up Telegram Messenger ...', self, enabled=True)
        # addMenuTip(self.TelegramAction, 'Set Properties of Telegram Messenger Updating')
        # self.TelegramAction.triggered.connect(lambda: gsup_tools.setupTelegram())

        # menu entry and toolbar button for GMC Map access
        self.GMCmapAction = QAction('Set up Radiation World Map ...', self, enabled=True)
        self.GMCmapAction.setIcon(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_world_v2_inactive.png'))))
        addMenuTip(self.GMCmapAction, 'Set Properties of Radiation World Map Updating')
        self.GMCmapAction.triggered.connect(lambda: gweb_radworld.setupRadWorldMap())

        webMenu = self.menubar.addMenu('&Web')
        webMenu.setToolTipsVisible(True)
        webMenu.addAction(self.IPAddrAction)
        webMenu.addAction(self.MonServerAction)
        # webMenu.addAction(self.TelegramAction)
        webMenu.addAction(self.GMCmapAction)

        toolbar = self.addToolBar('Web')
        toolbar.setToolTip("Web Toolbar")
        toolbar.setIconSize(QSize(32,32))  # standard size is too small
        toolbar.addAction(self.IPAddrAction)
        toolbar.addAction(self.MonServerAction)
        # toolbar.addAction(self.TelegramAction)
        toolbar.addAction(self.GMCmapAction)

# Tools menu
        # menu entry and toolbar button for tools

        PlotLogAction = QAction('Plot Full Log', self)
        addMenuTip(PlotLogAction, 'Plot the complete Log file')
        PlotLogAction.triggered.connect(lambda: self.plotGraph('Log', full=False))

        PlotHisAction = QAction('Plot Full History', self)
        addMenuTip(PlotHisAction, 'Plot the complete History file')
        PlotHisAction.triggered.connect(lambda: self.plotGraph('His', full=False))

        fprintSuStAction =  QAction('Show SuSt (Summary Statistics) of Plot Data ', self)
        addMenuTip(fprintSuStAction, "Shows Summary Statistics of all variables and data in the plot")
        fprintSuStAction.triggered.connect(lambda: gsup_tools.fprintSuSt())

        showStatsAction =  QAction('Show Statistics of Plot Data ', self)
        addMenuTip(showStatsAction, "Shows the Statistics of the data in the current plot")
        showStatsAction.triggered.connect(lambda: gsup_tools.showStats())

        PlotScatterAction = QAction('Show Scatterplot from Plot Data ...', self)
        addMenuTip(PlotScatterAction, 'Show an X-Y Scatter plot with optional polynomial fit, using data in the plot')
        PlotScatterAction.triggered.connect(lambda: gsup_tools.selectScatterPlotVars())

        PlotPoissonAction =  QAction("Show Poisson Test of Plot Data", self)
        addMenuTip(PlotPoissonAction, "Shows a Poisson curve on a histogram of the data in the plot for the selected variable")
        PlotPoissonAction.triggered.connect(lambda: gstat_poisson.plotPoisson())

        PlotFFTAction =  QAction("Show FFT && Autocorrelation of Plot Data", self)
        addMenuTip(PlotFFTAction, "Shows the FFT Spectra & an Autocorrelation of the data in the plot for the selected variable")
        PlotFFTAction.triggered.connect(lambda: gstat_fft.plotFFT())

        editScalingAction = QAction('Scaling ...', self)
        addMenuTip(editScalingAction, "Scaling - View and edit current settings for value- and graph-scaling")
        editScalingAction.triggered.connect(lambda: self.editScaling())

        SaveGraph2FileAction = QAction("Save Graph to File", self)
        addMenuTip(SaveGraph2FileAction, "Save the graph as a 'PNG' file")
        SaveGraph2FileAction.triggered.connect(lambda: saveGraphToFile())

        fprintPlotDataAction = QAction('Show Plot Data', self)
        addMenuTip(fprintPlotDataAction, 'Show the DateTime and values of all variables as currently selected in Plot')
        fprintPlotDataAction.triggered.connect(lambda: self.showData("PlotData"))

        DisplayLastValAction = QAction('Display Last Values', self)
        addMenuTip(DisplayLastValAction, 'Show a table with the variables and their last value, including scaled value')
        DisplayLastValAction.triggered.connect(lambda: gsup_tools.displayLastValues())

        FixAudioAction = QAction("Fix garbled audio", self)
        addMenuTip(FixAudioAction, 'Fix for a Linux-only PulseAudio bug resulting in garbled audio')
        FixAudioAction.triggered.connect(lambda: fixGarbledAudio())


        toolsMenu = self.menubar.addMenu('&Tools')
        toolsMenu.setToolTipsVisible(True)

        toolsMenu.addAction(PlotLogAction)
        toolsMenu.addAction(PlotHisAction)

        toolsMenu.addSeparator()
        toolsMenu.addAction(fprintSuStAction)
        toolsMenu.addAction(showStatsAction)
        toolsMenu.addAction(PlotScatterAction)
        toolsMenu.addAction(PlotPoissonAction)
        toolsMenu.addAction(PlotFFTAction)

        toolsMenu.addSeparator()
        toolsMenu.addAction(editScalingAction)
        toolsMenu.addAction(SaveGraph2FileAction)
        toolsMenu.addAction(fprintPlotDataAction)
        toolsMenu.addAction(DisplayLastValAction)

        if "LINUX" in platform.platform().upper():
            toolsMenu.addSeparator()
            toolsMenu.addAction(FixAudioAction)


#Help Menu
        # menu entries for Help
        self.helpQickStartAction = QAction('Quickstart', self)
        addMenuTip(self.helpQickStartAction, 'Guidance for an easy start')
        self.helpQickStartAction.triggered.connect(self.helpQuickStart)

        self.helpManualUrlAction = QAction('GeigerLog Manual', self)
        addMenuTip(self.helpManualUrlAction, 'Open the GeigerLog Manual (locally if available, or online)')
        self.helpManualUrlAction.triggered.connect(openManual)

        self.helpFirmwareBugAction = QAction("Devices' Firmware Bugs", self)
        addMenuTip(self.helpFirmwareBugAction, 'Info on Firmware Bugs of the Devices and Workarounds')
        self.helpFirmwareBugAction.triggered.connect(self.helpFirmwareBugs)

        self.helpWorldMapsAction = QAction('Radiation World Maps', self)
        addMenuTip(self.helpWorldMapsAction, 'Contributing to the Radiation World Maps')
        self.helpWorldMapsAction.triggered.connect(self.helpWorldMaps)

        self.helpOccupationalRadiationAction = QAction('Occupational Radiation Limits', self)
        addMenuTip(self.helpOccupationalRadiationAction, 'Occupational Radiation Limits in USA and Germany')
        self.helpOccupationalRadiationAction.triggered.connect(self.helpOccupationalRadiation)

        self.showOptionsAction = QAction('Show Command Line Options', self)
        addMenuTip(self.showOptionsAction, 'Show command line options')
        self.showOptionsAction.triggered.connect(self.helpOptions)

        self.helpAboutAction = QAction('About GeigerLog', self)
        addMenuTip(self.helpAboutAction, 'About the GeigerLog program')
        self.helpAboutAction.triggered.connect(self.helpAbout)

        #self.helpAboutQTAction = QAction('About Qt', self)
        #addMenuTip(self.helpAboutQTAction, 'About the Qt toolkit used by GeigerLog')
        #self.helpAboutQTAction.triggered.connect(QApplication.aboutQt)

        helpMenu = self.menubar.addMenu('Hel&p')
        helpMenu.setToolTipsVisible(True)
        helpMenu.addAction(self.helpQickStartAction)
        helpMenu.addAction(self.helpManualUrlAction)
        helpMenu.addAction(self.helpFirmwareBugAction)
        helpMenu.addAction(self.helpWorldMapsAction)
        helpMenu.addAction(self.helpOccupationalRadiationAction)
        helpMenu.addAction(self.showOptionsAction)

        helpMenu.addSeparator()
        #helpMenu.addAction(self.helpAboutQTAction)
        helpMenu.addAction(self.helpAboutAction)

        #helpMenu.triggered[QAction].connect(self.processtrigger)


# Devel Menu
        if gglobs.devel:
            showOptionsAction = QAction('Show Command Line Options', self)
            addMenuTip(showOptionsAction, 'Show command line options')
            showOptionsAction.triggered.connect(self.helpOptions)

            changeOptionsAction = QAction('Change Command Line Options', self)
            addMenuTip(changeOptionsAction, 'Allows to change some command line options while running')
            changeOptionsAction.triggered.connect(self.changeOptions)

            showSystemInfoAction = QAction('Show System Info', self)
            addMenuTip(showSystemInfoAction, 'Show Details on the Current Program Settings and Environment')
            showSystemInfoAction.triggered.connect(showSystemInfo)

            develIotaAction = QAction("Print Vars Status", self)
            develIotaAction.triggered.connect(lambda: printVarsStatus())

            develAlphaAction = QAction("Convolution FFT", self)
            develAlphaAction.triggered.connect(lambda: gstat_convfft.convFFT())

            develBetaAction = QAction("Create Synthetic Data", self)
            develBetaAction.triggered.connect(lambda: gstat_synth.createSyntheticData())

            develGammaAction = QAction("GMC Configuration", self)
            develGammaAction.triggered.connect(lambda: gdev_gmc.editGMC_Configuration())

            develBipAction = QAction("Play Bip", self)
            develBipAction.triggered.connect(lambda: playWav(wtype = "ok"))

            develBurpAction = QAction("Play Burp", self)
            develBurpAction.triggered.connect(lambda: playWav(wtype = "burp"))

            develClickAction = QAction("Play Geiger Click", self)
            develClickAction.triggered.connect(lambda: playGeigerClick())

            develCounterAction = QAction("Play Geiger Counter", self)
            develCounterAction.triggered.connect(lambda: playGeigerCounter())

            develSineAction = QAction("Play Sine Scale", self)
            develSineAction.triggered.connect(lambda: playSineScale())

            develLogClickAction = QAction("Toggle Click Sound for Log Calls", self)
            develLogClickAction.triggered.connect(lambda: self.toggleLogClick())

            # SaveRepairLogAction = QAction('Repair DateTime and Save Data into *.log file (CSV)', self)
            # addMenuTip(SaveRepairLogAction, "Repair all records from current log and save into a CSV file with extension 'log'")
            # SaveRepairLogAction.triggered.connect(lambda: gsup_sql.saveRepairData("Log", full= True))

            # SaveRepairHisAction = QAction('Repair DateTime and Save Data into *.his file (CSV)', self)
            # addMenuTip(SaveRepairHisAction, "Repair all records from current log and save into a CSV file with extension 'his'")
            # SaveRepairHisAction.triggered.connect(lambda: gsup_sql.saveRepairData("His", full= True))

            develAudioAction = QAction("Show Audio Signal", self)
            develAudioAction.triggered.connect(lambda: gdev_audio.showLiveAudioSignal())

            develFixAudioAction = QAction("Fix garbled audio", self)
            develFixAudioAction.triggered.connect(lambda: fixGarbledAudio())

            develCRC8Action = QAction("Show CRC8 result", self)
            develCRC8Action.triggered.connect(lambda: showResultCRC8())

            develColorAction = QAction("Print color codes to Terminal", self)
            develColorAction.triggered.connect(lambda: printColorCodesToTerminal())


            # MonitorAction = QAction('Show Monitor', self)
            # addMenuTip(MonitorAction, 'Show a Monitor ')
            # MonitorAction.triggered.connect(lambda: gsup_tools.plotMonitor())

            # pggraphAction = QAction('Show PgGraph', self)
            # addMenuTip(pggraphAction, 'Show a pg graph comparison ')
            # pggraphAction.triggered.connect(lambda: gsup_tools.plotpgGraph())


            develMenu = self.menubar.addMenu('D&evel')
            develMenu.setToolTipsVisible(True)

            # develMenu.addAction(showOptionsAction)
            develMenu.addAction(changeOptionsAction)
            develMenu.addAction(showSystemInfoAction)

            develMenu.addSeparator()
            develMenu.addAction(develIotaAction)
            develMenu.addAction(develAlphaAction)
            develMenu.addAction(develBetaAction)
            develMenu.addAction(develGammaAction)
            develMenu.addAction(develBipAction)
            develMenu.addAction(develBurpAction)
            develMenu.addAction(develSineAction)
            develMenu.addAction(develClickAction)
            develMenu.addAction(develCounterAction)
            # develMenu.addAction(SaveRepairLogAction)
            # develMenu.addAction(SaveRepairHisAction)

            if "gdev_audio" in sys.modules:
                develMenu.addAction(develAudioAction)
            # develMenu.addAction(develLogClickAction)  # inactive
            # develMenu.addAction(MonitorAction)
            # develMenu.addAction(pggraphAction)

            if "LINUX" in platform.platform().upper():
                develMenu.addAction(develFixAudioAction)

            develMenu.addAction(develCRC8Action)
            develMenu.addAction(develColorAction)


# add navigation toolbar as last toolbar
        self.addToolBar(self.navtoolbar)

# DataOptions
# row Data
        BigButtonWidth  = 110
        PlotButtonWidth = 50
        col0width       = 70

    # col 0
        # labels and entry fields
        dltitle  = QLabel("Data")
        dltitle.setFont(self.fatfont)
        dlDevice  = QLabel("Device")
        dlDevice.setFont(self.fatfont)

    # col 1
        dbtnPlotLog =  QPushButton('Plot Log')
        dbtnPlotLog.setFixedWidth(col0width)
        dbtnPlotLog.setToolTip("Plot the Log File with Default settings")
        dbtnPlotLog.clicked.connect(lambda: self.plotGraph('Log', full=False))

        dbtnPlotHis =  QPushButton('Plot Hist')
        dbtnPlotHis.setFixedWidth(col0width)
        dbtnPlotHis.setToolTip("Plot the History File with Default settings")
        dbtnPlotHis.clicked.connect(lambda: self.plotGraph('His', full=False))

    # col 2, 3, 4
        self.dcfLog=QLineEdit()
        self.dcfLog.setReadOnly(True)
        self.dcfLog.setStyleSheet("QLineEdit { background-color: #DFDEDD; color: rgb(80,80,80); }")
        self.dcfLog.setToolTip('The full path of the Log-File if any is loaded')
        # self.dcfLog.setMinimumWidth(450)

        self.dcfHis=QLineEdit()
        self.dcfHis.setReadOnly(True)
        self.dcfHis.setStyleSheet("QLineEdit { background-color : #DFDEDD; color : rgb(80,80,80); }")
        self.dcfHis.setToolTip('The full path of the History-File if any is loaded')
        # self.dcfHis.setMinimumWidth(450)

    # col 5
        # vertical line

    # col 6
        # Geiger Tubes
        self.dtube  = QPushButton("Geiger Tubes")
        self.dtube.setToolTip("Set sensitivities for all Geiger tubes temporarily")
        self.dtube.setFixedWidth(BigButtonWidth)
        self.dtube.clicked.connect(self.setTemporaryTubeSensitivities)

        # button: Mapping
        self.btnMapping = QPushButton('Dev Mapping')
        self.btnMapping.setFixedWidth(BigButtonWidth)
        self.btnMapping.setEnabled(True)
        self.btnMapping.setToolTip('Show Device Mappings')
        self.btnMapping.clicked.connect(lambda: self.showDeviceMappings())


# Row Data
        DataButtonWidth = BigButtonWidth + 35

    # button: add comment
        self.btnAddComment = QPushButton('Add Comment')
        self.btnAddComment.setFixedWidth(DataButtonWidth)
        self.btnAddComment.setEnabled(False)
        self.btnAddComment.setToolTip('Add a comment to current database file')
        self.btnAddComment.clicked.connect(lambda: self.addComment("Current"))
#xyc
    # button: clear log file
        self.btnClearLogfile = QPushButton('Clear Log File')
        self.btnClearLogfile.setFixedWidth(DataButtonWidth)
        self.btnClearLogfile.setEnabled(False)
        self.btnClearLogfile.setToolTip('Set the log file to empty state')
        self.btnClearLogfile.clicked.connect(lambda: self.clearLogfile())

    # button: Log Cycle
        self.btnSetCycle = QPushButton()
        self.btnSetCycle.setFixedWidth(DataButtonWidth)
        self.btnSetCycle.setToolTip('Current setting of log cycle in seconds')
        self.btnSetCycle.setStyleSheet("QPushButton {}")
        self.btnSetCycle.clicked.connect(self.setLogCycle)

    # H layout for comment and logcycle
        DataLayout = QHBoxLayout()
        if gglobs.devel: DataLayout.addWidget(self.btnClearLogfile)
        DataLayout.addWidget(self.btnAddComment)
        DataLayout.addWidget(self.btnSetCycle)

# Row Notepad
        NPButtonWidth = 65

    # header
        dlnotepad = QLabel("NotePad")
        dlnotepad.setFixedWidth(col0width)
        dlnotepad.setFont(self.fatfont)


    # button: print notepad to printer / pdf
        self.btnPrint2Printer = QPushButton('Print')
        self.btnPrint2Printer.clicked.connect(lambda: self.printNotePad())
        self.btnPrint2Printer.setToolTip("Print Content of NotePad to Printer or  PDF-File")
        self.btnPrint2Printer.setFixedWidth(NPButtonWidth)

    # button: save notepad to file
        self.btnSaveNotePad = QPushButton('Save')
        self.btnSaveNotePad.clicked.connect(lambda: self.saveNotePad())
        self.btnSaveNotePad.setToolTip("Save Content of NotePad as Text File named <current filename>.notes")
        self.btnSaveNotePad.setFixedWidth(NPButtonWidth)

    # button: search notepad
        self.btnSearchNotePad = QPushButton("Search")
        self.btnSearchNotePad.clicked.connect(lambda: self.searchNotePad())
        self.btnSearchNotePad.setToolTip("Search NotePad for Occurence of a Text (Shortcut: CTRL-F)")
        self.btnSearchNotePad.setFixedWidth(NPButtonWidth)

    # button: print plot data
        self.btnPrintPlotData = QPushButton('Data Plt')
        self.btnPrintPlotData.setFixedWidth(NPButtonWidth)
        self.btnPrintPlotData.setToolTip("Print variables as in the current plot to the Notepad")
        self.btnPrintPlotData.clicked.connect(lambda: self.showData("PlotData"))

    # button: print full data to notepad
        self.btnPrintFullData = QPushButton('Data')
        self.btnPrintFullData.clicked.connect(lambda: self.showData(full=True))
        self.btnPrintFullData.setToolTip('Print Full Log or His Data to the NotePad')
        self.btnPrintFullData.setFixedWidth(NPButtonWidth)

    # button: print data excerpt to notepad
        self.btnPrintExceptData = QPushButton('Data Exc')
        self.btnPrintExceptData.clicked.connect(lambda: self.showData(full=False))
        self.btnPrintExceptData.setToolTip('Print Excerpt of Log or His Data to the NotePad')
        self.btnPrintExceptData.setFixedWidth(NPButtonWidth)

    # button: clear notepad
        clearbutton = QPushButton('Clear')
        clearbutton.clicked.connect(self.clearNotePad)
        clearbutton.setToolTip('Delete all content of the NotePad')
        clearbutton.setFixedWidth(BigButtonWidth)

        NPLayout = QHBoxLayout()
        NPLayout.addStretch()
        NPLayout.addWidget(self.btnPrint2Printer)
        NPLayout.addWidget(self.btnSaveNotePad)
        NPLayout.addWidget(self.btnSearchNotePad)
        NPLayout.addWidget(self.btnPrintFullData)
        NPLayout.addWidget(self.btnPrintPlotData)
        NPLayout.addWidget(self.btnPrintExceptData)
        NPLayout.addStretch()
        NPLayout.addWidget(clearbutton)

    # separator lines - vertical / horizontal
        vlinedB0 = QFrame()
        vlinedB0.setFrameShape(QFrame.VLine)
        hlinedB1 = QFrame()
        hlinedB1.setFrameShape(QFrame.HLine)

    # layout the Data Options
        dataOptions=QGridLayout()
        dataOptions.setContentsMargins(5,5,5,5) #spacing around the data options

        dataOptions.setRowStretch    (4, 1)
        dataOptions.setColumnStretch (0, 0)
        dataOptions.setColumnStretch (1, 10000)
        dataOptions.setColumnStretch (2, 10000)
        dataOptions.setColumnStretch (3, 10000)
        dataOptions.setColumnStretch (4, 0)
        dataOptions.setColumnStretch (5, 0)

        dataOptions.setColumnMinimumWidth(1, 140)
        dataOptions.setColumnMinimumWidth(2, 140)
        dataOptions.setColumnMinimumWidth(3, 140)

        row = 0
        dataOptions.addWidget(dltitle,                 row, 0)

        dataOptions.addLayout(DataLayout,              row, 1, 1, 3)
        dataOptions.addWidget(vlinedB0,                row, 4, 3, 1)
        dataOptions.addWidget(dlDevice,                row, 5)

        row = 1 # Log
        dataOptions.addWidget(dbtnPlotLog,             row, 0)
        dataOptions.addWidget(self.dcfLog,             row, 1, 1, 3)
        # col 5 is empty (vline)
        dataOptions.addWidget(self.btnMapping,         row, 5)

        row = 2 # History
        dataOptions.addWidget(dbtnPlotHis,             row, 0)
        dataOptions.addWidget(self.dcfHis,             row, 1, 1, 3)
        # col 5 is empty (vline)
        dataOptions.addWidget(self.dtube,              row, 5)

        row = 3 # hline
        dataOptions.addWidget(hlinedB1,                row, 0, 1, 6)

        row = 4 # NotePad
        dataOptions.addWidget(dlnotepad,               row, 0)
        dataOptions.addLayout(NPLayout,                row, 1, 1, 5)

        # group Data Options into Groupbox
        dataOptionsGroup = QGroupBox()
        dataOptionsGroup.setContentsMargins(0,0,0,0)
        dataOptionsGroup.setStyleSheet("QGroupBox {border-style:solid; border-width:1px; border-color:silver;}")
        dataOptionsGroup.setLayout(dataOptions)
        dataOptionsGroup.setFixedHeight(155)  # to match height with graph options (needed here: 143)
        # dataOptionsGroup.setStyleSheet("background-color:%s;" % "#FaFF00") # macht alles gelb


# GraphOptions
        ltitle  = QLabel("Graph")
        ltitle.setFont(self.fatfont)

        lmin    = QLabel("Min")
        lmin.setAlignment(Qt.AlignCenter)

        lmax    = QLabel("Max")
        lmax.setAlignment(Qt.AlignCenter)

        lcounts = QLabel("Counter")
        ly2     = QLabel("Ambient")
        ltime   = QLabel("Time")

        self.ymin = QLineEdit()
        self.ymin.setToolTip('Minimum setting for Counter axis')

        self.ymax = QLineEdit()
        self.ymax.setToolTip('Maximum setting for Counter axis')

        self.y2min=QLineEdit()
        self.y2min.setToolTip('Minimum setting for Ambient axis')

        self.y2max=QLineEdit()
        self.y2max.setToolTip('Maximum setting for Ambient axis')

        self.xmin=QLineEdit()
        self.xmin.setToolTip('The minimum (left) limit of the time to be shown. Enter manuallly or by left-mouse-click on the graph')

        self.xmax=QLineEdit()
        self.xmax.setToolTip('The maximum (right) limit of the time to be shown. Enter manuallly or by right-mouse-click on the graph')

    # col 3:
        col3width = 75

        self.btnClear = QPushButton('Clear')
        self.btnClear.setFixedWidth(col3width)
        self.btnClear.setToolTip("Clear the Graph Limit Options to Default conditions")
        self.btnClear.clicked.connect(self.clearGraphLimits)

        self.yunit = QComboBox()
        self.yunit.addItems(["CPM", "µSv/h"])
        self.yunit.setMaximumWidth(col3width)
        self.yunit.setToolTip('Select the Count Unit for the plot')
        self.yunit.currentIndexChanged.connect(self.changedGraphCountUnit)

        self.y2unit = QComboBox()
        self.y2unit.addItems(["°C", "°F"])
        self.y2unit.setMaximumWidth(col3width)
        self.y2unit.setToolTip('Select the Temperature Unit')
        self.y2unit.currentIndexChanged.connect(self.changedGraphTemperatureUnit)

        self.xunit = QComboBox()
        self.xunit.addItems(["Time", "auto", "second", "minute", "hour", "day", "week", "month"])
        self.xunit.setMaximumWidth(col3width)
        self.xunit.currentIndexChanged.connect(self.changedGraphTimeUnit)
        self.xunit.setToolTip('The time axis to be shown as Time-of-Day (Time) or time since first record in seconds, minutes, hours, days, weeks, months;\nauto selects most appropriate period')

    # col 4:
        col4width = 50

        btnReset  = QPushButton('Reset')
        btnReset.setFixedWidth(col4width)
        btnReset.setToolTip("Reset all Graph Options to Default conditions")
        btnReset.clicked.connect(lambda: self.reset_replotGraph(full=True))

        btnSetScaling =  QPushButton('Scale')
        btnSetScaling.setFixedWidth(col4width)
        btnSetScaling.setToolTip("Scaling - View and edit current settings for value- and graph-scaling")
        btnSetScaling.clicked.connect(self.editScaling)

        btnSaveFig =  QPushButton('Save')
        btnSaveFig.setFixedWidth(col4width)
        btnSaveFig.setToolTip("Save graph to file")
        btnSaveFig.clicked.connect(saveGraphToFile)

        btnApplyGraph = QPushButton('Apply')
        btnApplyGraph.setFixedWidth(col4width)
        btnApplyGraph.setToolTip("Apply the Graph Options and replot")
        btnApplyGraph.setStyleSheet("background-color: lightblue")
        btnApplyGraph.setDefault(True)
        btnApplyGraph.clicked.connect(self.applyGraphOptions)

    # col 5: vertical line

    # col 6:
        col6width = 80

        # The drop-down selector for selected variable
        self.select = QComboBox()
        self.select.setToolTip('The data to be selected for handling')
        self.select.setMaximumWidth(col6width)
        self.select.setMinimumWidth(col6width)
        self.select.setEnabled(False)
        self.select.currentIndexChanged.connect(self.changedGraphSelectedVariable)
        self.select.setMaxVisibleItems(12)
        for vname in gglobs.varsCopy:
            self.select.addItems([vname])

        # The checkboxes to select the displayed variables
        self.varDisplayCheckbox = {}
        for vname in gglobs.varsCopy:
            vshort = gglobs.varsCopy[vname][1]
            vlong  = gglobs.varsCopy[vname][0]

            self.varDisplayCheckbox[vname] = QCheckBox    (vshort)
            self.varDisplayCheckbox[vname].setToolTip     (vlong)
            self.varDisplayCheckbox[vname].setChecked     (False)
            self.varDisplayCheckbox[vname].setEnabled     (False)
            self.varDisplayCheckbox[vname].setTristate    (False)

            # "double lambda needed for closure" WTF???
            self.varDisplayCheckbox[vname].stateChanged.connect((lambda x: lambda: self.changedGraphDisplayCheckboxes(x))(vname))

        chk_width = 20

        self.mavbox = QCheckBox("MvAvg  s:")
        # self.mavbox.setLayoutDirection(Qt.RightToLeft)
        self.mavbox.setLayoutDirection(Qt.LeftToRight)
        self.mavbox.setChecked(gglobs.mavChecked)
        self.mavbox.setMaximumWidth(col6width)
        self.mavbox.setTristate (False)
        self.mavbox.setToolTip('If checked a Moving Average line will be drawn')
        self.mavbox.stateChanged.connect(self.changedGraphOptionsMav)

        self.avgbox = QCheckBox("Avg")
        # self.avgbox.setLayoutDirection(Qt.RightToLeft)
        self.avgbox.setLayoutDirection(Qt.LeftToRight)
        self.avgbox.setMaximumWidth(col6width)
        self.avgbox.setChecked(gglobs.avgChecked)
        self.avgbox.setTristate (False)
        self.avgbox.setToolTip("If checked, Average and ±95% lines will be shown")
        self.avgbox.stateChanged.connect(self.changedGraphOptionsAvg)

    # col 7:
        col7width = 55

        # this starts in col 6 and extends to col 7
        self.labelSelVar = QLabel("---")
        self.labelSelVar.setToolTip("Shows the last value of the Selected Variable when logging\nClick to show all values in separate window")
        self.labelSelVar.setMinimumWidth(col6width + col7width)
        self.labelSelVar.setFont(QFont('sans', 12, QFont.Bold))
        self.labelSelVar.setStyleSheet('color:darkgray;')
        self.labelSelVar.setAlignment(Qt.AlignCenter)
        self.labelSelVar.mousePressEvent=(lambda x: gsup_tools.displayLastValues())


        # color select button
        self.btnColorText = "Color of selected variable; click to change it. Current color:  "
        self.btnColor     = ClickLabel('Color')
        self.btnColor       .setAlignment(Qt.AlignCenter)
        self.btnColor       .setMaximumWidth(col7width)
        self.btnColor       .setMinimumWidth(col7width)
        self.btnColor       .setStyleSheet("QLabel { border: 1px solid silver;  border-radius: 3px; }")
        addMenuTip(self.btnColor, self.btnColorText + "None")

        self.mav=QLineEdit()
        self.mav.setMinimumWidth(col7width)
        self.mav.setMaximumWidth(col7width)
        self.mav.setToolTip('Enter the Moving Average smoothing period in seconds')
        self.mav.setText("{:0.0f}".format(gglobs.mav_initial))
        self.mav.textChanged.connect(self.changedGraphOptionsMavText)

        self.fitbox = QCheckBox("LinFit")
        # self.fitbox.setLayoutDirection(Qt.RightToLeft)
        self.fitbox.setLayoutDirection(Qt.LeftToRight)
        self.fitbox.setMaximumWidth(col7width)
        self.fitbox.setChecked(gglobs.fitChecked)
        self.fitbox.setTristate (False)
        self.fitbox.setToolTip("A Linear Regression will be applied to the Selected Variable and shown")
        self.fitbox.stateChanged.connect(self.changedGraphOptionsLinFit)

    # col 9:

        # col9width = 60
        col9width = 50

        # SuSt
        btnQuickStats =  QPushButton('SuSt')
        btnQuickStats.setFixedWidth(col9width)
        btnQuickStats.setToolTip("Shows Summary Statistics of variables and data as in the current plot")
        btnQuickStats.clicked.connect(lambda: gsup_tools.fprintSuSt())

        # Stats
        btnPlotStats =  QPushButton('Stats')
        btnPlotStats.setFixedWidth(col9width)
        btnPlotStats.setToolTip("Shows Detailed Statistics of variables and data as in the current plot")
        btnPlotStats.clicked.connect(lambda: gsup_tools.showStats())

        # Scatterplot
        btnScat =  QPushButton('Scat')
        btnScat.setToolTip('Show an X-Y Scatter plot with optional polynomial fit, using data currently selected in the plot')
        btnScat.setFixedWidth(col9width)
        btnScat.clicked.connect(lambda: gsup_tools.selectScatterPlotVars())

        # Poiss
        btnPoisson =  QPushButton('Poiss')
        btnPoisson.setFixedWidth(col9width)
        btnPoisson.setToolTip("Shows a plot of a Poisson curve on a histogram of the selected variable data as in the current plot")
        btnPoisson.clicked.connect(lambda: gstat_poisson.plotPoisson())

        # FFT
        btnFFT =  QPushButton('FFT')
        btnFFT.setFixedWidth(col9width)
        btnFFT.setToolTip("Show a plot of FFT spectra & Autocorrelation of the selected variable data as in the current plot")
        btnFFT.clicked.connect(lambda: gstat_fft.plotFFT())

    # separator lines
        vlineA0 = QFrame()
        vlineA0.setFrameShape(QFrame.VLine)

        vlineC0 = QFrame()
        vlineC0.setFrameShape(QFrame.VLine)

    # OFF / ON button
        btn_width = 35
        btnOFF = QPushButton('OFF')
        btnOFF .setToolTip("Uncheck all variables")
        btnOFF .clicked.connect(lambda: self.setPlotVarsOnOff("OFF"))
        btnOFF .setMaximumWidth(btn_width)

        btnON  = QPushButton('ON')
        btnON  .setToolTip("Check all avialable variables")
        btnON  .clicked.connect(lambda: self.setPlotVarsOnOff("ON"))
        btnON  .setMaximumWidth(btn_width)

    # layout of variables check boxes with OFF / ON button
        layoutH = QHBoxLayout()
        layoutH.addWidget(btnOFF)
        layoutH.addWidget(btnON)
        for vname in gglobs.varsCopy:
            layoutH.addWidget(self.varDisplayCheckbox[vname])

    #layout the GraphOptions
        graphOptions=QGridLayout()
        graphOptions.setContentsMargins(5,9,5,5) # spacing around the graph options top=9 is adjusted for fit!

        # STEPPING ORDER ##############################
        # to define the order of stepping through by tab-key
        # row 1 .. 3, col 1 + 2 is put in front
        row = 1
        graphOptions.addWidget(self.ymin,       row, 1)
        graphOptions.addWidget(self.ymax,       row, 2)
        row = 2
        graphOptions.addWidget(self.y2min,      row, 1)
        graphOptions.addWidget(self.y2max,      row, 2)
        row = 3
        graphOptions.addWidget(self.xmin,       row, 1)
        graphOptions.addWidget(self.xmax,       row, 2)
        # stepping end ###############################

        row = 0
        graphOptions.addWidget(ltitle,          row, 0)
        graphOptions.addWidget(lmin,            row, 1)
        graphOptions.addWidget(lmax,            row, 2)
        graphOptions.addWidget(self.btnClear,   row, 3)
        graphOptions.addWidget(btnReset,        row, 4)
        graphOptions.addWidget(vlineA0,         row, 5, 4, 1)
        graphOptions.addWidget(self.select,     row, 6)
        graphOptions.addWidget(self.btnColor,   row, 7)
        graphOptions.addWidget(vlineC0,         row, 8, 5, 1) # vertical line across all 6 rows
        graphOptions.addWidget(btnQuickStats,   row, 9)

        row = 1
        graphOptions.addWidget(lcounts,         row, 0)
        # see stepping order
        # see stepping order
        graphOptions.addWidget(self.yunit,      row, 3)
        graphOptions.addWidget(btnSetScaling,   row, 4)
        # col 5 is empty (vert line)
        graphOptions.addWidget(self.mavbox,     row, 6)
        graphOptions.addWidget(self.mav,        row, 7)
        # col 8 is empty (vert line)
        graphOptions.addWidget(btnPlotStats,    row, 9)

        row = 2
        graphOptions.addWidget(ly2,             row, 0)
        # see stepping order
        # see stepping order
        graphOptions.addWidget(self.y2unit,     row, 3)
        graphOptions.addWidget(btnSaveFig,      row, 4)

        # col 5 is empty (vert line)
        graphOptions.addWidget(self.avgbox,     row, 6)
        graphOptions.addWidget(self.fitbox,     row, 7)
        # col 8 is empty (vert line)
        graphOptions.addWidget(btnScat,         row, 9)

        row = 3
        graphOptions.addWidget(ltime,           row, 0)
        # see stepping order
        # see stepping order
        graphOptions.addWidget(self.xunit,      row, 3)
        graphOptions.addWidget(btnApplyGraph,   row, 4)
        # col 5 is empty (vert line)
        graphOptions.addWidget(self.labelSelVar,   row, 6, 1, 2)
        # col 7 is empty
        # col 8 is empty (vert line)
        graphOptions.addWidget(btnPoisson,      row, 9)

        row = 4
        graphOptions.addLayout(layoutH,         row, 0, 1, 8)
        graphOptions.addWidget(btnFFT,          row, 9)


    # group Graph Options into Groupbox
        graphOptionsGroup = QGroupBox()
        graphOptionsGroup.setContentsMargins(0,0,0,0)
        graphOptionsGroup.setStyleSheet("QGroupBox {border-style: solid; border-width: 1px; border-color: silver;}")
        # graphOptionsGroup.setStyleSheet("background-color:%s;" % "#FaFF00")
        graphOptionsGroup.setLayout(graphOptions)
        graphOptionsGroup.setFixedHeight(155)  # min height needed

# NotePad
        self.notePad = QTextEdit()
        self.notePad.setReadOnly(True)
        self.notePad.setFont(self.fontstd)
        self.notePad.setLineWrapMode(QTextEdit.NoWrap)          # alt: QTextOption::WordWrap
        self.notePad.setTextColor(QColor(40, 40, 40))
        # self.notePad.setStyleSheet("background-color:%s;" % "#FaFF00")

        gglobs.notePad = self.notePad # pointer used for fprint in utils

# LogPad
        # limit the amount of text stored in the logPad.
        # clear + append is MUCH faster than setText or setPlainText !!! (5000 ms vs 200 ms)
        # Character count: 5 + 8 + 7 * 12 = 97 round up to 100 per line
        # 100char/sec * 3600sec/h = 360 000 per h ==> 1 mio in 2.8h = ~3h
        # 10000 char / 100char/sec ==> 100 sec, ~2min
        # in overnight run the limit was done some 600 times; maximum duration was 0.237 sec!
        #
        # oldlptext = gglobs.logPad.toPlainText()
        # lenOld    = len(oldlptext)
        # lpmax     = 1e5                                       # max no of chars in logPad
        # if lenOld > lpmax:
        #     lpshort   = oldlptext[-int(lpmax - 10000):]       # exclude first 10000+ chars
        #     LFindex   = lpshort.find("\n")                    # find position of first LF in remaining text
        #     newlptext = lpshort[LFindex + 1:]
        #     lenNew    = len(newlptext)
        #     Delta     = lenOld - lenNew
        #     self.logPad.clear()
        #     gglobs.logPad.append(newlptext)                   # append shortened text to logPad
        # this is all replaced by:  self.logPad.document().setMaximumBlockCount(33)

        self.logHeader = QLabel()
        self.logHeader.setFont(self.fontstd)
        # self.logHeader.setStyleSheet("background-color: %s; padding-left: 3 px;" % "#f0f0f0")
        self.logHeader.setStyleSheet("background-color: {}; padding-left: 3 px;".format("#f0f0f0"))
        self.logHeader.setMaximumHeight(25)                     # single line only

        gglobs.LogHeaderText = "{:<11s} ".format("Time")
        hlist = "M,S,M1,S1,M2,S2,M3,S3"
        for a in hlist.split(","):  gglobs.LogHeaderText += "{:<6s}".format(a)  # 6 places
        hlist = "T,P,H,X"
        for a in hlist.split(","):  gglobs.LogHeaderText += "{:<7s}".format(a)  # 7 places
        gglobs.LogHeaderText += "  "
        self.logHeader.setText(gglobs.LogHeaderText)


        self.logPad = QTextEdit()
        self.logPad.setReadOnly(True)
        self.logPad.setFont(self.fontstd)
        self.logPad.setLineWrapMode(QTextEdit.NoWrap)
        self.logPad.setTextColor(QColor(40, 40, 40))
        self.logPad.document().setMaximumBlockCount(3600)  # Limit total output: 1 Block = 1 Zeile; at 1 sec cycle -> 3600 per hour
        # self.logPad.setStyleSheet("background-color:%s;" % "#FaFF00")

        gglobs.logPad = self.logPad # pointer used for logPrint in utils

        self.layoutLog = QVBoxLayout()
        self.layoutLog.addWidget(self.logHeader)
        self.layoutLog.addWidget(self.logPad)
        self.layoutLog.setSpacing(0)
        self.layoutLog.setContentsMargins(0,0,0,0)

        self.logCombo = QWidget()
        self.logCombo.setLayout(self.layoutLog)


# set the layout - left side
        splitterPad = QSplitter(Qt.Vertical)
        splitterPad.addWidget(self.notePad)
        splitterPad.addWidget(self.logCombo)
        splitterPad.setSizes([800, 290])

        layoutLeft = QVBoxLayout()
        layoutLeft.addWidget(dataOptionsGroup)
        layoutLeft.addWidget(splitterPad)
        layoutLeft.setContentsMargins(0,0,0,0)
        layoutLeft.setSpacing(0)

# set the layout - right side
        layoutRight = QVBoxLayout()
        layoutRight.addWidget(graphOptionsGroup)
        layoutRight.addWidget(self.canvas)          # add canvas directly, no frame
        layoutRight.setContentsMargins(0,0,0,0)
        layoutRight.setSpacing(0)

# set the layout - both
        leftWidget = QWidget()
        leftWidget.setLayout(layoutLeft)

        rightWidget = QWidget()
        rightWidget.setLayout(layoutRight)

        splitterBoth = QSplitter(Qt.Horizontal)
        splitterBoth.addWidget(leftWidget)
        splitterBoth.addWidget(rightWidget)
        splitterBoth.setSizes([800, 750])
        splitterBoth.setContentsMargins(5,0,5,0)

# centralwidget
        self.setCentralWidget(splitterBoth)

# timer for logging
# is replaced with its own thread
#         self.timer0 = QTimer()
#         self.timer0.timeout.connect(self.runLoggingCycle)

# timerCheck for checking
        self.timerCheck = QTimer()
        self.timerCheck.timeout.connect(self.runCheckCycle)     # checks various requests
        self.timerCheck.start(10)                               # time in millisec

#show
        self.dcfLog.setText(str(gglobs.logFilePath))        # default is "None" for filepath
        self.dcfHis.setText(str(gglobs.hisFilePath))        # default is "None" for filepath
        self.showTimingSetting (gglobs.logCycle)            # default is 3 (sec)

        self.show()
        if gglobs.window_size == "maximized":   self.showMaximized()

        dprint("Fonts:  App     -",     strFontInfo("", gglobs.app.font()))  # print font info for QApplication
        dprint("Fonts:  menubar -",     strFontInfo("", self.menubar.fontInfo()))
        dprint("Fonts:  logPad  -",     strFontInfo("", self.logPad.fontInfo()))
        dprint("Fonts:  notePad -",     strFontInfo("", self.notePad.fontInfo()))
        dprint("Screen: Dimensions: ",  QDesktopWidget().screenGeometry()) # gives screen dimensions
        dprint("Screen: Available:  ",  screen_available)                        # gives screen dimensions available

        # NOTE on Window sizes:
        # "On X11, a window does not have a frame until the window manager decorates it."
        # see: http://doc.qt.io/qt-4.8/application-windows.html#window-geometry
        # self.geometry(),      : gives Windows dimensions but has the frame EXCLUDED!
        # self.frameGeometry()  : gives Windows dimensions including frame, but not on X11!
        dprint("Window: Dimensions: ",  self.geometry(),      " w/o Frame")
        dprint("Window: Dimensions: ",  self.frameGeometry(), " WITH Frame (not valid on X11)")

        # copyright message
        message = __copyright__ + ", by " + __author__ + ", License: " + __license__
        self.showStatusMessage(message, timing=0, error=False) # message remains until overwritten by next

        QtUpdate()

        cdprint("Data  Options group: height: {}, width: {}".format(dataOptionsGroup.height(), dataOptionsGroup.width()))
        cdprint("Graph Options group: height: {}, width: {}".format(graphOptionsGroup.height(), graphOptionsGroup.width()))

        dprint(TGREEN + "Starting the GUI is complete " + "-" * 100 + TDEFAULT + "\n")

        # Python problems - wrong version --> EXIT
        if gglobs.python_version  > "":
            self.startupProblems(gglobs.python_version,  closeGL=True)

        # Startup problems --> EXIT
        if gglobs.startupProblems > "":
            self.startupProblems(gglobs.startupProblems, closeGL=True)

        # Config problems --> Continue
        if gglobs.configAlerts > "":
            msg  = gglobs.configAlerts.replace("\n", "<br>")
            self.startupProblems(msg,  closeGL=False)
            gglobs.configAlerts = ""

        # at least one activated device?  if not warn but continue
        ### local def #########################################
        def isAnyDeviceActive():
            for DevName in gglobs.Devices:
                if gglobs.Devices[DevName][ACTIV]: return True
            return False
        ### end local def #####################################

        if not isAnyDeviceActive():
            dprint("No Devices are Activated !")
            self.warnMissingDeviceActivations()

        # MonServer autostart
        if gglobs.MonServerAutostart:
            gweb_monserv.initMonServer(force=True)

        ## GeigerLog autostart options
        if gglobs.autoQuickStart:
            # quickstart - takes precedence
            self.switchAllConnections(new_connection = "ON")
            self.quickLog()
        else:
            # make autoLogPath
            autoLogPath = os.path.join(gglobs.dataPath, gglobs.autoLogFile)

            if gglobs.autoLogStart:
                # autoLogStart
                self.switchAllConnections(new_connection = "ON")
                self.getFileLog(defaultLogDBPath=autoLogPath)
                self.startLogging()
            else:
                if gglobs.autoDevConnect:
                    # only auto Connect
                    self.switchAllConnections(new_connection = "ON")

                if gglobs.autoLogLoad:
                    # only auto Load
                    self.getFileLog(defaultLogDBPath=autoLogPath)



    #     edprint("Screen Geometry: ", QDesktopWidget().screenGeometry())    # total hardware screen
    #     edprint("Screen Available:", QDesktopWidget().availableGeometry()) # available screen
    #     edprint("Screen as set: ", (x, y, sw, sh)  )
    #     geom             = self.geometry()
    #     geom_frame       = self.frameGeometry()
    #     edprint("Current window size:", "{}x{} including window frame (w/o frame: {}x{})".format(geom_frame.width(), geom_frame.height(), geom.width(), geom.height()))



#========== END __init__ ======================================================
#
#========== BEGIN Class Functions =============================================


    def processtrigger(self, q):
        """testing processtrigger"""

        pass
        #rdprint("'{}' was triggered".format(q.text()))

#xyz
    def runCheckCycle(self):
        """triggered by timerCheck"""

        fncname     = "runCheckCycle: "

        rCCstart    = time.time()
        msgfmt      = "{:<14s}{:7.2f} ms"

    # switch cycle button - options: "", "On", "Off"
        if gglobs.logCycleButtonFlag > "":
            self.flashCycleButton(gglobs.logCycleButtonFlag)
            gglobs.logCycleButtonFlag = ""


    # update Displays
        # 1: "Last value" of the Selected Variable in the Graph area (~0.3 ms)
        # 2: "Display Last Values" window                            (~1 ms)
        elif gglobs.needDisplayUpdate :
            gglobs.needDisplayUpdate = False

            self.updateDisplayVariableValue()

            duration    = 1000 * (time.time() - rCCstart)
            msg         = msgfmt.format("update Disp:", duration)
            cdprint(fncname + msg)


    # update LogPad
        elif len(gglobs.logLogPadDeque) > 0:
            # logHeaderText:  Time       M     S     M1    S1    M2    S2    M3    S3    T      P      H      X
            # Example:        14:25:53.4 4849  75    4829  80    .     .     4727  77    33.72  33.09  233680 0.994

            msgLogPad, logValues   = gglobs.logLogPadDeque.popleft()
            # edprint("msgLogPad: ", msgLogPad)

            # extract values for all variables
            if "No data" in msgLogPad:  # all data are NAN; msgLogPad has timestamp plus "No data"
                pass
            else:
                for i, vname in enumerate(gglobs.varsCopy):
                    if i < 8:
                        # for all CPM* and CPS* give 5 digits space
                        if logValues[vname] is None or np.isnan(logValues[vname]):
                            sval = "{:<5s}".format(".")
                        else:
                            val = logValues[vname]
                            if   isinstance(val, int) or val.is_integer():              # it is of integer value
                                if      val < 1E5:      sval = "{:<5.0f}".format(val)   # less than 100 000
                                else:                   sval = "{:<#5.3g}".format(val)  # 100 000 or greater
                            else:
                                val = round(val, 2)
                                if      val <= 0.99:    sval = "{:<#5.2g}".format(val)
                                else:                   sval = "{:<#5.3g}".format(val)
                    else:
                        # for T, P, H, X give 5 digits space + 1 extra space
                        if logValues[vname] is None or np.isnan(logValues[vname]):
                            sval = "{:<6s}".format(".")
                        else:
                            rval = round(logValues[vname], 3)
                            # edprint("val:{} rval:{}".format(val, rval))
                            if      rval <= 0.999:   sval = "{:<#6.3g}".format(rval)
                            elif    rval <  1e3:     sval = "{:<#6.4g}".format(rval)
                            elif    rval <  1E9:     sval = "{:<6.0f}" .format(rval)    # less than 1000 mio (999 999 999 = 9 digits)
                            else:                    sval = "{:<#6.4G}".format(rval)

                    msgLogPad += " {}".format(sval)

            gglobs.SnapRecord = msgLogPad               # saving in case it was called by snaprecord
            logPrint(msgLogPad)

            duration    = 1000 * (time.time() - rCCstart)
            msg         = msgfmt.format("update LogPad:", duration)
            cdprint(fncname + msg)


    # update mem
        elif len(gglobs.logMemDataDeque) > 0:
            # update 1 deque entry per loop. comes before graph, will be complete before graph update

            datalist = gglobs.logMemDataDeque.popleft()

            try:
                # update options:
                #   gglobs.logDBData = np.append       (gglobs.logDBData, [datalist],  axis=0)        # max = 10000 ms
                #   gglobs.logDBData = np.concatenate ((gglobs.logDBData, [datalist]), axis=0)        # max = 12000 ms
                #   gglobs.logDBData = np.vstack      ((gglobs.logDBData, [datalist])        )        # max =  9000 ms

                gglobs.logDBData = np.vstack ((gglobs.logDBData, [datalist]))

            except Exception as e:
                exceptPrint(e, fncname)
                efprint(longstime() + " " + fncname + str(e))

            duration   = 1000 * (time.time() - rCCstart)
            msg        = fncname + msgfmt.format("update Mem:", duration)

            if gglobs.devel:
                if duration > 500:
                    efprint("DVL {} {} {}".format(longstime(), msg, "++++++++"))

            cdprint(msg)

            gglobs.needGraphUpdate = True   # the only place where:  gglobs.needGraphUpdate = True


    # update graph
        # plot the log data but only if Log (and not His) is displayed
        elif gglobs.needGraphUpdate:
            gglobs.needGraphUpdate = False

            # from rCCstart to here: approx 5µs
            if gglobs.activeDataSource == "Log":
                # displaying Log
                gglobs.currentDBData = gglobs.logDBData      # make the log data current!
                makePlotMsg          = gsup_plot.makePlot()  # direct plot; slightly quicker than plotGraph
            else:
                # displaying His
                makePlotMsg          = "No graph update; His is displayed"

            duration  = 1000 * (time.time() - rCCstart)
            xmsg      = " "             # " --> Xtra   " if gglobs.timing else " "
            msg       = msgfmt.format("update Graph:", duration) + xmsg + str(makePlotMsg)
            cdprint(fncname + msg)


    # efprint thread message
        # cannot fprint directly when origin is in different thread (e.g. MiniMon)
        # Note: testing for empty is 3x faster than testing length > 0!
        elif gglobs.ThreadMsg > "":
            for msg in gglobs.ThreadMsg.strip().split("\n"): qefprint(msg)
            gglobs.ThreadMsg = ""


    ###### Web stuff Begin #####################################################
    # check for start-flag from web
        elif gglobs.startflag:
            gglobs.startflag = False
            if not gglobs.logging: self.startLogging()


    # check for stop-flag from web
        elif gglobs.stopflag:
            gglobs.stopflag = False
            if gglobs.logging:     self.stopLogging()


    # check for quick-flag from web
        elif gglobs.quickflag:
            gglobs.quickflag = False
            if not gglobs.logging: self.quickLog()


    # update Telegram Messenger
        # INACTIVE !!! removed when Telegram had a code change
        #
        # if gglobs.TelegramActivation:
        #     now = time.time()
        #     # print("now - gglobs.TelegramLastUpdate: ", now - gglobs.TelegramLastUpdate)
        #     if now - gglobs.TelegramLastUpdate > gglobs.TelegramUpdateCycle * 60:
        #         gglobs.TelegramLastUpdate = now
        #         updateTelegram()


    # update GMCmap
        elif gglobs.RWMmapActivation:
            if gglobs.logging:
                now = time.time()
                if gglobs.RWMmapLastUpdate is None:
                    # set the cycle time
                    gglobs.RWMmapLastUpdate = now
                else:
                    # update when RWMmapUpdateCycle expires
                    # print("now - gglobs.RWMmapLastUpdate: ", now - gglobs.RWMmapLastUpdate)
                    if now - gglobs.RWMmapLastUpdate > gglobs.RWMmapUpdateCycle * 60:
                        gglobs.RWMmapLastUpdate = now
                        gweb_radworld.updateRadWorldMap()
    ##### web stuff end ####################################################


    # check for log cycletime overrun
        # sollte nicht mehr vorkommen!?
        elif gglobs.runLogCycleDurs[2] > (gglobs.logCycle * 250) and gglobs.devel:           # 1000 * 0.25 = 250
            totalDur = gglobs.runLogCycleDurs[2] / 1000                     # totalDur = Grand Total dur in sec
            msg1     = "LogCycle "
            color    = None

            if   totalDur > gglobs.logCycle * 1.0:                          # > full cycle
                color = BOLDRED
                msg1 += "OVERRUN"

            # elif totalDur > gglobs.logCycle * 0.5:                          # > half cycle
            #     color = BOLDMAGENTA
            #     msg1 += "Half Cycle"

            if color is not None:
                msg1 += "\nDetails: Fetch: {:0.1f} ms, SaveToDB: {:0.1f} ms, Grand Total: {:0.1f} ms".format(*gglobs.runLogCycleDurs)

                efprint(stime() + " " + msg1)
                dprint(color + msg1.replace("\n", " ") + TDEFAULT)
                gglobs.runLogCycleDurs = [0, 0, 0]  # runCheckCycle would catch it multiple times with its cycle shorter than logcycle

        # print("r", end="", flush=True)
##### end runCheckCycle(self): #############################################


    def fetchLogValues(self):
        """Reads all variables from all activated devices and returns as logValues dict"""

        fncname = "fetchLogValues: "

        vprint(getLoggedValuesHeader())

        # logValues is dict, always ordered, like:
        # {'CPM':93.0,'CPS':2.0,'CPM1st':45,'CPS1st':3,'CPM2nd':0,'CPS2nd':0,'CPM3rd':nan,'CPS3rd':nan,'Temp':3.0,'Press':4.0,'Humid':5.0,'Xtra':12}
        # set all logValues items to NAN
        logValues = {}
        for vname in gglobs.varsCopy:
            logValues[vname] = gglobs.NAN   # NAN is needed later for testing

        # fetch the new values for each device (if active)
        #   gglobs.Devices keys: "GMC", "Audio", "RadMon", "AmbioMon", "GammaScout", "I2C", "LabJack", "MiniMon", ...
        #   e.g.: gglobs.Devices['GMC']   [VNAME] : ['CPM', 'CPS']              # note: VNAME == 1
        #   e.g.: gglobs.Devices['RadMon'][VNAME] : ['T', 'P', 'H', 'X']
        for DevName in gglobs.Devices:
            if gglobs.Devices[DevName][CONN]: # look only at connected devices
                devvars = gglobs.Devices[DevName][VNAME]    #  e.g. == ['CPM', 'T', 'X']
                if   DevName == "GMC"       : logValues.update(gdev_gmc         .getValuesGMC        (devvars))
                elif DevName == "Audio"     : logValues.update(gdev_audio       .getValuesAudio      (devvars))
                elif DevName == "RadMon"    : logValues.update(gdev_radmon      .getValuesRadMon     (devvars))
                elif DevName == "AmbioMon"  : logValues.update(gdev_ambiomon    .getValuesAmbioMon   (devvars))
                elif DevName == "GammaScout": logValues.update(gdev_gscout      .getValuesGammaScout (devvars))

                elif DevName == "I2C"       : logValues.update(gdev_i2c         .getValuesI2C        (devvars))
                elif DevName == "LabJack"   : logValues.update(gdev_labjack     .getValuesLabJack    (devvars))
                elif DevName == "MiniMon"   : logValues.update(gdev_minimon     .getValuesMiniMon    (devvars))
                elif DevName == "Simul"     : logValues.update(gdev_simul       .getValuesSimul      (devvars))

                elif DevName == "WiFiClient": logValues.update(gdev_wificlient  .getValuesWiFiClient (devvars))
                elif DevName == "WiFiServer": logValues.update(gdev_wifiserver  .getValuesWiFiServer (devvars))

                elif DevName == "RaspiI2C"  : logValues.update(gdev_raspii2c    .getValuesRaspiI2C   (devvars))
                elif DevName == "RaspiPulse": logValues.update(gdev_raspipulse  .getValuesRaspiPulse (devvars))

                elif DevName == "Manu"      : logValues.update(gdev_manu        .getValuesManu       (devvars))

                elif DevName == "Rad Pro"   : logValues.update(gdev_radpro      .getValuesRadPro     (devvars))

        # cdprint("logValues: ", logValues)
        return logValues


    def snapLogValue(self):
        """Take an out-of-order measurement (like when toolbar icon Snap is clicked)"""

        if not gglobs.logging: return

        fncname = "snapLogValue: "

        vprint(fncname)
        setIndent(1)

        runLogCycle() # do an extra logging cycle

        fprint(header("Snapped Log Record"))
        fprint(gglobs.LogHeaderText)
        fprint(gglobs.SnapRecord)
        dprint(fncname + gglobs.SnapRecord)

        # send comment to the DB
        ctype       = "COMMENT"
        cJulianday  = "NOW"
        cinfo       = "Snapped log record: '{}'".format(gglobs.SnapRecord)
        gsup_sql.DB_insertComments(gglobs.logConn, [[ctype, cJulianday, "localtime", cinfo]])

        setIndent(0)


#####################################################################################################

    def toggleLogClick(self):
        """toggle making a click at avery log cycle"""

        gglobs.LogClickSound = not gglobs.LogClickSound
        fprint(header("Toggle Log Click"))
        fprint("Toggle Log Click", "is ON" if gglobs.LogClickSound else "is OFF")


    def flashCycleButton(self, mode):
        """make LogCycle button yellow during a log call, and grey otherwise"""

        if mode == "On": stylesheetcode = "QPushButton {background-color:#F4D345; color:rgb(0,0,0);}" # yellow button bg, black text
        else:            stylesheetcode = "QPushButton {}"                                            # std grey button bg

        self.btnSetCycle.setStyleSheet(stylesheetcode)


    def warnMissingDeviceActivations(self):
        """Warning on no-Devices-activated"""

        message  = "<b>You have not activated any devices!</b><br><br>\
                    You can work on existing data from Log or History loaded from database or CSV file,\
                    but you cannot create new data, neither by Logging nor by History download from device, until a device is activated.\
                    <br><br>Devices are activated in GeigerLog's configuration file <b>geigerlog.cfg</b>, which you find in the GeigerLog directory.\
                    <br><br>Search in the file for the word <b>DEVICES</b>, then scroll down to find your \
                    device <b>[XYZ]</b>, and set its <b>XYZActivation = yes</b>.<br><br>\
                    <b>Example</b>: To activate a GMC counter find <b>[GMC_Device]</b> and set: <b>GMC_Activation = yes</b>.<br><br>\
                    For more see chapter 'Configuration of GeigerLog' in the GeigerLog manual.<br>"

        msg = QMessageBox()
        msg.setWindowIcon       (self.iconGeigerLog)
        msg.setWindowTitle      ("Missing Device Activation")
        msg.setIcon             (QMessageBox.Warning)
        msg.setStandardButtons  (QMessageBox.Ok)
        msg.setDefaultButton    (QMessageBox.Ok)
        msg.setEscapeButton     (QMessageBox.Ok)
        msg.setWindowModality   (Qt.WindowModal)

        msg.setText("<!doctype html>" + message)    # message must be html coded text

        playWav("err")

        msg.exec()


    def startupProblems(self, message, closeGL=True):
        """Warning on serious problems like wrong Python version, configuration file missing,
        configuration file incorrect"""

        msg = QMessageBox()
        msg.setWindowIcon(self.iconGeigerLog)
        msg.setWindowTitle("STARTUP PROBLEM")
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons  (QMessageBox.Ok)
        msg.setDefaultButton    (QMessageBox.Ok)
        msg.setEscapeButton     (QMessageBox.Ok)
        msg.setWindowModality   (Qt.WindowModal)

        # msg.setText("<!doctype html>Please, review:\n\n" + message)    # message must be html coded text
        msg.setText("<!doctype html>" + message)    # message must be html coded text

        playWav("err")

        msg.exec()

        if closeGL:
            self.close() # End GeigerLog; may not result in exit, needs sys.exit()
            sys.exit(1)


    def showIPStatus(self):

        fncname = "showIPStatus"
        # dprint(fncname)

    # GeigerLog's IP Address
        lglip = QLabel("GeigerLog's IP Address:")
        lglip.setMinimumWidth(200)

        IPfont = QFont()
        IPfont.setPixelSize(30)

        glip  = QLabel()
        glip.setToolTip('IP Address of computer running GeigerLog')
        glip.setFont(IPfont)
        glip.setText(getGeigerLogIP())

    # Monitor Server
        lmonserve = QLabel("GeigerLog's Monitor Server:")
        lmonserve.setAlignment(Qt.AlignLeft)

        monserve = QLabel()
        monserve.setToolTip('Monitor Server:   IP:Port')
        if gglobs.MonServerSSL: ssl = "https://"
        else:                   ssl = "http://"
        monserve.setText("{}{} : {}".format(ssl, gglobs.GeigerLogIP, gglobs.MonServerPort))

    # WiFiClient Server
        if gglobs.Devices["WiFiClient"][ACTIV]:
            lwific = QLabel("GeigerLog's WiFiClient Server:")
            lwific.setAlignment(Qt.AlignLeft)

            wific = QLabel()
            wific.setToolTip('WiFiClient Server:   IP:Port')
            ssl = "http://"
            wific.setText("{}{} : {}".format(ssl, gglobs.GeigerLogIP, gglobs.WiFiClientPort))
        else:
            lwific = QLabel("")
            wific  = QLabel("")

        ipoptions=QGridLayout()
        ipoptions.addWidget(lglip,                          0, 0)
        ipoptions.addWidget(glip,                           0, 1)
        ipoptions.addWidget(QLabel(""),                     1, 0)
        ipoptions.addWidget(QLabel("        IP Address :   Port"),    2, 1)
        ipoptions.addWidget(lmonserve,                      3, 0)               # MonServer
        ipoptions.addWidget(monserve,                       3, 1)
        ipoptions.addWidget(lwific,                         4, 0)               # WiFiClient
        ipoptions.addWidget(wific,                          4, 1)
        ipoptions.addWidget(QLabel(""),                     6, 1)

    # Dialog box
        d = QDialog() # set parent empty to popup in center of screen
        d.setWindowIcon(self.iconGeigerLog)
        d.setWindowTitle("Show IP Status")
        d.setWindowModality(Qt.WindowModal)

    # Buttons
        self.bbox = QDialogButtonBox()
        self.bbox.setStandardButtons(QDialogButtonBox.Ok)
        self.bbox.accepted.connect(lambda: d.done(100))

    # VLayout to d
        layoutV = QVBoxLayout(d)
        layoutV.addLayout(ipoptions)
        layoutV.addWidget(self.bbox)

        d.exec()


    def searchNotePad(self):
        """Search Content of NotePad for occurence of text"""

        fncname = "searchNotePad: "

        qid = QInputDialog()
        stxt, ok = qid.getText(None, 'Search NotePad', 'Search Text:' + ' ' * 35, text=gglobs.notePadSearchText)
        if not ok: return

        gglobs.notePadSearchText = stxt
        # cdprint(fncname + "stxt = '{}'".format(stxt), type(stxt))

        flag  = QTextDocument.FindBackward            # flag to search backwards
        found = self.notePad.find(stxt, flag)
        if found:  return
        else: # not found
            # set cursor to end and try again
            self.notePad.moveCursor(QTextCursor.End)
            found = self.notePad.find(stxt, flag)
            if found or stxt == "": return

        self.showStatusMessage("Search NotePad Content: Text '{}' not found".format(stxt))


    def saveNotePad(self):
        """Save Content of NotePad to file"""

        fncname = "saveNotePad: "

        nptxt = self.notePad.toPlainText()  # Saving as Plain Text; all is B&W, no colors
        #nptxt = self.notePad.toHtml()      # Saving in HTML Format; preserves color
        #print("nptxt:", nptxt)

        if gglobs.currentDBPath is None:
            newFile = defaultFile = os.path.join(gglobs.dataPath, "notepad.notes")
        else:
            newFile = gglobs.currentDBPath + '.notes'

        fprint(header("Saving NotePad Content"))
        fprint("to File: {}\n".format(newFile))

        try:
            with open(newFile, 'a') as f:
                f.write(nptxt)
        except Exception as e:
            exceptPrint(e, fncname + "save nptxt")


#exit GeigerLog
    def closeEvent(self, event):
        """is called via self.close! Allow to Exit unless Logging is active"""
        # Qt event: QEvent.Close = 19 : Widget was closed

        fncname = "closeEvent: "

        setBusyCursor()

        dprint("closeEvent: event type: {}".format(event.type()))
        setIndent(1)

        if gglobs.logging :
            event.ignore()
            msg = "Cannot exit when logging! Stop logging first"
            self.showStatusMessage(msg)
            dprint(fncname + "ignored; " + msg)

        else:
            event.accept()                           # allow closing the window
            dprint(fncname + "accepted")

            # terminate threads
            gweb_monserv.terminateMonServer()

            # terminate all connected devices
            for DevName in gglobs.Devices:
                # print(fncname + "DevName: {:10s},  Connection: {}".format(DevName, gglobs.Devices[DevName][CONN]))
                if gglobs.Devices[DevName][CONN] :  self.terminateDevice(DevName)

            # close the databases for Log and His
            gsup_sql.DB_closeDatabase("Log")
            gsup_sql.DB_closeDatabase("His")

            dprint(fncname + "exiting now")

            # Force Exit
            # The standard way to exit is sys.exit(n). sys.exit() is identical to
            # raise SystemExit(). It raises a Python exception which may be caught
            # by the caller.
            # os._exit calls the C function _exit() which does an immediate program
            # termination. Note the statement "can never return".
            sys.exit(0) # otherwise sub windows won't close

        setIndent(0)
        setNormalCursor()


#GraphOptions

    def changedGraphSelectedVariable(self):
        """called from the select combo for variables"""

        self.applyGraphOptions()


    def changedGraphDisplayCheckboxes(self, vname):
        """Graph varDisplayCheckbox vname has changed"""

        if not gglobs.allowGraphUpdate: return

        fncname  = "changedGraphDisplayCheckboxes: "
        oldIndex = self.select.currentIndex() # index of dropdown box selected variable
        index    = self.select.findText(vname)
        vIsChkd  = self.varDisplayCheckbox[vname].isChecked()
        # gdprint(fncname + "var:{}, longname:{}, index:{} status Chk:{}".format(vname, vname, index, vIsChkd))

        if gglobs.activeDataSource == "Log" : gglobs.varChecked4PlotLog[vname] = vIsChkd
        else:                                 gglobs.varChecked4PlotHis[vname] = vIsChkd
        # gdprint("varChecked4PlotLog", getEasyDictPrint(gglobs.varChecked4PlotLog))

        if vIsChkd:
            # sets and enables the select combobox to the checked variable
            # thus making it to the selected variable
            self.select.model().item(index) .setEnabled(True)
            self.select                     .setCurrentIndex(index)

        else:
            # disables the unchecked variable on the select combobox,
            # and sets combobox to the first enabled entry. If none found then CPM is selected
            self.select.model().item(index) .setEnabled(False)
            foundSelVar = 0
            for i, vname in enumerate(gglobs.varsCopy):
                #print("i, vname, self.select.model().item(i) .isEnabled():", i, vname, self.select.model().item(i) .isEnabled())
                if self.select.model().item(i) .isEnabled():
                    foundSelVar = i
                    break
            if self.select.currentIndex() == index:
                self.select.setCurrentIndex(foundSelVar)

        #print("----self.select.model().item(index).isEnabled:", self.select.model().item(index).isEnabled())

        # if the index is not changed, then an explicit update is needed; otherwise
        # a changed index results in an update anyway via changedGraphSelectedVariable
        if self.select.currentIndex() == oldIndex:
            self.applyGraphOptions()


    def changedGraphOptionsMav(self, i):
        """Graph Option Mav checkbox check-status has changed"""

        #print("changedGraphOptionsMav: i:", i)
        gglobs.mavChecked  = self.mavbox.isChecked()

        self.applyGraphOptions()


    def changedGraphOptionsMavText(self, i):
        """Graph Option Mav Value has changed"""

        # print("changedGraphOptionsMavText: i:", i)

        try:
            mav_val = self.mav.text().replace(",", ".").replace("-", "")
            self.mav.setText(mav_val)
            val = float(mav_val)  # can value be converted to float?
            gglobs.mav = val
        except Exception as e:
            # exceptPrint(e, "changedGraphOptionsMavText: MvAvg permits numeric values only")
            pass

        self.applyGraphOptions()


    def changedGraphOptionsAvg(self, i):
        """Graph Option Avg has changed"""

        #print("changedGraphOptionsAvg: i:", i)
        gglobs.avgChecked  = self.avgbox.isChecked()
        self.applyGraphOptions()


    def changedGraphOptionsLinFit(self, i):
        """Graph Option LinFit has changed"""

        #print("changedGraphOptionsLinFit: i:", i)
        gglobs.fitChecked = self.fitbox.isChecked()
        self.applyGraphOptions()


    def changedGraphCountUnit(self, i):
        """counter unit Graph Options for left Y-axis was changed"""

        oldYunit            = gglobs.YunitCurrent
        gglobs.YunitCurrent = str(self.yunit.currentText())
        newYunit            = gglobs.YunitCurrent
        # print("changedGraphCountUnit: i:", i, ",  oldYunit:", oldYunit, ",  newYunit:", newYunit)

        # convert Y to CPM unit if not already CPM
        # print("changedGraphCountUnit: gglobs.Ymin, gglobs.Ymax, gglobs.Sensitivity[0]", gglobs.Ymin, gglobs.Ymax, gglobs.Sensitivity[0])
        if oldYunit == "µSv/h":
            if gglobs.Ymin != None: gglobs.Ymin = gglobs.Ymin * gglobs.Sensitivity[0]
            if gglobs.Ymax != None: gglobs.Ymax = gglobs.Ymax * gglobs.Sensitivity[0]

        # convert Y to µSv/h unit if not already µSv/h
        if newYunit == "µSv/h":
            if gglobs.Ymin != None: gglobs.Ymin = gglobs.Ymin / gglobs.Sensitivity[0]
            if gglobs.Ymax != None: gglobs.Ymax = gglobs.Ymax / gglobs.Sensitivity[0]

        if gglobs.Ymin == None: self.ymin.setText("")
        else:                   self.ymin.setText("{:.5g}".format(gglobs.Ymin))

        if gglobs.Ymax == None: self.ymax.setText("")
        else:                   self.ymax.setText("{:.5g}".format(gglobs.Ymax))

        if newYunit == "µSv/h":
            for vname in ("CPM", "CPS", "CPM1st", "CPS1st", "CPM2nd", "CPS2nd", "CPM3rd", "CPS3rd"):
                gglobs.varsCopy[vname][2] = "µSv/h"

        else: # newYunit == CPM
            for vname in ("CPM", "CPM1st", "CPM2nd", "CPM3rd"):
                gglobs.varsCopy[vname][2] = "CPM"

            for vname in ("CPS", "CPS1st", "CPS2nd", "CPS3rd"):
                gglobs.varsCopy[vname][2] = "CPS"

        self.applyGraphOptions()


    def changedGraphTemperatureUnit(self, i):
        """Temperature unit Graph Options was changed"""

        #print("changedGraphTemperatureUnit: New T unit:  i:", i, str(self.y2unit.currentText()) )

        if   i == 0:    gglobs.varsCopy["Temp"][2] = "°C"
        elif i == 1:    gglobs.varsCopy["Temp"][2] = "°F"

        self.applyGraphOptions()


    def changedGraphTimeUnit(self, i):
        """recalc xmin, xmax on Time unit changes"""

        #print("-----------------------changedGraphTimeUnit: i:", i)

        if np.all(gglobs.logTime) == None: return

        gsup_plot.changeTimeUnitofPlot(self.xunit.currentText())

        self.applyGraphOptions()


    def keyPressEvent(self, event):
        """Apply Graph is only Button to accept Enter and Return key"""

        # from: http://pyqt.sourceforge.net/Docs/PyQt4/qt.html#Key-enum
        # Qt.Key_Return     0x01000004
        # Qt.Key_Enter      0x01000005  Typically located on the keypad. (= numeric keypad)
        #print("event.key():", event.key())

        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.applyGraphOptions()


    def setPlotVarsOnOff(self, newstate="OFF"): # 'OFF' 'ON'
        """checks or unchecks all variables from plotting"""

        gglobs.allowGraphUpdate    = False  # prevents auto-updating at every variable
        if newstate == "OFF":
            for i, vname in enumerate(gglobs.varsCopy):
                if gglobs.varsSetForCurrent[vname]:
                    self.varDisplayCheckbox[vname].setEnabled(True)     # the checkbox at the bottom of Graph dashboard - always enabled
                    self.varDisplayCheckbox[vname].setChecked(False)    # the checkbox at the bottom of Graph dashboard - unchecked
                    self.select.model().item(i)   .setEnabled(False)    # the dropdown selector for Selected Variable

                    if gglobs.activeDataSource == "Log" : gglobs.varChecked4PlotLog[vname] = False
                    else:                                 gglobs.varChecked4PlotHis[vname] = False

        else:
            for i, vname in enumerate(gglobs.varsCopy):
                if gglobs.varsSetForCurrent[vname]:
                    self.varDisplayCheckbox[vname].setEnabled(True)     # the checkbox at the bottom of Graph dashboard - always enabled
                    self.varDisplayCheckbox[vname].setChecked(True)
                    self.select.model().item(i)   .setEnabled(True)

        # makes the index of the first enabled variable as the currentindex
        # of the variable select drop-down box
        for i, vname in enumerate(gglobs.varsCopy):
            #print("----i, self.select.model().item(i).isEnabled:", i, gglobs.exgg.select.model().item(i).isEnabled())
            if self.select.model().item(i).isEnabled():
                gglobs.exgg.select.setCurrentIndex(i)
                break

        gglobs.allowGraphUpdate    = True
        self.applyGraphOptions() # not automatically done due to
                                 # blocking by gglobs.allowGraphUpdate


    def clearGraphLimits(self):
        """resets all min, max graph options to empty and plots the graph"""

        vprint("clearGraphLimits:")
        setIndent(1)

        gglobs.Xleft               = None
        gglobs.Xright              = None
        self.xmin.                   setText("")
        self.xmax.                   setText("")

        gglobs.Ymin                = None
        gglobs.Ymax                = None
        self.ymin.                   setText("")
        self.ymax.                   setText("")

        gglobs.Y2min               = None
        gglobs.Y2max               = None
        self.y2min.                  setText("")
        self.y2max.                  setText("")

        gsup_plot.makePlot()

        setIndent(0)


    def plotGraph(self, dataType, full=True):
        """Plots the data as graph; dataType is Log or His"""

        if  dataType == "Log" and gglobs.logConn == None or \
            dataType == "His" and gglobs.hisConn == None:
            self.showStatusMessage("No data available")
            return

        vprint("plotGraph: dataType:", dataType)
        setIndent(1)

        if dataType == "Log":
            gglobs.activeDataSource     = "Log"
            gglobs.currentConn          = gglobs.logConn
            gglobs.currentDBPath        = gglobs.logDBPath
            gglobs.currentDBData        = gglobs.logDBData
            gglobs.varsSetForCurrent    = gglobs.varsSetForLog.copy()
            varsChecked4Plot            = gglobs.varChecked4PlotLog

            self.dcfLog.setText(gglobs.currentDBPath)
            self.dcfLog.setStyleSheet("QLineEdit { background-color: #F9F4C9; color: rgb(80,80,80); }")
            self.dcfHis.setStyleSheet("QLineEdit { background-color: #DFDEDD; color: rgb(80,80,80); }")

        elif dataType == 'His':
            gglobs.activeDataSource     = "His"
            gglobs.currentConn          = gglobs.hisConn
            gglobs.currentDBPath        = gglobs.hisDBPath
            gglobs.currentDBData        = gglobs.hisDBData
            gglobs.varsSetForCurrent    = gglobs.varsSetForHis.copy()
            varsChecked4Plot            = gglobs.varChecked4PlotHis

            self.dcfHis.setText(gglobs.currentDBPath)
            self.dcfLog.setStyleSheet("QLineEdit { background-color: #DFDEDD; color: rgb(80,80,80); }")
            self.dcfHis.setStyleSheet("QLineEdit { background-color: #F9F4C9; color: rgb(80,80,80); }")

        else:
            edprint("PROGRAMMING ERROR in geigerlog:plotGraph: var dataType is:", dataType, debug=True)
            sys.exit(1)

        gglobs.allowGraphUpdate    = False  # otherwise a replot at every var happens!
        for i, vname in enumerate(gglobs.varsCopy):
            self.select.model().item(i)         .setEnabled(False)
            if gglobs.varsSetForCurrent[vname]:
                value = varsChecked4Plot[vname]   # bool
                self.varDisplayCheckbox[vname]  .setChecked(value)
                self.varDisplayCheckbox[vname]  .setEnabled(True)
                self.select.model().item(i)     .setEnabled(value)
            else:
                self.varDisplayCheckbox[vname]  .setChecked(False)
                self.varDisplayCheckbox[vname]  .setEnabled(False)
        gglobs.allowGraphUpdate    = True

        if gglobs.currentDBData is not None:
            if gglobs.currentDBData.size > 0:
                fprint(header("Plot Data"))
                fprint("from: {}".format(gglobs.currentDBPath))

        self.figure.set_facecolor('#F9F4C9') # change colorbg in graph from gray to light yellow

        self.reset_replotGraph(full=full)

        setIndent(0)


    def reset_replotGraph(self, full=True):
        """resets all graph options to start conditions and plots the graph"""

        fncname = "reset_replotGraph: "

        vprint(fncname + "full: {}".format(full))
        setIndent(1)

        gglobs.allowGraphUpdate    = False

        if full:
            gglobs.Xleft               = None
            gglobs.Xright              = None
            gglobs.Xunit               = "Time"
            self.xmin.                   setText("")
            self.xmax.                   setText("")
            self.xunit.                  setCurrentIndex(0)

            gglobs.Ymin                = None
            gglobs.Ymax                = None
            gglobs.Yunit               = "CPM"
            self.ymin.                   setText("")
            self.ymax.                   setText("")
            self.yunit.                  setCurrentIndex(0)

            gglobs.Y2min               = None
            gglobs.Y2max               = None
            gglobs.Y2unit              = "°C"
            self.y2min.                  setText("")
            self.y2max.                  setText("")
            self.y2unit.                 setCurrentIndex(0)

            self.select.                 setCurrentIndex(0) # in case no data
            self.select.                 setEnabled(True)   # required

        # if full, reset to start condition
        if full:
            for i, vname in enumerate(gglobs.varsCopy):
                # cdprint("i:{:2d} vname: {:10s} varDisplayCheckbox[vname].isEnabled(): {}".format(i, vname, self.varDisplayCheckbox[vname].isEnabled()))
                if self.varDisplayCheckbox[vname].isEnabled():
                    self.varDisplayCheckbox[vname].setChecked(True)

        # Find the first enabled var and set this as selected var in dropdown box
        for i, vname in enumerate(gglobs.varsCopy):
            # cdprint("i:{:2d} vname: {:10s} select.model().item(i).isEnabled: {}".format(i, vname, gglobs.exgg.select.model().item(i).isEnabled()))
            if self.select.model().item(i).isEnabled():
                self.select.setCurrentIndex(i)
                break

        gglobs.mavChecked          = False
        self.mavbox.                 setChecked(gglobs.mavChecked)

        gglobs.mav                 = gglobs.mav_initial
        self.mav.                    setText("{:0.0f}".format(gglobs.mav_initial))

        gglobs.avgChecked          = False
        self.avgbox.                 setChecked(gglobs.avgChecked)

        gglobs.fitChecked          = False
        self.fitbox.                 setChecked(gglobs.fitChecked)

        gglobs.varsCopy            = gglobs.varsDefault.copy() # reset colors and linetype

        gglobs.allowGraphUpdate    = True

        self.updateDisplayVariableValue()

        self.applyGraphOptions()

        setIndent(0)


    def applyGraphOptions(self):

        if gglobs.currentConn == None: return

        fncname = "applyGraphOptions: "

        #replace comma with dot, strip outer whitespace
        xmin  = (str(self.xmin.text()).replace(",", ".")).strip()
        xmax  = (str(self.xmax.text()).replace(",", ".")).strip()
        xunit = str(self.xunit.currentText())

        ymin  = (str(self.ymin.text()).replace(",", ".")).strip()
        ymax  = (str(self.ymax.text()).replace(",", ".")).strip()
        yunit = str(self.yunit.currentText())

        y2min = (str(self.y2min.text()).replace(",", ".")).strip()
        y2max = (str(self.y2max.text()).replace(",", ".")).strip()

        mav   = (str(self.mav.text()).replace(",", ".") ).strip()

        #~print(fncname + "X : xmin:'{}', xmax:'{}', xunit:'{}', gglobs.Xunit:'{}'".format(xmin, xmax, xunit, gglobs.Xunit))
        #~print(fncname + "Y : ymin:'{}', ymax:'{}', yunit:'{}', gglobs.Yunit:'{}'".format(ymin, ymax, yunit, gglobs.Yunit))
        #~print(fncname + "Y2: ymin:'{}', ymax:'{}'                      ".format(y2min, y2max))
        #~print(fncname + "mav:'{}'".format(mav))

    # x
        if  xmin == "":
            gglobs.Xleft  = None
        else:
            if gglobs.Xunit == "Time":
                try:
                    gglobs.Xleft = mpld.datestr2num(str(xmin))
                except:
                    gglobs.Xleft = None
                    efprint("Did not recognize Time Min")
            else:
                try:
                    gglobs.Xleft     = float(xmin)
                except:
                    gglobs.Xleft     = None
                    efprint("Did not recognize Time Min")

        if  xmax == "":
            gglobs.Xright = None
        else:
            if gglobs.Xunit == "Time":
                try:
                    gglobs.Xright = mpld.datestr2num(str(xmax))
                except:
                    gglobs.Xright = None
                    efprint("Did not recognize Time Max")
            else:
                try:
                    gglobs.Xright    = float(xmax)
                except:
                    gglobs.Xright    = None
                    efprint("Did not recognize Time Max")

        #print(fncname + "Xleft ", gglobs.Xleft,  ",  Xright", gglobs.Xright)

        if gglobs.Xleft != None and gglobs.Xright != None:
            if gglobs.Xleft >= gglobs.Xright:
                efprint("Graph: Wrong numbers: Time Min must be less than Time Max")
                return

        gglobs.Xunit     = xunit

    # y
        try:    gglobs.Ymin      = float(ymin)
        except: gglobs.Ymin      = None

        try:    gglobs.Ymax      = float(ymax)
        except: gglobs.Ymax      = None

        if gglobs.Ymin != None and gglobs.Ymax != None:
            if gglobs.Ymin >= gglobs.Ymax:
                efprint("Graph: Wrong numbers: Count Rate min must be less than Count Rate max")
                return

        gglobs.Yunit     = yunit

    # y2
        try:    gglobs.Y2min      = float(y2min)
        except: gglobs.Y2min      = None

        try:    gglobs.Y2max      = float(y2max)
        except: gglobs.Y2max      = None

        if gglobs.Y2min != None and gglobs.Y2max != None:
            if gglobs.Y2min >= gglobs.Y2max:
                efprint("Graph: Wrong numbers: Ambient min must be less than Ambient max")
                return

    # color
        colorName = gglobs.varsCopy[getNameSelectedVar()][3]
        self.btnColor.setText("")
        self.btnColor.setStyleSheet("QLabel { border: 1px solid silver;  border-radius: 3px; background-color: %s ; }" % (colorName))
        addMenuTip(self.btnColor, self.btnColorText + colorName)

    # replot
        gsup_plot.makePlot()
        self.updateDisplayVariableValue()


    def updatecursorposition(self, event):
        """when cursor inside plot, get position and print to statusbar"""
        # see: https://matplotlib.org/api/backend_bases_api.html#matplotlib.backend_bases.MouseEvent

        # calc based on:
        # gglobs.y1_limit = ax1.get_ylim    defined in gsup_plot.py
        # gglobs.y2_limit = ax2.get_ylim

        #print("updatecursorposition: event: ", event, ", event.inaxes: ", event.inaxes, end="   ")

        try: # results in non-breaking error messages when no data are displayed
            if event.inaxes:
                x  = event.xdata
                y2 = event.ydata
                #print("updatecursorposition: ", x, y2)
                y1 = (y2 - gglobs.y2_limit[0]) / (gglobs.y2_limit[1] - gglobs.y2_limit[0]) * (gglobs.y1_limit[1] - gglobs.y1_limit[0]) + gglobs.y1_limit[0]

                if gglobs.Xunit == "Time":
                    tod = (str(mpld.num2date(x)))[:19]          # time of day
                    t   = gsup_plot.getTimeSinceFirstRecord(gglobs.logTimeFirst, x)

                else:
                    tod = gsup_plot.getTimeOfDay(gglobs.logTimeFirst, x, gglobs.XunitCurrent)
                    t   = "{:0.3f} {}s".format(x, gglobs.XunitCurrent)

                message = "Time since 1st record: {}, Time: {}, Counter: {:0.3f}, Ambient: {:0.3f}".format(t, tod, y1, y2)
                self.showStatusMessage(message, timing=0, error=False) # message remains until overwritten by next
        except:
            #print("event not inaxes")
            pass


    def onclick(self, event):
        """on mouseclick in graph enter time coords into xmin, xmax;
        left click = xmin, right click = xmax"""

        try: # if no data are shown, this may result in non-breaking error messages
            if event.inaxes:
                x = event.xdata
                y = event.ydata
                b = event.button
                #print event, x,y,b

                if gglobs.Xunit == "Time":
                    t = (str(mpld.num2date(x)))[:19]
                else:
                    t = "{:0.6f}".format(x)

                if b == 1:                  # left click, xmin
                    self.xmin.setText(t)
                elif b == 3:                # right click, xmax
                    self.xmax.setText(t)
                else:
                    pass
        except:
            pass


#history
    def getFileHistory(self, source):
        """getFileHistory from source. source is one out of:
                - "Device"
                - "Database"
                - "Binary File"
                - "Parsed File"
        no return; data stored in global variables"""

        fncname = "getFileHistory: "

    #
    # make the filedialog
    #
        # conditions
        if   source == "Database":
            # there must be an existing '*hisdb' file;
            # writing to it is not necessary; it will not be modified
            dlg=QFileDialog(caption = "Get History - Select from Existing Database File", options=QFileDialog.DontUseNativeDialog)
            dlg.setFileMode(QFileDialog.ExistingFile)
            dlg.setNameFilter("History or Log Files (*.hisdb *.logdb);;Only History Files (*.hisdb);;Only Log Files (*.logdb);;Any Files (*)")

        elif source == "Binary File":
            # there must be an existing, readable '*.bin' file,
            # and it must be allowed to write .hisdb files
            # the bin file will remain unchanged
            dlg=QFileDialog(caption = "Get History - Select from Existing Binary File", options=QFileDialog.DontUseNativeDialog)
            dlg.setFileMode(QFileDialog.ExistingFile)
            dlg.setNameFilter("History Files (*.bin *.gmc);;Any Files (*)")

        elif source == "Parsed File":
            # there must be an existing, readable '*.his' file
            # and it must be allowed to write .hisdb files
            # the his file will remain unchanged
            dlg=QFileDialog(caption= "Get History - Select from Existing *.his or other CSV File", options=QFileDialog.DontUseNativeDialog)
            dlg.setFileMode(QFileDialog.ExistingFile)
            dlg.setNameFilter("History Files (*.log *.his *.csv *.txt *.notes);;Any Files (*)")

        elif source == "Device":    # a GMC device
            if gglobs.logging:
                fprint(header("Get History from GMC Device"))
                efprint("Cannot load History when logging. Stop Logging first")
                return

            # may use existing or new .hisdb file, but must be allowed to overwrite this file
            # an existing hisdb file will be overwritten
            dlg=QFileDialog(caption = "Get History from GMC Device - enter new filename or select from existing", options=QFileDialog.DontUseNativeDialog)
            dlg.setFileMode(QFileDialog.AnyFile)
            dlg.setNameFilter("History Files (*.hisdb);;Any Files (*)")

        elif source == "GSDevice":  # a Gamma Scout device
            # may use existing or new .hisdb file, but must be allowed to overwrite this file
            # an existing hisdb file will be overwritten
            dlg=QFileDialog(caption = "Get History from Gamma-Scout Device - enter new filename or select from existing", options=QFileDialog.DontUseNativeDialog)
            dlg.setFileMode(QFileDialog.AnyFile)
            dlg.setNameFilter("History Files (*.hisdb);;Any Files (*)")

        elif source == "GSDatFile":
            # there must be an existing, readable '*.dat' file, created by
            # memory dumping of a Gamm Scout device,
            # and it must be allowed to write .hisdb files
            # the dat file will remain unchanged
            dlg=QFileDialog(caption = "Get History - Select from Existing Gamma Scout *.dat File", options=QFileDialog.DontUseNativeDialog)
            dlg.setFileMode(QFileDialog.ExistingFile)
            dlg.setNameFilter("History Files (*.dat);;Any Files (*)")

        elif source == "AMDeviceCAM":  # an Manu device for CAM data
            # may use existing or new .hisdb file, but must be allowed to overwrite this file
            # an existing hisdb file will be overwritten
            dlg=QFileDialog(caption = "Get History from Manu Device - enter new filename or select from existing", options=QFileDialog.DontUseNativeDialog)
            dlg.setFileMode(QFileDialog.AnyFile)
            dlg.setNameFilter("History Files (*.hisdb);;Any Files (*)")

        elif source == "AMDeviceCPS":  # an Manu device for CPS data
            # may use existing or new .hisdb file, but must be allowed to overwrite this file
            # an existing hisdb file will be overwritten
            dlg=QFileDialog(caption = "Get History from Manu Device - enter new filename or select from existing", options=QFileDialog.DontUseNativeDialog)
            dlg.setFileMode(QFileDialog.AnyFile)
            dlg.setNameFilter("History Files (*.hisdb);;Any Files (*)")

        #~ elif source == "AMDatFile":
            #~ ####### not valid -- placeholder for Manu !!!!!!!! ############
            #~ # wird es auch nicht geben, da CSV Files verwendet werden !!!
            #~ #
            #~ # there must be an existing, readable '*.dat' file, created by
            #~ # memory dumping of a Gamm Scout device,
            #~ # and it must be allowed to write .hisdb files
            #~ # the dat file will remain unchanged
            #~ dlg=QFileDialog(caption = "Get History - Select from Existing Gamma Scout *.dat File", options=QFileDialog.DontUseNativeDialog)
            #~ dlg.setFileMode(QFileDialog.ExistingFile)
            #~ dlg.setNameFilter("History Files (*.dat);;Any Files (*)")

        elif source == "AMFileCAM":
            # there must be an existing, readable '*.CAM' file, created by
            # e.g. downloading from an Manu device,
            # and it must be allowed to write .hisdb files
            # the *.CAM file will remain unchanged
            dlg=QFileDialog(caption = "Get History - Select from Existing Manu binary *.CAM File", options=QFileDialog.DontUseNativeDialog)
            dlg.setFileMode(QFileDialog.ExistingFile)
            dlg.setNameFilter("History Binary Files (*.CAM);;Any Files (*)")

        elif source == "AMFileCPS":
            # there must be an existing, readable '*.CPS' file, created by
            # e.g. downloading from an Manu device,
            # and it must be allowed to write .hisdb files
            # the *.CPS file will remain unchanged
            dlg=QFileDialog(caption = "Get History - Select from Existing Manu binary *.CPS File", options=QFileDialog.DontUseNativeDialog)
            dlg.setFileMode(QFileDialog.ExistingFile)
            dlg.setNameFilter("History Binary Files (*.CPS);;Any Files (*)")

        elif source == "Rad Pro Device (new)":
            # may use existing or new .hisdb file, but must be allowed to overwrite this file
            # an existing hisdb file will be overwritten
            dlg=QFileDialog(caption = "Get New History from Rad Pro Device - enter new filename or select from existing", options=QFileDialog.DontUseNativeDialog)
            dlg.setFileMode(QFileDialog.AnyFile)
            dlg.setNameFilter("History Files (*.hisdb);;Any Files (*)")

        elif source == "Rad Pro Device (all)":
            # may use existing or new .hisdb file, but must be allowed to overwrite this file
            # an existing hisdb file will be overwritten
            dlg=QFileDialog(caption = "Get All History from Rad Pro Device - enter new filename or select from existing", options=QFileDialog.DontUseNativeDialog)
            dlg.setFileMode(QFileDialog.AnyFile)
            dlg.setNameFilter("History Files (*.hisdb);;Any Files (*)")

        else:
            printProgError("getFileHistory: Filedialog: Wrong source: ", source)

        dlg.setViewMode     (QFileDialog.Detail)
        dlg.setWindowIcon   (self.iconGeigerLog)
        dlg.setDirectory    (gglobs.fileDialogDir)
        dlg.setFixedSize    (950, 550)

        # Execute dialog
        if dlg.exec() == QDialog.Accepted:  pass     # QDialog Accepted
        else:                               return   # QDialog Rejected
    ### end filedialog -  a file was selected

    #
    # Process the selected file
    #
        while True:
            fprint(header("Get History from {}".format(source)))
            dprint(fncname + "from source: ", source)
            setIndent(1)

            gglobs.fileDialogDir = dlg.directory().path() # remember the directory
            #print("getFileHistory: fileDialogDir:", gglobs.fileDialogDir)

            fnames      = dlg.selectedFiles()
            fname       = str(fnames[0])                # file path
            fext        = os.path.splitext(fname)[1]    # file ext
            fname_base  = os.path.splitext(fname)[0]    # file basename with path w/o ext

            vprint(fncname + "file name:   '{}'"                   .format(fname))
            wprint(fncname + "fname_base:  '{}', fname_ext: '{}'"  .format(fname_base, fext))

            gglobs.binFilePath = None
            gglobs.hisFilePath = None
            gglobs.datFilePath = None

            if   source == "Database":
                gglobs.hisDBPath   = fname # already has extension ".hisdb"
                if not isFileReadable(gglobs.hisDBPath):     break

            elif source == "Binary File":
                gglobs.binFilePath = fname
                gglobs.hisDBPath   = fname_base + ".hisdb"
                if not isFileReadable (gglobs.binFilePath):  break
                if not isFileWriteable(gglobs.hisDBPath):    break

            elif source == "Parsed File":
                gglobs.hisFilePath = fname
                gglobs.hisDBPath   = fname_base + ".hisdb"
                if not isFileReadable (gglobs.hisFilePath):  break
                if not isFileWriteable(gglobs.hisDBPath):    break

            elif source in ("Device", "GSDevice", "AMDeviceCAM", "AMDeviceCPS", "Rad Pro Device (new)", "Rad Pro Device (all)"):
                if fext != ".hisdb":
                    gglobs.hisDBPath   = fname + ".hisdb" # file has any extension or none
                else:
                    gglobs.hisDBPath   = fname            # file already has .hisdb extension
                if not isFileWriteable(gglobs.hisDBPath):    break

            elif source == "GSDatFile":
                gglobs.datFilePath = fname
                gglobs.hisDBPath   = fname + ".hisdb"
                if not isFileReadable (gglobs.datFilePath):  break
                if not isFileWriteable(gglobs.hisDBPath):    break

            elif source in ("AMFileCAM", "AMFileCPS"):
                gglobs.AMFilePath = fname
                gglobs.hisDBPath   = fname + ".hisdb"
                if not isFileReadable (gglobs.AMFilePath):   break
                if not isFileWriteable(gglobs.hisDBPath):    break

            else:
                printProgError(fncname + "Processing Selected File: Wrong source: ", source)


            # Messagebox re Overwriting file
            if source in ("Device", "GSDevice", "AMDeviceCAM", "AMDeviceCPS", "Rad Pro Device (new)", "Rad Pro Device (all)"):
                if os.path.isfile(gglobs.hisDBPath):
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Critical)
                    msg.setWindowTitle("CAUTION")
                    critical  = """You selected an existing file, which will be <b>OVERWRITTEN</b> if you continue. Please confirm with OK.
                                    \n\nOtherwise click Cancel and enter a new filename in the Get History from Device dialog."""
                    msg.setText(critical)
                    msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                    msg.setDefaultButton(QMessageBox.Cancel)
                    msg.setEscapeButton(QMessageBox.Cancel)
                    retval = msg.exec()

                    if retval != 1024:
                        fprint("Get History is cancelled")
                        break

            gglobs.currentDBPath   = gglobs.hisDBPath

            #dprint("getFileHistory: gglobs.binFilePath:     ", gglobs.binFilePath)
            #dprint("getFileHistory: gglobs.hisFilePath:     ", gglobs.hisFilePath)
            #dprint("getFileHistory: gglobs.hisDBPath:       ", gglobs.hisDBPath)
            #dprint("getFileHistory: gglobs.currentDBPath:   ", gglobs.currentDBPath)

            self.setBusyCursor()
            hidbp = "History database: {}"      .format(gglobs.hisDBPath)
            fprint(hidbp)
            dprint(fncname + hidbp)

            self.dcfHis.setText(gglobs.currentDBPath)
            self.clearLogPad()

            # an existing classic his, bin, or dat file was selected,
            # delete old database first
            if      gglobs.hisFilePath != None \
                or  gglobs.binFilePath != None \
                or  gglobs.datFilePath != None \
                or  gglobs.hisDBPath   != None and source in ("Device", "GSDevice", "AMDeviceCAM", "AMDeviceCPS", "Rad Pro Device (new)", "Rad Pro Device (all)"):

                gsup_sql.DB_deleteDatabase("His", gglobs.hisDBPath)

            # Open the database
            gglobs.hisConn = gsup_sql.DB_openDatabase  (gglobs.hisConn, gglobs.hisDBPath)

            if gglobs.hisFilePath != None:
                fprint("Creating from file {}".format(gglobs.hisFilePath))
                # read data from CSV file into database
                self.setNormalCursor()
                success = gsup_sql.getCSV(gglobs.hisFilePath)
                if success:
                    self.setBusyCursor()
                    gsup_sql.DB_convertCSVtoDB(gglobs.hisConn, gglobs.hisFilePath)
                else:
                    fprint("Database creation was cancelled")
                    return

            elif gglobs.binFilePath != None:
                fprint("Creating from file {}".format(gglobs.binFilePath))

            # Make Hist for source = GMC Device, GMC Binary File
            if source in ("Device", "Binary File"):
                error, message = gdev_gmc_hist.makeGMC_History(source)
                if error == -1:                                # a severe error
                    efprint(message)
                    break

            # Make Hist for source = Gamma Scout device or Gamma Scout *.dat File
            elif source in ("GSDevice", "GSDatFile"):
                error, message = gdev_gscout.GSmakeHistory(source)
                if error == -1:                                # a severe error
                    efprint(message)
                    break

            # Make Hist for source = AmbioMon device
            elif source in ("AMDeviceCAM", "AMDeviceCPS"):
                # error, message = gdev_Manu.makeAmbioHistory(source, gglobs.AmbioDeviceName)
                error, message = gdev_ambiomon.makeAmbioHistory(source, gglobs.Devices["AmbioMon"][DNAME])
                if error == -1:                                # a severe error
                    efprint(message)
                    break

            # Make Hist for source = AmbioMon binary file
            elif source in ("AMFileCAM", "AMFileCPS"):
                # error, message = gdev_Manu.makeAmbioHistory(source, gglobs.AmbioDeviceName)
                error, message = gdev_ambiomon.makeAmbioHistory(source, gglobs.Devices["AmbioMon"][DNAME])
                if error == -1:                                # a severe error
                    efprint(message)
                    break

            # Make Hist for source = RadPro device
            elif source in ("Rad Pro Device (new)", "Rad Pro Device (all)"):
                error, message = gdev_radpro.loadHistoryRadPro(source)
                if error == -1:                                # a severe error
                    efprint(message)
                    break

            gglobs.hisDBData, varsFromDB = gsup_sql.getDataFromDatabase("His") # also creates varchecked
            for vname in gglobs.varsCopy:
                if varsFromDB[vname]:           gglobs.varsSetForHis[vname] = True
                if gglobs.varsSetForHis[vname]: gglobs.varChecked4PlotHis[vname] = True

            self.plotGraph("His")

            self.checkLoggingState()
            break

        self.setNormalCursor()

        setIndent(0)

#xyc
    def clearLogfile(self):
        """Delete the logfile database and recreate it"""

        msg = QMessageBox()
        msg.setWindowIcon(gglobs.iconGeigerLog)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Clear Log File")
        msg.setText("You will loose all data in this database.\n\nPlease confirm with OK, or Cancel")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Cancel)
        msg.setEscapeButton(QMessageBox.Cancel)
        retval = msg.exec()

        if retval == QMessageBox.Ok:                        # QMessageBox.Ok == 1024
            self.btnClearLogfile.setEnabled(False)

            autoLogPath = os.path.join(gglobs.dataPath, gglobs.autoLogFile)
            self.stopLogging()
            gsup_sql.DB_deleteDatabase("Log", autoLogPath)
            self.getFileLog(defaultLogDBPath=autoLogPath)

            self.btnClearLogfile.setEnabled(True)


    def setLogCycle(self):
        """Set logCycle"""

        fncname = "setLogCycle: "

        dprint(fncname)
        setIndent(1)

        lctime     = QLabel("Log Cycle [s]  \n(0.100 ... 1000)   ")
        lctime.setAlignment(Qt.AlignLeft)

        self.ctime = QLineEdit()
        validator  = QDoubleValidator(0.1, 1000, 3, self.ctime)
        self.ctime.setValidator(validator)
        self.ctime.setToolTip('The log cycle in seconds. Changeable only when not logging.')
        self.ctime.setText("{:0.5g}".format(gglobs.logCycle))

        graphOptions=QGridLayout()
        graphOptions.addWidget(lctime,                  0, 0)
        graphOptions.addWidget(self.ctime,              0, 1)

        d = QDialog() # set parent empty to popup in center of screen
        d.setWindowIcon(self.iconGeigerLog)
        d.setWindowTitle("Set Log Cycle")
        d.setWindowModality(Qt.WindowModal)

        self.bbox = QDialogButtonBox()
        self.bbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok )
        self.bbox.accepted.connect(lambda: d.done(100))
        self.bbox.rejected.connect(lambda: d.done(0))

        gglobs.btn = self.bbox.button(QDialogButtonBox.Ok)
        gglobs.btn.setEnabled(True)

        layoutV = QVBoxLayout(d)
        layoutV.addLayout(graphOptions)
        layoutV.addWidget(self.bbox)

        self.ctime.textChanged.connect(self.check_state) # last chance
        self.ctime.textChanged.emit   (self.ctime.text())

        if gglobs.logging:
            gglobs.btn.setEnabled(False)
            self.ctime.setEnabled(False)
            self.ctime.setStyleSheet('QLineEdit { background-color: %s;  }' % ("#e0e0e0",))

        retval = d.exec()
        #print("retval:", retval)

        if retval == 0:
            dprint(fncname + "Cancel. Cycle time unchanged: ", gglobs.logCycle) # Cancel or ESC
        else:
            # change the cycle time
            oldlogCycle = gglobs.logCycle
            logCycle    = self.ctime.text().replace(",", ".")  #replace comma with dot
            try:    lc  = round(float(logCycle), 3)
            except: lc  = oldlogCycle

            gglobs.logCycle = lc
            self.showTimingSetting(gglobs.logCycle)
            dprint(fncname + "ok, new cycle time: ", gglobs.logCycle)

            # update database with logcyle
            if gglobs.logConn != None:
                gsup_sql.DB_updateLogcycle(gglobs.logConn, gglobs.logCycle)

        setIndent(0)


    def check_state(self, *args, **kwargs):

        sender = self.sender()

        # print("sender.text():", sender.text())
        # print("args:", args)
        # print("kwargs:", kwargs)

        try:
            v = float(sender.text().replace(",", "."))
            if   v < 0.1:       state = 0   # too low
            elif v > 1000:      state = 0   # too high
            else:               state = 2   # ok
        except:
            state = 0                       # wrong data

        # print("QValidator.Acceptable:", QValidator.Acceptable)

        # Value: QValidator.Acceptable == 2
        if state == QValidator.Acceptable:
            bgcolor = 'white' # white
            color   = 'black'
            gglobs.btn.setEnabled(True)

        #elif state == QValidator.Intermediate:
        #    color = '#fff79a' # yellow

        else:
            bgcolor = '#fff79a' # yellow
            color   = 'red'
            self.ctime.setFocus()
            gglobs.btn.setEnabled(False)

        sender.setStyleSheet('QLineEdit { background-color: %s; color: %s }' % (bgcolor, color))


# start logging
    def startLogging(self):
        """Starts the logging"""

        dprint("startLogging:")

        fprint(header("Start Logging"))

        # A logfile is not loaded
        # should never happen as the start button should be inactive
        if gglobs.logDBPath == None:
            efprint("WARNING: Cannot log; Logfile is not loaded")
            return

        # Logfile is either read-only, not writeable, or had been removed
        if not os.access(gglobs.logDBPath, os.W_OK):
            efprint("WARNING: Cannot log; Logfile is not available for writing!")
            return

        # No loggable variables
        if gglobs.varMapCountTotal == 0:
            efprint("WARNING: No variables for logging available; Logging is not possible!")
            qefprint("Please check configuration if this is unexpected !")
            return

    # all clear, go for it

        setIndent(1)

        gglobs.logging       = True          # set early, to allow threads to get data
        gglobs.LogReadings   = 0
        gglobs.currentDBPath = gglobs.logDBPath

        # make comment lines like:
        #   DEVICES, 2022-06-06 15:54:46, Connected: GMC : GMC-300Re 4.54 : CPS
        #   DEVICES, 2022-06-06 15:54:46, Connected: Manu : GeigerLog Manu : Temp Press Humid Xtra
        #   LOGGING, 2022-06-06 15:54:46, Start @Cycle: 1.0 sec
        comments  = []
        printcom  = ""
        for DevName in gglobs.Devices:
            if gglobs.DevVarsAsText[DevName] != None:
                cinfo     = "Connected: {} : {} : {}" .format(DevName, gglobs.Devices[DevName][0], gglobs.DevVarsAsText[DevName])
                printcom += "#DEVICES, {}, {}\n"     .format(stime(), cinfo)
                comments.append(["DEVICES", "NOW", "localtime", cinfo])

        cinfo     = "Start @Cycle: {} sec"   .format(gglobs.logCycle)
        printcom += "#LOGGING, {}, {}"       .format(stime(), cinfo)
        comments.append(["LOGGING", "NOW", "localtime", cinfo])

        gsup_sql.DB_insertComments(gglobs.logConn, comments)
        logPrint(printcom)
        fprint  (printcom)

        cleanupDevices("before logging")

    # STARTING
        self.checkLoggingState()
        self.plotGraph("Log", full=False)                   # initialize graph settings
        gglobs.logCycleButtonFlag = "On"

        initLogThread()

        dprint("startLogging: Logging now; Timer was started with cycle {} sec.".format(gglobs.logCycle))

        setIndent(0)


# stop logging
    def stopLogging(self):
        """Stops the logging"""

        if not gglobs.logging: return

        fncname = "stopLogging: "

        dprint(fncname)
        setIndent(1)

        fprint(header("Stop Logging"))

        # cdprint(fncname + "about to call terminateLogThread()")
        terminateLogThread()

        gglobs.logging = False
        dprint(fncname + "Logging is stopped")

        writestring  = "#LOGGING, {}, Stop".format(stime())
        logPrint(writestring)
        fprint(writestring)

        gsup_sql.DB_insertComments(gglobs.logConn, [["LOGGING", "NOW", "localtime", "Stop"]])

        cleanupDevices("after logging")

        self.checkLoggingState()
        self.labelSelVar.setStyleSheet('color:darkgray;')
        self.updateDisplayVariableValue()

        # For the the Rad World Map update - will make it wait for full cycle
        gglobs.RWMmapLastUpdate = None

        gglobs.logCycleButtonFlag = "Off"
        setIndent(0)


    def addComment(self, dataType):
        """Adds a comment to the current log"""

        if dataType == "Log":
            if gglobs.logConn is None:
                self.showStatusMessage("No LogFile available")
                return

        elif dataType == "His":
            if gglobs.hisConn is None:
                self.showStatusMessage("No HisFile available")
                return

        else:
            if gglobs.currentConn is None:
                self.showStatusMessage("No File available")
                return
            elif gglobs.currentConn == gglobs.logConn:  dataType = "Log"
            else:                                       dataType = "His"

        info        = ("Enter your comment to the <b>{}</b> file: " + "&nbsp;"*100).format(dataType)

        d           = QInputDialog()
        # it looks like QInputDialog() always blocks outside clicking????
        d.setWindowModality(Qt.NonModal)                                      # no clicking outside
        dtext, ok   = d.getText(None, 'Add a Comment', info)

        if ok:
            dtext       = str(dtext)
            ctype       = "COMMENT"
            cJulianday  = "NOW"
            cinfo       = dtext
            if dataType == "Log":
                fprint(header("Add Comment to Log"))
                logPrint("#COMMENT, {}, {}".format(stime(), dtext)) # to the LogPad
                fprint("#COMMENT, {}, {}".format(stime(), dtext))   # to the NotePad
                gsup_sql.DB_insertComments(gglobs.logConn, [[ctype, cJulianday, "localtime", cinfo]]) # to the DB

            else: # dataType == "His"
                fprint(header("Add Comment to History"))
                fprint("#COMMENT, {}, {}".format(stime(), dtext))   # to the NotePad
                cJulianday  = None
                gsup_sql.DB_insertComments(gglobs.hisConn, [[ctype, cJulianday, "localtime", cinfo]]) # to the db

            vprint("Add a Comment: text='{}', ok={}".format(dtext,ok))


    def addGMC_Error(self, errtext):
        """Adds ERROR info from gdev_gmc as comment to the current log"""

        logPrint("#GMC_ERROR, {}, {}".format(stime(), errtext))   # to the LogPad

        if not gglobs.logConn is None:                            # to the DB
            gsup_sql.DB_insertComments(gglobs.logConn, [["DevERROR", "NOW", "localtime", errtext]])


    def addMsgToLog(self, type, msg):
        """Adds message to the current log
        type: like 'Success', 'Failure'"""

        logPrint("#{}, {}, {}".format(type, stime(), msg))        # to the LogPad
        if not gglobs.logConn is None:                            # to the DB
            gsup_sql.DB_insertComments(gglobs.logConn, [[type, "NOW", "localtime", msg]])


#
# Update the LogCycle setting in the dashboard
#
    def showTimingSetting(self, logCycle):
        """update the Timings shown on the LogCycle button"""

        self.btnSetCycle.setText("Log Cycle: {:0.5g} s".format(logCycle))


#
# Update the display
#
    def updateDisplayVariableValue(self):
        """
        update: the Selected Variable value displayed in the Graph LastValue box
        and   : the Display Last Log Values window
        return: nothing
        """

        #***********************************************************************************************

        def getStatusTip(counttype, svalue, scaleIndex):

            if counttype == "M": value = svalue         # CPM
            else:                value = svalue * 60    # CPS

            statusTip  = "{:0.2f} CPM"     .format(value)
            statusTip += " = {:0.2f} CPS"  .format(value / 60)
            statusTip += " = {:0.2f} µSv/h".format(value * scale[scaleIndex])
            statusTip += " = {:0.2f} mSv/a".format(value * scale[scaleIndex] / 1000 * 24 * 365.25)

            return statusTip


        # original version of 1.4.0
        #~def getVarText(selUnit1, value, scaleIndex, counttype):

            #~# if selUnit1 == "CPM":   varText = "{:0.0f} CP{}".format(value, counttype)
            #~if selUnit1 == "CPM":   varText = "{:0.5g} CP{}".format(value, counttype)
            #~else:                   varText = "{:0.5g} µSv/h".format(value * 60 * scale[scaleIndex])
            #~# if selUnit1 == "CPM":   varText = "{:0.3g} CP{}".format(value, counttype)
            #~# else:                   varText = "{:0.3g} µSv/h".format(value * 60 * scale[scaleIndex])

            #~return varText

        # the fixed version of 1.4.1
        def getVarText(selUnit1, svalue, scaleIndex, counttype):
            """the text to show in the last variable field"""

            if counttype == "M": value = svalue         # CPM
            else:                value = svalue * 60    # CPS

            if selUnit1 == "CPM":
                # rdprint("CPM")
                varText = "{:0.5g} CP{}".format(value, counttype)
            else:
                # rdprint("µSv/h")
                varText = "{:0.4g} µSv/h".format(value * scale[scaleIndex])

            return varText


        #***********************************************************************************************

        fncname = "updateDisplayVariableValue: "

        if gglobs.lastLogValues == None:
            self.labelSelVar.setText(" --- ")
            addMenuTip(self.labelSelVar, "Shows Last Value of the Selected Variable when logging")
            return

    # update DisplayVariables Window
        # see function displayLastValues() in gsup_tools.py
        if gglobs.displayLastValsIsOn:
            try:
                for vi, vname in enumerate(gglobs.varsCopy):
                    # print("vi", vi, "vname: ", vname, ", self.vlabels[vi]", self.vlabels[vi])
                    if self.vlabels[vi] is None: continue
                    gsup_tools.setLastValues(vi, vname)

            except Exception as e:
                msg = "Exception updateDisplayVariableValue:"
                exceptPrint(e, msg)

    # update selected variable:
        # when logging: black on yellow background, else with dark.grey on grey
        if gglobs.activeDataSource == "Log" and gglobs.logging :
            self.labelSelVar.setStyleSheet('color: black; background-color: #F4D345;')

        elif gglobs.activeDataSource == "His":
            self.labelSelVar.setText(" --- ")
            self.labelSelVar.setStyleSheet('color:darkgray;')
            addMenuTip(self.labelSelVar, "")
            return

        selVar    = self.select.currentText()         # selected variable
        selUnit1  = self.yunit .currentText()
        selUnit2  = self.y2unit.currentText()
        varText   = " --- "

        scale = [None] * 4
        for i in range(0, 4):
            if gglobs.Sensitivity[i] == "auto":  scale[i] = 1 / gglobs.DefaultSens[i]
            else:                                scale[i] = 1 / gglobs.Sensitivity[i]
            # print(fncname + "scale[{}]: {}".format(i, scale[i]))

        value       = gglobs.lastLogValues[selVar]
        statusTip   = ""
        if not np.isnan(value):               # on NAN no update, keep the old value

            if   selVar == "CPM":
                varText   = getVarText(selUnit1, value, 0, "M")
                statusTip = getStatusTip("M", value, 0)

            elif selVar == "CPS":
                varText   = getVarText(selUnit1, value, 0, "S")
                statusTip = getStatusTip("S", value, 0)

            elif selVar == "CPM1st":
                varText   = getVarText(selUnit1, value, 1, "M")
                statusTip = getStatusTip("M", value, 1)

            elif selVar == "CPS1st":
                varText   = getVarText(selUnit1, value, 1, "S")
                statusTip = getStatusTip("S", value, 1)

            elif selVar == "CPM2nd":
                varText   = getVarText(selUnit1, value, 2, "M")
                statusTip = getStatusTip("M", value, 2)

            elif selVar == "CPS2nd":
                varText   = getVarText(selUnit1, value, 2, "S")
                statusTip = getStatusTip("S", value, 2)

            elif selVar == "CPM3rd":
                varText   = getVarText(selUnit1, value, 3, "M")
                statusTip = getStatusTip("M", value, 3)

            elif selVar == "CPS3rd":
                varText   = getVarText(selUnit1, value, 3, "S")
                statusTip = getStatusTip("S", value, 3)

            elif selVar == "Temp":
                if selUnit2 == "°C":  varText = "{:0.2f} °C".format(value)
                else:                 varText = "{:0.2f} °F".format(value / 5 * 9 + 32)
                statusTip  = "{:0.2f} °C = {:0.2f} °F".format(value, value / 5 * 9 + 32)

            elif selVar == "Press":
                varText   = "{:0.2f} hPa".format(value)
                statusTip = "{:0.2f} hPa = {:0.2f} mbar".format(value, value)

            elif selVar == "Humid":
                varText   = "{:0.2f} %RH".format(value)
                statusTip = "{:0.2f} %RH".format(value)

            elif selVar == "Xtra":
                varText   = "{:0.2f}".format(value)
                statusTip = "{:0.2f}".format(value)

        self.labelSelVar.setText(varText)
        addMenuTip(self.labelSelVar, statusTip)

#
# Get Log file
#
    def quickLog(self):
        """Starts logging with empty default log file 'default.log'"""

        fncname = "quickLog: "

        fprint(header("Quick Log"))
        msg = "Start logging using Quick Log database 'default.logdb'"
        fprint(msg)
        dprint(fncname + msg)
        setIndent(1)

        # set up default.logdb
        gglobs.logDBPath = os.path.join(gglobs.dataPath, "default.logdb")
        gsup_sql.DB_deleteDatabase("Log", gglobs.logDBPath)     # close any existing db, and then delete file
        self.getFileLog(defaultLogDBPath=gglobs.logDBPath)      # make a new one
        self.startLogging()

        setIndent(0)


    def getFileLog(self, defaultLogDBPath=False, source="Database"):
        """Load existing file for logging, or create new one.
        source can be:
        - "Database" (which is *.logdb file )
        - "CSV File" (which is any csv file)
        """

        fncname = "getFileLog: "

        #
        # Get logfile filename/path
        #
        # If a default logfile is given; use it
        if defaultLogDBPath != False:
            gglobs.logFilePath      = None
            gglobs.logDBPath        = defaultLogDBPath
            dprint("getFileLog: using defaultLogDBPath: ", gglobs.logDBPath)

        # else run dialog to get one
        else:
            if   source == "Database":
                # may use existing or new .logdb file, but must be allowed to overwrite this file
                # an existing logdb file allows appending with new data
                dlg=QFileDialog(caption= "Get Log - Enter New Filename or Select from Existing", options=QFileDialog.DontUseNativeDialog)
                dlg.setFileMode(QFileDialog.AnyFile)

                dlg.setNameFilter("Log Files (*.logdb);;Any Files (*)")

            elif source == "CSV File":
                # there must be an existing, readable csv file with extension '*.log' or '*.csv' or '*.txt' or '*.notes' file
                # the csv file will remain unchanged
                dlg=QFileDialog(caption = "Get Log - Select from Existing *.log or other CSV File", options=QFileDialog.DontUseNativeDialog)
                dlg.setFileMode(QFileDialog.ExistingFile)
                dlg.setNameFilter("Log Files (*.log *.csv *.txt *.notes);;Any Files (*)")

            else:
                printProgError("undefined source:", source)

            dlg.setViewMode(QFileDialog.Detail)
            dlg.setWindowIcon(self.iconGeigerLog)
            dlg.setDirectory(gglobs.fileDialogDir)

            dlg.setFixedSize(950, 550)

            # Execute dialog
            if dlg.exec() == QDialog.Accepted:  pass     # QDialog Accepted
            else:                               return   # QDialog Rejected

        ### end filedialog -  a file was selected

            gglobs.fileDialogDir = dlg.directory().path()
            # print("dlg.directory().path():", dlg.directory().path())

            fnames      = dlg.selectedFiles()
            fname       = str(fnames[0])                    # file path
            fext        = os.path.splitext(fname)[1]        # file extension
            fname_base  = os.path.splitext(fname)[0]        # file basename with path w/o ext

            if   source == "Database":  # extension is .logdb
                gglobs.logFilePath = None
                if fext != ".logdb":    gglobs.logDBPath   = fname + ".logdb" # file has any extension or none
                else:                   gglobs.logDBPath   = fname            # file already has .logdb extension

            elif source == "CSV File":  # extension is .log, .csv, .txt
                gglobs.logFilePath = fname
                gglobs.logDBPath   = fname_base + ".logdb"
                if not isFileReadable (gglobs.logFilePath):   return

            if source == "Database":
                # if file exists, give warning on overwriting
                if os.path.isfile(gglobs.logDBPath):
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle("CAUTION")
                    critical  = """You selected an existing file, which will be modified \
                                when logging by <b>APPENDING</b> new data to it.
                                \n\nPlease confirm with OK.
                                \n\nOtherwise click Cancel and enter a new filename in the Get Log dialog."""
                    msg.setText(critical)
                    msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                    msg.setDefaultButton(QMessageBox.Cancel)

                    msg.setEscapeButton(QMessageBox.Cancel)
                    retval = msg.exec()

                    if retval != 1024:
                        return

        # Done getting LogFile   ##############################################

        self.setBusyCursor()

        gglobs.currentDBPath   = gglobs.logDBPath

# ######################################################
#         # does this interfere with His????
#         # scheint ok, hilft aber nicht on var use

#         gglobs.logTime             = None                 # array: Time data from total file
#         gglobs.logTimeDiff         = None                 # array: Time data as time diff to first record in days
#         gglobs.logTimeFirst        = None                 # value: Time of first record of total file

#         gglobs.logTimeSlice        = None                 # array: selected slice out of logTime
#         gglobs.logTimeDiffSlice    = None                 # array: selected slice out of logTimeDiff
#         gglobs.logSliceMod         = None

#         gglobs.sizePlotSlice       = None                 # value: size of plotTimeSlice

#         gglobs.logDBData           = None                 # 2dim numpy array with the log data
#         gglobs.hisDBData           = None                 # 2dim numpy array with the his data
#         gglobs.currentDBData       = None                 # 2dim numpy array with the currently plotted data

# ######################################################

        fprint(header("Get Log"))
        fprint("Log database: {}".                               format(gglobs.logDBPath))
        if defaultLogDBPath == False:
            dprint("getFileLog: use selected Log DB file: '{}'". format(gglobs.logDBPath))
        else:
            dprint("getFileLog: use default Log DB file: '{}'".  format(defaultLogDBPath))
        setIndent(1)

        dprint("getFileLog: gglobs.logFilePath:     ", gglobs.logFilePath)
        dprint("getFileLog: gglobs.logDBPath:       ", gglobs.logDBPath)
        dprint("getFileLog: gglobs.currentDBPath:   ", gglobs.currentDBPath)

        if gglobs.logging:   self.stopLogging()
        self.dcfLog.setText(gglobs.logDBPath)
        self.clearLogPad()

        # an existing classic log was selected. It will be converted to a database;
        # any previous conversion will be deleted first
        if gglobs.logFilePath != None:
            fprint("Created from file {}".format(gglobs.logFilePath))
            # delete old database
            gsup_sql.DB_deleteDatabase("Log", gglobs.logDBPath)

            # open new database
            gglobs.logConn      = gsup_sql.DB_openDatabase(gglobs.logConn, gglobs.logDBPath)

            # read data from CSV file into database
            self.setNormalCursor()

            if gsup_sql.getCSV(gglobs.logFilePath):
                self.setBusyCursor()
                gsup_sql.DB_convertCSVtoDB(gglobs.logConn, gglobs.logFilePath)
            else:
                fprint("Database creation was cancelled")
                return


        # a database file was selected
        else:
            # Database File does NOT exist; create new one
            if not os.path.isfile(gglobs.logDBPath):
                fprint("LogFile newly created - available for writing")

                linfo = "LogFile newly created as '{}'".format(os.path.basename(gglobs.logDBPath))
                logPrint("#HEADER , {}, ".format(stime()) + linfo)

                # open new database
                gglobs.logConn      = gsup_sql.DB_openDatabase(gglobs.logConn, gglobs.logDBPath)

                ctype       = "HEADER"
                cJulianday  = 'NOW'
                cinfo       = linfo
                gsup_sql.DB_insertComments(gglobs.logConn, [[ctype, cJulianday, "localtime", cinfo]])

                # data array for the variables
                gglobs.logDBData = np.empty([0, gglobs.datacolsDefault])
                # edprint(fncname + "gglobs.logDBData empty: ", gglobs.logDBData)

            # Database File does exist
            else:
                # Database File does exist and can read and write
                if os.access(gglobs.logDBPath, os.W_OK):
                    fprint("LogFile opened - available for writing")

                # DB File does exist but can read only
                elif os.access(gglobs.logDBPath, os.R_OK):
                    efprint("LogFile opened - WARNING: available ONLY FOR READING")

                gglobs.logConn    = gsup_sql.DB_openDatabase  (gglobs.logConn, gglobs.logDBPath)

        ## end of else ##############

        gglobs.logDBData, varsFromDB = gsup_sql.getDataFromDatabase("Log")
        gglobs.varsSetForLog = gglobs.varsSetForLogNew.copy()           # reset to default device dependent setting
        for vname in gglobs.varsCopy:
            if varsFromDB[vname]: gglobs.varsSetForLog[vname] = True    # this adds vars from DEB which are no longer active!
            if gglobs.varsSetForLog[vname]: gglobs.varChecked4PlotLog[vname] = True


        # set the logCycle as read from the database (if present)
        DefLogCycle = gsup_sql.DB_readLogcycle(gglobs.logConn)          # DefLogCycle is type float
        #print("Default LogCycle:",DefLogCycle, type(DefLogCycle))
        if DefLogCycle is None:                                         # old DB may not have one
            gsup_sql.DB_insertLogcycle(gglobs.logConn, gglobs.logCycle)
        else:
            gglobs.logCycle = DefLogCycle
            self.showTimingSetting(gglobs.logCycle)

        self.plotGraph("Log")
        self.checkLoggingState()
        self.setNormalCursor()

        setIndent(0)


#
# Show data from Log, His, and Bin files ######################################
#
    def showData(self, dataSource=None, full=True):
        """Print Log or His Data to notepad, as full file or excerpt.
        dataSource can be 'Log' or 'His' or 'HisBin' (for binary data) or
        HisParse or PlotData"""

        # print("showData dataSource: {}, fullflag: {}".format(dataSource, full))
        if dataSource == None:
            if    gglobs.activeDataSource == "Log": dataSource = "Log"
            else:                                   dataSource = "His"
        # print("\n\nshowData dataSource: {}, fullflag: {}".format(dataSource, full))

        if gglobs.activeDataSource == None:
            self.showStatusMessage("No data available")
            return

        textprintButtonDef  = "Data"
        textprintButtonStop = "STOP"

        # stop printing
        if self.btnPrintFullData.text() == textprintButtonStop:
            gglobs.stopPrinting = True
            # print("gglobs.stopPrinting: ", gglobs.stopPrinting)
            return

        if full:
            # switch button mode to "STOP"
            self.btnPrintFullData.setStyleSheet('QPushButton {color: blue; background-color:white; font:bold;}')
            self.btnPrintFullData.setText(textprintButtonStop)

        if   dataSource == "Log":          self.showDBData(DBtype="Log",     DBpath=gglobs.logDBPath, DBconn=gglobs.logConn, varchecked=gglobs.varsSetForLog, full=full)
        elif dataSource == "His":          self.showDBData(DBtype="History", DBpath=gglobs.hisDBPath, DBconn=gglobs.hisConn, varchecked=gglobs.varsSetForHis, full=full)
        elif dataSource == "HisBin":       gsup_sql.createLstFromDB(full=full)
        elif dataSource == "HisParse":     gsup_sql.createParseFromDB(full=full)
        elif dataSource == "PlotData":     gsup_tools.fprintPlotData()              # print data as shown in plot

        # reset button to default
        self.btnPrintFullData.setStyleSheet('QPushButton {}')
        self.btnPrintFullData.setText(textprintButtonDef)


    def showDBData(self, DBtype=None, DBpath=None, DBconn=None, varchecked=None, full=True):
        """ print logged data from Log or Hist to notepad"""

        fncname = "showDBData: "

        if DBconn == None:
            self.showStatusMessage("No data available")
            return

        self.setBusyCursor()

        if full:    addp = ""
        else:       addp = " Excerpt"
        fprint(header("Show {} Data".format(DBtype) + addp))
        fprint("from: {}\n".format(DBpath))

        sql, ruler = gsup_sql.getShowCompactDataSql(varchecked)

        fprint(ruler)
        # dprint(fncname + "ruler: ", ruler)

        if full:
            data = gsup_sql.DB_readData(DBconn, sql, limit=0)
            # for a in data:   print(fncname + "sql dataline:", a)

            counter      = 0
            counter_max  = 100
            update       = 900
            update_max   = 1000
            datastring   = ""
            gglobs.stopPrinting = False
            for a in data:
                datastring += a + "\n"
                if counter >= counter_max:
                    fprint(datastring[:-1])
                    fprint(ruler)
                    datastring = ""
                    counter    = 0

                if update >= update_max:
                    QtUpdate()
                    update = 0

                if gglobs.stopPrinting: break
                counter     += 1
                update      += 1

            gglobs.stopPrinting = False
            fprint(datastring[:-1])

        else:
            fprint(self.getExcerptLines(sql, DBconn))

        fprint(ruler)

        self.setNormalCursor()


    def showDBTags(self, DBtype=None):
        """print comments from DB, either DBtype=Log or =History"""

        if DBtype == "Log":
            DBConn = gglobs.logConn
            DBPath = gglobs.logDBPath
        else:   # "History"
            DBConn = gglobs.hisConn
            DBPath = gglobs.hisDBPath

        if DBConn == None:
            self.showStatusMessage("No data available")
            return

        self.setBusyCursor()

        fprint(header("Show {} Tags and Comments".format(DBtype)))
        fprint("from: {}\n".format(DBPath))
        rows = gsup_sql.DB_readComments(DBConn)
        fprint("\n".join(rows))

        self.setNormalCursor()


    def getExcerptLines(self, sql, DB_Conn, lmax=10):
        """get first and last lines from the db"""

        if DB_Conn == None:  return ""

        excLines  = gsup_sql.DB_readData(DB_Conn, sql, limit=lmax)
        # for a in excLines: print(a)

        lenall    = len(excLines)
        # print("lenall", lenall)
        if lenall == 0:      return ""      # no data

        plines = ""
        if lenall < lmax * 2:
            for i in range(0, lenall):   plines += excLines[i] + "\n"

        else:
            for a in excLines[0:lmax]:   plines += a + "\n"
            plines +=                         "      ...\n"
            for a in excLines[-lmax:]:   plines += a + "\n"

        return plines[:-1] # remove "\n"


# printing to hardware printer or pdf file
    def printNotePad(self):
        """prints NotePad content to printer or pdf"""

        fncname = "printNotePad: "

        if gglobs.currentDBPath is None: defaultOutputFile = os.path.join(gglobs.dataPath, "notepad.pdf")
        else:                            defaultOutputFile = gglobs.currentDBPath + '.pdf'
        # vprint(fncname + "default output file:", defaultOutputFile)

        myprinter = QPrinter()
        myprinter.  setOutputFormat(QPrinter.PdfFormat)
        myprinter.  setOutputFileName(defaultOutputFile)

        dialog = QPrintDialog(myprinter, self)
        dialog.setOption(QAbstractPrintDialog.PrintToFile, on=True)

        if dialog.exec():
            mydoc = self.notePad.document()
            mydoc.print(dialog.printer())


    def setTemporaryTubeSensitivities(self):
        """Dialog to set tube sensitivities for all tubes temporarily"""

        fncname = "setTemporaryTubeSensitivities: "

        # setting the scaling factor (needed if no device connected)
        scale = [None] * 4
        for i in range(0, 4):
            if gglobs.Sensitivity[i] == "auto":    scale[i] = gglobs.DefaultSens[i]
            else:                                  scale[i] = gglobs.Sensitivity[i]

        dprint(fncname)
        setIndent(1)

        # Comment
        intro = """
<p>Allows to set the sensitivities for all Geiger tubes.
<p>This is temporary for this run only. For a permanent change edit the GeigerLog configuration file 'geigerlog.cfg'.
<p>Sensititivities are in units of <b>CPM / (µSv/h) </b>.
<p><b>NOTE:</b>
If no data for the tube's sensitivity are avail&shy;able, then take guidance
from the following numbers and see chapter 'Appendix G – Calibration' of the GeigerLog manual.</p>
<p>For a tube like M4011 and a radiation scenario like:
<pre>
    Cs-137 : 154 CPM / (µSv/h)  (100%)
    Co-60  : 132 CPM / (µSv/h)  ( 86%)
    Ra-226 : 174 CPM / (µSv/h)  (113%)
</pre>
</p>
"""

    # Intro
        lcomment = QLabel(intro)
        lcomment.setMaximumWidth(400)
        lcomment.setWordWrap(True)

    # Def tube
        ltubeDef = QLabel("CPM / CPS  ")
        ltubeDef.setAlignment(Qt.AlignLeft)

        etubeDef = QLineEdit()
        etubeDef.setToolTip('Code: M / S')
        etubeDef.setText("{:0.6g}".format(scale[0]))

    # 1st tube
        ltube1st = QLabel("CPM1st / CPS1st")
        ltube1st.setAlignment(Qt.AlignLeft)

        etube1st = QLineEdit()
        etube1st.setToolTip('Code: M1 / S1')
        etube1st.setText("{:0.6g}".format(scale[1]))

    # 2nd tube
        ltube2nd = QLabel("CPM2nd / CPS2nd  ")
        ltube2nd.setAlignment(Qt.AlignLeft)

        etube2nd = QLineEdit()
        etube2nd.setToolTip('Code: M2 / S2')
        etube2nd.setText("{:0.6g}".format(scale[2]))

    # 3rd tube
        ltube3rd = QLabel("CPM3rd / CPS3rd  ")
        ltube3rd.setAlignment(Qt.AlignLeft)

        etube3rd = QLineEdit()
        etube3rd.setToolTip('Code: M3 / S3')
        etube3rd.setText("{:0.6g}".format(scale[3]))

        tubeOptions=QGridLayout()
        tubeOptions.addWidget(lcomment,    0, 0, 1, 2) # from 0,0 over 1 row and 2 cols
        tubeOptions.addWidget(ltubeDef,    1, 0)
        tubeOptions.addWidget(etubeDef,    1, 1)
        tubeOptions.addWidget(ltube1st,    2, 0)
        tubeOptions.addWidget(etube1st,    2, 1)
        tubeOptions.addWidget(ltube2nd,    3, 0)
        tubeOptions.addWidget(etube2nd,    3, 1)
        tubeOptions.addWidget(ltube3rd,    4, 0)
        tubeOptions.addWidget(etube3rd,    4, 1)

    # Dialog box
        d = QDialog() # set parent empty to popup in center of screen
        d.setWindowIcon(self.iconGeigerLog)
        d.setWindowTitle("Set Geiger Tube Sensitivities")
        d.setWindowModality(Qt.WindowModal)
        # d.setMaximumWidth(200)

    # Buttons
        self.bbox = QDialogButtonBox()
        self.bbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.bbox.accepted.connect(lambda: d.done(100))
        self.bbox.rejected.connect(lambda: d.done(0))

        layoutV = QVBoxLayout(d)
        layoutV.addLayout(tubeOptions)
        layoutV.addWidget(self.bbox)
        layoutV.addStretch()

        retval = d.exec()
        #print("reval:", retval)
        if retval == 0:
            # CANCEL
            dprint(fncname + "CANCEL clicked, Sensitivities unchanged")

        else:
            # OK
            fprint(header("Set Geiger Tube Sensitivities"))
            try:        ftubeDef = float(etubeDef.text().replace(",", "."))
            except:     ftubeDef = 0
            try:        ftube1st = float(etube1st.text().replace(",", "."))
            except:     ftube1st = 0
            try:        ftube2nd = float(etube2nd.text().replace(",", "."))
            except:     ftube2nd = 0
            try:        ftube3rd = float(etube3rd.text().replace(",", "."))
            except:     ftube3rd = 0

            # to catch both zero values and illegal entries
            if ftubeDef > 0:     gglobs.Sensitivity[0] = ftubeDef
            else:                efprint("CPM/CPS tube: Illegal Value, >0 required, you entered: ", etubeDef.text())

            if ftube1st > 0:     gglobs.Sensitivity[1] = ftube1st
            else:                efprint("CPM1st/CPS1st tube: Illegal Value, >0 required, you entered: ", etube1st.text())

            if ftube2nd > 0:     gglobs.Sensitivity[2] = ftube2nd
            else:                efprint("CPM2nd/CPS2nd tube: Illegal Value, >0 required, you entered: ", etube2nd.text())

            if ftube3rd > 0:     gglobs.Sensitivity[3] = ftube3rd
            else:                efprint("CPM3rd/CPS3rd tube: Illegal Value, >0 required, you entered: ", etube3rd.text())

            msgfmt = "{:30s}{}"
            # msgDef = msgfmt.format("Def tube:", "{} CPM / (µSv/h)" .format(gglobs.Sensitivity[0]))
            # msg1st = msgfmt.format("1st tube:", "{} CPM / (µSv/h)" .format(gglobs.Sensitivity[1]))
            # msg2nd = msgfmt.format("2nd tube:", "{} CPM / (µSv/h)" .format(gglobs.Sensitivity[2]))
            # msg3rd = msgfmt.format("3rd tube:", "{} CPM / (µSv/h)" .format(gglobs.Sensitivity[3]))
            msgDef = msgfmt.format("Tube CPM/CPS:",       "{} CPM / (µSv/h)" .format(gglobs.Sensitivity[0]))
            msg1st = msgfmt.format("Tube CPM1st/CPS1st:", "{} CPM / (µSv/h)" .format(gglobs.Sensitivity[1]))
            msg2nd = msgfmt.format("Tube CPM2nd/CPS2nd:", "{} CPM / (µSv/h)" .format(gglobs.Sensitivity[2]))
            msg3rd = msgfmt.format("Tube CPM3rd/CPS3rd:", "{} CPM / (µSv/h)" .format(gglobs.Sensitivity[3]))

            fprint(msgDef)
            fprint(msg1st)
            fprint(msg2nd)
            fprint(msg3rd)

            dprint(msgDef)
            dprint(msg1st)
            dprint(msg2nd)
            dprint(msg3rd)

            gsup_plot.makePlot()

        setIndent(0)


    def showDeviceMappings(self):
        """Shows active devices and variables mapped to them and alerts on
        variables being mapped to more than one device"""

        fncname = "showDeviceMappings: "

        fprint(header("Device Mappings"))

        if gglobs.DevicesConnected == 0:
            fprint("Unknown until a connection is made. Use menu: Device -> Connect Devices")
            return

        if gglobs.DevicesConnected > 0 and gglobs.varMapCountTotal == 0:
            efprint("<b>WARNING: </b>No mapped variables found although a device is connected.\
                     \nLogging will not be possible! Please check configuration if this is unexpected !")
            return

        fprint("Mappings as configured in GeigerLog's configuration file geigerlog.cfg.")

        BadMappingFlag = False
        for vname in gglobs.varsCopy:
            if gglobs.varMapCount[vname] > 1:
                if BadMappingFlag == False:    # print only on first occurence
                    efprint("<b>WARNING: </b>Mapping problem of Variables")
                qefprint("Variable {}".format(vname), "is mapped to more than one device")
                BadMappingFlag = True

        dline = "{:10s}: {:4s} {:4s} {:6s} {:6s} {:6s} {:6s} {:6s} {:6s} {:5s} {:5s} {:5s} {:5s}"
        fprint("\n" + dline.format("Device", *list(gglobs.varsCopy)))
        fprint("-" * 86)
        for DevName in gglobs.Devices:              # Device?
            checklist = []
            if gglobs.Devices[DevName][ACTIV]:      # connected?
                checklist.append(DevName)
                for vname in gglobs.varsCopy:       # Var?
                    try:
                        if vname in gglobs.Devices[DevName][VNAME]: checklist.append("M")
                        else:                                       checklist.append("-")
                    except:
                        checklist.append("?")
                fprint(dline.format(*checklist))

        if BadMappingFlag:
            # Mapping is bad
            msg  = "<b>INFO: </b>"
            msg += "Measurements are made on devices from top to bottom, and for each from left to<br>"
            msg += "right. If double-mapping of variables occurs, then the last measured variable will<br>"
            msg += "overwrite the previous one, almost always resulting in useless data. "
            fprintInColor(msg, "blue")

        else:
            # Mapping is good
            fprintInColor("Mapping is valid", "green")
            playWav("ok")


    def fprintDeviceInfo(self, DevName, extended=False):
        """prints basic / extended info on the device DevName"""
        # called ONLY from the menu or the device toolbar button


        fncname = "fprintDeviceInfo: "
        dprint(fncname + "DevName: {:10s}, extended: {}".format(DevName, extended))
        setIndent(1)
        setBusyCursor()

        txt = DevName + " Device Info"
        if extended:  txt += " Extended"
        fprint(header(txt))

        if   DevName == "GMC"         : info = gdev_gmc         .getInfoGMC        (extended=extended)
        elif DevName == "Audio"       : info = gdev_audio       .getInfoAudio      (extended=extended)
        elif DevName == "RadMon"      : info = gdev_radmon      .getInfoRadMon     (extended=extended)
        elif DevName == "AmbioMon"    : info = gdev_ambiomon    .getInfoAmbioMon   (extended=extended)
        elif DevName == "GammaScout"  : info = gdev_gscout      .getInfoGammaScout (extended=extended)

        elif DevName == "I2C"         : info = gdev_i2c         .getInfoI2C        (extended=extended)
        elif DevName == "LabJack"     : info = gdev_labjack     .getInfoLabJack    (extended=extended)
        elif DevName == "Simul"       : info = gdev_simul       .getInfoSimul      (extended=extended)
        elif DevName == "MiniMon"     : info = gdev_minimon     .getInfoMiniMon    (extended=extended)
        elif DevName == "Manu"        : info = gdev_manu        .getInfoManu       (extended=extended)
        elif DevName == "WiFiClient"  : info = gdev_wificlient  .getInfoWiFiClient (extended=extended)
        elif DevName == "WiFiServer"  : info = gdev_wifiserver  .getInfoWiFiServer (extended=extended)

        elif DevName == "RaspiPulse"  : info = gdev_raspipulse  .getInfoRaspiPulse (extended=extended)
        elif DevName == "RaspiI2C"    : info = gdev_raspii2c    .getInfoRaspiI2C   (extended=extended)

        elif DevName == "Rad Pro"     : info = gdev_radpro      .getInfoRadPro     (extended=extended)

        else:                           info = "incorrect Device Name '{}'".format(DevName)

        fprint(info)
        cdprint("\n" + info)

        setIndent(0)
        setNormalCursor()


    def toggleDeviceConnection(self):
        """if no connection exists, then make connection else disconnect"""

        if gglobs.logging:
            self.showStatusMessage("Cannot change when logging! Stop logging first")
            return

        if gglobs.DevicesConnected == 0:    self.switchAllConnections(new_connection="ON")
        else:                               self.switchAllConnections(new_connection="OFF")


    def switchAllConnections(self, new_connection="ON"):
        """
        if new_connection == ON:    if no connection exists, then try to make connection
                                    (with verification of communication with device)
        if new_connection == OFF:   if connection does exist, then disconnect
        """

        fncname = "switchAllConnections: "

        if gglobs.logging:
            self.showStatusMessage("Cannot change when logging! Stop logging first")
            return

        self.setBusyCursor()

        dprint(fncname + "--> {}. ".format(new_connection))
        setIndent(1)

        #
        # Connect / Dis-Connect all devices which are activated
        #
        for DevName in gglobs.Devices:
            if gglobs.Devices[DevName][ACTIV]:
                self.switchDeviceConnection (DevName, new_connection=new_connection)
                QtUpdate()

        #
        # Print all Devices and their states
        #
        gglobs.DevicesActivated = 0
        gglobs.DevicesConnected = 0
        dprint(fncname + "Device Status:")
        setIndent(1)
        for i, DevName in enumerate(gglobs.Devices):
            DevVars      = gglobs.Devices[DevName][VNAME]           # var names with this device
            DevActvState = gglobs.Devices[DevName][ACTIV]           # device activated?
            DevConnState = gglobs.Devices[DevName][CONN]            # device connected?

            if DevActvState:  gglobs.DevicesActivated += 1
            if DevConnState:  gglobs.DevicesConnected += 1
            if DevVars is not None:    svs = ", ".join(DevVars)     # the variables
            else:                      svs = "None"
            dprint("   Device #{:<2d}: {:10s}  Activation: {:6s} Connection: {}{:6s}  Vars: {}".
                    format(i, DevName, str(DevActvState), TGREEN if DevConnState else "", str(DevConnState), svs), TDEFAULT)

        dprint("   Devices Activated: {}".format(gglobs.DevicesActivated))
        dprint("   Devices Connected: {}".format(gglobs.DevicesConnected))
        setIndent(0)

        if gglobs.DevicesActivated == 0:
            self.setNormalCursor()
            self.warnMissingDeviceActivations()

        #
        # set plug-icon green on at least 1 connected device
        #
        if gglobs.DevicesConnected > 0: plugicon = 'icon_plug_closed.png'   # green icon
        else:                           plugicon = 'icon_plug_open.png'     # red icon
        self.toggleDeviceConnectionAction.setIcon(QIcon(QPixmap(os.path.join(gglobs.gresPath, plugicon))))

        #
        # determine the mapping and active variables on new connections
        #
        if new_connection == "ON" and gglobs.DevicesConnected > 0:
            gglobs.varMapCountTotal = 0
            for vname   in gglobs.varsCopy:  gglobs.varMapCount[vname] = 0
            for DevName in gglobs.Devices:   gglobs.DevVarsAsText[DevName] = None

            # Scan all devices for loggable variables
            for DevName in gglobs.Devices:                                  # scan all devices
                # rdprint("DevName: ", DevName)
                if gglobs.Devices[DevName][VNAME] != None:                  # use only those with variables named
                    tmpDevVarsAsText = ""
                    for vname in gglobs.Devices[DevName][VNAME]:            # scan all vars of this device
                        # rdprint("                  : vname: ", vname)
                        if vname == "Unused" or vname == "auto" or vname == "None": continue
                        gglobs.varMapCount[vname]   += 1
                        gglobs.varMapCountTotal     += 1
                        tmpDevVarsAsText            += " {}".format(vname)  # like: CPM1st CPS1st CPM2nd ...
                        gglobs.varsSetForLogNew[vname] = True               # and mark them active for this log
                        gglobs.varsSetForLog.update({vname : True})
                        gglobs.varChecked4PlotLog   [vname] = True

                    gglobs.DevVarsAsText[DevName] = tmpDevVarsAsText.strip() # like: {'GMC': 'CPM1st CPS1st CPM2nd CPS2nd Humid', 'Audio': None,

            self.showDeviceMappings()

        # cleanup
        self.checkLoggingState()

        setIndent(0)
        self.setNormalCursor()


    def setStyleSheetTBButton(self, button, stylesheetflag):
        """set toolbar button of devices to grey, green, red, or yellow"""

        if   stylesheetflag == "ON"    : button.setStyleSheet(self.dbtnStyleSheetON)        # green
        elif stylesheetflag == "OFF"   : button.setStyleSheet(self.dbtnStyleSheetOFF)       # grey
        elif stylesheetflag == "ERR"   : button.setStyleSheet(self.dbtnStyleSheetError)     # red
        elif stylesheetflag == "SIM"   : button.setStyleSheet(self.dbtnStyleSheetSimul)     # yellow - simulation


    def initDevice(self, DevName):
        """init the device DevName"""

        # NOTE: errmsg will be "" unless there was an error in an initXYZ

        fncname = "initDevice: " + DevName
        dprint(fncname)
        setIndent(1)

        if   DevName == "GMC":          errmsg = gdev_gmc       .initGMC()
        elif DevName == "Audio":        errmsg = gdev_audio     .initAudio()
        elif DevName == "RadMon":       errmsg = gdev_radmon    .initRadMon()
        elif DevName == "AmbioMon":     errmsg = gdev_ambiomon  .initAmbioMon()
        elif DevName == "GammaScout":   errmsg = gdev_gscout    .initGammaScout()
        elif DevName == "I2C":          errmsg = gdev_i2c       .initI2C()
        elif DevName == "LabJack":      errmsg = gdev_labjack   .initLabJack()
        elif DevName == "Simul":        errmsg = gdev_simul     .initSimul()
        elif DevName == "MiniMon":      errmsg = gdev_minimon   .initMiniMon()
        elif DevName == "Manu":         errmsg = gdev_manu      .initManu()
        elif DevName == "WiFiClient":   errmsg = gdev_wificlient.initWiFiClient()
        elif DevName == "WiFiServer":   errmsg = gdev_wifiserver.initWiFiServer()
        elif DevName == "RaspiPulse":   errmsg = gdev_raspipulse.initRaspiPulse()
        elif DevName == "RaspiI2C":     errmsg = gdev_raspii2c  .initRaspiI2C()
        elif DevName == "Rad Pro":      errmsg = gdev_radpro    .initRadPro()

        setIndent(0)
        return errmsg


    def terminateDevice(self, DevName):
        """terminate the device DevName"""

        # errmsg is "" unless there was an error in an terminateXYZ

        if   DevName == "GMC":          errmsg = gdev_gmc       .terminateGMC()
        elif DevName == "Audio":        errmsg = gdev_audio     .terminateAudio()
        elif DevName == "RadMon":       errmsg = gdev_radmon    .terminateRadMon()
        elif DevName == "AmbioMon":     errmsg = gdev_ambiomon  .terminateAmbioMon()
        elif DevName == "GammaScout":   errmsg = gdev_gscout    .terminateGammaScout()
        elif DevName == "I2C":          errmsg = gdev_i2c       .terminateI2C()
        elif DevName == "LabJack":      errmsg = gdev_labjack   .terminateLabJack()
        elif DevName == "Simul":        errmsg = gdev_simul     .terminateSimul()
        elif DevName == "MiniMon":      errmsg = gdev_minimon   .terminateMiniMon()
        elif DevName == "Manu":         errmsg = gdev_manu      .terminateManu()
        elif DevName == "WiFiClient":   errmsg = gdev_wificlient.terminateWiFiClient()
        elif DevName == "WiFiServer":   errmsg = gdev_wifiserver.terminateWiFiServer()
        elif DevName == "RaspiPulse":   errmsg = gdev_raspipulse.terminateRaspiPulse()
        elif DevName == "Rad Pro":      errmsg = gdev_radpro    .terminateRadPro()

        return errmsg


    def setEnableDeviceActions(self, new_enable=True, device="", stylesheetflag="ON"):
        """Dis/Enable device specific device actions"""

        # Device
        self.DeviceConnectAction.        setEnabled(not new_enable)
        self.DeviceDisconnectAction.     setEnabled(new_enable)
        self.setLogTimingAction.         setEnabled(new_enable)

        # GMC counter
        if device == "GMC":
            self.GMCInfoActionExt.       setEnabled(new_enable)
            self.GMCConfigMemoryAction.  setEnabled(new_enable)
            self.GMCConfigEditAction.    setEnabled(new_enable)
            self.GMCSetTimeAction.       setEnabled(new_enable)
            self.GMCEraseSavedDataAction.setEnabled(new_enable)
            self.GMCREBOOTAction.        setEnabled(new_enable)
            self.GMCFACTORYRESETAction.  setEnabled(new_enable)
            self.GMCONAction.            setEnabled(new_enable)
            self.GMCOFFAction.           setEnabled(new_enable)

            # # GMC Device functions using the config
            # replaced by setGMCconfiguration()
            # self.GMCSpeakerONAction.     setEnabled(new_enable)
            # self.GMCSpeakerOFFAction.    setEnabled(new_enable)
            # self.GMCAlarmONAction.       setEnabled(new_enable)
            # self.GMCAlarmOFFAction.      setEnabled(new_enable)
            # self.GMCSavingStateAction.   setEnabled(new_enable)

            #toolbar GMC Power Toggle
            self.dbtnGMCPower.           setEnabled(new_enable)

            # History
            self.histGMCDeviceAction.    setEnabled(new_enable)

            self.setStyleSheetTBButton(self.dbtnGMC, stylesheetflag)
            self.setGMCPowerIcon()

        # AudioCounter
        elif device == "Audio":
            self.AudioInfoActionExt .setEnabled(new_enable)             # extended info
            self.AudioPlotAction    .setEnabled(new_enable)             # audio plotting
            self.AudioSignalAction  .setEnabled(new_enable)             # audio raw signal
            self.AudioEiaAction     .setEnabled(new_enable)             # audio eia action

            self.setStyleSheetTBButton(self.dbtnAudio, stylesheetflag)

        # RadMon
        elif device == "RadMon":
            self.RMInfoActionExt.setEnabled(new_enable)                 # enable extended info
            self.setStyleSheetTBButton(self.dbtnRM, stylesheetflag)

        # AmbioMon
        elif device == "AmbioMon":
            #needed???
            self.histAMDeviceCAMAction.  setEnabled(new_enable)
            self.histAMDeviceCPSAction.  setEnabled(new_enable)
            self.AmbioDataModeAction.    setEnabled(new_enable)
            self.AmbioInfoActionExt.     setEnabled(new_enable)         # enable extended info
            self.setStyleSheetTBButton(self.dbtnAmbio, stylesheetflag)

        # Gamma-Scout counter
        elif device == "GammaScout":
            self.histGSDeviceAction.    setEnabled(new_enable)
            self.GSInfoActionExt.       setEnabled(new_enable)          # enable extended info
            self.GSResetAction.         setEnabled(new_enable)          # enable reset
            self.GSSetPCModeAction.     setEnabled(new_enable)          # enable PC Mode
            self.GSDateTimeAction.      setEnabled(new_enable)          # enable set DateTime
            if gglobs.GS_DeviceDetected == "Online":
                self.GSSetOnlineAction. setEnabled(new_enable)          # enable Online mode
                self.GSRebootAction.    setEnabled(new_enable)          # enable Reboot
            else:
                self.GSSetOnlineAction.     setEnabled(False)           # set True if "online" device
                self.GSRebootAction.        setEnabled(False)           # or leave false

            self.setStyleSheetTBButton(self.dbtnGS, stylesheetflag)

        # I2C
        elif device == "I2C":                                           # I2C
            self.I2CInfoActionExt.          setEnabled(new_enable)      #   extended info
            self.I2CScanAction.             setEnabled(new_enable)      #   can scan only when not logging
            self.I2CForceCalibAction.       setEnabled(new_enable)      #   can calibrate only when not logging
            self.I2CResetAction.            setEnabled(new_enable)      #   can reset only when not logging
            # self.I2CSerialAction.           setEnabled(new_enable)    #   always enabled
            self.setStyleSheetTBButton(self.dbtnI2C, stylesheetflag)

        # LabJack
        elif device == "LabJack":
            self.LJInfoActionExt.setEnabled(new_enable)                     # enable extended info
            self.setStyleSheetTBButton(self.dbtnLJ, stylesheetflag)

        # MiniMon
        elif device == "MiniMon":
            self.setStyleSheetTBButton(self.dbtnMiniMon, stylesheetflag)

        # Simul
        elif device == "Simul":
            self.SimulSettings.setEnabled(new_enable)                       # enable settings
            self.setStyleSheetTBButton(self.dbtnSimul, stylesheetflag)

        # Manu
        elif device == "Manu":
            # self.ManuInfoActionExt.setEnabled(new_enable)                 # enable extended info
            self.ManuValAction.setEnabled(new_enable)                       # enable manual data entry
            self.setStyleSheetTBButton(self.dbtnManu, stylesheetflag)

        # WiFiServer
        elif device == "WiFiServer":
            self.WiFiInfoActionExt.setEnabled(new_enable)                   # enable extended info
            self.setStyleSheetTBButton(self.dbtnWServer, stylesheetflag)

        # WiFiClient
        elif device == "WiFiClient":
            # self.WiFiClientInfoActionExt.setEnabled(new_enable)           # enable extended info
            self.setStyleSheetTBButton(self.dbtnWClient, stylesheetflag)

        # RaspiPulse
        elif device == "RaspiPulse":
            self.RaspiPulseInfoActionExt.setEnabled(new_enable)             # enable extended info
            self.setStyleSheetTBButton(self.dbtnRPulse, stylesheetflag)

        # RaspiI2C
        elif device == "RaspiI2C":
            self.RaspiI2CInfoActionExt.setEnabled(new_enable)               # enable extended info
            self.setStyleSheetTBButton(self.dbtnRI2C, stylesheetflag)

        # Rad Pro
        elif device == "Rad Pro":
            self.histRadProLoadNewAction.setEnabled(new_enable)             # enable load new history
            self.histRadProLoadAllAction.setEnabled(new_enable)             # enable load all history
            self.setStyleSheetTBButton(self.dbtnRadPro, stylesheetflag)


    # GENERIC
    def switchDeviceConnection(self, DevName, new_connection = "ON"):
        """generic handler for connections"""

        fncname = "switchDeviceConnection: "

        dprint(fncname + "Device: {} --> {}. ".format(DevName, new_connection))
        setIndent(1)

        self.setBusyCursor()

        #
        # INIT
        #
        if new_connection == "ON":
            fprint(header("Connect {} Device".format(DevName)))
            QtUpdate()

            if gglobs.Devices[DevName][CONN]:
                fprint("Already connected")
                self.fprintDeviceInfo(DevName)
            else:
                errmsg = self.initDevice(DevName)
                if gglobs.Devices[DevName][CONN] :
                    # successful connect
                    if   errmsg == "":    self.setEnableDeviceActions(new_enable = True, device=DevName, stylesheetflag="ON")
                    elif errmsg == "SIM": self.setEnableDeviceActions(new_enable = True, device=DevName, stylesheetflag="SIM")
                    fprintInColor("Device successfully connected", "green")
                    gdprint(fncname + "Status: ON: for device: {}".format(gglobs.Devices[DevName][DNAME]))

                else:
                    # failure connecting
                    self.setEnableDeviceActions(new_enable = False, device=DevName, stylesheetflag="ERR")
                    msg = "Failure connecting with Device: '{}' for reason:\n\"{}\"".format(DevName, errmsg) # tuple of 2 parts
                    efprint(msg)
                    edprint((fncname + "Status: " + msg).replace("\n", " "))

        #
        # TERMINATE
        #
        else: # new_connection == OFF
            fprint(header("Disconnect {} Device".format(DevName)))
            if not gglobs.Devices[DevName][CONN]:
                # is already de-connected
                fprint("No connected {} Device".format(DevName))
                self.setEnableDeviceActions(new_enable=False, device=DevName, stylesheetflag="OFF")

            else:
                # is connected; now deconnecting
                errmsg = self.terminateDevice(DevName)
                if not gglobs.Devices[DevName][CONN] :
                    # successful dis-connect
                    msg = "Device {} successfully disconnected".format(DevName)
                    fprint(msg)
                    gdprint(msg)
                    self.setEnableDeviceActions(new_enable=False, device=DevName, stylesheetflag="OFF")
                else:
                    # failure dis-connecting
                    self.setEnableDeviceActions(new_enable=False, device=DevName, stylesheetflag="ERR")
                    efprint("Failure disconnecting:", "'{}'".format(gglobs.Devices[DevName][0] ), debug=True)
                    qefprint(errmsg)
                    edprint(errmsg)

        self.setNormalCursor()
        setIndent(0)


    def checkLoggingState(self):
        """enabling and disabling menu and toolbar entries"""

        # Logging
        if gglobs.logging:
            self.logLoadFileAction.             setEnabled(False)  # no loading of log files during logging
            self.logLoadCSVAction .             setEnabled(False)  # no loading of CSV log files during logging
            self.startloggingAction.            setEnabled(False)  # no start logging - it is running already
            self.stoploggingAction.             setEnabled(True)   # stopping is possible
            self.quickLogAction.                setEnabled(False)  # no quickstart of logging - it is running already
            self.logSnapAction.                 setEnabled(True)   # snaps are possible only during logging

            if gglobs.Devices["GMC"][ACTIV]:                       # GMC
                self.histGMCDeviceAction.       setEnabled(False)  #   no downloads during logging

                self.GMCInfoActionExt.          setEnabled(False)  #
                self.GMCConfigEditAction.       setEnabled(False)  #
                self.GMCConfigMemoryAction.     setEnabled(False)  #
                self.GMCSetTimeAction.          setEnabled(False)  #
                self.GMCEraseSavedDataAction.   setEnabled(False)  #
                self.GMCREBOOTAction.           setEnabled(False)  #
                self.GMCFACTORYRESETAction.     setEnabled(False)  #
                self.GMCONAction.               setEnabled(False)
                self.GMCOFFAction.              setEnabled(False)
                self.GMCSerialAction.           setEnabled(False)  #


            if gglobs.Devices["Audio"][ACTIV]:                     # Audio is activated; may NOT be connected
                self.AudioInfoActionExt.        setEnabled(True)   #
                self.AudioSignalAction.         setEnabled(False)  # audio raw signal
                self.AudioPlotAction.           setEnabled(False)
                self.AudioEiaAction.            setEnabled(False)  # audio eia action


            if gglobs.Devices["GammaScout"][ACTIV]:                # GammaScout
                self.histGSDeviceAction.        setEnabled(False)  #   no downloads during logging
                self.GSSerialAction.            setEnabled(False)  #   no serial port settings during logging

                self.GSResetAction.             setEnabled(False)  #   disable reset
                self.GSSetPCModeAction.         setEnabled(False)  #   disable PC Mode
                self.GSDateTimeAction.          setEnabled(False)  #   disable set DateTime
                self.GSSerialAction.            setEnabled(False)  #


            if gglobs.Devices["AmbioMon"][ACTIV]:                  # AmbioMon
                self.histAMDeviceCAMAction.     setEnabled(False)  #   no downloads during logging
                self.histAMDeviceCPSAction.     setEnabled(False)  #   no downloads during logging


            if gglobs.Devices["I2C"][ACTIV] :                      # I2C - Activated
                self.I2CScanAction.             setEnabled(False)  #   can scan only when not logging
                self.I2CForceCalibAction.       setEnabled(False)  #   can calibrate only when not logging
                self.I2CResetAction.            setEnabled(False)  #   can reset only when not logging
                self.I2CSerialAction.           setEnabled(False)  #


            if gglobs.Devices["Manu"][ACTIV] :                      # Manu - Activated
                self.ManuValAction.             setEnabled(True)  #   can enter data only when logging

        # Not Logging
        else:
            self.logLoadFileAction.             setEnabled(True)   # can load log files
            self.logLoadCSVAction.              setEnabled(True)   # can load CSV log files
            self.startloggingAction.            setEnabled(True)   # can start logging (GMC powering need will be excluded later)
            self.stoploggingAction.             setEnabled(False)  # cannot stop - it is not running
            self.quickLogAction.                setEnabled(True)   # quickstart is possible (GMC powering need will be excluded later)
            self.logSnapAction.                 setEnabled(False)  # cannot take snaps when not logging

            if gglobs.Devices["GMC"][ACTIV] \
                and gglobs.Devices["GMC"][CONN]:                   # GMC - Activated AND Connected

                self.histGMCDeviceAction.       setEnabled(True)   #   can download from device when not logging even if powered off
                if gdev_gmc.isGMC_PowerOn(True) == "OFF" and gglobs.DevicesConnected == 1:  # GMC is NOT powered ON and is only device
                    self.startloggingAction.    setEnabled(False)  #   cannot start logging without power and no other devices connected
                    self.quickLogAction.        setEnabled(False)  #   quickstart is NOT possible without power and no other devices connected

                self.GMCInfoActionExt.          setEnabled(True)   #
                self.GMCConfigEditAction.       setEnabled(True)   #
                self.GMCConfigMemoryAction.     setEnabled(True)   #
                self.GMCSetTimeAction.          setEnabled(True)   #
                self.GMCEraseSavedDataAction.   setEnabled(True)   #
                self.GMCREBOOTAction.           setEnabled(True)   #
                self.GMCFACTORYRESETAction.     setEnabled(True)   #
                self.GMCSerialAction.           setEnabled(True)   #
                self.GMCONAction.               setEnabled(True)
                self.GMCOFFAction.              setEnabled(True)

            if gglobs.Devices["Audio"][ACTIV]:                     # Audio is activated; may NOT be connected
                self.AudioInfoActionExt.        setEnabled(True)   #
                self.AudioSignalAction.         setEnabled(True)   # audio raw signal
                self.AudioPlotAction.           setEnabled(True)
                self.AudioEiaAction.            setEnabled(True)   # audio eia action

            if gglobs.Devices["GammaScout"][ACTIV]:                # GammaScout is activated; may NOT be connected
                self.GSSerialAction.            setEnabled(True)   #

            if gglobs.Devices["GammaScout"][ACTIV] \
                and gglobs.Devices["GammaScout"][CONN]:            # GammaScout - is activated AND Connected

                self.histGSDeviceAction.        setEnabled(True)   #   can download from device when not logging

                self.GSResetAction.             setEnabled(True)   #   enable reset
                self.GSSetPCModeAction.         setEnabled(True)   #   enable PC Mode
                self.GSDateTimeAction.          setEnabled(True)   #   enable set DateTime
                self.GSSerialAction.            setEnabled(True)   #

            if gglobs.Devices["AmbioMon"][ACTIV]:                  # AmbioMon
                self.histAMDeviceCAMAction.     setEnabled(True)   #   can download from device when not logging
                self.histAMDeviceCPSAction.     setEnabled(True)   #   can download from device when not logging

            if gglobs.Devices["I2C"][ACTIV] \
                and gglobs.Devices["I2C"][CONN]:                   # I2C - Activated AND Connected:                       # I2C
                self.I2CScanAction.             setEnabled(True)   #   can scan only when not logging AND connected
                self.I2CForceCalibAction.       setEnabled(True)   #   can calibrate only when not logging AND connected
                self.I2CResetAction.            setEnabled(True)   #   can reset only when not logging AND connected
                self.I2CSerialAction.           setEnabled(True)   #   can set serial when Activated

            if gglobs.Devices["Manu"][ACTIV] :                     # Manu - Activated
                self.ManuValAction.             setEnabled(False)  #   can enter data only when logging

            if gglobs.logDBPath == None:
                self.startloggingAction.        setEnabled(False)  # no log file loaded, cannot start logging

            if gglobs.DevicesConnected == 0:                       # no connected devices
                self.quickLogAction.            setEnabled(False)  #   no quick Log
                self.startloggingAction.        setEnabled(False)  #   no start log

        # adding Log comments allowed when a file is defined
        if gglobs.logDBPath != None:    self.addCommentAction.      setEnabled(True)
        else:                           self.addCommentAction.      setEnabled(False)

        # adding History comments allowed when a file is defined
        if gglobs.hisDBPath != None:    self.addHistCommentAction.  setEnabled(True)
        else:                           self.addHistCommentAction.  setEnabled(False)

        # general add comment button enabled if either Log or Hist file is available
        if gglobs.logDBPath != None or gglobs.hisDBPath != None: self.btnAddComment.setEnabled(True)    # either or both DBs are loaded
        else:                                                    self.btnAddComment.setEnabled(False)   # neither DB is loaded

        # general empty Log File button enabled if either Log or Hist file is available
        if gglobs.logDBPath != None or gglobs.hisDBPath != None: self.btnClearLogfile.setEnabled(True)    # either or both DBs are loaded
        else:                                                    self.btnClearLogfile.setEnabled(False)   # neither DB is loaded


    def toggleGMCPower(self):
        """Toggle GMC device Power ON / OFF"""

        if gglobs.logging:
            self.showStatusMessage("Cannot change power when logging! Stop logging first")
            return

        if gdev_gmc.isGMC_PowerOn(True) == "ON": self.switchGMCPower("OFF")
        else:                                    self.switchGMCPower("ON")


    def switchGMCPower(self, newstate="ON"):
        """Switch power of GMC device to ON or OFF"""

        fncname = "switchGMCPower: "
        self.setBusyCursor()

        dprint(fncname + "--> {}".format(newstate))
        setIndent(1)

        fprint(header("Switch GMC Device Power"))
        QtUpdate()

        # faster to set Power than first reading config to check whether necessary
        if newstate == "ON":
            # set power "ON"
            gdev_gmc.setGMC_POWERON()

        else:
            # set power "OFF"
            if gglobs.logging: self.stopLogging()
            gdev_gmc.setGMC_POWEROFF()

        # set getconfig=True to read config after power change
        ipo = self.setGMCPowerIcon(getconfig=True)

        fprint("Current Power State: GMC Power is ", ipo)

        self.checkLoggingState()
        self.setNormalCursor()
        setIndent(0)


    def setGMCPowerIcon(self, getconfig=False):

        ipo = gdev_gmc.isGMC_PowerOn(getconfig=getconfig)

        if   ipo == "ON":   self.dbtnGMCPower.setIcon(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_power-round_on.png'))))
        elif ipo == "OFF":  self.dbtnGMCPower.setIcon(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_power-round_off.png'))))
        else:               self.dbtnGMCPower.setIcon(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_power-round_on.png'))))

        return ipo


#help
    def helpQuickStart(self):
        """Quickstart item on the Help menu"""

        msg = QMessageBox()
        msg.setWindowIcon(self.iconGeigerLog)
        msg.setWindowTitle("Help - Quickstart")
        msg.setText(gglobs.helpQuickstart)

        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        msg.setEscapeButton(QMessageBox.Ok)
        msg.setWindowModality(Qt.WindowModal)
        msg.setMinimumWidth(800)
        msg.setStyleSheet("QLabel{min-width:700px; font-size:12pt;}")

        msg.exec()


    def helpFirmwareBugs(self):
        """Geiger Counter Firmware Bugs info on the Help menu"""

        msg = QMessageBox()
        msg.setWindowIcon(self.iconGeigerLog)
        msg.setWindowTitle("Help - Firmware Bugs")
        msg.setTextFormat(Qt.RichText)
        msg.setText(gglobs.helpFirmwareBugs)

        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        msg.setEscapeButton(QMessageBox.Ok)
        msg.setWindowModality(Qt.WindowModal)
        msg.setStyleSheet("QLabel{min-width:700px; font-size:11pt;}")
        msg.setMinimumWidth(800)

        msg.exec()


    def helpWorldMaps(self):
        """Using the Radiation World Map"""

        msg = QMessageBox()
        msg.setWindowIcon(self.iconGeigerLog)
        msg.setWindowTitle("Help - Radiation World Maps")
        msg.setText(gglobs.helpWorldMaps)

        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        msg.setEscapeButton(QMessageBox.Ok)
        msg.setWindowModality(Qt.WindowModal)
        msg.setStyleSheet("QLabel{min-width:700px; font-size:12pt;}")
        msg.setMinimumWidth(800)

        msg.exec()


    def helpOccupationalRadiation(self):
        """Occupational Radiation Limits"""

        msg = QMessageBox()
        msg.setWindowIcon(self.iconGeigerLog)
        msg.setWindowTitle("Help - Occupational Radiation Limits")
        msg.setText(gglobs.helpOccupationalRadiation)

        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        msg.setEscapeButton(QMessageBox.Ok)
        msg.setWindowModality(Qt.WindowModal)
        msg.setStyleSheet("QLabel{min-width:700px; font-size:12pt;}")
        msg.setMinimumWidth(800)

        msg.exec()


    def helpOptions(self):
        """Options item on the Help menu"""

        msg = QMessageBox()
        msg.setWindowIcon(self.iconGeigerLog)
        msg.setWindowTitle("Help - Command Line Options")
        msg.setFont(self.fontstd)   # required! must det to plain text, not HTML
        msg.setText(gglobs.helpOptions)

        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        msg.setEscapeButton(QMessageBox.Ok)
        msg.setWindowModality(Qt.WindowModal)
        msg.setStyleSheet("QLabel{min-width:800px; font-size:12pt;}")
        msg.setMinimumWidth(800)

        msg.exec()


    def helpAbout(self):
        """About item on the Help menu"""

        # the curly brackets {} used for Python's format() don't work when the text has
        # CSS formatting using {}!
        # --> solution: use double quotes for what is NOT part of format (i.e. for the CSS)
        description = gglobs.helpAbout.format(__author__, gglobs.__version__, __copyright__, __license__)


        p = QPixmap(os.path.join(gglobs.gresPath, 'icon_geigerlog.png')) # the icon is 512 x 512
        w = 100
        h = 100
        licon   = QLabel()                                  # label to hold the geigerlog icon
        licon.setPixmap(p.scaled(w,h,Qt.KeepAspectRatio))   # set a scaled pixmap to a w x h window keeping its aspect ratio

        ltext   = QLabel()                                  # label to hold the 'eigerlog' text as picture
        ltext.setPixmap(QPixmap(os.path.join(gglobs.gresPath, 'eigerlog.png')))

        labout  = QTextBrowser() # label to hold the description
        labout.setLineWrapMode(QTextEdit.WidgetWidth)
        labout.setText(description)
        labout.setOpenExternalLinks(True) # to open links in a browser
        labout.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)
        labout.setMaximumWidth(800) # set the width:

        d = QDialog()
        d.setWindowIcon(self.iconGeigerLog)
        d.setWindowTitle("Help - About GeigerLog")
        d.setWindowModality(Qt.WindowModal)
        d.setMaximumWidth(800)
        d.setMinimumWidth(750)
        screen_available = QDesktopWidget().availableGeometry()
        d.setMinimumHeight(min(screen_available.height(), gglobs.window_height + 220))

        bbox      = QDialogButtonBox()
        bbox.setStandardButtons(QDialogButtonBox.Ok)
        bbox.accepted.connect(lambda: d.done(0))

        layoutTop = QHBoxLayout()
        layoutTop.addWidget(licon)
        layoutTop.addWidget(ltext)
        layoutTop.addStretch()      # to keep the icons on the left

        layoutV   = QVBoxLayout(d)
        layoutV.addLayout(layoutTop)
        layoutV.addWidget(labout)
        layoutV.addWidget(bbox)

        d.exec()


    def changeOptions(self):
        """Switches State of some options"""

        fncname = "changeOptions: "

    # left column:

        # debug
        checkD = QCheckBox("Debug")
        checkD.setLayoutDirection(Qt.LeftToRight)
        checkD.setChecked(gglobs.debug)

        # verbose
        checkV = QCheckBox("Verbose")
        checkV.setLayoutDirection(Qt.LeftToRight)
        checkV.setChecked(gglobs.verbose)

        # werbose
        checkW = QCheckBox("Werbose")
        checkW.setLayoutDirection(Qt.LeftToRight)
        checkW.setChecked(gglobs.werbose)

    # middle column:

        # devel
        checkL = QCheckBox("Devel")
        checkL.setLayoutDirection(Qt.LeftToRight)
        checkL.setChecked(gglobs.devel)

        # trace
        checkTR = QCheckBox("Trace")
        checkTR.setLayoutDirection(Qt.LeftToRight)
        checkTR.setChecked(gglobs.traceback)
        checkTR.setToolTip("Prints traceback in devel mode")

        # timing
        checkM = QCheckBox("Timing")
        checkM.setLayoutDirection(Qt.LeftToRight)
        checkM.setChecked(gglobs.timing)
        checkM.setToolTip("Writes timing values to Manu device")

    # right column:

        # testing
        checkT = QCheckBox("Testing")
        checkT.setLayoutDirection(Qt.LeftToRight)
        checkT.setChecked(gglobs.testing)
        checkT.setToolTip("Effective only on GMC")

        # gstesting
        checkGS = QCheckBox("GS Testing")
        checkGS.setLayoutDirection(Qt.LeftToRight)
        checkGS.setChecked(gglobs.gstesting)
        checkGS.setToolTip("Effective only on GammaScout")

        # Stattest
        checkS = QCheckBox("Stattest")
        checkS.setLayoutDirection(Qt.LeftToRight)
        checkS.setChecked(gglobs.stattest)
        checkS.setToolTip("Adds Normal statistics to Poisson test")

        # GraphEmphasis
        checkG = QCheckBox("GraphEmphasis")
        checkG.setLayoutDirection(Qt.LeftToRight)
        checkG.setChecked(gglobs.graphemph)
        checkG.setToolTip("Plot lines with full, thick linewidth")


        layoutL = QVBoxLayout()         # left
        layoutL.addWidget(checkD)
        layoutL.addWidget(checkV)
        layoutL.addWidget(checkW)
        layoutL.addWidget(checkTR)
        layoutL.addStretch()

        layoutM = QVBoxLayout()         # middle
        layoutM.addWidget(checkL)
        layoutM.addWidget(checkM)
        layoutM.addStretch()

        layoutR = QVBoxLayout()         # right
        layoutR.addWidget(checkT)
        layoutR.addWidget(checkGS)
        layoutR.addWidget(checkS)
        layoutR.addWidget(checkG)
        layoutR.addStretch()

        layoutB = QHBoxLayout()         # set cols left, middle, right
        layoutB.addLayout(layoutL)
        layoutB.addLayout(layoutM)
        layoutB.addLayout(layoutR)

        bbox = QDialogButtonBox()
        bbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok )
        bbox.accepted.connect(lambda: d.done(100))
        bbox.rejected.connect(lambda: d.done(0))   # ESC key produces 0 (zero)!

        d = QDialog()
        d.setWindowIcon(gglobs.iconGeigerLog)
        d.setWindowTitle("Change Command Line Options")
        d.setWindowModality(Qt.WindowModal)
        d.setMinimumWidth(320)

        layoutV = QVBoxLayout(d)
        layoutV.addLayout(layoutB)
        layoutV.addWidget(bbox)

        retval = d.exec()
        #print("reval:", retval)
        if retval != 100: return

        #
        # The ranking is debug --> verbose --> werbose
        # if any is true, the higher one(s) must also be set true
        # trace requires debug
        if checkD.isChecked():
            gglobs.debug    = True
        else:
            gglobs.debug    = False
            gglobs.verbose  = False
            gglobs.werbose  = False

        if checkV.isChecked():
            gglobs.verbose  = True
            gglobs.debug    = True
        else:
            gglobs.verbose  = False
            gglobs.werbose  = False

        if checkW.isChecked():
            gglobs.werbose  = True
            gglobs.verbose  = True
            gglobs.debug    = True
        else:
            gglobs.werbose  = False


        if checkTR.isChecked():
            gglobs.traceback= True
            gglobs.debug    = True
        else:
            gglobs.traceback= False

        gglobs.devel        = True if checkL.isChecked()  else False
        gglobs.timing       = True if checkM.isChecked()  else False

        gglobs.testing      = True if checkT.isChecked()  else False
        gglobs.gstesting    = True if checkGS.isChecked() else False

        gglobs.stattest     = True if checkS.isChecked()  else False
        gglobs.graphemph    = True if checkG.isChecked()  else False

        fprint(header("Change Command Line Options"))
        setfrmt   = "   {:27s}{}\n"
        settings  = "Current settings:\n"
        settings += setfrmt.format("Debug:",            gglobs.debug)
        settings += setfrmt.format("Verbose:",          gglobs.verbose)
        settings += setfrmt.format("Werbose:",          gglobs.werbose)
        settings += setfrmt.format("Trace:",            gglobs.traceback)
        settings += setfrmt.format("Devel:",            gglobs.devel)
        settings += setfrmt.format("Timing:",           gglobs.timing)
        settings += setfrmt.format("Testing:",          gglobs.testing)
        settings += setfrmt.format("GS Testing:",       gglobs.gstesting)
        settings += setfrmt.format("Stattest:",         gglobs.stattest)
        settings += setfrmt.format("GraphEmphasis:",    gglobs.graphemph)
        fprint(settings)
        dprint(fncname + settings)


    def editScaling(self):
        """shows the current settings of [ValueScaling] and [GraphScaling]"""

        # value
        valueBox=QFormLayout()
        valueBox.setSizeConstraint (QLayout.SetFixedSize)
        valueBox.RowWrapPolicy(QFormLayout.DontWrapRows)
        valueBox.addRow(QLabel("{:60s}".format("<b>ValueScaling</b> - it DOES modify the saved value!<br> ")))
        for vname in gglobs.varsCopy:
            valueBox.addRow(vname, QLineEdit(gglobs.ValueScale[vname]))

        # graph
        graphBox=QFormLayout()
        graphBox.setFieldGrowthPolicy (QFormLayout.ExpandingFieldsGrow)
        graphBox.RowWrapPolicy(QFormLayout.DontWrapRows)
        graphBox.addRow(QLabel("{:60s}".format("<b>GraphScaling</b> - it does NOT modify the saved value, <br>only the plotted value")))
        for vname in gglobs.varsCopy:
            graphBox.addRow(vname, QLineEdit(gglobs.GraphScale[vname]))

        vgLayout = QHBoxLayout()
        vgLayout.addLayout(valueBox)
        vgLayout.addLayout(graphBox)

        self.dialog = QDialog()
        self.dialog.setWindowIcon(self.iconGeigerLog)
        self.dialog.setWindowTitle("View and Edit Current Scaling")
        self.dialog.setWindowModality(Qt.ApplicationModal)
        self.dialog.setMinimumWidth(700)
        self.dialog.setMaximumWidth(1000)

        bbox = QDialogButtonBox()
        bbox.setStandardButtons(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        bbox.accepted.connect(lambda: self.dialog.done(0))
        bbox.rejected.connect(lambda: self.dialog.done(1))

        layoutV = QVBoxLayout(self.dialog)
        layoutV.addWidget(QLabel("See GeigerLog manual in chapter <b>Configuration of GeigerLog</b>, topic <b>Scaling</b>, for guidance<br>"))
        layoutV.addLayout(vgLayout)
        layoutV.addWidget(bbox)

        resultdlg = self.dialog.exec()             # both seem to work the same

        if resultdlg == 0:
            #print("row count: ", valueBox.rowCount(), graphBox.rowCount())
            for i in range(0, len(gglobs.varsCopy) + 1):
                if valueBox.itemAt(i, QFormLayout.LabelRole) is not None:
                    vvname = (valueBox.itemAt(i, QFormLayout.LabelRole).widget().text()).strip()
                    vval   = (valueBox.itemAt(i, QFormLayout.FieldRole).widget().text()).strip().replace(",", ".")
                    wprint("valueBox i: {:2d}  {:10s}  {}".format(i, vvname, vval))
                    gglobs.ValueScale[vvname] = vval

            for i in range(0, len(gglobs.varsCopy) + 1):
                if graphBox.itemAt(i, QFormLayout.LabelRole) is not None:
                    gvname = (graphBox.itemAt(i, QFormLayout.LabelRole).widget().text()).strip()
                    gval   = (graphBox.itemAt(i, QFormLayout.FieldRole).widget().text()).strip().replace(",", ".")
                    wprint("graphBox i: {:2d}  {:10s}  {}".format(i, gvname, gval))
                    gglobs.GraphScale[gvname] = gval

        #print("gglobs.ValueScale: ", gglobs.ValueScale)
        #print("gglobs.GraphScale: ", gglobs.GraphScale)


#utilities in Class

    def clearNotePad(self):
        """Clear the notepad"""

        self.notePad.clear()
        self.notePad.setTextColor(QColor(40, 40, 40))


    def clearLogPad(self):
        """Clear the logPad"""

        self.logPad.clear()


    def setBusyCursor(self):
        "Change cursor to rotating clock"
        QApplication.setOverrideCursor(Qt.WaitCursor)


    def setNormalCursor(self):
        "Change cursor to normal (arrow or insert"
        QApplication.restoreOverrideCursor()


    def showStatusMessage(self, message, timing=0, error=True):
        """shows message by flashing the Status Bar red for 0.5 sec, then switches back to normal"""

        if error == False:
            self.statusBar.setStyleSheet("QStatusBar { }")      # reset to default colors
            self.statusBar.showMessage(message, msecs=timing)   # message remains until overwritten by next status
        else:
            playWav("err")
            self.statusBar.showMessage(message, msecs=timing)   # message remains until overwritten by next status
            self.statusBar.setStyleSheet("QStatusBar { background-color:red; color:white; }")
            QtUpdate()                                         # assure that things are visible
            time.sleep(0.5)                                     # stays red for 0.5 sec
            self.statusBar.setStyleSheet("QStatusBar { }")      # reset to default colors


######## class ggeiger ends ###################################################
