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
# Standard function
###############################################################################

import logging
import sys
import os
import os.path
import collections
import tempfile
from copy import deepcopy
import yaml


if (__package__ in [None, '']) and ('.' not in __name__):
    import gui
    import tty
else:
    from . import gui
    from . import tty

###############################################################################
# The filename of the default configuration
###############################################################################
__DEFAULT_CONF_FILENAME__ = "default.conf"

###############################################################################
# The filename of the default configuration
###############################################################################
__EXT_FILENAME__ = ".conf"

###############################################################################
# The filename of the default configuration
###############################################################################
__UPREF_FOLDER__ = ".upref"


###############################################################################
# Read a conf file and return the dict
###############################################################################
def load_conf(filename):
    logging.debug('Load the configuration file: %s', filename)
    result = {}

    filename = os.path.abspath(filename)

    if not os.path.isfile(filename):
        logging.warning('The configuration file does not exists.')
        logging.warning('The configuration filename is %s', filename)
        return result

    with open(filename, 'r') as ymlfile:
        result = yaml.load(ymlfile, Loader=yaml.FullLoader)

    return result

###############################################################################
# Read a conf file and return the dict
###############################################################################
def save_conf(conf, filename):
    logging.debug('Save the configuration file: %s', filename)
    filename = os.path.abspath(filename)

    if os.path.isfile(filename):
        logging.info('The configuration file already exists.')

    folder = os.path.split(filename)[0]
    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)

    with open(filename, 'w') as outfile:
        yaml.dump(conf, outfile, default_flow_style=False)

    return conf


###############################################################################
# Read a conf file and return the dict
###############################################################################
def default_conf():
    logging.debug('Load the default configuration.')
    filename = os.path.join(__get_this_folder(), __DEFAULT_CONF_FILENAME__)
    return load_conf(filename)


###############################################################################
# Read the current upref of the user
#
# @param name the name of the preference file (we add the extension .upref)
# @return the complet filename of the upref file
###############################################################################
def upref_filename(name):
    upref_folder = None
    if sys.platform == "win32":
        upref_folder = os.path.join(os.getenv("APPDATA"), __UPREF_FOLDER__)
    elif sys.platform == "platform_value":
        upref_folder = os.path.join(os.path.expanduser("~"),
                                    ".local", "share", __UPREF_FOLDER__)

    filename = os.path.join(upref_folder, name + __EXT_FILENAME__)

    return filename


###############################################################################
# Read the current upref of the user
#
# @param name the name of the preference file (we add the extension .upref)
# @return the dict with the preference
###############################################################################
def current_upref(name):
    logging.debug('Load the current preference for %s.', name)
    return load_conf(upref_filename(name))


###############################################################################
# Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
# updating only top-level keys, dict_merge recurses down into dicts nested
# to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
# ``dct``.
#
# This version will return a copy of the dictionary and leave the original
#     arguments untouched.
#
# The optional argument ``add_keys``, determines whether keys which are
#     present in ``merge_dict`` but not ``dct`` should be included in the
#     new dict.
#
#
# Code from https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
#
# Args:
#         dct (dict) onto which the merge is executed
#         merge_dct (dict): dct merged into dct
#         add_keys (bool): whether to add new keys
#
# Returns:
#         dict: updated dict
###############################################################################
def dict_merge(dct, merge_dct, add_keys=True):
    dct = deepcopy(dct)

    if not add_keys:
        merge_dct = {
            k: merge_dct[k]
            for k in set(dct).intersection(set(merge_dct))
        }

    for k, value in merge_dct.items():
        if isinstance(dct.get(k), dict) \
           and isinstance(value, collections.Mapping):
            dct[k] = dict_merge(dct[k], value, add_keys=add_keys)
        else:
            dct[k] = value
    return dct


###############################################################################
# Get the value of preference or setting
###############################################################################
def get_pref(data_description, name, interface="gui", force_renew=False):
    # And finally merged with the data from the user preference
    current_data = dict_merge(data_description, current_upref(name))
    default = default_conf()

    not_all_values_are_set = not all_values_are_set(current_data)
    while not_all_values_are_set or force_renew:
        force_renew = False
        completed_data = dict_merge(default, current_data)
        if interface == "gui":
            completed_data = gui.get_data(completed_data)
        else:
            completed_data = tty.get_data(completed_data)

        for key in completed_data:
            if not key.endswith("__") and not key.startswith("__"):
                value = completed_data[key].get('value')
                if value is None or len(value) == 0:
                    current_data[key]['value'] = value

        save_conf(current_data, upref_filename(name))
        not_all_values_are_set = not all_values_are_set(current_data)
        if not_all_values_are_set:
            if interface == "gui":
                gui.message("You need to fill all the data")
            else:
                tty.message("You need to fill all the data")

    return conv_description_to_raw(current_data)

###############################################################################
# Conversion from the direct pref dict to a dict of descripiton
###############################################################################
def all_values_are_set(data_description):
    result = True
    for key in data_description:
        if not key.endswith("__") and not key.startswith("__"):
            value = data_description[key].get('value')
            if value is None or len(value) == 0:
                result = False

    return result

###############################################################################
# Conversion from the direct pref dict to a dict of descripiton
###############################################################################
def conv_raw_to_description(data):
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = value
        else:
            result[key] = {'value': value}
    return result

###############################################################################
# Conversion from the direct pref dict to a dict of descripiton
###############################################################################
def conv_description_to_raw(data_description):
    result = {}
    for data in data_description:
        if not data.endswith("__") and not data.startswith("__"):
            if 'value' in data_description[data]:
                result[data] = data_description[data]['value']
            else:
                logging.error("No value in the pref %s", data)

    return result

###############################################################################
# Get the value of preference or setting
###############################################################################
def set_pref(data, name, data_description=None):
    # read the current description if there is none
    if data_description is None:
        data_description = current_upref(name)

    data = dict_merge(data_description, conv_raw_to_description(data))
    save_conf(data, upref_filename(name))

###############################################################################
# Remove the preference file
###############################################################################
def remove_pref(name):
    filename = upref_filename(name)
    if os.path.isfile(filename):
        logging.debug('Remove the configuration file: %s', filename)
        os.remove(filename)

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

    ex_conf = load_conf(os.path.join(__get_this_folder(), "example1.conf"))
    data_ex1 = get_pref(ex_conf, "example1")
    print("Ex1: url=%s" % data_ex1['url'])
    remove_pref("example1")
    data_ex1 = get_pref(ex_conf, "example1")
    print("Ex1: url=%s" % data_ex1['url'])

    logging.info('Finished')
    # ------------------------------------


###############################################################################
# Call main function if the script is main
# Exec only if this script is runned directly
###############################################################################
if __name__ == '__main__':
    __set_logging_system()
    __main()
