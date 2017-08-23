import unittest

import os
import shutil
import tempfile

from .. import arimage

class TestARImage(unittest.TestCase):
    _temp_path = None

    def setUp(self):
        self._temp_path = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._temp_path)

    def test_find_arimg_in_dir(self):
        subdir_path = os.path.join(self._temp_path, "subdir")
        os.makedirs(subdir_path)
        imgs = []

        for i in range(5):
            # Create 20 images in total, 10 with ".fits" ext and 10 with ".fts" ext
            # Half of each extension goes in a sub directory to test recursion option
            img_prefix_with_base_path = os.path.join(self._temp_path, "testimg-" + str(i))
            img_prefix_with_sub_path = os.path.join(subdir_path, "testimg-" + str(i))
            imgs.append(arimage.ARImage(img_prefix_with_base_path + ".fits", new_file=True))
            imgs.append(arimage.ARImage(img_prefix_with_base_path + ".fts", new_file=True))
            imgs.append(arimage.ARImage(img_prefix_with_sub_path + ".fits", new_file=True))
            imgs.append(arimage.ARImage(img_prefix_with_sub_path + ".fts", new_file=True))

        for img in imgs:
            img.saveToDisk()

        base_dir_imgs = arimage.find_arimgs_in_dir(self._temp_path, recursive=False)
        all_imgs = arimage.find_arimgs_in_dir(self._temp_path, recursive=True)

        # Check the number of images found
        self.assertEqual(len(base_dir_imgs), 10)
        self.assertEqual(len(all_imgs), 20)

        # Assert ARImage type
        for img in base_dir_imgs:
            self.assertTrue(isinstance(img, arimage.ARImage))
        for img in all_imgs:
            self.assertTrue(isinstance(img, arimage.ARImage))
