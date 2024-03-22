#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
GLsermon.py - Serial Monitor to read from and write to a USB-to-Serial Connection
              with Extra-Support for GMC counter

    Start with: 'GLsermon.py -h'                          to get Help Info")
    Start with: 'GLsermon.py -P <Port> -B <Baudrate>'     to set Port and Baudrate")
    Start with: 'GLsermon.py -P <Port> -B <Baudrate> gmc' to set Port and Baudrate for any GMC counter")
    Stop  with: CTRL-C")
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
__version__         = "1.1"

import sys, os, io, time, datetime  # basic modules
import serial                       # handling the serial port
import serial.tools.list_ports      # allows listing of serial ports
import threading                    # thread to read the keyboard
import getopt                       # parse command line for options and commands
import traceback                    # for traceback on error; used in: exceptPrint

helpOptions = """
Usage:  GLsermon.py [Options] [Commands]

All serial communication will be logged to file 'GLsermon.log'. You'll find it
in the directory where GLsermon was started from.

Options:
    -h, --help          Show this help and exit.
    -d, --debug         Run with printing debug info.
                           Default: no debug
    -V, --Version       Show version and exit.
    -P, --Port          Define USB-to-Serial port:
                           on Linux   = /dev/ttyUSBx, x = 0, 1, 2, ...
                           on Windows = COMx, x = 0, 1, 2, ...
                           Default: /dev/ttyUSB0
    -B, --Baudrate      Define Baudrate:
                           57600, 115200, ...
                           Default: 115200
    -L, --List          Show available USB-to-Serial ports
                           Ports existing only as Symlinks are also shown
    -T, --Term          Termination characters when sending:
                           'CR' for Carriage Return,
                           'LF' for Linefeed,
                           or for both 'CRLF' or 'LFCR'.
                           Default: No termination characters.

Commands:
    gmc                 To use GLsermon with GMC Geiger counters.

                          -----------------------

                                MINI MANUAL

Runtime guidance:
    Some devices, in particular GMC counters, may become non-responsive under
    certain conditions; commands 'clear' and 'reconnect' may be of help..

    clear:      Clears the serial connection pipeline
    reconnect:  If 'clear' does not help, try 'reconnect'. Repeat if no success.
                Last resort is restarting the counter.
    cmds:       Prints a list of all GMC commands
    help:       Prints out this help information during a run


Using GMC counters:
    To use GLsermon.py with GMC counters start with: (Note the 'gmc' at the end!)

            GLsermon.py -P <Port> -B <Baudrate> gmc

    This will activate some helpful extra GLsermon code when using GMC counters.

    *   No Termination characters are allowed and will automatically be suppressed.
    *   Enter commands in small caps and leave out all enclosing brackets.
        GLsermon will format them so that a command given as 'getver' will be send
        to the counter as '<GETVER>>' when you press the Enter key.
    *   Since GMC counters not only return ASCII text, but also binary data, the
        output becomes hard to read. GLsermon shows human-readable text (when
        possible), HEX values, Decimal values.

    Examples:
    The GMC counter response to 'getver'+ ENTER is similar to:
        Receive-Bytes:  15: GMC-500+Re 2.24
        Receive-Values HEX: 0x47 0x4D 0x43 0x2D 0x35 0x30 0x30 0x2B 0x52 0x65 0x20 0x32 0x2E 0x32 0x34
        Receive-Values DEC:   71   77   67   45   53   48   48   43   82  101   32   50   46   50   52
        Receive-Values ASC:    G    M    C    -    5    0    0    +    R    e         2    .    2    4

    command 'getcpm' + ENTER becomes <GETCPM>> and results in a response like:
        Receive-Bytes:   4: 3
        Receive-Values HEX: 0x00 0x00 0x02 0x33
        Receive-Values DEC:    0    0    2   51       --> results in: CPM = 2 * 256 + 51 = 563
        Receive-Values ASC:                  3

    command 'spir,0,0,0,16,0' becomes binary coded <SPIRXYZAB>> with X, Y, Z, A, B being bytes with a
        value from 0 ... 255. It will read the first 4k bytes of memory beginning at address 0x000.
        It results in a response like:
        Receive-Bytes: 4096: (Non-decodeable)
        Receive-Values HEX:
        01  01  00  00  02  01  00  01  02  00  00  02  00  00  01  01  01  00  00  00  00  00  00  55  AA  00  00  00  00  00  00  00
        55  AA  01  01  02  00  00  00  01  02  00  00  01  00  01  01  00  00  01  01  00  03  00  03  01  01  01  00  01  00  01  01
        00  01  00  01  03  00  00  01  00  00  01  00  00  00  00  00  00  00  01  00  01  02  00  01  01  00  01  01  03  00  00  00
        ... plus 61 more lines, folowed by DEC and ASCII lines

"""

gmc_commands = \
"""
GMC Counter Command List:
see: GQ-RFC1801 GMC Communication Protocol,
https://www.gqelectronicsllc.com/comersus/store/download.asp

No Parameter:
    cfgupdate
    ecfg
    factoryreset
    getcfg

    getcpm
    getcpmh
    getcpml
    getcps
    getcpsh
    getcpsl

    getdatetime
    getgyro
    getserial
    gettemp
    getver
    getvolt
    heartbeat0
    heartbeat1
    poweron
    poweroff
    reboot

2 Parameter: for counter 3XX series (2 Bytes)
    wcfg,A0,Ch                  A0 - address
                                Ch - Byte to write

3 Parameter: for counter 5XX, 6XX series (3 bytes)
    wcfg,Hi,Lo,Ch               Hi - High byte, Lo - Low byte of address
                                Ch - Byte to write

5 Parameter:
    spir,A2,A1,A0,L1,L0         A2,A1,A0 are three bytes address data, from MSB to LSB
                                L1,L0 are the data length requested, from MSB to LSB
                                The length normally not exceed 4096 bytes in each request.
                                for the first 2048 bytes use:    spir{0,0,0,8,0}
6 Parameter:
    setdatetime,Y,M,D,h,m,s     for: 2021-04-19 13:02:50 use:    setdatetime{21,4,19,13,2,50}

"""

ser         = None                   # the pointer to the serial connection
debug       = False                  # print output for debugging
Port        = "/dev/ttyUSB0"         # Port
Baud        = 115200                 # Baudrate
gmc         = False                  # flag to signal use of GMC counter
filename    = "GLsermon.log"         # file for saving all communication
Term        = ""                     # CR or LF or both (will be reset to "" for GMC counters!)


def longstime():
    """Return current time as YYYY-MM-DD HH:MM:SS.mmm, (mmm=millisec)"""

    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] # trim down to ms resolution


def exceptPrint(e, srcinfo):
    """Print exception details (errmessage, file, line no)"""

    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]    # which file?

    print("EXCEPTION: '{}' in file: '{}' in line {}".format(e, fname, exc_tb.tb_lineno))
    if srcinfo > "": print("{}".format(srcinfo))
    # print("EXCEPTION: Traceback:\n", traceback.format_exc()) # more extensive info


def printPortList(symlinks=True):
    """print serial port details. Include symlinks or not"""

    # Pyserial:
    # 'include_links (bool)' – include symlinks under /dev when they point to a serial port
    # lp = serial.tools.list_ports.comports(include_links=False) # default; no symlinks shown
    # lp = serial.tools.list_ports.comports(include_links=True)  # also shows symlinks like e.g. /dev/geiger

    fncname = "printPortList: "
    print("Listing all Ports:")

    try:
        lp = []
        lp = serial.tools.list_ports.comports(include_links=symlinks)
        lp.sort()
    except Exception as e:
        msg = fncname + "Exception on getting port list: {}".format(lp)
        exceptPrint(e, msg)
        # print(fncname + "Current list: ", lp)
        # lp = []

    for p in lp:
        print(fncname, p)


class KeyboardThread(threading.Thread):
    """keyboard-input-thread"""
    # initiate with: kthread = KeyboardThread(input_callback)

    def __init__(self, input_cbk = None, name='keyboard-input-thread'):
        self._is_running = True
        self.input_cbk = input_cbk
        super(KeyboardThread, self).__init__(name=name)
        self.start()

    def run(self):
        while self._is_running:
            self.input_cbk(input()) #waits to get input + Return
        sys.exit()

    def stop(self):
        self._is_running = False


def input_callback(inp):
    """evaluate the keyboard input"""
    # use in: kthread = KeyboardThread(input_callback)

    global ser

    if debug: print('DEBUG: You Entered:', inp)

    inpUP = inp.upper()

    if   inpUP == "CLEAR":                      # Clear (read all bytes from pipeline)
        clearPipeline()

    elif inpUP == "RECONNECT":                  # Reconnect (done in main loop)
        clearPipeline()
        ser.close()
        ser = None

    elif inpUP == "HELP":                       # print Help info
        print(helpOptions)

    elif inpUP == "CMDS":                       # print GMC commands set
        if gmc: print(gmc_commands)
        else:   print("Commands available only for GMC")

    else:                                       # write data to device and file
        if gmc:
            bw     = inpUP.strip().replace(" ", "")
            binval = ""
            if "," in bw:
                if debug: print("',' is at pos: ", bw.find(","))
                cmd = bw[0 : bw.find(",")]
                par = bw[bw.find(",") + 1 : ] # cut out segment to the right of first ','
                if debug: print("bw:'{}',  cmd:'{}', par:'{}'".format(bw, cmd, par))

                par = par.split(",")                      # split to list
                for b in par: binval += chr(int(b))       # combine to string
            else:
                cmd = bw

            sendb = "<" + cmd + binval + ">>"
            if debug: print("cmd:    ", cmd, ",  binval: ", binval)
            print(">>>>> NOTE: Byte values printed to a Terminal may look incomplete! Compare Length with expected length! <<<<<")

        else:
            sendb = inp + Term                         # other devices than GMC may need low cap!

        print("Sending: '{}'  (Length:{})".format(sendb, len(sendb)))
        ser.write(bytes(sendb, 'utf-8'))
        with open(filename, "a") as f:
            f.write("Sending : {}\n".format(sendb))


def clearPipeline():
    """read all bytes from serial until no more bytes"""

    br = b""
    while True:
        time.sleep(0.1)
        bw = ser.in_waiting
        if bw > 0:
            try:
                br += ser.read(1)
            except Exception as e:
                msg = "clearPipeline: Exception on reading: "
                exceptPrint(e, msg)
                sys.exit()

        else:
            if len(br) == 0: print("Clearing Pipeline -- it was empty")
            else:            print("Clearing Pipeline -- its content was: {}".format(br))
            break


def serConnect():
    """
    connect to the serial device
    return: True  : on success
            False : otherwise
    """

    global ser

    try:
        ser  = serial.Serial(Port, Baud, timeout = 0.5, write_timeout=0.5)
        return True
    except:
        return False


def main():
    """on errors return with message to print out"""

    global Port, Baud, Term, debug, gmc, ser

    fncname = "main: "

    print("+" * 100)

    # parse command line options (sys.argv[0] is progname)
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdVLP:B:T:", ["help", "debug", "Version", "List", "Port=", "Baudrate=", "Term="])
    except getopt.GetoptError as errmessage :
        # errmessage like "option -a not recognized"; results in exit
        return "ERROR: '{}', use './geigerlog -h' for help".format(errmessage)

    # processing the options
    for opt, optval in opts:
        if opt in ("-h", "--help"):
            return helpOptions

        elif opt in ("-V", "--Version"):
            return "Version: " + __version__

        elif opt in ("-d", "--debug"):
            debug    = True

        elif opt in ("-L", "--List"):       # which ports are available?
            #printPortList(symlinks=False)  # not including Sylinks
            printPortList(symlinks=True)    # including Sylinks
            return ""

        elif opt in ("-P", "--Port"):       # Port
            Port = optval

        elif opt in ("-B", "--Baudrate"):   # Baudrate
            Baud = optval

        elif opt in ("-T", "--Term"):       # Termination character for sending
            Term = ""                       # use Term = ""; none used for GMC counter
            if "CR" in optval.upper():      Term += "\r"
            if "LF" in optval.upper():      Term += "\n"

    # processing the args
    for arg in args:
        if arg.upper() == "GMC":
            gmc  = True
            TERM = ""                       # no Termination character when sending to GMC!

    print("Start with: 'GLsermon.py -h'                          to get Help Info")
    print("Start with: 'GLsermon.py -P <Port> -B <Baudrate>'     to set Port and Baudrate")
    print("Start with: 'GLsermon.py -P <Port> -B <Baudrate> gmc' to set Port and Baudrate for any GMC counter")
    print("Stop  with: CTRL-C")
    print()

    # Show command line
    if debug: print("DEBUG: {:15s}: sys.argv: {}".format("Command line", sys.argv))
    if debug: print("DEBUG: {:15s}: options: {}, commands: {}\n".format("Recognized", opts, args))

    print("Connecting with Port: {}, Baudrate: {} - ".format(Port, Baud), end = " ")

    if serConnect() :
        print("successful")
        clearPipeline()
    else:
        print("NOT successful, exiting")
        return "Failed making a Serial Connection - Check cable, plugs, connections"

    if debug: print("DEBUG: Connection: ", ser)

    with open(filename, "w") as f:  # to empty the file
        pass

    #start the Keyboard thread
    kthread = KeyboardThread(input_callback)

    print()
    try:
        while True:
            val = b""
            # print("begin ser: ", ser)
            while ser is None:
                print("No Serial-Connection --> reconnecting: ", end=" ")
                if serConnect():
                    print("successful")
                    break
                else:
                    print("NOT successful")

                time.sleep(1)

            while not os.access(Port , os.R_OK):
                print("Port: ", Port, " can NOT be read --> closing Serial-Connection")
                ser.close()
                ser = None
                time.sleep(1)
                break

            if ser is not None:
                try:
                    while True:
                        bw = ser.in_waiting
                        if bw > 0:
                            val += ser.read(bw)
                        else:
                            break
                        time.sleep(0.5)

                except OSError as e:
                    print(fncname + "OSError: ERRNO:{} ERRtext:'{}'".format(e.errno, e.strerror))
                    if e.errno == 5:
                        msg = fncname + "Serial connectiomn was lost"
                        print(msg)

                except Exception as e:
                    msg = fncname + "Failure in getting data"
                    exceptPrint(e, msg)

                if(val > b""):
                    if gmc: # adressing some GMC counter issues
                        print()

                        flag=""
                        msg = longstime()
                        msg += " :\nReceive-Bytes: {:3d}: ".format(len(val))
                        try:
                            msg += val.decode()
                        except:
                            msg += "(Non-decodeable) "
                            flag = "\n"
                            # msg += str(val)

                        msg += "\nReceive-Values HEX: " + flag
                        for i, a in enumerate(val):
                            msg += " {:02X} ".format(a)
                            if i % 32 == 31: msg += flag
                        msg += flag

                        msg += "\nReceive-Values DEC: " + flag
                        for i, a in enumerate(val):
                            msg += "{:3d} ".format(a)
                            if i % 32 == 31: msg += flag
                        msg += flag

                        msg += "\nReceive-Values ASC: " + flag
                        for i, a in enumerate(val):
                            if a > 0:   msg += "{:>3s} ".format(chr(a)) # an a == 0x00 results in 3 instead of 4 spaces???
                            else:       msg += "    "                   # a == 0x00
                            if i % 32 == 31: msg += flag
                        msg += flag

                        msg += "\n"

                        print(msg, end="")

                        with open(filename, "a") as f:
                            f.write(msg + "\n")
                        print()

                    else: # generic serial terminal
                        try:    msg  = val.decode()
                        except: msg  = "(Non-decodeable) " + str(val)
                        print(msg, end="")

                        with open(filename, "a") as f:
                            f.write(msg)

            time.sleep(0.01) # to reduce CPU load

    except Exception as e:
        msg = "Main loop"
        exceptPrint(e, msg)
        return "Exception: " + str(e)

    except KeyboardInterrupt:
        kthread.stop()
        #~print("kthread._is_running ?:", kthread._is_running)
        return "KeyboardInterrupt"


if __name__ == "__main__":
    print(main())
    print("\n")
    os._exit(123) # sys.exit() not helping

