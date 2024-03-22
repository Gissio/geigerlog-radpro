#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
GLaudiocheck.py - check the Audio signal by plotting live microphone signals
    NOTE: helpful for setting Audio amplification
    Start with: 'GLaudiocheck.py'
    Stop  with: Closing graph or Entering CTRL-C in terminal
"""

import argparse
import queue
import sys, time

from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import numpy as np
import sounddevice as sd

import os
# Set "QT_STYLE_OVERRIDE" to avoid this message:
#   QApplication: invalid style override 'gtk' passed, ignoring it.
#   Available styles: Windows, Fusion
os.environ["QT_STYLE_OVERRIDE"] = ""


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-l', '--list-devices', action='store_true',                                            help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument('channels',             type=int,           default=[1], nargs='*', metavar='CHANNEL',  help='input channels to plot (default: the first)')
parser.add_argument('-d', '--device',       type=int_or_str,                                                help='input device (numeric ID or substring)')
parser.add_argument('-w', '--window',       type=float,         default=200, metavar='DURATION',            help='visible time slot (default: %(default)s ms)')
parser.add_argument('-i', '--interval',     type=float,         default=30,                                 help='minimum time between plot updates (default: %(default)s ms)')
parser.add_argument('-b', '--blocksize',    type=int,                                                       help='block size (in samples)')
parser.add_argument('-r', '--samplerate',   type=float,                                                     help='sampling rate of audio device')
parser.add_argument('-n', '--downsample',   type=int,           default=10, metavar='N',                    help='display every Nth sample (default: %(default)s)')
args = parser.parse_args(remaining)
if any(c < 1 for c in args.channels):
    parser.error('argument CHANNEL: must be >= 1')
mapping = [c - 1 for c in args.channels]  # Channel numbers start with 1

print("mapping: ", mapping) # mapping = [0]

q = queue.Queue()


def audio_callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    # Fancy indexing with mapping creates a (necessary!) copy:
    q.put(indata[::args.downsample, mapping])


def update_plot(frame):
    """This is called by matplotlib for each plot update.

    Typically, audio callbacks happen more frequently than plot updates,
    therefore the queue tends to contain multiple blocks of audio data.
    """
    start = time.time()
    fncname = "update_plot: "
    global plotdata
    while True:
        try:
            data = q.get_nowait()
            #print("data: ", data)
        except queue.Empty:
            break
        shift = len(data)
        plotdata = np.roll(plotdata, -shift, axis=0)
        plotdata[-shift:, :] = data
    for column, line in enumerate(lines):
        line.set_ydata(plotdata[:, column])

    #print(fncname + "dur: {:0.3f} ms".format(time.time() - start))

    return lines


try:
    print("Audio Devices found on system:\n{}".format(sd.query_devices()))

    #############################################################
    # Best values for GeigerLog Audio, comment-out for defaults
    #~args.samplerate = 44100
    args.samplerate = None  # will mostly become 44100
    args.window     = 10000
    args.downsample = 1
    args.channels   = 1,
    args.interval   = 10
    #############################################################

    if args.samplerate is None:
        device_info = sd.query_devices(args.device, 'input')
        args.samplerate = device_info['default_samplerate']

    length = int(args.window * args.samplerate / (1000 * args.downsample))
    plotdata = np.zeros((length, len(args.channels)))

    fig, ax = plt.subplots(figsize=(15, 8))
    lines = ax.plot(plotdata)
    if len(args.channels) > 1:
        ax.legend(['channel {}'.format(c) for c in args.channels],loc='lower left', ncol=len(args.channels))
    ax.axis((0, len(plotdata), -1, 1))
    ax.set_yticks([0])
    ax.yaxis.grid(True)
    ax.tick_params(bottom=False, top=False, labelbottom=False, right=False, left=False, labelleft=False)
    fig.tight_layout(pad=0)

    start = time.time()
    stream = sd.InputStream(device=args.device, channels=max(args.channels), samplerate=args.samplerate, callback=audio_callback)
    print(" sd.InputStream(device=args.device, channels=max(args.channels), samplerate=args.samplerate, callback=audio_callback)", end=" ")
    print( args.device, max(args.channels), args.samplerate, audio_callback)
    ani = FuncAnimation(fig, update_plot, interval=args.interval, blit=True)

    with stream:
        plt.show()  # blocking


except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))
