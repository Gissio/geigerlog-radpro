#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
WiFiClient Devices - External devices which call GeigerLog's built-in web server
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

# Port Scanning:
# ~$ nmap  10.0.0.20 -p1-65535
#   PORT      STATE SERVICE
#   80/tcp    open  http        # apache
#   8000/tcp  open  http-alt    # GeigerLog

# Python http.server:  /usr/lib/python3.9/http/server.py
# to accommodate "Unsafe" requests with CR only instead of CRLF
# modify line 283ff:
#
#     requestline = str(self.raw_requestline, 'iso-8859-1')
#     # mod by ullix
#     msg = "http.server: requestline ending with "
#     if requestline.endswith('\r\n'):
#         print(msg + "CRLF")
#         requestline = requestline.rstrip('\r\n')
#
#     elif requestline.endswith('\r'):
#         print(msg + "CR")
#         requestline = requestline.rstrip('\r')
#
#     elif requestline.endswith('\n'):
#         print(msg + "LF")
#         requestline = requestline.rstrip('\n')
#
#     else:
#         print(msg + "neither CR nor LF !!!!!!!!!!")
#     # end mod


__author__          = "ullix"
__copyright__       = "Copyright 2016, 2017, 2018, 2019, 2020, 2021, 2022"
__credits__         = [""]
__license__         = "GPL3"


from   gsup_utils           import *

dogetmsg = "no data"                    # dummy to have var defined
color    = None


def initWiFiClient():
    """Initialize WiFiClient"""

    fncname                 = "initWiFiClient: "
    gglobs.WiFiClientValues = {}
    msg                     = ""

    dprint(fncname + "Initializing WiFiClient")
    setIndent(1)

    if gglobs.WiFiClientPort        == "auto": gglobs.WiFiClientPort        = 8000              # something other than 80 (below port 1024 only as sudo!)
    if gglobs.WiFiClientType == "GMC":
    # GMC
        if gglobs.WiFiClientVariables == "auto": gglobs.WiFiClientVariables   = "CPM"
    else:
    # GENERIC
        if gglobs.WiFiClientVariables == "auto": gglobs.WiFiClientVariables = "CPM, CPS, Temp, Press, Humid"

    gglobs.Devices["WiFiClient"][DNAME] = "WiFiClient " + gglobs.WiFiClientType
    gglobs.Devices["WiFiClient"][CONN]  = True
    dprint(fncname + "connected to: IP:Port '{}:{}', detected device: '{}'".format(
                                                gglobs.GeigerLogIP,
                                                gglobs.WiFiClientPort,
                                                gglobs.Devices["WiFiClient"][DNAME]))

    setLoggableVariables("WiFiClient", gglobs.WiFiClientVariables)

    # create the web server
    try:
        # 'ThreadingHTTPServer': New in version Py 3.7. Not compatible with 3.6
        # non-threading may have been cause for crashing on double requests!
        # WiFiClientServer = http.server.HTTPServer((gglobs.GeigerLogIP, gglobs.WiFiClientPort), MyServer)
        gglobs.WiFiClientServer = http.server.ThreadingHTTPServer((gglobs.GeigerLogIP, gglobs.WiFiClientPort), MyServer)
        gglobs.WiFiClientServer.timeout = 3
        dprint(fncname + "GeigerLog HTTPServer listening at: http://%s:%s" % (gglobs.GeigerLogIP, gglobs.WiFiClientPort))

    except OSError as e:
        exceptPrint(e, "")
        msg0 = "WiFiClientServer could not be started, because "
        if e.errno == 98:   msg = (False, msg0 + "Port number {} is already in use".format(gglobs.WiFiClientPort))
        else:               msg = (False, msg0 + "of OS.Error: {}".format(e.errno))

    except Exception as e:
        msg = "Unexpected Failure - WiFiClientServer could not be started"
        exceptPrint(e, msg)
        efprint(e)
        qefprint(msg)

    gglobs.WiFiClientThread = threading.Thread(target=WiFiClientThreadTarget)
    gglobs.WiFiClientThread.daemon = True        # daemons will be stopped on exit!
    gglobs.WiFiClientThread.start()

    setIndent(0)
    return msg


def WiFiClientThreadTarget():
    """Thread that constantly triggers readings from the usb device."""

    fncname = "WiFiClientThreadTarget: "

    try:
        gglobs.WiFiClientServer.serve_forever()
    except Exception as e:
        exceptPrint(e, fncname + "serve_forever")


def terminateWiFiClient():
    """terminate all WiFiClient function"""

    fncname = "terminateWiFiClient: "

    dprint(fncname)
    setIndent(1)

    if gglobs.WiFiClientServer is not None:
        gglobs.WiFiClientServer.server_close()

    gglobs.Devices["WiFiClient"][CONN] = False

    dprint(fncname + "Terminated")
    setIndent(0)


def getInfoWiFiClient(extended=False):
    """Info on the WiFiClient Device"""

    WiFiInfo  = ""
    WiFiInfo += "Configured Connection:        Server IP:Port: '{}:{}'\n"      .format(gglobs.GeigerLogIP, gglobs.WiFiClientPort)

    if not gglobs.Devices["WiFiClient"][CONN]: return WiFiInfo + "<red>Device is not connected</red>"

    WiFiInfo += "Connected Device:             {}\n"         .format(gglobs.Devices["WiFiClient"][DNAME])
    WiFiInfo += "Configured Device Type:       {}\n"         .format(gglobs.WiFiClientType)
    WiFiInfo += "Configured Variables:         {}\n"         .format(gglobs.WiFiClientVariables)
    WiFiInfo += getTubeSensitivities(gglobs.WiFiClientVariables)

    if extended == True:
        WiFiInfo += "No extended info"

    return WiFiInfo


def getValuesWiFiClient(varlist):
    """Read and return all WiFiClient data"""

    #############################################################################
    # inner function
    def getValueWiFiClient(valname):
        """check for missing value in WiFiClient data and return floats"""

        rawval = gglobs.WiFiClientValues[valname]
        # edprint(fncname + "rawval: ", rawval) # 2 decimals for ACPM and uSv
        if  rawval == "":   # missing value
            val = gglobs.NAN
        else:
            try:
                val = float(rawval)
            except Exception as e:
                msg = "valname: {}".format(valname)
                exceptPrint(e, msg)
                val = gglobs.NAN
        return val
    # end inner function
    #############################################################################


    start   = time.time()
    fncname = "getValuesWiFiClient: "
    alldata = {}                        # data to be returned

    for vname in varlist:
        # print("vname: ", vname)
        if gglobs.WiFiClientType == "GMC":
            # GMC
            if   vname == "CPM"  and "CPM"  in gglobs.WiFiClientValues: alldata.update({vname: getValueWiFiClient("CPM" )})
            elif vname == "CPS"  and "ACPM" in gglobs.WiFiClientValues: alldata.update({vname: getValueWiFiClient("ACPM")})
            elif vname == "Xtra" and "uSV"  in gglobs.WiFiClientValues: alldata.update({vname: getValueWiFiClient("uSV" )})

        else:
            # GENERIC
            if   vname in gglobs.WiFiClientValues:    alldata.update({vname:  getValueWiFiClient(vname)})

    gglobs.WiFiClientValues = {}  # reset

    vprintLoggedValues(fncname, varlist, alldata, (time.time() - start) * 1000)

    return alldata


class MyHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        """replacing the log_message function"""

        # output:  ... WiFiClient LogMsg: GET /?ID=GeigerLog&M=10&S=11&M1=12&S1=13&M2=14&S2=15&M3=16&S3=17&T=18&P=19&H=20&X=21 HTTP/1.1, 302, - | WiFiClient do_GET: ERROR: GMC Device: query lacks ID
        strarg = ", ".join(args)    # count(args) = 3 (except on errors)

        if color == TYELLOW:    dprint("WiFiClient LogMsg: ", strarg, dogetmsg)


class MyServer(MyHandler):

    def do_GET(self):
        """'do_GET' overwrites class function"""

        ######## this is the only place with these details #################################################################
        # when calling with: http://10.0.0.20:8000/log2.asp?CPM=44&AID=karl&GID=12345&ACPM=46&uSV=0.30
        #
        # vprint("self.path: ",               self.path)              # /log2.asp?CPM=44&AID=karl&GID=12345&ACPM=46&uSV=0.30
        # vprint("self.command: ",            self.command)           # GET
        # vprint("self.client_address: ",     self.client_address)    # ('10.0.0.20', 60856)
        # vprint("self.server: ",             self.server)            # <http.server.ThreadingHTTPServer object at 0x7f0fbd160a00>
        # vprint("self.close_connection: ",   self.close_connection)  # True
        # vprint("self.requestline: ",        self.requestline)       # GET /log2.asp?CPM=44&AID=karl&GID=12345&ACPM=46&uSV=0.30 HTTP/1.1
        # vprint("self.responses: ",          self.responses)         # {<HTTPStatus.CONTINUE: 100>: ('Continue', 'Request received, please continue'), <and much more>
        # vprint("self. handle(): ",          self.handle())          # None
        # vprint("self. version_string(): ",  self.version_string())  # BaseHTTP/0.6 Python/3.9.4
        # vprint("self.headers: ",            self.headers)           # Host: 10.0.0.20:8000
        #                                                             # Connection: keep-alive
        #                                                             # Cache-Control: max-age=0
        #                                                             # DNT: 1
        #                                                             # Upgrade-Insecure-Requests: 1
        #                                                             # User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36
        #                                                             # Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
        #                                                             # Accept-Encoding: gzip, deflate
        #                                                             # Accept-Language: en-US,en;q=0.9,de;q=0.8
        ###################################################################################################################


        global dogetmsg, color

        fncname = "WiFiClient do_GET: "

        wprint("")
        wprint(fncname + "self.path: " + self.path)

        myresponse = 200
        myheader2  = None


        # send favicon.ico
        if self.path == '/favicon.ico':
            # for a dummy favicon.ico:
            #   myheader  = 'Content-Type', 'image/x-icon'
            #   myheader2 = 'Content-Length', 0
            #   mybytes   = b""
            myheader = 'Content-Type', 'image/png'
            mybytes  = gglobs.iconGeigerLogWeb


        # send Root page
        elif self.path == "/":
            answer  = """
            <!DOCTYPE html>
            <html lang='en'>
            <meta name='viewport' content='width=device-width, initial-scale=1.0, user-scalable=yes'>
            <meta charset='utf-8' />\n
            <style>html  {font-family:Helvetica; display:inline-block; margin:0px auto; text-align:center; font-size:20px;}</style>\n
            <img style='width:100px; height:100px;' src='favicon.ico'>
            <h3>I am<br>GeigerLog's Web Server,<br>waiting for <h2>WiFiClient Devices</h2> to call me at:</h3>\n
            <p>%s</p>
            <p>GeigerLog Version: %s
            """ % (self.headers.get("Host"), gglobs.__version__)

            myheader = 'Content-Type', "text/html"
            mybytes  = bytes(answer.strip().replace("  ", ""), "UTF-8")


        # ID
        elif self.path == "/id":
            answer   = "GeigerLog {}".format(gglobs.__version__)

            myheader = 'Content-Type', "text/plain"
            mybytes  = bytes(answer, "UTF-8")


        # either GENERIC or GMC, nothing else possible as WiFiClientType is limited to those
        elif self.path.startswith("/" + gglobs.WiFiClientType):
            query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query, max_num_fields=20)
            # edprint(fncname + "query_components: ", query_components)

            if self.path.startswith("/GENERIC"):
                # Generic Device was configured
                # url : http://10.0.0.20:8000/GENERIC?M=10&S=11&M1=12&S1=13&M2=14&S2=15&M3=16&S3=17&T=18&P=19&H=20&X=21

                for i, vname in enumerate(gglobs.varsCopy):
                    vsvname = gglobs.varsCopy[vname][1]
                    if vsvname in query_components: gglobs.WiFiClientValues[vname] = query_components[vsvname][0]

                answer = "OK for Generic WiFiClient Device"

            elif self.path.startswith("/GMC"):
                # GMC device was configured
                # gmcmap info:      http://www.gmcmap.com/AutomaticallySubmitData.asp
                # URL format:       http://www.GMCmap.com/log2.asp?AID=UserAccountID&GID=GeigerCounterID&CPM=nCPM&ACPM=nACPM&uSV=nuSV
                # like:             http://www.GMCmap.com/log2.asp?AID=123&GID=456&CPM=15&ACPM=19.7&uSV=0.12
                # NOTE:             uSV is calculated from CPM, NOT from ACPM!
                # NOTE:             there are only 2 decimals for ACPM and uSV; all decimals are kept in GeigerLog
                #
                # server response:  b'\r\n<!--               sendmail.asp-->\r\n\r\nOK.ERR0'
                #              or:  b"User is not found.ERR1."
                #              or:  b"Counter is not found.ERR2."
                # NOTE:
                # the counter receives an 'OK 200' via the header. But this is not enough; the counter
                # also wants an 'Err0' within the answer or it will say "Link Server failed"
                #       answer = 'OK'           : Counter: Link Server Failed
                #       answer = 'blahERR0blah' : Counter: Successful!
                #       answer = 'ERR0'         : Counter: Successful!

                # AID and GID are ignored
                if 'CPM'  in query_components: gglobs.WiFiClientValues["CPM"]  = query_components["CPM"] [0]
                if 'ACPM' in query_components: gglobs.WiFiClientValues["ACPM"] = query_components["ACPM"][0]
                if 'uSV'  in query_components: gglobs.WiFiClientValues["uSV"]  = query_components["uSV"] [0]

                answer = 'ERR0 - OK for GMC Device'   # 'ERR0' is needed by counter

            color    = TGREEN
            dogetmsg = "{} | {}{} {}".format(color, fncname, answer, TDEFAULT)

            myheader = 'Content-Type', "text/plain"
            mybytes  = bytes(answer, "UTF-8")

            wprint(fncname + "values: " + str(gglobs.WiFiClientValues).replace(" ", "").replace("'", "").replace(",", "  "))


        # page not found 404 error
        else:
            color    = TYELLOW
            # gdprint("headers['User-Agent']: ", self.headers["User-Agent"])
            # ["User-Agent"] from Python:      BaseHTTP/0.6 Python/3.9.4
            # ["User-Agent"] from GMC counter: None
            # ['User-Agent'] from Firefox:     Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0
            if self.headers["User-Agent"] is None or "Python" in self.headers["User-Agent"]:
                answer   = "404 Page not found"
                myheader = 'Content-Type', "text/plain"
                dogetmsg = "{} | {}{} {}".format(color, fncname, answer, TDEFAULT)

            else:
                answer   = "<!DOCTYPE html><style>html{text-align:center;</style><h1>404 Page not found</h1>"
                myheader = 'Content-Type', "text/html"
                dogetmsg = "{} | {}{} {}".format(color, fncname, answer, TDEFAULT)

            myresponse = 404

        try:
            self.send_response(myresponse)
            self.send_header(*myheader)
            if myheader2 is not None: self.send_header(*myheader2)
            self.end_headers()
            self.wfile.write(mybytes)
        except Exception as e:
            exceptPrint(e, fncname + "send & write 200")

