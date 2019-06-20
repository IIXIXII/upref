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

import logging
import sys
import os
import os.path
import pytest

from upref.common import dict_merge
from upref.common import default_conf
from upref.common import upref_filename
from upref.common import remove_pref


def test_dict_merge():
    aaa = {
        'a': 1,
        'b': {
            'b1': 2,
            'b2': 3,
        },
    }
    bbb = {
        'a': 1,
        'b': {
            'b1': 4,
        },
    }

    assert dict_merge(aaa, bbb)['a'] == 1
    assert dict_merge(aaa, bbb)['b']['b2'] == 3
    assert dict_merge(aaa, bbb)['b']['b1'] == 4


def test_inserts_new_keys():
    """Will it insert new keys by default?"""
    aaa = {
        'a': 1,
        'b': {
            'b1': 2,
            'b2': 3,
        },
    }
    bbb = {
        'a': 1,
        'b': {
            'b1': 4,
            'b3': 5
        },
        'c': 6,
    }

    assert dict_merge(aaa, bbb)['a'] == 1
    assert dict_merge(aaa, bbb)['b']['b2'] == 3
    assert dict_merge(aaa, bbb)['b']['b1'] == 4
    assert dict_merge(aaa, bbb)['b']['b3'] == 5
    assert dict_merge(aaa, bbb)['c'] == 6

def test_does_not_insert_new_keys():
    """Will it avoid inserting new keys when required?"""
    aaa = {
        'a': 1,
        'b': {
            'b1': 2,
            'b2': 3,
        },
    }
    bbb = {
        'a': 1,
        'b': {
            'b1': 4,
            'b3': 5,
        },
        'c': 6,
    }

    assert dict_merge(aaa, bbb, add_keys=False)['a'] == 1
    assert dict_merge(aaa, bbb, add_keys=False)['b']['b2'] == 3
    assert dict_merge(aaa, bbb, add_keys=False)['b']['b1'] == 4
    try:
        assert dict_merge(aaa, bbb, add_keys=False)['b']['b3'] == 5
    except KeyError:
        pass
    else:
        raise Exception('New keys added when they should not be')

    try:
        assert dict_merge(aaa, bbb, add_keys=False)['b']['b3'] == 6
    except KeyError:
        pass
    else:
        raise Exception('New keys added when they should not be')


def test_default_conf():
    assert default_conf()['__gui__'] is not None
    assert 'lkjslfdqkjhslfdksq' not in default_conf()

def test_upref_filename():
    assert upref_filename("test") is not None
    assert upref_filename("test").endswith("test.conf")

    random_name = "lkhjlkhjlkhlkhjlqsdqs"
    remove_pref(random_name)
    assert not os.path.isfile(upref_filename(random_name))

    assert upref_filename(random_name) is not None

###############################################################################
# Find the filename of this file (depend on the frozen or not)
# This function return the filename of this script.
# The function is complex for the frozen system
#
# @return the filename of THIS script.
###############################################################################
def __get_this_filename():
    result = ""

    if getattr(sys, 'frozen', False):
        # frozen
        result = sys.executable
    else:
        # unfrozen
        result = __file__

    return result

###############################################################################
# Set up the logging system
###############################################################################
def __set_logging_system():
    log_filename = os.path.splitext(os.path.abspath(
        os.path.realpath(__get_this_filename())))[0] + '.log'
    logging.basicConfig(filename=log_filename, level=logging.DEBUG,
                        format='%(asctime)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(asctime)s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)


###############################################################################
# Launch the test
###############################################################################
def __launch_test():
    pytest.main(__get_this_filename())


##############################################################################
# Main script call only if this script is runned directly
###############################################################################
def __main():
    # ------------------------------------
    logging.info('Started %s', __get_this_filename())
    logging.info('The Python version is %s.%s.%s',
                 sys.version_info[0], sys.version_info[1], sys.version_info[2])

    __launch_test()

    logging.info('Finished')
    # ------------------------------------


###############################################################################
# Call main function if the script is main
# Exec only if this script is runned directly
###############################################################################
if __name__ == '__main__':
    __set_logging_system()
    __main()
