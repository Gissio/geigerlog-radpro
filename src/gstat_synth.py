#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
gstat_synth.py - GeigerLog tools for the generation of synthetic data

include in programs with:
    include gstat_synth
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



def createSyntheticData():
    """Create synthetic data and save in log format. All times in SECONDS"""

    def shd(d):
        return " ".join("%0.2f" % e for e in d)

    fncname = "createSyntheticData: "

    default_meanlist    = (0.3, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000)
    records             = 100000
    mean                = 30
    cycletime           = 1.0       # in seconds

    # Dialog to input single mean value, or input 0 to use default list
    mean, okPressed = QInputDialog.getDouble(None, "Create Synthetic Log","CPS Mean: Enter desired mean value, or 0 to use this default list for CPS mean:\n{}".format(default_meanlist), 20, min=0, max=1000000, decimals=2)
    # gdprint("mean", mean)
    if okPressed:
        if mean > 0:    meanlist = (mean,)
        else:           meanlist = default_meanlist
    else:
        return

    setBusyCursor()

    # fprint(header("Create Synthetic Log CSV file"), debug=True)
    # fprint("Create logs for mean(s):", "{}\n".format(shd(meanlist)), debug=True)
    msg1 = header("Create Synthetic Log CSV file")
    msg2 = "Create logs for mean(s):", "{}\n".format(shd(meanlist))
    fprint(msg1)
    fprint(msg2)
    dprint(msg1)
    dprint(msg2)

    QtUpdate() # needed to show fprints

    for mean in meanlist:
    # get time
        t = np.float64(np.array(list(range(0, records)))) * cycletime
        dprint(fncname + "get time: size: {}, Delta_t: {} sec".format(t.size, (t[1] - t[0])))
        dprint(fncname + "time data: ", np.int_(t))

        # convert time in sec to datetime strings
        strt0 = "2021-01-01 00:00:00"          # nominal default start datetime
        t0    = mpld.datestr2num(strt0)        # time zero
        td    = np.empty(records, dtype='U19') # holds strings of max length 19
        #print("td, len:", td.size, td)
        for i in range(records):
            td[i] = mpld.num2date(t0 + t[i] / 86400.) # clipped after 19 chars by U19 def

        dprint(fncname + "First 3 DateTimes:", td[:3])
        dprint(fncname + "Last  3 DateTimes:", td[-3:])


    # get data - select the distribution you want
        stddev      = np.sqrt(mean)

        # sigt, DataSrc     = getDeltaTimePoisson(records, mean)
        sigt, DataSrc     = getWhiteNoisePoisson(records, mean)                             # White Noise from Poisson Distribution
        #sigt, DataSrc    = getWhiteNoiseNormal(records, mean, stddev)                      # White Noise from Normal Distribution
        #sigt, DataSrc    = getSinus(records, t)                                            # Sine (one or more)
        #sigt, DataSrc    = getWhiteNoiseSine(records, t)                                   # White Noise with Sine
        #sigt, DataSrc    = getConstantData(records, t)                                     # constant + breaks
        #sigt, DataSrc    = getAutocorr(records)                                            # Autocorr as time function
        #sigt, DataSrc    = getRectangle(records)                                           # Rectangle of 20 samples @ 3sec = 1min
        #sigt, DataSrc    = getWhiteNoisePoissonAutocorr(records, mean, cycletime)          # Autocorrelated Poisson Noise !! perhaps problem
        #sigt, DataSrc    = getRandomData(records, mean, stddev)                            # Radom Data

        # Mean=17, followed by mean=29
        #~sigt1, DataSrc     = getWhiteNoisePoisson(int(records / 2), mean=17)                    # White Noise from Poisson Distribution
        #~sigt2, DataSrc2    = getWhiteNoisePoisson(int(records / 2), mean=29)                    # White Noise from Poisson Distribution
        #~sigt = np.concatenate((sigt1 , sigt2))
        #~print("len(sigt):", len(sigt))
        #~DataSrc = "WhiteNoisePoisson,mean=17&29CPM"

        # Mean=17, added to mean=29
        #~sigt1, DataSrc     = getWhiteNoisePoisson(int(records), mean=17)                    # White Noise from Poisson Distribution
        #~sigt2, DataSrc2    = getWhiteNoisePoisson(int(records), mean=29)                    # White Noise from Poisson Distribution
        #~sigt = sigt1 + sigt2
        #~print("len(sigt):", len(sigt))
        #~DataSrc = "WhiteNoisePoisson,mean=17+29CPM"


    # write to log file
        path = os.path.join(gglobs.dataPath, DataSrc + ".csv")
        writeFileW(path, "", linefeed = True)
        writeFileA(path, "#HEADER ," + strt0 + ", SYNTHETIC data: " + DataSrc)
        writeFileA(path, "#LOGGING," + strt0 + ", Start @Cycle {} sec, device 'SYNTHETIC'".format(cycletime))
        nsigt = np.array(sigt)
        maxprints = 10
        for i in range(records):
            dt          = td[i]     # DateTime
            cps         = nsigt[i]
            cpm         = int(np.nansum(nsigt[max(0, i - 60): i]))
            writestring = " {:7d},{:19s}, {:}, {:}".format(i, dt, cpm, cps)
            writeFileA(path, writestring)
            if i < maxprints or i >= (records - maxprints): print(writestring)

        # fprint("Saved to file: {}\n".format(path), debug=True)
        msg = "Saved to file: {}\n".format(path)
        fprint(msg)
        dprint(msg)

    setNormalCursor()


def getDeltaTimePoisson(records, mean):
    """The length of the intervall of two successive Poisson events
    mean:   in CPS
    return: distribution with times in µs
    """

    fncname = "getDeltaTimePoisson_"
    DataSrc = "DeltaTimePoisson_CPSmean={}".format(mean)

    x       = np.random.exponential(1 / mean, size=records) * 1E6    # duration before next pulse in µs

    xtext   = fncname + "size:{}, mean={:0.4f}, var={:0.4f}".format(x.size, np.mean(x), np.var(x))
    # fprint("Resulting Data:", xtext, debug=True)
    msg = "Resulting Data:", xtext
    fprint(msg)
    dprint(msg)

    return x, DataSrc


def getWhiteNoisePoisson(records, mean):
    """White noise data drawn from Poisson distribution"""

    fncname = "getWhiteNoisePoisson_"
    DataSrc = fncname + "CPSmean={}".format(mean)

    x       = np.random.poisson(mean, size=records)

    xtext   = fncname + "size:{}, mean={:0.4f}, var={:0.4f}".format(x.size, np.mean(x), np.var(x))
    # fprint("Resulting Data:", xtext, debug=True)
    msg = "Resulting Data:", xtext
    fprint(msg)
    dprint(msg)


    return x, DataSrc


def getWhiteNoiseNormal(records, mean, stddev):
    """White noise data drawn from Normal distribution"""

    fncname = "getWhiteNoiseNormal_"
    DataSrc = fncname + "CPSmean={}_std={:3.2f}".format(mean, stddev)

    x       = np.random.normal(mean, stddev, size=records)

    xtext   = fncname + "size:{}, mean={:0.3f}, var={:0.3f}, std={:0.3f}".format(x.size, np.mean(x), np.var(x), np.std(x))
    # fprint("Resulting Data:", xtext, debug=True)
    msg = "Resulting Data:", xtext
    fprint(msg)
    dprint(msg)


    return x, DataSrc


def getWhiteNoisePoissonAutocorr(records, mean, cycletime):
    """White noise data drawn from Poisson distribution"""
    # review results before using!!!

    DataSrc = "Autocorrelated Poisson Noise, CPM={}, cycle={}sec".format(mean, cycletime)

    x    = np.random.poisson(mean / 60., size=records * 60 + 60 )
    print("x.size, x.mean, x.var, x.std. :", x.size, np.mean(x), np.var(x), np.std(x))
    print(x)

    x2   = np.zeros(records)
    print("all zeros: x2.size, x2.mean, x2.var, x2.std. :", x2.size, np.mean(x2), np.var(x2), np.std(x2))

    for i in range(0, records):
        j = i * cycletime
        x2[i] = np.sum(x[j : j + 60])

    print("x2.size, x2.mean, x2.var, x2.std. :", x2.size, np.mean(x2), np.var(x2), np.std(x2))

    return x2, DataSrc


def getSinus(records, t):
    """
    sinus data
    All times in seconds
    """

    DataSrc = "Sinus"
    pi2     = 2.0 * np.pi

    x   = 10.0 + 5.0 * np.sin(t * pi2 / (100  * 60 +  0)  ) # periode von 100   min
    x  +=  0.0 + 5.0 * np.sin(t * pi2 / (400  * 60 +  0)  ) # periode von 400   min
    x  +=  0.0 + 5.0 * np.sin(t * pi2 / ( 30  * 60 +  0)  ) # periode von  50   min
    x  +=  0.0 + 5.0 * np.sin(t * pi2 / (  3  * 60 +  4)  ) # periode von   3.x min
    x  +=  0.0 + 5.0 * np.sin(t * pi2 / (  3  * 60 +  9)  ) # periode von   3.y min
    x  +=  0.0 + 5.0 * np.sin(t * pi2 / (  3  * 60 + 13)  ) # periode von   3.z min
    x  +=  0.0 + 5.0 * np.sin(t * pi2 / (  1           )  ) # periode von   1   sec
    x  +=  0.0 + 5.0 * np.sin(t * pi2 / (  0.5         )  ) # periode von   0.5 sec

    return x, DataSrc


def getConstantData(records, t):
    """
    constant data
    All times in seconds
    """

    DataSrc = "Constant + Breaks"
    x       = np.ones(records) * 1000

    for i in range(0, records - 10, 20):
        x[i]     = 500
        x[i + 1] = -10
        x[i + 2] =   1

    return x, DataSrc


def getAutocorr(records):
    """
    The autocorrelation function as time series to use as input
    All times in seconds
    """

    DataSrc = "Autocorrelation as time series - 1st point=1"

    # a small random component
    mean = 0
    std  = 0.01
    x    = np.random.normal(mean, std, size=records)

    #for a 1 sec cycle time the first 60 records will show a linear down curve
    #for i in range (0, 20):
    #    x[i] = 1 - i * 1/20

    x[0] = 1


    return x, DataSrc


def getRectangle(records):
    """
    A rectangle 1 min long with 20 samples @assumed 3sec cycle, otherwise zeros
    """

    DataSrc = "Rectangle_1min"
    x       = np.zeros(records)
    #print x
    for i in range(20): x[i] = 1
    print("x: len:", len(x), x)

    return x, DataSrc


def getWhiteNoiseSine(records, t):
    """
    White noise with Sine data
    """

    DataSrc = "WhiteNoiseNormal + Sine"
    pi2     = 2.0 * np.pi

    mean = 2500
    std  = np.sqrt(mean)
    x    = np.random.normal(mean, std, size=records)
    p1   = (100 * 60 + 1.4) / 60  # 100,0333 min
    print("getWhiteNoiseSinusData: p1:", p1)
    x   +=  40 * std * (np.sin(t * pi2 / p1 ))
    x   +=  10 * std * (np.sin(t * pi2 / 11 ))

    return x, DataSrc


def getRandomData(records, mean, stddev):
    """random data from a uniform range of 0 ... 2*mean"""

    DataSrc = "Random Data_mean={}_postive_uniform_range0...{}".format(mean, 2 * mean)

    x = mean * 2 * np.random.rand(records)
    print(DataSrc, x)

    return x, DataSrc
