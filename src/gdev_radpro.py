#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gdev_radpro.py - GeigerLog module to handle devices with the
                 Rad Pro custom firmware (https://github.com/Gissio/radpro).
"""

from gsup_utils import *
import gsup_sql

__author__ = "Gissio"
__copyright__ = "Copyright 2024"
__credits__ = [""]
__license__ = "GPL3"


class RadProDevice:
    def __init__(self):
        self.port = None
        self.serial = None

        self.deviceId = None
        self.info = {}

        self.lastCPSTime = None
        self.lastCPSPulseCount = None

    def open(self, port):
        self.port = port

        try:
            self.serial = serial.Serial(port=port,
                                        baudrate=115200,
                                        timeout=0.25)

        except Exception as e:
            dprint(f"Could not open port {self.port}: {e}")

            return False

        dprint(f"Opened port {self.port}.")

        response = self.query("GET deviceId")
        if response == None:
            return False

        responseComponents = response.split(";")

        self.hardwareId = responseComponents[0]
        self.softwareId = responseComponents[1]
        self.deviceId = responseComponents[2]

        self.id = self.hardwareId + ";" + self.deviceId

        if gglobs.RadProSyncTime == "yes":
            timestamp = int(datetime.datetime.now().timestamp())
            self.query(f"SET deviceTime {str(timestamp)}")

        return True

    def close(self):
        try:
            if self.serial != None:
                self.serial.close()

            self.serial = None

        except Exception as e:
            dprint(f"Could not close port {self.port}: {e}")

    def query(self, request):
        dprint(f"Rad Pro device request: \"{request}\".")

        try:
            self.serial.write(request.encode("ascii") + b"\n")

        except Exception as e:
            dprint(f"Could not make Rad Pro device request: {e}.")

            self.close()

            return False

        response = ""

        while True:
            try:
                data = self.serial.readline().decode("ascii")

            except Exception as e:
                dprint(f"Could not receive Rad Pro device response: {e}.")

                self.close()

                return False

            if data == "":
                dprint(f"Response time out.")

                return None

            response += data

            if response[-1] == "\n":
                break

        response = response.strip()

        dprint(f"Rad Pro device response: \"{response}\".")

        if response.startswith("OK"):
            return response[3:]

        return None

    def getTime(self, time):
        if time != None:
            time = datetime.timedelta(seconds=int(time))

        return str(time)

    def getDateTime(self, time):
        if time != None:
            time = datetime.datetime.fromtimestamp(int(time))

        return str(time)

    def getInfo(self):
        return {
            "Hardware ID": self.hardwareId,
            "Software ID": self.softwareId,
            "Device ID": self.deviceId,
            "Device battery voltage": str(
                self.query("GET deviceBatteryVoltage")) + "V",
            "Device time": self.getDateTime(
                self.query("GET deviceTime")),
            "Tube life time": self.getTime(
                self.query("GET tubeTime")),
            "Tube life pulse count": str(
                self.query("GET tubePulseCount")),
            "Tube rate": str(
                self.query("GET tubeRate")) + " CPM",
            "Tube conversion factor": str(
                self.query("GET tubeConversionFactor")) + " CPM/µSv/h",
            "Tube dead time": str(
                self.query("GET tubeDeadTime")) + " s",
            "Tube dead-time compensation": str(
                self.query("GET tubeDeadTimeCompensation")) + " s",
            "Tube HV PWM frequency": str(
                self.query("GET tubeHVFrequency")) + " Hz",
            "Tube HV PWM duty cycle": str(
                self.query("GET tubeHVDutyCycle")) + " %",
        }

    def getDatalog(self, startTime):
        response = self.query(f"GET datalog {startTime}")

        if response == None:
            return None

        records = response.split(";")
        datalog = []

        last_time = None
        last_delta_time = None
        last_pulse_count = None

        for index, record in enumerate(records):
            if index == 0:
                continue

            values = record.split(",")

            if len(values) != 2:
                dprint("Entry '" + record + "' malformed.")

                continue

            try:
                record_time = int(values[0])
                record_pulse_count = int(values[1])

                if last_pulse_count != None:
                    delta_time = record_time - last_time
                    delta_pulse_count = record_pulse_count - last_pulse_count

                    if delta_time > 0 and last_delta_time == delta_time:
                        cpm = delta_pulse_count * 60 / delta_time

                        datalog.append([record_time, cpm])

                    last_delta_time = delta_time

                last_time = record_time
                last_pulse_count = record_pulse_count

            except Exception as e:
                dprint("Error while parsing datalog entry: " + e)

        return datalog


def loadDeviceHistoryDataRadPro():
    values = {}

    try:
        file = open("geigerlog-radpro-history.conf")

        for line in file:
            parts = line.strip().split(",")

            if len(parts) >= 2:
                values[parts[0]] = parts[1]

    except Exception as e:
        dprint("Error while loading device history data: " + e)

    return values


def saveDeviceHistoryDataRadPro(values):
    with open("geigerlog-radpro-history.conf", "wt") as file:
        for key, value in values.items():
            file.write(key + "," + value + "\n")


def updatePropertiesRadPro():
    gglobs.Devices["Rad Pro"][CONN] = (gglobs.RadProDevice != None)
    if gglobs.RadProDevice != None:
        gglobs.Devices["Rad Pro"][DNAME] = gglobs.RadProDevice.id
    else:
        gglobs.Devices["Rad Pro"][DNAME] = None


def initRadPro():
    """
    Open device
    """

    fncname = "initRadPro: "
    dprint(fncname)
    setIndent(1)

    errmsg = ""

    if (gglobs.RadProPort == "auto"):
        ports = [port.device for port in getPortList(symlinks=False)]
    else:
        ports = [gglobs.RadProPort]

    gglobs.RadProDevice = None
    for port in ports:
        for attempt in range(2):
            dprint(f"Connection attempt {attempt}.")

            device = RadProDevice()
            if device.open(port):
                gglobs.RadProDevice = device

                break

    if gglobs.RadProDevice == None:
        errmsg = "A Rad Pro device was not detected."

    # Configuration
    setLoggableVariables("Rad Pro", "CPM, CPS")
    updatePropertiesRadPro()

    # Finished initialization
    setIndent(0)

    return errmsg


def terminateRadPro():
    """
    Close device
    """

    fncname = "terminateRadPro: "
    dprint(fncname)
    setIndent(1)

    errmsg = ""

    if gglobs.RadProDevice != None:
        gglobs.RadProDevice.close()
        gglobs.RadProDevice = None

    updatePropertiesRadPro()

    dprint(fncname + "Terminated")
    setIndent(0)

    return errmsg


def getInfoRadPro(extended=False):
    """
    Return info
    """

    if not gglobs.Devices["Rad Pro"][CONN]:
        info = "<red>Device not connected.</red>\n"
    else:
        info = f"Configured Connection: Port:\"{gglobs.RadProDevice.port}\"\n"
        info += "Device connected.\n"

        deviceInfo = gglobs.RadProDevice.getInfo()

        for key, value in deviceInfo.items():
            info += f"{key:<32}: {value}\n"

    return info


def getValuesRadPro(varlist):
    """
    Return current data
    """

    values = {}

    for key in varlist:
        value = None

        try:
            if key == "CPM":
                cpm = gglobs.RadProDevice.query("GET tubeRate")
                if cpm != None:
                    value = float(cpm)

            elif key == "CPS":
                cpsTime = datetime.datetime.now().timestamp()
                cpsPulseCountString = gglobs.RadProDevice.query(
                    "GET tubePulseCount")
                if cpsPulseCountString != None:
                    cpsPulseCount = float(cpsPulseCountString)
                else:
                    cpsPulseCount = None

                if cpsPulseCount != None:
                    if gglobs.RadProDevice.lastCPSPulseCount != None:
                        cpsDeltaTime = cpsTime - gglobs.RadProDevice.lastCPSTime
                        cpsDeltaPulseCount = cpsPulseCount - gglobs.RadProDevice.lastCPSPulseCount

                        if abs(cpsDeltaTime - gglobs.logCycle) < 5:
                            if cpsDeltaTime < 1:
                                cpsDeltaTime = 1

                            value = cpsDeltaPulseCount / round(cpsDeltaTime)

                    gglobs.RadProDevice.lastCPSTime = cpsTime
                    gglobs.RadProDevice.lastCPSPulseCount = cpsPulseCount

            if value != None:
                values[key] = value

        except Exception as e:
            dprint("Error while parsing values: " + e)

    return values


def loadHistoryRadPro(sourceHist):
    """
    Load history
    """

    # Load device history data
    deviceHistoryData = loadDeviceHistoryDataRadPro()
    deviceLastTime = 0
    if sourceHist == "Rad Pro Device (new)":
        print(deviceHistoryData)
        if gglobs.RadProDevice.id in deviceHistoryData:
            deviceLastTime = int(datetime.datetime.fromisoformat(
                deviceHistoryData[gglobs.RadProDevice.id]).timestamp())

    # Update database
    datalog = gglobs.RadProDevice.getDatalog(deviceLastTime)
    if datalog == None:
        return (-1, "Could not download history.")

    history = []
    lastTime = None
    for entry in datalog:
        time = entry[0]
        dateTime = datetime.datetime.fromtimestamp(time)
        cpm = entry[1]
        lastTime = str(dateTime)

        history.append(
            [time,
             dateTime,
             "0 hours",
             cpm,
             None,
             None,
             None,
             None,
             None,
             None,
             None,
             None,
             None,
             None,
             None,
             ]
        )

    gsup_sql.DB_insertDevice(gglobs.hisConn, stime(), gglobs.RadProDevice.id)
    gsup_sql.DB_insertComments(gglobs.hisConn, [
        ["HEADER", None, "0 hours", "File created by reading history from device"],
        ["ORIGIN", None, "0 hours", "Download from device"],
        ["DEVICE", None, "0 hours", gglobs.RadProDevice.id],
    ])
    gsup_sql.DB_insertData(gglobs.hisConn, history)

    fprint(f"Got {len(history)} records")

    # Save device history data
    if lastTime != None:
        deviceHistoryData[gglobs.RadProDevice.id] = lastTime
        saveDeviceHistoryDataRadPro(deviceHistoryData)

    return (0, "")
