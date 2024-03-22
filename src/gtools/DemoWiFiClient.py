#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
DemoWiFiClient.py - a utility which acts like a WiFiClient device by calling GeigerLog's
                    built-in web server with a GET message carrying the data.

                    It can act either as    WiFiClientType = GENERIC
                                   or as    WiFiClientType = GMC
                    by setting python variable WiFiClientType accordingly
                    (see: User adaptable configuration; approx line 40 ff).

                    As GENERIC it will be sending all possible 12 variables of GeigerLog,
                    with each value being a random number.

                    As GMC     it will be sending 3 variables
                    with each value being a random number as it might come from a GMC counter.

Start with:     DemoWiFiClient.py
Stop with:      CTRL-C
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


###########################################################################
### User adaptable configuration
serverIP        = "10.0.0.20"    # IP of computer running GeigerLog
serverPort      = "8000"         # Port where GeigerLog will be listening
WiFiClientType  = "GENERIC"      # use "GENERIC" or "GMC"
WiFiClientType  = "GMC"
### END User adaptable configuration - no changes below this line
###########################################################################


__author__          = "ullix"
__copyright__       = "Copyright 2016, 2017, 2018, 2019, 2020, 2021, 2022"
__credits__         = [""]
__license__         = "GPL3"


import sys, os, io, time, datetime  # basic modules
import urllib.request               # calling a web server
import numpy           as np        # for random f'on


def longstime():
    """Return current time as YYYY-MM-DD HH:MM:SS.mmm, (mmm = millisec)"""

    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] # ms resolution


def main():

    baseurl = "http://{}:{}".format(serverIP, serverPort)
    numbers = [0] * 12              # THIS IS FOR THE GENERIC DEVICE

    if WiFiClientType == "GENERIC": typeurl = baseurl + "/GENERIC"
    else:                           typeurl = baseurl + "/GMC"

    # Get the ID of GL's server
    idurl   = baseurl + "/id"
    try:
        with urllib.request.urlopen(idurl, timeout=3) as page:
            answer    = page.read()

        print("Get the ID of GL's server: ", idurl, "    answer: ", answer)

    except Exception as e:
        print("Exception: ", e, "Failed to get: " + idurl)

    dur = 0

    while True:
        tstart = time.time()
        if WiFiClientType == "GENERIC":
            # THIS IS FOR THE GENERIC DEVICE - a bunch of random normal numbers
            for i in range(12): numbers[i] = round(np.random.normal(i + 10, 0.5), 2)

            dataurl = typeurl + "?M={}&S={}&M1={}&S1={}&M2={}&S2={}&M3={}&S3={}&T={}&P={}&H={}&X={}".format(*numbers)

        else:
            # THIS IS FOR THE GMC DEVICE - a poisson, a normal, and a calculated uSv value
            cpm  = np.random.poisson(100)
            acpm = round(np.random.normal(100, 1), 2)
            # usv  = round(cpm / 154, 2)
            usv  = round(dur, 3)

            dataurl = typeurl + "?CPM={}&ACPM={}&uSV={}".format(cpm, acpm, usv)

        try:
            # upload the data via GET call
            with urllib.request.urlopen(dataurl, timeout=3) as page:
                answer = page.read()

            dur = 1000 * (time.time() - tstart)
            print(longstime() + " DemoWiFiClient: {:65s} answer: {}  dur: {:0.2f} ms".format(dataurl, answer.strip(), dur))

        except Exception as e:
            print("Exception: ", e, dataurl)
            time.sleep(2)

        time.sleep(1)


if __name__ == '__main__':
    main()

