upref 🐸
========

Upref is a small python module to grab and save some user data like login, password, url (mainly string data).
After some projects, I want a simple method to find the right login and url from the user and save it in the personnal data of the user.

.. image:: https://img.shields.io/pypi/wheel/upref.svg?style=flat
   :target: https://pypi.python.org/pypi/upref/
   :alt: Wheel Status
.. image:: https://img.shields.io/pypi/v/upref.svg
   :target: https://pypi.python.org/pypi/upref/
   :alt: Latest Version
.. image:: https://img.shields.io/github/downloads/IIXIXII/upref/total.svg
   :target: https://github.com/IIXIXII/upref/releases
   :alt: Total download
.. image:: https://img.shields.io/github/license/IIXIXII/upref.svg
   :target: https://github.com/IIXIXII/upref/blob/master/LICENSE.md
   :alt: License

Installation
------------

Installing upref with pip::

    $ pip install upref


Basic Usage
-----------

Here is the first example. The code fetch the URL from the user parameter

.. code:: python

    import upref

    user_data = upref.get_pref(
        {"url": {"label": "The application url"}},
        "example01")

    print("URL is {}".format(user_data['url']))


This code create a file in the user folder. And this file will be read again during the next run.

.. code:: yaml

    url:
      label: The application url
      value: http://www.test.org/


Code example
------------

.. code:: python

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

All data are saved in a yaml file at %APPDATA%/.upref/example02.conf or ~/.local/share/.upref/example02.conf.

.. code:: yaml

    login:
      label: Your login
      value: My login
    passwd:
      label: Your secret password
      value: Password


Features
--------

* Read and save small amount of data (url, login, )
* Small gui to ask data from the user
* Text option is avaible


License
-------

The upref is licensed under the terms of the MIT license and is available for free.

MIT © Florent
