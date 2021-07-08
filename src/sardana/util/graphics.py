#!/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
##
# This file is part of Sardana
##
# http://www.sardana-controls.org/
##
# Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
# Sardana is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
##
# Sardana is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
##
# You should have received a copy of the GNU Lesser General Public License
# along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

"""This package provides graphics related helper functions"""

import os
import sys


def xsession_available():
    """
    Checks if an X-session is available.

    Returns:
        bool: True when an X-session is available. False when not.
    """

    ret_val = True

    if sys.platform.startswith("linux"):
        # No display environment
        if os.environ.get("DISPLAY") is None:
            ret_val = False

        # In docker without X-session auth
        elif not os.path.exists("/tmp/.X11-unix"):
            ret_val = False

    return ret_val
