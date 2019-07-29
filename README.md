upref 🐸
========

Upref is a small python module to grab and save some user data like login, password, url (mainly string data). After some projects, I want a simple method to find the right login and url from the user and save it in the personnal data of the user.

[![Wheel Status](https://img.shields.io/pypi/wheel/upref.svg?style=flat)](https://pypi.python.org/pypi/upref/)
[![Latest Version](https://img.shields.io/pypi/v/upref.svg?style=flat)](https://pypi.python.org/pypi/upref/)
[![Total download](https://img.shields.io/github/downloads/IIXIXII/upref/total.svg?style=flat)](https://github.com/IIXIXII/upref/releases)
[![License](https://img.shields.io/github/license/IIXIXII/upref.svg?style=flat)](https://github.com/IIXIXII/upref/blob/master/LICENSE.md)
[![Build Status](https://img.shields.io/travis/IIXIXII/upref/master.svg?style=flat)](https://travis-ci.org/IIXIXII/upref)
[![Documentation Status](https://img.shields.io/readthedocs/upref.svg?style=flat)](https://upref.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://img.shields.io/coveralls/github/IIXIXII/upref/master.svg?style=flat)](https://coveralls.io/github/IIXIXII/upref?branch=master)

Installation
------------

Installing upref with pip:

    $ pip install upref

Basic Usage
------------

Here is the first example. The code fetch the URL from the user parameter

    import upref
  
    user_data = upref.get_pref(
        {"url": {"label": "The application url"}},
        "example01")
  
    print("URL is {}".format(user_data['url']))

This code create a file in the user folder. And this file will be read again during the next run.

    url:
      label: The application url
      value: http://www.test.org/

Code example
------------

    import upref
    data = upref.get_pref(
        {
            'login': {'label': "Your login"},
            'passwd': {'label': "Your secret password",
                    'type': "Password"},
        },
        name="example02")
    print("Your login is %s" % data['login'])
    print("Your password (not so secret) is %s" % data['passwd'])

At the first execution, there is a window to grab the data. The second execution, there will be no windows, the data are only read from the file.

All data are saved in a yaml file at %APPDATA%/.upref/example02.conf or \~/.local/share/.upref/example02.conf.

    login:
      label: Your login
      value: My login
    passwd:
      label: Your secret password
      value: Password

Features
------------

- Read and save small amount of data (url, login, )
- Small gui to ask data from the user
- Text option is avaible

License
-------

The upref is licensed under the terms of the MIT license and is available for free.

MIT © Florent
