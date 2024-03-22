#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
gsup_tools.py - GeigerLog tools

include in programs with:
    include gsup_tools
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

import gsup_sql
import gsup_gauge

xt, yt, vline, zero, FitFlag, FitSelector = 0, 0, True, "None", True, "1"


def fprintSuSt():
    """Prints an overview of data from all variables"""

    def getTimespanText(timespan):
        """get optimal duration representation"""

        ts = timespan
        if ts > 1 : return "{:10,.2f} d".format(ts)
        ts = ts * 24
        if ts > 1 : return "{:10,.2f} h".format(ts)
        ts = ts * 60
        if ts > 1 : return "{:10,.2f} m".format(ts)
        ts = ts * 60
        return "{:10,.2f} s".format(ts)


    if gglobs.logTimeSlice is None:
        gglobs.exgg.showStatusMessage("No data available")
        return

    timespan_total = (gglobs.logTime[-1]      - gglobs.logTime[0])          # days
    timespan_plot  = (gglobs.logTimeSlice[-1] - gglobs.logTimeSlice[0])     # days
    size_total     = gglobs.logTime.size
    size_plot      = gglobs.logTimeSlice.size
    cycle_total    = "{:10,.1f} s".format((timespan_total * 86400) / (size_total  - 1)) if size_total > 1 else "        NA  "
    cycle_plot     = "{:10,.1f} s".format((timespan_plot  * 86400) / (size_plot   - 1)) if size_plot  > 1 else "        NA  "

    fprint(header("Summary Statistics of Variables selected in Plot"))
    fprint("File       = {}".format(gglobs.currentDBPath))
    if os.access(gglobs.currentDBPath , os.R_OK):   fprint("Filesize   = {:10,.0f} Bytes".format(os.path.getsize(gglobs.currentDBPath)))
    else:                                           fprint("Filesize   = File not found!")
    fprint("Records    = {:10,.0f}   total,     {:10,.0f}   shown in Plot"  .format(size_total,     size_plot))
    fprint("Time Span  = {:10s} total,     {:10s} shown in Plot"            .format(getTimespanText(timespan_total), getTimespanText(timespan_plot)))
    fprint("Avg. Cycle = {:>10s} total avg, {:>10s} shown in Plot"          .format(cycle_total,    cycle_plot))

    fprint("")
    fprint("Variable  [Unit]       Avg ±StdDev    ±SDev%  Variance     Min ... Max    Recs    Last")
    # like: Temp    : [°C]      1.435 ±0.788    ±54.9%    0.622 0.77367  5.6682    1775  1.4219
    for i, vname in enumerate(gglobs.varsCopy):
        if vname in gglobs.logSliceMod:         # only the vars shown in current plot
            line = gglobs.varStats[vname].strip()
            if line > "":   fprint(line)
            else:           fprint("{:8s}: No Data".format(vname))


def getDataForshowStats(logTime, logVar, vname):
    """get the text for the QTextBrowser in showStats"""

    vnameFull        = gglobs.varsCopy[vname][0]

    logSize          = logTime.size
    logtime_max      = logTime.max()
    logtime_min      = logTime.min()
    logtime_delta    = logtime_max - logtime_min # in days

    records_nonnan   = np.count_nonzero(~np.isnan(logVar))

    # return when all data are nan
    if np.isnan(logVar).all():
        allnan = "Variable: {}: No Data\n".format(vname)
        return allnan

    logVar_max       = np.nanmax    (logVar)
    logVar_min       = np.nanmin    (logVar)
    logVar_avg       = np.nanmean   (logVar)
    logVar_med       = np.nanmedian (logVar)
    logVar_var       = np.nanvar    (logVar)
    logVar_std       = np.nanstd    (logVar)

    logVar_err       = logVar_std / np.sqrt(logVar.size)
    logVar_sqrt      = np.sqrt(logVar_avg)
    logVar_95        = logVar_std * 1.96   # 95% confidence range

    if vname in ("CPM", "CPM1st", "CPM2nd", "CPM3rd"):
        logVar_text      = "(in units of: {})".format(gglobs.Yunit)

    elif vname in ("CPS",  "CPS1st", "CPS2nd", "CPS3rd"):
        if gglobs.Yunit == "CPM":   unitText = "CPS"
        else:                       unitText = gglobs.Yunit
        logVar_text      = "(in units of: {})".format(unitText)

    else:
        logVar_text      = ""

    ltext = []
    ltext.append("Variable: {} {}\n".format(vnameFull, logVar_text))
    ltext.append(    "  Recs        = {:10,.0f}  Records".format(records_nonnan))

    if   gglobs.Yunit == "CPM" and (vname in ("CPM", "CPM1st", "CPM2nd", "CPM3rd")):
        ltext.append("  Counts      = {:10,.0f}  Counts calculated as: Average CPM * Log-Duration[min]\n".format(logVar_avg * logtime_delta * 24 * 60))

    elif gglobs.Yunit == "CPM" and (vname in ("CPS", "CPS1st", "CPS2nd", "CPS3rd")):
        ltext.append("  Counts      = {:10,.0f}  Counts calculated as: Average CPS * Log-Duration[sec]\n".format(logVar_avg * logtime_delta * 24 * 60 * 60))

    else:
        ltext.append("")

    #~print("----------------vname: ", vname)
    ltext.append(    "                          % of avg")
    ltext.append(    "  Average     = {:8.2f}      100%       Min  ={:8.2f}        Max  ={:8.2f}" .format(logVar_avg,                              logVar_min,          logVar_max)          )
    if logVar_avg != 0:
        ltext.append("  Variance    = {:8.2f} {:8.2f}%"                                          .format(logVar_var,  logVar_var  / logVar_avg * 100))
        ltext.append("  Std.Dev.    = {:8.2f} {:8.2f}%       LoLim={:8.2f}        HiLim={:8.2f}" .format(logVar_std,  logVar_std  / logVar_avg * 100,  logVar_avg-logVar_std,         logVar_avg+logVar_std)  )
        ltext.append("  Sqrt(Avg)   = {:8.2f} {:8.2f}%       LoLim={:8.2f}        HiLim={:8.2f}" .format(logVar_sqrt, logVar_sqrt / logVar_avg * 100,  logVar_avg-logVar_sqrt,        logVar_avg+logVar_sqrt) )
        ltext.append("  Std.Err.    = {:8.2f} {:8.2f}%       LoLim={:8.2f}        HiLim={:8.2f}" .format(logVar_err,  logVar_err  / logVar_avg * 100,  logVar_avg-logVar_err,         logVar_avg+logVar_err) )
        ltext.append("  Median      = {:8.2f} {:8.2f}%       P_5% ={:8.2f}        P_95%={:8.2f}" .format(logVar_med,  logVar_med  / logVar_avg * 100,  np.nanpercentile(logVar, 5),   np.nanpercentile(logVar, 95)))
        ltext.append("  95% Conf *) = {:8.2f} {:8.2f}%       LoLim={:8.2f}        HiLim={:8.2f}" .format(logVar_95,   logVar_95   / logVar_avg * 100,  logVar_avg-logVar_95,          logVar_avg+logVar_95)   )
    else:
        ltext.append("  Variance    = {:8.2f}  {:>8s}"                                           .format(logVar_var,  "N.A."))
        ltext.append("  Std.Dev.    = {:8.2f}  {:>8s}       LoLim={:8.2f}        HiLim={:8.2f}"  .format(logVar_std,  "N.A."                        ,  logVar_avg-logVar_std,         logVar_avg+logVar_std)  )
        ltext.append("  Sqrt(Avg)   = {:8.2f}  {:>8s}       LoLim={:8.2f}        HiLim={:8.2f}"  .format(logVar_sqrt, "N.A."                        ,  logVar_avg-logVar_sqrt,        logVar_avg+logVar_sqrt) )
        ltext.append("  Std.Err.    = {:8.2f}  {:>8s}       LoLim={:8.2f}        HiLim={:8.2f}"  .format(logVar_err,  "N.A."                        ,  logVar_avg-logVar_err,         logVar_avg+logVar_err) )
        ltext.append("  Median      = {:8.2f}  {:>8s}       P_5% ={:8.2f}        P_95%={:8.2f}"  .format(logVar_med,  "N.A."                        ,  np.nanpercentile(logVar, 5),   np.nanpercentile(logVar, 95)))
        ltext.append("  95% Conf *) = {:8.2f}  {:>8s}       LoLim={:8.2f}        HiLim={:8.2f}"  .format(logVar_95,   "N.A."                        ,  logVar_avg-logVar_95,          logVar_avg+logVar_95)   )

    return "\n".join(ltext)


def showStats():
    """Printing statistics - will always show only data in current plot"""

    logTimeTotal     = gglobs.logTime           # time data
    logTime          = gglobs.logTimeSlice           # time data

    if gglobs.logTime is None:
        gglobs.exgg.showStatusMessage("No data available") # when called without a loaded file
        return

    setBusyCursor()

    logSize          = logTime.size
    logSizeTotal     = logTimeTotal.size

    logtime_size     = logTime.size
    logtime_max      = logTime.max()
    logtime_min      = logTime.min()
    logtime_delta    = logtime_max - logtime_min # in days

    oldest   = (str(mpld.num2date(logtime_min)))[:19]
    youngest = (str(mpld.num2date(logtime_max)))[:19]

    lstats   = QTextBrowser()      # label to hold the description
    lstats.setLineWrapMode(QTextEdit.NoWrap)
    lstats.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

    lstats.append("Data from file: {}\n".format(gglobs.currentDBPath))
    lstats.append("Totals")
    lstats.append("  Filesize      = {:12,.0f} Bytes".format(os.path.getsize(gglobs.currentDBPath)))
    lstats.append("  Records       = {:12,.0f} Total, {:0,.0f} shown in Plot".format(logSizeTotal, logSize))
    lstats.append("")
    lstats.append("Legend:   *): Approximately valid for a Poisson Distribution when Average > 10")
    lstats.append("NOTE:     Requirement for Poisson: Average = Variance")
    lstats.append("="*100)

    lstats.append("Time")
    lstats.append("  Oldest rec    = {}  (time = {:.3f} d)".format(oldest,   0))
    lstats.append("  Youngest rec  = {}  (time = {:.3f} d)".format(youngest, logtime_max - logtime_min))
    lstats.append("  Duration      = {:.1f} s   = {:.1f} m   = {:.1f} h   = {:.1f} d".format(logtime_delta *86400, logtime_delta*1440, logtime_delta *24, logtime_delta))
    lstats.append("  Cycle average = {:0.2f} s".format(logtime_delta *86400/ (logSize -1)))
    lstats.append("="*100)

    for i, vname in enumerate(gglobs.varsCopy):
        if gglobs.varsSetForCurrent[vname]:
            try:
                if vname in gglobs.logSliceMod:         # else the var had not been checked for the plot
                    logVar = gglobs.logSliceMod[vname]  # var data
                    getlstatstext =  getDataForshowStats(logTime, logVar, vname)
                    lstats.append("")
                    lstats.append(getlstatstext)
                    lstats.append("="*100)
            except Exception as e:
                exceptPrint(e, "")

    lstats.append("First and last few records:\n")
    sql, ruler = gsup_sql.getShowCompactDataSql(gglobs.varsSetForCurrent)
    lstats.append(ruler)
    lstats.append(gglobs.exgg.getExcerptLines(sql, gglobs.currentConn, lmax=10))
    lstats.append(ruler)

    lstats.moveCursor(QTextCursor.Start)

    d = QDialog()
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setFont(gglobs.fontstd)
    d.setWindowTitle("Statistics on Checked Variables")
    d.setWindowModality(Qt.WindowModal)
    d.setMinimumWidth(1100)
    d.setMinimumHeight(750)

    bbox    = QDialogButtonBox()
    bbox.setStandardButtons(QDialogButtonBox.Ok)
    bbox.accepted.connect(lambda: d.done(0))

    layoutV = QVBoxLayout(d)
    layoutV.addWidget(lstats)
    layoutV.addWidget(bbox)

    setNormalCursor()

    d.exec()


def selectScatterPlotVars():
    """Selecting the vars for the scatter plot and display and fit options"""

    global xt, yt, vline, zero, FitFlag, FitSelector # to keep the selectios

    if gglobs.logTime is None:              # when called without a loaded file
        gglobs.exgg.showStatusMessage("No data available")
        return

    # X-axis and Y-axis vars
    xlist = QListWidget()
    xlist.setSelectionMode(QAbstractItemView.SingleSelection)
    xlist.addItem("time")
    ylist = QListWidget()
    ylist.setSelectionMode(QAbstractItemView.SingleSelection)
    ylist.addItem("time")
    for i, vname in enumerate(gglobs.varsCopy):
        if gglobs.varsSetForCurrent[vname]:
            #~print("gglobs.varsSetForCurrent[vname]: ", vname,  gglobs.varsSetForCurrent[vname])
            xlist.addItem(vname)
            ylist.addItem(vname)

    if xt == 0:
        xlist.setCurrentRow(0)
        ylist.setCurrentRow(0)
    else:
        for i in range(len(xlist)):
            if xlist.item(i).text() == xt: xlist.setCurrentRow(i)
            if ylist.item(i).text() == yt: ylist.setCurrentRow(i)

    # force origin to zero?
    b0 = QRadioButton("Show Optimal ")             # this is default
    b1 = QRadioButton("Show X=0")
    b2 = QRadioButton("Show Y=0")
    b3 = QRadioButton("Show X,Y=0")

    if   zero == "None"      : b0.setChecked(True)
    elif zero == "x"         : b1.setChecked(True)
    elif zero == "y"         : b2.setChecked(True)
    elif zero == "x and y"   : b3.setChecked(True)
    else                     : b0.setChecked(True)

    # draw connecting lines?
    checkb  = QCheckBox("Connecting Line")      # default is yes
    checkb.setChecked(vline)

    layoutT = QHBoxLayout()
    layoutT.addWidget(b3)
    layoutT.addWidget(b1)
    layoutT.addWidget(b2)
    layoutT.addWidget(b0)
    layoutT.addStretch()

    # add polynomial fit?                         default is yes
    checkF = QCheckBox("Add Polynomial Fit of order:")
    checkF.setChecked(FitFlag)

    # selector for order of fit                   default is 1st order = linear
    comboboxF = QComboBox()
    comboboxF.addItems(["Prop", "0", "1", "2", "3", "4", "5", "6", "7"])
    comboboxF.setMaximumWidth(70)
    comboboxF.setToolTip('Select the degree of the polynomial fit')

    #~print("-------------FitSelector: ", FitSelector)
    if FitSelector == "Prop":   comboboxF.setCurrentIndex(0)
    else:                       comboboxF.setCurrentIndex(int(FitSelector) + 1)

    layoutF = QHBoxLayout()
    layoutF.addWidget(checkb)
    layoutF.addWidget(checkF)
    layoutF.addWidget(comboboxF)
    layoutF.addStretch()

    bbox = QDialogButtonBox()
    bbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok )
    bbox.accepted.connect(lambda: d.done(100)) # ESC key produces 0 (zero)!
    bbox.rejected.connect(lambda: d.done(-1))

    layoutH0 = QHBoxLayout()
    layoutH0.addWidget(QLabel("Xtra"))
    layoutH0.addWidget(QLabel("Y"))

    layoutH = QHBoxLayout()
    layoutH.addWidget(xlist)
    layoutH.addWidget(ylist)

    d = QDialog()
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setFont(gglobs.fontstd)
    d.setWindowTitle("Select Variables for Scatter Plot")
    d.setMinimumHeight(350)
    #d.setStyleSheet("QLabel { background-color:#DFDEDD; color:rgb(40,40,40); font-size:30px; font-weight:bold;}")

    d.setWindowModality(Qt.WindowModal)       # default alles andere kann bedient werden
    # d.setWindowModality(Qt.NonModal)          #         alles andere blockiert
    # d.setWindowModality(Qt.ApplicationModal)  #         alles andere blockiert
    # nothing set                               #         alles andere blockiert
    # d.setModal(False)                         #         alles andere blockiert!
    # d.setModal(True)                          #         alles andere blockiert


    layoutV = QVBoxLayout(d)
    layoutV.addLayout(layoutH0)
    layoutV.addLayout(layoutH)
    layoutV.addLayout(layoutT)
    layoutV.addLayout(layoutF)
    layoutV.addWidget(bbox)

    retval = d.exec()
    #print("reval:", retval)
    if retval != 100: return  # ESC key produces 0

    #~print("xlist.currentItem(): ", xlist.currentItem().text())
    #~print("ylist.currentItem(): ", ylist.currentItem().text())
    xt          = xlist.currentItem().text()
    yt          = ylist.currentItem().text()
    vline       = checkb.isChecked()
    FitFlag     = checkF.isChecked()
    FitSelector = comboboxF.currentText()

    if   b0.isChecked():  zero = "None"
    elif b1.isChecked():  zero = "x"
    elif b2.isChecked() : zero = "y"
    elif b3.isChecked() : zero = "x and y"
    else                : zero = "None"

    plotScatter(xt, yt, vline, zero, FitFlag, FitSelector)


def plotScatter(vx, vy, vline, zero, FitFlag, FitSelector):
    """Plotting a Scatter plot"""

    vprint("plotScatter: x:{}, y:{}, vline:{}, zero:{}, FitFlag:{}, FitSelector:{}".format(vx, vy, vline, zero, FitFlag, FitSelector))

    # Plotstyle
    plotstyle        = {'color'             : 'black',
                        'linestyle'         : 'solid' if vline else 'none',
                        'linewidth'         : '0.5',
                        'label'             : 'testlabel',
                        'markeredgecolor'   : 'black',
                        'marker'            : 'o',
                        'markersize'        : '60',
                        'alpha'             : 1,
                        }

    if gglobs.currentDBPath is None: DataSrc = "No Data source!"
    else:                            DataSrc = os.path.basename(gglobs.currentDBPath)

    localvardict = gglobs.varsCopy.copy()
    localvardict.update( {'time' : ('time [d]', 'time') } )

    #~print("gglobs.logTimeDiffSlice: ", gglobs.logTimeDiffSlice)
    #~print("gglobs.logSlice: ", gglobs.logSlice)
    #print("vx: ", vx)
    if vx == "time":
        x0 = gglobs.logTimeDiffSlice
    else:
        try:
            x0 = gglobs.logSlice[vx]
        except Exception as e:
            fprint(header("Plot Scatter X"))
            fprint("ERROR in plotScatter: Exception: ", e)
            return

    #print("vy: ", vy)
    if vy == "time":
        y0 = gglobs.logTimeDiffSlice
    else:
        try:
            y0 = gglobs.logSlice[vy]
        except Exception as e:
            fprint(header("Plot Scatter Y"))
            fprint("ERROR in plotScatter: Exception: ", e)
            return

    ymask                   = np.isfinite(y0)      # mask for nan values
    y1                      = y0[ymask]
    x1                      = x0[ymask]

    xmask                   = np.isfinite(x1)      # mask for nan values
    y                       = y1[xmask]
    x                       = x1[xmask]

    if y.size > 0:  plotstyle['markersize'] = float(plotstyle['markersize']) / np.sqrt(y.size)
    else:           plotstyle['markersize'] = 3

    # make the figure
    fig2 = plt.figure(facecolor = "#E7F9C9", dpi=gglobs.hidpiScaleMPL)
    gglobs.plotScatterFigNo = plt.gcf().number
    vprint("plotScatter: open figs count: {}, current fig: #{}".format(len(plt.get_fignums()), plt.gcf().number))

    plt.title("Scatter Plot\n", fontsize=12, loc='center')
    subTitleLeft  = DataSrc
    subTitleRight = "Recs:" + str(len(x))
    plt.title(subTitleLeft,  fontsize=10, fontweight='normal', loc = 'left')
    plt.title(subTitleRight, fontsize=10, fontweight='normal', loc = 'right')

    plt.xlabel("x = " + localvardict[vx][0], fontsize=12)
    plt.ylabel("y = " + localvardict[vy][0], fontsize=12)

    plt.grid(True)
    plt.subplots_adjust(hspace=None, wspace=.2 , left=.15, top=0.90, bottom=0.1, right=.97)
    plt.ticklabel_format(useOffset=False)

    # show the cursor x, y position in the Nav toolbar
    ax1 = plt.gca()
    ax1.format_coord = lambda x,y: "x={:.1f}, y={:.1f}".format(x, y)    # to hide use: lambda x, y: ""

    d = QDialog()
    gglobs.plotScatterPointer = d
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setWindowTitle("Scatter Plot")
    d.setWindowModality(Qt.WindowModal)          # multiple Windows open, all runs, all is clickable

    # canvas - this is the Canvas Widget that displays the `fig2`
    # it takes the `figure` instance as a parameter to __init__
    canvas2 = FigureCanvas(fig2)
    canvas2.setFixedSize(700, 600)
    navtoolbar = NavigationToolbar(canvas2, gglobs.exgg)

    labout  = QTextBrowser() # label to hold the description
    labout.setFont(gglobs.fontstd)
    labout.setMinimumHeight(220)
    txtlines  = "Connecting lines are {}drawn".format("" if vline else "not ")
    txtorigin = "an origin of zero is enforced for {}".format(zero)
    labout.setText("Scatter Plot of y = {} versus x = {}.".format(localvardict[vy][0], localvardict[vx][0]))
    labout.append("{}; {}.".format(txtlines, txtorigin))

    okButton = QPushButton("OK")
    okButton.setAutoDefault(True)
    okButton.clicked.connect(lambda:  d.done(0))

    selectButton = QPushButton("Select")
    selectButton.setAutoDefault(False)
    selectButton.clicked.connect(lambda:  nextScatterPlot())

    bbox = QDialogButtonBox()
    bbox.addButton(selectButton,  QDialogButtonBox.ActionRole)
    bbox.addButton(okButton,      QDialogButtonBox.ActionRole)

    layoutV = QVBoxLayout(d)
    layoutV.addWidget(navtoolbar)
    layoutV.addWidget(canvas2)
    layoutV.addWidget(labout)
    layoutV.addWidget(bbox)


    plt.plot(x, y, **plotstyle) # need to plot first, so xlim, ylim become available!

    xlim = ax1.get_xlim()       # xlim is tuple
    ylim = ax1.get_ylim()

    labout.append("\nPolynomial Coefficients of the Least-Squares-Regression Fit:")
    labout.append("<span style='font-weight:bold; font-size:20px;'>y = a + b * x + c * x² + d * x³ + ... </span><br>")

    if FitFlag:
        if x.size != 0 and y.size != 0:
            #print("size(x), (y): ", x.size, " ", y.size)

            if FitSelector != "Prop":
                try:
                    coeff = ["a", "b", "c", "d", "e", "f", "g", "h"]
                    pfit = np.polyfit(x, y, int(FitSelector))
                    vprint("plotScatter: pfit: ", pfit)

                    # getting r-squared for linear fit
                    correlation_matrix = np.corrcoef(x, y)
                    # edprint(correlation_matrix)
                    correlation_xy = correlation_matrix[0,1]
                    # edprint(correlation_xy)
                    r_squared = correlation_xy**2
                    # edprint(r_squared)
                    if int(FitSelector) == 1:
                        labout.append("R²  : {:0.3f} ".format(r_squared))

                    for i,f in enumerate(np.flip(pfit)):
                        labout.append("({:d}) : {:s} = {: .4g}".format(i, coeff[i], f))
                    p  = np.poly1d(pfit)
                    xs = sorted(x)
                    plt.plot(xs, p(xs), color="red", marker=None, linestyle="solid", linewidth=2)
                except Exception as e:
                    dprint("plotScatter: pfit: Failure with exception: ", e)
                    labout.append("\nFailure to plot. Exception: {}".format(e))
                    playWav("err")

            else:
                def func(x, a):
                    return a * x

                # from scipy.optimize import curve_fit
                try:
                    # popt, pcov = curve_fit(func, x, y)
                    popt, pcov = scipy.optimize.curve_fit(func, x, y)
                    vprint("plotScatter: curve_fit: popt, pcov, perr: ", popt, pcov, np.sqrt(np.diag(pcov)))
                    labout.append("(0) : a = {: .4g} (Prop)".format(0))
                    labout.append("(1) : b = {: .4g}".format(popt[0]))
                    plt.plot(x, func(x, *popt), color="red", marker=None, linestyle="solid", linewidth=2)
                except Exception as e:
                    dprint("plotScatter: curve_fit: Failure with exception: ", e)
                    labout.append("\nFailure to plot. Exception: {}".format(e))
                    playWav("err")
        else:
            vprint("plotScatter: no data in either x or y: x:\n", x, "\ny:\n", y)
            labout.append("\nFailure to plot:")
            if x.size == 0: labout.append("   No data in x")
            if y.size == 0: labout.append("   No data in y")
            playWav("err")

    if   zero == "x" :      plt.xlim(left   = 0)
    elif zero == "y" :      plt.ylim(bottom = 0)
    elif zero == "x and y":
        plt.ylim(bottom = 0)
        plt.xlim(left   = 0)
    elif zero == "None":    pass

    # show window
    fig2.canvas.draw_idle()
    d.exec()
    plt.close(gglobs.plotScatterFigNo)


def nextScatterPlot():
    """closes the dialog and reopens the var selection """

    #print("nextScatterPlot: ")
    gglobs.plotScatterPointer.close()   # closes the dialog
    plt.close(gglobs.plotScatterFigNo)  # closes the figure
    selectScatterPlotVars()


def setLastValues(i, vname):
    """update the values in the displayLastValues() dialog box"""

    fncname = "setLastValues: "
    # start = time.time()

    lastval = gglobs.lastLogValues[vname]

    if not gglobs.varsSetForLog[vname]:
        val  = "not mapped"
        sval = "not mapped"
    else:
        if not np.isnan(lastval):
            # val  = "{:7.3f}".format(lastval)
            val  = "{:8.3f}".format(lastval)
            if gglobs.GraphScale[vname].upper().strip() == "VAL":
                sval = "---"
            else:
                # sval = "{:7.3f}".format(scaleVarValues(vname, lastval, gglobs.GraphScale[vname]))
                sval = "{:8.3f}".format(scaleVarValues(vname, lastval, gglobs.GraphScale[vname]))
        else:
            val  = "---"
            sval = "---"

    gglobs.exgg.vlabels[i] .setText(val)
    gglobs.exgg.svlabels[i].setText(sval)

    if gglobs.logging and gglobs.varsSetForLog[vname]:
        # make black on yellow
        ssheet = "QLabel {background-color:#F4D345; color:black; }"
        gglobs.exgg.vlabels[i] .setStyleSheet(ssheet)
        gglobs.exgg.svlabels[i].setStyleSheet(ssheet)

    elif not gglobs.logging and gglobs.varsSetForLog[vname]:
        # make darkgrey on light grey
        ssheet = "QLabel {color:darkgray; }"
        gglobs.exgg.vlabels[i] .setStyleSheet(ssheet)
        gglobs.exgg.svlabels[i].setStyleSheet(ssheet)

    else:
        # make darkgrey on light grey and in smaller size letters
        ssheet = "QLabel {color:darkgray; font-size:14px;}"
        gglobs.exgg.vlabels[i] .setStyleSheet(ssheet)
        gglobs.exgg.svlabels[i].setStyleSheet(ssheet)

    # edprint(fncname + "ssheet: ", ssheet)

    # takes < 0.2 ms
    # duration = (time.time() - start) * 1000
    # cdprint(fncname + "duration: {:0.3f} ms".format(duration))


def displayLastValues():
    """Displays the last values in big letters"""
    # For updating see updateDisplayVariableValue() in file ggeiger

    # start = time.time()

    fncname = "displayLastValues: "

    if gglobs.displayLastValsIsOn:              # already showing
        return

    if gglobs.logConn    == None:               # no database
        msg = "No data available"
        gglobs.exgg.showStatusMessage(msg, timing=0, error=True)
        return

    gglobs.displayLastValsIsOn = True

    d = QDialog()
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setWindowTitle("Display Last Values")
    d.setWindowModality(Qt.WindowModal)     # can click everywhere
    d.setMinimumWidth(530)
    d.setStyleSheet("QLabel {background-color:#DFDEDD; color:rgb(80,80,80);}")

    bbox = QDialogButtonBox()
    bbox.setStandardButtons(QDialogButtonBox.Ok)
    bbox.accepted.connect(lambda: d.done(0))

    gridlo = QGridLayout()
    gridlo.setVerticalSpacing(10) # more than default, 5 is about normal?

    layoutV = QVBoxLayout(d)
    layoutV.addLayout(gridlo)
    layoutV.addWidget(bbox)

    lenvn       = len(gglobs.varsCopy)
    klabels     = [None] * lenvn   # variable names
    dlabels     = [None] * lenvn   # device names
    vlabels     = [None] * lenvn   # variable values
    svlabels    = [None] * lenvn   # scaled variable values
    widthValCol = 160

    t1 = QLabel("Variable")
    t1.setStyleSheet("QLabel {color: #111111; font-size:20px; font-weight:bold;}")

    t2 = QLabel("Device")
    t2.setStyleSheet("QLabel {color: #111111; font-size:20px; font-weight:bold; qproperty-alignment:AlignCenter;}")

    t3 = QLabel("Value")
    t3.setStyleSheet("QLabel {color: #111111; font-size:20px; font-weight:bold; qproperty-alignment:AlignCenter;}")
    t3.setMinimumWidth(widthValCol)

    t4 = QLabel("Graph-Scaled")
    t4.setStyleSheet("QLabel {color: #111111; font-size:20px; font-weight:bold; qproperty-alignment:AlignCenter;}")
    t4.setMinimumWidth(widthValCol)

    gridlo.addWidget(t1,    0, 0)
    gridlo.addWidget(t2,    0, 1)
    gridlo.addWidget(t3,    0, 2)
    gridlo.addWidget(t4,    0, 3)
    gridlo.setColumnStretch(2, 1) # give more space to value col
    gridlo.setColumnStretch(3, 1) # give more space to value col

    for i, vname in enumerate(gglobs.varsCopy):
        #print("---i, vname:", i, vname)

        # set the var name
        klabels[i] = QLabel(vname)
        klabels[i].setFont((QFont("Sans", 12, weight=QFont.Bold)))

        # set the device name if it supports this variable
        dlabels[i] = QLabel()
        dlabels[i].setAlignment(Qt.AlignCenter)
        dlabels[i].setStyleSheet("QLabel {color:#111; font-size:14px; font-weight:bold;}")
        for dname in gglobs.Devices:
            #print("dname:", dname, ", vname:", vname)
            if gglobs.Devices[dname][1] is None: continue                   # no vars defined
            if vname in gglobs.Devices[dname][1]: dlabels[i].setText(dname) # this var is defined

        # setup values
        gglobs.exgg.vlabels[i] = QLabel()
        gglobs.exgg.vlabels[i].setAlignment(Qt.AlignCenter)
        gglobs.exgg.vlabels[i].setFont(QFont("Monospace", 22, weight=QFont.Black))
        gglobs.exgg.vlabels[i].setMinimumWidth(widthValCol)

        # setup scaled values
        gglobs.exgg.svlabels[i] = QLabel()
        gglobs.exgg.svlabels[i].setAlignment(Qt.AlignCenter)
        gglobs.exgg.svlabels[i].setFont(QFont("Monospace", 22, weight=QFont.Black))
        gglobs.exgg.svlabels[i].setMinimumWidth(widthValCol)

        # set the values and scaled values
        setLastValues(i, vname)

        gridlo.addWidget(klabels[i],                i + 1, 0)
        gridlo.addWidget(dlabels[i],                i + 1, 1)
        gridlo.addWidget(gglobs.exgg.vlabels[i],    i + 1, 2)
        gridlo.addWidget(gglobs.exgg.svlabels[i],   i + 1, 3)

    # takes 10 ... 20 ms
    # duration = (time.time() - start) * 1000
    # cdprint(fncname + "duration: {:0.3f} ms".format(duration))

    d.exec()
    gglobs.displayLastValsIsOn = False


def fprintPlotData():
    """Print Plot Data to Notepad. Data are taken from the plot, not from the database!"""

    fncname = "fprintPlotData: "

    t0 = gglobs.logTimeSlice

    if t0 is None or len(t0) == 0:
        gglobs.exgg.showStatusMessage("No data available")
        return

    setBusyCursor()

    header = "{:6s}, {:19s}".format("#Index", "Datetime")
    for vname in gglobs.varsCopy:
        if gglobs.exgg.varDisplayCheckbox[vname].isChecked():
            header += ", {:>7s}".format(vname)
    fprint(header)

    printstring    = ""
    printlinecount = 0
    printlineMax   = 20

    for i in range(len(t0)):
        vcc = "{:>6d}, {:<19s}".format(i, str(mpld.num2date(t0[i]))[:19])   # Index, DateTime
        NonNoneCount = 0
        for vi, vname in enumerate(gglobs.varsCopy):
            if gglobs.exgg.varDisplayCheckbox[vname].isChecked():
                varvalue = gglobs.logSlice[vname][i]
                # if vname == "CPM" or vname == "CPM1st" : rdprint(fncname, varvalue)
                if not np.isnan(varvalue):  NonNoneCount += 1
                if vi < 8: # CPM et al
                    if   isinstance(varvalue, int) or varvalue.is_integer():             # it is of integer value
                        # cdprint(fncname + "it is of integer value ", varvalue)
                        if      varvalue < 1E5:   vcc += ", {:>7.0f}".format(varvalue)   # less than 100 000
                        else:                     vcc += ", {:>#7.6g}".format(varvalue)  # 100 000 or greater
                    else:
                        # cdprint(fncname + "it is NOT  of integer value ", varvalue)
                        val = round(varvalue, 4)
                        # if      val <= 0.9999:    vcc += ", {:>#7.4g}".format(val)
                        # else:                     vcc += ", {:>#7.3g}".format(val)
                        if      val <= 0.9999:    vcc += ", {:>#7.6g}".format(val)
                        else:                     vcc += ", {:>#7.6g}".format(val)
                else: # T, P, H, X
                    if   isinstance(varvalue, int) or varvalue.is_integer():             # it is of integer value
                        if      varvalue < 1E6:   vcc += ", {:>7.0f}".format(varvalue)   # less than 100 000
                        else:                     vcc += ", {:>#7.6g}".format(varvalue)  # 100 000 or greater
                    else:
                        val = round(varvalue, 4)
                        if      val <= 0.9999:    vcc += ", {:>#7.4g}".format(val)
                        else:                     vcc += ", {:>#7.5g}".format(val)

        #print("vcc: ", vcc, ", NonNoneCount: ", NonNoneCount, ", printlinecount: ", printlinecount )

        if NonNoneCount > 0:
            printstring    += vcc + "\n"
            printlinecount += 1

        if printlinecount > printlineMax:
            fprint(printstring[:-1])
            printstring    = ""
            printlinecount = 0
            printlineMax  += 30
            QtUpdate()

        if gglobs.stopPrinting: break

    fprint(printstring[:-1])

    gglobs.stopPrinting = False

    fprint(header)

    setNormalCursor()


# not used
def plotMonitor():
    """Plot the Monitor"""

    if not gglobs.debug: return

    fncname = "plotMonitor: "

    # get the last value
    if gglobs.lastLogValues is None:
        lastvalue = 316
    else:
        lastvalue = gglobs.lastLogValues["CPM"]

    # the speedometer with matplotlib
    canvasMon = getMonGraph(lastvalue)

    labout  = QTextBrowser() # label to hold the description
    labout.setFont(gglobs.fontstd)
    labout.setFixedHeight(80)
    labout.append("lastvalue:        {}".format(lastvalue))
    labout.append("log10(lastvalue): {:0.2f}".format(np.log10(lastvalue)))

    okButton = QPushButton("OK")
    okButton.setAutoDefault(True)
    okButton.clicked.connect(lambda:  d.done(0))

    bbox = QDialogButtonBox()
    bbox.addButton(okButton,      QDialogButtonBox.ActionRole)

    # makes the Qt speedometer graph
    my_gauge = gsup_gauge.AnalogGaugeWidget()
    my_gauge.scale_angle_start_value = 180          # 0 is east
    my_gauge.scale_angle_size = 180                 # 180 is west =270 grad
    my_gauge.angle_offset = 0
    my_gauge.gauge_color_inner_radius_factor = 0.75 # set thickness of arc hiher numer -> thinner arc
    my_gauge.enable_fine_scaled_marker = False      # minor marker a problem in log scale
    my_gauge.text_radius_factor = 1.15              # place numeric value -=bottom half += top half
    my_gauge.initial_scale_fontsize = 18            # scale labels
    my_gauge.setStyleSheet("border: 1px solid red; background-color:pink;") # nothing
    my_gauge.needle_scale_factor = 0.75              # length of needle 0.55  #0.8
    my_gauge.value = lastvalue

    layoutV = QVBoxLayout()
    layoutV.addWidget(canvasMon)
    layoutV.addWidget(labout)
    layoutV.addWidget(my_gauge)
    layoutV.addWidget(bbox)

    d = QDialog()
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setWindowTitle("Monitor")
    d.setWindowModality(Qt.WindowModal)          # multiple Windows open, all runs, all is clickable
    d.setLayout(layoutV)

    # show window
    # figMon.canvas.draw_idle()
    d.exec()
    plt.close(gglobs.monitorFigNo)


def getMonGraph(lastvalue):
    """makes the matplotlib speedometer graph"""

    fncname = "getMonGraph: "

    if gglobs.monitorfig is not None: plt.close(gglobs.monitorfig)

    figMon, ax = plt.subplots(facecolor = "#E7F9C9", dpi=gglobs.hidpiScaleMPL)
    gglobs.monitorfig = figMon
    gglobs.monitorax  = ax
    gglobs.monitorFigNo = plt.gcf().number

    vprint(fncname + "open figs count: {}, current fig: #{}".format(len(plt.get_fignums()), plt.gcf().number))

    lowThreshholdColor  = '#00C853' # green
    defaultColor        = '#ffe500' # yellow
    highThreshholdColor = '#EA4335' # red

    # get the threshold nunbers
    lowThreshhold  = 150
    highThreshhold = 1070

    # make the wedges
    wwidth = 0.10   # wedge width
    Valmin = np.log10(0.5)
    Valmax = np.log10(50000)
    ValTLo = 180 - np.log10(lowThreshhold) / (Valmax - Valmin) * 180
    ValTHi = 180 - np.log10(highThreshhold) / (Valmax - Valmin) * 180

    # print("Valmin, Valmax, ValTLo, ValTHi", Valmin, Valmax, ValTLo, ValTHi)

    # class matplotlib.patches.Wedge(center, r, theta1, theta2, width=None, **kwargs)
    # drawing goes counterclockwise, beginning at 0 = East
    wedge1 = mpat.Wedge((0.5,0.0), 0.5, 0,      ValTHi, zorder=0, width=wwidth, facecolor=highThreshholdColor)    # red
    wedge2 = mpat.Wedge((0.5,0.0), 0.5, ValTHi, ValTLo, zorder=0, width=wwidth, facecolor=defaultColor)           # yellow
    wedge3 = mpat.Wedge((0.5,0.0), 0.5, ValTLo, 180,    zorder=0, width=wwidth, facecolor=lowThreshholdColor)     # green

    ax.axis('off')
    ax.set_ylim([-0.1, 0.5])
    ax.set_xlim([0, 1])

    ax.add_artist(wedge1)
    ax.add_artist(wedge2)
    ax.add_artist(wedge3)

    # calc and make arrow
    arrow_length = 0.45
    # arrow_angle = np.log10(lastvalue)           # 180 * (1 - lastvalue / 100)
    arrow_angle = 180 - np.log10(lastvalue) / (Valmax - Valmin) * 180
    arrow_dy    = np.sin(np.pi * arrow_angle / 180) * arrow_length
    arrow_dx    = np.cos(np.pi * arrow_angle / 180) * arrow_length
    # print(fncname + "lastvalue {:5.2f} arrow_angle {:5.2f}  dx {:5.2f}  dy {:5.2f}".format(lastvalue, arrow_angle, arrow_dx, arrow_dy) )
    myarr = ax.arrow(0.5, 0.0, arrow_dx, arrow_dy, width=0.03, color="k", head_length=0.37, length_includes_head=True, head_width=0.095, overhang=-0.2)
    gglobs.myarr = myarr

    # canvas - this is the Canvas Widget that displays the `figure`
    # it takes the `figure` instance as a parameter to __init__
    canvasMon = FigureCanvas(figMon)
    canvasMon.setFixedSize(240, 144)
    # navtoolbar = NavigationToolbar(canvasMon, gglobs.exgg)

    return canvasMon



def plotpgGraph():
    """Plot the Time course graph in pyqtgraph,
    pyqtgraph as alternative to matplotlib
    """

    if not gglobs.debug: return

    # pyqtgraph stuff
    # import pyqtgraph            as pg
    # pg.setConfigOption('background', 'pink')
    # pg.setConfigOption('foreground', 'k')

    # y2 = np.random.normal(size=(3, 1000))
    # plotWidget = pg.plot(title="Three plot curves")
    # plotWidget.setMinimumHeight(300)
    # for i in range(3):
    #     plotWidget.plot(x[:1000], y2[i], pen=(i,3))  ## setting pen=(i,3) automaticaly creates three different-colored pens
    # plotWidget.plot(x[:1000],y[:1000])
    # plotWidget.plot(x[:1000],y[1000:2000])
    # plotWidget.plot(x[:1000],y[2000:3000])

    fncname = "plotpgGraph: "

    import pyqtgraph as pg

    start = time.time()

    # textbrowser
    labout  = QTextBrowser() # label to hold the description
    labout.setFont(gglobs.fontstd)
    labout.setFixedHeight(180)

    # print("start", start, "stop", stop)

    stop = time.time()
    labout.append("labout time: {:0.6f} ms".format((stop - start) * 1000))

    # buttonbox
    bbox = QDialogButtonBox()
    # bbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok )
    bbox.setStandardButtons(QDialogButtonBox.Ok )
    bbox.accepted.connect(lambda: d.done(1))
    # bbox.rejected.connect(lambda: d.done(-1))

    stop = time.time()
    labout.append("labout  + bbox time: {:0.6f} ms".format((stop - start) * 1000))

    # pggraph
    pg.setConfigOption('background', 'pink')
    pg.setConfigOption('foreground', 'k')

    plotWidget = pg.PlotWidget(title="My plot curves")
    plotWidget.setMinimumHeight(300)

    # data
    x = gglobs.logTime
    # print("x:\n", x)

    try:
        for i in (0,1,2,3,4,5,6,7,8,10,11):
            y = gglobs.currentDBData[:, i + 1]
            # print("y:\n", y)
            plotWidget.plot(x,y, pen=(i, 13))
    except Exception as e:
        msg = "Show PgGraph: No data"
        exceptPrint(e, msg)
        efprint(msg)
        return

    stop = time.time()
    labout.append("labout  + bbox + plotwidget time: {:0.6f} ms".format((stop - start) * 1000))

    layoutV = QVBoxLayout()
    layoutV.addWidget(labout)
    layoutV.addWidget(plotWidget)
    layoutV.addWidget(bbox)
    stop = time.time()
    labout.append("labout  + bbox + plotwidget + lV time: {:0.6f} ms".format((stop - start) * 1000))


    d = QDialog()
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setWindowTitle("Monitor")
    d.setWindowModality(Qt.WindowModal)          # multiple Windows open, all runs, all is clickable
    d.setLayout(layoutV)

    stop = time.time()
    labout.append("labout  + bbox + plotwidget + lV + dialog time: {:0.6f} ms".format((stop - start) * 1000))

    # show window
    d.exec()


def getNTPDateTime(NTPversion = 4):
    """Call NTP server and return offset in seconds as reported by NTP"""


    try:
        import ntplib
        ntplib_available = True
    except:
        edprint("ntplib not found. Cannot use NTP server!")
        ntplib_available = False
        return gglobs.NAN


    # typical offset is in the order of 10 milli second (offset = +/- 0.010

    # latest NTP version is now: 4;     working versions are 2, 3, 4 (not 1!)
    # https://www.eecis.udel.edu/~mills/ntp/html/release.html
    #
    # ntplib: def request(self, host, version=2, port='ntp', timeout=5):
    #
    # NTP document by IETF:       https://tools.ietf.org/html/rfc5905
    # see: page 23, Figure 7 for functions, and ff for details
    #
    # Reference Timestamp:
    # Time when the system clock was last set or corrected, in NTP timestamp format.
    #
    # Origin Timestamp (org):
    # Time at the client when the request departed for the server, in NTP timestamp format.
    #
    # Receive Timestamp (rec):
    # Time at the server when the request arrived from the client, in NTP timestamp format.
    #
    # Transmit Timestamp (xmt):
    # Time at the server when the response left for the client, in NTP timestamp format.
    #
    # Destination Timestamp (dst):
    # Time at the client when the reply arrived from the server, in NTP timestamp format.

    if not ntplib_available:
        edprint("Cannot call NTP Server as ntplib is not available!")
        return gglobs.NAN


    NTP_SERVERS = [ #'pool.ntp.org',
                    #'asia.pool.ntp.org',
                    #~'oceania.pool.ntp.org',
                    #'north-america.pool.ntp.org',
                    #~'south-america.pool.ntp.org',
                    #'europe.pool.ntp.org',
                    'de.pool.ntp.org',
                    #~'0.de.pool.ntp.org',
                    #~'1.de.pool.ntp.org',
                    #~'2.de.pool.ntp.org',
                    #~'3.de.pool.ntp.org',
                    #~'uk.pool.ntp.org',
                    #~'0.uk.pool.ntp.org',
                  ]

    fncname     = "getNTPDateTime: "
    vprint(fncname)
    setIndent(1)
    orig = recv = dest = offset = gglobs.NAN

    client = ntplib.NTPClient()
    for ntpserver in NTP_SERVERS:
        ntps     = []
        try:
            response = client.request(ntpserver, version=NTPversion, timeout=0.2)
        except Exception as e:
            msg = fncname + "NTPversion:{} ".format(NTPversion)
            exceptPrint(e, msg)
            setIndent(0)
            #return gglobs.NAN
            continue

        #print("response.orig_time: ", response.orig_time) # like: 1614266943.3662605

        orig   = response.orig_time     # all times in seconds
        recv   = response.recv_time
        tx     = response.tx_time
        dest   = response.dest_time
        offset = response.offset

        ntps.append( ["orig"     , orig - orig]) # always zero
        ntps.append( ["recv"     , recv - orig])
        ntps.append( ["tx  "     , tx   - orig])
        ntps.append( ["dest"     , dest - orig])
        ntps.append( ["offset"   , offset])
        #ntps.append( ["calc offset"   , ((recv - orig) + (tx - dest)) / 2])

        # vprint for each server
        if gglobs.verbose:
            for  a in ntps: vprint("NTP Version: {}  {:20s}  {:15s}  {:10.3f} ".format(NTPversion, ntpserver, a[0], a[1]))
            print("")

    setIndent(0)

    return offset # offset in seconds


# NTP
###############################################################################