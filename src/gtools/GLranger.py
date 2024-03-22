#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GLranger.py - To parse download from Ranger Counter and convert to CSV

usage:   GLranger.py path/to/<file-to-be-converted>
output:  converted file: path/to/<file-to-be-converted>.csv
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

"""
NOTE:
from the downloaded Ranger file:
2033/31/31  37:33   57       cpm per mR/h   115.99 % 

FF:  0x0C: Form Feed       -- seems meaningless in this setting
SOH: 0x01: Start of header -- seems meaningless in this setting
"""

import sys                                      # system
import re                                       # regex

def main():

    inputfile  = sys.argv[1]
    outputfile = inputfile + ".csv"

    with open(outputfile, "wt") as handle:      # delete file
            pass

    print("\n------------------------ GLranger.py ---------------------------")
    print("Converting file: ", inputfile)
    print("----------------------------------------------------------------")
    print()

    p = re.compile("\d\d\d\d/\d\d/\d\d")        # regex matching like: 2021/03/27

    with open(inputfile, "r") as handle:
        for line in handle:
            mline   = line.rstrip()             # remove right whitespace
            newline = ""
            seg1 = mline[ 0:17]                 # DateTime
            seg2 = mline[18:32]                 # CPM if seg3=='1'
            seg3 = mline[32:33]                 # must be '1' for seg2 to be CPM
            print("seg1:'{:20s}', seg2:'{:15s}', seg3:'{:1s}'".format(seg1, seg2, seg3), end="        -->    ")
            if p.match(seg1):
                newline = seg1.replace("/", "-").replace("  ", " ") + ":00"
                if seg3 == '1':  newline += ", " + str(int(seg2))
                else:            newline  = "#"  + newline + mline[18:]
            else:
                newline = "#" + mline

            newline += "\n"
            print(newline, end="")

            with open(outputfile, "at") as handle:
                handle.write(newline)


if __name__ == '__main__':
    main()
