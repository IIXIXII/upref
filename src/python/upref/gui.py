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
# Standard function
###############################################################################

import logging
import sys
import os
import os.path
import tempfile
import wx

class LoginDialog(wx.Dialog):
    def __init__(self, *args, **kwargs):
        super(LoginDialog, self).__init__(*args, **kwargs)

        # Attributes
        self.panel = LoginPanel(self)

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetInitialSize()

    def GetUsername(self):
        return self.panel.GetUsername()

    def GetPassword(self):
        return self.panel.GetPassword()

class LoginPanel(wx.Panel):
    def __init__(self, parent):
        super(LoginPanel, self).__init__(parent)

        # Attributes
        self._username = wx.TextCtrl(self)
        self._passwd = wx.TextCtrl(self, style=wx.TE_PASSWORD)

        # Layout
        sizer = wx.FlexGridSizer(2, 2, 8, 8)
        sizer.Add(wx.StaticText(self, label="Username:"),
                  0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self._username, 0, wx.EXPAND)
        sizer.Add(wx.StaticText(self, label="Password:"),
                  0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self._passwd, 0, wx.EXPAND)
        msizer = wx.BoxSizer(wx.VERTICAL)
        msizer.Add(sizer, 1, wx.EXPAND | wx.ALL, 20)
        btnszr = wx.StdDialogButtonSizer()
        button = wx.Button(self, wx.ID_OK)
        button.SetDefault()
        btnszr.AddButton(button)
        msizer.Add(btnszr, 0, wx.ALIGN_CENTER | wx.ALL, 12)
        btnszr.Realize()

        self.SetSizer(msizer)

    def GetUsername(self):
        return self._username.GetValue()

    def GetPassword(self):
        return self._passwd.GetValue()


# if __name__ == "__main__":
#     app = MyApp(False)
#     app.MainLoop()


###############################################################################
# Main dialog in wxPython
###############################################################################
def get_widget(parent, data):
    result = {}
    label = ""
    if 'label' in data:
        label = data['label']

    result['label'] = wx.StaticBox(parent, wx.ID_ANY, label)
    result['sizer'] = wx.StaticBoxSizer(wx.VERTICAL, parent,
                                        label=label)

    if 'description' in data:
        result['description'] = wx.StaticText(
            result['label'], label=data['description'])
        # result['sizer'].Add(result['description'], 0, wx.ALIGN_CENTER_VERTICAL)

    result['value'] = wx.TextCtrl(result['label'])
    # result['sizer'].Add(result['value'], 0, wx.ALIGN_CENTER_VERTICAL)

    return result


###############################################################################
# Main dialog in wxPython
###############################################################################
class PrefDialog(wx.Dialog):
    def __init__(self, parent, data):
        super(PrefDialog, self).__init__(
            parent,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.data_description = data
        if '__gui__' not in self.data_description:
            self.data_description['__gui__'] = {}
        self.init_ui()

    def init_ui(self):
        if 'title' in self.data_description['__gui__']:
            self.SetTitle(self.data_description['__gui__']['title'])

        self.panel = wx.Panel(self)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.data_widget = {}
        for key in self.data_description:
            if not key.endswith("__") and not key.startswith("__"):
                self.data_widget[key] = get_widget(self.panel,
                                                   self.data_description[key])
                sizer.Add(self.data_widget[key]['label'],
                          0, wx.ALL | wx.CENTER, 5)

        # buttons
        button_label = "OK"
        if 'button_label' in self.data_description['__gui__']:
            button_label = self.data_description['__gui__']['button_label']
        button = wx.Button(self.panel, wx.ID_OK, label=button_label)
        button.SetDefault()
        sizer.Add(button, 0, wx.ALIGN_CENTER | wx.ALL, 12)
        button.Bind(wx.EVT_BUTTON, self.on_ok)
        self.panel.SetSizer(sizer)

        # self.SetSize((300, 690))
        self.Centre()

    def on_ok(self, event):
        del event
        self.Destroy()


###############################################################################
# Remove the preference file
###############################################################################
def get_data(data_description):
    app = wx.App()
    dialog = PrefDialog(parent=None, data=data_description)
    dialog.Show()
    app.MainLoop()

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
            'icon': 'the icon',
            'button_label': 'OKOK',
        },
        'url': {
            'label': 'URL',
            'description': 'Could you give me a coffee',
        }
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
