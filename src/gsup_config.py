#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
gsup_config.py - GeigerLog support file to evaluate the configuration

include in programs with:
    import gsup_config
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


def readGeigerLogConfig():
    """reading the configuration file, return if not available.
    Not-available or illegal options are being ignored with only a debug message"""

    ######  local function  ###########################################################
    def getConfigEntry(section, parameter, ptype):
        """utility for readGeigerLogConfig"""

        errmsg  = "\n\n<b>- Configuration File has Problems</b>\n"
        errmsg += "(will continue using defaults):\n\n"

        # print("getConfigEntry: ", section, ", ", parameter, ", ", ptype, end="  ")
        try:
            t = config.get(section, parameter)
            #print(", t: ", t)

            t = t.strip()
            if   ptype == "float":    t = float(t)
            elif ptype == "int":      t = int(float(t))
            elif ptype == "str":      t = t
            elif ptype == "upper":    t = t.upper()

            return t

        except ValueError: # e.g. failure to convert to float
            errmsg += "Section: {}, Parameter: {}\n\nProblem: has wrong value: {}".format(section, parameter, t)
            gglobs.configAlerts += errmsg + "\n\n"
            edprint("WARNING: " + errmsg, debug=True)

            return "WARNING"

        except Exception as e:
            errmsg += "Section: {}, Parameter: {}\n\nProblem: {}".format(section, parameter, e)
            gglobs.configAlerts += errmsg + "\n\n"
            edprint("WARNING: " + errmsg, debug=True)

            return "WARNING"

    ##################################################################################

    fncname = "readGeigerLogConfig: "

    dprint(fncname + "using config file: ", gglobs.configPath)
    setIndent(1)

    infostrHeader = "cfg: {:35s} {}"
    infostr       = "cfg:     {:35s}: {}"
    while True:

    # does the config file exist and can it be read?
        if not os.path.isfile(gglobs.configPath) or not os.access(gglobs.configPath, os.R_OK) :
            msg = """Configuration file <b>'geigerlog.cfg'</b> does not exist or is not readable."""
            edprint(msg, debug=True)
            msg += "<br><br>Please check and correct. Cannot continue, will exit."
            gglobs.startupProblems = msg
            break

    # is it error free?
        try:
            config = configparser.ConfigParser()
            with open(gglobs.configPath) as f:
               config.read_file(f)
        except Exception as e:
            msg = "Configuration file <b>'geigerlog.cfg'</b> cannot be interpreted."
            exceptPrint(e, msg)
            msg += "\n\nNote that duplicate entries are not allowed!"
            msg += "\n\nERROR Message:\n" + str(sys.exc_info()[1])
            msg += "\n\nPlease check and correct. Cannot continue, will exit."
            gglobs.startupProblems = msg.replace("\n", "<br>")
            break

    # the config file exists and can be read:
        dprint(infostrHeader.format("Startup values", ""))


    # Logging
        t = getConfigEntry("Logging", "logCycle", "upper" )
        gglobs.logCycle = 1
        if t != "WARNING":
            if t == "AUTO":                     gglobs.logCycle = 1
            else:
                try:    ft = float(t)
                except: ft = 1
                if      ft >= 0.1:              gglobs.logCycle = ft
                else:                           gglobs.logCycle = 1
        dprint(infostr.format("Logcycle (sec)", gglobs.logCycle))


    # DataDirectory
        t = getConfigEntry("DataDirectory", "DataDir", "str" )
        # edprint("DataDirectory: gglobs.dataPath:", gglobs.dataPath)
        if t != "WARNING":
            errmsg = "WARNING: "
            try:
                if t.upper() == "AUTO":
                    pass                        # no change to default = 'data'
                else:
                    if os.path.isabs(t): testpath = t                           # is it absolute path? yes
                    else:                testpath = gglobs.dataPath + "/" + t   # it is relative path? yes
                    #cdprint("path:", testpath)

                    # Make sure the data directory exists; create it if needed
                    # ignore if it cannot be made or is not writable
                    if os.access(testpath, os.F_OK):
                        # dir exists, ok
                        if not os.access(testpath , os.W_OK):
                            # dir exists, but is not writable
                            errmsg += "Configured data directory '{}' exists, but is not writable".format(testpath)
                            raise NameError
                        else:
                            # dir exists and is writable
                            gglobs.dataPath = testpath
                    else:
                        # dir does not exist; make it
                        try:
                            os.mkdir(testpath)
                            gglobs.dataPath = testpath
                        except:
                            # dir cannot be made
                            errmsg += "Could not make configured data directory '{}'".format(testpath)
                            raise NameError

            except Exception as e:
                dprint(errmsg, "; Exception:", e, debug=True)

        dprint(infostr.format("Data directory", gglobs.dataPath))


    # Manual
        t = getConfigEntry("Manual", "ManualName", "str" )
        if t != "WARNING":
            if t.upper() == 'AUTO' or t == "":
                gglobs.manual_filename = 'auto'
                dprint(infostr.format("Filename GeigerLog Manual", gglobs.manual_filename))
            else:
                manual_file = getProgPath() + "/" + t
                if os.path.isfile(manual_file):     # does the file exist?
                    # it exists
                    gglobs.manual_filename = t
                    dprint(infostr.format("Filename GeigerLog Manual", gglobs.manual_filename))
                else:
                    # it does not exist
                    gglobs.manual_filename = 'auto'
                    dprint("WARNING: Filename GeigerLog Manual '{}' does not exist".format(t))


    # Monitor Server
        dprint(infostrHeader.format("Monitor Server", ""))

        # MonServer Autostart
        t = getConfigEntry("MonServer", "MonServerAutostart", "upper" )
        if t != "WARNING":
            if     t == "NO":                              gglobs.MonServerAutostart = False
            else:                                          gglobs.MonServerAutostart = True
            dprint(infostr.format("MonServer Autostart",   gglobs.MonServerAutostart))

        # MonServer SSL
        t = getConfigEntry("MonServer", "MonServerSSL", "upper" )
        if t != "WARNING":
            if     t == "YES":                             gglobs.MonServerSSL = True
            else:                                          gglobs.MonServerSSL = False
            dprint(infostr.format("MonServer SSL",         gglobs.MonServerSSL))

        # MonServer Port
        t = getConfigEntry("MonServer", "MonServerPort", "upper" )
        if t != "WARNING":
            if t == "AUTO":                                gglobs.MonServerPorts = "auto"
            else:
                default = False
                mspraw = t.split(",")
                # edprint("mspraw: ", mspraw)
                MSPorts = []
                for pn in mspraw:
                    pn = pn.strip()
                    if pn == "":    continue
                    try:
                        tport = int(float(pn))
                        # edprint("tport: ", tport)
                        if 1024 <= tport <= 65535:
                            MSPorts.append(tport)
                        else:
                            default = True
                            break
                    except Exception as e:
                        exceptPrint(e, "MonServerPort has non-numeric value")
                        default = True
                        break

                if default: gglobs.MonServerPorts = "auto"
                else:       gglobs.MonServerPorts = MSPorts

            dprint(infostr.format("MonServer Port",         gglobs.MonServerPorts))

        # MonServer UTC Correction
        t = getConfigEntry("MonServer", "MonServerUTCcorr", "upper" )
        if t != "WARNING":
            if t == "AUTO":                                 gglobs.MonServerUTCcorr = "auto"
            else:
                try:
                    msuc = int(float(t))
                    if -12 * 3600 <= msuc <= +12 * 3600:    gglobs.MonServerUTCcorr = msuc
                    else:                                   gglobs.MonServerUTCcorr = "auto"
                except Exception as e:
                    exceptPrint(e, "MonServerUTCcorr has non-numeric value")
                    gglobs.MonServerUTCcorr = "auto"
            dprint(infostr.format("MonServer UTCcorr",      gglobs.MonServerUTCcorr))

        # MonServerThresholds (low, high)
        t = getConfigEntry("MonServer", "MonServerThresholds", "upper" )
        if t != "WARNING":
            if t == "AUTO":                                         gglobs.MonServerThresholds = "auto"
            else:
                ts = t.split(",")
                if len(ts) == 2:
                    try:
                        lo = float(ts[0])
                        hi = float(ts[1])
                        if lo > 0 and hi > lo:                      gglobs.MonServerThresholds = (lo, hi)
                        else:                                       gglobs.MonServerThresholds = "auto"
                    except:
                        gglobs.MonServerThresholds = "auto"
                else:
                    gglobs.MonServerThresholds = "auto"

            dprint(infostr.format("MonServer Thresholds",   gglobs.MonServerThresholds))

        # MonServerPlotConfig       (Default:  10, 0, 1)
        t = getConfigEntry("MonServer", "MonServerPlotConfig", "upper" )
        if t != "WARNING":
            # edprint("config: t: ", t)
            if t == "AUTO":                                         gglobs.MonServerPlotConfig = "auto"
            else:
                ts = t.split(",")
                # edprint("config: ts: ", ts)
                if len(ts) == 3:
                    try:
                        plotlen = clamp(float(ts[0]), 0.1, 1500)
                        plottop = clamp(int(float(ts[1])), 0, 11)
                        plotbot = clamp(int(float(ts[2])), 0, 11)
                        gglobs.MonServerPlotConfig = (plotlen, plottop, plotbot)
                    except:
                        exceptPrint(e, "config MonServerPlotConfig")
                        gglobs.MonServerPlotConfig = "auto"
                else:
                    gglobs.MonServerPlotConfig = "auto"

            dprint(infostr.format("MonServer PlotConfig",   gglobs.MonServerPlotConfig))

        # MonServerDataConfig       (Default:  1, 3, 10)
        t = getConfigEntry("MonServer", "MonServerDataConfig", "upper" )
        if t != "WARNING":
            # edprint("config: t: ", t)
            if t == "AUTO":                                         gglobs.MonServerDataConfig = "auto"
            else:
                ts = t.split(",")
                # edprint("config: ts: ", ts)
                if len(ts) == 3:
                    try:
                        dataA = clamp(float(ts[0]), 1, 1000)
                        dataB = clamp(float(ts[1]), 2, 1000)
                        dataC = clamp(float(ts[2]), 3, 1000)
                        gglobs.MonServerDataConfig = (dataA, dataB, dataC)
                    except:
                        exceptPrint(e, "config MonServerDataConfig")
                        gglobs.MonServerDataConfig = "auto"
                else:
                    gglobs.MonServerDataConfig = "auto"

            dprint(infostr.format("MonServer DataConfig",   gglobs.MonServerDataConfig))

#inactive ####################
    # #from geigerlog.cfg
    #     # MonServer REFRESH
    #     # This sets the refresh timings for the web pages Monitor, Data, Graph. The
    #     # numbers give the seconds after which the site will be refreshed. Numbers
    #     # must be separated by comma.
    #     #
    #     # Option auto defaults to 1, 10, 3
    #     #
    #     # Options:         auto | < <Monitor Refresh> , <Data Refresh> , <Graph Refresh> >
    #     # Default        = auto
    #     # MonServerRefresh = auto
    #     MonServerRefresh = 1, 10, 1

    # # from here
    #     # # MonServer Refresh
    #     # t = getConfigEntry("MonServer", "MonServerRefresh", "upper" )
    #     # if t != "WARNING":
    #     #     if t == "AUTO":                                 gglobs.MonServerRefresh = "auto"
    #     #     else:
    #     #         ts = t.split(",")
    #     #         try:
    #     #             gglobs.MonServerRefresh[0] = int(ts[0])
    #     #             gglobs.MonServerRefresh[1] = int(ts[1])
    #     #             gglobs.MonServerRefresh[2] = int(ts[2])
    #     #         except Exception as e:
    #     #             exceptPrint(e, "MonServer Refresh defined improperly")
    #     #             gglobs.MonServerRefresh  = "auto"
    #     #     dprint(infostr.format("MonServer Refresh",     gglobs.MonServerRefresh))
# end inactive ####################



    # Window
        dprint(infostrHeader.format("Window", ""))

    # Window HiDPIactivation
        t = getConfigEntry("Window", "HiDPIactivation", "upper" )
        if t != "WARNING":
            if    t == 'AUTO':         gglobs.hidpiActivation = "auto"
            elif  t == 'YES':          gglobs.hidpiActivation = "yes"
            elif  t == 'NO':           gglobs.hidpiActivation = "no"
            else:                      gglobs.hidpiActivation = "auto"
            dprint(infostr.format("Window HiDPIactivation", gglobs.hidpiActivation))

    # Window HiDPIscaleMPL
        t = getConfigEntry("Window", "HiDPIscaleMPL", "upper" )
        if t != "WARNING":
            if    t == 'AUTO':         gglobs.hidpiScaleMPL = "auto"
            try:                       gglobs.hidpiScaleMPL = int(float(t))
            except:                    gglobs.hidpiScaleMPL = "auto"
            dprint(infostr.format("Window HiDPIscaleMPL", gglobs.hidpiScaleMPL))

    # Window dimensions
        w = getConfigEntry("Window", "windowWidth", "int" )
        h = getConfigEntry("Window", "windowHeight", "int" )
        # edprint("Window dimension: ", w, "  ", h)
        if w != "WARNING" and h != "WARNING":
            if w > 500 and w < 5000 and h > 100 and h < 5000:
                gglobs.window_width  = w
                gglobs.window_height = h
                dprint(infostr.format("Window dimensions (pixel)", "{} x {}".format(gglobs.window_width, gglobs.window_height)))
            else:
                dprint("WARNING: Config Window dimension out-of-bound; ignored: {} x {} pixel".format(gglobs.window_width, gglobs.window_height), debug=True)

    # Window Size
        t = getConfigEntry("Window", "windowSize", "upper" )
        if t != "WARNING":
            if    t == 'MAXIMIZED':    gglobs.window_size = 'maximized'
            else:                      gglobs.window_size = 'auto'
            dprint(infostr.format("Window Size ", gglobs.window_size))

    # Window Style
        t = getConfigEntry("Window", "windowStyle", "str" )
        if t != "WARNING":
            available_style = QStyleFactory.keys()
            if t in available_style:    gglobs.windowStyle = t
            else:                       gglobs.windowStyle = "auto"
            dprint(infostr.format("Window Style ", gglobs.windowStyle))

    # WINDOW PAD COLORS cannot be used due to a bug in PyQt5
    # # from the geigerlog.cfg file:
    # # WINDOW PAD COLORS:
    # # Sets the background color of NotePad and LogPad. Default is a
    # # very light green for NotePad, and very light blue for LogPad.
    # # Colors can be given as names (red, green, lightblue,...) - not
    # # all names will work - or #<red><green><blue> with red, green, blue
    # # in HEX notation.
    # # Example: #FFFFFF is pure white, #FF0000 is pure red, #00FF00 is pure green,
    # # #CCCCFF is a blueish grey, and #000000 is pure black.
    # #
    # # Option auto defaults to: '#FaFFFa, #FaFaFF'
    # #
    # # Options:       auto | <color name, color name>
    # # Default      = auto
    # windowPadColor = auto
    # # windowPadColor = #FaFFFa, #e0e0FF
    #
    # # Window Pad Color
    #     t = getConfigEntry("Window", "windowPadColor", "str" )
    #     if t != "WARNING":
    #         if t.upper() == "AUTO":     gglobs.windowPadColor = ("#FaFFFa", "#FaFaFF")
    #         else:
    #             ts = t.split(",")
    #             Np = ts[0].strip()
    #             Lp = ts[1].strip()
    #             gglobs.windowPadColor      = (Np, Lp)
    #         dprint(infostr.format("Window Pad BG-Color ", gglobs.windowPadColor))


    # Graphic
        dprint(infostrHeader.format("Graphic", ""))

        # Graphic MovingAverage
        t = getConfigEntry("Graphic", "MovingAverage", "float" )
        if t != "WARNING":
            if   t >= 1:                        gglobs.mav_initial = t
            else:                               gglobs.mav_initial = 600
            gglobs.mav =                        gglobs.mav_initial
            dprint(infostr.format("Moving Average Initial (sec)", int(gglobs.mav_initial)))


    # Plotstyle
        dprint(infostrHeader.format("Plotstyle", ""))

        # linewidth
        t = getConfigEntry("Plotstyle", "linewidth", "str" )
        if t != "WARNING":
            try:    gglobs.linewidth           = float(t)
            except: gglobs.linewidth           = 1
        dprint(infostr.format("linewidth", gglobs.linewidth))

        # markersymbol
        t = getConfigEntry("Plotstyle", "markersymbol", "str" )
        if t != "WARNING":
            t = t[0]
            if t in "osp*h+xD" :              gglobs.markersymbol = t
            else:                             gglobs.markersymbol = 'o'
        dprint(infostr.format("markersymbol", gglobs.markersymbol))

        # markersize
        t = getConfigEntry("Plotstyle", "markersize", "str" )
        if t != "WARNING":
            try:                            gglobs.markersize = float(t)
            except:                         gglobs.markersize = 15
        dprint(infostr.format("markersize", gglobs.markersize))


    # Network
        dprint(infostrHeader.format("Network", ""))

        # WiFi SSID
        t = getConfigEntry("Network", "WiFiSSID", "str" )
        if t != "WARNING":  gglobs.WiFiSSID       = t
        dprint(infostr.format("WiFiSSID", gglobs.WiFiSSID))

        # WiFi Password
        t = getConfigEntry("Network", "WiFiPassword", "str" )
        if t != "WARNING":  gglobs.WiFiPassword       = t
        dprint(infostr.format("WiFiPassword", gglobs.WiFiPassword))


    # Radiation World Maps
        dprint(infostrHeader.format("Worldmaps", ""))

        t = getConfigEntry("Worldmaps", "gmcmapWebsite", "str" )
        if t != "WARNING":  gglobs.gmcmapWebsite    = t
        dprint(infostr.format("Website",                gglobs.gmcmapWebsite))

        t = getConfigEntry("Worldmaps", "gmcmapURL", "str" )
        if t != "WARNING":  gglobs.gmcmapURL        = t
        dprint(infostr.format("URL",                    gglobs.gmcmapURL))

        t = getConfigEntry("Worldmaps", "gmcmapUserID", "str" )
        if t != "WARNING":  gglobs.gmcmapUserID     = t
        dprint(infostr.format("UserID",                 gglobs.gmcmapUserID))

        t = getConfigEntry("Worldmaps", "gmcmapCounterID", "str" )
        if t != "WARNING":  gglobs.gmcmapCounterID  = t
        dprint(infostr.format("CounterID",              gglobs.gmcmapCounterID))

        t = getConfigEntry("Worldmaps", "gmcmapPeriod", "upper" )
        if t != "WARNING":
            if t == "AUTO":                             gglobs.gmcmapPeriod = "auto"
            else:
                try:
                    ift = int(float(t))
                    if ift > 0:                         gglobs.gmcmapPeriod = ift
                    else:                               gglobs.gmcmapPeriod = "auto"
                except:                                 gglobs.gmcmapPeriod = "auto"
        dprint(infostr.format("Period",                 gglobs.gmcmapPeriod))

        t = getConfigEntry("Worldmaps", "gmcmapWiFiSwitch", "upper" )
        if t != "WARNING":
            if t == "ON":                               gglobs.gmcmapWiFiSwitch = True
            else:                                       gglobs.gmcmapWiFiSwitch = False
            dprint(infostr.format("WiFi",               "ON" if gglobs.gmcmapWiFiSwitch else "OFF"))


    #
    # ValueScaling - it DOES modify the variable value!
    #
    # infostr = "INFO: {:35s}: {}"
        dprint(infostrHeader.format("ValueScaling", ""))
        for vname in gglobs.varsCopy:
            t = getConfigEntry("ValueScaling", vname, "upper" )
            if t != "WARNING":
                if t == "":     pass                    # use value from gglobs
                else:           gglobs.ValueScale[vname] = t
                dprint(infostr.format("ValueScale['{}']".format(vname), gglobs.ValueScale[vname]))


    #
    # GraphScaling - it does NOT modify the variable value, only the plot value
    #
        dprint(infostrHeader.format("GraphScaling", ""))
        for vname in gglobs.varsCopy:
            t = getConfigEntry("GraphScaling", vname, "upper" )
            if t != "WARNING":
                if t == "":     pass                    # use value from gglobs
                else:           gglobs.GraphScale[vname] = t
                dprint(infostr.format("GraphScale['{}']".format(vname), gglobs.GraphScale[vname]))



    #
    # TubeSensitivities
    #
        dprint(infostrHeader.format("TubeSensitivities", ""))

        # sensitivity Def tube is 154 CPM/(µSv/h), =  0.0065 in units of µSv/h/CPM
        t = getConfigEntry("TubeSensitivities", "TubeSensitivityDef", "str" )
        if t != "WARNING":
            try:                                    gglobs.DefaultSens[0] = float(t)
            except:                                 gglobs.DefaultSens[0] = 154
        if gglobs.DefaultSens[0] <= 0:              gglobs.DefaultSens[0] = 154
        dprint(infostr.format("TubeSensitivityDef", gglobs.DefaultSens[0]))

        # sensitivity 1st tube is 154 CPM/(µSv/h), =  0.0065 in units of µSv/h/CPM
        t = getConfigEntry("TubeSensitivities", "TubeSensitivity1st", "str" )
        if t != "WARNING":
            try:                                    gglobs.DefaultSens[1] = float(t)
            except:                                 gglobs.DefaultSens[1] = 154
        if gglobs.DefaultSens[1] <= 0:              gglobs.DefaultSens[1] = 154
        dprint(infostr.format("TubeSensitivity1st", gglobs.DefaultSens[1]))

        # sensitivity 2nd tube is 2.08 CPM/(µSv/h), =  0.48 in units of µSv/h/CPM
        t = getConfigEntry("TubeSensitivities", "TubeSensitivity2nd", "str" )
        if t != "WARNING":
            try:                                    gglobs.DefaultSens[2] = float(t)
            except:                                 gglobs.DefaultSens[2] = 2.08
        if gglobs.DefaultSens[2] <= 0:              gglobs.DefaultSens[2] = 2.08
        dprint(infostr.format("TubeSensitivity2nd", gglobs.DefaultSens[2]))

        # sensitivity 3rd tube is 154 CPM/(µSv/h), =  0.0065 in units of µSv/h/CPM
        t = getConfigEntry("TubeSensitivities", "TubeSensitivity3rd", "str" )
        if t != "WARNING":
            try:                                    gglobs.DefaultSens[3] = float(t)
            except:                                 gglobs.DefaultSens[3] = 154
        if gglobs.DefaultSens[3] <= 0:              gglobs.DefaultSens[3] = 154
        dprint(infostr.format("TubeSensitivity3rd", gglobs.DefaultSens[3]))

        # set Sensitivity[Tube No]
        for i in range(4):  gglobs.Sensitivity[i] = gglobs.DefaultSens[i]



###
### DEVICES
###

        dprint(infostrHeader.format("Activated Devices", ""))

        # re-definition for increased indentation
        infostrHeader = "cfg:     {:31s} {}"
        infostr       = "cfg:         {:31s}: {}"

    # GMC_Device
        t = getConfigEntry("GMC_Device", "GMC_Activation", "upper" )
        if t != "WARNING":
            if t == "YES":
                gglobs.Devices["GMC"][2] = True

        if gglobs.Devices["GMC"][2]: # show only if activated
            dprint(infostrHeader.format("GMC Device", ""))

            # GMC_Device Firmware Bugs
            # location bug: "GMC-500+Re 1.18, GMC-500+Re 1.21"
            t = getConfigEntry("GMC_Device", "GMC_locationBug", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO":                 gglobs.GMC_locationBug = "auto"
                else:                                   gglobs.GMC_locationBug = t
                dprint(infostr.format("Location Bug",   gglobs.GMC_locationBug))

            # GMC_Device Firmware Bugs
            # FET bug: GMC_FastEstimateTime
            t = getConfigEntry("GMC_Device", "GMC_FastEstTime", "upper" )
            if t != "WARNING":
                try:    tFET = int(float(t))
                except: tFET = "auto"
                if   t == "AUTO":                       gglobs.GMC_FastEstTime = "auto"
                elif t == "DYNAMIC":                    gglobs.GMC_FastEstTime = 3
                elif tFET in (3,5,10,15,20,30,60):      gglobs.GMC_FastEstTime = tFET
                else:                                   gglobs.GMC_FastEstTime = "auto"
                dprint(infostr.format("FET",            gglobs.GMC_FastEstTime))

            # GMC_Device memory
            t = getConfigEntry("GMC_Device", "GMC_memory", "upper" )
            if t != "WARNING":
                if   t ==  '1MB':                       gglobs.GMC_memory = 2**20   # 1 048 576
                elif t == '64KB':                       gglobs.GMC_memory = 2**16   #    65 536
                else:                                   gglobs.GMC_memory = 'auto'
                dprint(infostr.format("Memory",         gglobs.GMC_memory))

            # GMC_Device GMC_SPIRpage
            t = getConfigEntry("GMC_Device", "GMC_SPIRpage", "upper" )
            if t != "WARNING":
                if   t == '2K':                     gglobs.GMC_SPIRpage = 2048     # @ 2k speed: 6057 B/sec
                elif t == '4K':                     gglobs.GMC_SPIRpage = 4096     # @ 4k speed: 7140 B/sec
                elif t == '8K':                     gglobs.GMC_SPIRpage = 4096 * 2 # @ 8k speed: 7908 B/sec
                elif t == '16K':                    gglobs.GMC_SPIRpage = 4096 * 4 # @16k speed: 8287 B/sec
                else:                               gglobs.GMC_SPIRpage = "auto"
                dprint(infostr.format("SPIRpage",   gglobs.GMC_SPIRpage))

            # GMC_Device GMC_SPIRbugfix
            t = getConfigEntry("GMC_Device", "GMC_SPIRbugfix", "upper" )
            if t != "WARNING":
                if   t == 'YES':                    gglobs.GMC_SPIRbugfix = True
                elif t == 'NO':                     gglobs.GMC_SPIRbugfix = False
                else:                               gglobs.GMC_SPIRbugfix = 'auto'
                dprint(infostr.format("SPIRbugfix", gglobs.GMC_SPIRbugfix))

            # GMC_Device GMC_configsize
            t = getConfigEntry("GMC_Device", "GMC_configsize", "upper" )
            if t != "WARNING":
                t = config.get("GMC_Device", "GMC_configsize")
                if   t == '256':                    gglobs.GMC_configsize = 256
                elif t == '512':                    gglobs.GMC_configsize = 512
                else:                               gglobs.GMC_configsize = 'auto'
                dprint(infostr.format("Configsize", gglobs.GMC_configsize))

            # GMC_Device GMC_voltagebytes
            t = getConfigEntry("GMC_Device", "GMC_voltagebytes", "upper" )
            if t != "WARNING":
                if   t == '1':                          gglobs.GMC_voltagebytes = 1
                elif t == '5':                          gglobs.GMC_voltagebytes = 5
                else:                                   gglobs.GMC_voltagebytes = 'auto'
                dprint(infostr.format("Voltagebytes",   gglobs.GMC_voltagebytes))

            # GMC_Device GMC_endianness
            t = getConfigEntry("GMC_Device", "GMC_endianness", "upper" )
            if t != "WARNING":
                if   t == 'LITTLE':                     gglobs.GMC_endianness = 'little'
                elif t == 'BIG':                        gglobs.GMC_endianness = 'big'
                else:                                   gglobs.GMC_endianness = 'auto'
                dprint(infostr.format("Endianness",     gglobs.GMC_endianness))


            # GMC_Device GMC_WifiIndex
            t = getConfigEntry("GMC_Device", "GMC_WifiIndex", "upper" )
            if t != "WARNING":
                if   t == "AUTO":                       gglobs.GMC_WifiIndex = "auto"
                elif t == "NONE":                       gglobs.GMC_WifiIndex = None
                elif t in  ["2", "3", "4"]:             gglobs.GMC_WifiIndex = t
                else:                                   gglobs.GMC_WifiIndex = "auto"
                dprint(infostr.format("WifiIndex",      gglobs.GMC_WifiIndex))


            # GMC_Device GMC_Bytes
            t = getConfigEntry("GMC_Device", "GMC_Bytes", "upper" )
            if t != "WARNING":
                if t == "AUTO":                         gglobs.GMC_Bytes = "auto"
                else:
                    nt = int(t)
                    if nt in (2, 4):                    gglobs.GMC_Bytes = nt
                    else:                               gglobs.GMC_Bytes = 2
                dprint(infostr.format("Nbytes",         gglobs.GMC_Bytes))


            # GMC_Device variables
            t = getConfigEntry("GMC_Device", "GMC_Variables", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO":                 gglobs.GMC_Variables = "auto"
                else:                                   gglobs.GMC_Variables = correctVariableCaps(t)
                dprint(infostr.format("Variables",      gglobs.GMC_Variables))


            t = getConfigEntry("GMC_Device", "GMC_usbport", "str" )
            if t != "WARNING":
                if   t.upper() == "AUTO":               gglobs.GMC_usbport = "auto"
                else:                                   gglobs.GMC_usbport = t
                dprint(infostr.format("Serial Port",    gglobs.GMC_usbport))


            t = getConfigEntry("GMC_Device", "GMC_ID", "str" )
            if t != "WARNING":
                if   t.upper() == "AUTO":               gglobs.GMC_ID = "auto"
                else:
                    ts = t.split(",")
                    if len(ts) != 2:                    gglobs.GMC_ID = "auto"
                    else:
                        ts[0] = ts[0].strip()
                        ts[1] = ts[1].strip()
                        if ts[0].upper() == "NONE": ts[0] = None
                        if ts[1].upper() == "NONE": ts[1] = None
                        gglobs.GMC_ID = ts
                dprint(infostr.format("Device IDs", gglobs.GMC_ID))



    # AudioCounter
        t = getConfigEntry("AudioCounter", "AudioActivation", "upper" )
        if t != "WARNING":
            if t == "YES":
                gglobs.Devices["Audio"][2] = True

        if gglobs.Devices["Audio"][2]: # show only if activated
            dprint(infostrHeader.format("AudioCounter Device", ""))

            # AudioCounter DEVICE
            t = getConfigEntry("AudioCounter", "AudioDevice", "str" )
            if t != "WARNING":
                if   t.upper() == "AUTO":               gglobs.AudioDevice = "auto"
                elif not ("," in t):                    gglobs.AudioDevice = "auto" # must have 2 items separated by comma
                else:
                    t = t.split(",", 1)
                    t[0] = t[0].strip()
                    t[1] = t[1].strip()
                    if t[0].isdecimal():   t[0] = int(t[0])
                    if t[1].isdecimal():   t[1] = int(t[1])
                    gglobs.AudioDevice = tuple(t)
                dprint(infostr.format("AudioDevice",    gglobs.AudioDevice))

            # AudioCounter LATENCY
            t = getConfigEntry("AudioCounter", "AudioLatency", "str" )
            if t != "WARNING":
                if   t.upper() == "AUTO":               gglobs.AudioLatency = "auto"
                elif not ("," in t):                    gglobs.AudioLatency = "auto" # must have 2 items separated by comma
                else:
                    t = t.split(",", 1)
                    try:    t[0] = float(t[0])
                    except: t[0] = 1.0
                    try:    t[1] = float(t[1])
                    except: t[1] = 1.0
                    gglobs.AudioLatency = tuple(t)
                dprint(infostr.format("AudioLatency", gglobs.AudioLatency))

            # AudioCounter PULSE Dir
            t = getConfigEntry("AudioCounter", "AudioPulseDir", "upper" )
            if t != "WARNING":
                if   t == "AUTO":           gglobs.AudioPulseDir = "auto"
                elif t == "NEGATIVE":       gglobs.AudioPulseDir = False
                elif t == "POSITIVE":       gglobs.AudioPulseDir = True
                else:                       pass # unchanged from default False
                dprint(infostr.format("AudioPulseDir", gglobs.AudioPulseDir))

            # AudioCounter PULSE Max
            t = getConfigEntry("AudioCounter", "AudioPulseMax", "upper" )
            if t != "WARNING":
                if t == "AUTO":                     gglobs.AudioPulseMax = "auto"
                else:
                    try:                            gglobs.AudioPulseMax = int(float(t))
                    except:                         gglobs.AudioPulseMax = "auto"
                    if gglobs.AudioPulseMax <= 0:   gglobs.AudioPulseMax = "auto"
                dprint(infostr.format("AudioPulseMax", gglobs.AudioPulseMax))

            # AudioCounter LIMIT
            t = getConfigEntry("AudioCounter", "AudioThreshold", "upper" )
            if t != "WARNING":
                if t == "AUTO":             gglobs.AudioThreshold = "auto"
                else:
                    try:                    gglobs.AudioThreshold = int(float(t))
                    except:                 gglobs.AudioThreshold = 60
                    if gglobs.AudioThreshold < 0 or gglobs.AudioThreshold > 100:
                                            gglobs.AudioThreshold = 60
                dprint(infostr.format("AudioThreshold", gglobs.AudioThreshold))

            # AudioCounter Variables
            t = getConfigEntry("AudioCounter", "AudioVariables", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO":                 gglobs.AudioVariables = "auto"
                else:                                   gglobs.AudioVariables = correctVariableCaps(t)
                dprint(infostr.format("AudioVariables", gglobs.AudioVariables))


    # RadMonPlus
        # RadMon Activation
        t = getConfigEntry("RadMonPlusDevice", "RMActivation", "upper" )
        if t != "WARNING":
            if t == "YES":
                gglobs.Devices["RadMon"][2] = True

        if gglobs.Devices["RadMon"][2]: # show the other stuff only if activated
            dprint(infostrHeader.format("RadMonPlus Device", ""))

            # RadMon Server IP
            t = getConfigEntry("RadMonPlusDevice", "RMServerIP", "str" )
            if t != "WARNING":
                if t.upper() == 'AUTO':                 gglobs.RMServerIP = "auto"
                else:                                   gglobs.RMServerIP = t
                dprint(infostr.format("RMServerIP",     gglobs.RMServerIP ))

            # RadMon Server Port
            t = getConfigEntry("RadMonPlusDevice", "RMServerPort", "str" )
            if t != "WARNING":
                if t.upper() == 'AUTO':                 gglobs.RMServerPort = "auto"
                else:
                    try:    gglobs.RMServerPort = abs(int(t))
                    except: gglobs.RMServerPort = "auto"
                dprint(infostr.format("RMServerPort",   gglobs.RMServerPort))

            # Radmon timeout
            t = getConfigEntry("RadMonPlusDevice", "RMTimeout", "upper" )
            if t != "WARNING":
                if t == 'AUTO':                         gglobs.RMTimeout = "auto"
                else:
                    try:
                        if float(t) > 0:                gglobs.RMTimeout = float(t)
                        else:                           gglobs.RMTimeout = "auto"  # if zero or negative value given
                    except:                             gglobs.RMTimeout = "auto"
                dprint(infostr.format("RMTimeout",      gglobs.RMTimeout))

            # RadMon Server Folder
            t = getConfigEntry("RadMonPlusDevice", "RMServerFolder", "str" )
            if t != "WARNING":
                # blank in folder name not allowed
                if " " in t or t.upper() == "AUTO":     gglobs.RMServerFolder = "auto"
                else:
                    gglobs.RMServerFolder = t
                    if gglobs.RMServerFolder[-1] != "/":gglobs.RMServerFolder += "/"
                dprint(infostr.format("RMServerFolder", gglobs.RMServerFolder ))

            # Radmon variables
            t = getConfigEntry("RadMonPlusDevice", "RMVariables", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO":                 gglobs.RMVariables = "auto"
                else:
                    gglobs.RMVariables = correctVariableCaps(t)
                    if gglobs.RMVariables.count("CPM") > 1 or gglobs.RMVariables.count("CPS") > 0:
                        edprint("WARNING: Improper configuration of variables: ", gglobs.RMVariables)
                        edprint("WARNING: Only a single CPM* is allowed, and no CPS*")
                        gglobs.RMVariables = "auto"
                        edprint("WARNING: RadMon variables are reset to: ", gglobs.RMVariables)
                dprint(infostr.format("RMVariables",    gglobs.RMVariables))


    # AmbioMon
        t = getConfigEntry("AmbioMonDevice", "AmbioActivation", "upper" )
        if t != "WARNING":
            if t == "YES":
                gglobs.Devices["AmbioMon"][2] = True

        if gglobs.Devices["AmbioMon"][2]: # show the other stuff only if activated
            dprint(infostrHeader.format("AmbioMon Device", ""))

            # AmbioMon Server IP
            t = getConfigEntry("AmbioMonDevice", "AmbioServerIP", "str" )
            if t != "WARNING":
                if t.upper() == 'AUTO':                 gglobs.AmbioServerIP = "auto"
                else:                                   gglobs.AmbioServerIP = t
                dprint(infostr.format("AmbioServerIP",  gglobs.AmbioServerIP ))

            # AmbioMon Server Port
            t = getConfigEntry("AmbioMonDevice", "AmbioServerPort", "upper" )
            if t != "WARNING":
                if t == "AUTO":                             gglobs.AmbioServerPort = "auto"
                else:
                    wp = int(float(t))
                    if 0 <= wp  <= 65535:                   gglobs.AmbioServerPort = wp
                    else:                                   gglobs.AmbioServerPort = "auto"
                dprint(infostr.format("AmbioServerPort",    gglobs.AmbioServerPort ))

            # AmbioMon timeout
            t = getConfigEntry("AmbioMonDevice", "AmbioTimeout", "upper" )
            if t != "WARNING":
                if t == 'AUTO':                         gglobs.AmbioTimeout = "auto"
                else:
                    try:
                        if float(t) > 0:                gglobs.AmbioTimeout = float(t)
                        else:                           gglobs.AmbioTimeout = "auto"  # if zero or negative value given
                    except:                             gglobs.AmbioTimeout = "auto"
                dprint(infostr.format("AmbioTimeout",   gglobs.AmbioTimeout))

            # AmbioMon DataType
            t = getConfigEntry("AmbioMonDevice", "AmbioDataType", "str" )
            if t != "WARNING":
                if   t.upper() == "AUTO":               gglobs.AmbioDataType = "auto"
                elif t.upper() == "AVG":                gglobs.AmbioDataType = "AVG"
                else:                                   gglobs.AmbioDataType = "LAST"
                dprint(infostr.format("AmbioDataType",  gglobs.AmbioDataType))

            # AmbioMon variables
            t = getConfigEntry("AmbioMonDevice", "AmbioVariables", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO":                 gglobs.AmbioVariables = "auto"
                else:                                   gglobs.AmbioVariables = correctVariableCaps(t)
                dprint(infostr.format("AmbioVariables", gglobs.AmbioVariables))

    # Gamma-Scout counter
        # Gamma-Scout Activation
        t = getConfigEntry("GammaScoutDevice", "GSActivation", "upper" )
        if t != "WARNING":
            if t == "YES":
                gglobs.Devices["GammaScout"][2] = True

        if gglobs.Devices["GammaScout"][2]: # show the other stuff only if activated
            dprint(infostrHeader.format("GammaScout Device", ""))

            # Gamma-Scout variables
            t = getConfigEntry("GammaScoutDevice", "GSVariables", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO":                 gglobs.GSVariables = "auto"
                else:                                   gglobs.GSVariables = correctVariableCaps(t)
                dprint(infostr.format("Variables",      gglobs.GSVariables))

            # Gamma-Scout USB Port
            t = getConfigEntry("GammaScoutDevice", "GSusbport", "str" )
            if t != "WARNING":
                if   t.upper() == "AUTO":               gglobs.GSusbport = "auto"
                else:                                   gglobs.GSusbport = t
                dprint(infostr.format("Serial Port",    gglobs.GSusbport))


    # I2C
        # I2C variables:  included in sensors settings
        t = getConfigEntry("I2C", "I2CActivation", "upper" )
        if t != "WARNING":
            if t == "YES":
                gglobs.Devices["I2C"][2] = True

        if gglobs.Devices["I2C"][2]: # show the other stuff only if activated
            dprint(infostrHeader.format("I2CSensor Device", ""))

            # I2C Dongle - ISS, ELV, IOW
            t = getConfigEntry("I2C", "I2CDongle", "upper" )
            if t != "WARNING":
                t = t.strip()
                try:
                    # if t in ["ISS", "ELV", "IOW", "FTD"]:   gglobs.I2CDongleCode = t  # no FTD support
                    if t in ["ISS", "ELV", "IOW"]:          gglobs.I2CDongleCode = t
                    else:                                   gglobs.I2CDongleCode = "ISS"
                except:
                    gglobs.I2CDongleCode = "ISS"
                dprint(infostr.format("Dongle",   gglobs.I2CDongleCode))


            # I2C usbport
            t = getConfigEntry("I2C", "I2Cusbport", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO":                     gglobs.I2Cusbport = "auto"
                else:                                       gglobs.I2Cusbport = t
                dprint(infostr.format("Serial Port",        gglobs.I2Cusbport))


            # I2C Sensors Options (3 sep by comma):  < yes | no > , <Sensor Addr in hex>, <variables>
            # like: I2CSensorBME280  = y, 0x76, Temp, Press, Humid
            # here 'y' and 'n' can be used for 'yes' and 'no'

            # I2C Sensors - LM75, addr 0x48 | 0x49 | 0x4A | 0x4B | 0x4C | 0x4E | 0x4F
            # like: I2CSensorLM75      = yn, 0x48, CPS3rd
            t = getConfigEntry("I2C", "I2CSensorLM75", "str" )
            if t != "WARNING":
                t = t.strip().split(",")
                try:
                    if "Y" in t[0].strip().upper():         gglobs.I2CSensor["LM75"][0] = True
                    else:                                   gglobs.I2CSensor["LM75"][0] = False
                    gglobs.I2CSensor["LM75"][1] = int(t[1], 16)
                except:
                    gglobs.I2CSensor["LM75"][0] = False
                    gglobs.I2CSensor["LM75"][1] = 0x48
                gglobs.I2CSensor["LM75"][2] = t[2:]
                dprint(infostr.format("SensorLM75",         gglobs.I2CSensor["LM75"]))

            # I2C Sensors - BME280, addr 0x76 | 0x77
            # I2CSensorBME280 : [True, 118, [' Temp', ' Press', ' Humid']]
            t = getConfigEntry("I2C", "I2CSensorBME280", "str" )
            if t != "WARNING":
                t = t.strip().split(",")
                try:
                    if "Y" in t[0].strip().upper():         gglobs.I2CSensor["BME280"][0] = True
                    else:                                   gglobs.I2CSensor["BME280"][0] = False
                    gglobs.I2CSensor["BME280"][1] = int(t[1], 16)
                except:
                    gglobs.I2CSensor["BME280"][0] = False
                    gglobs.I2CSensor["BME280"][1] = 0x76
                gglobs.I2CSensor["BME280"][2] = t[2:]
                dprint(infostr.format("SensorBME280",       gglobs.I2CSensor["BME280"]))

            # I2C Sensors - SCD41, addr 0x62
            t = getConfigEntry("I2C", "I2CSensorSCD41", "str" )
            if t != "WARNING":
                t = t.strip().split(",")
                try:
                    if "Y" in t[0].strip().upper():         gglobs.I2CSensor["SCD41"][0] = True
                    else:                                   gglobs.I2CSensor["SCD41"][0] = False
                    gglobs.I2CSensor["SCD41"][1] = int(t[1], 16)
                except:
                    gglobs.I2CSensor["SCD41"][0] = False
                    gglobs.I2CSensor["SCD41"][1] = 0x29
                gglobs.I2CSensor["SCD41"][2] = t[2:]
                dprint(infostr.format("SensorSCD41",        gglobs.I2CSensor["SCD41"]))

            # I2C Sensors - SCD30, addr 0x61
            t = getConfigEntry("I2C", "I2CSensorSCD30", "str" )
            if t != "WARNING":
                t = t.strip().split(",")
                try:
                    if "Y" in t[0].strip().upper():         gglobs.I2CSensor["SCD30"][0] = True
                    else:                                   gglobs.I2CSensor["SCD30"][0] = False
                    gglobs.I2CSensor["SCD30"][1] = int(t[1], 16)
                except:
                    gglobs.I2CSensor["SCD30"][0] = False
                    gglobs.I2CSensor["SCD30"][1] = 0x61
                gglobs.I2CSensor["SCD30"][2] = t[2:]
                dprint(infostr.format("SensorSCD30",        gglobs.I2CSensor["SCD30"]))

            # I2C Sensors - TSL2591, addr 0x29
            t = getConfigEntry("I2C", "I2CSensorTSL2591", "str" )
            if t != "WARNING":
                t = t.strip().split(",")
                try:
                    if "Y" in t[0].strip().upper():         gglobs.I2CSensor["TSL2591"][0] = True
                    else:                                   gglobs.I2CSensor["TSL2591"][0] = False
                    gglobs.I2CSensor["TSL2591"][1] = int(t[1], 16)
                except:
                    gglobs.I2CSensor["TSL2591"][0] = False
                    gglobs.I2CSensor["TSL2591"][1] = 0x29
                gglobs.I2CSensor["TSL2591"][2] = t[2:]
                dprint(infostr.format("SensorTSL2591",      gglobs.I2CSensor["TSL2591"]))


            # I2C Sensors - BH1750, addr 0x23 oder 0x5C
            t = getConfigEntry("I2C", "I2CSensorBH1750", "str" )
            if t != "WARNING":
                t = t.strip().split(",")
                try:
                    if "Y" in t[0].strip().upper():         gglobs.I2CSensor["BH1750"][0] = True
                    else:                                   gglobs.I2CSensor["BH1750"][0] = False
                    gglobs.I2CSensor["BH1750"][1] = int(t[1], 16)
                except:
                    gglobs.I2CSensor["BH1750"][0] = False
                    gglobs.I2CSensor["BH1750"][1] = 0x23
                gglobs.I2CSensor["BH1750"][2] = t[2:]
                dprint(infostr.format("SensorBH1750",       gglobs.I2CSensor["BH1750"]))


            # I2C Sensors - GDK101, addr 0x18
            t = getConfigEntry("I2C", "I2CSensorGDK101", "str" )
            if t != "WARNING":
                t = t.strip().split(",")
                try:
                    if "Y" in t[0].strip().upper():         gglobs.I2CSensor["GDK101"][0] = True
                    else:                                   gglobs.I2CSensor["GDK101"][0] = False
                    gglobs.I2CSensor["GDK101"][1] = int(t[1], 16)
                except:
                    gglobs.I2CSensor["GDK101"][0] = False
                    gglobs.I2CSensor["GDK101"][1] = 0x18
                gglobs.I2CSensor["GDK101"][2] = t[2:]           # the variables
                dprint(infostr.format("SensorGDK101",        gglobs.I2CSensor["GDK101"]))


    # LabJack U3 (type U3B, perhaps with probe EI1050)
        # LabJack Activation
        t = getConfigEntry("LabJackDevice", "LJActivation", "upper" )
        if t != "WARNING":
            if t == "YES":
                gglobs.Devices["LabJack"][2] = True

        if gglobs.Devices["LabJack"][2]: # show the other stuff only if activated
            dprint(infostrHeader.format("LabJack Device", ""))

            # LabJack  EI1050 Activation
            t = getConfigEntry("LabJackDevice", "LJEI1050Activation", "upper" )
            if t != "WARNING":
                if t == "YES":                              gglobs.LJEI1050Activation = True
                dprint(infostr.format("LJEI1050Activation", gglobs.LJEI1050Activation))

            # LabJack variables
            t = getConfigEntry("LabJackDevice", "LJVariables", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO":                     gglobs.LJVariables = "auto"
                else:                                       gglobs.LJVariables = correctVariableCaps(t)
                dprint(infostr.format("LJVariables",        gglobs.LJVariables))


    # MiniMon
        t = getConfigEntry("MiniMon", "MiniMonActivation", "upper" )
        if t != "WARNING":
            if t == "YES":
                gglobs.Devices["MiniMon"][2] = True

        if gglobs.Devices["MiniMon"][2]: # show the other stuff only if activated
            dprint(infostrHeader.format("MiniMon Device", ""))

            # MiniMon Device
            t = getConfigEntry("MiniMon", "MiniMonOS_Device", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO":                     gglobs.MiniMonOS_Device = "auto"
                else:                                       gglobs.MiniMonOS_Device = t
                dprint(infostr.format("MiniMonOS_Device",   gglobs.MiniMonOS_Device))

            # MiniMon Variables
            t = getConfigEntry("MiniMon", "MiniMonVariables", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO":                     gglobs.MiniMonVariables = "auto"
                else:                                       gglobs.MiniMonVariables = correctVariableCaps(t)
                dprint(infostr.format("MiniMonVariables",   gglobs.MiniMonVariables))

            # MiniMon Interval
            t = getConfigEntry("MiniMon", "MiniMonInterval", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO":                     gglobs.MiniMonInterval = "auto"
                else:
                    try:
                        gglobs.MiniMonInterval = float(t)
                        if gglobs.MiniMonInterval < 0:      gglobs.MiniMonInterval = "auto"
                    except:                                 gglobs.MiniMonInterval = "auto"
                dprint(infostr.format("MiniMonInterval",    gglobs.MiniMonInterval))


    # Simul Device
        # Simul Device Activation
        t = getConfigEntry("Simul", "SimulActivation", "upper" )
        if t != "WARNING":
            if t == "YES":
                gglobs.Devices["Simul"][2] = True

        if gglobs.Devices["Simul"][2]: # show the other stuff only if activated
            dprint(infostrHeader.format("Simul Device", ""))

            # Simul Device MEAN
            t = getConfigEntry("Simul", "SimulMean", "upper" )
            if t != "WARNING":
                if   t == "AUTO":                           gglobs.SimulMean = "auto"
                else:
                    try:
                        gglobs.SimulMean = float(t)
                        if gglobs.SimulMean < 0:            gglobs.SimulMean = "auto"
                    except:                                 gglobs.SimulMean = "auto"
                dprint(infostr.format("SimulMean",          gglobs.SimulMean))

            # inactive. config file code in module gdev_simul.py
            #
            #~t = getConfigEntry("Simul", "SimulPredictive", "upper" )
            #~if t != "WARNING":
                #~if t == "YES":                      gglobs.SimulPredictive = True
                #~else:                               gglobs.SimulPredictive = False
                #~dprint(infostr.format("SimulPredictive", gglobs.SimulPredictive))

            #~t = getConfigEntry("Simul", "SimulPredictLimit", "str" )
            #~if t != "WARNING":
                #~if t.upper() == "AUTO":             gglobs.SimulPredictLimit = "auto"
                #~try:
                    #~gglobs.SimulPredictLimit = int(float(t))
                    #~if gglobs.SimulPredictLimit < 0:gglobs.SimulPredictLimit = "auto"
                #~except:                             gglobs.SimulPredictLimit = "auto"
                #~dprint(infostr.format("SimulPredictLimit", gglobs.SimulPredictLimit))

            # Simul Device Deadtime
            t = getConfigEntry("Simul", "SimulDeadtime", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO":                     gglobs.SimulDeadtime = "auto"
                else:
                    try:
                        gglobs.SimulDeadtime = float(t)
                        if gglobs.SimulDeadtime < 0:        gglobs.SimulDeadtime = "auto"
                    except:                                 gglobs.SimulDeadtime = "auto"
                dprint(infostr.format("SimulDeadtime",      gglobs.SimulDeadtime))

            # Simul Device Variables
            t = getConfigEntry("Simul", "SimulVariables", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO":                     gglobs.SimulVariables = "auto"
                else:                                       gglobs.SimulVariables = correctVariableCaps(t)
                dprint(infostr.format("SimulVariables",     gglobs.SimulVariables))


    # Manu
        t = getConfigEntry("Manu", "ManuActivation", "upper" )
        if t != "WARNING":
            if t == "YES":
                gglobs.Devices["Manu"][2] = True

        if gglobs.Devices["Manu"][2]: # show the other stuff only if activated
            dprint(infostrHeader.format("Manu Device", ""))

            # Manu RecordStyle
            t = getConfigEntry("Manu", "ManuRecordStyle", "upper" )
            if t != "WARNING":
                if t == "AUTO":                             gglobs.ManuRecordStyle = "auto"
                else:
                    if      t == "POINT":                   gglobs.ManuRecordStyle = "Point"
                    elif    t == "STEP":                    gglobs.ManuRecordStyle = "Step"
                    else:                                   gglobs.ManuRecordStyle = "auto"
                dprint(infostr.format("ManuRecordStyle",    gglobs.ManuRecordStyle))

            # Manu Variables
            t = getConfigEntry("Manu", "ManuVariables", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO" :                    gglobs.ManuVariables = "auto"
                else:                                       gglobs.ManuVariables = correctVariableCaps(t)
                dprint(infostr.format("ManuVariables",      gglobs.ManuVariables))


    # WiFiServer
        t = getConfigEntry("WiFiServerDevice", "WiFiServerActivation", "upper" )
        if t != "WARNING":
            if t == "YES":
                gglobs.Devices["WiFiServer"][ACTIV] = True

        if gglobs.Devices["WiFiServer"][ACTIV]: # show the other stuff only if activated
            dprint(infostrHeader.format("WiFiServer Device", ""))

            # WiFiServer IP
            t = getConfigEntry("WiFiServerDevice", "WiFiServerIP", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO":                     gglobs.WiFiServerIP = "auto"
                else:                                       gglobs.WiFiServerIP = t
                dprint(infostr.format("WiFiServerIP",       gglobs.WiFiServerIP))

            # WiFiServer Port
            t = getConfigEntry("WiFiServerDevice", "WiFiServerPort", "upper" )
            if t != "WARNING":
                if t == "AUTO":                             gglobs.WiFiServerPort = "auto"
                else:
                    wp = int(float(t))
                    if 0 <= wp  <= 65535:                   gglobs.WiFiServerPort = wp
                    else:                                   gglobs.WiFiServerPort = "auto"
                dprint(infostr.format("WiFiServerPort",     gglobs.WiFiServerPort))

            # WiFiServer Folder
            t = getConfigEntry("WiFiServerDevice", "WiFiServerFolder", "str" )
            if t != "WARNING":
                if t.upper() == 'AUTO':                     gglobs.WiFiServerFolder = "auto"
                else:                                       gglobs.WiFiServerFolder = t.replace("\\", "").replace("/", "")
                dprint(infostr.format("WiFiServerFolder",   gglobs.WiFiServerFolder))

            # WiFiServer timeout
            t = getConfigEntry("WiFiServerDevice", "WiFiServerTimeout", "upper" )
            if t != "WARNING":
                if t == 'AUTO':                             gglobs.WiFiServerTimeout = "auto"
                else:
                    try:
                        tt = float(t)
                        if tt > 0:                          gglobs.WiFiServerTimeout = tt
                        else:                               gglobs.WiFiServerTimeout = "auto"  # if zero or negative value
                    except:                                 gglobs.WiFiServerTimeout = "auto"  # if non-float value
                dprint(infostr.format("WiFiServerTimeout",  gglobs.WiFiServerTimeout))

            # WiFiServer DataType
            t = getConfigEntry("WiFiServerDevice", "WiFiServerDataType", "upper" )
            if t != "WARNING":
                if   t == "AUTO":                           gglobs.WiFiServerDataType = "auto"
                elif t == "AVG":                            gglobs.WiFiServerDataType = "AVG"
                else:                                       gglobs.WiFiServerDataType = "LAST"
                dprint(infostr.format("WiFiServerDataType", gglobs.WiFiServerDataType))

            # WiFiServer variables
            t = getConfigEntry("WiFiServerDevice", "WiFiServerVariables", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO":                     gglobs.WiFiServerVariables = "auto"
                else:                                       gglobs.WiFiServerVariables = correctVariableCaps(t)
                dprint(infostr.format("WiFiServerVariables",gglobs.WiFiServerVariables))


    # WiFiClient
        t = getConfigEntry("WiFiClientDevice", "WiFiClientActivation", "upper" )
        if t != "WARNING":
            if t == "YES":
                gglobs.Devices["WiFiClient"][2] = True

        if gglobs.Devices["WiFiClient"][2]: # show the other stuff only if activated
            dprint(infostrHeader.format("WiFiClient Device", ""))

            # WiFiClient Server Port
            t = getConfigEntry("WiFiClientDevice", "WiFiClientPort", "upper" )
            if t != "WARNING":
                if t == 'AUTO':                             gglobs.WiFiClientPort = "auto"
                else:
                    try:
                        if float(t) > 0:                    gglobs.WiFiClientPort = int(float(t))
                        else:                               gglobs.WiFiClientPort = "auto"  # if zero or negative value given
                    except:                                 gglobs.WiFiClientPort = "auto"
                dprint(infostr.format("WiFiClientPort",     gglobs.WiFiClientPort ))


            # WiFiClient Type
            t = getConfigEntry("WiFiClientDevice", "WiFiClientType", "upper" )
            if t != "WARNING":
                if t == "GMC":                              gglobs.WiFiClientType = "GMC"
                else:                                       gglobs.WiFiClientType = "GENERIC"
                dprint(infostr.format("WiFiClientType",     gglobs.WiFiClientType))


            # WiFiClient variables
            t = getConfigEntry("WiFiClientDevice", "WiFiClientVariables", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO":                     gglobs.WiFiClientVariables = "auto"
                else:                                       gglobs.WiFiClientVariables = correctVariableCaps(t)
                dprint(infostr.format("WiFiClientVariables",gglobs.WiFiClientVariables))



    # RaspiPulse
        # RaspiPulse Activation
        t = getConfigEntry("RaspiPulseDevice", "RaspiPulseActivation", "upper" )
        if t != "WARNING":
            if t == "YES":
                gglobs.Devices["RaspiPulse"][2] = True

        if gglobs.Devices["RaspiPulse"][2]: # show the other stuff only if activated
            dprint(infostrHeader.format("RaspiPulse Device", ""))

            # RaspiPulse Server Pin
            t = getConfigEntry("RaspiPulseDevice", "RaspiPulsePin", "upper" )
            if t != "WARNING":
                if t == 'AUTO':                             gglobs.RaspiPulsePin = "auto"
                else:
                    try:
                        if float(t) > 0:                    gglobs.RaspiPulsePin = int(float(t))
                        else:                               gglobs.RaspiPulsePin = "auto"  # if zero or negative value given
                    except:                                 gglobs.RaspiPulsePin = "auto"
                dprint(infostr.format("RaspiPulsePin",      gglobs.RaspiPulsePin))

            # RaspiPulse Edge
            t = getConfigEntry("RaspiPulseDevice", "RaspiPulseEdge", "upper" )
            if t != "WARNING":
                if   t == "AUTO":                           gglobs.RaspiPulseEdge = "auto"
                elif t in ("RISING", "FALLING"):            gglobs.RaspiPulseEdge = t
                else:                                       gglobs.RaspiPulseEdge = "auto"
                dprint(infostr.format("RaspiPulseEdge",     gglobs.RaspiPulseEdge))

            # RaspiPulse variables
            t = getConfigEntry("RaspiPulseDevice", "RaspiPulseVariables", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO":                     gglobs.RaspiPulseVariables = "auto"
                else:                                       gglobs.RaspiPulseVariables = correctVariableCaps(t)
                dprint(infostr.format("RaspiPulseVariables", gglobs.RaspiPulseVariables))


    # RaspiI2C
        # RaspiI2C Activation
        t = getConfigEntry("RaspiI2CDevice", "RaspiI2CActivation", "upper" )
        if t != "WARNING":
            if t == "YES":
                gglobs.Devices["RaspiI2C"][2] = True

        if gglobs.Devices["RaspiI2C"][2]: # show the other stuff only if activated
            dprint(infostrHeader.format("RaspiI2C Device", ""))

            # RaspiI2C Address
            t = getConfigEntry("RaspiI2CDevice", "RaspiI2CAdress", "upper" )
            if t != "WARNING":
                if t == 'AUTO':                             gglobs.RaspiI2CAdress = "auto"
                else:
                    try:
                        ad = int(float(t))
                        if ad in (0x48, 0x49, 0x4A, 0x4B, 0x4C, 0x4D, 0x4E, 0x4F):
                                                            gglobs.RaspiI2CAdress = ad
                        else:                               gglobs.RaspiI2CAdress = "auto"
                    except:                                 gglobs.RaspiI2CAdress = "auto"
                dprint(infostr.format("RaspiI2CAdress",     gglobs.RaspiI2CAdress))

            # RaspiI2C variables
            t = getConfigEntry("RaspiI2CDevice", "RaspiI2CVariables", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO":                     gglobs.RaspiI2CVariables = "auto"
                else:                                       gglobs.RaspiI2CVariables = correctVariableCaps(t)
                dprint(infostr.format("RaspiI2CVariables",  gglobs.RaspiI2CVariables))


    # Rad Pro
        # Rad Pro Activation
        t = getConfigEntry("RadProDevice", "RadProActivation", "upper" )
        if t != "WARNING":
            if t == "YES":
                gglobs.Devices["Rad Pro"][2] = True

            t = getConfigEntry("RadProDevice", "RadProPort", "str" )
            if t != "WARNING":
                if t.upper() == "AUTO":                 gglobs.RadProPort = "auto"
                else:                                   gglobs.RadProPort = t
                dprint(infostr.format("Serial Port",    gglobs.RadProPort))

            t = getConfigEntry("RadProDevice", "RadProSyncTime", "str" )
            if t != "WARNING":
                gglobs.RadProSyncTime = t
                dprint(infostr.format("Sync Time",      gglobs.RadProPort))


        break # still in while loop, don't forget to break!


    setIndent(0)

# End Configuration file evaluation #############################################################################
#################################################################################################################


def readPrivateConfig():
    """reads the private.cfg file if present, and adds the definitions to the config.
    If not present, the geigerlog.cfg settings remain in use unmodified"""

    # the private file uses this format (Telegram is not used):
    # gglobs.WiFiSSID, gglobs.WiFiPassword, gglobs.gmcmapUserID, gglobs.gmcmapCounterID, gglobs.TelegramToken
    # like:
    #       mySSID, myPW, 012345, 01234567890, 2008102243:AAHGv...kG9Pg1rfVY

    fncname  = "readPrivateConfig: "
    filepath = os.path.join(gglobs.progPath, "../private.cfg")
    dprint(fncname)
    setIndent(1)

    if not os.access(filepath, os.R_OK) :
        dprint("{:25s}: {}".format(fncname, "Private file is not readable"))
    else:
        dprint("{:25s}: {}".format(fncname, "Private file is readable"))
        try:
            with open(filepath) as f:
                filecfg = f.readlines()
        except Exception as e:
            msg = fncname + "FAILURE reading Private file"
            exceptPrint(e, msg)

        try:
            foundData = False
            for i, line in enumerate(filecfg):
                a = line.strip()
                if   a.startswith("#"): continue
                elif a == "":           continue
                else:
                    gdprint("{:25s}: {}".format(fncname, "line: {}:  {}".format(i, a[:-1])))
                    data = a.split(",")
                    if len(data) >= 4: # excluding Telegram
                        gglobs.WiFiSSID         = data[0].strip()
                        gglobs.WiFiPassword     = data[1].strip()
                        gglobs.gmcmapUserID     = data[2].strip()
                        gglobs.gmcmapCounterID  = data[3].strip()
                        # gglobs.TelegramToken    = data[4].strip()
                        foundData = True
                    else:
                        dprint("{:25s}: {}".format(fncname, "Not enough data in Private file"))

            if not foundData:
                dprint("{:25s}: {}".format(fncname, "Invalid Private file"))

        except Exception as e:
            msg = fncname + "FAILURE interpreting Private file"
            exceptPrint(e, msg)

    setIndent(0)

