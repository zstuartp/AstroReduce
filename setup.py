#!/usr/bin/env python

import os

from setuptools import setup

PKG_NAME="astroreduce"
PKG_ROOT_DIR=os.path.join(".", PKG_NAME)

# Open VERSION file and read version string
PKG_VERSION_FILE_PATH=os.path.join(PKG_ROOT_DIR, "VERSION")
try:
    version_file = open(PKG_VERSION_FILE_PATH)
except OSError as err:
    print("Failed to open version file at " + PKG_VERSION_FILE_PATH + ".")
    exit(1)
PKG_VERSION=version_file.read().strip()

setup(
	name=PKG_NAME,
	version=PKG_VERSION,
	author="",
	description="Astronomy data reduction program",
	packages=[PKG_NAME],
        include_package_data=True
)
