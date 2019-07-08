upref 🐸
============

A small python module to grab and save some user data like login, password, url (mainly string data).

Motivation
----------

After some projects, I want a simple method to find the right login and url from the user and save it.

Code example
------------

    import upref
    data = upref.get_pref(
            {
                'login': {'label': 'Your login'},
                'passwd': {'label': "Your secret password"},
            },
            name="myprog")
    print("Your login is %s" % data['login'])
    print("Your password (not so secret) is %s" % data['passwd'])

At the first execution, there is a window to grab the data. The second execution, there will be no windows, the data are only read from the file.

All data are saved in a yaml file at %APPDATA%/.upref/myprog.conf or ~/.local/share/.upref/myprog.conf.

    # myprog.conf 
    login:
      label: Your login
      value: name
    passwd:
      label: Your secret password
      value: secret

Features
--------

* Read and save small amount of data (url, login, )
* Small gui to ask data from the user
* Text option is avaible

License
-------

The upref is licensed under the terms of the MIT license and is available for free.

MIT © Florent
