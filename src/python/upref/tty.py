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

###############################################################################
# wxPython input for preference
###############################################################################

import logging
import sys
import os
import os.path
import tempfile
import getpass

__all__ = ['get_data']

###############################################################################
# Get the data from the user
###############################################################################
def get_data(data_description):
    gui = data_description.get('__gui__')
    if 'title' in gui:
        print(gui['title'])
        print('-' * len(gui['title']))
        print()

    for key in data_description:
        if not key.endswith("__") and not key.startswith("__"):
            data = data_description[key]
            if 'label' in data:
                print(data['label'])
            if 'description' in data:
                print(data['description'])

            if 'type' in data_description[key] and \
                    data_description[key]['type'].upper().startswith("PASS"):
                data_description[key]['value'] = getpass.getpass("-->")
            else:
                data_description[key]['value'] = input("-->")

            print()

    if 'button_label' in gui:
        print(gui['button_label'])

    return data_description

###############################################################################
# Test the frozen situation of the executable
###############################################################################
def is_frozen():
    return getattr(sys, 'frozen', False)

###############################################################################
# Find the filename of this file (depend on the frozen or not)
# This function return the filename of this script.
# The function is complex for the frozen system
#
# @return the folder of THIS script.
###############################################################################
def __get_this_folder():
    return os.path.split(os.path.abspath(os.path.realpath(
        __get_this_filename())))[0]

###############################################################################
# Find the filename of this file (depend on the frozen or not)
# This function return the filename of this script.
# The function is complex for the frozen system
#
# @return the filename of THIS script.
###############################################################################
def __get_this_filename():
    result = ""

    if is_frozen():
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

    if is_frozen():
        log_filename = os.path.abspath(os.path.join(
            tempfile.gettempdir(),
            os.path.basename(__get_this_filename()) + '.log'))

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
# Main script call only if this script is runned directly
###############################################################################
def __main():
    # ------------------------------------
    logging.info('Started %s', __get_this_filename())
    logging.info('The Python version is %s.%s.%s',
                 sys.version_info[0], sys.version_info[1], sys.version_info[2])

    conf = {
        '__gui__': {
            'title': 'The title here',
            'icon': 'src/python/upref/tower.ico',
            'button_label': 'Cool baby',
        },
        'url': {
            'label': 'URL',
            'description': 'Could you give me a coffee not an URL',
        },
        'login': {
            'label': 'Login',
            'description': 'Could you give me a coffee again',
        },
        'logsdfin11': {
            'label': 'Login new one',
            'description': 'Could you give me a coffee black',
        },
        'logqqqin13': {
            'label': 'Logoff',
            'description': 'Could you give me a\nTEA',
        },
        'loginfsdf12': {
            'label': 'Password',
            'description': 'Could you give me a coffee again',
            'value': "lkjhlkhj",
            'type': "pass",
        },
    }

    get_data(conf)

    logging.info('Finished')
    # ------------------------------------


###############################################################################
# Call main function if the script is main
# Exec only if this script is runned directly
###############################################################################
if __name__ == '__main__':
    __set_logging_system()
    __main()
