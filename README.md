# geigerlog-radpro

This is a modification of [GeigerLog 1.4.3](https://sourceforge.net/projects/geigerlog/) that enables live data logging and datalog download for [Rad Pro](https://github.com/Gissio/radpro) devices.

## Installation

If you use Windows, simply download the latest binary from the [releases](https://github.com/Gissio/geigerlog-radpro/releases) and decompress it.

If you use Linux or macOS, follow the installation instructions in the [GeigerLog manual](docs/GeigerLog-Manual-v1.4.1.pdf).

## Use

Starting GeigerLog:

* If you use Windows, start `geigerlog.bat`.
* If you use Linux or macOS, start `src/geigerlog.py`.

To connect to a Rad Pro device:

* Connect the Rad Pro device to your computer.
* Click on the second icon of the toolbar, or select "Connect Devices ..." from the "Device" menu.
* The device's clock is automatically synchronized to your computer's clock.

To live log data:

* Click on the "Quick Log" button to start logging.
* "CPS" data is the low-level counts per second value.
* Click on the "Stop Log" button to stop logging.

You can also live log data by creating or opening a log database: click on "Log DB" button, select the file name for your log database, and then click on "Start Log".

To download datalogs from Rad Pro's flash memory:

* In the "History" menu, select "Rad Pro Series" and "Get New History From Device ..." to download only new (not yet downloaded) datalog records, or "Get All History From Device ..." to download the entire datalog.
