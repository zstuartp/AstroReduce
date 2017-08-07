# BSD 3-Clause License
#
# Copyright (c) 2017, Zackary Parsons
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#
# Python3 verification script for AstroReduce
#
# This script is meant to be run from "scripts/verify.sh", not directly.
#
# To verify that AstroReduce is correcting images properly, we create a 3x3 fits
# image. We add dark current and vignetting, then we make copies with several
# different "hot" pixel masks.  The hot pixels simulate cosmic ray hits and
# check that the median-combine routine is working correctly. Once the images
# are created, AstroReduce is run in the test directory and the output files
# are compared compared with the original 3x3 image.
#

import numpy as np
import sys

from astroreduce import reduce

if "astroreduce" not in sys.modules or test_data_dir == None:
    print ("This script is not meant to be run directly, please run the test.sh script in the base directory.")
    sys.exit(1)

test_fits_suffix = "gen-test.fts"

mflat_data_expect = [1]
dark_data = [1]
mdark_data_expect = [1]
light_data = [1]
lout_data_expect = [1]

# Hot pixels
hot_data = [
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
flat_data_base = np.array([
		[25832, 23182, 15771],
		[5226, 9340, 27285],
		[13194, 17725, 8694]])

# Dark data
dark_data_base = np.array([
		[10, 30, 4],
		[96, 55, 43],
		[19, 8, 77]])

# Light
light_data_base = np.array([
		[3500, 5343, 888],
		[123, 1969, 82],
		[3695, 8220, 4701]])

# Create raw flat images
flat_imgs = []
print ("Creating raw flats... ", end="")
i = 0
for hot in hot_data:
	flat_img = reduce.AstroImage(test_data_dir+"flats/Flat-"+str(i)+"-"+test_fits_suffix, new_file=True)
	flat_img.exp_time = 1.0
	flat_img.filter = "Clear"
	flat_img.img_type = reduce.ImageType.FLAT
	flat_img.writeValues()
	flat_img.fits_data = flat_data_base + dark_data_base + hot
	flat_img.saveToDisk()
	flat_img.unloadData()
	flat_imgs.append(flat_img)
	i += 1
print ("Done.")

# Create raw dark images
dark_imgs = []
print ("Creating raw darks... ", end="")
i = 0
for hot in hot_data:
	dark_img = reduce.AstroImage(test_data_dir+"darks/Dark-"+str(i)+"-"+test_fits_suffix, new_file=True)
	dark_img.exp_time = 1.0
	dark_img.filter = "Clear"
	dark_img.img_type = reduce.ImageType.DARK
	dark_img.writeValues()
	dark_img.fits_data = dark_data_base + hot
	dark_img.saveToDisk()
	dark_img.unloadData()
	dark_imgs.append(dark_img)
	i += 1
print ("Done.")

light_imgs = []
print ("Creating raw lights... ", end="")
i = 0
for hot in hot_data:
	light_img = reduce.AstroImage(test_data_dir+"lights/Light"+str(i)+"-"+test_fits_suffix, new_file=True)
	light_img.exp_time = 1.0
	light_img.filter = "Clear"
	light_img.img_type = reduce.ImageType.RAW
	light_img.writeValues()
	light_img.fits_data = (light_data_base * (flat_data_base / np.median(flat_data_base))) + dark_data_base
	light_img.saveToDisk()
	light_img.unloadData()
	light_imgs.append(light_img)
	i += 1
print ("Done.")

print ("Reducing...")
reduce.reduce(
	darks_dir=test_data_dir + "darks",
	mdarks_dir=test_data_dir + "mdarks",
	flats_dir=test_data_dir + "flats",
	mflats_dir=test_data_dir + "mflats",
	raw_dir=test_data_dir + "lights",
	output_dir=test_data_dir + "output",
	stack=False, level=0)

print ("Verifying... ", end="")
out_imgs = reduce.find_astro_imgs(test_data_dir + "output")
verified = True
for img in out_imgs:
	img.loadData()
	if not np.allclose(img.fits_data, light_data_base):
		verified = False
	img.unloadData()
if not verified:
	print ("FAILED")
	exit (1)

print ("PASSED")
exit (0)
