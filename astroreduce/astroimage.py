import datetime
from enum import Enum
import os

from astropy.io import fits

CURRENT_DATE_TIME = datetime.datetime.now().strftime("%y-%m-%dT%H:%M:%S")

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
                          "mflat": ImageType.MFLAT }.get(type, ImageType.RAW)

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
        if self.fits_header == None:
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
        self.loadHeader() # Load fits header
        self.loadValues() # Read in important header values
        self.loadImageType() # Get the type of image (dark, flat, light, etc.)
        if self.img_type == ImageType.RAW:
            # If the image is a light image, get the name of the object
            self.object_name = os.path.basename(path).split("-")[0]
