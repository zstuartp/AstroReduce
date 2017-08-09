#!/usr/bin/env python3

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

################################################################################
#
# For information on using this program, view the README.
#
# - Contact "Zackary Parsons <parsonsz@coyote.csusb.edu>"
#   with any questions, comments, and/or improvements
#
################################################################################

import argparse
from astropy.io import fits
import datetime
import getopt
import glob
import logging
from threading import Thread
import numpy as np
import os
import sys
from time import sleep

from . import astroimage as aimg
from . import flags

PROGRAM_NAME = "AstroReduce" # TODO: Use a global

CURRENT_DATE_TIME = datetime.datetime.now().strftime("%y-%m-%dT%H:%M:%S")

#
# Setup logging
#
logger = logging.getLogger(PROGRAM_NAME + " Log")
fh = logging.FileHandler("reduce-" + CURRENT_DATE_TIME.replace("-", "").replace("T", "at").replace(":", "") + ".log")
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



def update_progress(progress):
    """ A simple progress bar, accepts a float between 0 and 1 """
    if flags.is_verbose:
        return
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
    if flags.is_okay: # Reverse the loading bar for fun (-k option)
        if progress <= 0:
            progress = 0
            status = "Done..."
        elif progress >= 1:
            progress = 1
            status = "       \r\n"
        else:
            status = "        "
        progress = 1 - progress
    block = int(round(barLength*progress))
    text = "\rProgress: [{0}] {1}% {2}".format( "#"*block + "-"*(barLength-block), round(progress*100), status)
    sys.stdout.write(text)
    sys.stdout.flush()


def update_progress_on_threads(threads):
    """ Update the progress bar based on the number of threads completed """
    i = 0
    prog = 0
    end = len(threads)
    handled = {}
    update_progress(0)

    logger.debug(str(end) + " threads created")
    while True: # Check thread status and update the progress bar
        sleep(0.001)
        if not threads[i].is_alive() and not bool(handled.get(i)):
            logger.debug("Thread[" + str(i) + "] finished")
            handled[i] = True
            prog += 1
            update_progress(prog / end)
            if prog == end:
                break
        i += 1
        if i >= end:
            i = 0


def find_astro_imgs(path):
    """ Find all fits files in the specified path """
    astro_imgs = []
    img_paths = glob.glob(os.path.join(path, "**" ,"*.fits"), recursive=True)
    img_paths.extend(glob.glob(os.path.join(path, "**" ,"*.fts"), recursive=True))
    for img_path in img_paths:
        img = aimg.AstroImage(img_path)
        logger.info("Found astronomy fits image: " + img.getFullPath())
        astro_imgs.append(img)
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
    data_out = np.median(data_in, axis=0)
    output_img.fits_data = data_out
    logger.info("Median combined " + str(len(data_in)) + " images to: " + output_img.getFullPath())
    return output_img


def med_combine_new_file(imgs, output_path):
    """ Median combine fits images into a new file """
    output_img = aimg.AstroImage(output_path, new_file=True)
    imgs[0].fits_header.tofile(output_path, overwrite=True)
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
    logger.info("            with dark: " + dark.getFullPath())
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


def create_master_dark(darks, output_dir):
    """ Median combine darks into one file in output_dir """
    if not bool(darks):
        logger.error("No darks available to create master dark")
        return

    # Create the file name
    path = os.path.join(output_dir, "MDark-Exp" + str(darks[0].exp_time).replace(".", "s") + ".fts")

    # Median combine
    mdark = med_combine_new_file(darks, path)
    unload_astro_imgs(darks)

    # Save
    mdark.copyValues(darks[0])
    mdark.saveToDisk()
    mdark.unloadData()
    logger.info("Created master dark with exp_time=" + str(darks[0].exp_time) + ": " + path)


def create_master_darks(darks_dic, output_dir):
    """ Create the master dark images """
    if not bool(darks_dic):
        logger.warning("No darks are available to median combine")
        return

    threads = []
    for darks in darks_dic.values():
        # Spawn a process for each group of darks
        t = Thread(target=create_master_dark, args=(darks, output_dir))
        t.start()
        threads.append(t)

    update_progress_on_threads(threads)


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


def create_master_flat(flats, mdarks_dic, output_dir):
    """ Dark correct and median combine flats into one file in output_dir """
    if not bool(flats):
        logger.error("No flats available to create master flat")
        return

    # Create the file name
    path = os.path.join(output_dir, "MFlat-" + flats[0].filter + ".fts")

    # Dark correct the flats
    dark_correct_flats(flats, mdarks_dic)
    # Median combine to a new fits image
    mflat = med_combine_new_file(flats, path)
    # Free up memory
    unload_astro_imgs(flats)

    # Normalize
    data = mflat.fits_data
    mflat.fits_data = data / np.median(data)

    # Copy important header values
    mflat.copyValues(flats[0])
    mflat.img_type = aimg.ImageType.MFLAT

    # Save new master flat to disk and free up memory
    mflat.saveToDisk()
    mflat.unloadData()
    logger.info("Created master flat for filter=" + flats[0].filter + ": " + path)


def create_master_flats(flats_dic, mdarks_dic, output_dir):
    """ Create the master flat images """
    if not bool(flats_dic):
        logger.warning("No flats are available to median combine")
        return

    threads = []
    for flats in flats_dic.values():
        # Spawn a process for each group of flats
        t = Thread(target=create_master_flat, args=(flats, mdarks_dic, output_dir))
        t.start()
        threads.append(t)

    update_progress_on_threads(threads)


def create_corrected_img(key, imgs, mdarks_dic, mflats_dic, output_dir, stack=False):
    on = key[0] # Object name
    et = key[1] # Exposure time
    fl = key[2] # Filter
    mdark = None
    mflat = None

    # Find the corresp. master dark
    if bool(mdarks_dic):
        mdark = mdarks_dic.get(int(round(et)))
        if mdark == None: # No dark was found with the correct exposure time
            logger.warning("Skipping image with no matching master dark (exp_time=" + str(et) + "): " + imgs[0].getFullPath())
            return
        else:
            mdark = mdark[0] # Get the first master dark in list

    # Find the corresp. master flat
    if bool(mflats_dic):
        mflat = mflats_dic.get(fl)
        if mflat == None: # No flat was found with the correct filter
            logger.warning("Skipping image with no matching master flat(filter=" + fl + "): " + imgs[0].getFullPath())
            return
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
        cimg = aimg.AstroImage(file_path, new_file=True)
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


def create_corrected_images(imgs_dic, mdarks_dic, mflats_dic, output_dir, stack=False):
    """ Dark and flat corrects light images, stacking is not implemented yet """
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

    threads = []
    for key, imgs in imgs_dic.items():
        # Spawn a process for each group of lights
        t = Thread(target=create_corrected_img, args=(key, imgs, mdarks_dic, mflats_dic, output_dir))
        t.start()
        threads.append(t)

    update_progress_on_threads(threads)


def reduce(darks_dir="./darks", mdarks_dir="./mdarks", flats_dir="./flats", \
           mflats_dir="./mflats", raw_dir="./lights", output_dir="./output", \
           stack=False, level=0):
    mdarks_dic = None
    mflats_dic = None
    raw_dic = None

    if level < 1:
        # Create master darks
        print ("Creating master darks in " + mdarks_dir + " from " + darks_dir)
        # Find all dark images in darks_dir,
        # then sort them by exposure time,
        # Then median combine to master darks in mdarks_dir
        create_master_darks( \
            sort_darks(find_astro_imgs_with_type(darks_dir, aimg.ImageType.DARK)), \
            mdarks_dir)

    mdarks_dic = sort_darks(find_astro_imgs_with_type(mdarks_dir, aimg.ImageType.MDARK))

    if level < 2:
        # Create master flats
        print ("Creating master flats in " + mflats_dir + " from " + flats_dir)
        create_master_flats( \
            sort_flats(find_astro_imgs_with_type(flats_dir, aimg.ImageType.FLAT)), \
            mdarks_dic, mflats_dir)

    mflats_dic = sort_flats(find_astro_imgs_with_type(mflats_dir, aimg.ImageType.MFLAT))

    # Find and correct the light images
    raw_dic = sort_lights(find_astro_imgs_with_type(raw_dir, aimg.ImageType.RAW))
    print ("Correcting light images from " + raw_dir)
    print ("             with darks from " + mdarks_dir)
    print ("              and flats from " + mflats_dir)
    create_corrected_images(raw_dic, mdarks_dic, mflats_dic, output_dir, stack)
