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
# wxPython input
###############################################################################

import logging
import sys
import os
import os.path
import tempfile
import wx

__all__ = ['get_data']

###############################################################################
# Build a widget to collect the data
###############################################################################
def get_widget_style(style):
    style = style.strip().upper()
    if style == "PASSWORD" or style == "PASSWD" or style == "PASS":
        return wx.TE_PASSWORD

    return None

###############################################################################
# Build a widget to collect the data
###############################################################################
def get_widget(parent, data):
    result = {}
    label = ""
    if 'label' in data:
        label = data['label']

    result['label'] = wx.StaticBox(parent, wx.ID_ANY, label)
    result['sizer'] = wx.StaticBoxSizer(result['label'], wx.HORIZONTAL)

    sizer = wx.BoxSizer(wx.VERTICAL)
    if 'description' in data:
        result['description'] = wx.StaticText(
            result['label'], label=data['description'])
        sizer.Add(result['description'],
                  0, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND, 2)

    if 'type' in data:
        result['value'] = wx.TextCtrl(result['label'],
                                      style=get_widget_style(data['type']))
    else:
        result['value'] = wx.TextCtrl(result['label'])

    if 'value' in data and data['value'] is not None:
        result['value'].SetValue(data['value'])
    sizer.Add(result['value'], 0, wx.ALL | wx.ALIGN_RIGHT | wx.EXPAND, 2)

    result['sizer'].Add(sizer, 1, wx.ALL | wx.EXPAND, 2)

    return result


###############################################################################
# Main dialog in wxPython
###############################################################################
class PrefDialog(wx.Dialog):
    def __init__(self, parent, data):
        super(PrefDialog, self).__init__(
            parent,
            style=wx.DEFAULT_DIALOG_STYLE)

        self.data_description = data
        if '__gui__' not in self.data_description:
            self.data_description['__gui__'] = {}
        self.init_ui()

    def init_ui(self):
        if 'title' in self.data_description['__gui__']:
            self.SetTitle(self.data_description['__gui__']['title'])

        if 'icon' in self.data_description['__gui__']:
            data_ico = self.data_description['__gui__']['icon']
            ico_locations = []
            ico_locations.append(data_ico)
            ico_locations.append(os.path.abspath(data_ico))
            loca_path = os.path.split(__file__)[0]
            ico_locations.append(os.path.join(loca_path, data_ico))
            loca_path = os.path.split(sys.executable)[0]
            ico_locations.append(os.path.join(loca_path, data_ico))

            for loc in ico_locations:
                if os.path.isfile(loc):
                    self.SetIcon(wx.Icon(loc))
                    break

        self.panel = wx.Panel(self)
        self.data_widget = {}

        sizer = wx.BoxSizer(wx.VERTICAL)
        for key in self.data_description:
            if not key.endswith("__") and not key.startswith("__"):
                self.data_widget[key] = get_widget(self.panel,
                                                   self.data_description[key])
                sizer.Add(self.data_widget[key]['sizer'],
                          0, wx.ALL | wx.EXPAND, 5)

        # button
        button_label = "OK"
        if 'button_label' in self.data_description['__gui__']:
            button_label = self.data_description['__gui__']['button_label']

        button = wx.Button(self.panel, wx.ID_ANY, label=button_label)
        button.SetDefault()
        button.Bind(wx.EVT_BUTTON, self.on_ok)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        sizer.Add(button, 0, wx.ALL | wx.ALIGN_RIGHT, 12)
        sizer.SetSizeHints(self)
        self.panel.SetAutoLayout(True)
        self.panel.SetSizerAndFit(sizer)
        self.panel.Layout()
        self.Centre()

    def on_ok(self, event):
        del event
        logging.info('Read the new value')
        for key in self.data_widget:
            value = self.data_widget[key]['value'].GetValue()
            if value is not None and len(value) > 0:
                self.data_description[key]['value'] = value
        self.Destroy()

    def on_close(self, event):
        del event
        logging.info('No new value...')
        self.Destroy()

###############################################################################
# Get the data from the user
###############################################################################
def get_data(data_description):
    app = wx.App()
    dialog = PrefDialog(parent=None, data=data_description)
    dialog.Show()
    app.MainLoop()
    app.Destroy()
    return dialog.data_description


###############################################################################
# Display a message
###############################################################################
def message(msg_txt, title):
    app = wx.App()
    wx.MessageBox(msg_txt, title, wx.OK | wx.ICON_INFORMATION)
    app.Destroy()


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
            'icon': 'tower.ico',
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
