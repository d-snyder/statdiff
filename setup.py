import os
from setuptools import setup

kwds = {}

# Read the long description from the README.txt
thisdir = os.path.abspath(os.path.dirname(__file__))
f = open(os.path.join(thisdir, 'README.txt'))
kwds['long_description'] = f.read()
f.close()


setup(
    name = 'statdiff',
    version = '0.1.0',
    author = 'David Snyder',
    author_email = 'code@dsnyder.com',
    description = "Utility to compare file statistic differences between two directories, local or remote.",
    license = "LGPL",
    classifiers = [
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Topic :: Utilities",
    ],

    py_modules = ["statdiff"],
    entry_points = dict(
        console_scripts = [
            "statdiff = statdiff:statdiff_main",
        ],
    ),
    install_requires = [
        'paramiko',
    ],
    tests_require = [
        'nose >= 0.10',
    ],
    test_suite = 'nose.collector',
    **kwds
)
