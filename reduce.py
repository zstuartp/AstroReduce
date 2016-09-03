################################################################################
##########            CSUSB Astronomy Data Reduction Script           ##########
################################################################################

################################################################################
#
# - To use this script directly without needing to specify specific
#   derectories, place it in a directory with all of the following folders:
#
# //===========================================\\
# || Directory  | Contents                     ||
# ||------------+------------------------------||
# || ./lights/  | Raw light images             ||
# || ./darks/   | Dark images                  ||
# || ./flats/   | Flat images                  ||
# || ./mdarks/  | Master dark images output    ||
# || ./mflats/  | Master flat images output    ||
# || ./output/  | Corrected light image output ||
# \\===========================================//
#
#   Then run the program using python3
#
# - For information about running the script with a different directory
#   structure, run the program with either the "-h" or "--help" options
#
# - Contact "Zackary Parsons <parsonsz@coyote.csusb.edu>"
#   with any questions, comments, and/or improvements
# 
################################################################################

import argparse
from astropy.io import fits
import datetime
from enum import Enum
import getopt
import glob
import logging
import numpy
import os
import sys

PROGRAM_NAME = "Astronomy Data Reduction Script"
VERSION = 2
PATCH = 1
VERSION_STR = str(VERSION) + "." + str(PATCH)

CURRENT_DATE_TIME = datetime.datetime.now().strftime("%y-%m-%dT%H:%M:%S")

#
# Flags
#
VERBOSE = False

#
# Setup logging
#
logger = logging.getLogger(PROGRAM_NAME + " Log")
fh = logging.FileHandler(CURRENT_DATE_TIME + "-reduce.log")
ch = logging.StreamHandler()
log_format_file = logging.Formatter("%(asctime)s::%(levelname)s -- %(message)s")
log_format_console = logging.Formatter("%(levelname)s -- %(message)s")
fh.setFormatter(log_format_file)
ch.setFormatter(log_format_console)
logger.setLevel(logging.DEBUG)
ch.setLevel(logging.WARNING)
logger.addHandler(ch)
logger.addHandler(fh)
logger.info("================================================")
logger.info(PROGRAM_NAME + " Log")
logger.info(CURRENT_DATE_TIME)
logger.info("================================================")

#
# ImageType enum
#
class ImageType(Enum):
	UNKNOWN = -1
	RAW = 0
	CORRECTED = 1
	FLAT = 2
	MFLAT = 3
	DARK = 4
	MDARK = 5

#
# AstroImage
# This class provides an easy way to interact with astronomy fits images
#
class AstroImage:
	# Fits info
	fits_header = None
	fits_data = None

	# File info
	file_dir = "."
	file_name = "null"

	# Image parameters
	binning = 0
	ccd_temp = 0
	date_obs = CURRENT_DATE_TIME
	exp_time = 0
	filter = "NA"
	img_type = ImageType.UNKNOWN

	# Astronomy info
	object_name = "earth"

	def getFullPath(self):
		""" Get the full path of the fits image """
		return os.path.join(self.file_dir, self.file_name)

	def loadImageType(self):
		""" Get the type enum of an image based on the file name """
		type = os.path.basename(self.getFullPath()).split("-")[0].lower()
		self.img_type = { "dark":  ImageType.DARK,
						  "mdark": ImageType.MDARK,
						  "flat":  ImageType.FLAT,
						  "mflat": ImageType.MFLAT
						  }.get(type, ImageType.RAW)

	def loadData(self):
		""" Load image data """
		if self.fits_data is None:
			# Only load the data if it has not already been loaded
			# If you want to reload the data, use .unloadData() first
			self.fits_data = fits.getdata(self.getFullPath())
		return self.fits_data

	def unloadData(self):
		""" Unload the image data from memory """
		self.fits_data = None

	def loadHeader(self):
		""" Load the fits header """
		self.fits_header = fits.getheader(self.getFullPath())
		return self.fits_header

	def loadValues(self):
		""" Load the important values from the fits header """
		if fits.header == None:
			logger.warning("Attempted to load values from image with no header: " + self.getFullPath())
		self.binning  = self.fits_header.get("XBINNING")
		self.ccd_temp = self.fits_header.get("CCD-TEMP")
		self.date_obs = self.fits_header.get("DATE-OBS")
		self.exp_time = self.fits_header.get("EXPTIME")
		self.filter   = self.fits_header.get("FILTER")

	def copyValues(self, astro_img):
		""" Copy the important header values from another AstroImage """
		self.binning = astro_img.binning
		self.ccd_temp = astro_img.ccd_temp
		self.date_obs = astro_img.date_obs
		self.exp_time = astro_img.exp_time
		self.filter = astro_img.filter

	def writeValues(self):
		""" Write the important header values back to the disk """
		self.fits_header["XBINNING"] = self.binning
		self.fits_header["CCD-TEMP"] = self.ccd_temp
		self.fits_header["DATE-OBS"] = self.date_obs
		self.fits_header["EXPTIME"]  = self.exp_time
		self.fits_header["FILTER"]   = self.filter

	def saveToDisk(self):
		""" Save the fits header and image data to the disk """
		self.writeValues()
		fits.writeto(self.getFullPath(), data=self.fits_data, header=self.fits_header, clobber=True)

	def setFilePath(self, path):
		""" Set the full path of the file """
		self.file_dir = os.path.dirname(path)
		if self.file_dir == "":
			self.file_dir = "."
		self.file_name = os.path.basename(path)

	def __init__(self, path=None, new_file=False):
		if path == None:
			logger.warning("Cannot load AstroImage from unspecified path")
			return
		self.setFilePath(path)
		if new_file and path != None: # Create a new fits file
			hdu = fits.PrimaryHDU()
			hdulist = fits.HDUList([hdu])
			self.fits_header = hdulist[0].header
			self.fits_data = hdulist[0].data
			self.saveToDisk()
		self.loadHeader() # Load fits header
		self.loadValues() # Read in important header values
		self.loadImageType() # Get the type of image (dark, flat, light, etc.)
		if self.img_type == ImageType.RAW:
			# If the image is a light image, get the name of the object
			self.object_name = os.path.basename(path).split("-")[0]


def update_progress(progress):
	""" A simple progress bar, accepts a float between 0 and 1 """
	barLength = 54 # Modify this to change the length of the progress bar
	status = ""
	if isinstance(progress, int):
		progress = float(progress)
	if not isinstance(progress, float):
		progress = 0
		status = "E\r\n"
	if progress < 0:
		progress = 0
		status = "Halt...\r\n"
	if progress >= 1:
		progress = 1
		status = "Done...\r\n"
	block = int(round(barLength*progress))
	text = "\rProgress: [{0}] {1}% {2}".format( "#"*block + "-"*(barLength-block), round(progress*100), status)
	sys.stdout.write(text)
	sys.stdout.flush()


def find_astro_imgs(path):
	""" Find all fits files in the specified path """
	astro_imgs = []
	img_paths = glob.glob(os.path.join(path, "**" ,"*.fits"), recursive=True)
	img_paths.extend(glob.glob(os.path.join(path, "**" ,"*.fts"), recursive=True))
	for img_path in img_paths:
		aimg = AstroImage(img_path)
		logger.info("Found astronomy fits image: " + aimg.getFullPath())
		astro_imgs.append(aimg)
	return astro_imgs


def unload_astro_imgs(astro_imgs):
	""" Free memory from a list of AstroImages """
	for img in astro_imgs:
		img.unloadData()


def find_astro_imgs_with_type(path, img_type):
	""" Load the paths of all fits images with the given type into an array """
	imgs = find_astro_imgs(path)
	imgs[:] = [img for img in imgs if (img.img_type == img_type)]
	return imgs


def med_combine(imgs, output_img):
	""" Median combine fits images """
	data_in = []
	for img in imgs:
		data_in.append(img.loadData())
	data_out = numpy.median(data_in, axis=0)
	output_img.fits_data = data_out
	logger.info("Median combined " + str(len(data_in)) + " images to: " + output_img.getFullPath())
	return output_img


def med_combine_new_file(imgs, output_path):
	""" Median combine fits images into a new file """
	output_img = AstroImage(output_path, new_file=True)
	imgs[0].fits_header.tofile(output_path, clobber=True)
	output_img = med_combine(imgs, output_img)
	return output_img


def sort_darks(darks_unsorted):
	""" Sort dark images into a dictionary with "exp_time" as the key """
	if bool(darks_unsorted) == False:
		return
	darks = { }
	logger.info("Sorting dark images by exposure time:")
	for dark in darks_unsorted:
		et = int(round(dark.exp_time))
		if et not in darks:
			# Found a dark with a new exposure time
			# Create a new array in the dictionary
			logger.info("Found a dark with exp_time=" + str(et))
			darks[et] = []
		darks[et].append(dark)
	return darks


def sort_flats(flats_unsorted):
	""" Sort flat images into a dictionary with "filter" as the key """
	if bool(flats_unsorted) == False:
		return None
	flats = { }
	logger.info("Sorting flat images by filter")
	for flat in flats_unsorted:
		fl = flat.filter
		if fl not in flats:
			# Found a flat with a new filter
			# Create a new array in the dictionary
			logger.info("Found a flat with filter=" + fl)
			flats[fl] = []
		flats[fl].append(flat)
	return flats


def sort_lights(lights_unsorted):
	""" Sort light images by object, exposure time, and filter """
	if bool(lights_unsorted) == False:
		return None
	lights = { }
	logger.info("Sorting light images by object, exposure time, and filter")
	for light in lights_unsorted:
		on = light.object_name
		et = light.exp_time
		fl = light.filter
		key = (on, et, fl) # Combine the three elements into a single tuple to be used as the key
		if key not in lights:
			logger.info("Found a light of " + on + " with exp_time=" + str(et) + " in filter=" + fl)
			lights[key] = []
		lights[key].append(light)
	return lights


def dark_correct(img, dark):
	""" Dark corrects image (Duh! Read the function name next time!) """
	if img is None:
		logger.error("Attempted to dark correct a non-existing light image")
		return
	if dark is None:
		logger.error("Attempted to dark correct with a non-existing dark image")
		return
	logger.info("Dark correcting image: " + img.getFullPath())
	logger.info("	         with dark: " + dark.getFullPath())
	img.loadData()
	dark.loadData()
	img.fits_data = img.fits_data - dark.fits_data
	return img


def flat_correct(img, flat):
	""" Flat corrects the image """
	if img is None:
		logger.error("Attempted to flat correct a non-existing light image")
		return
	if flat is None:
		logger.error("Attempted to flat correct with a non-existing flat image")
		return
	logger.info("Flat correcting image: " + img.getFullPath())
	logger.info("            with flat: " + flat.getFullPath())
	img.loadData()
	flat.loadData()
	img.fits_data = img.fits_data / flat.fits_data
	return img


def create_master_darks(darks_dic, output_dir):
	""" Create the master dark images """
	prog = 0
	end = len(darks_dic)
	for exp_time, darks in darks_dic.items():
		# Create the file name
		path = os.path.join(output_dir, "MDark-Exp" + str(exp_time).replace(".", "s") + ".fts")

		# Median combine
		mdark = med_combine_new_file(darks, path)
		unload_astro_imgs(darks)

		# Copy important header values
		mdark.exp_time = exp_time
		mdark.img_type = ImageType.MDARK

		# Save new master dark to disk and free up memory
		mdark.saveToDisk()
		mdark.unloadData()
		logger.info("Create master dark with exp_time=" + str(exp_time) + ": " + path)
		if not VERBOSE:
			update_progress(prog / end)
			prog += 1
	if not VERBOSE:
		update_progress(1)


def dark_correct_flats(flats, mdarks_dic):
	""" Dark correct the flat images """
	if not bool(flats):
		logger.warning("No flats are available to dark correct")
		return
	if not bool(mdarks_dic):
		logger.warning("No master darks available to dark correct flats for filter=" + flats[0].filter)
		return
	for flat in flats:
		et = int(round(flat.exp_time))
		mdark = mdarks_dic.get(et)
		if mdark == None:
			# No dark found with required exposure time, ignore this flat
			logger.warning("Dropping flat without matching dark (exp_time=" + str(et) + "): " + flat.getFullPath())
			flat.unloadData()
			flats.remove(flat)
			continue
		dark_correct(flat, mdark[0])
	return flats


def create_master_flats(flats_dic, mdarks_dic, output_dir):
	""" Create the master flat images """
	if not bool(flats_dic):
		logger.warning("No flats are available to median combine")
		return
	prog = 0
	end = len(flats_dic)
	for filter, flats in flats_dic.items():
		# Create the file name
		path = os.path.join(output_dir, "MFlat-" + filter + ".fts")

		# Dark correct the flats
		dark_correct_flats(flats, mdarks_dic)
		# Median combine to a new fits image
		mflat = med_combine_new_file(flats, path)
		# Free up memory
		unload_astro_imgs(flats)

		# Normalize
		data = mflat.fits_data
		mflat.fits_data = data / numpy.median(data)

		# Copy important header values
		mflat.copyValues(flats[0])
		mflat.img_type = ImageType.MFLAT

		# Save new master flat to disk and free up memory
		mflat.saveToDisk()
		mflat.unloadData()
		logger.info("Created master flat for filter=" + filter + ": " + path)
		if not VERBOSE:
			update_progress(prog / end)
			prog +=1
	if not VERBOSE:
		update_progress(1)


def create_corrected_images(imgs_dic, mdarks_dic, mflats_dic, output_dir, stack=False):
	""" Dark and flat corrects light images, stacking is not implimented yet """
	# TODO: Place all images into a dictionary with key=object_name and return the dictionary for stacking
	if not bool(imgs_dic):
		logger.error("No images available to correct")
		return
	no_run = 0
	if not bool(mdarks_dic):
		logger.warning("No master darks available")
		no_run += 1
	if not bool(mflats_dic):
		logger.warning("No master flats available")
		no_run += 1
	if no_run > 1:
		logger.warning("No corrections possible, skipping all light images")
		return

	
	total_count = 0

	prog = 0
	end = len(imgs_dic)

	for key, imgs in imgs_dic.items():
		on = key[0] # Object name
		et = key[1] # Exposure time
		fl = key[2] # Filter
		mdark = None
		mflat = None

		# Find the corresp. master dark
		if bool(mdarks_dic):
			mdark = mdarks_dic.get(int(round(et)))
			if mdark == None: # No dark was found with the correct exposure time
				logger.warning("Skipping image with no matching master dark (exp_time=" + str(et) + "): " + img.getFullPath())
				continue
			else:
				mdark = mdark[0] # Get the first master dark in list

		# Find the corresp. master flat
		if bool(mflats_dic):
			mflat = mflats_dic.get(fl)
			if mflat == None: # No flat was found with the correct filter
				logger.warning("Skipping image with no matching master flat(filter=" + fl + "): " + img.getFullPath())
				continue
			else:
				mflat = mflat[0]

		i = 0
		for img in imgs: # Copy the raw light to a new file, then dark correct and flat correct
			file_path = os.path.join(output_dir, on \
				+ "-" + img.date_obs.replace("-", "").replace("T", "at").replace(":", "") \
				+ "-Temp" + str(int(round(img.ccd_temp))).replace("-", "m") \
				+ "-Bin" + str(img.binning) \
				+ "-Exp" + str(et).replace(".", "s") \
				+ "-" + fl \
				+ ".fts")
			cimg = AstroImage(file_path, new_file=True)
			cimg.fits_header = img.fits_header
			cimg.loadValues()
			if mdark is not None:
				dark_correct(img, mdark)
			else:
				logger.warning("No dark image found for light: " + cimg.getFullPath())
			if mflat is not None:
				flat_correct(img, mflat)
			else:
				logger.warning("No flat image found for light: " + cimg.getFullPath())
			cimg.fits_data = img.fits_data
			cimg.saveToDisk()
			cimg.unloadData()
			img.unloadData()
			logger.info("Corrected image with exp_time=" + str(et) + " and filter=" + fl + ": " + img.getFullPath())
			i += 1
		total_count += i
		if not VERBOSE:
			update_progress(prog / end)
			prog += 1
	if not VERBOSE:
		update_progress(1)
	if total_count > 0:
		logger.info("Corrected " + str(total_count) + " image" + ("s" if total_count > 1 else "") + ". Enjoy :-)")


def reduce(darks_dir="./darks", mdarks_dir="./mdarks", flats_dir="./flats", \
		   mflats_dir="./mflats", raw_dir="./lights", output_dir="./output", \
		   stack=False):
	# Create master darks
	print ("Creating master darks in " + mdarks_dir + " from " + darks_dir)
	# Find all dark images in darks_dir,
	# then sort them by exposure time,
	# Then median combine to master darks in mdarks_dir
	create_master_darks( \
		sort_darks(find_astro_imgs_with_type(darks_dir, ImageType.DARK)), \
		mdarks_dir)
	# Find and sort master darks by exposure time
	mdarks_dic = sort_darks(find_astro_imgs_with_type(mdarks_dir, ImageType.MDARK))

	# Create master flats
	print ("Creating master flats in " + mflats_dir + " from " + flats_dir)
	create_master_flats( \
		sort_flats(find_astro_imgs_with_type(flats_dir, ImageType.FLAT)), \
		mdarks_dic, mflats_dir)
	# Find and sort master flats
	mflats_dic = sort_flats(find_astro_imgs_with_type(mflats_dir, ImageType.MFLAT))

	# Find and correct the light images
	raw_dic = sort_lights(find_astro_imgs_with_type(raw_dir, ImageType.RAW))
	print ("Correcting light images from " + raw_dir)
	create_corrected_images(raw_dic, mdarks_dic, mflats_dic, output_dir, stack)


def version():
	""" Print the version of the script """
	print (PROGRAM_NAME + ": v" + VERSION_STR)


def usage():
	""" Print the usage of the script """
	version()
	print ("Usage: python3 " + os.path.basename(sys.argv[0]) + " [options]")
	print ("Options:")
	print ("    -h, --help      Displays this help message")
	print ("    -v, --version   Displays the version of the script")
	print ("    -V, --verbose   Prints log messages to the terminal screen")
	print ("    -l light_dir    Uncorrected images directory")
	print ("    -o output_dir   Correct images output directory")
	print ("    -d dark_dir     Raw dark images directory")
	print ("    -D mdark_dir    Master dark images output directory")
	print ("    -f flat_dir     Raw flat images directory")
	print ("    -F mflat_dir    Master flat images output directory")


def main():
	light_dir = "./lights"
	dark_dir = "./darks"
	mdark_dir = "./mdarks"
	flat_dir = "./flats"
	mflat_dir = "./mflats"
	output_dir = "./output"

	OPTIONS = "vhVl:d:D:f:F:o:L:"
	LONG_OPTIONS = ["version", "help", "verbose"]

	try:
		opts, args = getopt.getopt(sys.argv[1:], OPTIONS, LONG_OPTIONS)
	except getopt.GetoptError as e:
		print (str(e))
		usage()
		sys.exit(1)
	for o, a in opts:
		if o in ("-V", "--verbose"):
			# Enable verbose message output
			global VERBOSE
			VERBOSE = True
			ch.setLevel(logging.INFO)
		elif o in ("-l", "--light_dir"):
			light_dir = a
		elif o in ("-d", "--dark-dir"):
			dark_dir = a
		elif o in ("-D", "--mdark-dir"):
			mdark_dir = a
		elif o in ("-f", "--flat-dir"):
			flat_dir = a
		elif o in ("-F", "--mflat-dir"):
			mflat_dir = a
		elif o in ("-o", "--output-dir"):
			output_dir = a
		elif o in ("-v", "--version"):
			version()
			sys.exit(0)
		elif o in ("-h", "--help"):
			usage()
			sys.exit(1)

	# Reduce
	reduce(dark_dir, mdark_dir, flat_dir, mflat_dir, light_dir, output_dir, stack=False)
	return


if __name__ == "__main__" and not sys.flags.interactive:
	main()
