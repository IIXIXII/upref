#!/usr/bin/env python
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
# pylint: skip-file

from recommonmark.parser import CommonMarkParser
import os
import sys
import recommonmark
from recommonmark.transform import AutoStructify
import textwrap
import upref as mymodule

sys.path.insert(0, os.path.abspath('..'))


# -- Project information -----------------------------------------------------

project = mymodule.__name__
copyright = mymodule.__copyright__
author = mymodule.__author__
release = mymodule.__version__
language = 'en'

# -- General configuration ---------------------------------------------------

html_static_path = ['layout']
templates_path = ['_templates']
exclude_patterns = []
extensions = ['m2r',
              'breathe',
              'exhale',
              ]
source_suffix = ['.rst', '.md']

master_doc = 'index'


# -- Setup the breathe extension ---------------------------------------------
breathe_projects = {
    "UPref": "./doxyoutput/xml"
}
breathe_default_project = "UPref"

# -- Setup the exhale extension ---------------------------------------------
exhale_args = {
    # These arguments are required
    "containmentFolder": "./api",
    "rootFileName": "library_root.rst",
    "rootFileTitle": "Library API",
    "doxygenStripFromPath": "..",
    # Suggested optional arguments
    "createTreeView": True,
    "treeViewIsBootstrap": True,
    # TIP: if using the sphinx-bootstrap-theme, you need
    # "treeViewIsBootstrap": True,
    "exhaleExecutesDoxygen": True,
    "exhaleDoxygenStdin": textwrap.dedent('''
        INPUT = ../upref
        EXCLUDE_SYMBOLS  = *test_* \
                         __main \
                         __set_logging_system \
                         __get_this_filename \
                         __get_this_folder \
                         is_frozen \
                         __launch_test
    ''')
}


# -- Options for HTML output -------------------------------------------------
pygments_style = 'friendly'

# -- Options for HTML output -------------------------------------------------
# on_rtd is whether we are on readthedocs.org,
# this line of code grabbed from docs.readthedocs.org
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:  # only import and set the theme if we're building docs locally
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
else:
    html_theme = 'default'
