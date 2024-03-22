#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gstat_convfft.py - GeigerLog commands for FFT statistics on convoluted functions

include in programs with:
    import gstat_convfft
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


def convFFT():
    """Plotting FFT and Autocorrelation after connvolution of time functions
    t       = time
    sigt    = Signal in time domain, (CPM/CPS here)
    freq    = Signal in frequency domain

    Has extra function for rectangle and autocorr
    """

    markersize     = 1.0
    rectangle_size = 60     # normally 60 for 60 s = 1 min

    vindex      = gglobs.exgg.select.currentIndex()
    vname       = list(gglobs.varsCopy)[vindex]
    vnameFull   = gglobs.varsCopy[vname][0]
    yunit       = vnameFull
    vprint("plotFFT: vname: '{}', vnameFull: '{}'".format(vname, vnameFull))

    rawt0    = gglobs.logTimeDiffSlice
    rawsigt0 = gglobs.logSliceMod[vname]

    if rawsigt0 is None:
        showStatusMessage("No data available")
        return

    if rawt0.size <= rectangle_size:
        showStatusMessage("Not enough data (need more than {})".format(rectangle_size))
        return

    setBusyCursor()
    DataSrc = os.path.basename(gglobs.currentDBPath)

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

    t    = rawt.copy()
    sigt = rawsigt.copy()

    """Call numpy.isnan(arr) to get a boolean array showing whether or not each
    index in the initial array arr has a value of NaN. Use the ~ operator to
    invert this array so that indices with NaN are now marked as False. Then
    call indexing syntax arr[n_arr] with n_arr as the result of the last step
    to get a new array with all NaNs filtered out."""
    nan_array = np.isnan(sigt)
    not_nan_array = ~ nan_array
    sigt = sigt[not_nan_array]

    if sigt.size == 0:
        gglobs.exgg.showStatusMessage("No data available")
        setNormalCursor()
        return


# Window functions ############################################################
    # the only place to activate Window function is here
    use_window_functions = False

    if use_window_functions:
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

        # Select one
        #win     = hamm
        #win     = hann
        #win     = black
        win     = kaiser

        # When using window functions subtract the average in order to avoid
        # spurious low-frequency peaks!
        sigt   = sigt - np.mean(sigt)

        # Time domain signal with Window function applied
        sigt_win = sigt * win

# Prepare variables ###########################################################

    t               = t * 1440.0  # convert days to minutes
    timeunit        = "minutes"
    frequencyunit   = "1/minute"
    cycletime       = (t[-1] - t[0]) / (t.size -1)  # in minutes

    sigt_mean       = np.mean(sigt)
    sigt_var        = np.var(sigt)
    sigt_std        = np.std(sigt)
    sigt_var        = np.var(sigt)
    sigt_err        = sigt_std / np.sqrt(sigt.size)

    print("t:    size:"       , t.size        , "\n", t[:30])
    print("sigt: size:"       , sigt.size     , "\n", sigt[:30])
    #print("sigt_win: size:"  , sigt_win.size , "\n", sigt_win[:30])

    if t.size < rectangle_size:
        msg = "Not enough data; need {} records as minimum".format(rectangle_size)
        gglobs.exgg.showStatusMessage(msg)
        setNormalCursor()
        return

    maxf = int(sigt.size / 60 * 10) # --> up to 10/min frequency

# figure and canvas ###########################################################
    figEvalFFT = plt.figure(facecolor = "#C9F9F0", dpi=gglobs.hidpiScaleMPL) # blueish tint
    vprint("figEvalFFT: open figs count: {}, current fig: #{}".format(len(plt.get_fignums()), plt.gcf().number))

# arrange sub plots
    plt.subplots_adjust(hspace=0.4, wspace=0.3, left=.04, top=0.93, bottom=0.08, right=.99)

    # canvas - this is the Canvas Widget that displays the `figure`
    # it takes the `figure` instance as a parameter to __init__
    canvas3 = FigureCanvas(figEvalFFT)
    canvas3.setFixedSize(1800, 700)
    navtoolbar = NavigationToolbar(canvas3, None)

# Data vs Time ################################################################
    plt.subplot (2,4,2)
    plt.title   ("Time (Counts)", fontsize=12, loc = 'left')
    subTitle = "Recs:" + str(sigt.size)
    plt.title   (subTitle, fontsize=10, fontweight='normal', loc = 'right')
    plt.xlabel  ("Time ({})".format(timeunit), fontsize=12)
    plt.ylabel  ("Count Rate  " + yunit, fontsize=12)
    plt.grid    (True)
    plt.ticklabel_format(useOffset=False)

    plt.plot    (t, sigt        ,  linewidth=0.4, color='red'   , label ="Time Domain" , marker="o", markeredgecolor='red'   , markersize=markersize)

# Autocorrelation vs Lag ######################################################
    # calculations
    asigt = sigt - sigt_mean
    #print "np.mean(sigt) , np.var(sigt) :", np.mean(sigt),  np.var(sigt)
    #print "np.mean(asigt), np.var(asigt):", np.mean(asigt), np.var(asigt)

    asigtnorm = np.var(asigt) * asigt.size  # to normalize autocorrelation
    ac = np.correlate(asigt, asigt, mode='full') / asigtnorm
    ac = ac[int(ac.size/2):]
    #print "ac: len:", ac.size
    #print "ac:", "\n", ac

    # autocorrelation plot
    aax1 =  plt.subplot(2, 4, 1)

    plt.title   ("Autocorrelation (normalized) vs. Lag Period", fontsize=11, loc = 'left', y = 1.08)
    plt.xlabel  ("Lag Period ({})".format(timeunit), fontsize=12)
    plt.ylabel  ("Autocorrelation", fontsize=12)
    plt.grid    (True)
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

    tnew = t - t[0]
    aax1.plot(tnew,          ac         , linewidth= 1.0, color='red'  , label ="Full Lag Period - Bottom Scale" , marker="o", markeredgecolor='red'   , markersize=markersize * 1)
    #aax1.legend(loc='upper right', fontsize=12)

    aax2.plot(60*tnew[:tindex], ac[:tindex], linewidth= 2.0, color='blue' , label ="Expanded Lag Period in sec - Top Scale" , marker="D", markeredgecolor='blue'  , markersize=markersize * 1)
    #print "ac:", ac[:10]

    plt.legend(loc='upper right', fontsize=8) # larger does not fit

    for a in aax1.get_xticklabels():
        #a.set_color("red")
        #a.set_weight("bold")
        pass

    for a in aax2.get_xticklabels():
        a.set_color("blue")
        #~a.set_weight("bold")

# FFT plots ###################################################################
    # calculations
    # using amplitude spectrum, not power spectrum; power would be freq^2
    freq                = np.abs(np.fft.rfft(sigt     ))
    #freq2              = np.abs(np.fft.rfft(sigt2    ))
    print("freq:"       , len(freq)     , "\n", freq[0:25])

    if use_window_functions:
        freq_win        = np.abs(np.fft.rfft(sigt_win))
        print("freq_win:"   , len(freq_win) , "\n", freq_win[0:25])

    f = np.fft.rfftfreq(t.size, d = cycletime)
    print("f:   len:", f.size, "\n", f[0:25])

    p  = np.reciprocal(f[1:])  # skipping 1st value frequency = 0
    print("Period: len:", p.size, "\n", p[0:25])


    # Plot FFT vs Time #########################################################
    plt.subplot(2, 4, 5)
    plt.title("FFT (Counts)", fontsize=12, loc = 'left')
    subTitle = "Recs:" + str(freq.size)
    plt.title   (subTitle, fontsize=10, fontweight='normal', loc = 'right')
    plt.xlabel("Time Period ({})".format(timeunit), fontsize=12)
    plt.ylabel("FFT Amplitude", fontsize=12)
    plt.grid(True)
    plt.ticklabel_format(useOffset=False)

    plt.loglog(p, freq[1:]        , linewidth= 0.4, color='red'   , label ="FFT" , marker="o", markeredgecolor='red'   , markersize=markersize)

    # Plot FFT vs Frequency ####################################################
    plt.subplot(2, 4, 6)
    plt.title("FFT (Counts)", fontsize=12, loc = 'left')
    subTitle = "Recs:" + str(freq.size)
    plt.title   (subTitle, fontsize=10, fontweight='normal', loc = 'right')
    plt.xlabel("Frequency ({})".format(frequencyunit), fontsize=12)
    plt.ylabel("FFT Amplitude", fontsize=12)
    plt.grid(True)
    plt.ticklabel_format(useOffset=False)

    #~plt.semilogy (f[1:], freq[1:]     , linewidth= 0.4, color='red'   , label ="FFT" , marker="o", markeredgecolor='red'   , markersize=markersize)
    plt.semilogy (f[1:maxf], freq[1:maxf]     , linewidth= 0.4, color='red'   , label ="FFT" , marker="o", markeredgecolor='red'   , markersize=markersize)


# convolution plots ###########################################################

    # rect for convolution
    nr = rectangle_size # nr values of 1, followed by zeros

    rect = np.zeros(sigt.size)
    for i in range(nr): rect[i] = 1
    print("rect:", len(rect), ", Values:\n0:10: ", rect[0:10], "\n50:70:", rect[50:70])

    # time axis
    #~bf = t[:rect.size]


# Plot Rectangle Signal vs time ###############################################
    plt.subplot (2, 4, 3)
    plt.title   ("Time (Rectangle)", fontsize=12, loc = 'left')
    subTitle = "Recs:" + str(rect.size)
    plt.title   (subTitle, fontsize=10, fontweight='normal', loc = 'right')
    plt.xlabel  ("Time ({})".format(timeunit), fontsize=12)
    plt.ylabel  ("Signal Value", fontsize=12)
    plt.grid    (True)
    plt.ticklabel_format(useOffset=False)
    #~plt.plot (bf, rect     , linewidth= 1.0, color='red'   , label ="FFT" , marker="o", markeredgecolor='red'   , markersize=markersize)
    plt.plot (t[:rect.size], rect     , linewidth= 1.0, color='red'   , label ="FFT" , marker="o", markeredgecolor='red'   , markersize=markersize)


# FFT of Signal vs Frequency ##################################################

    cfreq = np.abs(np.fft.rfft(rect     ))
    print("cfreq:   len:", cfreq.size, "\n", cfreq[0:25])

    f = np.fft.rfftfreq(t.size, d = cycletime)
    print("f:   len:", f.size, "\n", f[0:25])

    p  = np.reciprocal(f[1:])  # skipping 1st value frequency = 0
    print("Period: len:", p.size, "\n", p[0:25])

    plt.subplot (2, 4, 7)
    plt.title   ("FFT (Rectangle)", fontsize=12, loc = 'left')
    subTitle = "Recs:" + str(cfreq.size)
    plt.title   (subTitle, fontsize=10, fontweight='normal', loc = 'right')
    plt.xlabel  ("Frequency ({})".format(frequencyunit), fontsize=12)
    plt.ylabel  ("FFT Amplitude", fontsize=12)
    plt.grid    (True)
    plt.ticklabel_format(useOffset=False)

    #~plt.semilogy (f[1:], cfreq[1:]     , linewidth= 0.4, color='red'   , label ="FFT" , marker="o", markeredgecolor='red'   , markersize=markersize)
    plt.semilogy (f[1:maxf], cfreq[1:maxf]     , linewidth= 0.4, color='red'   , label ="FFT" , marker="o", markeredgecolor='red'   , markersize=markersize)


# last columns (convolution columns) ##########################################
    # upper

    csigt = scipy.signal.convolve(rect, sigt ) * (60 / nr)
    csigt = csigt[nr:len(sigt) + nr]
    print("csigt:", len(csigt), csigt[:30])

    plt.subplot (2, 4, 4)
    plt.title   ("Time (Counts && Rectangle)", fontsize=12, loc = 'left')
    subTitle = "Recs:" + str(csigt.size)
    plt.title   (subTitle, fontsize=10, fontweight='normal', loc = 'right')

    plt.xlabel  ("Time ({})".format(timeunit), fontsize=12)
    plt.ylabel  ("Count Rate CPM", fontsize=12)
    plt.grid    (True)
    plt.ticklabel_format(useOffset=False)

    plt.plot (t[:-nr], csigt[:-nr]     , linewidth= 0.4, color='red'   , label ="FFT" , marker="o", markeredgecolor='red'   , markersize=markersize)

    # lower
    ccfreq = cfreq * freq

    plt.subplot (2, 4, 8)
    plt.title   ("FFT (Counts && Rectangle)", fontsize=12, loc = 'left')
    subTitle = "Recs:" + str(cfreq.size)
    plt.title   (subTitle, fontsize=10, fontweight='normal', loc = 'right')
    plt.xlabel  ("Frequency ({})".format(frequencyunit), fontsize=12)
    plt.ylabel  ("FFT Amplitude", fontsize=12)
    plt.grid    (True)
    plt.ticklabel_format(useOffset=False)

    #~plt.semilogy (f[1:], ccfreq[1:]     , linewidth= 0.4, color='red'   , label ="FFT" , marker="o", markeredgecolor='red'   , markersize=markersize)
    plt.semilogy (f[1:maxf], ccfreq[1:maxf]     , linewidth= 0.4, color='red'   , label ="FFT" , marker="o", markeredgecolor='red'   , markersize=markersize)


# textboxes ###################################################################
    labout_left  = QTextBrowser() # label to hold some data on left side
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
    labout_left.append("{:22s}= {:4.2f} "                       .format("A.corr(lag={:5.1f} sec)".format(tnew[3] *60.), ac[3]))

    labout_right  = QTextBrowser() # label to hold some data on right side
    labout_right.setLineWrapMode(QTextEdit.NoWrap)
    labout_right.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)
    labout_right.setMinimumHeight(120)

    fftmax      = np.max    (freq[1:])
    fftmaxindex = np.argmax (freq[1:]) + 1
    f_max       = f         [fftmaxindex ]

    labout_right.append("{:22s}: {:s}"                 .format("Legend", "'Counts && Rectangle' means: 'Counts convolved with Rectangle'\n"))
    labout_right.append("{:22s}= {:4.0f}"              .format("FFT(f=0)"         , freq[0]) )
    labout_right.append("{:22s}= {:4.0f}"              .format("len(t)"           , len(t)) )
    labout_right.append("{:22s}= {:4.2f} (= FFT(f=0)/No of Records)".format("Count Rate Average", freq[0] / len(t)) )
    labout_right.append("{:22s}= {:4.2f}"              .format("Max FFT(f>0)"     , fftmax))
    labout_right.append("{:22s}= {}"                   .format("  @ Index"        , fftmaxindex))
    labout_right.append("{:22s}= {:4.4f}"              .format("  @ Frequency"    , f_max ))
    try:
        labout_right.append("{:22s}= {:4.4f}"          .format("  @ Period"       , p[fftmaxindex] ))
    except:
        labout_right.append("{:22s}= {:s}"             .format("  @ Period"       , "undefined" ))


# Pop Up  #################################################################
    d       = QDialog()
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setFont(gglobs.fontstd)
    d.setWindowTitle("FFT & Autocorrelation")
    #d.setMinimumHeight(gglobs.window_height)
    d.setWindowModality(Qt.WindowModal)

    bbox    = QDialogButtonBox()
    bbox.setStandardButtons(QDialogButtonBox.Ok)
    bbox.accepted.connect(lambda: d.done(0))

    layoutH   = QHBoxLayout()
    layoutH.addWidget(labout_left)
    layoutH.addWidget(labout_right)

    layoutV   = QVBoxLayout(d)
    layoutV.addWidget(navtoolbar)
    layoutV.addWidget(canvas3)
    layoutV.addLayout(layoutH)
    layoutV.addWidget(bbox)

    figEvalFFT.canvas.draw_idle()
    d.exec()
    plt.close(figEvalFFT)
