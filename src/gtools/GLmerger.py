#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
gmerger.py - merging multiple CSV data files
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
__version__         = "1.0"

import sys, os, io, time, datetime  # basic modules
import getopt                       # parse command line for options and commands
from operator import itemgetter


helpOptions = """
Usage:  gmerger.py [Options] [filepath1 [filepath2 [filepath3]]]

Options:
    -h, --help          Show this help and exit.
    -V, --Version       Show version and exit.

Filepaths:
    filepath1           path of 1st file to merge
    filepath2           path of 2nd file to merge
    filepath3           path of merged files

    You can give only 1, only 2, or all 3 filepaths.

    Only 1: If only filepath1 is given, then this file is converted to a
            file with all vars listed, and saved as 'filepath1.FULL.csv'.

    Only 2: If two filepaths are given, then they will both be taken as
            source files and converted to FULL. They will NOT be saved.
            The filepath3 is created from filepath1 by adding extension
            ".MERGED.csv". This file is saved.

    All 3:  If all 3 filepaths are given, then #1 and #2 will be taken as
            source files and converted to FULL. They will NOT be saved.
            The #3 is taken as destination path. This file is saved.

"""


# This is the full FullLegendStr header with Index, DateTime, and all 12 vars
FullLegendList  = ['Index', 'DateTime', 'CPM', 'CPS', 'CPM1st', 'CPS1st', 'CPM2nd', 'CPS2nd', 'CPM3rd', 'CPS3rd', 'Temp', 'Press', 'Humid', 'Xtra']
FullLegendStr   = "to be created"
SourcePath1     = "read from commandline"
SourcePath2     = "read from commandline"
MergePath       = "read from commandline"


def exceptPrint(e, srcinfo):
    """Print exception details (errmessage, file, line no)"""

    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]    # which file?

    print("EXCEPTION: '{}' in file: '{}' in line {}".format(e, fname, exc_tb.tb_lineno))
    if srcinfo > "": print("{}".format(srcinfo))


def convertToFullCSV(sourcefilepath):
    """sourcefilepath is the Source file, which is a CSV file in GeigerLog format,
    but may not have all data columns filled.
    return: a file line list with all columns set
    """

    print("\nconvert2FullCSV: sourcefilepath: ", sourcefilepath)

    # read 1st line of file;
    # it has the Legend String header like:
    #     '#   Index,            DateTime,  CPM1st,  CPS1st,  CPM2nd,  CPS2nd,   Xtra'
    with open(sourcefilepath, 'r', encoding="UTF-8", errors='replace', buffering = 1) as fp:
        line = fp.readline()

    # convert legend string to list
    SourceLegendList = []
    line = line[1:].split(",")  # omit the initial '#'
    # print("line {}: {}".format(1, line))
    for a in line:
        SourceLegendList.append(a.strip())
    # print("SourceLegendList  : {}".format(SourceLegendList))

    FullLineList = []
    flegend = [""]*14
    flegend[0] = FullLegendStr
    FullLineList.append(flegend)
    # print("Line {}: {}".format(0, FullLegendStr))
    with open(sourcefilepath, 'r', encoding="UTF-8", errors='replace', buffering = 1) as sfp:
        rline = sfp.readline()   # 1st line is old index; to be discarded
        srline  = rline.strip()
        linecount = 1

        while rline:
            newline = [""]*14
            if linecount < 10: print("Line {:5d}: '{}'".format(linecount, srline))
            rline   = sfp.readline()
            srline  = rline.strip()
            #print("srline: ", srline)
            linecount += 1

            if srline == "" or "Index" in srline:
                continue                        # ignore empty line and line with 'Index'

            elif rline.lstrip()[0] == "#":
                newline[0] = rline[:-1]
                FullLineList.append(newline)

            else:
                data = srline.split(",")

                for i, LegItem in enumerate(FullLegendList):
                    # print("LegItem:       '{}'".format(LegItem))
                    if LegItem in SourceLegendList:
                        index = SourceLegendList.index(LegItem)
                        newline[i] = data[index].strip()

                    else:
                        newline[i] = ""

                FullLineList.append(newline)

        FullLineList.append(flegend)

    return FullLineList


def printListProper(filelist, msg="", lines=10):
    """print a list of lists"""

    print()
    if msg > "":    print(msg)
    if lines == 0:  flist = filelist
    else:           flist = filelist[:lines]

    for a in flist:
        # print(a)
        newline = ""
        if a[0][0] == "#":  # print comments as they are
            newline += a[0]
        else:
            for i, LegItem in enumerate(FullLegendList):
                # print("LegItem:       '{}'".format(LegItem))
                if    i == 1 : fmt = "{:>20s},"     # DateTime
                else:          fmt = "{:>9s},"      # all else
                newline += fmt.format(a[i])
            newline = newline[:-1]

        print(newline)
    print()


def saveListProper(filelist, sourcefile):
    """save FULL csv file nicely formatted"""

    # destination file path
    destfilepath = sourcefile + ".FULL.csv"

    with open(destfilepath, 'w', encoding="UTF-8", errors='replace', buffering = 1) as dfp:
        for i, a in enumerate(filelist):
            newline = ""
            if a[0][0] == "#":
                newline += a[0]
            else:
                for j, b in enumerate(a):
                    if    j == 1 : fmt = "{:>20s},"
                    else:          fmt = "{:>9s},"
                    newline += fmt.format(b)
            dfp.write(newline[:-1] + "\n")


def makeComboCSV(SourcePath1, SourcePath2, MergePath):
    """Merge two CSV files into one and save to MergePath"""

    global FullLegendList, FullLegendStr

    # get File One
    file1list = convertToFullCSV(SourcePath1)
    # printListProper(file1list, "Proper file1list", 10)
    # saveListProper(file1list, SourcePath1)

    # get File Two
    file2list = convertToFullCSV(SourcePath2)
    # printListProper(file2list, "Proper file2list", 10)
    # saveListProper(file2list, SourcePath2)

    # mix the two
    fileCombolist = sorted(file1list + file2list, key=itemgetter(1))
    # printListProper(fileCombolist, "Proper fileCombolist  --------------------------------------------------------", 0)
    # saveListProper(fileCombolist, SourcePath1 + ".COMBO")

    # merge and save
    with open(MergePath, 'w', encoding="UTF-8", errors='replace', buffering = 1) as dfp:
        dfp.write("# Combo CSV file using files: '{}' and '{}'\n".format(SourcePath1, SourcePath2))
        dfp.write("# using gmerger.py version: {}\n#\n".format(__version__))
        dfp.write(FullLegendStr + "\n")
        line0 = fileCombolist[0]
        # print("line0: ", line0)
        linecount = 0
        skipflag = False

        for i, line1 in enumerate(fileCombolist[1:]):

            if skipflag:                                    # there had been a line merger
                skipflag = False

            elif "Index" in line0[0]:                       # old legend line; ignore
                pass

            elif line0[0][0] == "#":                        # Comment; keep unchanged
                newline = line0[0]
                dfp.write(newline + "\n")                   # save to file

            else:
                linecount += 1
                newline  = ""
                newline += "{:>9d}," .format(linecount)     # write new index
                newline += "{:>20s},".format(line0[1])      # write DateTime

                if line0[1] != line1[1]:
                    for a in line0[2:]:
                        newline += "{:>9s},".format(a)      # write all else
                    dfp.write(newline + "  orig" + "\n")    # save to file

                else:
                    # dfp.write("EQUAL 0   " + ",".join(line0) + "\n")
                    # dfp.write("EQUAL 1   " + ",".join(line1) + "\n")
                    for i, a in enumerate(line0[2:]):
                        if line1[i + 2].strip() > "":
                            line0[i + 2] = line1[i + 2]     # overwrite line0 with line1 data
                    for i, a in enumerate(line0[2:]):
                        newline += "{:>9s},".format(a)      # write all else
                    dfp.write(newline + "  merged" + "\n")  # save to file
                    skipflag = True

            line0 = line1

        dfp.write(FullLegendStr + "\n")                     # last line is FullLegendStr


def main():
    """
    make a full csv file with all vars,
    (optional) combine 2 csv files into 1, properly sorted
    """

    global FullLegendList, FullLegendStr, SourcePath1, SourcePath2, MergePath

    print("\ngmerger.py - ", sys.argv[1:], " #" * 50)

    # prep FullLegendStr string in format for use in file
    FullLegendStr    = "#{:>8s},".format(FullLegendList[0])
    FullLegendStr   += "{:>20s},".format(FullLegendList[1])
    for a in FullLegendList[2:]:    FullLegendStr += "{:>9s},".format(a)
    FullLegendStr = FullLegendStr[:-1]

    # parse command line options (sys.argv[0] is progname)
    try:
        # opts, args = getopt.getopt(sys.argv[1:], "hVc:m:", ["help", "Version", "csv=", "merge="])
        opts, args = getopt.getopt(sys.argv[1:], "hV", ["help", "Version"])
    except getopt.GetoptError as e :
        # print info like "option -a not recognized", then exit
        msg = "For Help use: './gmerger.py -h'"
        exceptPrint(e, msg)
        print (helpOptions)
        return 1

    # processing the options
    for opt, optval in opts:
        if   opt in ("-h", "--help"):
            print (helpOptions)
            return 0

        elif opt in ("-V", "--Version"):
            print("Version:", __version__)
            return 0

    # processing the args
    lenargs = len(args)
    # print("debug: found {} args".format(lenargs))

    if lenargs == 0:
        # no filenames given; show help info
        print("No filenames were given, see Help")
        print (helpOptions)

    elif lenargs == 1:
        # just convert the one given file to FULL csv
        SourcePath1 = args[0]
        file1list = convertToFullCSV(SourcePath1)
        printListProper(file1list)
        saveListProper(file1list, SourcePath1)

    elif lenargs == 2:
        # convert the files to FULL csv, then
        # merge the files and save to default path
        SourcePath1 = args[0]
        SourcePath2 = args[1]
        MergePath   = SourcePath1 + ".MERGED.csv"
        makeComboCSV(SourcePath1, SourcePath2, MergePath)

    elif lenargs == 3:
        # convert the files to FULL csv, then
        # merge the files and save to user given name
        SourcePath1 = args[0]
        SourcePath2 = args[1]
        MergePath   = args[2]
        makeComboCSV(SourcePath1, SourcePath2, MergePath)


if __name__ == '__main__':
    main()
    print()

