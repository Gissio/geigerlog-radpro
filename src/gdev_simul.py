#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gdev_simul.py - GeigerLog commands to handle the simul device, which simulates
                counts using a synthetic Poisson number generator
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


def initSimul():
    """Start the simulator"""

    global cps_record_POISSON, cps_record_NORMAL, SimulCounterCalls, prevtimePointNopa, prevtimePointPara, M, tau, lasteventPara, lasteventNopa

    fncname ="initSimul: "

    dprint(fncname + "Initializing Simul Device")
    setIndent(1)

    errmsg  = "" # what errors can be here?
    gglobs.Devices["Simul"][DNAME] = "Simulator"

    if gglobs.SimulMean         == "auto": gglobs.SimulMean         = 0.3         # "background"
    if gglobs.SimulVariables    == "auto": gglobs.SimulVariables    = "CPM, CPS"  # non-predictive;
    if gglobs.SimulDeadtime     == "auto": gglobs.SimulDeadtime     = 120         # 120 µs deadtime

    #if gglobs.SimulPredictive   == "auto": gglobs.SimulPredictive   = False      # let CPM accumulate
    #if gglobs.SimulPredictLimit == "auto": gglobs.SimulPredictLimit = 25         # CPM prediction after this count was reached

    setLoggableVariables("Simul", gglobs.SimulVariables)

    makeStartRecord(gglobs.SimulMean)

    gglobs.Devices["Simul"][CONN] = True

    SimulCounterCalls  =  0   # how many times the get data routine was called (??? not used anywhere)
    prevtimePointNopa  =  0
    prevtimePointPara  =  0
    lasteventNopa      = -1
    lasteventPara      = -1

    setIndent(0)

    return errmsg


def makeStartRecord(mean):
    """sets the first 60 CPS values to get full cpm reading"""

    global cps_record_POISSON, cps_record_NORMAL

    stddev              = np.sqrt(mean) # StdDev must be same for POISSON and NORMAL
    gglobs.SimulStdDev  = stddev

    # make POISSON record
    cps_record_POISSON = np.random.poisson(mean, size=60)           # POISSON: generates 1 record of 60 "CPS counts"

    # make NORMAL record
    cps_record_NORMAL  = np.random.normal(mean, stddev, size=60)    # NORMAL: generates 1 record of 60 "CPS counts"
    # clean NORMAL to POISSON-like
    for i in range(60):
        if cps_record_NORMAL[i] < 0: cps_record_NORMAL[i] = 0                              # eliminate negative values
        else:                        cps_record_NORMAL[i] = round(cps_record_NORMAL[i], 0) # round positiv values to integer


def terminateSimul():
    """Stop the Simul Device"""

    fncname ="terminateSimul: "

    dprint(fncname)
    setIndent(1)

    gglobs.Devices["Simul"][CONN] = False

    dprint(fncname + "Terminated")
    setIndent(0)


def getValuesSimul(varlist):
    """Read all data; return empty dict when not available"""

    ##############################################################
    def FixNANtoInt(value):
        """if value is NAN, it returns NAN, otherwise a value rounded to integer"""

        if np.isnan(value): return gglobs.NAN
        else:               return round(value, 0)
    ##############################################################

    global cps_record_POISSON, cps_record_NORMAL, SimulCounterCalls, prevtimePointNopa, prevtimePointPara, lasteventPara, lasteventNopa

    start = time.time()
    fncname = "getValuesSimul: "
    #print(fncname + "varlist: ", varlist)

    alldata = {}

    # take as many samples as the logCycle has seconds to cover full cps
    size               = int(max(1, gglobs.logCycle))
    SimulCounterCalls += size

    # now add the fresh counts for POISSON
    simulcpsPOISSON    = np.random.poisson(gglobs.SimulMean, size=size)             # generates the POISSON "CPS counts"
    cps_record_POISSON = np.append(cps_record_POISSON, simulcpsPOISSON)[-60:]       # append, but then take last 60 values only

    # now add the fresh counts for NORMAL
    simulcpsNORMAL     = np.random.normal(gglobs.SimulMean, gglobs.SimulStdDev, size=size)  # generates the NORMAL "CPS counts"
    for i in range(size):
        # print(simulcpsNORMAL[i])
        if   simulcpsNORMAL[i] < 0: simulcpsNORMAL[i] = 0                           # negative values eliminated
        else:                       simulcpsNORMAL[i] = round(simulcpsNORMAL[i], 0) # positiv values rounded to integer
    cps_record_NORMAL  = np.append(cps_record_NORMAL, simulcpsNORMAL)[-60:]         # append, but then take last 60 values only

    #~print("--------size: ", size, ", simulcpsPOISSON:", simulcpsPOISSON)
    #~print("cps_record_POISSON: nansum", np.nansum(cps_record_POISSON), "cps_record_POISSON:\n", cps_record_POISSON)

    for vname in varlist:
        # CPM from Poisson
        if   vname == "CPM":
            cpm             = float(np.nansum(cps_record_POISSON))        # must do float conversion or a blob will be stored in db
            cpm             = FixNANtoInt(scaleVarValues(vname, cpm, gglobs.ValueScale[vname]))
            alldata.update(  {vname: cpm})

        # CPS from Poisson
        elif vname == "CPS":
            cps             = float(cps_record_POISSON[-1])               # must do float conversion or a blob will be stored in db
            cps             = FixNANtoInt(scaleVarValues(vname, cps, gglobs.ValueScale[vname] ))
            alldata.update(  {vname: cps})

        # CPM1st from NORMAL
        elif vname == "CPM1st":
            cpm             = float(np.nansum(cps_record_NORMAL)) # must do float conversion or a blob will be stored in db
            cpm             = FixNANtoInt(scaleVarValues(vname, cpm, gglobs.ValueScale[vname]))
            alldata.update(  {vname: cpm})

        # CPS1st from NORMAL
        elif vname == "CPS1st":
            cps             = float(cps_record_NORMAL[-1])        # must do float conversion or a blob will be stored in db
            cps             = FixNANtoInt(scaleVarValues(vname, cps, gglobs.ValueScale[vname] ))
            alldata.update(  {vname: cps})

## testing
        # CPM2nd
        elif vname == "CPM2nd":
            alldata.update(  {vname: int(np.random.poisson(600))} )

        # CPS2nd
        elif vname == "CPS2nd":
            alldata.update(  {vname: int(np.random.poisson(25))} )

        # CPM3rd
        elif vname == "CPM3rd":
            alldata.update(  {vname: int(np.random.poisson(6000))} )

        # CPS3rd
        elif vname == "CPS3rd":
            alldata.update(  {vname: int(np.random.poisson(77))} )

        # Temp
        elif vname == "Temp":
            alldata.update(  {vname: np.random.normal(25, 2.5)} )

        # Press
        elif vname == "Press":
            alldata.update(  {vname: np.random.normal(1000, 10)} )

        # # Humid
        # elif vname == "Humid":
        #     alldata.update(  {vname: np.random.normal(50, 5)} )

        # # Xtra
        # elif vname == "Xtra":
        #     alldata.update(  {vname: np.random.normal(70, 7)} )
## end testing ##################

# # NOPA
#         # CPM2nd
#         # used for CPS with ***non-paralyzing deadtime*** correction
#         # die nicht verlängerbare und die verlängerbare Totzeit. https://de.wikipedia.org/wiki/Totzeit_(Teilchenmesstechnik)
#         elif vname == "CPM2nd":
#             mean                = gglobs.SimulMean              # mean in CPS
#             dt                  = gglobs.SimulDeadtime / 1E6    # deadtime[s] converted from deadtime[µs] as given in config
#             cps_counted         = 0                             # counts detected within present collection cycle
#             cps_missed          = 0                             # counts UN-detected because too soon after last
#             timePoint           = prevtimePointNopa             # duration in sec of this current second of collection; starting with leftover from last cycle

#             # print("prevtimePointNopa: {:10.6f}".format(prevtimePointNopa))

#             if prevtimePointNopa >= 1:      # more than 1 sec; skip counting for this 1 sec interval
#                 prevtimePointNopa -= 1

#             else:
#                 if prevtimePointNopa > 0:
#                     cps_counted += 1        # count set in last cycle

#                 counter = 0
#                 while True:
#                     gap        = np.random.exponential(1 / mean)     # gap between two pulse starts in sec
#                     timePoint += gap
#                     # print("{} mean= {:0.2f}, timepoint= {:9.6f}s  lastevent:{:9.6f}, tpnt-lastev: {:6.0f}µs ".format(counter, mean, timePoint, lasteventNopa, 1e6*(timePoint - lasteventNopa)))
#                     counter += 1
#                     if timePoint > 1:                                # count up to 1 sec only; beyond 1 sec events will be counted in next cycle
#                         prevtimePointNopa = timePoint - 1            # The pulse begins in next cycle
#                         lasteventNopa    -= 1                        # subtract 1 sec to have last event at proper position
#                         # print("mean= {:0.0f}, t= {:7.3f} totd= {:0.6f} prevtimePointNopa: {:3.0f} break".format(mean, t * 1e6, timePoint, prevtimePointNopa * 1e6))
#                         break                                        # nothing more to do in this cycle

#                     else:  # timePoint <= 1 sec                      # still in the current cycle
#                         if (timePoint - lasteventNopa) >= dt:        # and time to last pulse is > deadtime,
#                             cps_counted += 1                         # so count it as CPS, ...
#                             lasteventNopa = timePoint                # make this to the last pulse time oint
#                         else:
#                             cps_missed += 1                          # ... otherwise count it as missed CPS!
#                                                                      # NOTE: lasteventNopa has NOT changed, as non-paralyzing event!
#                 # end while

#             cps             = cps_counted + cps_missed
#             cps             = FixNANtoInt(scaleVarValues(vname, cps, gglobs.ValueScale[vname] ))
#             alldata.update(  {vname: cps})

#             # counts after correction based on counted counts
#             vnameX = "CPS2nd"
#             if vnameX in varlist:
#                 # Die NOPADEC Gleichung ist  N = M / (1 - M * τ)
#                 localValueScale = "nopadec(VAL, {})".format(gglobs.SimulDeadtime)
#                 cps_corr        = cps_counted
#                 cps_corr        = FixNANtoInt(scaleVarValues(vnameX, cps_corr, localValueScale))
#                 # print("CPS2nd: cps_counted:{} cps_corr:{}".format(cps_counted, cps_corr))
#                 alldata.update(  {vnameX: cps_corr})

#             # counted counts
#             vnameX = "CPM3rd"
#             if vnameX in varlist:
#                 cps        = cps_counted
#                 cps        = FixNANtoInt(scaleVarValues(vnameX, cps, gglobs.ValueScale[vnameX] ))
#                 alldata.update(  {vnameX: cps})

#             # missed counts
#             vnameX = "CPS3rd"
#             if  vnameX in varlist:
#                 cps        = cps_missed
#                 cps        = FixNANtoInt(scaleVarValues(vnameX, cps, gglobs.ValueScale[vnameX] ))
#                 alldata.update(  {vnameX: cps})

# # PARA
#         # T
#         # used for CPS with ***paralyzing deadtime*** correction
#         # die nicht verlängerbare und die verlängerbare Totzeit. https://de.wikipedia.org/wiki/Totzeit_(Teilchenmesstechnik)
#         elif vname == "Temp":
#             mean                = gglobs.SimulMean              # mean in CPS
#             dt                  = gglobs.SimulDeadtime / 1E6    # deadtime[s] converted from deadtime[µs] as given in config
#             cps_counted         = 0                             # counts detected within present collection cycle
#             cps_missed          = 0                             # counts UN-detected because too soon after last
#             timePoint           = prevtimePointPara               # duration in sec of this current second of collection; starting with leftover from last cycle

#             # print("prevtimePointPara: {:10.6f}".format(prevtimePointPara))
#             # print("mean= {:0.2f}, totd= {:9.6f}s  lasteventPara:{}, prevtimePointPara: {:9.6f}s ".format(mean, timePoint, lasteventPara, prevtimePointPara))
#             if prevtimePointPara >= 1:
#                 prevtimePointPara -= 1
#             else:
#                 if prevtimePointPara > 0:
#                     cps_counted += 1               # count coming from last cycle

#                 while True:
#                     gap        = np.random.exponential(1 / mean)        # gap between two pulse-starts in sec
#                     timePoint += gap
#                     #print("mean= {:0.2f}, dt= {:9.6f}s  tPoint= {:9.6f}s  prevtimePointPara: {:9.6f}s ".format(mean, dt, timePoint, prevtimePointPara))

#                     if timePoint > 1:                                   # count up to 1 sec only; then events will be counter in next cycle
#                         prevtimePointPara = timePoint - 1               # The pulse extends into next counting cycle
#                         lasteventPara    -= 1
#                         # print("mean= {:0.0f}, t= {:7.3f} totd= {:0.6f} prevtimePointPara: {:3.0f} break".format(mean, t * 1e6, timePoint, prevtimePointPara * 1e6))
#                         break
#                     else:
#                         if (timePoint - lasteventPara) >= dt:
#                             cps_counted += 1                            # if time to last pulse is > deadtime then count it as CPS
#                             lasteventPara = timePoint

#                         else:
#                             cps_missed += 1                             # otherwise increment missed CPS!
#                             lasteventPara = timePoint                   # but ALSO extent duration, as the event has increased the deadtime!
#                 # end while

#             cps             = cps_counted + cps_missed
#             cps             = FixNANtoInt(scaleVarValues(vname, cps, gglobs.ValueScale[vname] ))
#             alldata.update(  {vname: cps})

#             # counts after correction based on counted counts
#             vnameX = "Press"
#             if vnameX in varlist:
#                 # Die PADEC Gleichung ist  m = n * exp(− n τ)
#                 localValueScale        = "padec(VAL, {})".format(gglobs.SimulDeadtime)
#                 cps_corr               = cps_counted
#                 cps_corr               = FixNANtoInt(scaleVarValues(vnameX, cps_corr, localValueScale)) # do I need to round() this?
#                 alldata.update(  {vnameX: cps_corr})

#             # counted counts
#             vnameX = "Humid"
#             if vnameX in varlist:
#                 cps        = cps_counted
#                 cps        = FixNANtoInt(scaleVarValues(vnameX, cps, gglobs.ValueScale[vnameX] ))
#                 alldata.update(  {vnameX: cps})

#             # missed counts
#             vnameX = "Xtra"
#             if  vnameX in varlist:
#                 cps        = cps_missed
#                 cps        = FixNANtoInt(scaleVarValues(vnameX, cps, gglobs.ValueScale[vnameX] ))
#                 alldata.update(  {vnameX: cps})

    duration = 1000 * (time.time() - start)
    if gglobs.devel: alldata.update({"Humid": duration})

    vprintLoggedValues(fncname, varlist, alldata, duration)

    return alldata


def getSimulProperties():
    """Set mean and predictive limit"""

    fncname = "getSimulProperties: "
    dprint(fncname)
    setIndent(1)

    lmean = QLabel("CPS Mean\n(0 ... 100000)")
    lmean.setAlignment(Qt.AlignLeft)
    mean = QLineEdit()
    mean.setToolTip('The mean of the Poisson distribution for the CPS variable')
    mean.setText("{:0.5g}".format(gglobs.SimulMean))

    # lplimit = QLabel("Prediction Limit\n(not negative)")
    # lplimit.setAlignment(Qt.AlignLeft)
    # plimit  = QLineEdit()
    # plimit.setToolTip('The limit for prediction')
    # plimit.setText("{:0.5g}".format(gglobs.SimulPredictLimit))

    ldeadtime = QLabel("Tube Deadtime [µs]\n(not negative)")
    ldeadtime.setAlignment(Qt.AlignLeft)
    deadtime  = QLineEdit()
    deadtime.setToolTip("The tube's deadtime in micro-second")
    deadtime.setText("{:0.5g}".format(gglobs.SimulDeadtime))

    graphOptions=QGridLayout()
    graphOptions.addWidget(lmean,           0, 0)
    graphOptions.addWidget(mean,            0, 1)
    # graphOptions.addWidget(ldeadtime,       1, 0)
    # graphOptions.addWidget(deadtime,        1, 1)
    #~graphOptions.addWidget(lplimit,         1, 0) # do not show
    #~graphOptions.addWidget(plimit,          1, 1) # do not show

    d = QDialog()
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setFont(gglobs.fontstd)
    d.setWindowTitle("Simul Device Properties")
    d.setWindowModality(Qt.WindowModal)
    d.setMinimumWidth(300)

    bbox = QDialogButtonBox()
    bbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok )
    bbox.accepted.connect(lambda: d.done(100))
    bbox.rejected.connect(lambda: d.done(0))

    layoutV = QVBoxLayout(d)
    layoutV.addLayout(graphOptions)
    layoutV.addWidget(bbox)

    retval = d.exec()
    #print("reval:", retval)

    if retval == 0:
        dprint(fncname + "Cancelled, Properties unchanged")
    else:
        # mean
        mean        = mean.text().replace(",", ".")    #replace any comma with dot
        try:    lm  = round(abs(float(mean)), 2)
        except: lm  = gglobs.SimulMean
        if lm <= 100000: gglobs.SimulMean = lm
        else:            efprint("Illegal entry for mean: ", lm)

        makeStartRecord(gglobs.SimulMean)   # make full CPS records to have correct CPM from the beginning

        # # plimit
        #     plimit      = plimit.text().replace(",", ".")  #replace any comma with dot
        #     try:    lp  = round(abs(float(plimit)), 1)
        #     except: lp  = gglobs.SimulPredictLimit
        #     gglobs.SimulPredictLimit = lp

        # deadtime
        deadtime    = deadtime.text().replace(",", ".")  #replace any comma with dot
        try:    gglobs.SimulDeadtime = round(abs(float(deadtime)), 1)
        except: pass

        # dprint(fncname + "ok, new settings: Mean: {}  Tube Deadtime: {} µs  Prediction Limit: {}".\
        #             format(gglobs.SimulMean, gglobs.SimulDeadtime, gglobs.SimulPredictLimit))
        dprint(fncname + "ok, new settings: Mean: {}  Tube Deadtime: {} µs".format(
                                                                                    gglobs.SimulMean,
                                                                                    gglobs.SimulDeadtime))

        fprint(getInfoSimul())

    setIndent(0)


def getInfoSimul(extended = False):
    """Info on the Simul Device"""

    SimulInfo = "Configured Connection:        Plugin\n"

    if not gglobs.Devices["Simul"][CONN]:
        SimulInfo += "<red>Device is not connected</red>"
    else:
        SimulInfo += "Connected Device:             {}\n".format(gglobs.Devices["Simul"][DNAME])
        SimulInfo += "Configured Variables:         {}\n".format(gglobs.SimulVariables)
        SimulInfo += "Counts-Per-Second Mean:       {:0.2f} --> CPM={:0.2f}\n".format(gglobs.SimulMean, gglobs.SimulMean * 60,)
        SimulInfo += getTubeSensitivities(gglobs.SimulVariables)

    return SimulInfo



# ## from the config file; currently not used
#
# Extended geigerlog.cfg content for simul
#
# [Simul Device]
# # Using a Poisson number generator to get "counts", simulating recordings with
# # defined Poisson properties. Experiments with deadtime correction is also
# # supported

# # Simul Device ACTIVATION
# # to use (yes) or not use (no) the Simul Device
# #
# # Options:        yes | no
# # Default       = yes
# SimulActivation = no

# # Simul Device MEAN
# # A Poisson generator needs only a single value, which is the mean of the
# # distribution. GeigerLog interprets it as CPS.
# #
# # A typical background count for a M4011 or SBM20 tube is CPM = 18, which
# # gives: CPS = 18 / 60 = 0.3. This is used as default setting
# #
# # NOTE:     an option of 0 (zero) is mathematically possible, but meaningless, as
# #           there will never be a single "count".
# #
# # Option auto defaults to 0.3
# #
# # Options:     auto | <any number greater or equal to 0(zero)>
# # Default    = auto
# # SimulMean    = auto
# SimulMean    = 300


# # Simul Device VARIABLES:
# # Available are all variables CPM, CPS, CPM1st, CPS1st, CPM2nd, CPS2nd, Temp, Press, Humid, Xtra.
# # Only certain combinations are meaningful due to some specific programming:
# #
# # Selecting: CPM and CPS:
# # Data with a true Poisson distribution property are generated for a CPS and
# # resulting CPM with a mean as spcified above as SimulMean.
# #
# # Selecting: CPM1st and CPS1st:
# # Data with a Normal distribution property are generated for a CPS and resulting
# # CPM with a mean as spcified above as SimulMean.
# # NOTE: a Normal distribution is incorrect with respect to radioactive decay! This
# #       is thus only for educational purposed to demonstrate how close Normal is to
# #       Poisson when the mean is large enough (e.g > 10 CPS).
# #
# # The remaining 8 variables are configured in this SIMULCOUNTER to reveal the
# # results from using a "Deadtime Correction" procedure. You will need to see
# # the manual for information.
# #
# # Selecting CPM2nd, CPS2nd, CPM3rd, and CPSrd:
# # NOTE:     The results are relevant for a process with Non-Paralyzing events.
# #           This is NOT the situation in a Geiger counter!
# #
# # In this specific setup all 4 variables will give CPS (Count per SECOND)
# # results, including the two CPM* named variables!
# # CPM2nd:   The full counts from a Poisson distribution with a mean specified
# #           above as SimulMean
# # CPM3rd:   Only the counts that would have been registered given the deadtime
# # CPS3rd:   Only the counts that would have been missed given the deadtime
# #           It is strictly valid:  CPM2nd = CPM3rd + CPS3rd
# # CPS2nd:   The corrected counts determined from CPMrd
# #           The fourmula is:  CPS_true = CPS_obs / (1 - CPS_obs * deadtime[s])
# #
# #
# # Selecting Temp, Press, Humid, and Xtra:
# # NOTE:     The results are relevant for a process with Paralyzing events.
# #           This is the situation as in a Geiger counter!
# #
# # In this specific setup all 4 Ambient variables will give CPS (Count per SECOND)
# # results.
# # Temp:     The full counts from a Poisson distribution with a mean specified
# #           above as SimulMean
# # Humid:    Only the counts that would have been registered given the deadtime
# # Xtra:     Only the counts that would have been missed given the deadtime
# #           It is strictly valid:  Temp = Humid + Xtra
# # Press:    The corrected counts determined from H
# #           The fourmula is:  CPM_obs = CPM_true * exp(- CPM_true * deadtime)
# # NOTE:     This formula cannot be solved analytically; GeigerLog uses an
# #           iterative process to find a solution, IF A SOLUTION EXISTS AT ALL!
# #
# #
# # Option auto defaults to 'CPM, CPS'
# #
# # Options:        auto | <any variables as explained above>
# # Default       = auto
# # SimulVariables = auto
# # SimulVariables = CPM, CPS
# # SimulVariables = CPM, CPS, CPM1st, CPS1st, CPM2nd, CPS2nd, CPM3rd, CPS3rd
# SimulVariables = CPM, CPS, Temp, Press, Humid, Xtra
# # SimulVariables = Temp, Press, Humid, Xtra
# # SimulVariables = CPM, CPS, CPM1st, CPS1st, CPM2nd, CPS2nd, CPM3rd, CPS3rd, Temp, Press, Humid, Xtra

# # Simul Device DEADTIME:
# # To be given in µs (micro-seconds)
# #
# # Typical Geiger tube deadtimes range from 50 ... 200 µs.
# # GQ is rating its M4011 tube with a deadtime of 120µs. This may not be correct.
# # The true deadtime might well be larger, perhaps as large as 200µs, see:
# # http://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=4598
# #
# # NOTE: CPS=7000 is limit for deadtime=120 -> every 10th count fails
# #
# # Option auto defaults to 120
# #
# # Options:       auto | <any non-negative number>
# # Default      = auto
# # SimulDeadtime  = auto
# SimulDeadtime  = 200
#
#
# ################ NOT IN USE ###################################################
# # Simul Device PREDICTIVE
# # Determines whether CPM is let to accumulate or a prediction is made after
# # first counts.
# #
# # Option auto defaults to 'no'
# #
# # Options:        auto | yes | no
# # Default       = auto
# #~SimulPredictive   = auto
# SimulPredictive   = no


# # Simul Device PREDICTLIMIT
# # Sets the count limit which CPM must have reached before a first CPM-prediction
# # is given. Before CPM will be reported as NAN.
# # Statistical certainty from Std.Dev = Sqrt(N) (valid for Poisson):
# # CPM =  10:   ~30%
# # CPM =  25:    20%
# # CPM = 100:    10%
# #
# # Option auto defaults to 25
# #
# # Options:          auto | <any number >= 0 >
# # Default         = auto
# SimulPredictLimit = auto
# ###############################################################################

