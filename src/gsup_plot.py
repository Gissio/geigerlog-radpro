#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
gsup_plot.py - GeigerLog commands to plot data collected from from Geiger Counter

include in programs with:
    include gsup_plot

Data in the form:
    #Index  Date&Time             CPM, CPS, ...
        12, 2017-01-11 11:01:33,  117,   2, ...
        13, 2017-01-11 11:02:33,  120,   3, ...
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

from   gsup_utils       import *

# keep - had been used for legend placement
# legendPlacement = {0:'upper left',   1:'upper center', 2:'upper right',
#                    3:'center right', 4:'lower right',  5:'lower center',
#                    6:'lower left',   7:'center left',  8:'center'}


def getTimeSinceFirstRecord(Tfirst, Tdelta):
    """Get Time since first record in best unit;
    used only in function updatecursorposition"""

    l = Tdelta - Tfirst

    if   l              > 3:
        unit = "day"
        t = l
    elif l * 24         > 3:
        unit = "hour"
        t = l * 24
    elif l * 1440       > 3:
        unit = "minute"
        t = l * 1440
    else:
        unit = "second"
        t = l * 86400

    #print "t, unit:", t, unit

    return "{:0.3f} {}s".format(t, unit)


def getTimeOfDay(Tfirst, delta, deltaUnit):
    """From time of first record = Tfirst plus the delta time in days
    return TimeOfDay; used only in function updatecursorposition"""

    if   deltaUnit == "hour":       x = delta / 24.
    elif deltaUnit == "minute":     x = delta / 24. / 60.
    elif deltaUnit == "second":     x = delta / 24. / 60. / 60.
    else:                           x = delta # delta is in the correct unit day

    ret = str(mpld.num2date(Tfirst + x))[:19]
    #print("getToD: ret:", ret)

    return ret

# not used any more - keep (just in case)
# def getXLabelsToD():
#     """find proper label for x-axis and x-ticks when gglobs.Xunit == "Time";
#     used only in gsup_plot.makePlot"""

#     global plotTime, strFirstRecord

#     #~totalDays     = (plotTime.max() - plotTime.min()) # in days

#     #~if   totalDays                  > 5:    tformat = '%Y-%m-%d'            # > 5 d
#     #~elif totalDays                  > 1:    tformat = '%Y-%m-%d  %H:%M:%S'  # > 1 d
#     #~elif totalDays * 24             > 1:    tformat = '%Y-%m-%d  %H:%M:%S'  # > 1 h
#     #~elif totalDays * 24 * 60        > 1:    tformat = '%H:%M:%S'            # > 1 min
#     #~elif totalDays * 24 * 60 * 60   > 1:    tformat = '%H:%M:%S'            # > 1 sec
#     #~else:                                   tformat = '%Y-%m-%d  %H:%M:%S'  # else
#     #~#print("getXLabelsToD: ret: ", tformat, 'Time (First Record: {})'.format(strFirstRecord))

#     tformat = '%Y-%m-%d  %H:%M:%S'  # always the same full format
#     return tformat, 'Time (First Record: {})'.format(strFirstRecord)


def getXLabelsSince(Xunit):
    """find proper label for x-axis and x-ticks when gglobs.Xunit other than "Time";
    used only in gsup_plot.makePlot"""

    global plotTime, strFirstRecord

    #print("getXLabelsSince: gglobs.XunitCurrent:", gglobs.XunitCurrent)

    oldXunit = gglobs.XunitCurrent
    newXunit = Xunit

    if Xunit == "auto":
        l = plotTime.max() - plotTime.min()
        #print l

        if   l / 30.42  > 3:       newXunit = "month"
        elif l / 7      > 3:       newXunit = "week"
        elif l          > 3:       newXunit = "day"
        elif l * 24     > 3:       newXunit = "hour"
        elif l * 1440   > 3:       newXunit = "minute"
        else:                      newXunit = "second"

    gglobs.XunitCurrent = newXunit

    # now we have the new Xunit or "auto" was not requested
    # rescale the time and prepare label for the x axis
    # plotTime is in days
    if   newXunit == "second":
        plotTime = plotTime * 86400
        xlabel = '[seconds]'

    elif newXunit == "minute":
        plotTime = plotTime * 1440      # convert to minutes
        xlabel = '[minutes]'

    elif newXunit == "hour":
        plotTime = plotTime * 24        # convert to hours
        xlabel = '[hours]'

    elif newXunit == "day":
        plotTime = plotTime             # is in days already
        xlabel = '[days]'

    elif newXunit == "week":
        plotTime = plotTime / 7         # is in days convert to weeks
        xlabel = '[weeks]'

    elif newXunit == "month":
        plotTime = plotTime / 30.42     # is in days convert to months; 365 / 12 = 30.4167
        xlabel = '[months]'

    else:
        # no change
        plotTime = plotTime
        xlabel = '[days]'


    if newXunit != oldXunit:
        factorlookup = {"second":86400, "minute":1440, "hour":24, "day":1, "week":1/7, "month":1/30.42}
        oldfactor    = factorlookup[oldXunit]
        newfactor    = factorlookup[newXunit]
        if gglobs.Xleft != None:
            try:
                xleft = float(gglobs.Xleft)
                gglobs.Xleft = xleft / oldfactor * newfactor # convert all to days, then to new unit
            except Exception as e:
                exceptPrint(e, "xleft")
                gglobs.Xleft = None

        if gglobs.Xright != None:
            try:
                xright = float(gglobs.Xright)
                gglobs.Xright = xright / oldfactor * newfactor # convert all to days, then to new unit
            except Exception as e:
                exceptPrint(e, "xright")
                gglobs.Xright = None

        strxl = "{:1.8f}".format(float(gglobs.Xleft) ) if gglobs.Xleft  != None else ""
        strxr = "{:1.8f}".format(float(gglobs.Xright)) if gglobs.Xright != None else ""
        gglobs.exgg.xmin.setText(strxl)
        gglobs.exgg.xmax.setText(strxr)

    return 'time {} since first record: {}'.format(xlabel, strFirstRecord)


def changeTimeUnitofPlot(newXunit):
    """recalc xmin, xmax on Time unit changes"""

    #print("-----------------------changedGraphTimeUnit: i:", i)

    if np.all(gglobs.logTime) == None: return

    oldXunit = gglobs.XunitCurrent
    #print("changedGraphTimeUnit: oldXunit: ", oldXunit)

    # convert all entries to days since start
    if   oldXunit == "Time":
        if gglobs.Xleft  != None: gglobs.Xleft  = gglobs.Xleft  - gglobs.logTimeFirst
        if gglobs.Xright != None: gglobs.Xright = gglobs.Xright - gglobs.logTimeFirst

    elif oldXunit == "month":
        if gglobs.Xleft  != None: gglobs.Xleft  = gglobs.Xleft  * 30.42 # 365 / 12 = 30.4167
        if gglobs.Xright != None: gglobs.Xright = gglobs.Xright * 30.42 # 365 / 12 = 30.4167

    elif oldXunit == "week":
        if gglobs.Xleft  != None: gglobs.Xleft  = gglobs.Xleft  * 7
        if gglobs.Xright != None: gglobs.Xright = gglobs.Xright * 7

    elif oldXunit == "day": # no changes all in days
        if gglobs.Xleft  != None: gglobs.Xleft  = gglobs.Xleft
        if gglobs.Xright != None: gglobs.Xright = gglobs.Xright

    elif oldXunit == "hour":
        if gglobs.Xleft  != None: gglobs.Xleft  = gglobs.Xleft  / 24.
        if gglobs.Xright != None: gglobs.Xright = gglobs.Xright / 24.

    elif oldXunit == "minute":
        if gglobs.Xleft  != None: gglobs.Xleft  = gglobs.Xleft  / 1440.
        if gglobs.Xright != None: gglobs.Xright = gglobs.Xright / 1440.

    elif oldXunit == "second":
        if gglobs.Xleft  != None: gglobs.Xleft  = gglobs.Xleft  / 86400.
        if gglobs.Xright != None: gglobs.Xright = gglobs.Xright / 86400.

    #~gglobs.XunitCurrent = str(self.xunit.currentText())
    #~print("changedGraphTimeUnit: gglobs.XunitCurrent: ", gglobs.XunitCurrent)
    #~newXunit            = gglobs.XunitCurrent
    #newXunit            = self.xunit.currentText()
    if newXunit == "auto":
        l = gglobs.logTime.max() - gglobs.logTime.min()
        #print "l=", l
        if   l         > 3:  Xunit = "day"
        elif l * 24.   > 3:  Xunit = "hour"
        elif l * 1440. > 3:  Xunit = "minute"
        else:                Xunit = "second"

        newXunit = Xunit

    gglobs.XunitCurrent = newXunit
    #~print("changedGraphTimeUnit: gglobs.XunitCurrent: ", gglobs.XunitCurrent)
    gglobs.Xunit        = newXunit
    #print( "newXunit", newXunit)

    if newXunit == "Time":
        if gglobs.Xleft  != None: gglobs.Xleft =  (str(mpld.num2date((gglobs.Xleft  + gglobs.logTimeFirst))))[:19]
        if gglobs.Xright != None: gglobs.Xright = (str(mpld.num2date((gglobs.Xright + gglobs.logTimeFirst))))[:19]

    elif newXunit == "month":
        if gglobs.Xleft  != None: gglobs.Xleft  = gglobs.Xleft  / 30.42 # 365 / 12 = 30.4167
        if gglobs.Xright != None: gglobs.Xright = gglobs.Xright / 30.42 # 365 / 12 = 30.4167

    elif newXunit == "week":
        if gglobs.Xleft  != None: gglobs.Xleft  = gglobs.Xleft  / 7
        if gglobs.Xright != None: gglobs.Xright = gglobs.Xright / 7

    elif newXunit == "day": # no changes all in days
        if gglobs.Xleft  != None: gglobs.Xleft  = gglobs.Xleft
        if gglobs.Xright != None: gglobs.Xright = gglobs.Xright

    elif newXunit == "hour":
        if gglobs.Xleft  != None: gglobs.Xleft  = gglobs.Xleft  * 24
        if gglobs.Xright != None: gglobs.Xright = gglobs.Xright * 24

    elif newXunit == "minute":
        if gglobs.Xleft  != None: gglobs.Xleft  = gglobs.Xleft  * 1440
        if gglobs.Xright != None: gglobs.Xright = gglobs.Xright * 1440

    elif newXunit == "second":
        if gglobs.Xleft  != None: gglobs.Xleft  = gglobs.Xleft  * 86400
        if gglobs.Xright != None: gglobs.Xright = gglobs.Xright * 86400

    if gglobs.Xleft == None:
        gglobs.exgg.xmin.setText("")
    else:
        try:    xl = "{:1.8f}".format(float(gglobs.Xleft))
        except: xl = gglobs.Xleft
        gglobs.exgg.xmin.setText(xl)

    if gglobs.Xright == None:
        gglobs.exgg.xmax.setText("")
    else:
        try:    xr = "{:1.8f}".format(float(gglobs.Xright))
        except: xr = gglobs.Xright
        gglobs.exgg.xmax.setText(xr)


def makePlot(gcurrentDBData = None):
    """Plots the data in array gcurrentDBData vs. time-of-day or
    vs time since start, observing plot settings;
    using matplotlib date functions

    Return: nothing or PlotMsg
    """

    # local function ###########################################
    def clearFigure():
        """löscht die main fig"""

        # DEVEL  : ...503    clearFigure() 1: takes: 0.042 ms
        # DEVEL  : ...504    clearFigure() 2: takes: 36.701 ms

        global fig

        # start = time.time()
        fig = plt.figure(1)
        # cdprint("clearFigure() 1: takes: {:0.3f} ms".format(1000 * (time.time() - start)))

        # start = time.time()
        plt.clf()                                # is REQUIRED, kostet 30 ... 50 ms
        # cdprint("clearFigure() 2: takes: {:0.3f} ms".format(1000 * (time.time() - start)))

        # start = time.time()
        fig.canvas.draw_idle()                   # is REQUIRED. kostet 0.04 ms
        # cdprint("clearFigure() draw idle: takes: {:0.3f} ms".format(1000 * (time.time() - start)))

    # end local function ###########################################

    global plotTime, strFirstRecord, rdplt, fig, ax1, ax2, xFormatStr

    startMkPlt = time.time()            # timing durations
    fncname    = "makePlot: "

    if not gglobs.allowGraphUpdate            : return

    if gcurrentDBData is None:
        gcurrentDBData = gglobs.currentDBData
        # edprint(fncname + "gcurrentDBData is None")
        # playWav("err")

    #print(fncname, "-"*100)
    #~print(fncname + "  gcurrentDBData.shape:",   gcurrentDBData.shape)
    #~print(fncname + "  gcurrentDBData:\n",       gcurrentDBData)
    #~print(fncname + "  gglobs.logDBData:\n",     gglobs.logDBData)
    #~print(fncname + "  gglobs.hisDBData:\n",     gglobs.hisDBData)

    if np.all(gcurrentDBData) == None   : return

    try:
        if gcurrentDBData.size == 0:
            dprint(fncname + "no records; nothing to plot")
            clearFigure()
            return
    except Exception as e:
        # if there is no gcurrentDBData then .size results in error
        # but then there is also nothing to plot
        msg = fncname + "no 'gcurrentDBData', nothing to plot"
        exceptPrint(e, msg)
        efprint(msg)
        clearFigure()
        return

    #clear the checkboxes' default ToolTip
    for vname in gglobs.varsCopy:
        gglobs.exgg.varDisplayCheckbox[vname].setToolTip(gglobs.varsCopy[vname][0])


    # NOTE:
    # Before Matplotlib 3.3, the epoch was 0000-12-31T00:00:00 which lost
    # modern microsecond precision and also made the default axis limit of 0
    # an invalid datetime.
    # In 3.3 time the epoch was changed to 1970-01-01T00:00:00 with
    # 0.35 microsecond resolution.
    # To convert old ordinal floats to the new epoch, users can do:
    #     new_ordinal = old_ordinal + mdates.date2num(np.datetime64('0000-12-31'))
    TimeBaseCorrection      = mpld.date2num(np.datetime64('0000-12-31'))        # = -719163.0
    #print(fncname + "TimeBaseCorrection: ", TimeBaseCorrection)
    gglobs.logTime          = gcurrentDBData[:,0] + TimeBaseCorrection          # time data of total file
    gglobs.logTimeFirst     = gglobs.logTime[0]                                 # time of first record in total file
    gglobs.logTimeDiff      = gglobs.logTime - gglobs.logTimeFirst              # using time diff to first record in days


    # get time of first record, properly rounded
    try:
        # get the time of first record
        ltf = (mpld.num2date(gglobs.logTimeFirst))
    except Exception as e:
        msg = fncname + "ERROR: incorrect value in 'gglobs.logTimeFirst', cannot plot"
        exceptPrint(e, msg)
        efprint(msg)
        clearFigure()
        return

    # rounding the time
    # mpld.num2date(gglobs.logTimeFirst) delivers date with sec fractions, like:
    # 2019-01-02 18:05:00.999980+00:00
    # but does not allow rounding to a second. Therefore cutting off after 19
    # chars (before the '.')  may yield a time too low by 1 second, like:
    # 2019-01-02 18:05:00 instead of:
    # 2019-01-02 18:05:01
    F0 = ltf.strftime("%Y-%m-%d %H:%M:%S.%f")
    #print("F0: ", F0)
    try:
        # good! 2020-08-18 16:34:11.609016 -> 2020-08-18 16:34:12
        # has been rounded up
        strFirstRecord = "{}{:02.0f}".format(F0[:17], float(F0[17:])) # good!

    except Exception as e:
        #exceptPrint(e, "TEST")
        # bad! 2020-08-18 16:34:11.609016 -> 2020-08-18 16:34:11
        # should have been rounded up
        strFirstRecord = F0[:19]
    #~print("F0: ", F0, "reduced to: ", strFirstRecord)


    # define the data source and label for the X-axis,
    # either Time-since-epoch 0001-01-01 or Time-since-start in days
    # labels need strFirstRecord !
    if gglobs.Xunit == "Time" :
        plotTime                = gglobs.logTime
        xFormatStr              = "%Y-%m-%d  %H:%M:%S"      # always the same full format,
                                                            # not using XLabelsToD()!
        xLabelStr               = "Time (First Record: {})".format(strFirstRecord)
    else:
        plotTime                = gglobs.logTimeDiff
        xLabelStr               = getXLabelsSince(gglobs.Xunit)

    # split multi-dim np.array into 10 single-dim np.arrays like log["CPM"] = [<var data>]
    log = {}
    for i, vname in enumerate(gglobs.varsCopy):
        log[vname] = gcurrentDBData[:, i + 1]
        #print("{}: log[{}]: {}".format(i, vname, log[vname]))

    # is the temperature to be shown in °C or °F ? (data are in °C )
    if gglobs.varsCopy["Temp"][2] == "°F":        log["Temp"] = log["Temp"] / 5 * 9 + 32

    # confine limits to what is available
    Xleft = gglobs.Xleft
    Xright= gglobs.Xright

    #dprint("before re-setting limits: Xleft, Xright, plotTime.min, plotTime.max   {}   {}   {}   {}".format(gglobs.Xleft, gglobs.Xright, plotTime.min(), plotTime.max()))
    if Xright == None or Xright > plotTime.max():    Xright = plotTime.max()
    if                   Xright < plotTime.min():    Xright = plotTime.min()
    if Xleft  == None or Xleft  < plotTime.min():    Xleft  = plotTime.min()
    if                   Xleft  > plotTime.max():    Xleft  = plotTime.max()
    #dprint("after                                                                 {}   {}   {}   {}".format(Xleft, Xright, plotTime.min(), plotTime.max()))

    # find the records, where the time limits apply
    recmin = np.where(plotTime >= Xleft )[0][0]
    recmax = np.where(plotTime <= Xright)[0].max() # excludes recs > gglobs.Xleft, and takes max of remaining
    #dprint("recmin, recmax:", recmin, recmax)

    # slice the arrays; include record #recmax (thus +1)
    gglobs.logTimeSlice         = gglobs.logTime     [recmin:recmax + 1 ]
    gglobs.logTimeDiffSlice     = gglobs.logTimeDiff [recmin:recmax + 1 ]
    x                           = plotTime           [recmin:recmax + 1 ]   # plotTime is either Time or TimeDiff

    if gglobs.logTimeSlice.size == 0:
        fprint("ALERT: No records in selected range")
        return

    logSlice        = {}
    for vname in gglobs.varsCopy:
        logSlice[vname] = log[vname][recmin:recmax + 1 ]
    gglobs.logSlice = logSlice

    stopprep   = time.time()
    stopwatch  = "{:0.1f} ms data load and prep".format((stopprep - startMkPlt) * 1000)

    ###########################################################################
    # prepare the graph
    ###########################################################################
    gglobs.plotIsBusy = True

    clearFigure()

    # get/set left and right Y-axis
    ax1 = plt.gca()                           # left Y-axis
    ax2 = ax1.twinx()                         # right Y-Axis

    vnameselect   = list(gglobs.varsCopy)[gglobs.exgg.select.currentIndex()]

    # The 'b' parameter of grid() has been renamed 'visible' since Matplotlib 3.5;
    # support for the old name will be dropped two minor releases later.
    if vnameselect in ("CPM", "CPS", "CPM1st", "CPS1st", "CPM2nd", "CPS2nd", "CPM3rd", "CPS3rd"):
        ax1.grid(visible=True, axis="both")         # left Y-axis grid + X-grid
    else:
        ax1.grid(visible=True, axis="x")            # X-axis grid
        ax2.grid(visible=True, axis="y")            # right Y-axis grid

    mysubTitle = os.path.basename(gglobs.currentDBPath) + "   " + "Recs:" + str(gglobs.logTimeSlice.size)
    plt.title(mysubTitle, fontsize= 9, fontweight='normal', loc = 'right')

    plt.subplots_adjust(hspace=None, wspace=None , left=0.15, top=0.84, bottom=0.10, right=.87)

    # avoid "offset" and "scientific notation" on the Y-axis
    # i.e. showing scale in exponential units
    # https://stackoverflow.com/questions/28371674/prevent-scientific-notation-in-matplotlib-pyplot
    ax1.ticklabel_format(useOffset=False, style='plain', axis='x')
    ax1.ticklabel_format(useOffset=False, style='plain', axis='y')
    ax2.ticklabel_format(useOffset=False, style='plain', axis='x')
    ax2.ticklabel_format(useOffset=False, style='plain', axis='y')

    # make ticks red
    # for larger numbers use option: "labelsize='medium'"
    # ax2.tick_params(axis='y', colors='red')

    # hide the cursor position from showing in the toolbar
    ax1.format_coord = lambda x, y: ""
    ax2.format_coord = lambda x, y: ""

    #
    # add labels to all three axis
    #
    # X-axis
    ax1.set_xlabel(xLabelStr, fontsize=10, fontweight='bold')

    # Y1-axis
    if gglobs.Yunit == "CPM":   ylabel = "Counter  [CPM or CPS]"
    else:                       ylabel = "Counter  [µSv/h]"
    ax1.set_ylabel(ylabel,      fontsize=12, fontweight='bold')

    # Y2-axis
    ax2.set_ylabel("Ambient",   fontsize=12, fontweight='bold')

    #
    # set the µSv-scaling factor
    #
    scale = [None] * 4
    for i in range(0, 4):
        if gglobs.Sensitivity[i] == "auto":  scale[i] = 1 / gglobs.DefaultSens[i]
        else:                                scale[i] = 1 / gglobs.Sensitivity[i]

    scaleFactor = {}
    for i, vname in enumerate(gglobs.varsCopy):
        if   vname in ("CPM", "CPS"):
            if gglobs.Yunit == "CPM":
                scaleFactor[vname] = 1.0
            else: # gglobs.Yunit == "µSv/h"
                scaleFactor[vname]    = scale[0]
                scaleFactor['CPS']    = scale[0] * 60

        elif vname in ("CPM1st", "CPS1st"):
            if gglobs.Yunit == "CPM":
                scaleFactor[vname] = 1.0
            else: # gglobs.Yunit == "µSv/h"
                scaleFactor[vname]    = scale[1]
                scaleFactor['CPS1st'] = scale[1] * 60

        elif vname in ("CPM2nd", "CPS2nd"):
            if gglobs.Yunit == "CPM":
                scaleFactor[vname] = 1.0
            else: # gglobs.Yunit == "µSv/h"
                scaleFactor[vname]    = scale[2]
                scaleFactor["CPS2nd"] = scale[2] * 60

        elif vname in ("CPM3rd", "CPS3rd"):
            if gglobs.Yunit == "CPM":
                scaleFactor[vname] = 1.0
            else: # gglobs.Yunit == "µSv/h"
                scaleFactor[vname]    = scale[3]
                scaleFactor["CPS3rd"] = scale[3] * 60

        else:
            scaleFactor[vname] = 1.0
    #print("scaleFactor:", type(scaleFactor), scaleFactor)

    #
    # set the plotting style
    #
    # each variable gets a copy of the plotstyle, which is then corrected for
    # the color chosen for each variable
    plotalpha        = 1.0
    plotstyle        = {'color'             : gglobs.linecolor,     # overwritten by Style from varsCopy
                        'linestyle'         : gglobs.linestyle,     # overwritten by Style from varsCopy
                        'linewidth'         : gglobs.linewidth,
                        'label'             : "",
                        'markeredgecolor'   : gglobs.linecolor,     # overwritten by Style from varsCopy
                        'marker'            : gglobs.markersymbol,
                        'markersize'        : gglobs.markersize,
                        'alpha'             : plotalpha,
                        }

    varPlotStyle    = {}    # holds the plotstyle for each variable
    for i, vname in enumerate(gglobs.varsCopy):
        varPlotStyle[vname]                       = plotstyle.copy()
        varPlotStyle[vname]['color']              = gglobs.varsCopy[vname][3]
        varPlotStyle[vname]['markeredgecolor']    = gglobs.varsCopy[vname][3]
        varPlotStyle[vname]['linestyle']          = gglobs.varsCopy[vname][4]

    #
    # Emphasize the selected variable by color and line thickness and draw last (on top)
    #
    # the selected var will be drawn with thicker lines and full brightness, other lines
    # will be dimmed in color via alpha setting.
    # Plot the selected variable last, i.e. on top of all others, by ordering varnames
    vname_ordered = ()
    vnameselect   = list(gglobs.varsCopy)[gglobs.exgg.select.currentIndex()]

    # start GL with command 'graphemph' to get the demo variations of alpha and lw
    # which is:     alpha     = 1 -> not transparent
    #               linewidth = 2 -> all lines same big width
    if not gglobs.graphemph:
        corr_alpha  = 0.7
        corr_lw_sel = 2
        corr_lw_oth = 1
    else:
        corr_alpha  = 1
        corr_lw_sel = 2
        corr_lw_oth = 2

    for i, vname in enumerate(gglobs.varsCopy):
        # emphasize: select var in brighter, wider line
        if vname == vnameselect:
            varPlotStyle[vname]['alpha']     = plotalpha
            varPlotStyle[vname]['linewidth'] = float(varPlotStyle[vname]['linewidth']) * corr_lw_sel

        # de-emphasize: non-select var in dimmer, thinner line
        else:
            varPlotStyle[vname]['alpha']     = plotalpha * corr_alpha
            varPlotStyle[vname]['linewidth'] = float(varPlotStyle[vname]['linewidth']) * corr_lw_oth
            vname_ordered                   += (vname,)
        #print("----------vname, alpha, linewidth:", vname, varPlotStyle[vname]['alpha'], varPlotStyle[vname]['linewidth'])

    vname_ordered += (vnameselect,)
    #print("------vname_ordered:", vname_ordered)

    #
    # plot the data
    #
    varlines            = {}            # lines objects for legend
    gglobs.logSliceMod  = {}            # data; will be used by Stat, Poiss, FFT

    # use in SuSt like:"Variable  [Unit]      Avg ±StdDev   Variance     Min ... Max    Recs     Last")
    fmtLineLabel     = "{:8s}: {:7s}{:>9.3f} ±{:<9.3g} ±{:<6.1%} {:>8.3g} {:>7.5g} {:>7.5g} {:7d} {}"
    fmtLineLabelTip  = "{:s}: [{}]  Avg: {:<8.3f}  StdDev: {:<0.3g} ±{:<5.1%}    Variance: {:<0.3g}   Range: {:>0.6g} ... {:<0.6g}  Recs: {}   Last Value: {}"

    #arrprint(fncname + "logSlice:", logSlice)
    #arrprint(fncname + "scaleFactor:", scaleFactor)
    for vname in vname_ordered:
        # print("plot the data: vname:", vname)
        if gglobs.exgg.varDisplayCheckbox[vname].isChecked():
            #print("logSlice[vname]:", type(logSlice[vname]), logSlice[vname] )
            #print("scaleFactor[vname]:", type(scaleFactor[vname]), scaleFactor[vname] )
            y                           = logSlice[vname] * scaleFactor[vname]
            ymask                       = np.isfinite(y)      # mask for nan values
            var_y                       = y[ymask]
            var_x                       = x[ymask]

            gglobs.logSliceMod[vname]   = y  # will be used by Stat, Poiss, FFT

            var_size                    = var_y.size
            #print("vname: var_size:", vname, var_size)
            if var_size == 0: continue

            var_avg                     = np.nanmean(var_y)
            var_std                     = np.nanstd (var_y)
            if var_avg != 0:    var_stdpct = var_std / var_avg
            else:               var_stdpct = gglobs.NAN
            var_var                     = np.nanvar (var_y)
            var_max                     = np.nanmax (var_y)
            var_min                     = np.nanmin (var_y)
            var_size                    = var_y.size
            var_err                     = var_std / np.sqrt(var_size)
            var_recs                    = np.count_nonzero(~np.isnan(var_y))
            var_unit                    = gglobs.varsCopy[vname][2]
            var_lastval                 = "{:>7.5g}".format(gglobs.lastLogValues[vname])
            #print("var_lastval:", var_lastval)
            # edprint("var_avg : ", var_avg )

            gglobs.varStats[vname]      = fmtLineLabel   .format(vname, "[" + var_unit + "]", var_avg, var_std, var_stdpct, var_var, var_min, var_max, var_recs, var_lastval)
            Tip                         = fmtLineLabelTip.format(gglobs.varsCopy[vname][0], var_unit, var_avg, var_std, var_stdpct, var_var, var_min, var_max, var_recs, var_lastval)
            gglobs.exgg.varDisplayCheckbox[vname].setToolTip  (Tip)
            gglobs.exgg.varDisplayCheckbox[vname].setStatusTip(Tip)

            # set markersize to 0 when it is equal to linewidth (and thus marker not visible) to save plotting time
            # msize = float(plotstyle['markersize']) / np.sqrt(var_size)
            # if msize <= plotstyle['linewidth']: msize = 0

            # set markersize to 0 when more than 100 datapoints
            if var_size > 100: msize = 0
            else:              msize = float(plotstyle['markersize']) / np.sqrt(var_size)
            varPlotStyle[vname]['markersize'] = msize

            varlines[vname] = plotLine(var_x, var_y, gglobs.Xunit, vname, **varPlotStyle[vname])

    #
    # Plot the Moving Average
    #
    plotMovingAverage(x, logSlice, scaleFactor, varPlotStyle)

    #
    # Plot the Average and +/- 95% as horizontal lines
    #
    plotAverage(x, logSlice, scaleFactor, varPlotStyle)

    #
    # Plot the LinFit
    #
    plotLinFit(x, logSlice, scaleFactor, varPlotStyle)

    #
    # apply the Y-Limits
    #
    if   gglobs.Ymin  != None and gglobs.Ymax  != None:  ax1.set_ylim(bottom = gglobs.Ymin,     top = gglobs.Ymax)
    elif gglobs.Ymin  != None:                           ax1.set_ylim(bottom = gglobs.Ymin)
    elif                          gglobs.Ymax  != None:  ax1.set_ylim(                          top = gglobs.Ymax)

    if   gglobs.Y2min != None and gglobs.Y2max != None:  ax2.set_ylim(bottom = gglobs.Y2min,    top = gglobs.Y2max)
    elif gglobs.Y2min != None:                           ax2.set_ylim(bottom = gglobs.Y2min)
    elif                          gglobs.Y2max != None:  ax2.set_ylim(                          top = gglobs.Y2max)

    # limits are needed for calculation of the mouse pointer w respect to counter Y-axis
    # see: def updatecursorposition(self, event)
    gglobs.y1_limit = ax1.get_ylim()
    gglobs.y2_limit = ax2.get_ylim()
    #print("gglobs.y1_limit:", gglobs.y1_limit, ", gglobs.y2_limit:", gglobs.y2_limit)

    #
    # plot the legend
    #
    pp = ()
    pl = ()
    for vname in gglobs.varsCopy:
        p   = plt.Rectangle((0, 0), 1, 1, fc=gglobs.varsCopy[vname][3], ec="black", lw=0.2)
        pp += (p,)
        pl += (gglobs.varsCopy[vname][0],)
    plt.figlegend(pp, pl, shadow=False, mode="expand", handlelength=1.6, ncol=6, framealpha=0)

    #
    # refresh the figure
    #
    # start = time.time()
    #fig.canvas.draw_idle() # is that needed at all????  costs only 10 mikrosecond
    # vprint("Delta: ", (time.time() - start)*1000)

    figdone   = time.time()
    stopwatch += " + {:0.1f} ms graph draw".format((figdone - stopprep) * 1000)

    # finish
    stopwatch = "{} {:0.1f} ms = {}".format("makePlot: Total:", (time.time() - startMkPlt) * 1000, stopwatch)

    if not gglobs.logging: vprint(stopwatch)

    gglobs.plotIsBusy = False

    return stopwatch

#xyz
def plotLinFit(x, logSlice, scaleFactor, varPlotStyle):
    """Plot a Linear Fit to the selected variable data"""

    if not gglobs.fitChecked: return

    vname           = list(gglobs.varsCopy)[gglobs.exgg.select.currentIndex()]

    lSM_mask        = np.isfinite(logSlice[vname])          # mask for nan values
    logSliceNoNAN   = logSlice[vname][lSM_mask]             # all NANs removed
    if logSliceNoNAN.size < 3 : return                      # either no data, or not enough -> return

    x_NoNAN         = x[lSM_mask]                           # remove all x where data is nan

    if gglobs.exgg.varDisplayCheckbox[vname].isChecked():
        logSliceMod                  = logSliceNoNAN * scaleFactor[vname]
        # print("x_NoNAN: ", x_NoNAN)
        # print("logSliceMod:", logSliceMod)

        try:
            FitSelector = 1                                             # linear fit
            pfit        = np.polyfit(x_NoNAN, logSliceMod, FitSelector)
            FitFon      = np.poly1d(pfit)                               # Fit Function

            deltatime   = x_NoNAN[-1] - x_NoNAN[0]
            deltavalue  = pfit[0] * deltatime

            # cdprint("plotLinFit: pfit= {}  Delta plot: {:<+6.3g}".format(pfit, deltavalue))

        except Exception as e:
            msg = "plotScatter: pfit: Failure with Exception"
            exceptPrint(e, msg)
            efprint("\nFailure plotting LinFit. Exception: {}".format(e))
            return

        fit_plotstyle                = varPlotStyle[vname].copy()
        fit_plotstyle["linewidth"]   = 2
        fit_plotstyle["markersize"]  = 0

        fit_plotstyle2               = varPlotStyle[vname].copy()
        fit_plotstyle2["linewidth"]  = 5
        fit_plotstyle2["color"]      = "yellow"
        fit_plotstyle2["markersize"] = 0

        fit_plotstyle['label']       = "LinFit: {:0.4g} + {:0.4g} * time  [Delta plot: {:<+6.3g}]".format(pfit[1], pfit[0], deltavalue)

        y = FitFon(x)
        plotLine(x, y, gglobs.Xunit, vname,                  **fit_plotstyle2)   # make yellow shadow under line; plot first to keep it below line
        plotLine(x, y, gglobs.Xunit, vname, drawlegend=True, **fit_plotstyle)


def plotAverage(x, logSlice, scaleFactor, varPlotStyle):
    """Plot the Average and +/- 95% as horizontal lines"""

    if not gglobs.avgChecked: return

    vname     = list(gglobs.varsCopy)[gglobs.exgg.select.currentIndex()]
    #print("average: vname, gglobs.exgg.varDisplayCheckbox[vname].isChecked():", vname, gglobs.exgg.varDisplayCheckbox[vname].isChecked())
    if gglobs.exgg.varDisplayCheckbox[vname].isChecked():
        avg_Time                     = np.array([x[0], x[-1]])
        #print("plotAverage: avg_Time: ", avg_Time)

        logSliceMod                  = logSlice[vname] * scaleFactor[vname]
        #print("logSliceMod:", logSliceMod)

        avg_avg                      = np.nanmean(logSliceMod)

        if avg_avg >= 0:    avg_std = np.sqrt(avg_avg)  # this is std.dev derived from avg!
        else:               avg_std = gglobs.NAN        # not valid for neg numbers
        #print("---Avg: {}, StdDev of Data: {:6.3f}, SQRT(avg): {:6.3f}".format(avg_avg, np.nanstd (logSliceMod), avg_std))

        # limit 2 sigma: https://en.wikipedia.org/wiki/68%E2%80%9395%E2%80%9399.7_rule
        #                https://en.wikipedia.org/wiki/1.96
        avg_CPMS                     = np.array([avg_avg, avg_avg]) # MUST use np.aray!
        avg_plotHiLo = False
        if avg_avg >= 0:
            avg_CPMS_lo              = avg_CPMS - avg_std * 1.96
            avg_CPMS_hi              = avg_CPMS + avg_std * 1.96
            avg_plotHiLo             = (avg_avg - avg_std * 1.96) > 0 # flag to plot 95%

        if vname in ("Temp", "Press", "Humid"): avg_plotHiLo = False # no limits drawn for Temp, Press, Humid

        avg_plotstyle                = varPlotStyle[vname].copy()
        avg_plotstyle["linewidth"]   = 2
        avg_plotstyle["markersize"]  = 0
        avg_plotstyle['label']       = "Avg: {:0.4g}  ".format(avg_avg)

        avg_plotstyle2               = varPlotStyle[vname].copy()
        avg_plotstyle2["linewidth"]  = 5
        avg_plotstyle2["color"]      = "yellow"
        avg_plotstyle2["markersize"] = 0
        avg_plotstyle2['label']       = None

        plotLine(avg_Time, avg_CPMS, gglobs.Xunit, vname, drawlegend=False, **avg_plotstyle2) # make yellow shadow under line
        plotLine(avg_Time, avg_CPMS, gglobs.Xunit, vname, drawlegend=True,  **avg_plotstyle)

        if avg_plotHiLo :
            # plot dashed lin color of var, interrupted by white dots
            # makes it visible on white and on var color
            avg_plotstyle["linestyle"]  = "--"
            avg_plotstyle['label']       = None
            plotLine(avg_Time, avg_CPMS_lo, gglobs.Xunit, vname, drawlegend=False, **avg_plotstyle)
            plotLine(avg_Time, avg_CPMS_hi, gglobs.Xunit, vname, drawlegend=False, **avg_plotstyle)

            avg_plotstyle["color"]      = "white"
            avg_plotstyle["linestyle"]  = ":"
            plotLine(avg_Time, avg_CPMS_lo, gglobs.Xunit, vname, drawlegend=False, **avg_plotstyle)
            plotLine(avg_Time, avg_CPMS_hi, gglobs.Xunit, vname, drawlegend=False, **avg_plotstyle)


def plotMovingAverage(x, logSlice, scaleFactor, varPlotStyle):
    """Plot the Moving Average"""

    # Plot the moving average over with a thin line in the variable's color on a yellow thick line background.
    # Do the average over no more than N/2 data points. Determine N from time delta between first and last
    # record and the number of records.
    # Note: improper with long periods of no data, or changing cycle time!
    # In plot skip the first and last N/2 data points, which are meaningless due to averaging.

    fncname = "plotMovingAverage: "

    # is MvAvg checked?
    if not gglobs.mavChecked: return

    # enough data?
    logTimeDelta    = gglobs.logTimeSlice.max() - gglobs.logTimeSlice.min()   # total log time in days
    if logTimeDelta == 0: return                                              # not enough data, return

    # selected variable
    vname           = list(gglobs.varsCopy)[gglobs.exgg.select.currentIndex()]

    # enough non-NAN data?
    lSM_mask        = np.isfinite(logSlice[vname])                            # mask for nan values
    logSliceNoNAN   = logSlice[vname][lSM_mask]                               # all NANs removed
    if logSliceNoNAN.size == 0:      return                                   # no data remaining for vname, return

    # apply scale factor
    logSliceMod     = logSliceNoNAN * scaleFactor[vname]

    # get max/min averaging period
    x_mav           = x[lSM_mask]
    x_mav_size      = x_mav.size                        # no of records
    logTime         = 86400.0 * logTimeDelta            # total log time in sec
    logCycleSec     = logTime / x_mav_size              # average cycle time in sec
    minMvAvgSec     = logCycleSec * 1                   # min sec for MvAvg, -> 1 datapoint
    maxMvAvgSec     = logCycleSec * (x_mav_size / 2)    # max sec for MvAvg, -> half of max datapoints
    # print("x_mav_size {}, logTime {}, logCycleSec {}, minMvAvgSec {}, maxMvAvgSec {}".format(x_mav_size, logTime, logCycleSec, minMvAvgSec, maxMvAvgSec))

    if   gglobs.mav < minMvAvgSec:  mvsecs = minMvAvgSec
    elif gglobs.mav > maxMvAvgSec:  mvsecs = maxMvAvgSec
    else:                           mvsecs = gglobs.mav

    Nmav     = max(1, round(mvsecs / minMvAvgSec))
    newMvAvg = Nmav * logCycleSec
    #dprint("Currently set limit: N={:0.0f} datapoints".format(Nmav))

    try:
        MvAvgEntry = gglobs.exgg.mav.text().replace(",", ".").replace("-", "")
        val = float(MvAvgEntry)  # can value be converted to float?
    except Exception as e:
        MvAvgFail       = True
        if MvAvgEntry > "": # ignore blank entries
            msg = "MvAvg: Enter numeric values >0 for Moving Average period in seconds!"
            exceptPrint(e, fncname + msg)
            efprint(msg)

    lower    = int(Nmav/2)
    upper    = int(x_mav_size - (Nmav / 2))
    #dprint("Nmav: {}, lower: {}, upper: {}, delta:: {}".format(Nmav, lower, upper, upper - lower))

    if upper - lower > 2: # needs more than a single record
        if gglobs.exgg.varDisplayCheckbox[vname].isChecked():

            mav_x = x_mav[lower:upper]

            mav_y =   np.convolve(logSliceMod,     np.ones((Nmav,))/Nmav, mode='same')[lower:upper]
            # mav_y = np.convolve(logSliceMod,     np.ones((Nmav,))/Nmav, mode='full')[lower:upper]
            # mav_y = np.convolve(logSliceMod,     np.ones((Nmav,))/Nmav, mode='valid')[lower:upper]

            mav_plotstyle               = varPlotStyle[vname].copy()
            mav_plotstyle['markersize'] = 0

            # draw yellow background
            mav_plotstyle['color']      = 'yellow'
            mav_plotstyle['linewidth']  = 5
            plotLine(mav_x, mav_y, gglobs.Xunit, vname, **mav_plotstyle)

            # draw line in vname color
            mav_plotstyle['color']      = varPlotStyle[vname]['color']
            mav_plotstyle['linewidth']  = 2
            mav_plotstyle['label']      = "MvAvg {:0.4g} sec (N={:0.0f})".format(newMvAvg, Nmav)
            plotLine(mav_x, mav_y, gglobs.Xunit, vname, drawlegend=True, **mav_plotstyle)   # line

    else:
        fprint("ALERT: Not enough data to plot Moving Average")


def plotLine(x, y, xunit="Time", vname="CPM", drawlegend=False, **plotstyle):
    """plots a single line of data"""

    # ATTENTION:
    # Different definitions for "plot" and "plot_date":
    #     matplotlib.pyplot.plot     (*args, scalex=True, scaley=True, data=None, **kwargs)
    #     matplotlib.pyplot.plot_date(x, y, fmt='o', tz=None, xdate=True, ydate=False, *, data=None, **kwargs)
    # Note that plot_date has "fmt='0'", while plot has not!
    # Using "**plotstyle" results in Warning:
    #     UserWarning: marker is redundantly defined by the 'marker' keyword argument and the fmt string "o"
    #     (-> marker='o'). The keyword argument will take precedence.
    # --> must handle the two plot types differently

    global xFormatStr

    # select Y-axis
    if vname in ("CPM", "CPS", "CPM1st", "CPS1st", "CPM2nd", "CPS2nd", "CPM3rd", "CPS3rd"):
        yaxis  = ax1
    else: # Temp, Press, Humid, Xtra
        yaxis  = ax2

    # Graph scaling:  scaleVarValues(variable, value, scale), with scale like: LOG10(val)
    y = scaleVarValues(vname,    y,     gglobs.GraphScale[vname])

    if xunit == "Time":
        fig.autofmt_xdate(rotation = 15)
        #formatter   = mpld.AutoDateFormatter(mpld.AutoDateLocator()) # What for?
        yaxis.xaxis.set_major_formatter(mpld.DateFormatter(xFormatStr))
        ax1.xaxis.set_tick_params(labelsize=8)   # ax1 defines the size of the labels
        #ax2.xaxis.set_tick_params(labelsize=8)  # ax2 appears to be not relevant

        # X-Label positioning: (the label like: Time (First Record: ...)
        # you can move the location of axis labels using set_label_coords.
        # The coords you give it are x and y, and by default the transform
        # is the axes coordinate system: so (0,0) is (left,bottom), (0.5, 0.5)
        # is in the middle, etc.
        #    yaxis.xaxis.set_label_coords(0.5, -0.25)

        # correction of plotstyle:
        psc = plotstyle.copy()                                              # make a copy
        del psc["marker"]                                                   # remove marker
        # print("plotLine: Time plotstyle: markersize", psc["markersize"])
        # print("plotLine: Time plotstyle: marker    ", psc["marker"])      # "marker" is gone

        line,  = yaxis.plot_date (x, y, fmt=gglobs.markersymbol, **psc)     # add markersymbol to 'fmt'
        # print("plotLine: Time plotstyle:", psc)                           # "marker" is gone
        # --> psc: {'color': 'deepskyblue', 'linestyle': 'solid', 'linewidth': 2.0, 'label': '', 'markeredgecolor': 'deepskyblue', 'markersize': 6.123724356957946, 'alpha': 0.9}

    else:
        line,  = yaxis.plot      (x, y, **plotstyle)
        # print("plotLine: auto plotstyle:", plotstyle)                     # "marker" is present
        # --> plotstyle: {'color': 'deepskyblue', 'linestyle': 'solid', 'linewidth': 2.0, 'label': '', 'markeredgecolor': 'deepskyblue', 'marker': 'o', 'markersize': 6.123724356957946, 'alpha': 0.9}

    if drawlegend: yaxis.legend()

    return line


###############################################################################
# NOT IN USE!
#~def updatePlot(filePath, timetag, cpm):
    #~"""updates an existing plot (made by makePlot) with last record"""
    #~# caution: not active; not tested for current code!!!

    #~start= time.time()

    #~try:
        #~x = gglobs.logTime[0]   # logTime is defined only after 1st plot
    #~except:
        #~print("updatePlot, no gglobs.logTimeSlice.size")
        #~return

    #~if gglobs.XunitCurrent == "Time":
        #~# plot versus Date&Time of day
        #~ptime = mpld.datestr2num(timetag)
    #~else:
        #~# Plot vs DiffTime (time since first record)
        #~# XunitCurrent is one of second, minute, hour day
        #~ptime = mpld.datestr2num(timetag) - gglobs.logTime[0]

    #~# rescale for X-axis
    #~if gglobs.XunitCurrent   == "second":
        #~ptime = ptime * 86400.              # convert to seconds
    #~elif gglobs.XunitCurrent == "minute":
        #~ptime = ptime * 1440.               # convert to minutes
    #~elif gglobs.XunitCurrent == "hour":
        #~ptime = ptime * 24.                 # convert to hours
    #~elif gglobs.XunitCurrent == "day":
        #~pass                                # is in days already
    #~else:
        #~pass                                # gglobs.XunitCurrent is "Time"

    #~# rescale for Y-axis
    #~if gglobs.Yunit == "CPS":        cpm /= 60.
    #~#print "ptime:", ptime, "cpm:", cpm

    #~rdplt.set_xdata(np.append(rdplt.get_xdata(), ptime))
    #~rdplt.set_ydata(np.append(rdplt.get_ydata(), cpm))

    #~gglobs.sizePlotSlice += 1

    #~subTitle = 'File:' + os.path.basename(filePath) + "  Recs:" + str(gglobs.sizePlotSlice)
    #~plt.title(subTitle, fontsize=12, fontweight='normal', loc = 'right')

    #~ax = plt.gca()
    #~ax.relim()              # recompute the ax.dataLim
    #~ax.autoscale_view()     # update ax.viewLim using the new dataLim

    #~#plt.draw()   # seems to be unnecessary

    #~stop = time.time()
    #~dprint("updatePlot: update: {:0.1f} ms Total".format( (stop - start) * 1000))

# end of not in use
###############################################################################
