#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
gweb_radworld.py - GeigerLog support to update RadWorldMap (GMCMAP)

include in programs with:
    include gweb_radworld
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


def setupRadWorldMap():
    """Setup Radiation World Map properties"""

    fncname = "setupRadWorldMap: "
    dprint(fncname)
    setIndent(1)

    # set properties
    retval = setRadWorldMapProperties()

    if retval == 0:
        msg = "Cancelled, properties unchanged"

    else:
        fprint(header("Radiation World Map Properties"))
        fprint("Activation:",           "{}"    .format("Yes" if gglobs.RWMmapActivation else "No"))
        fprint("Update Cycle:",         "{} min".format(gglobs.RWMmapUpdateCycle))
        fprint("Selected Variable:",    "{}"    .format(gglobs.RWMmapVarSelected))
        if gglobs.RWMmapActivation:
            if gglobs.RWMmapLastUpdate is None: msg = "No - will wait for expiry of update cycle time"
            else:                               msg = "Yes - will update immediately when logging"
        else:
            msg = "N/A - No Activation"
        fprint("Update immediately:",   "{}"    .format(msg))

        msg = "ok, new settings: Activation:{}, UpdateCycle:{} min, Variable:{}, Update Now:{}".format(
                    gglobs.RWMmapActivation,
                    gglobs.RWMmapUpdateCycle,
                    gglobs.RWMmapVarSelected,
                    "No" if gglobs.RWMmapLastUpdate is None else "Yes",
                )

        # Update after next log call
        if gglobs.RWMmapActivation and gglobs.RWMmapLastUpdate == 0 and not gglobs.logging:
            fprint("Currently not logging; Radiation World Map will be updated after first logging cycle")

        # set icons
        if gglobs.RWMmapActivation:     icon = 'icon_world_v2.png'
        else:                           icon = 'icon_world_v2_inactive.png'
        gglobs.exgg.GMCmapAction.setIcon(QIcon(QPixmap(os.path.join(gglobs.gresPath, icon))))

    dprint(fncname + msg)
    setIndent(0)


def setRadWorldMapProperties():
    """Set activation and cycle time"""

    fncname = "setRadWorldMapProperties: "

    lmean = QLabel("Activate Updates")
    lmean.setAlignment(Qt.AlignLeft)
    lmean.setMinimumWidth(200)

    r01=QRadioButton("Yes")
    r02=QRadioButton("No")
    r01.setToolTip("Check 'Yes' to send Updates to Radiation World Map in regular intervals")
    r02.setToolTip("Check 'No' to never send Updates to Radiation World Map")
    if gglobs.RWMmapActivation:
        r01.setChecked(True)
        r02.setChecked(False)
    else:
        r01.setChecked(False)
        r02.setChecked(True)
    powergroup = QButtonGroup()
    powergroup.addButton(r01)
    powergroup.addButton(r02)
    hbox0=QHBoxLayout()
    hbox0.addWidget(r01)
    hbox0.addWidget(r02)
    hbox0.addStretch()

    lctime = QLabel("Update Cycle Time [minutes]\n(at least 1 min)")
    lctime.setAlignment(Qt.AlignLeft)
    ctime  = QLineEdit()
    ctime.setToolTip('Enter X to update Radiation World Map every X minutes;\nCPM averaged over this period will be used for CPM and ACPM')
    ctime.setText("{:0.5g}".format(gglobs.RWMmapUpdateCycle))

    # The selector for variable-to-use for update
    lavars = QLabel("Select Variable for Map Update")
    lavars.setAlignment(Qt.AlignLeft)
    avars = QListWidget()
    avars.setToolTip('Select the CPM variable you want to use for update')
    avars.setMaximumHeight(90)

    lstItem = QListWidgetItem("None")
    lstItem.setToolTip("No variable selected - make your selection")
    avars.addItem(lstItem)
    avars.setCurrentItem(lstItem);
    for index, vname in enumerate(gglobs.varsCopy):
        if not "CPM" in vname: continue
        lstItem = QListWidgetItem(vname)
        # edprint("vname: ", vname, "  logging: ", gglobs.varsSetForLogNew[vname])
        if gglobs.varsSetForLogNew[vname] == False:
                lstItem.setFlags(Qt.NoItemFlags)

        avars.addItem(lstItem)

    # The checkbox to set immediate update
    lckbox = QLabel("Do first update immediately")
    ckbox = QCheckBox    ()
    ckbox.setToolTip     ("A first update will be done immediately after button OK is pressed (not recommended)")
    ckbox.setChecked     (False)
    ckbox.setEnabled     (True)
    ckbox.setTristate    (False)

    # fill the grid
    graphOptions=QGridLayout()
    graphOptions.addWidget(lmean,          0, 0)
    graphOptions.addLayout(hbox0,          0, 1)
    graphOptions.addWidget(lctime,         1, 0)
    graphOptions.addWidget(ctime,          1, 1)
    graphOptions.addWidget(lavars,         2, 0)
    graphOptions.addWidget(avars,          2, 1)
    graphOptions.addWidget(lckbox,         3, 0)
    graphOptions.addWidget(ckbox,          3, 1)
    graphOptions.addWidget(QLabel(""),     4, 0)    # a blank line

    d = QDialog() # set parent to None to popup in center of screen
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setFont(gglobs.fontstd)
    srmptitle = "Set up Radiation World Map"
    d.setWindowTitle(srmptitle)
    d.setWindowModality(Qt.NonModal)
    d.setMinimumWidth(300)

    bbox = QDialogButtonBox()
    bbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok )
    bbox.accepted.connect(lambda: d.done(100))
    bbox.rejected.connect(lambda: d.done(0))

    layoutV = QVBoxLayout(d)
    layoutV.addLayout(graphOptions)
    layoutV.addWidget(bbox)

    retval = d.exec()
    # print("retval:", retval)

    if retval != 0:
        # Activation
        if r01.isChecked(): gglobs.RWMmapActivation = True
        else:               gglobs.RWMmapActivation = False

        # Cycletime
        uctime = ctime.text().replace(",", ".")  #replace any comma with dot
        try:    dt  = max(round(abs(float(uctime)), 2), 0.1)
        except: dt  = gglobs.RWMmapUpdateCycle
        gglobs.RWMmapUpdateCycle = dt

        # Variable
        text  = str(avars.currentItem().text())
        if text == "None":  # no selection was made
            text = "No variable selected - Updating is inactivated"
            gglobs.RWMmapActivation = False
            efprint(header(srmptitle))
            qefprint(text)

        dprint("Variable selection: ", text)
        gglobs.RWMmapVarSelected = text

        # Checkbox "update-now"
        if ckbox.isChecked():   gglobs.RWMmapLastUpdate = 0
        else:                   gglobs.RWMmapLastUpdate = None

    return retval


def getRadWorldMapURL():
    """assemble the data into the url and return url and data msg"""

    fncname = "getRadWorldMapURL: "

    if   gglobs.RWMmapVarSelected in ("CPM",    "CPS"):         sens = gglobs.Sensitivity[0]
    elif gglobs.RWMmapVarSelected in ("CPM1st", "CPS1st"):      sens = gglobs.Sensitivity[1]
    elif gglobs.RWMmapVarSelected in ("CPM2nd", "CPS2nd"):      sens = gglobs.Sensitivity[2]
    elif gglobs.RWMmapVarSelected in ("CPM3rd", "CPS3rd"):      sens = gglobs.Sensitivity[3]
    else:                                                       sens = gglobs.NAN

    DeltaT  = gglobs.RWMmapUpdateCycle   # DeltaT in minutes, RWMmapUpdateCycle in min

    cdprint(fncname + "gglobs.RWMmapVarSelected: {},  DeltaT: {} min".format(gglobs.RWMmapVarSelected, DeltaT))

    try:
        timedata, cpmdata, deltaTime  = getTimeCourseInLimits(gglobs.RWMmapVarSelected, DeltaT)
        cdprint(fncname + "cpmdata[:10] ... [-10:]: ", cpmdata[:10], "...", cpmdata[-10:])

    except Exception as e:
        srcinfo = "No proper data available"
        exceptPrint(fncname + str(e), srcinfo)
        return "", srcinfo                      # blank url is used for testing

    if np.isnan(cpmdata).all():
        srcinfo = "All data are NAN"
        return "", srcinfo                      # blank url is used for testing

    CPM          = np.nanmean(cpmdata)
    ACPM         = CPM
    uSV          = CPM / sens
    # cdprint(fncname + "CPM: {:0.3f}, ACPM: {:0.3f}, uSV: {:0.3f}".format(CPM, ACPM, uSV))

    data         = {}
    data['AID']  = gglobs.gmcmapUserID
    data['GID']  = gglobs.gmcmapCounterID
    data['CPM']  = "{:3.1f}".format(CPM)
    data['ACPM'] = "{:3.1f}".format(ACPM)
    data['uSV']  = "{:3.2f}".format(uSV)

    baseURL      = gglobs.gmcmapWebsite + "/" + gglobs.gmcmapURL
    gmcmapURL    = "http://" + baseURL + "?" + urllib.parse.urlencode(data)                 # MUST use 'http://' in front!
    dmsg         = "CPM:{}  ACPM:{}  uSV:{}".format(data['CPM'],data['ACPM'],data['uSV'])

    return gmcmapURL, dmsg


def updateRadWorldMap():
    """get a new data set and send as message to GMCmap"""

    fncname = "updateRadWorldMap: "

    dprint(fncname)
    setIndent(1)

    gmcmapURL, dmsg = getRadWorldMapURL()    # gmcmapURL has the url with data as GET
    dprint(fncname + "URL:  " + gmcmapURL)
    dprint(fncname + "Data: " + dmsg)

    fprint(header("Update Radiation World Map"))
    if gmcmapURL > "":
        try:
            fprint(" {}  Sending Data: {}".format(stime(), dmsg))
            with urllib.request.urlopen(gmcmapURL) as response:
                answer = response.read()
            dprint(fncname + "RAW Server Response: ", answer)

        except Exception as e:
            answer  = b"Bad URL"
            srcinfo = "Bad URL: " + gmcmapURL
            exceptPrint("pushToWeb: " + str(e), srcinfo)

        # remove the HTML code from answer
        cleanAnswer = "{}".format((re.sub('<[^<]+?>', '', answer.decode('UTF-8'))).strip())
        # dprint("Server Response cleaned: ", cleanAnswer)
        msg1        = "Updating got server response: '{}' ".format(cleanAnswer)
        msg2        = "on URL: {}".format(gmcmapURL)

        # Evaluate server answer
        if b"ERR0" in answer:
            # Success
            # b"ERR0" in answer     => Ok
            gglobs.exgg.addMsgToLog("Success", msg1 + msg2)
            fprint("Server Response: OK")

        else:
            # Failure
            # b"ERR1" in answer     => wrong userid
            # b"ERR2" in answer     => wrong counterid
            # b"Bad URL" in answer  => misformed URL => typo in GeigerLog config?
            # other                 => other errors, including ERR3 (when wrong url was used)
            efprint ("{} FAILURE".format(stime()))
            qefprint(msg1)
            qefprint(msg2)
            gglobs.exgg.addMsgToLog("FAILURE", msg1 + msg2)
    else:
        efprint ("{} FAILURE - {}".format(stime(), dmsg) )
        gglobs.exgg.addMsgToLog("FAILURE", "Updating Radiation World Map: " + dmsg)

    setIndent(0)
