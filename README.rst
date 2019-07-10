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


Installation
------------

Installing upref with pip::

    $ pip install upref


Basic Usage
-----------

Here is the first example. The code fetch the URL from the user parameter

.. literalinclude:: examples/example01.py

This code create a file in the user folder. And theis file will be read again during the next run.

.. literalinclude:: examples/example01.conf
   :language: yaml


Code example
------------

.. literalinclude:: examples/example02.py

At the first execution, there is a window to grab the data. The second execution, there will be no windows, the data are only read from the file.

All data are saved in a yaml file at %APPDATA%/.upref/example02.conf or ~/.local/share/.upref/example02.conf.

.. literalinclude:: examples/example02.conf
   :language: yaml


Features
--------

* Read and save small amount of data (url, login, )
* Small gui to ask data from the user
* Text option is avaible


License
-------

The upref is licensed under the terms of the MIT license and is available for free.

MIT © Florent
