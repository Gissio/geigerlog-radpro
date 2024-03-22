#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GeigerLog - A combination of data logger, data presenter, and data analyzer to
            handle Geiger counters as well as environmental sensors for
            Temperature, Pressure, Humidity, CO2, and else

Start as 'geigerlog -h' for help on available options and commands
Use document 'GeigerLog-Manual-v<version number>.pdf' for further details

This file serves as front-end to verify that Python has version 3 before
real GeigerLog is started.
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


# Test for Python being at least version 3; exit otherwise
import sys
svi            = sys.version_info
currentVersion = "{}.{}.{}".format(svi[0], svi[1], svi[2])
msg            = ""

if svi < (3,) :
    msg += """
        This version of GeigerLog requires Python in version 3.7 or later!
        Your Python version is: {}.

        Python 2 is deprecated since January 1, 2020. The preferred way is to
        upgrade to Python 3. You can download a new version of Python from:
        https://www.python.org/downloads/

        If you can't do that, you can download an old copy of GeigerLog
        which still runs on Python 2, from:
        https://sourceforge.net/projects/geigerlog/

        The last version of GeigerLog for Python 2 is GeigerLog 0.9.06.
        Future versions will all be for Python 3.
        """.format(currentVersion)

    print(msg)
    sys.exit(1)


import gmain
gmain.main()
