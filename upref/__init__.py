﻿#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (c) 2018 Florent TOURNOIS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
###############################################################################

###############################################################################
# @package upref
# Small tool to grab data from the user and to save it
###############################################################################

from .core import get_pref
from .core import set_pref
from .core import remove_pref
from .core import current_upref
from .core import upref_filename
from .core import load_data
from .core import save_data
from .core import load_conf
from .version import __version_info__
from .version import __release_date__

__version__ = '.'.join(str(c) for c in __version_info__)
__author__ = "Florent Tournois"
__copyright__ = "Copyright 2018, Florent Tournois"

__credits__ = ["Arnaud Boidard, Bernard Migaud"]
__license__ = "MIT"
__maintainer__ = "Florent Tournois"
__email__ = "florent.tournois@gmail.fr"
__status__ = "Production"


__all__ = [
    'get_pref', 'set_pref', 'remove_pref',
    'upref_filename',
    'load_conf',
    'load_data', 'save_data',
    'current_upref',
]
