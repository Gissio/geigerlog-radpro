#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GLestimate.py - GeigerLog estimating CPM forecast based on CPS data

Start with: GLestimate.py [datarecords [usePredictive [useLimitStats [statlimit]]]]
            datarecords:   >= 240                     default = 1000)
            usePredictive: 0 or 1   (0 = No, 1 = Yes, default = 1)
            useLimitStats: 0 or 1   (0 = No, 1 = Yes, default = 1)
            statlimit:     >= 0                       default = 25)
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

import sys, os
import numpy             as np
import matplotlib.pyplot as plt


def plotDataT(dataX, data, xmin, xmax, ymin, ymax, xlabel):
    """plot data"""

    plt.ylim(ymin, ymax)
    plt.xlim(xmin, xmax)
    plt.plot(dataX, data,  "b", linestyle='solid', linewidth=2.0)
    plt.legend(["CPS= " + str(xlabel) + "\nCPM= " + str(xlabel * 60)])


def main():

    # Set "QT_STYLE_OVERRIDE" to avoid this nuisance message originating
    # from the import of matplotlib:
    #   QApplication: invalid style override 'gtk' passed, ignoring it.
    #   Available styles: Windows, Fusion
    os.environ["QT_STYLE_OVERRIDE"] = ""

    print("-"*200)

    fig = plt.figure("GLestimate", figsize=(18, 11))
    #~fig = plt.figure("GLestimate", figsize=(18, 11), dpi=gglobs.hidpiScaleMPL)

    #~cpsmeans    = [0.3, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000]
    cpsmeans    = [0.3, 1, 3, 10, 100, 10000]
    print("cpsmeans    :", cpsmeans)

    # command line option to set datalen
    # if none given on command line, an exception will set default
    try:    datalen = abs(int(sys.argv[1]))
    except: datalen = 1000
    print("data length :", datalen)

    # command line option to set predictive
    # if none given on command line, an exception will set default
    # True: make est of CPm on first CPS
    try:    predictive = True if (int(sys.argv[2]) != 0) else False
    except: predictive = True
    print("predictive  :", "Yes" if predictive else "No")

    if predictive: ylimit = 500
    else:          ylimit = 250

    # command line option to select min statistic
    # if none given on command line, an exception will set default
    # True: limit to sum of cps > statlimit
    try:    limitstats = True if (int(sys.argv[3]) != 0) else False
    except: limitstats = True
    print("limitstats  :", "Yes" if limitstats else "No")

    # command line option to select min statistic
    # if none given on command line, an exception will set default
    # statlimit   = 25  --> StdDev= 20%
    # statlimit   = 100 --> StdDev= 10%
    try:    statlimit = abs(int(sys.argv[4]))
    except: statlimit = 25
    print("statlimit   :", statlimit, "--> StdDev: {:0.2f}%".format(np.sqrt(statlimit) / statlimit * 100))

    chunk       = 120
    #~chunk       = 300
    walkstep    = 7

    for recno in range(0, len(cpsmeans)):
        #~if recno > 2: break
        cpsmean = cpsmeans[recno]
        data   = np.random.poisson(cpsmean, size=datalen)

        print("\n")
        print("recno       : #{}".format(recno))
        print("Preset CPS  : ", cpsmean)
        print("data [0:10] : ", data[:10])
        print("data Avg    : {:10.4f}".format(np.nanmean(data)))
        print("data Var    : {:10.4f}".format(np.nanvar(data)))
        print("data StdDev : {:10.4f}  (±{:4.1f}%)".format(np.nanstd(data), (100 * (np.nanstd(data))) / cpsmean))
        print("data Min    : {:10.4f}  ({:+5.1f}%)".format(np.nanmin(data), (100 * (np.nanmin(data) - cpsmean)) / cpsmean))
        print("data Max    : {:10.4f}  ({:+5.1f}%)".format(np.nanmax(data), (100 * (np.nanmax(data) - cpsmean)) / cpsmean))

        plt.subplot(2, 3, recno + 1);   # 2 rows with 3 cols each; plots called from 1 ... 6
        plt.tight_layout()              # expand graphs to use all space, leave no white space

        maxY    = -1
        minY    = 9999999
        maxYend = maxY
        minYend = minY
        plots   = 0

        normalizer = 100 / (cpsmean * 60) # 100% / avg(record as CPM)

        for i in range(0, datalen - chunk, walkstep):
            #~if i>30: break
            dataXcum = np.empty([chunk])
            datacum = np.empty([chunk])

            sum = 0
            for k in range(0, 60):
                dataXcum[k] = k

                sum += data[i + k]
                if sum < statlimit and limitstats:
                    #~print("<statlimit @i+k:", i+k)
                    datacum[k] = None
                else:
                    if predictive:  y = sum * normalizer * (60 / (k + 1)) # projecting CPM
                    else:           y = sum * normalizer                  # CPM as measured up to this point
                    #~if recno==0 and k > 57: print("i,k:", i,k, "i+k:", i+k, "data[i + k]:", data[i + k], "sum:", sum, "y:", y)
                    datacum[k] = y

            for k in range(60, chunk):
                dataXcum[k] = k

                if limitstats: allsum = np.nansum(data[i: i + k])
                else:          allsum = statlimit      # simulate
                if allsum < statlimit:
                    #~print("<statlimit @i+k:", i+k, "allsum:", allsum)
                    datacum[k] = None
                else:
                    sum = np.nansum(data[i + k - 60: i + k])
                    y = sum * normalizer
                    #~if recno==0 and k < 62: print("i,k:", i,k, "i+k:", i+k, "data[i + k]:", data[i + k], "sum:", sum, "y:", y)
                    datacum[k] = y

            #~print(dataXcum)
            #~print(datacum)
            lastAll = datacum
            if not np.isnan(lastAll).all():
                minY    = min(minY,     np.nanmin(lastAll))
                maxY    = max(maxY,     np.nanmax(lastAll))

            last10  = datacum[-10:]
            if not np.isnan(last10).all():
                endmean = np.nanmean(last10)
                minYend = min(minYend, endmean)
                maxYend = max(maxYend, endmean)

            plotDataT(dataXcum, datacum, 0, chunk, 0, ylimit, cpsmean)
            plots += 1

        plt.plot([0, chunk], [100, 100], "red") # finally red, horizontal line at y=100 drawn
        plt.plot([0, chunk], [130, 130], color='red', linestyle='dashed') # + 30%
        plt.plot([0, chunk], [ 70,  70], color='red', linestyle='dashed', ) # -30%
        plt.plot([0, chunk], [120, 120], color='red', linestyle='dotted') # + 30%
        plt.plot([0, chunk], [ 80,  80], color='red', linestyle='dotted', ) # -30%

        print("minY        : {:+6.1f}%, maxY   :{:+6.1f}%".format(minY    - 100, maxY    - 100))
        print("minYend     : {:+6.1f}%, maxYend:{:+6.1f}%".format(minYend - 100, maxYend - 100))
        print("plots done  : ", plots)
        plots = 0
        plt.pause(.5)

    print("Done plotting. To Exit close graph, or press CTRL-C in terminal")
    plt.show()


if __name__ == '__main__':
    main()
    print()

