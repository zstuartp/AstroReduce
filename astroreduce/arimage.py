import datetime
from enum import Enum
import glob
import os
from typing import List, NewType

from astropy.io import fits

from . import log

CURRENT_DATE_TIME = datetime.datetime.now().strftime("%y-%m-%dT%H:%M:%S")

logger = log.get_logger()

#
# ARImage
# This class provides an easy way to interact with astronomy fits images
#
class ARImage:
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

    # Astronomy info
    object_name = "earth"

    def getFullPath(self):
        """ Get the full path of the fits image """
        return os.path.join(self.file_dir, self.file_name)

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
        if self.fits_header is None:
            self.fits_header = fits.getheader(self.getFullPath())
        return self.fits_header

    def unloadHeader(self):
        """ Unload the fits header """
        self.fits_header = None

    def loadValues(self):
        """ Load the important values from the fits header """
        unload_after = False
        if self.fits_header is None:
            unload_after = True
            self.loadHeader()
        self.binning  = self.fits_header.get("XBINNING")
        self.ccd_temp = self.fits_header.get("CCD-TEMP")
        self.date_obs = self.fits_header.get("DATE-OBS")
        self.exp_time = self.fits_header.get("EXPTIME")
        self.filter   = self.fits_header.get("FILTER")
        if unload_after:
            self.unloadHeader()

    def copyValues(self, astro_img):
        """ Copy the important header values from another AstroImage """
        self.binning = astro_img.binning
        self.ccd_temp = astro_img.ccd_temp
        self.date_obs = astro_img.date_obs
        self.exp_time = astro_img.exp_time
        self.filter = astro_img.filter

    def writeValues(self):
        """ Write the important header values back to the disk """
        unload_after = False
        if self.fits_header is None:
            unload_after = True
            self.loadHeader()
        self.fits_header["XBINNING"] = self.binning
        self.fits_header["CCD-TEMP"] = self.ccd_temp
        self.fits_header["DATE-OBS"] = self.date_obs
        self.fits_header["EXPTIME"]  = self.exp_time
        self.fits_header["FILTER"]   = self.filter
        if unload_after:
            self.unloadHeader()

    def saveToDisk(self):
        """ Save the fits header and image data to the disk """
        self.writeValues()
        fits.writeto(self.getFullPath(), data=self.fits_data, header=self.fits_header, overwrite=True)

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
        self.loadValues() # Read in important header values

def find_arimgs_in_dir(directory: str, recursive: bool=True) -> List[ARImage]:
    """ Find and create ARImage objects for fits images in a "directory" """
    arimgs = []

    if recursive:
        dir_prefix = os.path.join(directory, "**")
    else:
        dir_prefix = directory

    try:
        # Get a list of all files ending in ".fits" and ".fts" in "directory"
        img_paths = glob.glob(os.path.join(dir_prefix, "*.fits"), recursive=recursive)
        img_paths.extend(glob.glob(os.path.join(dir_prefix, "*.fts"), recursive=recursive))
    except OSError as err:
        logger.error("Failed to open directory: " + directory)
        return None

    for img_path in img_paths:
        # Load each found fits image as an ARImage and append it to the arimgs list
        img = ARImage(img_path)
        logger.info("Found fits image: " + img.getFullPath())
        arimgs.append(img)

    return arimgs

def find_arimgs_from_list_file(list_path: str) -> List[ARImage]:
    """ Find and create ARImage objects for fits images listed in a text file """
    print("TODO: Impliment me: find_arimgs_from_list_file")

def unload_data_arimgs(arimgs: ARImage):
    """ Unload image data from memory for a list of ARImages """
    for img in arimgs:
        img.unloadData()
