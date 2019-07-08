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

.. literalinclude:: ../examples/example01.py

This code create a file in the user folder. And theis file will be read again during the next run.

.. literalinclude:: ../examples/example01.conf
   :language: yaml





upref's documentation
=====================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   readme_link
   license_link

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
