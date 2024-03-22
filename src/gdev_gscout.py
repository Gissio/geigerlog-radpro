#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
gdev_gscout.py - GeigerLog commands to handle the Gamma-Scout Geiger counter
                 Standard, Alert, Rechargeable, Online
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


# NOTES:
# GeigerLog supports Gamma-Scout models Standard, Alert, Rechargeable, and Online.
# Since Standard, Alert, and Rechargeable do not support logging from these devices,
# GeigerLog implements their use for logging such that those GS counters return
# only empty values (= NAN values) as logged data.

# The Online Gamma-Scout .... tbd

# Logging requires that a connection exists to a GS device, even if only as a
# simulator, see next.

# SIMULATION:
# If a GS device is not available, it can be simulated. To do so start program
# GLgammascoutsim.py in a separate Terminal window as SUDO (!):
#                     sudo gtools/GLgammascoutsim.py
# and start GeigerLog with the command gstesting, like:
#                     python3 geigerlog gstesting
# GS will be connectable and allows downloading from the simulated device (but
# logging will result in empty values only).

# DOWNLOADING:
# Gamma-Scout_Communication_Interface_V1.7.txt
# from: https://www.gamma-scout.com/wp-content/uploads/Gamma-Scout_Communication_Interface_V1.7.txt

# The contents of the protocol memory consists of either 2 byte pulse entries or
# special codes. It must be interpreted byte by byte. Special codes start with a
# byte with its high-nibble being 0xF. If the high-nibble is not 0xF, this byte
# will be the first byte of a 2 byte pulse entry.

# This 2 byte pulse entry represents the number of pulses collected during the
# last protocol interval (or the number of pulse during an out-of-band protocol
# interval, see below). The highest 5 bits contain the exponent, the lower 11
# bits the mantissa. E.g.:
#     0x3E27 = %0011111000100111 = 2^7 (exponent) * 1575 (mantissa) = 201600

# TUBE:
# Gamma-Scout tube: LND 712
# https://www.lndinc.com/products/geiger-mueller-tubes/712/
# Spec.Sheet:
#     GAMMA SENSITIVITY CO60 (CPS/mR/HR)                  : 18
#     MAXIMUM BACKGROUND SHIELDED 50MM PB + 3MM AL (CPM)  : 10

# Calculated:
# Gamma Sensitivity : 18 CPS/mR/h = 1080 CPM/mR/h = 1080 CPM/10µSv/h = 108 CPM/µSv/h
# invers:           : 1/108 = 0.00926 µSv/h/CPM
# Compare with M4011: (0.00926 / 0.0065 = 1.42 (1 / 1.42 = 0.70)
#                   : LND 712 has only 70% of sensitivity of M4011 for gamma

# Memory: (manual 2018 page 16)
# Wenn im Speicher nur noch 256 Bytes (von den 65280 Bytes) zum Beschreiben
# zur Verfügung stehen, schaltet der GAMMA-SCOUT® automatisch auf 7 Tage
# Protokollintervall zurück. In diesem Fall sind kürzere Protokollintervalle
# erst nach dem Löschen des Speichers wieder einstellbar.



from   gsup_utils       import *
import gsup_sql                         # database handling


#
# Private Constants
#

# intervals in sec as used in GammaScout
# this is the list of intervals for the 'Online' breed of counters. The Classic
# list is reached with using 'index + 1'
#
# "The device now supports stopping the protocol. Since a protocol interval of 0
# (zero) now denotes a stopped protocol, the remaining protocol intervals have
# shiftet +1."

protocol_interval_online  = {
    0x00 : 0               ,  #   User disabled the protocol
    0x01 : 7 * 24 * 60 * 60,  #   User selected a protocol interval of 1 week
    0x02 : 3 * 24 * 60 * 60,  #   User selected a protocol interval of 3 days
    0x03 : 1 * 24 * 60 * 60,  #   User selected a protocol interval of 1 day
    0x04 :     12 * 60 * 60,  #   User selected a protocol interval of 12 hours
    0x05 :      2 * 60 * 60,  #   User selected a protocol interval of 2 hours
    0x06 :      1 * 60 * 60,  #   User selected a protocol interval of 1 hour
    0x07 :          30 * 60,  #   User selected a protocol interval of 30 minutes
    0x08 :          10 * 60,  #   User selected a protocol interval of 10 minutes
    0x09 :           5 * 60,  #   User selected a protocol interval of 5 minutes
    0x0A :           2 * 60,  #   User selected a protocol interval of 2 minutes
    0x0B :           1 * 60,  #   User selected a protocol interval of 1 minute
    0x0C :               30,  #   User selected a protocol interval of 30 seconds
    0x0D :               10,  #   User selected a protocol interval of 10 seconds
}


def printTestValues():
    """test values for floating formatting"""

    testraws = [0x3e27,             # = 201600 # example from Gamma Scout company
                0x00aa,             # = 170
                0x01bb,             # = 443
                0x02cc,             # = 716
                0x03dd,             # = 989
                0x04ee,             # = 1262
                0x05ff,             # = 1535
                0x1234,             # = 3176
                0b0000011111111110, # = 2046
                0b0000011111111111, # = 2047
                0b0000111111111111, # = 4094
                0b0001111111111111, # = 16376
                0xabcd,             # = 2094006272
                0x7fff,             # max des Gerätes 0xF signalisiert Funktion
                0xffff,             # max test
                0x0DAE,             # aus *.dat
                ]

    for raw in testraws:
        print("raw: 0x {:04X}, 0b {:016b},   value: {:17,d}".format(raw, raw, _getValue(raw)))

    print("\n")


#
# Private Functions
#

def _getValue(raw):
    """
    Gamma-Scout_Communication_Interface; raw is a 2 byte value. The highest
    5 bits contain the exponent, the lower 11 bits the mantissa. E.g.:
    0x3E27 = %0011 1  110 0010 0111 = 2^7 (exponent) * 1575 (mantissa) = 201600
    """

    exponent = raw >> 11
    mantissa = raw & 0b0000011111111111
    counts   = mantissa * (2 ** exponent)

    #print("raw: {:6d}  0x{:04X} 0b{:016b} {} {}".format(raw, raw, raw, "{:016b}".format(raw)[0:5], "{:016b}".format(raw)[5:]), end= "  ")
    #print("exponent: {:3d},  mantissa: {:5d}".format(exponent, mantissa ), end ="  ")
    #print("counts: {:17,d}".format(counts))

    return counts


def _getDateByte(raw):
    """hex value to be interpreted as alphanumeric: 0x37 = decimal 37!"""

    rdate = 10 * (raw  >> 4) + (raw & 0x0f)
    return "{:02d}".format(rdate)


def _num2datstr(timestamp):

    dt = datetime.datetime.fromtimestamp(timestamp)

    return str(dt)


def _New_parseCommentAdder(i, countertime, dbtype):

    rectime      = _num2datstr(countertime)

    datalist     = [None] * 4   # 4 x None
    datalist[0]  = i            # byte index
    datalist[1]  = rectime      # Date&Time
    datalist[2]  = "0 hours"    # the modifier for julianday; here: no modification
    datalist[3]  = dbtype       # Date&Time Stamp Info
    #print("#{:5d}, {:19s}, {:}".format(i, rectime, dbtype))

    gglobs.HistoryCommentList.append(datalist)


def _New_parseValueAdder(i, countertime, counts, parsecomment, cpm_calc, interval):
    """Add the parse results to the *.his list and commented *.his.parse list"""

    # create the data for the database; datalist covers:
    # Index, DateTime, <modifier>,  CPM, CPS, CPM1st, CPS1st, CPM2nd, CPS2nd,  CPM3rd, CPS3rd, Temp, Press, Humid, X
    # 0      1         2            3    4    5       6       7        8       9       10      11    12     13     14

    rectime      = _num2datstr(countertime)

    datalist     = [None] * (gglobs.datacolsDefault + 2)   # (13 + 2)=15 x None
    datalist[0]  = i                    # byte index
    datalist[1]  = rectime              # Date&Time
    datalist[2]  = "0 hours"            # the modifier for julianday; here: no modification
    datalist[9]  = cpm_calc             # the cpm CALCULATED by adding up counts for last 60 sec
    datalist[10] = counts               # the counts in whatever the interval had been
    datalist[14] = interval             # the interval of counting
    #print("_New_parseValueAdder: datalist: ", datalist)

    gglobs.HistoryDataList.append (datalist)
    gglobs.HistoryParseList.append([i, parsecomment])


def GSgetParsedHistory(hisbytes, maxbytes=0xFFFF):
    """For Gamma-Scout Classic and ONLINE: Parse the history as bytes dump"""

   # startPH   = time.time()

    fncname = "GSgetParsedHistory: "
    vprint(fncname)
    setIndent(1)
    try:
        index = hisbytes.index(0xF5) # =245 =start location of history
    except Exception as e:
        msg = "ERROR: Cannot find start byte 0xF5 (=245) in downloaded Online History"
        exceptPrint(e, msg)
        efprint(msg)
        return

    parsecounter    = 0
    parsecountlimit = 30       # max number of count records to be printed
    parsecountpos   = 300      # print every parsecountpos record
    lastinterval    = None     #the last interval used, needed to see changes
    interval        = 0
    countertime     = 0
    timestamp       = 0
    datestr         = ""
    cpmHistfreq     = 6        # number of measurements taken per minute (6 when interval is 10sec)
    cpmcalc         = None     # for storing last Counts_per_Xsec values as long as X <= 60

    while True:
        raw = hisbytes[index]       # raw is SINGLE byte!

     # Special code - Flag for more bytes to check
        if raw == 0xF5:
            rtime    = _num2datstr(countertime)
            dbtype = "{:20s}: 0x{:02X} ({:3d})".format("Code-Follows Flag", raw, raw)
            wprint("index:{:5d} {:5d} : {:19s}, {}".format(index, 0, rtime, dbtype))
            _New_parseCommentAdder(index, countertime, dbtype)

            index += 1
            raw = hisbytes[index]       # take next byte; raw is SINGLE byte!

        # interval
            if raw >= 0x00 and raw <= 0x0d:
                if gglobs.GS_DeviceDetected == "Online": interval_offset = 0
                else:                         interval_offset = 1
                interval = protocol_interval_online[raw + interval_offset]
                rtime    = _num2datstr(countertime)
                dbtype   = "{:20s}: 0x{:02X} ({:3d}), Interval[sec]: old:{} new:{} ".format("Protocol Interval", raw, raw, lastinterval, interval)
                dbtype2  = TGREEN + dbtype + TDEFAULT
                wprint("index:{:5d} {:5d} : {:19s}, {}".format(index, 0, rtime, dbtype2))
                _New_parseCommentAdder(index, countertime, dbtype)

                if interval != lastinterval:
                    if interval <= 60:
                        cpmHistfreq = int(60 / interval)
                        cpmcalc     = np.full(cpmHistfreq, gglobs.NAN)    # for storing last cpmHistfreq of count values, fill with NANs
                    else:
                        cpmcalc     = None
                    #edprint("interval != lastinterval: {}  {} cpmcalc: {}".format(interval, lastinterval, cpmcalc))
                    lastinterval = interval

                index += 1

        # timestamp Online -- 6 bytes
            # 0xED   format: ssmmhhDDMMYY
            elif raw == 0xED:
                ss = _getDateByte(hisbytes[index + 1])
                mm = _getDateByte(hisbytes[index + 2])
                hh = _getDateByte(hisbytes[index + 3])
                DD = _getDateByte(hisbytes[index + 4])
                MM = _getDateByte(hisbytes[index + 5])
                YY = _getDateByte(hisbytes[index + 6])

                tbytes      = "6 Bytes hex:" + " ".join("%02X" % e for e in hisbytes[index + 1: index + 7]) + " "
                tstamp      = "20{}-{}-{} {}:{}:{}".format(YY, MM, DD, hh, mm, ss)
                countertime = datestr2num(tstamp)
                rtime       = _num2datstr(countertime)
                dbtype      = "{:20s}: 0x{:02X} ({:3d}): {} ({})".format("Timestamp Online", raw, raw, tbytes, tstamp)
                dbtype2     = TGREEN + dbtype + TDEFAULT
                wprint("index:{:5d} {:5d} : {:19s}, {}".format(index, 0, rtime, dbtype2))
                _New_parseCommentAdder(index, countertime, dbtype)

                index += 1 + 6


        # timestamp Classic -- 5 bytes
            # 0xEF   format:  mmhhDDMMYY
            elif raw == 0xEF:
                ss = "00" # added here, not defined in firmware of the Classics
                mm = _getDateByte(hisbytes[index + 1])
                hh = _getDateByte(hisbytes[index + 2])
                DD = _getDateByte(hisbytes[index + 3])
                MM = _getDateByte(hisbytes[index + 4])
                YY = _getDateByte(hisbytes[index + 5])

                #tbytes      = "hexbytes:" + " ".join("%02X" % e for e in hisbytes[index + 1: index + 6])
                tbytes      = "5 Bytes hex:" + " ".join("%02X" % e for e in hisbytes[index + 1: index + 6]) + " "
                tstamp      = "20{}-{}-{} {}:{}:{}".format(YY, MM, DD, hh, mm, ss)
                countertime = datestr2num(tstamp)
                rtime       = _num2datstr(countertime)
                dbtype      = "{:20s}: 0x{:02X} ({:3d}): {} ({})".format("Timestamp Classic", raw, raw, tbytes, tstamp)
                dbtype2     = TGREEN + dbtype + TDEFAULT
                wprint("index:{:5d} {:5d} : {:19s}, {}".format(index, 0, rtime, dbtype2))

                _New_parseCommentAdder(index, countertime, dbtype)

                index += 1 + 5


        # out of band
            elif raw == 0xEE:
                nextbyte1 = hisbytes[index + 1]  # nextbyte1 and 2 give number of 10 sec to be added to time
                nextbyte2 = hisbytes[index + 2]
                addedtime = (nextbyte2 * 256 + nextbyte1) * 10 # multiples of 10 sec
                rtime     = _num2datstr(countertime)
                dbtype = "{:20s}: 0x{:02X} ({:3d}): protocol interval: 0x{:02X} 0x{:02X} => addedTime:{}".format("Out-Of-Band", raw, raw, nextbyte1, nextbyte2, addedtime)
                wprint("index:{:5d} {:5d} : {:19s}, {}".format(index, 0, rtime, dbtype))
                _New_parseCommentAdder(index, countertime, dbtype)
                extra = 0
                while hisbytes[index + 3 + extra] == 0xFC:
                    extra += 1 #das Alarm byte sollte nie innerhalb einer anderen Sequenz vorkommen!
                    dbtype = "{:20s}: 0x{:02X} ({:3d}): Dose (rate) alarm fired".format("Alarm", 0xFC, 0xFC)
                    wprint("index:{:5d} {}".format(index + 3 + extra, dbtype))
                    _New_parseCommentAdder(index + 3 + extra, countertime, dbtype)

                raw1 = hisbytes[index + 3 + extra]
                raw2 = hisbytes[index + 4 + extra]
                count = _getValue(raw1 << 8 | raw2)
                dbtype = "{:20s}: 0x{:02X} 0x{:02X} : => count:{}".format("Out-of-Band pulses", raw1, raw2, count)
                wprint("index:{:5d} {:5d} : {:19s}, {}".format(index, 0, rtime, dbtype))
                _New_parseCommentAdder(index, countertime, dbtype)

                if addedtime > 0:
                    dbtype = "{:19s}, {:10d}, {:9,.1f}, {:8d}".format(_num2datstr(countertime), count, count/addedtime * 60, addedtime)
                    wprint("index:{:5d} {:5d} : {}  # Out-of-Band pulses, excluded from parsing result".format(index, 0, dbtype))
                    #_New_parseValueAdder (index, countertime, count, parsecomment, count/addedtime * 60, addedtime)
                    #parsecounter += 1           # wäre notwendig wenn _parseValueAdder zum Zuge gekommen wäre

                #~countertime += interval + addedtime
                #~countertime += interval
                countertime += addedtime
                index       += 1 + 4 + extra


        # ignore debug - seems relevant only for Classic but does not harm Online
            # "0xF0-0xFE debug flags, must be ignored"
            elif raw >= 0xF0 and raw <= 0xFE:
                dbtype = "{:20s} must be ignored: 0x{:02X} ({:3d}): ".format("Debug flags", raw, raw)
                wprint(dbtype)
                _New_parseCommentAdder(index, countertime, dbtype)

                index += 1

    # skip byte
        # "0xF8    This is a new internal special byte. The following size byte denotes
        # the amount of additionally following bytes (including this size byte
        # but not including the special byte 0xF8) which have to be ignored and
        # skipped over in the protocol stream."
        elif raw == 0xF8:
            nextbyte = hisbytes[index + 1]
            rtime    = _num2datstr(countertime)
            dbtype   = "{:20s}: 0x{:02X} ({:3d}): Bytes to skip: {}".format("Skip Byte", raw, raw, nextbyte)
            dbtype2  = TGREEN + dbtype + TDEFAULT
            wprint("index:{:5d} {:5d} : {:19s}, {}".format(index, 0, rtime, dbtype2))
            _New_parseCommentAdder(index, countertime, dbtype)

            index += 1 + nextbyte


    # Special code - Dose overflow - Classic Only
        elif raw == 0xFA and gglobs.GS_DeviceDetected == "Classic":
            rtime   = _num2datstr(countertime)
            dbtype  = "{:20s}: 0x{:02X} ({:3d}): Dose rate overflowed (> 1000 uSv/h) during the current protocol interval at least once.".format("Overflow Code", raw, raw)
            wprint("index:{:5d} {:5d} : {:19s}, {}".format(index, 0, rtime, dbtype))
            _New_parseCommentAdder(index, countertime, dbtype)
            index += 1


    # special codes 0xF9 with 0xFF
        # 0xF9    Dose rate overflowed
        # 0xFA    Dose alarm fired
        # 0xFB    Dose alarm fired + Dose rate overflowed
        # 0xFC    Dose rate alarm fired
        # 0xFD    Dose rate alarm fired + Dose rate overflowed
        # 0xFE    Dose rate alarm fired + Dose alarm fired
        # 0xFF    Dose rate alarm fired + Dose alarm fired + Dose rate overflowed
        elif raw >= 0xF9 and raw <= 0xFF:
            rtime    = _num2datstr(countertime)
            dbtype = "{:20s}: 0x{:02X} ({:3d}): Dose or Dose rate alarm overflowed/fired".format("Alarm", raw, raw)
            wprint("index:{:5d} {:5d} : {:19s}, {}".format(index, 0, rtime, dbtype))
            _New_parseCommentAdder(index, countertime, dbtype)

            index += 1


    # counts
        else:
            raw1  = hisbytes[index    ]
            raw2  = hisbytes[index + 1]
            count = _getValue(raw1 << 8 | raw2)

            if cpmcalc is not None:     # use only when interval <= 60
                cpmcalc = np.append(cpmcalc, count)[-cpmHistfreq:] # append, but then take last cpmHistfreq values only
                cpi     = float(np.sum(cpmcalc))
            else:
                cpi     = gglobs.NAN    # cannot calculate true CPM if interval > 60!

            parsecomment = "# raw bytes: 0x{:02X}{:02X}".format(raw1, raw2)
            _New_parseValueAdder     (index, countertime, count, parsecomment, cpi, interval)
            parsecounter += 1

            # printouts, like first 50, then every 150th, then last 50
            if parsecounter < parsecountlimit or parsecounter % parsecountpos == 0 or (maxbytes - index) < (parsecountlimit * 2) :
                rtime = _num2datstr(countertime)
                dbtype = "{:10d}, {:9,.1f}, {:8d}, # raw bytes: 0x{:02X}{:02X}".format(count, cpi, interval, raw1, raw2)
                wprint("index:{:5d} {:5d} : {:19s}, {}".format(index, parsecounter, rtime, dbtype))

            countertime += interval
            index       += 1 + 1


        if index >= maxbytes:
            rtime    = _num2datstr(countertime)
            dbtype = "# maxbytes reached or exceeded: index:{}, maxbytes:{} (0x{:04X})".format(index, maxbytes, maxbytes)
            wprint("index:{:5d} {:5d} : {:19s}, {}".format(index, 0, rtime, dbtype))
            _New_parseCommentAdder(index, countertime, dbtype)
            break

        if index >= len(hisbytes) - 1:
            break

    setIndent(0)


def GSreadDataFromFile(dat_path):
    """read an ASCII file as readlines and return as list of byte values"""

    fncname  = "GSreadDataFromFile: "
    dumpdata = []
    wprint(fncname)
    setIndent(1)

    if not gglobs.Devices["GammaScout"][CONN] : return dumpdata

    try:
        with open(dat_path) as f:
            filedata = f.readlines()     # reads data as list of STRINGS
                                         # last char in each line is LF (value: 0x10)
    except Exception as e:
        exceptPrint(e, fncname + "Exception at f.readlines()")
        return dumpdata
    wprint(fncname + "filedata: type:{}, lines:{}".format(type(filedata), len(filedata)))

    if gglobs.werbose:
        wprint(fncname + "filedata - begin ------------------------------------")
        limit = 13
        for i, a in enumerate(filedata):
            if i == limit: print("...")
            if i < limit or i > len(filedata) - limit:
                print("    i: {:5d} : ".format(i), a, end="")
        print()
        wprint(fncname + "filedata - end   ------------------------------------")

    # write *.dat data to database
    gsup_sql.DB_insertBin (gglobs.hisConn, "".join(filedata))

    for a in filedata:    # remove last char LF
        dumpdata.append(a[:-1])

    wprint(fncname + "dumpdata: type:{}, lines:{}".format(type(dumpdata), len(dumpdata)))
    dashline = fncname + "-" * 80
    wprint(dashline)
    for a in dumpdata[ :12]: wprint(a)
    wprint("...")
    for a in dumpdata[-10:]: wprint(a)
    wprint(dashline)

    setIndent(0)
    return dumpdata


def GSclearPipeline():
    """Clearing pipeline"""

    if not gglobs.Devices["GammaScout"][CONN] : return
    if gglobs.GSser is None: return

    fncname = "GSclearPipeline: "
    dprint(fncname)

    while True:
        time.sleep(0.1)
        cnt = globs.GSser.in_waiting
        if cnt == 0: break
        globs.GSser.read(cnt)


def GSreadAll(bytecount=None, waittime=4):
    """Read all waiting data"""

    fncname = "GSreadAll: "

    msg = "requested bytes to read: {}".format(bytecount)

    alldata, rmsg = _GSread_waiting(bytecount=bytecount, waittime=waittime)
    cdprint(fncname + msg + ",  alldata: '{}'  rmsg: '{}'".format(alldata, rmsg))

    return alldata


def _GSread_waiting(bytecount=None, waittime=4):
    """read all waiting bytes and return decoded and stripped string"""

    fncname  = "_GSread_waiting: "
    bytedata = b""
    alldata  = ""
    msg      = ""

    if gglobs.GSser is None:
        return alldata, "no connection"

    # wait for the first bytes appearing in_waiting
    start1 = time.time()
    while (time.time() - start1) < waittime: # could take more than 3 sec!
        try:
            bw = gglobs.GSser.in_waiting
        except Exception as e:
            exceptPrint(e, fncname + "#1 GSser.in_waiting Exception")
            bw = 0

        #print(".", end="", flush=True)
        time.sleep(0.01)
        if bw > 0: break
    #print()
    cdprint(fncname + "1st   wait: {:6.1f} ms, now waiting: {} bytes".format((time.time() - start1) * 1000, bw)) # 400 ... 1000 ms

    # at this point there are some bytes waiting
    if bytecount != None:   bytedata += gglobs.GSser.read(bytecount) # reads bytecount data BYTES
    else:                   bytedata += gglobs.GSser.read(bw)        # reads bw data as BYTES

    # wait for any late bytes
    start2 = time.time()
    last   = start2
    wait2  = 0.05 # sec waiting in while loop
    try:
        bw = gglobs.GSser.in_waiting
    except Exception as e:
        exceptPrint(e, fncname + "#2 GSser.in_waiting Exception")
        bw = 0
    while time.time() - start2 < wait2 or bw > 0:
        if bw > 0:
            bytedata += gglobs.GSser.read(bw)   # reads data as BYTES
            now =  time.time()
            wprint(fncname + "2nd   wait: {:6.1f} ms, now waiting: {} bytes".format((now - last) * 1000, bw))
            last = now
        time.sleep(0.02)
        try:
            bw = gglobs.GSser.in_waiting
        except Exception as e:
            exceptPrint(e, fncname + "#3 GSser.in_waiting Exception")
            bw = 0

    cdprint(fncname + "total wait: {:6.1f} ms, got total  : {} bytes".format((time.time() - start1) * 1000, len(bytedata))) # 400 ... 1000 ms

    ######################
    #~sbytedata = bytedata.strip().split(b"\r\n")
    #~for i, a in enumerate(sbytedata):
        #~print("_GSread_waiting: {:3d} len: {:3d} {}".format(i, len(a), a))
    ################

    # check Null values #######################################################
    if 0x00 in bytedata:
        msg0  = "Bytes read from device contain the illegal value 0x00 !"
        msg1  = "\nThere may be a problem with the device or with the transmission."
        msg1 += "You can try to unplug/replug \nthe device with the computer.\n"
        msg1 += "Any records containing wrong chracters will be ignored in the anaylsis. "
        msg1 += "You can continue,\nbut be aware of possibly missing records."
        setIndent(1)
        edprint(msg0, debug=True)
        setIndent(0)
        efprint(msg0 + msg1)
        qefprint("Count of 0x00 in transferred 7-bit bytes: {}. First occurence at position: {} of {}."\
                    .format(bytedata.count(0x00), bytedata.index(0x00), len(bytedata)))
        bytedata = bytedata.replace(b"\x00", b"\x01")
        playWav("err")
    # End Check Null Values ###################################################

    alldata    = bytedata.decode("UTF-8").strip()
    lenalldata = len(alldata)
    msg = ""

    if lenalldata > 0:
        msg        = "Read data: decoded: len:{}".format(lenalldata)
        if lenalldata < 100:
            msg += "  '{}'"  .format(alldata)
        else:
            limit = 200
            msg += "\n{}".format(alldata[0:limit])
            if lenalldata >= limit: msg += " <more>"

    return alldata, msg


def GSwriteToDevice(wdata, purpose=""):
    """writing wdata to device; type(wdata)=bytes
    returns True if ok, otherwise False"""

    fncname = "GSwriteToDevice: "

    if gglobs.GSser is None:
        edprint(fncname + "Serial Port is closed; cannot write to it!")
        return False

    wprint(fncname + "Writing '{}' (len:{}) to device -- purpose: '{}'".format( wdata, len(wdata),purpose))

    bytesWritten = None
    try:
        bytesWritten = gglobs.GSser.write(wdata) # this line writes the data to the port; takes <0.1ms
        if bytesWritten == len(wdata):
            ok = True
        else:
            ok = False
            setIndent(1)
            wprint(fncname + "FAILURE writing '{}' to device: {} bytes written, but write data has length {}".format(wdata, bytesWritten, len(wdata)))
            setIndent(0)

    except Exception as e:
        ok  = False
        msg = "ERROR: Writing data '{}' to device".format(wdata)
        exceptPrint(e, msg)
        efprint(msg)

    return ok


def GSconvertDumpToBinList(dumpdata):
    """take ascii coded hex values from readlines str data and convert to list of bytes"""

    # e,g,: dumpdata[12]: len=67: f5ef5923130819f507f5ee0300000af50c00020001000100050004000500030096
    # ends with '96' as any LF or CR+LF has been removed!

    fncname = "GSconvertDumpToBinList: "
    len_dumpdata = len(dumpdata)

    vprint(fncname + "len(dumpdata): {}".format(len_dumpdata))
    setIndent(1)

    if len_dumpdata == 0:
        vprint(fncname + "No data to convert")
        setIndent(0)
        return []

    index = 0
    # search for text "GAMMA-SCOUT Protokoll"
    for i in range(0, len_dumpdata):
        if dumpdata[i].startswith("GAMMA-SCOUT Protokoll"):
            index = i
            strwprint  = "i={:5d} dumpdata[i]: {}".format(i, dumpdata[i])
            wprint(strwprint)
            break

    # search for text "f5" beginning at "GAMMA-SCOUT Protokoll"
    for i in range(index, len_dumpdata):
        if dumpdata[i].startswith("f5"):
            index = i
            break

    # convert double-chr to byte and add to list
    listdumpdata = []
    for i in range(index, len_dumpdata):
        lendata = len(dumpdata[i])

        ###########################################
        if lendata > 66:
            strwprint  = "i={:5d} dumpdata[i]: {}  lendata: {}".format(i, dumpdata[i], lendata)
            edprint(strwprint + "  ************ wrong data *************")
            continue # to avoid wrong records!!!!!!!!!!!!!!!!
        ###########################################

        # limited printout
        if i == index + 10: wprint("....")
        if i < index + 10 or i > (len_dumpdata - 10):
            strwprint  = "i={:5d} dumpdata[i]: {}  lendata: {}".format(i, dumpdata[i], lendata)
            try:
                checksum = 0
                for j in range(0, lendata - 2, 2):
                    newval = int(dumpdata[i][j:j+2], 16)
                    #print(newval, end=" ")
                    checksum += newval
                checksum = checksum & 0xFF
                strwprint += " Checksum: {:02x}".format(checksum)
                strwprint += " Delta to dumpdata ...{}: {:3d}".format(dumpdata[i][-2:], checksum - int(dumpdata[i][-2:], 16))

            except Exception as e:
                msg  = "Checksum calculation gave Exception, i:{} j:{}".format(i, j)
                msg += strwprint
                exceptPrint(e, msg)
            wprint(strwprint)

        # get byte data from ASCII list
        for j in range(0, lendata - 2, 2):
            #print("j={}".format(j), end=" ")
            try:
                lbyte = int(dumpdata[i][j : j + 2], 16)
            except Exception as e:
                msg  = fncname + "Exception in 'lbyte = int(dumpdata[i][j : j + 2], 16)': i:{}, j={}".format(i,j)
                msg += "  dumpdata[i][j : j + 2], =" + str(dumpdata[i][j : j + 2])
                exceptPrint(e, msg)
                lbyte = 0xFA # overflow single byte value
            listdumpdata.append(lbyte)

    wprint(fncname + "listdumpdata : len: {} (0x{:04X}) ".format(len(listdumpdata), len(listdumpdata)))
    wprint(fncname + "first 30     : ", listdumpdata[:30])
    wprint(fncname + "last  30     : ", listdumpdata[-30:])
    wprint(fncname + "======================================")

    setIndent(0)
    return listdumpdata


def GSextractExtendedInfo(infoline):
    """to extract info from infoline
    return: nothing (all returns via gglobs)
    """

    """
    PC mode up to fw 6.1x:
    'v' returns: fw version, SN, number of used bytes in the protocol memory, date and time

    changes in PC mode starting with fw 6.90:
    'v' returns: fw version, CPU version, SN, number of used bytes in the protocol memory, date and time

    changes in PC mode starting with fw 7.03:
    'v' returns: fw version, SN, number of used bytes in the protocol memory, date and time

            GSfwtype
    e.g.:   610:    infoline = 'Version 6.10 d93683 4217 18.08.19 17:43:57'
            702:    infoline = 'Version 7.02Lb07 1020 073160 4bde 18.02.21 15:42:39'
            703:    infoline = 'Version 7.03xyz 073160 4bde 18.02.21 15:42:39'
    """

    if infoline is None or len(infoline) == 0: return

    fncname  = "GSextractExtendedInfo: "

    dprint(fncname + "infoline: '{}'".format(infoline))
    setIndent(1)

    gglobs.GS_DeviceDetected           = ""
    gglobs.GSDateTime       = ""
    gglobs.GSSerialNumber   = ""
    gglobs.GSFirmware       = ("", "")  # major, minor fw numbers
    gglobs.GSusedMemory     = 0

    # if len(infoline) == 0:
    #     dprint(fncname + "No data in infoline: '{}'".format(infoline))

    # else:
    if 1:
        infolist = infoline.split(" ")
        cdprint(fncname + "infolist: '{}'".format(infolist))
        fw = tuple(infolist[1].split(".", 1))
        cdprint(fncname + "fw: '{}'".format(fw))

        gglobs.GSFirmware = fw

        fw0 = fw[0]
        fw1 = fw[1][0:2]


        if   fw0 < "6":
            gglobs.GS_DeviceDetected   = "Old"
            gglobs.GSfwtype = None

            msg = "Gamma-Scout versions older than Classic are not supported by GeigerLog"
            dprint(fncname + msg, debug=True)
            efprint(msg)
            setIndent(0)
            return

        elif fw0 == "6" and (fw1 > "017" and fw1 < "90"):
            gglobs.GS_DeviceDetected = "Classic"
            gglobs.GSfwtype = "610"

            gglobs.GSSerialNumber   = infolist[2]
            gglobs.GSusedMemory     = int(infolist[3], 16)
            dt                      = infolist[4] + " " + infolist[5]   # 14.08.2019 18:37:00

        elif fw0 == "7" and (fw1 >= "01" and fw1 <= "02"):
            gglobs.GS_DeviceDetected = "Online"
            gglobs.GSfwtype = "702"

            gglobs.GSSerialNumber   = infolist[3]
            gglobs.GSusedMemory     = int(infolist[4], 16)
            dt                      = infolist[5] + " " + infolist[6]   # 14.08.2019 18:37:00

        elif fw0 == "7" and (fw1 >= "03"):
            gglobs.GS_DeviceDetected = "Online"
            gglobs.GSfwtype = "703"

            gglobs.GSSerialNumber   = infolist[2]
            gglobs.GSusedMemory     = int(infolist[4], 16)
            dt                      = infolist[5] + " " + infolist[6]   # 14.08.2019 18:37:00

        else:
            gglobs.GS_DeviceDetected = "OnlineX"
            gglobs.GSfwtype = "999"

            gglobs.GSSerialNumber   = infolist[2]
            gglobs.GSusedMemory     = int(infolist[4], 16)
            dt                      = infolist[5] + " " + infolist[6]   # 14.08.2019 18:37:00

        wprint(fncname + "Firmware: fw:{}  GS_DeviceDetected:{}  GSfwtype:{}".format(fw, gglobs.GS_DeviceDetected, gglobs.GSfwtype))

        # if   gglobs.GSfwtype == "610":
            # gglobs.GSSerialNumber   = infolist[2]
            # gglobs.GSusedMemory     = int(infolist[3], 16)
            # dt                      = infolist[4] + " " + infolist[5]   # 14.08.2019 18:37:00

        # elif gglobs.GSfwtype == "702":
        #     gglobs.GSSerialNumber   = infolist[3]
        #     gglobs.GSusedMemory     = int(infolist[4], 16)
        #     dt                      = infolist[5] + " " + infolist[6]   # 14.08.2019 18:37:00

        # elif gglobs.GSfwtype == "703":
        #     gglobs.GSSerialNumber   = infolist[2]
        #     gglobs.GSusedMemory     = int(infolist[4], 16)
        #     dt                      = infolist[5] + " " + infolist[6]   # 14.08.2019 18:37:00

        # elif gglobs.GSfwtype == "999": # just guessing
        #     gglobs.GSSerialNumber   = infolist[2]
        #     gglobs.GSusedMemory     = int(infolist[4], 16)
        #     dt                      = infolist[5] + " " + infolist[6]   # 14.08.2019 18:37:00

        # else: #gglobs.GS_DeviceDetected == "Old", gglobs.GSfwtype = None
        #     msg = "Gamma-Scout versions older than Classic are not supported by GeigerLog"
        #     dprint(fncname + msg, debug=True)
        #     efprint(msg)
        #     setIndent(0)
        #     return

        try:
            timestamp   = time.mktime(datetime.datetime.strptime(dt, "%d.%m.%y %H:%M:%S").timetuple())
            device_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            edprint(fncname +  "Exception timestamp: ", e)
            device_time = "Failure"
        gglobs.GSDateTime       = device_time

    setIndent(0)


def GSgetCalibData():
    """get the Gamma-Scout internal calibration data"""

    """
    # 'c' dumps internal calibration data

    from an old file produced with Gamma-Scout software:
        b0 07 0078
        0b000000a4f8a29c3b01
        48010000450783fa1c02
        77040000db06fcf91c02
        ce110000ca6918fe7602
        de5a0000eb26b5fb5802
        9e050100df1f27ff6702
        e0ff1f00bf038efdb202


    produced by this function on a Gamma-Scout Online firmware 7.02:
        GAMMA-SCOUT SoftCal gueltig
        b0 00 07 7e 00
        cd0900001a05f6da2d00
        9a210000c1e1acb12d00
        9a7d00002f0995c63c00
        00a0020002009af24b00
        9a46080004001cc23c00
        c47d130085010e9e2d00
        15dd4400990210b32d00
    """

    gglobs.GSCalibData  = None

    fncname = "GSgetCalibData: "
    wprint(fncname)
    setIndent(1)

    GSwriteToDevice(b'c', "get calib data")
    mode_response = GSreadAll() # decoded and stripped
    #wprint(fncname + "mode_response: ", mode_response)

    if mode_response > "": gglobs.GSCalibData = mode_response

    setIndent(0)


def GSgetVersionDetails():
    """writing 'v' to the counter, while in PC Mode, to return Details:
    like: ['', 'Version 6.10 d93683 4213 18.08.19 17:42:05'],
    then extract:
    - fw version
    - SN
    - number of used bytes in the protocol memory
    - date and time
    Valid in PC mode up to fw 6.1x
    """

    gglobs.GSinPCmode   = False
    version             = None

    fncname = "GSgetVersionDetails: "

    dprint(fncname)
    setIndent(1)

    GSclearPipeline()
    # print("GSclearPipeline")
    GSgetMode()
    # print("GSgetMode")
    if gglobs.GScurrentMode == "Failure": return False

    if not gglobs.GScurrentMode == "PC":       # if not in PC Mode then switch to it
        GSsetModePC()
        # print("GS  set Mode")
        dprint(fncname + "1st: Device is in {} Mode".format(gglobs.GScurrentMode))
        GSgetMode() # now to get the version
        # print("GSgetMode")
        if gglobs.GScurrentMode == "Failure": return False
    else:
        dprint(fncname + "Device is in {} Mode".format(gglobs.GScurrentMode))

    GSextractExtendedInfo(gglobs.GSversion)
    # print("GSextractExtendedInfo")

    setIndent(0)

    return True


def GSreadMemoryData(saveToBin=False, bytecount=None):
    """read data from the Gamma Scout device"""

    fncname = "GSreadMemoryData: "

    vprint(fncname)
    setIndent(1)

    QtUpdate()

    start       = time.time()
    devicedata  = GSreadAll(bytecount=bytecount)
    dtime       = time.time() - start
    data        = devicedata.strip()
    dumpdata    = data.split("\r\n")

    wprint(fncname + "devicedata: type: {:16s},  total length: {}".format(str(type(devicedata)), len(devicedata)))
    wprint(fncname + "dumpdata:   type: {:16s},  total length: {}".format(str(type(dumpdata)),   len(dumpdata)))
    #wprint(fncname + "Data (devicedata after stripping and decoding):\n{}".format(data)) # too much data

    lendevdata  = int(len(dumpdata) * 64  / 2)                   # transfer in 7bit format! takes 2 bytes for 1 byte
    msg = "Got {} byte-values in {:0.1f} s -->  {:0.1f} kBytes/s".format(lendevdata, dtime, lendevdata / dtime / 1000)
    vprint(fncname + msg)
    fprint(msg)

    QtUpdate()

    if saveToBin:
        # write device data to bin blob of database
        newdevicedata  = str(gglobs.GSversion)   + "\n\n" # make empty line between version and calib data
        newdevicedata += str(gglobs.GSCalibData) + "\n\n" # make empty line between version and dump data
        # need type 'str' for saving to database
        if   isinstance(devicedata, str):   newdevicedata += devicedata
        elif isinstance(devicedata, bytes): newdevicedata += devicedata.decode("UTF-8")
        else:                               newdevicedata += "Cannot read the dat data; possibly not of Gamma-Scout origin"

        gsup_sql.DB_insertBin(gglobs.hisConn, newdevicedata)

    setIndent(0)

    return dumpdata


#
# Public Functions
#

def GSmakeHistory(source):  # source == "GSDevice" oder "GSDatFile"
    """read the history from a Gamma-Scout device or dump-file"""

    startMH = time.time()
    fncname = "GSmakeHistory: "

    dprint(fncname + "make Gamma-Scout history from source: ", source)
    setIndent(1)

    error           = 0         # default: no error
    message         = ""        # default: no message

# get data from Gamma-Scout device
    if source == "GSDevice":
        if not gglobs.Devices["GammaScout"][CONN] :
            msg = "Gamma-Scout device not connected"
            dprint(fncname + msg)
            setIndent(0)
            return -1, msg

        GSsetModePC()
        ##fprint("PC mode set after {:0.3f} sec".format(time.time() - startMH))

        # find the maxbytes value
        dprint(fncname + "# find the maxbytes value")
        GSgetVersionDetails() # to update GSusedMemory
        ##fprint("Got version details after {:0.3f} sec".format(time.time() - startMH))

        # when in PC mode: writing 'b' dumps protocol memory
        # (up to fw 6.1x; but apparently in all other modes too!)
        GSwriteToDevice(b'b', "Dump Data")
        dumpdata = GSreadMemoryData(saveToBin=True, bytecount= gglobs.GSusedMemory * 2) # *2 because 7 bit serial code
        ##fprint("Done downloading after {:0.3f} sec".format(time.time() - startMH))

        dbheader        = "File created by reading history from device"
        dborigin        = "Download from device"
        data_originDB   = (stime(), gglobs.Devices["GammaScout"][DNAME])
        dbdevice        = "{}".format(data_originDB[1])


# get data from a GammaScout *.dat file
    elif source == "GSDatFile":

        vprint("Make History as Database *.hisdb file from GS *.dat file: ", gglobs.datFilePath)

        dumpdata = GSreadDataFromFile(gglobs.datFilePath)

        for a in dumpdata[:10]:  wprint(a)
        wprint("...")
        for a in dumpdata[-10:]: wprint(a)

        # get version and more
        GSextractExtendedInfo(dumpdata[0])

        dbheader        = "File created by reading history from *.dat file"
        dborigin        = gglobs.datFilePath
        data_originDB   = (stime(), gglobs.datFilePath)
        dbdevice        = "Data read from file"


# Programming error
    else:
        printProgError(fncname + "Programming Error - wrong source: ", source)
###########end get data #######################################################

    hisbytes = GSconvertDumpToBinList(dumpdata)

    if len(hisbytes) == 0:
        error   = -1
        message = "No valid data found!"
        dprint(message)

    else:
    # parse HIST data
        gglobs.HistoryDataList      = []
        gglobs.HistoryParseList     = []
        gglobs.HistoryCommentList   = []

        GSgetParsedHistory(hisbytes, maxbytes=gglobs.GSusedMemory)
        ##fprint("Done Convert & Parsing after {:0.3f} sec".format(time.time() - startMH))

    # add headers
        dbhisClines    = [None] * 3
        #                  ctype    jday, jday modifier to use time unmodified
        dbhisClines[0] = ["HEADER", None, "0 hours", dbheader]
        dbhisClines[1] = ["ORIGIN", None, "0 hours", dborigin]
        dbhisClines[2] = ["DEVICE", None, "0 hours", dbdevice]

    # write to database
        gsup_sql.DB_insertDevice        (gglobs.hisConn, *data_originDB)
        gsup_sql.DB_insertComments      (gglobs.hisConn, dbhisClines)
        gsup_sql.DB_insertComments      (gglobs.hisConn, gglobs.HistoryCommentList)
        gsup_sql.DB_insertData          (gglobs.hisConn, gglobs.HistoryDataList)
        gsup_sql.DB_insertParse         (gglobs.hisConn, gglobs.HistoryParseList)

        fprint("Got {} records".format(len(gglobs.HistoryDataList)))
        ##fprint("Done Make History after {:0.3f} sec".format(time.time() - startMH))

    GSsetModeNormal()
    ##fprint("Done setting Normal mode after {:0.3f} sec".format(time.time() - startMH))

    setIndent(0)
    return error, message


def GSsaveDatDataToDatFile():
    """get the Gamma-Scout data from the database and save to *.dat file"""

    fncname = "GSsaveDatDataToDatFile: "

    if gglobs.hisConn == None:
        gglobs.exgg.showStatusMessage("No data available")
        return

    setBusyCursor()

    fprint(header("Save History Data to *.dat File"))
    fprint("from: {}\n".format(gglobs.hisDBPath))
    vprint(fncname)
    setIndent(1)

    hist = gsup_sql.DB_readBinblob(gglobs.hisConn)
    vprint(fncname + "hist: type: ", type(hist))
    if hist == None:
        msg = "No history dat data found in this database"
        vprint(fncname + msg)
        efprint(msg)
        setIndent(0)
        return

    # need type 'bytes' for binary saving
    if   isinstance(hist, str):     newhist = bytes(hist, 'utf-8')
    elif isinstance(hist, bytes):   newhist = hist
    else:                           printProgError() # ends program

    newpath = gglobs.hisDBPath + ".dat"
    writeBinaryFile(newpath, newhist)
    msg = "saved as file: " + newpath
    vprint(fncname + msg)
    fprint(msg)

    setIndent(0)
    setNormalCursor()


def GSshowDatData(*args):
    """Show Gamma-Scout type dat Data from the database table bin"""

    fncname = "GSshowDatData: "

    if gglobs.hisConn == None:
        gglobs.exgg.showStatusMessage("No data available")
        return

    setBusyCursor()

    fprint(header("Show History Dat Data"))

    hist = gsup_sql.DB_readBinblob(gglobs.hisConn)
    #wprint(fncname + "hist:\n", hist)
    if hist == None:
        efprint("No history dat data found in this database")
    else:
        if   isinstance(hist, str):   newhist = hist
        elif isinstance(hist, bytes): newhist = hist.decode("UTF-8")
        else:                         newhist = "Cannot read the dat data; possibly not of Gamma-Scout origin"

        fprint(newhist)

    setNormalCursor()


def getValuesGammaScout(varlist):
    """the GS "heartbeat" used for logging"""

    global cpmcalc, cpmLogfreq

    start = time.time()

    fncname   = "getValuesGammaScout: "
    cdprint(fncname, varlist)
    setIndent(1)

    alldata   = {}
    validflag = True
    xtra      = 0
    counts    = 0

    # expected response: 'I012c00088e' : bytecount = len('I012c00088e') + CRLF = 13
    resp = GSreadAll(waittime=0.1)

    if not (len(resp) == 11 and resp[0] == "I"): # wrong data; ignore
        validflag = False

    else:
        try:    xtra      = int(resp[1:5], 16)
        except: validflag = False

        try:    counts    = int(resp[5:], 16)
        except: validflag = False
        #print("getValuesGammaScout: resp: ", resp, type(resp), ", counts: ", counts, ", xtra: ", xtra)

        if validflag:
            cpmcalc = np.append(cpmcalc, counts)[-cpmLogfreq:] # append, but then take last cpmLogfreq values only
            cpi     = float(np.sum(cpmcalc))
            #print("getValuesGammaScout: cpmcalc: ", cpmcalc, ", cpi: ", cpi)

            if varlist != None:
                for vname in varlist:
                    if   vname in ("CPM", "CPM1st", "CPM2nd", "CPM3rd"):
                        cpm             = cpi
                        cpm             = scaleVarValues(vname, cpm, gglobs.ValueScale[vname])
                        alldata.update(  {vname: cpm})

                    elif vname in ("CPS", "CPS1st", "CPS2nd", "CPS3rd"):
                        cps             = counts
                        cps             = scaleVarValues(vname, cps, gglobs.ValueScale[vname] )
                        alldata.update(  {vname: cps})

                    elif vname in ("Xtra"):
                        xtra            = xtra
                        xtra            = scaleVarValues(vname, xtra, gglobs.ValueScale[vname] )
                        alldata.update(  {vname: xtra})

    setIndent(0)
    vprintLoggedValues(fncname, varlist, alldata, (time.time() - start) * 1000)

    return alldata


def GSreboot():
    """Do a Gamma-Scout Reboot (Warmstart) by sending 'N' in PC mode"""

    fncname = "GSreboot: "

    fprint(header("Gamma-Scout Reboot (Warm-start)"))
    QtUpdate()

    vprint(fncname)
    setIndent(1)

    GSclearPipeline()
    mode    = GSgetMode()
    newmode = None

    if mode == "Online":
        GSsetModeNormal() # must set back to Normal mode
        GSclearPipeline()
        mode    = GSgetMode()
        newmode = None

    if mode == "Normal":
        ok = GSwriteToDevice(b'P', "set to PC mode")
        if ok:
            response = GSreadAll()
            wprint(fncname + "response: '{}'".format(response))
            if 'PC-Mode gestartet' in response:
                newmode = "PC"
            else:
                wprint(fncname + "Failure starting PC Mode; response: '{}'".format(response))
        else:
            wprint(fncname + "Failure when writing 'P' to device")

    elif mode == "PC":
        newmode = "PC"
        wprint(fncname + "already in mode: '{}'".format(newmode))

    else:
        wprint(fncname + "unrecognized mode: '{}'".format(mode))

    if newmode == "PC":
        GSwriteToDevice(b'N', "do a reboot")
        time.sleep(1)           # a byte b'\x00' will be waiting
        GSsetModeNormal()       # clears the waiting byte

        mode    = GSgetMode()
        wprint(fncname + "in mode: '{}'".format(mode))
        fprint("Reboot completed")

        gglobs.GScurrentMode = mode
    else:
        efprint("Could not reboot; try repeating and/or unplug/replug the device")
        gglobs.GScurrentMode = newmode

    setIndent(0)


def GSgetMode():
    """is Gamma-Scout in mode Standard, Online, PC, (or Failure)"""

    gglobs.GSversion    = None

    fncname = "GSgetMode: "
    wprint(fncname)
    setIndent(1)

    GSwriteToDevice(b'v', "get current mode")
    response = GSreadAll() # decoded and stripped
    #wprint(fncname + "response: ", response)

    if   "Standard" in response:   mode = "Normal"
    elif "Online"   in response:   mode = "Online"
    elif "Version"  in response:
                                   mode = "PC"
                                   gglobs.GSversion = response
    else:                          mode = "response: '{}'".format(response)

    wprint(fncname + "mode: ", mode)
    gglobs.GScurrentMode = mode

    setIndent(0)

    return mode


def GSsetMode(mode):
    """Set the Gamma-Scout device to Mode: 'Normal', 'PC', 'Online'"""
    # set in ggeiger, line 502ff

    setBusyCursor()

    fncname = "GSsetMode: "

    msg = "Set Gamma-Scout to {} Mode".format(mode)
    fprint(header(msg))
    dprint(fncname + msg)
    setIndent(1)
    QtUpdate() # setting device may take some time

    rmode = None
    if   mode == "Normal":    rmode = GSsetModeNormal()
    elif mode == "PC":        rmode = GSsetModePC    ()
    elif mode == "Online":
        selection = GSsetOnline()
        if selection == (None, None):
            msg = "Change to Online Mode canceled"
            dprint(fncname + msg)
            fprint(msg)
        else:
            interval_code = selection[0]
            rmode = GSsetModeOnline(interval_code)
            msg = "Online Mode is set with counter log cycle of {} sec".format(selection[1])
            dprint(fncname + msg)
            fprint(msg)
    else:
        printProgError("GSsetMode(mode), mode: ", mode)

    if rmode is not None:
        if rmode in ("Normal", "PC", "Online"): fprint ("Gamma-Scout is in {} Mode".format(rmode))
        else:                                   efprint("Failure setting mode: {}".format(mode))

    setNormalCursor()
    setIndent(0)


def GSsetModeNormal():
    """writes 'X' to the counter to switch from PC Mode back to Normal Mode;
    response: when counter was in PC Mode       : 'PC-Mode beendet'
              when counter was in Normal Mode   : ''
    return: on success: True    (and gglobs.GSinPCmode = False)
            else      : False   (and gglobs.GSinPCmode = Unchanged)
    valid up to fw 6.1x"""

    fncname = "GSsetModeNormal: "

    dprint(fncname)
    setIndent(1)

    GSclearPipeline()
    mode    = GSgetMode()
    newmode = None

    if mode == "PC":
        ok = GSwriteToDevice(b'X', "exit PC mode")
        if ok:
            response = GSreadAll()
            wprint(fncname + "response: '{}'".format(response))

            if   'PC-Mode beendet' in response: newmode = "Normal"
            else:                               wprint(fncname + "Failure ending PC Mode; response: '{}'".format(response))

        else:
            wprint(fncname + "Failure when writing 'X' to device")

    elif mode == "Online":
        ok = GSwriteToDevice(b'X', "exit Online mode")
        if ok:
            response = GSreadAll()
            wprint(fncname + "response: '{}'".format(response))
            if   'Online-Mode beendet' in response: newmode = "Normal"
            else:                                   wprint(fncname + "Failure ending Online Mode; response: '{}'".format(response))

        else:
            wprint(fncname + "Failure when writing 'X' to device")

    elif mode == "Normal":
        newmode = "Normal"
        wprint(fncname + "already in mode: '{}'".format(newmode))

    else:
        wprint(fncname + "unrecognized mode: '{}'".format(mode))

    gglobs.GScurrentMode = newmode

    setIndent(0)
    return newmode


def GSsetModePC():
    """Set Gamma-Scout into PC Mode by sending P to device (same as pressing
    PC button at device) expecting answer: 'PC-Mode gestartet'
    return: on success: True    (and gglobs.GSinPCmode = True)
            else      : False   (and gglobs.GSinPCmode = unchanged)
    """

    fncname = "GSsetModePC: "
    success = False
    vprint(fncname)
    setIndent(1)

    GSclearPipeline()
    mode    = GSgetMode()
    newmode = None

    if mode == "Online":
        GSsetModeNormal() # must set back to Normal mode
        GSclearPipeline()
        mode    = GSgetMode()
        newmode = None

    if mode == "Normal":
        ok = GSwriteToDevice(b'P', "set to PC mode")
        if ok:
            response = GSreadAll()
            wprint(fncname + "response: '{}'".format(response))
            if 'PC-Mode gestartet' in response:
                newmode = "PC"
            else:
                wprint(fncname + "Failure starting PC Mode; response: '{}'".format(response))

        else:
            wprint(fncname + "Failure when writing 'P' to device")

    elif mode == "PC":
        newmode = "PC"
        wprint(fncname + "already in mode: '{}'".format(newmode))

    else:
        wprint(fncname + "unrecognized mode: '{}'".format(mode))

    gglobs.GScurrentMode = newmode

    setIndent(0)
    return newmode


def GSsetOnline():
    """Select settings for the Gamma-Scout Online mode"""

    fncname = "GSsetOnline: "

    dprint(fncname)
    setIndent(1)

    # GS interval
    lqcb = QLabel("Gamma-Scout Log cycle [sec]")
    lqcb.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    # The drop-down selector for the log cycle
    qcb = QComboBox()
    qcb.setToolTip("Select the log cycle to be used by the counter")
    qcb.setEnabled(True)
    for intv in ["2", "10", "30", "60", "120", "300"]:
        qcb.addItems([intv])

    graphOptions=QGridLayout()
    graphOptions.setContentsMargins(10,10,10,10) # spacing around the graph options
    graphOptions.addWidget(lqcb, 0, 0)
    graphOptions.addWidget(qcb,  0, 1)

    # Dialog box
    d = QDialog()
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setFont(gglobs.fontstd)
    d.setWindowTitle("Gamma-Scout Log Cycle")
    d.setWindowModality(Qt.WindowModal)
    d.setMinimumWidth(300)

    # Buttons
    bbox = QDialogButtonBox()
    bbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok )
    bbox.accepted.connect(lambda: d.done(100))
    bbox.rejected.connect(lambda: d.done(0))        # same as ESC key

    gglobs.btn = bbox.button(QDialogButtonBox.Ok)
    gglobs.btn.setEnabled(True)

    layoutV = QVBoxLayout(d)
    layoutV.addLayout(graphOptions)
    layoutV.addWidget(bbox)

    if gglobs.logging:         # no change of parameters when logging
        gglobs.btn  .setEnabled(False)

    retval = d.exec()
    #print("retval:", retval)

    if retval != 100:
        # ESCAPE pressed or Cancel Button
        #dprint(fncname + "Canceling; settings unchanged")
        i1 = None
        i2 = None

    else:
        # OK pressed
        i1 = qcb.currentIndex()
        i2 = qcb.currentText()
        #dprint(fncname + "Selection: code:{} text:{}".format(i1, i2))

    #print("qcb: ", i1, " ", i2)
    setIndent(0)

    return (i1, i2)



def GSsetModeOnline(interval="0"):
    """Set Gamma-Scout into Online Mode"""

    #~'s' requests online status and pulses
    #~'0'-'9' sets online interval
    # using this code:
    #

    """
    ok = GSwriteToDevice(b's', "requests online status and pulses")
    result = GSreadAll()
    for j in [b"0", b"1", b"2", b"3", b"4", b"5", b"6", b"7", b"8", b"9"]:
        print("j: ", j)
        ok = GSwriteToDevice(j, "sets online interval")
        result = GSreadAll()
        ok = GSwriteToDevice(b's', "requests online status and pulses")
        result = GSreadAll()
        counter = 0
        while True:
            result = GSreadAll()
            if result > "": counter += 1
            time.sleep(0.3)
            if counter > 10: break
    """
    #
    # gives this result:
    # Writing 1 bytes data 'b'0'' -- purpose: 'sets online interval'
    # Writing 1 bytes data 'b's'' -- purpose: 'requests online status and pulses'
    # Read data: decoded: len:15  'S00020000000003'                             =>     S   2    3 =>            ???
    # danach alle 2 s like 'I0002000013',                                       =>     I   2   19 => 60s: 570
    #
    # Writing 1 bytes data 'b'1'' -- purpose: 'sets online interval'
    # Writing 1 bytes data 'b's'' -- purpose: 'requests online status and pulses'
    # Read data: decoded: len:15  'S000a0004000019'                             =>     S  10   25 => /4*60= 375 ?
    # danach alle 10 s like 'I000a000044'                                       =>     I  10   68 => 60s: 408
    #
    # Writing 1 bytes data 'b'2'' -- purpose: 'sets online interval'
    # Writing 1 bytes data 'b's'' -- purpose: 'requests online status and pulses'
    # Read data: decoded: len:15  'S001e0004000028'                             =>     S  30   40 => /4*60= 600 ?
    # danach alle 30 s like 'I001e0000ea'                                       =>     I  30  234 => 60e: 468
    #
    # Writing 1 bytes data 'b'3'' -- purpose: 'sets online interval'
    # Writing 1 bytes data 'b's'' -- purpose: 'requests online status and pulses'
    # Read data: decoded: len:15  'S003c0004000022'                             =>     S  60   34 => /4*60= 510 ?
    # danach alle 1 min like 'I003c0001b6'                                      =>     I  60  438 => 60s: 438
    #
    # Writing 1 bytes data 'b'4'' -- purpose: 'sets online interval'
    # Writing 1 bytes data 'b's'' -- purpose: 'requests online status and pulses'
    # Read data: decoded: len:15  'S00780004000022'                             =>     S 120   34 => /4*60= 510 ?
    # danach alle 2 min like 'I007800037a'                                      =>     I 120  890 => 60s: 445
    #
    # Writing 1 bytes data 'b'5'' -- purpose: 'sets online interval'
    # Writing 1 bytes data 'b's'' -- purpose: 'requests online status and pulses'
    # Read data: decoded: len:15  'S012c0004000028'                             =>     S 300   40 => /4*60= 600 ?
    # danach alle 5 min like 'I012c00086f'                                      =>     I 300 2159 => 60s: 432
    #
    # Writing 1 bytes data 'b'6'' -- purpose: 'sets online interval'
    # Writing 1 bytes data 'b's'' -- purpose: 'requests online status and pulses'
    # Read data: decoded: len:15  'S012c0004000021'                             =>     S 300   33 => /4*60= 495 ?
    # danach alle 5 min like 'I012c0008ca'                                      =>     I 300 2250 => 60s: 450
    #
    # Writing 1 bytes data 'b'7'' -- purpose: 'sets online interval'
    # Writing 1 bytes data 'b's'' -- purpose: 'requests online status and pulses'
    # Read data: decoded: len:15  'S012c0004000028'                             =>     S 300   40 => /4*60= 600 ?
    # danach alle 5 min like 'I012c000814'                                      =>     I 300 2068 => 60s: 413
    #
    # Writing 1 bytes data 'b'8'' -- purpose: 'sets online interval'
    # Writing 1 bytes data 'b's'' -- purpose: 'requests online status and pulses'
    # Read data: decoded: len:15  'S012c000400001a'                             =>     S 300   26 => /4*60= 390 ?
    # danach alle 5 min like 'I012c00088d'                                      =>     I 300 2189 => 60s: 437
    #
    # Writing 1 bytes data 'b'9'' -- purpose: 'sets online interval'
    # Writing 1 bytes data 'b's'' -- purpose: 'requests online status and pulses'
    # Read data: decoded: len:15  'S012c0004000027'                             =>     S 300   39 => /4*60= 585 ?
    # danach alle 5 min like 'I012c00088e'                                      =>     I 300 2190 => 60s: 438


    global cpmcalc, cpmLogfreq

    fncname = "GSsetModeOnline: "
    success = False
    vprint(fncname)
    setIndent(1)

    GSclearPipeline()
    mode    = GSgetMode()
    #print("1st getMode: ", mode)

    if mode == "PC":
        GSsetModeNormal() # must set back to Normal mode
        GSclearPipeline()
        mode    = GSgetMode()
        #print("2nd getMode: ", mode)

    newmode = None

    if mode == "Normal":
        ok = GSwriteToDevice(b'O', "set to Online mode")   # ok= b'I000200000d'
        #~ok = GSwriteToDevice(b'R', "set to Online mode") # ok= b'4,854 uSv/h'
        #~ok = GSwriteToDevice(b'D', "set to Online mode") # ok= b'0,000 uSv' # keine Änderung der werte???
        if ok:
            response = GSreadAll()
            wprint(fncname + "response on starting Online Mode: '{}'".format(response))

            if 'Online-Mode gestartet' in response or response.startswith("S0"): # response is: 'S000a0000000000'

                newmode = "Online"
                try:
                    GScycle    = int(response[1:5], 16) # default=10
                    cpmLogfreq = int(60 / GScycle)
                except:
                    GScycle    = 10
                    cpmLogfreq = 6

                gglobs.logCycle = 2 #GScycle
                cpmcalc         = np.full(cpmLogfreq, gglobs.NAN)
                gglobs.exgg.showTimingSetting(gglobs.logCycle)

            else:
                wprint(fncname + "Failure starting Online Mode; response: '{}'".format(response))
        else:
            wprint(fncname + "Failure when writing 'O' to device")

    elif mode == "Online":
        newmode = "Online"
        wprint(fncname + "already in mode: '{}'".format(newmode))

    else:
        wprint(fncname + "unrecognized mode: '{}'".format(mode))

    intervalbyte = bytes(str(interval), "utf-8")
    GSwriteToDevice(intervalbyte, "sets online interval t 2 sec")

    gglobs.GScurrentMode = newmode

    setIndent(0)
    return newmode


def setGSDateTime():
    """set the Gamma-Scount onboard-clock to the computer time"""

    setBusyCursor()

    txt = "Set Date&Time of Gamma-Scout Device"
    fprint(header(txt))

    QtUpdate()

    GSsetModePC()

    gsdatetime  = datetime.datetime.fromtimestamp(time.time() + 5) # add 5 sec to compensate for delay
    gstime      = gsdatetime.strftime("%d%m%y%H%M%S")
    bgstime     = bytes(gstime, "utf-8")
    wprint("setGSDateTime: bgstime: ", bgstime)

    #'t' prepares setting date and time in the form "DDMMYYhhmmss".
    GSwriteToDevice(b't',    "DateTime setting prep")
    response = GSreadAll() # response is empty
    #fprint("write b't'", response)

    GSwriteToDevice(bgstime, "DateTime setting exec")
    response = GSreadAll() # response is empty
    #fprint("write DateTime: {}".format(bgstime), response)

    GSgetVersionDetails()
    GSsetModeNormal()

    # fprint("Date & Time from device:",  gglobs.GSDateTime)
    # fprint("Date & Time from computer:", stime())
    fprint("Device Date & Time:",  gglobs.GSDateTime)
    fprint("Computer Date & Time:", stime())

    setNormalCursor()


def GSgetDeltaTime():
    """reads the DateTime from the device, converts into a number, and returns
    the delta time in sec with 1 sec precision"""

    rec = gglobs.GSDateTime

    if rec is None:
        return gglobs.NAN
    else:
        time_computer = longstime()
        time_device   = str(rec)
        try:    time_delta = round((mpld.datestr2num(time_computer) - mpld.datestr2num(time_device)) * 86400, 3)
        except: time_delta = gglobs.NAN
        #fprint("getGMC_DeltaTime: device:{}, computer:{}, Delta C./.D:{:0.3f}".format(time_device, time_computer, time_delta))
        return time_delta


def getInfoGammaScout(extended = False):
    """Info and extended info on the Gamma-Scout Device"""

    fncname = "getInfoGammaScout: "

    try:    fw = gglobs.GSFirmware[0] + "." + gglobs.GSFirmware[1]
    except: fw = "unknown"

    GSInfo  = "Configured Connection:        Port:'{}' Baud:{} Timeouts[s]: R:{} W:{}\n".format(
                                                gglobs.GSusbport,
                                                gglobs.GSbaudrate,
                                                gglobs.GStimeoutR,
                                                gglobs.GStimeoutW)

    if not gglobs.Devices["GammaScout"][CONN]: return GSInfo + "<red>Device is not connected</red>"

    GSInfo      += "Connected Device:             {}  Firmware: {}\n"                        .format(gglobs.Devices["GammaScout"][DNAME], fw)
    GSInfo      += "Configured Variables:         {}\n"                                      .format(gglobs.GSVariables)
    GSInfo      += getTubeSensitivities(gglobs.GSVariables)
    GSInfo      += getDeltaTimeMessage(GSgetDeltaTime(), gglobs.GSDateTime)

    if extended == True:
        GSInfo  += "\n"
        GSInfo  += "Connection Details:           Stopbits:{}  Bits-per-Byte:{}  Parity:{}\n".format(gglobs.GSstopbits, gglobs.GSbytesize, gglobs.GSparity)
        GSInfo  += "Device status:                {}\n".format(gglobs.GScurrentMode)
        GSInfo  += "Used Memory [bytes]:          {} (0x{:04X}), {:0.1%} of {} (free: {})\n".format(
                                                        gglobs.GSusedMemory, gglobs.GSusedMemory,            \
                                                        gglobs.GSusedMemory / gglobs.GSMemoryTotal,          \
                                                        gglobs.GSMemoryTotal,                                \
                                                        gglobs.GSMemoryTotal - gglobs.GSusedMemory,          \
                                                    )
        GSInfo  += "Serial Number:                {}\n".format(gglobs.GSSerialNumber)
        GSInfo  += "Configuration Variables:\n"
        GSInfo  += "- CPS*:                       Counts-Per-X_seconds\n"
        GSInfo  += "- CPM*:                       CPM as sum of CPS* over rolling 1 min interval (True CPM)\n"
        GSInfo  += "- X:                          interval of 10 s, 30 s, 1 min, 2 min, ..., 1 week\n"


    return GSInfo


def terminateGammaScout():
    """Terminate Gamma-Scout; switches device back into Normal Mode"""

    fncname = "terminateGammaScout: "

    dprint(fncname)
    setIndent(1)

    if gglobs.GSser != None:
        if not gglobs.GScurrentMode == "Normal":   GSsetModeNormal()
        try:
            gglobs.GSser.close()
            dprint(fncname + "Done")
        except Exception as e:
            exceptPrint(e, fncname + "Failed trying to terminate Gamma-Scout")
        gglobs.GSser  = None

    gglobs.Devices["GammaScout"][CONN]  = False
    gglobs.Devices["GammaScout"][DNAME] = None

    dprint(fncname + "Terminated")
    setIndent(0)


def initGammaScout():
    """Initialize Gamma-Scout; switches device into PC Mode."""


    ## local ###################################################################################
    def lcl_getGS_SerialConfig(device):
        """
        gets the USB-to-Serial port name and baudrate for GammaScout
        This tests for a match of USB's vid + pid associated with device. If match found,
        then it tests for proper communication checking with specific call/answers
        """

        # The USB-to-Serial chip is an FTDI chip (Vendor=0x0403, Product=0xd678).
        # lsusb output: https://www.johannes-bauer.com/linux/gammascout/
        #
        # output by: lsusb
        #   bcdUSB               2.00
        #   idVendor           0x0403 Future Technology Devices International, Ltd
        #   idProduct          0xd678
        #   iManufacturer           1 Dr Mirow
        #   iProduct                2 GammaScout USB

        fncname   = "initGammaScout - lcl_getGS_SerialConfig: "

        dprint(fncname + "for device: '{}'".format(device))
        setIndent(1)

        portfound   = None
        baudfound   = None
        tmplt_port  = "Checking Port:{},  device:{}, product:{}, vid:{}, pid:{}"
        tmplt_match = "Found Chip ID match for '{}' at: Port:'{}' - vid:0x{:04x}, pid:0x{:04x}"
        tmplt_found = "Found: Port:{}, Baud:{}, description:{}, vid:0x{:04x}, pid:0x{:04x}"

        ports = getPortList(symlinks=False)

        if gglobs.gstesting:
            # SIMULATION ONLY !!!
            portfound = "/dev/ttyS91"
            baudfound = 9600
            cdprint(fncname + "SIMULATION: Port:{}, Baud:{}".format( portfound, baudfound))

        else:
            # testing for real devices
            for port in ports:
                if  port.vid == 0x0403 and port.pid == 0xd678:
                    dprint(fncname, tmplt_match.format(device, port.device, port.vid, port.pid))
                    baudrate = lcl_GS_autoBaudrate(port.device)
                    if baudrate is not None and baudrate > 0:
                        portfound = port.device
                        baudfound = baudrate
                        break

            if portfound is not None: cdprint(fncname + tmplt_found.format( portfound,
                                                                            baudfound,
                                                                            port.description,
                                                                            port.vid,
                                                                            port.pid))

        setIndent(0)
        return (portfound, baudfound)


    def lcl_GS_autoBaudrate(usbport):
        """Tries to find a proper baudrate by testing for successful serial
        communication at up to all possible baudrates, beginning with the
        highest"""

        # NOTE: the device port can be opened without error at any baudrate,
        # even when no communication can be done, e.g. due to wrong baudrate.
        # Therefore we test for successful communication by checking for the return
        # string on command 'v' containing 'Standard' or 'Online' (latest GS devices)
        #
        # return:   - on success, this baudrate will be returned.
        #           - a baudrate=0 will be returned when all communication fails.
        #           - on a serial error, baudrate=None will be returned.

        fncname = "initGammaScout - lcl_GS_autoBaudrate: "

        dprint(fncname + "Autodiscovery of baudrate on port: '{}'".format(usbport))
        setIndent(1)

        baudrates = gglobs.GSbaudrates
        baudrates.sort(reverse=True) # to start with highest baudrate
        cdprint(fncname + "baudrates: ", baudrates)

        for baudrate in baudrates:
            # print( usbport,
            #                     baudrate,
            #                     gglobs.GSbytesize,
            #                     gglobs.GSparity,
            #                     0.5,
            #                     0.5)

            try:
                with serial.Serial( usbport,
                                    baudrate,
                                    bytesize     =gglobs.GSbytesize,
                                    parity       =gglobs.GSparity,
                                    timeout      =0.5,
                                    write_timeout=0.5)      as ABRser:

                    bwrt = ABRser.write(b'v')
                    brec = ABRser.read(8)   # 8 is minimum of len(CRLF+(Standard, Online, Version)); may leave bytes in the pipeline
                    while True:
                        time.sleep(0.05)
                        cnt = ABRser.in_waiting
                        if cnt == 0: break  # while
                        brec += ABRser.read(cnt)
                    cdprint(fncname + "Trying baudrate: {:6d}, sending: 'v', getting: {}".format(baudrate, brec), debug=True)

                if b"Standard" in brec or b"Online" in brec or b"Version" in brec:
                    baudmsg = "SUCCESS with baudrate: {}".format(baudrate)
                    break  # for

            except Exception as e:
                exceptPrint(e, "")
                baudmsg  = "EXCEPTION in Serial communication with baudrate: {}".format(baudrate)
                baudrate = None
                break  # for

            baudmsg  = "FAILURE - No success at any baudrate"
            baudrate = 0

        dprint(fncname + baudmsg)
        setIndent(0)

        return baudrate

    ## end local ##################################################################################


    global cpmcalc, cpmLogfreq

    fncname = "initGammaScout: "

    dprint(fncname)
    setIndent(1)

    gglobs.Devices["GammaScout"][DNAME] = "GammaScout"

    # Gamma-Scout info on firmware & serial port settings.
    #   type #1: FW < 6.00:              2400,7,e,1
    #   type #2: 6.00 <= FW < 6.90:      9600,7,e,1
    #   type #3: FW >= 6.90:           460800,7,e,1

    if gglobs.GSusbport   == "auto" : gglobs.GSusbport  = None
    if gglobs.GSbaudrate  == "auto" : gglobs.GSbaudrate = 9600      # 2400 | 9600 | 460800
    if gglobs.GStimeoutR  == "auto" : gglobs.GStimeoutR = 3         # some responses of Gamma-Scout take almost 1 sec!
    if gglobs.GStimeoutW  == "auto" : gglobs.GStimeoutW = 1

    # next 3 settings will NOT change in code
    if gglobs.GSstopbits  == "auto" : gglobs.GSstopbits = 1                     # 1;    generic in pyserial
    if gglobs.GSbytesize  == "auto" : gglobs.GSbytesize = 7                     # 7;    specific to Gamma-Scout
    if gglobs.GSparity    == "auto" : gglobs.GSparity   = serial.PARITY_EVEN    # "E";  specific to Gamma-Scout

    if gglobs.gstesting:
        edprint("THIS IS A SIMULATION - (found 'gstesting' on CMD line)")
        gglobs.GSusbport    = "/dev/ttyS91"                                     # as set by socal command
        gglobs.GSbytesize   = 8                                                 # don't know how to re-configure socal
        gglobs.GSparity     = serial.PARITY_NONE                                # "N"; don't know how to re-configure socal

    if  gglobs.GSusbport == None:
        port, baud = lcl_getGS_SerialConfig("GammaScout")
        if port is None or baud is None:
            setIndent(0)
            return "A device {} was not detected.".format(gglobs.Devices["GammaScout"][DNAME])
        else:
            gglobs.GSusbport  = port
            gglobs.GSbaudrate = baud
            fprint("A device {} was detected at port: {} and baudrate: {}".format(
                                                                gglobs.Devices["GammaScout"][DNAME],
                                                                gglobs.GSusbport,
                                                                gglobs.GSbaudrate))

    else:
        fprint("A device {} was <b>user configured</b> for port: '{}'".format(
                                                                gglobs.Devices["GammaScout"][DNAME],
                                                                gglobs.GSusbport,))

        baudrate = lcl_GS_autoBaudrate(gglobs.GSusbport)
        if baudrate is not None and baudrate > 0:
            gglobs.GSbaudrate = baudrate
            fprint("A device {} was detected at port: {} and baudrate: {}".format(
                                                                            gglobs.Devices["GammaScout"][DNAME],
                                                                            gglobs.GSusbport,
                                                                            gglobs.GSbaudrate))
        else:
            return "A device {} was not detected at user defined port '{}'.".format(
                                                                            gglobs.Devices["GammaScout"][DNAME],
                                                                            gglobs.GSusbport)

    cpmLogfreq   = 6                                # number of measurements taken per minute (6 when interval is 10sec)
    cpmcalc      = np.full(cpmLogfreq, gglobs.NAN)  # for storing last 6 * 10 sec of CP10sec values, fill with NANs

    # try to make the serial connection
    gglobs.GSser = None
    try:
        gglobs.GSser = serial.Serial(port           = gglobs.GSusbport,
                                     baudrate       = gglobs.GSbaudrate,
                                     bytesize       = gglobs.GSbytesize,
                                     parity         = gglobs.GSparity,
                                     stopbits       = gglobs.GSstopbits,
                                     timeout        = gglobs.GStimeoutR,
                                     write_timeout  = gglobs.GStimeoutW,
                                    )

    except serial.SerialException as e:
        msg = "SerialException on connecting to port: '{}'".format(gglobs.GSusbport)
        exceptPrint(e, msg)
        errmessage1 = msg

    except Exception as e:
        msg  = "Did you try Gamma-Scout-Simulation but forgot GeigerLog command 'gstesting'?"
        exceptPrint(e, msg)
        errmessage1 = str(e) + "\n" + msg


    if gglobs.GSser == None:
        # FAILURE making Serial Connection
        terminateGammaScout()
        rmsg = "ERROR: " + errmessage1.replace('[Errno 2]', '')
        gglobs.Devices["GammaScout"][DNAME] = None

    else:
        # Serial Connection is made.
        dprint(fncname + "Serial Connection made: ", str(gglobs.GSser)[36:]) # ignore initial 'Serial<id=0x7f1b0ee8b520, open=True>'

        ok = GSgetVersionDetails()
        if not ok:
            errmessage1 = "Communication problem"
            edprint(fncname + errmessage1, debug=True)
            terminateGammaScout()
            gglobs.Devices["GammaScout"][DNAME] = None
            return errmessage1

        # get Gamma-Scout internal Calib data
        GSgetCalibData()
        GSsetModeNormal()

        gglobs.Devices["GammaScout"][CONN]  = True
        gglobs.Devices["GammaScout"][DNAME] = "GammaScout" + " " + gglobs.GS_DeviceDetected

        if gglobs.GSVariables    == "auto": gglobs.GSVariables    = "CPM3rd, CPS3rd, Xtra"

        setLoggableVariables("GammaScout",  gglobs.GSVariables)

        dprint(fncname + "device detected: '{}'".format(gglobs.Devices["GammaScout"][DNAME]))
        rmsg = ""

    setIndent(0)

    return rmsg


