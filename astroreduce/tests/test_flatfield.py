import unittest

import os
import shutil
import tempfile
from typing import List

import numpy as np

from .. import arimage
from .. import flatfield

_DARKS_DIR = "darks"
_MDARKS_DIR = "mdarks"
_FLATS_DIR = "flats"
_MFLATS_DIR = "mflats"
_LIGHTS_DIR = "lights"
_OUTPUT_DIR = "output"

# Hot pixels
_hot_data = [
    np.array([
        [0, 65000, 0],
        [0, 0, 0],
        [0, 0, 0]]),
    np.array([
        [0, 0, 0],
        [0, 0, 65000],
        [0, 0, 0]]),
    np.array([
        [0, 0, 0],
        [65000, 0, 0],
        [0, 0, 0]]),
    np.array([
        [65000, 0, 0],
        [0, 0, 0],
        [0, 0, 65000]]),
    np.array([
        [65000, 0, 0],
        [0, 0, 0],
        [0, 65000, 0]]),
    np.array([
        [0, 0, 0],
        [0, 0, 65000],
        [65000, 0, 0]])]

# Flat data
_flat_data_base = np.array([
        [25832, 23182, 15771],
        [5226, 9340, 27285],
        [13194, 17725, 8694]])

# Dark data
_dark_data_base = np.array([
        [10, 30, 4],
        [96, 55, 43],
        [19, 8, 77]])

# Light data
_light_data_base = np.array([
        [3500, 5343, 888],
        [123, 1969, 82],
        [3695, 8220, 4701]])

def _create_test_arimg(
        path_prefix: str,
        file_name: str,
        img_kind: flatfield.ImageKind,
        img_data: np.array,
        img_exp: float,
        img_filter: str) -> arimage.ARImage:
    """ Create a new ARImage for testing """
    full_path = os.path.join(path_prefix, file_name)
    img = arimage.ARImage(full_path, new_file=True)
    img.exp_time = img_exp
    img.filter = img_filter
    img.img_kind = img_kind
    img.writeValues()
    img.fits_data = img_data
    img.saveToDisk()
    img.unloadData()
    return img

def _create_test_arimgs(
        path_prefix: str,
        img_kind: flatfield.ImageKind) -> List[arimage.ARImage]:
    """ Create a set of ARImages for testing """
    img_data = None
    img_filter = "Clear"
    img_exp = 1.0
    img_prefix = None
    imgs = []

    i = 0
    for hot in _hot_data:
        if img_kind == flatfield.ImageKind.DARK:
            img_data = _dark_data_base + hot
            img_prefix = "dark"
            subpath_prefix = os.path.join(path_prefix, _DARKS_DIR)
        elif img_kind == flatfield.ImageKind.FLAT:
            img_data = _flat_data_base + _dark_data_base + hot
            img_prefix = "flat"
            subpath_prefix = os.path.join(path_prefix, _FLATS_DIR)
        else: # img_kind == ImageKind.LIGHT
            img_data = ((_light_data_base
                        * (_flat_data_base / np.median(_flat_data_base)))
                        + _dark_data_base)
            img_prefix = "light"
            subpath_prefix = os.path.join(path_prefix, _LIGHTS_DIR)
        img = _create_test_arimg(
            subpath_prefix,
            img_prefix + "-testimg-" + str(i) + ".fts",
            img_kind,
            img_data,
            img_exp,
            img_filter)
        imgs.append(img)
        i += 1

    return imgs

_temp_base_path = None
_temp_darks_path = None
_temp_mdarks_path = None
_temp_flats_path = None
_temp_mflats_path = None
_temp_lights_path = None
_temp_output_path = None

def _setup_temp_img_dirs():
    """ Create the directory structure required for testing the flatfield module """
    global _temp_base_path
    global _temp_darks_path
    global _temp_mdarks_path
    global _temp_flats_path
    global _temp_mflats_path
    global _temp_lights_path
    global _temp_output_path

    _temp_base_path = tempfile.mkdtemp()

    _temp_darks_path  = os.path.join(_temp_base_path, _DARKS_DIR)
    _temp_mdarks_path = os.path.join(_temp_base_path, _MDARKS_DIR)
    _temp_flats_path  = os.path.join(_temp_base_path, _FLATS_DIR)
    _temp_mflats_path = os.path.join(_temp_base_path, _MFLATS_DIR)
    _temp_lights_path = os.path.join(_temp_base_path, _LIGHTS_DIR)
    _temp_output_path = os.path.join(_temp_base_path, _OUTPUT_DIR)

    if not os.path.exists(_temp_darks_path):
        os.makedirs(_temp_darks_path)
    if not os.path.exists(_temp_mdarks_path):
        os.makedirs(_temp_mdarks_path)
    if not os.path.exists(_temp_flats_path):
        os.makedirs(_temp_flats_path)
    if not os.path.exists(_temp_mflats_path):
        os.makedirs(_temp_mflats_path)
    if not os.path.exists(_temp_lights_path):
        os.makedirs(_temp_lights_path)
    if not os.path.exists(_temp_output_path):
        os.makedirs(_temp_output_path)

def _remove_temp_img_dirs():
    global _temp_base_path
    global _temp_darks_path
    global _temp_mdarks_path
    global _temp_flats_path
    global _temp_mflats_path
    global _temp_lights_path
    global _temp_output_path
    shutil.rmtree(_temp_base_path)
    _temp_base_path   = None
    _temp_darks_path  = None
    _temp_mdarks_path = None
    _temp_darks_path  = None
    _temp_mdarks_path = None
    _temp_darks_path  = None
    _temp_mdarks_path = None

class TestDarks(unittest.TestCase):
    _darks = None

    def setUp(self):
        _setup_temp_img_dirs()
        self._darks = _create_test_arimgs(_temp_base_path, flatfield.ImageKind.DARK)

    def tearDown(self):
        _remove_temp_img_dirs()

    def test_sort_darks(self):
        darks_sorted = flatfield.sort_arimgs_as_kind(self._darks, flatfield.ImageKind.DARK)
        # Only one key should be present (1 sec exposure)
        self.assertEqual(len(darks_sorted), 1)

        for key, value in darks_sorted.items():
            # Key should be equal to 1 (for 1 sec exposure)
            self.assertEqual(key, 1)
            # All 6 darks should be here
            self.assertEqual(len(value), 6)

    def test_create_master_darks(self):
        self.assertTrue(True)

class TestFlats(unittest.TestCase):
    _darks = None
    _flats = None

    def setUp(self):
        _setup_temp_img_dirs()
        self._darks = _create_test_arimgs(_temp_base_path, flatfield.ImageKind.DARK)
        self._flats = _create_test_arimgs(_temp_base_path, flatfield.ImageKind.FLAT)

    def tearDown(self):
        _remove_temp_img_dirs()

    def test_sort_flats(self):
        flats_sorted = flatfield.sort_arimgs_as_kind(self._flats, flatfield.ImageKind.FLAT)
        # Only one key should be present (1 filter, "Clear")
        self.assertEqual(len(flats_sorted), 1)

        for key, value in flats_sorted.items():
            # Key should be equal to "Clear"
            self.assertEqual(key, "Clear")
            # All 6 flats should be here
            self.assertEqual(len(value), 6)
