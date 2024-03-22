# geigerlog-radpro

This is a modification of [GeigerLog 1.4.3](https://sourceforge.net/projects/geigerlog/) that enables live data logging and history download from Rad Pro devices.

## Installation

If you use Windows, simply download the latest binary from the [releases](https://github.com/Gissio/geigerlog-radpro/releases), uncompress it and execute the `geigerlog.bat` file.

If you use Linux or macOS, follow the installation instructions from the [manual](docs/GeigerLog-Manual-v1.4.1.pdf) and run `src/geigerlog`.

## Use

To connect to a Rad Pro device:

* Start GeigerLog.
* Connect the Rad Pro device to your computer.
* Click on the second icon of the toolbar, or select "Connect Devices ..." from the "Device" menu.

To log live data:

* Click on the "Quick Log" button to start logging data.
* "CPM" data is Rad Pro's instantaneous counts per minute value. This value is averaged through Rad Pro's adaptive averaging algorithm.
* "CPS" data is the low-level counts per second value. This value is not averaged.
* Click on the "Stop Log" to stop logging.

You can also log data by creating or opening a log database by clicking on the "Log DB" button, and clicking then "Start Log".

To download datalogs from Rad Pro's memory:

* In the "History" menu, select "Rad Pro Series" and "Get New History From Device ..." (to download only new datalog records) or "Get All History From Device ..." (to download the entire datalog history).
