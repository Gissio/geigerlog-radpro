# geigerlog-radpro

**This repository is no longer maintained.**

This was a community fork/patch of GeigerLog (based on version 1.4.3) that added support for devices running the **Rad Pro** custom firmware (e.g. FNIRSI GC-01, GQ GMC-800 with Rad Pro, etc.).

**Official GeigerLog has natively supported Rad Pro devices since later versions.**

Please use the current official release instead:

**Latest GeigerLog**: https://sourceforge.net/projects/geigerlog/

For questions, bug reports, feature requests, or help with Rad Pro devices in GeigerLog, please use the official discussion forum:

**GeigerLog Discussion**: https://sourceforge.net/p/geigerlog/discussion/

## Installation

If you use Windows, simply download the latest binary from the [releases](https://github.com/Gissio/geigerlog-radpro/releases) and decompress it.

If you use Linux or macOS, follow the installation instructions in the [GeigerLog manual](docs/GeigerLog-Manual-v1.4.1.pdf).

## Use

Starting GeigerLog:

* If you use Windows, download the latest release start `geigerlog.exe`.
* If you use Linux or macOS, download the source code and start `src/geigerlog.py`.

To connect to a Rad Pro device:

* Connect the Rad Pro device to your computer.
* Click on the second icon of the toolbar, or select “Connect Devices ...” from the “Device” menu.
* The device's clock is automatically synchronized to your computer's clock.

To live log data:

* Click on the “Quick Log” button to start logging.
* “CPS” data is the low-level counts per second value. To average the data, use the “MvAvg” function.
* Click on the “Stop Log” button to stop logging.

You can also live log data by creating or opening a log database: click on “Log DB” button, select the file name for your log database, and then click on “Start Log”.

To download datalogs from Rad Pro's flash memory:

* In the “History” menu, select “Rad Pro Series” and “Get New History From Device ...” to download only new (not yet downloaded) datalog records, or “Get All History From Device ...” to download the entire datalog.


