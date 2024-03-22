#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gstat_fft.py - GeigerLog commands for FFT statistics

include in programs with:
    import gstat_fft
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


from   gsup_utils            import *


def plotFFT():
    """Plotting FFT and Autocorrelation"""

    # nomenclature
    # t       = time
    # sigt    = Signal in time domain, (like CPM/CPS)
    # freq    = Signal in frequency domain

    if gglobs.logTimeSlice is None:
        gglobs.exgg.showStatusMessage("No data available")
        return

    vindex      = gglobs.exgg.select.currentIndex()
    vname       = list(gglobs.varsCopy)[vindex]
    vnameFull   = gglobs.varsCopy[vname][0]
    yunit       = vnameFull
    #print("plotFFT: vname, vnameFull: ", vname, vnameFull)

    try:
        rawt0    = gglobs.logTimeDiffSlice
    except Exception as e:
        srcinfo = "plotFFT: could not load time data"
        exceptPrint(e, srcinfo)
        return

    try:
        rawsigt0 = gglobs.logSliceMod[vname]
    except Exception as e:
        srcinfo = "plotFFT: could not load value data"
        exceptPrint(e, srcinfo)
        return

    if rawsigt0 is None:
        gglobs.exgg.showStatusMessage("No data available")
        return

    rawt0_nonnan   = np.count_nonzero(~np.isnan(rawt0))         # non-nan count
    rawsigt0_nonan = np.count_nonzero(~np.isnan(rawsigt0))      # dito

    if rawt0_nonnan < 20 or rawsigt0_nonan < 20:
        gglobs.exgg.showStatusMessage("Not enough data (need 20+)")
        return

    setBusyCursor()

    #print("rawt0, rawsigt0: len:", len(rawt0), len(rawsigt0))
    rawt    = np.ndarray(0)
    rawsigt = np.ndarray(0)
    for i in range(0, len(rawt0)):
        if np.isnan(rawsigt0[i]):
            #print("i, x0[i]:", i, x0[i])
            continue
        else:
            #print("i, x[i]:", i, x0[i])
            rawt    = np.append(rawt,    rawt0[i])
            rawsigt = np.append(rawsigt, rawsigt0[i])
    #print("rawt, rawsigt: len:", len(rawt), len(rawsigt))

    markersize  = 1.0
    DataSrc     = os.path.basename(gglobs.currentDBPath)

    t    = rawt.copy()
    sigt = rawsigt.copy()

    if t.size == 0:
        gglobs.exgg.showStatusMessage("No data available")
        setNormalCursor()
        return

    ####### Window functions ##############################################
    # the only place to activate Window function is this:
    use_window_functions = False

    if use_window_functions:
    # the window functions:
        hamm    = np.hamming (len(t))
        hann    = np.hanning (len(t))
        black   = np.blackman(len(t))
        # Kaiser:
        # "A beta value of 14 is probably a good starting point"
        # beta  Window shape
        # 0     Rectangular
        # 5     Similar to a Hamming
        # 6     Similar to a Hanning
        # 8.6   Similar to a Blackman
        beta    = 5
        kaiser  = np.kaiser(len(t), beta)

    # Select one of the windows functions
        #win     = hamm
        #win     = hann
        #win     = black
        win     = kaiser

    # apply window function
        # When using window function subtract the average in order to avoid
        # spurious low-frequency peaks!
        sigt   = sigt - np.mean(sigt)
        #sigt2  = sigt - np.mean(sigt)

        # Time domain signal with Window function applied
        sigt_win = sigt * win
    #######################################################################

    t               = t * 1440.0  # convert days to minutes
    timeunit        = "minutes"
    frequencyunit   = "1/minute"
    cycletime       = (t[-1] - t[0]) / (t.size -1)  # in minutes

    # calc with ignoreing the nan values            # including nan values
    sigt_mean       = np.nanmean    (sigt)          # np.mean(sigt)
    sigt_var        = np.nanvar     (sigt)          # np.var(sigt)
    sigt_std        = np.nanstd     (sigt)          # np.std(sigt)
    sigt_err        = sigt_std / np.sqrt(sigt.size) # sigt_std / np.sqrt(sigt.size)

    cdprint("----------------sigt_mean = ", sigt_mean)
    cdprint("----------------sigt_var  = ", sigt_var)
    cdprint("----------------sigt_std  = ", sigt_std)
    cdprint("----------------sigt_err  = ", sigt_err)

    if sigt_var == 0:
        gglobs.exgg.showStatusMessage("All data variances are zero; cannot calculate FFT!")
        setIndent(0)
        setNormalCursor()
        return

    # FFT calculation #####################################################
    # using amplitude spectrum, not power spectrum; power would be freq^2
    freq         = np.abs(np.fft.rfft(sigt     ))
    #freq2        = np.abs(np.fft.rfft(sigt2    ))

    if use_window_functions:
        freq_win     = np.abs(np.fft.rfft(sigt_win ))

    # Return the Discrete Fourier Transform sample frequencies
    f = np.fft.rfftfreq(t.size, d = cycletime)
    #print "f:   len:", f.size, "\n", f

    # Return the reciprocal of the argument, element-wise.
    p  = np.reciprocal(f[1:])  # skipping 1st value frequency = 0
    #print "Period: len:", p.size, "\n", p


    asigt = sigt - sigt_mean

    #print "np.mean(sigt) , np.var(sigt) :", np.mean(sigt),  np.var(sigt)
    #print "np.mean(asigt), np.var(asigt):", np.mean(asigt), np.var(asigt)

    asigtnorm = np.var(asigt) * asigt.size  # to normalize autocorrelation

    # Cross-correlation of two 1-dimensional sequences.

    ac = np.correlate(asigt, asigt, mode='full') / asigtnorm
    #print( "ac: len:", ac.size)
    ac = ac[int(ac.size/2):]
    #print( "ac: len:", ac.size)
    #print( "ac:", "\n", ac)


# figure and canvas ###################################################
    figFFT = plt.figure(facecolor = "#C9F9F0", dpi=gglobs.hidpiScaleMPL) # blueish tint
    vprint("plotFFT: open figs count: {}, current fig: #{}".format(len(plt.get_fignums()), plt.gcf().number))

    # canvas - this is the Canvas Widget that displays the `figure`
    # it takes the `figure` instance as a parameter to __init__
    canvas3 = FigureCanvas(figFFT)
    canvas3.setFixedSize(1000, 600)
    navtoolbar = NavigationToolbar(canvas3, gglobs.exgg)


# Data vs Time ################################################################
    plt.subplot(2,2,1)
    plt.title("Time Course", fontsize=12, loc = 'left')
    subTitle = "Recs:" + str(sigt.size)
    plt.title(subTitle, fontsize=10, fontweight='normal', loc = 'right')
    plt.xlabel("Time ({})".format(timeunit), fontsize=12)
    plt.ylabel("Variable  " + yunit, fontsize=12)
    plt.grid(True)
    plt.ticklabel_format(useOffset=False)

    plt.plot(t, sigt        ,  linewidth=0.4, color='red'   , label ="Time Domain" , marker="o", markeredgecolor='red'   , markersize=markersize)
    #plt.plot(t, sigt_win    ,  linewidth=0.4, color='black' , label ="Time Domain" , marker="o", markeredgecolor='black' , markersize=markersize)


    #def format_coord(x, y):
    #    col = int(x + 0.5)
    #    row = int(y + 0.5)
    #    z = 99
    #    return 'aaaaaaaaaaaaaaaaaaa x=%1.4f, y=%1.4f, z=%1.4f' % (x, y, z)

    # hide the cursor position from showing in the Nav toolbar
    #ax1 = plt.gca()
    #ax1.format_coord = lambda x, y: "asasjalksjalsjalskajlakj"
    #ax1.format_coord = format_coord


# Autocorrelation vs Lag #########################################################
    aax1 =  plt.subplot(2,2,3)

    plt.title("Autocorrelation (normalized) vs. Lag Period", fontsize=12, loc = 'left', y = 1.1)
    plt.xlabel("Lag Period ({})".format(timeunit), fontsize=12)
    plt.ylabel("Autocorrelation", fontsize=12)
    plt.grid(True)
    #plt.ticklabel_format(useOffset=False)

    aax2 = aax1.twiny()

    # how many points to show enlarged?
    for i in range(t.size):
        if ac[i] < 0: break

    tindex = min(i, t.size * 0.01)
    tindex = max(25, tindex, 60./(cycletime * 60.))
    tindex = int(tindex)  # Warning: ./geigerlog:3483: VisibleDeprecationWarning: using a non-integer number instead of an integer will result in an error in the future
                          # aax2.plot(tnew[:tindex], ac[:tindex], linewidth= 2.0, color='blue' , label ="Expanded Lag Period - Top Scale" , marker="o", markeredgecolor='blue'  , markersize=markersize*2)
                          # What is the reason ?????
    #print "tindex:", tindex
    #print "type(tindex):", type(tindex)

    tnew = t - t[0]
    aax1.plot(tnew,          ac         , linewidth= 0.4, color='red'  , label ="Full Lag Period - Bottom Scale" , marker="o", markeredgecolor='red'   , markersize=markersize)
    #aax1.legend(loc='upper right', fontsize=12)

    #~aax2.plot(tnew[:tindex], ac[:tindex], linewidth= 2.0, color='blue' , label ="Expanded Lag Period - Top Scale" , marker="o", markeredgecolor='blue'  , markersize=markersize * 2)
    aax2.plot(60 * tnew[:tindex], ac[:tindex], linewidth= 2.0, color='blue' , label ="Expanded Lag Period in sec - Top Scale" , marker="o", markeredgecolor='blue'  , markersize=markersize * 1)
    #print "ac:", ac[:10]

    plt.legend(loc='upper right', fontsize=10)

    for a in aax1.get_xticklabels():
        #a.set_color("red")
        #a.set_weight("bold")
        pass

    for a in aax2.get_xticklabels():
        a.set_color("blue")
#            a.set_weight("bold")



# FFT vs Time #########################################################
    plt.subplot(2,2,2)
    plt.title("FFT Amplitude Spectrum vs. Time Period", fontsize=12, loc = 'left')
    plt.xlabel("Time Period ({})".format(timeunit), fontsize=12)
    plt.ylabel("FFT Amplitude", fontsize=12)
    plt.grid(True)
    plt.ticklabel_format(useOffset=False)

    plt.loglog(p, freq[1:]        , linewidth= 0.4, color='red'   , label ="FFT" , marker="o", markeredgecolor='red'   , markersize=markersize)
    #plt.loglog(p, freq2[1:] -freq[1:]       , linewidth= 0.4, color='black'   , label ="FFT" , marker="o", markeredgecolor='red'   , markersize=markersize)
    #plt.loglog(p, freq_win[1:]    , linewidth= 0.4, color='black' , label ="FFT" , marker="o", markeredgecolor='black' , markersize=markersize)

# FFT vs Frequency ####################################################
    plt.subplot(2,2,4)
    plt.title("FFT Amplitude Spectrum vs. Frequency", fontsize=12, loc = 'left')
    plt.xlabel("Frequency ({})".format(frequencyunit), fontsize=12)
    plt.ylabel("FFT Amplitude", fontsize=12)
    plt.grid(True)
    plt.ticklabel_format(useOffset=False)

    plt.semilogy (f[1:], freq[1:]     , linewidth= 0.4, color='red'   , label ="FFT" , marker="o", markeredgecolor='red'   , markersize=markersize)
    #plt.semilogy (f[1:], freq2[1:] -freq[1:]     , linewidth= 0.4, color='black'   , label ="FFT" , marker="o", markeredgecolor='red'   , markersize=markersize)
    #plt.semilogy (f[1:], freq_win[1:] , linewidth= 0.4, color='black' , label ="FFT" , marker="o", markeredgecolor='black' , markersize=markersize)

    #plt.legend(loc='upper left', fontsize=12)

# arrange sub plots
    plt.subplots_adjust(hspace=0.5, wspace=0.2, left=.08, top=0.95, bottom=0.090, right=.98)

# textboxes ################################################################
    labout_left  = QTextBrowser() # label to hold some data on left side
    labout_left.setFont(gglobs.fontstd)
    labout_left.setLineWrapMode(QTextEdit.NoWrap)
    labout_left.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)
    labout_left.setMinimumHeight(150)

    labout_left.append("{:22s}= {}"                             .format('File'               , DataSrc))
    labout_left.append("{:22s}= {}"                             .format("No of Records"      , t.size))
    labout_left.append("{:22s}= {:4.2f}"                        .format("Count Rate Average" , sigt_mean))
    labout_left.append("{:22s}= {:4.2f} (Std.Dev:{:5.2f}, Std.Err:{:5.2f})"    .format("Count Rate Variance" , sigt_var, sigt_std, sigt_err))
    labout_left.append("{:22s}= {:4.2f} sec (overall average)"  .format("Cycle Time"         , cycletime * 60.)) # t is in minutes
    labout_left.append("{:22s}= {:4.2f} "                       .format("A.corr(lag=  0   sec)", ac[0]))
    labout_left.append("{:22s}= {:4.2f} "                       .format("A.corr(lag={:5.1f} sec)".format(tnew[1] *60.), ac[1]))
    labout_left.append("{:22s}= {:4.2f} "                       .format("A.corr(lag={:5.1f} sec)".format(tnew[2] *60.), ac[2]))

    labout_right  = QTextBrowser() # label to hold some data on right side
    labout_right.setFont(gglobs.fontstd)
    labout_right.setLineWrapMode(QTextEdit.NoWrap)
    labout_right.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)
    labout_right.setMinimumHeight(120)

    fftmax      = np.max    (freq[1:])
    fftmaxindex = np.argmax (freq[1:]) + 1
    f_max       = f         [fftmaxindex ]

    labout_right.append("{:22s}= {:4.0f}"              .format("FFT(f=0)"         , freq[0]) )
    labout_right.append("{:22s}= {:4.2f} (= FFT(f=0)/No of Records)".format("Count Rate Average", freq[0] / len(t)) )
    labout_right.append("{:22s}= {:4.2f}"              .format("Max FFT(f>0)"     , fftmax))
    labout_right.append("{:22s}= {}"                   .format("  @ Index"        , fftmaxindex))
    labout_right.append("{:22s}= {:4.4f}"              .format("  @ Frequency"    , f_max ))
    labout_right.append("{:22s}= {:4.4f}"              .format("  @ Period"       , p[fftmaxindex] ))

# Pop Up  #################################################################
    d       = QDialog()
    d.setWindowIcon(gglobs.iconGeigerLog)
    #d.setFont(gglobs.fontstd)
    d.setWindowTitle("FFT & Autocorrelation" )
    #d.setMinimumHeight(gglobs.window_height)
    d.setWindowModality(Qt.WindowModal)

    bbox    = QDialogButtonBox()
    bbox.setStandardButtons(QDialogButtonBox.Ok)
    bbox.accepted.connect(lambda: d.done(0))

    layoutH   = QHBoxLayout()
    layoutH.addWidget(labout_left)
    layoutH.addWidget(labout_right)


    #~layoutHtb = QHBoxLayout()
    #~layoutHtb.addWidget(bbox)
    #~layoutHtb.addWidget(navtoolbar)
    #~layoutHtb.addStretch()
    #~layoutHtb.addStretch() # strange - one is not enough? on Py3.5
    #~layoutHtb.addStretch() # strange - one is not enough? on Py3.8
    #~layoutHtb.addStretch() # strange - one is not enough? on Py3.8
    #~layoutHtb.addStretch() # strange - one is not enough? on Py3.8


    layoutV   = QVBoxLayout(d)
    #layoutV.addLayout(layoutHtb)
    layoutV.addWidget(navtoolbar)
    layoutV.addWidget(canvas3)
    layoutV.addLayout(layoutH)
    layoutV.addWidget(bbox)

    setNormalCursor()

    figFFT.canvas.draw_idle()
    d.exec()
    plt.close(figFFT)

