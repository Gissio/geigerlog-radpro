#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gstat_poisson.py - GeigerLog commands for poisson statistics

include in programs with:
    import gstat_poisson
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


def plotPoisson():
    """Plotting a Poisson Fit to a histogram of the data"""

    setBusyCursor()

    vindex      = gglobs.exgg.select.currentIndex()
    vname       = list(gglobs.varsCopy)[vindex]
    vnameFull   = gglobs.varsCopy[vname][0]

    if gglobs.logTimeDiffSlice is None:
        gglobs.exgg.showStatusMessage("No data available")
        setNormalCursor()
        return

    try:
        t0 = gglobs.logTimeDiffSlice
        x0 = gglobs.logSliceMod[vname]
    except Exception as e:
        gglobs.exgg.showStatusMessage("No data available")
        setNormalCursor()
        return
    #print("t0, x0: len:", len(t0), len(x0))

    fncname = "plotPoisson: "
    vprint(fncname + "Plotting Histogram and Poisson Fit")
    setIndent(1)

    # elimitate all nan data in x (t will always exist)
    counter_isnan = 0
    t = np.ndarray(0)
    x = np.ndarray(0)
    for i in range(0,len(t0)):
        #print("i, x0[i]:", i, x0[i])
        if np.isnan(x0[i]):
            counter_isnan += 1
            pass
        else:
            t = np.append(t, t0[i])
            x = np.append(x, x0[i])
    #~print("len(t0), len(x0), len(t), len(x): ", len(t0), len(x0), len(t), len(x))
    #~if counter_isnan > 0:   print("Found nan, count:", counter_isnan)
    #~else:                   print("Found no nan")

    if t.size == 0:
        gglobs.exgg.showStatusMessage("No data available")
        setNormalCursor()
        setIndent(0)
        return

    DataSrc     = os.path.basename(gglobs.currentDBPath)
    cycletime   = (t[-1] - t[0]) / (t.size - 1)  # in minutes
    yunit       = vnameFull

    ######################################
    # to show histogram of delta between 2 consecutive counts
    if 0:       # do not execute on 0
        dx = x[:-1].copy()
        for i in range(0, len(dx)):
            dx[i] = abs(x[i+1] - x[i])
            #if dx[i] > 10: print i, dx[i]
        #print x, len(x)
        #print dx, len(dx)
        x = dx
        yunit = "Differences between 2 consecutive CPM!"
    #######################################


    lenx        = len(x)
    sumx        = np.nansum (x)         # nan...: all values excluding NANs!
    avgx        = np.nanmean(x)         # though there shouldn't be any, as they
    varx        = np.nanvar (x)         # are eliminated above
    stdx        = np.nanstd (x)         # But it does not hurt
    minx        = np.nanmin (x)
    maxx        = np.nanmax (x)
    if avgx >= 0:
        std95   = np.sqrt(avgx) * 1.96  # +/- std95 is range for 95% of all values
    else:
        std95   = gglobs.NAN

    if avgx == 0:
        gglobs.exgg.showStatusMessage("All Variable data are zero; cannot calculate Poisson distribution!")
        setIndent(0)
        setNormalCursor()
        return


    cdprint(fncname + "count data: lenx:{}, sumx:{:5.0f}, avgx:{:5.3f}, varx:{:5.3f}, stdx:{:5.3f}, minx:{:5.3f}, maxx:{:5.3f}, std95%:{:5.3f}\n{}\n".\
                format(lenx,   sumx,         avgx,          varx,         stdx,         minx,         maxx,         std95,           x))

    # take the lower of (the lowest count rate) and (the average minus 2 StdDev), but must be at least zero
    bin_center_min    = int(max(0,    min(minx , avgx - (std95 * 2))))

    # take the higher of (the highest count rate) and (the average plus 2 StdDev) and 16
    bin_center_max    = int(max(16, maxx , avgx + (std95 * 2)))

    # limit the total no of bins to 30 by making the bins wider, but keep width at least at 1
    step              = int(max(1, int((bin_center_max - bin_center_min) / 30)))
    bin_total         = int((bin_center_max - bin_center_min) / step) + 1
    #print("  step: {}, bin_center_min: {}, bin_center_max: {}, bin_total: {}".format(step, bin_center_min, bin_center_max, bin_total))

    bins    = np.empty(bin_total + 1)
    bins[0] = int(bin_center_min)
    for i in range(1, bin_total + 1):
        bins[i] = int(bins[i - 1] + step)
    #print("bins: len(): ", len(bins), bins)


    # CREATE histogram
    # https://numpy.org/devdocs/reference/generated/numpy.histogram.html
    # If bins is an int, it defines the number of equal-width bins in the given
    # range (10, by default).If bins is a sequence, it defines the bin edges,
    # including the rightmost edge, allowing for non-uniform bin widths.
    # If bins is a string, it defines the method used to calculate the optimal
    # bin width, as defined by histogram_bins.
    # hist, bins = np.histogram(x, bins='auto') # gives bins as rational numbers
    # hist, bins = np.histogram(x, bins='sqrt') # used in Excel; bins as rational numbers
    #
    # returns: The values of the histogram. See density and weights for a
    #          description of the possible semantics.
    #          bins : array of dtype float. Return the bin edges (length(hist)+1).

    # Here using manually created histogram, as otherwise a synthetic normal distribution
    # would not properly sum up
    hist = np.empty( len(bins) - 1 )
    for i in range(0, len(bins) - 1):
        stepsum = 0
        ll0 = bins[i ]
        hl0 = bins[i + 1]
        dl0 = hl0 - ll0
        for j in range(0, step):
            ll = ll0 - (dl0 / 2 / step) + dl0 /step * j
            hl = ll + dl0 / step
            stepsum += len( x[((x>=ll) & (x<hl))] )
            #print("i, j, ll0, hl0,  ll, hl, stepsum: ", i, j, ll0, hl0, ll, hl, stepsum)
        hist[i] = stepsum
    #print( "manual histogram: len(hist):", len(hist), "\n", hist)



    # sum up the Poisson dist for the bins from above histogram
    pdfs = []
    for i in range(int(bins[0]), int(bins[-1]), int(step)):
        stepsum = 0
        for j in range(0, step):
            stepsum += scipy.stats.poisson.pmf(i + j, avgx)
        pdfs.append(stepsum * lenx)

    #print("----------------avgx = ", avgx)
    pdfnorm = []
    for i in range(int(bins[0]), int(bins[-1]), int(step)):
        stepsum = 0
        for j in range(0, step):
            if avgx >= 0:
                stepsum += scipy.stats.norm.pdf(i + j , avgx, scale=np.sqrt(avgx))
            else:
                stepsum += scipy.stats.norm.pdf(i + j , avgx, scale=gglobs.NAN)
        pdfnorm.append(stepsum * lenx)

    # determine r-squared for Poisson
    ss_res = np.sum((hist - pdfs    ) ** 2)         # residual sum of squares
    ss_tot = np.sum((hist - np.mean(hist)) ** 2)    # total sum of squares
    r2 = 1 - (ss_res / ss_tot)                      # r-squared for poisson

    # determine r-squared for Normal
    ss_res = np.sum((hist - pdfnorm    ) ** 2)      # residual sum of squares
    ss_tot = np.sum((hist - np.mean(hist)) ** 2)    # total sum of squares
    r2N = 1 - (ss_res / ss_tot)                     # r-squared for normal



# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# chi squared stuff  ----------------------------------------------------------
# since 22.Juli 2021 I noticed this error coming up in all data files, even synthetic data:
# Chi-squared Test Poisson: Exception: For each axis slice, the sum of the observed frequencies
# must agree with the sum of the expected frequencies to a relative tolerance of 1e-08, but
# the percent differences are: 1.3829332101245581e-05
# conclusion: some change in the scipy lib!
#             --> remove the whole chi-square calculation
#                 remove also Kolmogorov-Smirnoffcalculation

    #~obs     = hist
    #~exp     = pdfs
    #~mini    = 0
    #~maxi    = len(obs)

    #~# find where obs and exp are both > 5
    #~# first the left side
    #~for i in range(len(obs)):
        #~#print("Left:   i={}, obs={:9.0f}, exp={:9.2f}".format(i, obs[i], exp[i] ))
        #~if obs[i] >=5 and exp[i] >= 5:
            #~#print("mini--> i={}, obs= {}, exp={}".format(i, obs[i], exp[i]))
            #~mini = i
            #~break

    #~# now the right side
    #~for i in range(mini, len(obs) ):
        #~#print("Right: i={}, obs={:9.0f}, exp={:9.2f}".format(i, obs[i], exp[i] ))
        #~if obs[i] <= 5 or exp[i] <= 5:
            #~#print("maxi--> i={}, obs= {}, exp={}".format(i, obs[i], exp[i]))
            #~maxi = i
            #~break

    #~# the ignored values on the right side
    #~for i in range(maxi, len(obs) ):
        #~pass
        #~#print("Rest:  i={}, obs={:9.0f}, exp={:9.2f}".format(i, obs[i], exp[i] ))

    #~wprint(fncname + "mini:{}, maxi:{}, diff:{}".format(mini, maxi, maxi - mini))



# calc chi2 manually
    #obs_mima = obs[mini:maxi] # cut out the part where obs and exp are both > 5
    #exp_mima = exp[mini:maxi]
    #
    #sumchi2 = 0
    #for i in range(0, len(obs_mima)):
    #    v = (obs_mima[i] - exp_mima[i])**2/exp_mima[i]
    #    sumchi2 += v
    #    print("i={:4d}, obs={:11.4f}, exp={:11.4f}, obs-exp={:11.4f}, chi2={:11.4f}, sumchi2={:11.4f}".format(i, obs_mima[i], exp_mima[i], obs_mima[i] - exp_mima[i], v, sumchi2))

#testing full Hist, not selected for > 5
    # calc chi2 for Poisson
    #ddofPoiss               = 1
    #dofPoiss                = len(hist) - ddofPoiss
    #chi2Poiss, pchi2Poiss   = scipy.stats.chisquare(hist, f_exp=pdfs,    ddof=ddofPoiss, axis=None)
    #txtChi2Poiss            = "Chi-squared Test Poisson <5:  DoF= {:1d}, chi² = {:5.1f}, p0= {:2.1%}".format(dofPoiss, chi2Poiss, pchi2Poiss)
    #vprint(fncname + txtChi2Poiss)


    # Degrees of Freedom
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chisquare.html
    #   "ddofint, optional:
    #   Delta degrees of freedom”: adjustment to the degrees of freedom for the
    #   p-value. The p-value is computed using a chi-squared distribution with
    #   k - 1 - ddof degrees of freedom, where k is the number of observed
    #   frequencies. The default value of ddof is 0."
    #
    # assumption: for Poisson take 1 extra dof off ddof= 1 (estimate average from data)
    #             for Normal  take 2 extra dof off ddof= 2 (estimate average + StdDev from data)
    #

    #~# calc chi2 for Poisson
    #~try:
        #~ddofPoiss               = 1
        #~dofPoiss                = len(hist[mini:maxi]) - ddofPoiss
        #~chi2Poiss, pchi2Poiss   = scipy.stats.chisquare(hist[mini:maxi], f_exp=pdfs[mini:maxi],    ddof=ddofPoiss, axis=None)
        #~# testing same fucntion gives p=100%
        #~#chi2Poiss, pchi2Poiss   = scipy.stats.chisquare(pdfs[mini:maxi], f_exp=pdfs[mini:maxi],    ddof=ddofPoiss, axis=None)
        #~txtChi2Poiss            = "Chi-squared Test Poisson:  DoF = {:1d}, chi² = {:5.1f}, p = {:2.1%}".format(dofPoiss, chi2Poiss, pchi2Poiss)
    #~except Exception as e:
        #~dprint("Chi-squared Test Poisson: Exception: ", e)
        #~txtChi2Poiss            = "Chi-squared Test Poisson:  cannot be calculated!"
    #~vprint(fncname + txtChi2Poiss)

    #~# calc chi2 for Normal
    #~try:
        #~ddofNorm                = 2
        #~dofNorm                 = len(hist[mini:maxi]) - ddofNorm
        #~chi2Norm, pchi2Norm     = scipy.stats.chisquare(hist[mini:maxi], f_exp=pdfnorm[mini:maxi], ddof=ddofNorm, axis=None)
        #~# testing same fucntion gives p=100%
        #~#chi2Norm, pchi2Norm     = scipy.stats.chisquare(pdfnorm[mini:maxi], f_exp=pdfnorm[mini:maxi], ddof=ddofNorm, axis=None)
        #~txtChi2Norm             = "Chi-squared Test Normal :  DoF = {:1d}, chi² = {:5.1f}, p = {:2.1%}".format(dofNorm, chi2Norm, pchi2Norm)
    #~except Exception as e:
        #~dprint("Chi-squared Test Normal: Exception: ", e)
        #~txtChi2Norm             = "Chi-squared Test Normal:  cannot be calculated!"
    #~vprint(fncname + txtChi2Norm)

# END chi squared stuff  ------------------------------------------------------
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# code inactivated for same reason as chi-squared stuff above
#~# Kolmogorov-Smirnoff stuff ---------------------------------------------------
    #~#print("avgx: ", avgx)
    #~obs     = hist
    #~exp     = pdfs
    #~#print("blue values:\n", obs)
    #~#print("red  values:\n", exp)

    #~#print(scipy.stats.kstest(exp,'poisson', args=(20,), alternative='less'))

    #~ks_stats_p, ks_pval_p = scipy.stats.kstest(x, 'poisson', args=(avgx,))
    #~ks_stats_n, ks_pval_n = scipy.stats.kstest(x, 'norm'   , args=(avgx,))
    #~#print("========================= x_norm    : avg:", avgx, ks_stats_n, ks_pval_n)
    #~#print("========================= x_pois    : avg:", avgx, ks_stats_p, ks_pval_p)

    #~obs_cum  = np.empty_like(obs)
    #~exp_cum  = np.empty_like(exp)

    #~for i in range(0, len(obs) +1):
        #~obs_cum = np.cumsum(obs[0:i])
        #~exp_cum = np.cumsum(exp[0:i])

    #~#print("obs_cum: \n", obs_cum)
    #~#print("exp_cum: \n", exp_cum)

    #~#diff  = np.empty_like(obs)
    #~#for i in range(0, len(obs)):
    #~#    diff[i] = obs_cum[i] - exp_cum[i]
    #~#print("diff: \n", diff)
    #~#print("diff: \n", np.absolute(diff))

    #~#diffmax = np.max(np.absolute(diff))
    #~#print("diffmax: ", diffmax)

#~# END   Kolmogorov-Smirnoff stuff ---------------------------------------------
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


    fig2 = plt.figure(facecolor = "#E7F9C9", dpi=gglobs.hidpiScaleMPL)
    vprint("plotPoisson: open figs count: {}, current fig: #{}".format(len(plt.get_fignums()), plt.gcf().number))

    plt.suptitle("Histogram with Poisson Fit", fontsize=12 )
    RsubTitle = DataSrc + "  Recs:" + str(x.size)
    plt.title(RsubTitle, fontsize=10, fontweight='normal', loc = 'right')
    plt.xlabel("Variable {}".format(yunit), fontsize=12)
    plt.ylabel("Frequency of Occurence", fontsize=12)
    plt.grid(True)
    plt.subplots_adjust(hspace=None, wspace=.2 , left=.17, top=0.85, bottom=0.15, right=.97)
    plt.ticklabel_format(useOffset=False)

    # canvas - this is the Canvas Widget that displays the `figure`
    # it takes the `figure` instance as a parameter to __init__
    canvas2 = FigureCanvas(fig2)
    canvas2.setFixedSize(520, 400)


    # plot histogram and other curves #########################################

    # histogram
    plt.bar(bins[:-1],  hist,        color="cornflowerblue", align='center', width=step * 0.85,   label ="avg = {:0.2f}\nvar = {:0.2f}".format(avgx, varx))

    # Poisson curve
    plt.plot(bins[:-1], pdfs,        color='red',         linewidth=3,                        label ="r2  = {:0.3f}".format(r2))

    # Poisson curve residuals
    plt.plot(bins[:-1], hist - pdfs, color='orangered',   linewidth=1, marker='o', markersize=3, label="Residuals")

    if gglobs.stattest:
        # Normal curve
        plt.plot(bins[:-1], pdfnorm,        color='black', linewidth=1,                            label ="N r2 = {:0.3f}".format(r2N))

        # Normal curve residuals
        plt.plot(bins[:-1], hist - pdfnorm, color='0.3',   linewidth=1, marker='s', markersize=3,  label="N Residuals")

    # best place for Legend found with "best"!
    plt.legend(loc="best", fontsize=12, prop={"family":"monospace"})

    ###########################################################################

    labout = QTextBrowser()
    labout.setFont(gglobs.fontstd)
    labout.setLineWrapMode(QTextEdit.NoWrap)
    labout.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)
    labout.setMinimumHeight(330)

    labout.append("Countrates per Histogram Bin: {}".format(step))
    labout.append("Bin   Count Rate    Frequency    % of   Poisson-Fit    Residuals")
    labout.append("No.                (blue col)   Total    (red line) (Freq - Fit)")
    for i in range(0, len(hist)):
        labout.append("{:3d}   {:10.0f}   {:10.0f}  {:5.2f}%    {:10.1f}   {:+10.1f}".format(i + 1, bins[i], hist[i], hist[i]*100 / lenx, pdfs[i], hist[i] - pdfs[i]))
    labout.append("Total count=       {:10.0f} 100.00%    {:10.1f}   {:+10.1f}".format(sum(hist), sum(pdfs), sum(hist - pdfs)))
    labout.append("\nGoodness of Fit Poisson :  r²  = {:5.3f}".format(r2))

    # chi stuff all removed, see above
    #labout.append(txtChi2Poiss)

    if gglobs.stattest:
        # Normal statistics r-squared
        labout.append("Goodness of Fit Normal  :  r²  = {:5.3f}".format(r2N))
        # chi stuff all removed, see above
        #~labout.append(txtChi2Norm)

#    labout.append("Kolmogorov-Smirnow Poisson Test: ")
#    labout.append("Poisson :  statistic = {:5.3f}, pvalue= {:2.3%}".format(ks_stats_p, ks_pval_p))
#    labout.append("Normal  :  statistic = {:5.3f}, pvalue= {:2.3%}".format(ks_stats_n, ks_pval_n))


# Assemble Data set statistics
    labout.append("\nData Set:")
    labout.append("File      = {}"     .format(gglobs.currentDBPath))
    labout.append("Records   = {:8.0f}".format(x.size))
    labout.append("Cycletime = {:8.2f} sec (overall average)".format(cycletime * 86400))
    labout.append("Average   = {:8.2f}".format(avgx))
    labout.append("Variance  = {:8.2f} same as Average if true Poisson Distribution".format(varx))
    labout.append("Std.Dev.  = {:8.2f}".format(stdx))
    if avgx >= 0:   mysqrt = np.sqrt(avgx)
    else:           mysqrt = gglobs.NAN
    labout.append("Sqrt(Avg) = {:8.2f} same as Std.Dev. if true Poisson Distribution".format(mysqrt))
    labout.append("Std.Err.  = {:8.2f}".format(stdx / np.sqrt(x.size)))
    labout.append("Skewness  = {:8.2f} 0:Norm.Dist.; skewed to: +:right   -:left".format(scipy.stats.skew    (x) ))
    labout.append("Kurtosis  = {:8.2f} 0:Norm.Dist.; shape is:  +:pointy: -:flat".format(scipy.stats.kurtosis(x) ))
    labout.append("")

    d = QDialog()
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setWindowTitle("Poisson Test")
    d.setWindowModality(Qt.WindowModal)
    d.setMaximumWidth(520)

    navtoolbar = NavigationToolbar(canvas2, d) # choice of parent does not matter?

    # show the cursor x, y position in the Nav toolbar
    ax1 = plt.gca()
    ax1.format_coord = lambda x,y: "x={:.1f}, y={:.1f}".format(x, y)

    bbox    = QDialogButtonBox()
    bbox.setStandardButtons(QDialogButtonBox.Ok)
    bbox.accepted.connect(lambda: d.done(0))

    layoutV   = QVBoxLayout(d)
    layoutV.addWidget(navtoolbar)
    layoutV.addWidget(canvas2)
    layoutV.addWidget(labout)
    layoutV.addWidget(bbox)

    setNormalCursor()

# show window
    fig2.canvas.draw_idle()
    setIndent(0)
    d.exec()
    plt.close(fig2)

