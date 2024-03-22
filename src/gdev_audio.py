#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gdev_audio.py - GeigerLog commands to handle the audio-clicks as CPM/CPS input
                using module sounddevice
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


# NOTE:
# Raspi:      on Raspi module sounddevice cannot be installed until libffi-dev is installed
#             per 'sudo apt install libffi-dev'
# Windows:    make sure the soundsettings for input and output are set for 'standard'
#             using Windows settings
# Linux       with garbled sound and message in the terminal:
#                 "ALSA lib pcm.c:7963:(snd_pcm_recover) underrun occurred"
#             execute 'pulseaudio -k' as regular user (not sudo!) this should solve it
#
#             if not enough: look into '/etc/pulse/daemon.conf'. It may have lines:
#                 ; default-fragments = 4
#                 ; default-fragment-size-msec = 25
#             uncommenting, and changing to:
#                 default-fragments = 5
#                 default-fragment-size-msec = 2
#             might help


# LATENCY:
#
# Suggested input/output latency in seconds.
#
# The special values 'low' and 'high' can be used to select the default
# low/high latency of the chosen device. 'high' is typically more robust
# (i.e. buffer under-/overflows are less likely), but the latency may be
# too large for interactive applications.
#
# NOTE: latencies are given in millisec!
# on my Desktop:
# 'default_high_input_latency':  0.034829931972789115   --> 35 ms
# 'default_low_input_latency'  : 0.008707482993197279   -->  9 ms
# 'default_high_output_latency': 0.034829931972789115   --> 35 ms
# 'default_low_output_latency':  0.008707482993197279   -->  9 ms
#
# on MSI (low power) computer: using Input: 'Mikrofon (2- High Definition Au'
# 'default_high_input_latency':  0.18                   --> 180 ms
# 'default_low_input_latency':   0.09                   -->  90 ms
# 'default_high_output_latency': 0.18                   --> 180 ms
# 'default_low_output_latency':  0.09                   -->  90 ms

# tested on MSI (low power) computer on Windows 10 :
#~sd.default.latency  = ('low', 'low')   --> results in poor, low counts
#~sd.default.latency  = ('high', 'high') --> results in higher counts, but still less than digital on GMC300E+
#~sd.default.latency  = (100, 100)       --> results in same counts as digital on GMC300E+
#~sd.default.latency  = 1000, or 10000 works, but no improvement
#~sd.default.latency  = (1, 1)           --> works just as well!!!
#~sd.default.latency  = (0.1, 0.1)       --> getting 'overflowed' !
#~sd.default.latency  = (0.3, 0.3)       --> getting some 'overflowed' !
#~sd.default.latency  = (0.5, 0.5)       --> works, no 'overflowed' observed over >30sec !

# tested on Manu 4 with USB dongle "ID 1b3f:2008 Generalplus Technology Inc. "
# sd.default.latency  = (1.0, 1.0)       --> works, few 'overflowed' observed over >30sec !


from   gsup_utils       import *


def initAudio():
    """Start the thread to monitor the audio pulses for clicks"""

    global AudioCounterThread

    fncname ="initAudio: "

    dprint(fncname + "Initializing AudioCounter")
    setIndent(1)

    errmsg = ""                            # potential errors:  no input device!
    gglobs.Devices["Audio"][DNAME] = "Audio"

    if gglobs.AudioDevice       == "auto": gglobs.AudioDevice       = (None, None)      # the system's defaults
    if gglobs.AudioLatency      == "auto": gglobs.AudioLatency      = (1.0, 1.0)        # seems like a generic
    if gglobs.AudioPulseMax     == "auto": gglobs.AudioPulseMax     = 32768             # +/- 15 bit
    if gglobs.AudioPulseDir     == "auto": gglobs.AudioPulseDir     = False             # => negative
    if gglobs.AudioThreshold    == "auto": gglobs.AudioThreshold    = 60                # % of max
    if gglobs.AudioVariables    == "auto": gglobs.AudioVariables    = "CPM3rd, CPS3rd"

    setLoggableVariables("Audio", gglobs.AudioVariables)

    # print sound driver settings
    vprint(fncname + "Query Devices: \n",   sd.query_devices() )
    vprint(fncname + "Query Host Apis:")
    if gglobs.verbose:
        for a in sd.query_hostapis(index=None):
            vprint("   ", a)

    # samplerate has only one single int value, but others
    # allow 2 values: 1st=input, 2nd=output
    sd.default.reset()                              # clear all settings to default
    sd.default.device       = gglobs.AudioDevice    # set the AudioDevice defaults
    sd.default.latency      = gglobs.AudioLatency   # set latency values in sec, like (1.0, 1.0)
    sd.default.dtype        = ('int16', 'int16')    # choose from: 'float32', 'int32', 'int16', 'int8', 'uint8'
    sd.default.channels     = (1, 1)                # options: 1, 2, more
    sd.default.samplerate   = 44100                 # options: 96000, 48000, 44100, 22050, 11025

    try:
        defaultDevice = sd.default.device
        dprint(fncname + "Default Device (Input, Output): {}".format(defaultDevice))
        if defaultDevice[1] != -1 :
            sdqd = sd.query_devices(device=None, kind='output')
            vprint(fncname  + "Output Device: ")
            for key in sdqd: vprint("   {:30s} : {}".format(key, sdqd[key]))
        else:
            edprint(fncname + "Output Device: ", "No Default Output Device!")

        if defaultDevice[0] != -1 :
            sdqd = sd.query_devices(device=None, kind='input')
            vprint(fncname  + "Input Device : ")
            for key in sdqd: vprint("   {:30s} : {}".format(key, sdqd[key]))
        else:
            edprint(fncname + "Input Device : ", "No Default Input Device!")

    except Exception as e:
        info = fncname + "Exception in querying default devices"
        exceptPrint(e, info)

    if defaultDevice[0] != -1:
        gglobs.AudioFormat      = sd.default.dtype
        gglobs.AudioChannels    = sd.default.channels
        gglobs.AudioRate        = sd.default.samplerate
        gglobs.AudioChunk       = 32

        #testing #########
        gglobs.AudioChunk       *= 4  # -> 128 to make longer pulses visible (reduces maximum count rate)
        # end testing

        dprint(fncname + "DEVICE:{}, CHANNELS:{}, FORMAT:{}, Latency:{}, Host API Index:{}, RATE:{}, CHUNK:{}"\
                        .format(
                                gglobs.AudioDevice,
                                gglobs.AudioChannels,
                                gglobs.AudioFormat,
                                gglobs.AudioLatency,
                                sd.default.hostapi,
                                gglobs.AudioRate,
                                gglobs.AudioChunk,
                               )
             )

        gglobs.Devices["Audio"][CONN] = True

        gglobs.AudioThreadStop  = False

        AudioCounterThread      = threading.Thread(target=AudioCounterThreadTarget, args=(None,))
        AudioCounterThread.start()
        dprint(fncname + "Thread-status: is alive: ", AudioCounterThread.is_alive())

    else:
        errmsg  = "No Sound Input detected! Is there a proper connection?"

    setIndent(0)

    return errmsg


def terminateAudio():
    """Stop the thread to monitor the sounddev pulses for clicks"""

    global AudioCounterThread

    fncname ="terminateAudio: "

    dprint(fncname)
    setIndent(1)

    dprint(fncname + "stopping thread")
    gglobs.AudioThreadStop = True
    AudioCounterThread.join() # "This blocks the calling thread until the thread
                              #  whose join() method is called is terminated."

    # verify that thread has ended, but wait not longer than 5 sec (takes 0.006...0.016 ms)
    start = time.time()
    while AudioCounterThread.is_alive() and (time.time() - start) < 5:
        pass

    dprint(fncname + "thread-status: is alive: {}, waiting took:{:0.1f}ms".format(AudioCounterThread.is_alive(), 1000 * (time.time() - start)))
    gglobs.Devices["Audio"][CONN] = False

    dprint(fncname + "Terminated")
    setIndent(0)


def AudioCounterThreadTarget(Dummy):
    """The thread to read the sounddev input"""

    fncname = "AudioCounterThreadTarget: "

    gglobs.AudioLastCps     = 0
    gglobs.AudioLastCpm     = 0
    cps_count               = 0
    llimit                  = gglobs.AudioThreshold / 100 * gglobs.AudioPulseMax
    ilimit                  = 10000                             # the |pulse| must NOT exceed this value on first count in order to be countesd
                                                                # higher values give MORE counts!

    gglobs.AudioLast60CPS   = np.full(60, 0)                    # storing last 60 sec of CPS values
    gglobs.AudioMultiPulses = np.array([0])                     # time courses for last ~40 of the pulses
    gglobs.AudioRecording   = np.array([0])
    nandata                 = np.full(10, gglobs.NAN)           # creating a gap of 10 values
    chunks40                = (gglobs.AudioChunk + 10) * 40     # the length of 40 single pulses with gaps

    cstart                  = time.time()                       # to record the 1 sec collection period

    try:
        CHUNKstream = sd.InputStream(blocksize=gglobs.AudioChunk)   # no callback so we get blocking read
        CHUNKstream.start()
    except Exception as e:
        msg = "Audio cannot be activated. Is an input device missing?"
        #efprint(msg)
        exceptPrint(e, msg)
        gglobs.AudioThreadStop = True
        return

    while not gglobs.AudioThreadStop:
        try:
            record, overflowed = CHUNKstream.read(gglobs.AudioChunk)
            npdata = record.reshape(-1)     # convert from '[ [1] [0] [3] ...[2] ]'  to '[1, 0, 3, ..., 2]'
            gglobs.AudioRecording = np.concatenate((gglobs.AudioRecording, npdata))[-gglobs.AudioRate:]
        except Exception as e:
            info = fncname + "Exception reading stream "
            exceptPrint(e, info)
            npdata = np.array([0])

        if overflowed:
            # Input overflow.
            # In a stream opened with blocksize=0, indicates that data prior to
            # the first sample of the input buffer was discarded due to an overflow,
            # possibly because the stream callback is using too much CPU time.
            #
            # In a stream opened with a non-zero blocksize, it indicates that
            # data prior to one or more samples in the input buffer was discarded.
            # This can happen in full-duplex and input-only streams (including
            # playrec() and rec()).
            pass
            dprint("'overflowed' HAPPENED: Stream calls: record len:{}, overflowed:{}".format(len(record), overflowed) )

        # Determine if there is a count
        # ignore records catching pulses when already down; they were probably
        # already counted during last record
        gotCount = False
        if gglobs.AudioPulseDir:                        # True -> positive pulse
            if npdata[0] < +ilimit and npdata.max() > +llimit:
                gotCount = True
        else:                                           # False -> negative pulse
            if npdata[0] > -ilimit and npdata.min() < -llimit:
                gotCount = True

        if gotCount:
            cps_count  += 1
            gglobs.AudioMultiPulses   = np.concatenate((gglobs.AudioMultiPulses, nandata, npdata))[-chunks40:]

        deltat = time.time() - cstart
        if deltat >= 1:
            gglobs.AudioLastCps   = cps_count / deltat  * 1.05 # correct for calc time
            gglobs.AudioLast60CPS = np.append(gglobs.AudioLast60CPS, gglobs.AudioLastCps)[1:]
            cps_count             = 0
            cstart                = time.time()

    CHUNKstream.stop()
    CHUNKstream.close()


def getInfoAudio(extended = False):
    """Info on settings of the sounddev thread"""

    # if not gglobs.AudioConnection:   return "No connected device"
    # if not gglobs.Devices["Audio"][CONN] :   return "No connected device"

    AudioInfo  = "Configured Connection:        Default Audio Input\n"

    if not gglobs.Devices["Audio"][CONN]: return AudioInfo + "<red>Device is not connected</red>"

    AudioInfo += "Connected Device:             {}\n".format(gglobs.Devices["Audio"][DNAME])
    AudioInfo += "Configured Variables:         {}\n".format(gglobs.AudioVariables)
    AudioInfo += getTubeSensitivities(gglobs.AudioVariables)

    if extended == True:
        AudioInfo += """
Sampling Details:
- DEVICE:                     Input:'{}', Output:'{}'
- FORMAT:                     Input:'{}', Output:'{}'
- CHANNELS (1=Mono,2=Stereo): Input:'{}', Output:'{}'
- LATENCY [sec]:              Input:'{}', Output:'{}'
- Host API Index              {}
- RATE:                       {} (Samples per second)
- CHUNK:                      {} (Samples per read)
- Pulse Height Max            {} (System reported max signal)
- Pulse Direction             {} (negative or positive)
- Pulse Threshold             {}% of Pulse Height Max to trigger count"""\
                .format(
                        sd.default.device[0],
                        sd.default.device[1],
                        sd.default.dtype[0],
                        sd.default.dtype[1],
                        sd.default.channels[0],
                        sd.default.channels[1],
                        sd.default.latency[0],
                        sd.default.latency[1],
                        sd.default.hostapi,
                        sd.default.samplerate,

                        gglobs.AudioChunk,
                        gglobs.AudioPulseMax,
                        "POSITIVE" if gglobs.AudioPulseDir else "NEGATIVE",
                        gglobs.AudioThreshold,
                       )
        AudioInfo += "\nFull Device Query:\n"
        AudioInfo += str(sd.query_devices())
        AudioInfo += "\n"

    return AudioInfo


def toggleAudioCounterPulseDir():
    """toggle which pulse direction is sensed"""

    gglobs.AudioPulseDir = not gglobs.AudioPulseDir

    fprint(header("Switching Pulse Direction of AudioCounter"))
    if gglobs.AudioPulseDir:  direction = "POSITIVE"
    else:                     direction = "NEGATIVE"
    gglobs.AudioMultiPulses = gglobs.AudioMultiPulses[-10:]

    fprint("New pulse direction setting: {}".format(direction))


def getValuesAudio(varlist):
    """Read all sounddev data; return empty dict when not available"""

    start = time.time()

    fncname   = "getValuesAudio: "
    alldata = {}

    for vname in varlist:
        if   vname in ("CPM", "CPM1st", "CPM2nd", "CPM3rd"):
            cpm             = int(round(np.sum(gglobs.AudioLast60CPS), 0))
            cpm             = scaleVarValues(vname, cpm, gglobs.ValueScale[vname])
            alldata.update(  {vname: cpm})

        elif vname in ("CPS", "CPS1st", "CPS2nd", "CPS3rd"):
            cps             = int(round(gglobs.AudioLastCps, 0))
            cps             = scaleVarValues(vname, cps, gglobs.ValueScale[vname] )
            alldata.update(  {vname: cps})

    vprintLoggedValues(fncname, varlist, alldata, (time.time() - start) * 1000)

    return alldata


def plotAudio(dtype="Single Pulse", duration=None):
    """Plotting an audio plot"""

    fncname = "plotAudio: "

    data = gglobs.AudioPlotData
    #print(fncname + "dtype:{}, data:{}".format(dtype, data))

    subTitle = dtype

    if   dtype == "Single Pulse":
        pass

    elif dtype == "Multi Pulse":
        count     = len(data) / (gglobs.AudioChunk + 10) # 10 is: nan values as gap
        subTitle += " - {:1.0f} pulses shown".format(count)

    elif dtype == "Recording":
        subTitle += " - {:1.0f} second".format(duration)


    # Plotstyle
    plotstyle        = {'color'             : 'black',
                        'linestyle'         : 'solid',
                        'linewidth'         : '0.5',
                        'label'             : 'my label',
                        'markeredgecolor'   : 'black',
                        'marker'            : 'o',
                        'markersize'        : '1',
                        'alpha'             : 1,
                        }
    plt.close(99)
    fig2 = plt.figure(99, facecolor = "#E7cccc", dpi=gglobs.hidpiScaleMPL)
    wprint(fncname + "open figs count: {}, current fig: #{}".format(len(plt.get_fignums()), plt.gcf().number))

    plt.title("AudioCounter Device\n", fontsize=14, loc='center')
    plt.title("Audio Input", fontsize=10, fontweight='normal', loc = 'left')
    plt.title(subTitle, fontsize=10, fontweight='normal', loc = 'right')

    plt.grid(True)
    plt.subplots_adjust(hspace=None, wspace=.2 , left=.11, top=0.85, bottom=0.15, right=.97)
    plt.ticklabel_format(useOffset=False)

    # hide the cursor position from showing in the Nav toolbar
    ax1 = plt.gca()
    ax1.format_coord = lambda x, y: ""

    # canvas - this is the Canvas Widget that displays the `figure`
    # it takes the `figure` instance as a parameter to __init__
    canvas2 = FigureCanvas(fig2)
    canvas2.setFixedSize(1000, 550)
    navtoolbar = NavigationToolbar(canvas2, gglobs.exgg)

    labout = QTextBrowser()                  # label to hold the description
    labout.setFont(gglobs.fontstd)           # my std font for easy formatting
    labout.setText("")

    mtext1  =   "Device:           Input:'{}', Output:'{}'" .format(sd.default.device[0], sd.default.device[1])
    mtext1 += "\nSample Format:    {}"                      .format(gglobs.AudioFormat)
    mtext1 += "\nSampled Channels: {} (1=Mono, 2=Stereo)"   .format(gglobs.AudioChannels)
    mtext1 += "\nSampling rate:    {} per second"           .format(gglobs.AudioRate)
    mtext1 += "\nSamples:          {} per read"             .format(gglobs.AudioChunk)
    mtext1 += "\nPulse Height Max: ±{} "                    .format(gglobs.AudioPulseMax)
    mtext1 += "\nPulse Threshold:  {} %"                    .format(gglobs.AudioThreshold)
    mtext1 += "\nPulse Direction:  {} "                     .format(("POSITIVE" if gglobs.AudioPulseDir else "NEGATIVE"))

    if   dtype == "Single Pulse":
        labout.append("Showing the last detected AudioCounter pulse")

    elif dtype == "Multi Pulse":
        labout.append("Showing the last (up to 40) detected AudioCounter pulses")

    elif dtype == "Recording":
        labout.append("Showing a straight recording of {} second - no pulse detection applied".format(duration))

    labout.append(mtext1)

    d = QDialog()
    gglobs.plotAudioPointer = d
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setWindowTitle("AudioCounter Device")
    #d.setMinimumHeight(700)
    d.setWindowModality(Qt.WindowModal)

    okButton = QPushButton("OK")
    okButton.setAutoDefault(True)
    okButton.clicked.connect(lambda:  d.done(0))

    singleButton = QPushButton("Single Pulse")
    singleButton.setAutoDefault(False)
    singleButton.clicked.connect(lambda: reloadAudioData("Single Pulse"))

    multiButton = QPushButton("Multi Pulse")
    multiButton.setAutoDefault(False)
    multiButton.clicked.connect(lambda: reloadAudioData("Multi Pulse"))

    recordButton = QPushButton("Recording")
    recordButton.setAutoDefault(False)
    recordButton.clicked.connect(lambda: reloadAudioData("Recording"))

    togglePulseDirButton = QPushButton("Toggle Pulse Direction")
    togglePulseDirButton.setAutoDefault(False)
    togglePulseDirButton.clicked.connect(lambda: reloadAudioData("Toggle"))

    bbox    = QDialogButtonBox()
    bbox.addButton(okButton,                QDialogButtonBox.ActionRole)
    bbox.addButton(recordButton,            QDialogButtonBox.ActionRole)
    bbox.addButton(singleButton,            QDialogButtonBox.ActionRole)
    bbox.addButton(multiButton,             QDialogButtonBox.ActionRole)
    bbox.addButton(togglePulseDirButton,    QDialogButtonBox.ActionRole)

    layoutH = QHBoxLayout()
    layoutH.addWidget(bbox)
    layoutH.addWidget(navtoolbar)
    layoutH.addStretch()

    layoutV = QVBoxLayout(d)
    layoutV.addLayout(layoutH)
    layoutV.addWidget(canvas2)
    layoutV.addWidget(labout)

    plt.xlabel("Time [millisec]", fontsize=14)
    plt.ylabel("Amplitude [rel]", fontsize=14)
    plt.ylim(-35000, 35000)

    x = np.arange(len(data)) * 1 / gglobs.AudioRate * 1000 # create the x-axis data
    plt.plot(x, data,  **plotstyle)
    #d.update() # "Updates the widget unless updates are disabled or the widget is hidden."

    fig2.canvas.draw_idle()
    playWav("ok")
    d.exec()


def reloadAudioData(dtype):
    """closes the dialog and reopens"""

    #print("reloadAudioData: ", dtype)

    try: # fails if it had never been opened; but then it is closed anyway
        gglobs.plotAudioPointer.close()
    except:
        pass

    # when a recording was last, then gglobs.AudioMultiPulses will be 44100 samples long,
    # but even Multi needs only 40*(single pulse + 10) => 1680. Therfore crop it,
    # otherwise next Multi will show samples from recording
    if len(gglobs.AudioMultiPulses) > (40 * (gglobs.AudioChunk + 10)):
        #~gglobs.AudioMultiPulses = gglobs.AudioMultiPulses[-(gglobs.AudioChunk + 10):]
        gglobs.AudioMultiPulses =  np.array([0])

    duration = None

    if   dtype == "Single Pulse":
        gglobs.AudioPlotData = gglobs.AudioMultiPulses[-(gglobs.AudioChunk):] # last pulse only without nan
        #gglobs.AudioMultiPulses = gglobs.AudioMultiPulses[-(gglobs.AudioChunk):] # last pulse only without nan

    elif dtype == "Multi Pulse":
        pass    # will show all, i.e. up to last 40 pulses
        gglobs.AudioPlotData = gglobs.AudioMultiPulses

    elif dtype == "Recording":
        setBusyCursor()
        duration = 1 # seconds
        #gdev_audio.getLongChunk(duration)
        gglobs.AudioPlotData = gglobs.AudioRecording
        setNormalCursor()

    else: # dtype == "Toggle":
        #~gdev_audio.toggleAudioCounterPulseDir()
        toggleAudioCounterPulseDir()
        dtype = "Recording"
        duration = 1 # seconds
        #~gglobs.AudioPlotData = gglobs.AudioMultiPulses[-(gglobs.AudioChunk):] # last pulse only without nan
        gglobs.AudioMultiPulses = np.array([0]) # set to empty as old pulses do not make sense
        gglobs.AudioPlotData    = gglobs.AudioRecording

    plotAudio(dtype, duration)


def audio_callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""

    global liveq

    fncname = "audio_callback: "
    #print(fncname + "np.shape(indata): ", np.shape(indata), ", frames: ", frames, ", time: ", time, ", status: ", status)

    if status:
        edprint(fncname + "status: ", status)

    liveq.put(indata[:, 0])


def updateAnimationPlot(frame):
    """This is called by matplotlib for each animated plot update.

    Typically, audio callbacks happen more frequently than plot updates,
    therefore the queue tends to contain multiple blocks of audio data.
    """
    global liveq, plotdata

    start = time.time()

    fncname = "updateAnimationPlot: "

    #print(fncname + "frame", frame)

    #counter = 0
    while True:
        try:
            data = liveq.get_nowait()
            #print("liveq: ", counter)
            #counter += 1
        except queue.Empty:
            #edprint("queue.Empty: ", queue.Empty)
            break

        shift    = len(data)
        plotdata = np.roll(plotdata, -shift)
        plotdata[-shift:] = data

        lines[0].set_ydata(plotdata)

    return lines


def makeEnde():
    global ende
    ende = True


def showLiveAudioSignal():
    """Plotting a rolling audio plot"""

    fncname = "showLiveAudioSignal: "

    global liveq, lines, plotdata, ende
    global args_device, args_channels, args_samplerate

    liveq = queue.Queue()
    ende  = False

    try:
        #print(fncname + "Audio Devices found on system:\n{}".format(sd.query_devices()))

        #~args_samplerate = 44100 # get default instead
        args_samplerate = None
        #args_samplerate = 11050*2

        args_window     = 20000
        args_downsample = 1
        #~args_channels   = (1, ) # needed as tuple
        args_channels   = 1
        #~args_interval   = 300
        args_interval   = 50
        args_device     = None

        if args_samplerate is None:
            device_info = sd.query_devices(args_device, 'input')
            args_samplerate = device_info['default_samplerate']
        #print(fncname + "parameters: ", args_samplerate, args_window, args_downsample, args_channels, args_interval, args_device)

        length   = int(args_window * args_samplerate / (1000 * args_downsample)) # time length in ms
        plotdata = np.zeros((length))                        # create buffer of required length
        #~print("length: ", length)                                                # 20000 * 44100 / (1000 * 1) = 882000
        #~print("plotdata: ", plotdata)                                            # [[0.] [0.] [0.] ... [0.] [0.] [0.]]
        #~print("np.shape(plotdata): ", np.shape(plotdata))                        # np.shape(plotdata):  (441000, 1)

    except Exception as e:
        srcinfo = fncname + "Exception: "
        exceptPrint(e, srcinfo)

    plt.close(77)
    fig77 = plt.figure(77, facecolor = "#E7cccc", dpi=gglobs.hidpiScaleMPL) # light red
    vprint(fncname + "open figs count: {}, current fig: #{}".format(len(plt.get_fignums()), plt.gcf().number))

    lines = plt.plot(plotdata) # creates a plot array x=0,1,2,... y=0,0,0,

    #~for column, line in enumerate(lines):
        #~print("column: ", column, ", lines: ", lines, column, line)
        #~print("x: ", line.get_xdata(orig=True), "\ny: ", line.get_ydata(orig=True))

    plt.title("AudioCounter Device\n", fontsize=14, loc='center')
    plt.title("Live Audio Signal", fontsize=10, fontweight='normal', loc = 'left')

    plt.grid(True)
    plt.subplots_adjust(hspace=None, wspace=.2 , left=.11, top=0.85, bottom=0.15, right=.97)
    plt.ticklabel_format(useOffset=False)

    # do not draw x ticks and x labels
    plt.tick_params(
        axis='x',          # changes apply to the x-axis
        which='both',      # both major and minor ticks are affected
        bottom=False,      # ticks along the bottom edge are off
        top=False,         # ticks along the top edge are off
        labelbottom=False) # labels along the bottom edge are off

    # hide the cursor position from showing in the Nav toolbar
    ax1 = plt.gca()
    ax1.format_coord = lambda x, y: ""

    # canvas - this is the Canvas Widget that displays the `figure`
    # it takes the `figure` instance as a parameter to __init__
    canvas77 = FigureCanvas(fig77)
    canvas77.setFixedSize(1000, 550)
    navtoolbar = NavigationToolbar(canvas77, gglobs.exgg)

    d = QDialog()
    gglobs.plotAudioPointer = d
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setWindowTitle("AudioCounter Device")
    #d.setMinimumHeight(700)
    d.setWindowModality(Qt.WindowModal)

    okButton = QPushButton("OK")
    okButton.setAutoDefault(True)
    okButton.clicked.connect(lambda:  makeEnde())

    bbox    = QDialogButtonBox()
    bbox.addButton(okButton,                QDialogButtonBox.ActionRole)

    layoutH = QHBoxLayout()
    layoutH.setAlignment(Qt.AlignLeft);
    layoutH.addWidget(bbox)
    layoutH.addWidget(navtoolbar)
    layoutH.addStretch() # all stretches needed, very odd!
    layoutH.addStretch()
    layoutH.addStretch()
    layoutH.addStretch()
    layoutH.addStretch()
    layoutH.addStretch()
    layoutH.addStretch()
    layoutH.addStretch()
    layoutH.addStretch()

    layoutV = QVBoxLayout(d)
    layoutV.addLayout(layoutH)
    layoutV.addWidget(canvas77)

    plt.xlabel("\nTime", fontsize=14)
    plt.ylabel("Amplitude [rel]", fontsize=14)
    plt.ylim(-35000, 35000)

    # https://stackoverflow.com/questions/16732379/stop-start-pause-in-python-matplotlib-animation
  #~ani = mplanim.FuncAnimation(fig77, updateAnimationPlot, interval=args_interval, blit=True)
    ani = mplanim.FuncAnimation(fig77, updateAnimationPlot, interval=args_interval, blit=False)

    playWav("ok")

    d.open()    # needed!

    start = time.time()
    while True: # one cycle is about 350 ms
        stream = sd.InputStream(device=args_device, channels=args_channels, samplerate=args_samplerate, callback=audio_callback)

        with stream: # not doing anything, but still needed!
            pass

        QtUpdate() # ohne dies nur leerer Fensterrahmen
        #d.show() # kein Zusatznutzen; ohne QtUpdate nur leeres Bild
        #time.sleep(0.2)
        cdprint("time delta: {:0.3f} ms".format(1000*(time.time() -start))) # alle 300 - 400 ms
        start = time.time()

        if ende: break

    #print("with stream done")

    d.close()
    ani.event_source.stop() # ouff, this stops the animation!


def turnEia(tdir, mmovie):

    turnDir = tdir
    mmovie.stop()
    time.sleep(0.3)
    mmovie.start()


def showAudioEia():
    """https://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=9517&#7803"""

    fncname = "showAudioEia: "

    from PyQt5.QtGui import QMovie

    d = QDialog()

    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setWindowTitle("Eia")
    d.setWindowModality(Qt.WindowModal)

    okButton = QPushButton("OK")
    okButton.setAutoDefault(True)
    okButton.clicked.connect(lambda:  d.close())

    singleButton = QPushButton("Left Turn")
    singleButton.setAutoDefault(False)
    singleButton.clicked.connect(lambda: turnEia("Left", movie))

    rightButton = QPushButton("Right Turn")
    rightButton.setAutoDefault(False)
    rightButton.clicked.connect(lambda: turnEia("Right", movie))

    bbox    = QDialogButtonBox()
    bbox.addButton(okButton,                QDialogButtonBox.ActionRole)
    bbox.addButton(singleButton,            QDialogButtonBox.ActionRole)
    bbox.addButton(rightButton,             QDialogButtonBox.ActionRole)


    peia = "".join(map(chr, [101, 105, 97, 46, 103, 105, 102]))
    dp = os.path.join(getProgPath(), gglobs.gresDirectory, peia)

    label = QLabel()
    movie = QMovie(dp)
    label.setMovie(movie)
    movie.start()

    layoutH = QHBoxLayout()
    layoutH.addWidget(bbox)
    layoutH.addStretch()

    layoutV = QVBoxLayout(d)
    layoutV.addLayout(layoutH)
    layoutV.addWidget(label)

    playWav("ok")

    d.exec()



##############################################################################
# following only relevant for use via 'main()'
# like: 'python3 geigerlog/gdev_audio.py 7'


def getLongChunk(duration, recno):
    """record duration seconds of audio"""

    print("#{} - Recording for {} sec".format(recno, duration))

    reclen = int(sd.default.samplerate * duration)
    mystream = sd.InputStream(blocksize=reclen)
    mystream.start()
    record, overflowed = mystream.read(reclen) # get one record
    gglobs.AudioMultiPulses = record.reshape(-1)
    mystream.stop()


def plotDataT(AudioMultiPulses, inversrate):
    """plot record of sound data"""

    if len(AudioMultiPulses) == 0: return

    # Set "QT_STYLE_OVERRIDE" to avoid this message:
    #   QApplication: invalid style override 'gtk' passed, ignoring it.
    #   Available styles: Windows, Fusion
    os.environ["QT_STYLE_OVERRIDE"] = ""

    fig = plt.figure("Total", figsize=(14, 6), dpi=gglobs.hidpiScaleMPL)

    show = 0    # 1: accumulate the counts (don't delete the figure)
                # 0: delete last figure, and show a fresh record every time
    if    show: pass
    else:       fig.clf()

    x = np.arange(len(gglobs.AudioMultiPulses)) * inversrate * 1000 # create X-axis values
    y = gglobs.AudioMultiPulses                                     # Y-axis values
    #~print("plotDataT: x    :", len(x), x)
    #~print("plotDataT: y    :", len(y), y)
    plt.plot(x, y,  'k.', linestyle='solid', linewidth=0.3, markersize=0.5)
    plt.xlabel("millisec")
    plt.ylim(-35000, 35000)
    plt.pause(.5)


def main():
    """
    Start with: 'python3 gdev_audio.py' to get a list of available Sound Devices
    Start with: 'python3 gdev_audio.py N' to get a list of available Sound Devices,
                followed by N recordings and recoding plots from the default device
    """

    print("Available Sound Devices:")
    print(sd.query_devices())
    print()

    # Setting the soundcard
    sd.default.reset()
    sd.default.device       = (None, None)              # selects the default device
    sd.default.latency      = (1.0, 1.0)                # selects the default device
    sd.default.dtype        = ('int16', 'int16')        # signed 16 bit resolution for both input and output
    sd.default.channels     = (1, 1)                    # Mono for both input and output
    sd.default.samplerate   = 44100                     # options: 96000, 48000, 44100, 22050, 11025

    print("Sound Driver Settings:\n    DEVICE:{}, CHANNELS:{}, FORMAT:{}, Latency:{}, RATE:{}, Host API Index:{}"\
                    .format(
                            sd.default.device,
                            sd.default.channels,
                            sd.default.dtype,
                            sd.default.latency,
                            sd.default.samplerate,
                            sd.default.hostapi,
                           )
         )

    inversrate              = 1 / sd.default.samplerate
    gglobs.AudioMultiPulses = np.zeros(256)

    try:
        recs = abs(int(sys.argv[1])) # if none given on command line, an exception will be raised
    except:
        recs = 0

    for i in range(0, recs):
        try:
            getLongChunk(1.0, i + 1)
            plotDataT(gglobs.AudioMultiPulses, inversrate)
        except Exception as e:
            print("gdev_audio.py: main: Exception :", e)

    if recs > 0:
        plotDataT(gglobs.AudioMultiPulses, inversrate)
        print("Done recording. To Exit close graph, or press CTRL-C in terminal")
        plt.show()


if __name__ == '__main__':
    import matplotlib.pyplot as plt # plotting possible only when run as main
    main()
    print()

