#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gdev_manu.py - GeigerLog commands to handle the manual entry of data
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


def initManu():
    """Start the device"""

    fncname = "initManu: "

    dprint(fncname + "Initializing Manu Device")
    setIndent(1)

    gglobs.Devices["Manu"][DNAME] = "Manual Data"

    if gglobs.ManuVariables    == "auto": gglobs.ManuVariables    = "Temp, Press, Humid, Xtra"
    if gglobs.ManuRecordStyle  == "auto": gglobs.ManuRecordStyle  = "Point"                         # alternative: "Step"

    ManuVars = gglobs.ManuVariables.split(",")
    # MUST remove blanks on vars
    for i, mv in enumerate(ManuVars):   ManuVars[i] = mv.strip()

    # weed out any wrong vnames and put into right sequence as defined in varsCopy
    # then redefine gglobs.ManuVariables with cleaned version
    mvs = ""
    for vname in gglobs.varsCopy:
        if vname in ManuVars:  mvs += "{}, ".format(vname)
    gglobs.ManuVariables = mvs[:-2]

    # set standards
    setLoggableVariables("Manu", gglobs.ManuVariables)

    # device is connected
    gglobs.Devices["Manu"][CONN] = True

    setIndent(0)

    return ""  # no errmsg for return


def terminateManu():
    """Stop the Manu counting"""

    fncname ="terminateManu: "

    dprint(fncname)
    setIndent(1)

    gglobs.Devices["Manu"][CONN]  = False

    dprint(fncname + "Terminated")
    setIndent(0)


def getValuesManu(varlist):
    """provide entered values"""

    start = time.time()
    fncname = "getValuesManu: "
    # print(fncname + "varlist: ", varlist)

    alldata = {}
    for i, vname in enumerate(varlist):
        alldata.update({vname:   gglobs.ManuValue[i]})
        if gglobs.ManuRecordStyle == "Point": gglobs.ManuValue[i] = gglobs.NAN  # if Style is Point: reset after read-out

    vprintLoggedValues(fncname, varlist, alldata, (time.time() - start) * 1000)

    return alldata


def setManuValue():
    """Enter a value manually"""

    fncname = "setManuValue: "

    dprint(fncname)
    setIndent(1)

    countManuVars = len(gglobs.ManuVariables.split(","))

    lv = [None] * countManuVars
    v  = [None] * countManuVars
    for i in range(countManuVars):
        lv[i] = QLabel("Value #{:<2n} for Variable: {}".format(i + 1, gglobs.Devices["Manu"][VNAME][i]))
        lv[i].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        v[i]  = QLineEdit()
        v[i].setToolTip("Enter a value manually for variable: {}".format(gglobs.Devices["Manu"][VNAME][i]))
        v[i].setText("")

    lvR = QLabel("Select Record Style")
    lvR.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    rR1=QRadioButton("Point")
    rR1.setToolTip("A single point is drawn")
    rR2=QRadioButton("Step")
    rR2.setToolTip("The value is repeated until changed")
    enstyle = True if (gglobs.ManuRecordStyle == "Point" or gglobs.ManuRecordStyle == "auto") else False
    rR1.setChecked(enstyle)
    rR2.setChecked(not enstyle)
    rR1.setEnabled(True)
    rR2.setEnabled(True)
    rstylegroup = QButtonGroup()
    rstylegroup.addButton(rR1)
    rstylegroup.addButton(rR2)
    hboxR=QHBoxLayout()
    hboxR.addWidget(rR1)
    hboxR.addWidget(rR2)
    hboxR.addStretch()

    graphOptions=QGridLayout()
    graphOptions.setContentsMargins(10,10,10,10) # spacing around the graph options

    for i in range(countManuVars):
        graphOptions.addWidget(lv[i],   i, 0)
        graphOptions.addWidget(v[i],    i, 1)

    graphOptions.addWidget(lvR,     i + 1, 0)
    graphOptions.addLayout(hboxR,   i + 1, 1)

    # Dialog box
    d = QDialog()
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setFont(gglobs.fontstd)
    d.setWindowTitle("Enter Manual Value")
    d.setWindowModality(Qt.WindowModal)
    d.setMinimumWidth(400)

    # Buttons
    bbox = QDialogButtonBox()
    bbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok )
    bbox.accepted.connect(lambda: d.done(1))
    bbox.rejected.connect(lambda: d.done(-1))

    gglobs.btn = bbox.button(QDialogButtonBox.Ok)
    gglobs.btn.setEnabled(True)

    layoutV = QVBoxLayout(d)
    layoutV.addLayout(graphOptions)
    layoutV.addWidget(bbox)

    retval = d.exec()
    #print("reval:", retval)

    if retval != 1:
        # ESCAPE pressed or Cancel Button
        dprint(fncname + "Canceling; no changes made")

    else:
        # OK pressed
        # fill up all the ManuValue with manually entered data
        for i in range(countManuVars):
            mval = v[i].text().strip().replace(",", ".")
            if mval > "":
                try:    nval = float(mval)
                except: nval = gglobs.NAN
                gglobs.ManuValue[i] = nval

        if rR1.isChecked():     gglobs.ManuRecordStyle = "Point"
        else:                   gglobs.ManuRecordStyle = "Step"

        msg = ""
        for i in range(countManuVars):
            msg += "Value #{:<2d} for Variable: {:6s} : {:0.3f}\n".format(i + 1, gglobs.Devices["Manu"][VNAME][i], gglobs.ManuValue[i])
        msg +=     "Record Style: {}\n".format(gglobs.ManuRecordStyle)

        fprint(header("Manual Values"))
        fprint(msg)
        dprint(msg.replace("\n", "  "))

        runLogCycle()   # to force saving, displaying and plotting of the new data

    setIndent(0)


def getInfoManu(extended = False):
    """Info on settings of the sounddev thread"""

    ManuInfo  = "Configured Connection:        Plugin\n"
    if not gglobs.Devices["Manu"][CONN]: return ManuInfo + "<red>Device is not connected</red>"

    ManuInfo += "Connected Device:             {}\n"  .format(gglobs.Devices["Manu"][DNAME])
    ManuInfo += "Configured Variables:         {}\n"  .format(gglobs.ManuVariables)
    ManuInfo += getTubeSensitivities(gglobs.ManuVariables)

    if extended == True:
        ManuInfo += ""

    return ManuInfo

