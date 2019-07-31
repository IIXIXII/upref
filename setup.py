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
# @package upref
# Markdown Tools develops for Gucihet Entreprises
#
###############################################################################

import sys
import io
import os
import os.path
import time
from shutil import rmtree
from setuptools import setup, find_packages, Command

import upref as mymodule

__root__ = os.path.abspath(os.path.join(os.path.dirname(__file__)))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(__root__, 'README.md'), encoding='utf-8') as f:
        __long_description__ = '\n' + f.read()
except FileNotFoundError:
    __long_description__ = mymodule.__doc__


# -------------------------------------------------------------------------------
# Increase the version number
# -------------------------------------------------------------------------------
def print_status(msg):
    print('>> {0}'.format(msg))

# -------------------------------------------------------------------------------
# Increase the version number
# -------------------------------------------------------------------------------
def increase_version():
    about = {}
    with open(os.path.join(__root__, mymodule.__name__,
                           'version.py'), "r") as ver:
        exec(ver.read(), about)

    current_version = about['__version_info__']
    new_version = (current_version[0],
                   current_version[1],
                   current_version[2] + 1)
    print_status("New version = %s.%s.%s" % new_version)

    with open(os.path.join(__root__, mymodule.__name__,
                           'version.py'), "w") as ver:
        ver.write("#!/usr/bin/env python\n")
        ver.write("# -*- coding: utf-8 -*-\n\n")
        ver.write("__version_info__ = %s\n" % repr(new_version))
        ver.write("__release_date__ = '%s'\n" %
                  time.strftime("%Y-%m-%d", time.gmtime()))


class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(msg):
        print_status(msg)

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(__root__, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('{0} setup.py sdist bdist_wheel '
                  '--universal'.format(sys.executable))

        self.status('Uploading the package to PyPI via Twine…')
        os.system('twine upload dist/*')

        sys.exit()

class IncreaseVersionCommand(Command):
    """Support setup.py increaseversion."""

    description = 'Increase the package version.'
    user_options = []

    @staticmethod
    def status(msg):
        print_status(msg)

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.status('Change version number…')
        increase_version()
        sys.exit()


class TagVersionCommand(Command):
    """Support setup.py increaseversion."""

    description = 'Increase the package version.'
    user_options = []

    @staticmethod
    def status(msg):
        print_status(msg)

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.status('Tag the version number {0}'.format(mymodule.__version__))
        self.status('Pushing git tags…')
        os.system('git tag v{0}'.format(mymodule.__version__))
        os.system('git push --tags')
        sys.exit()


# -------------------------------------------------------------------------------
# All setup parameter
# -------------------------------------------------------------------------------
setup(
    name=mymodule.__name__,  # pypi name
    version=mymodule.__version__,
    author=mymodule.__author__,
    author_email=mymodule.__email__,
    description=mymodule.__doc__,
    license=mymodule.__license__,
    long_description=__long_description__,
    long_description_content_type='text/markdown',

    url='https://github.com/IIXIXII/upref',

    # https://pypi.python.org/pypi?%3Aaction=list_classifiers.
    classifiers=[
        "Programming Language :: Python",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
    ],

    # Liste les packages à insérer dans la distribution
    # plutôt que de le faire à la main, on utilise la foncton
    # find_packages() de setuptools qui va cherche tous les packages
    # python recursivement dans le dossier courant.
    # C'est pour cette raison que l'on a tout mis dans un seul dossier:
    # on peut ainsi utiliser cette fonction facilement
    packages=find_packages(exclude=["test_*.py"]),
    # py_modules=['upref'],

    # Active la prise en compte du fichier MANIFEST.in
    include_package_data=True,

    package_data={
        # If any package contains *.txt or *.rst files, include them:
        'upref': ['*.conf', '*.ico',
                  './README.md', './LICENSE.md'],
    },

    setup_requires=["pytest-runner"],
    tests_require=["pytest"],

    cmdclass={
        'upload': UploadCommand,
        'increaseversion': IncreaseVersionCommand,
        'tagversion': TagVersionCommand,
    },
)
