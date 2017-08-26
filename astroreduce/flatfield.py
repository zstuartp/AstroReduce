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

import argparse
import datetime
from enum import Enum
import getopt
import glob
import logging
from typing import Any, Dict, List
import numpy as np
import os
import sys
from time import sleep

from . import arimage
from . import env
from . import jobs
from . import log

logger = log.get_logger()

CURRENT_DATE_TIME = datetime.datetime.now().strftime("%y-%m-%dT%H:%M:%S")


class ImageKind(Enum):
    UNKNOWN = -1
    RAW = 0
    DARK = 1
    FLAT = 2
    LIGHT = 3


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
    output_img = arimage.ARImage(output_path, new_file=True)
    imgs[0].loadHeader()
    imgs[0].fits_header.tofile(output_path, overwrite=True)
    imgs[0].unloadHeader()
    output_img = med_combine(imgs, output_img)
    return output_img


def sort_darks(darks_unsorted: List[arimage.ARImage]):
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


def sort_flats(flats_unsorted: List[arimage.ARImage]):
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


def sort_lights(lights_unsorted: List[arimage.ARImage]):
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


def sort_arimgs_as_kind(arimgs: List[arimage.ARImage], img_kind: ImageKind) -> Dict[Any, List]:
    sorted_arimgs = None

    if img_kind == ImageKind.DARK:
        sorted_arimgs = sort_darks(arimgs)
    elif img_kind == ImageKind.FLAT:
        sorted_arimgs = sort_flats(arimgs)
    elif img_kind == ImageKind.LIGHT:
        sorted_arimgs = sort_lights(arimgs)
    else:
        logger.warning("Unable to sort image kind: " + str(img_kind))

    return sorted_arimgs


def dark_correct_arimg(img: arimage.ARImage, dark: arimage.ARImage) -> arimage.ARImage:
    """ Dark corrects image """
    logger.info("Dark correcting image: " + img.getFullPath())
    logger.info("            with dark: " + dark.getFullPath())

    # Load image data into memory if it is not already loaded
    img.loadData()
    dark.loadData()

    img.fits_data = img.fits_data - dark.fits_data

    return img


def dark_correct_arimgs(imgs: List[arimage.ARImage], darks_sorted: Dict[int, arimage.ARImage]) -> List[arimage.ARImage]:
    for img in imgs:
        et = int(round(img.exp_time))
        dark = darks_sorted.get(et)
        if dark == None:
            # No dark found with required exposure time, ignore this flat
            logger.warning("Dropping flat without matching dark (exp_time=" + str(et) + "): " + img.getFullPath())
            imgs.remove(img)
            continue
        dark_correct_arimg(img, dark[0])

    # Clean up loaded darks
    for darks in darks_sorted.values():
        arimage.unload_data_arimgs(darks)

    return imgs


def flat_correct_arimg(img: arimage.ARImage, flat: arimage.ARImage) -> arimage.ARImage:
    """ Flat corrects the image """
    logger.info("Flat correcting image: " + img.getFullPath())
    logger.info("            with flat: " + flat.getFullPath())

    img.loadData()
    flat.loadData()

    img.fits_data = img.fits_data / flat.fits_data

    return img


def flat_correct_arimgs(imgs: List[arimage.ARImage], flats_sorted: Dict[str, arimage.ARImage]) -> List[arimage.ARImage]:
    for img in imgs:
        fl = img.filter
        mflat = mflats_dic.get(fl)
        if mflat == None: # No flat was found with the correct filter
            logger.warning("Skipping image with no matching master flat(filter=" + fl + "): " + imgs[0].getFullPath())
            imgs.remove(img)
            continue
        flat.loadData(keep_loaded=True)
        flat_correct_arimg(img, flat[0])

    # Clean up loaded flats
    for flats in flats_sorted.value():
        arimage.unload_data_arimgs(flats, force_unload=True)

    return imgs


def create_master_dark(darks, output_dir):
    """ Median combine darks into one file in output_dir """
    if not bool(darks):
        logger.error("No darks available to create master dark")
        return

    # Create the file name
    path = os.path.join(output_dir, "MDark-Exp" + str(darks[0].exp_time).replace(".", "s") + ".fts")

    # Median combine
    mdark = med_combine_new_file(darks, path)
    arimage.unload_data_arimgs(darks)

    # Save
    mdark.copyValues(darks[0])
    mdark.saveToDisk()
    mdark.unloadData()
    logger.info("Created master dark with exp_time=" + str(darks[0].exp_time) + ": " + path)


def create_master_darks(darks_sorted: Dict, output_dir: str):
    """ Create the master dark images from sorted darks """
    if not bool(darks_sorted):
        logger.warning("No darks are available to median combine")
        return

    for darks in darks_sorted.values():
        # Create a job thread for each group of darks
        job = jobs.Job(target=create_master_dark, args=(darks, output_dir))
        jobs.push_job(job)

    # Start processing the job queue and wait
    jobs.start_jobs()
    jobs.wait_done()


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
        dark_correct_arimg(flat, mdark[0])
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
    arimage.unload_data_arimgs(flats)

    # Normalize
    data = mflat.fits_data
    mflat.fits_data = data / np.median(data)

    # Copy important header values
    mflat.copyValues(flats[0])
    mflat.img_type = ImageKind.FLAT

    # Save new master flat to disk and free up memory
    mflat.saveToDisk()
    mflat.unloadData()
    logger.info("Created master flat for filter=" + flats[0].filter + ": " + path)


def create_master_flats(flats_dic, mdarks_dic, output_dir):
    """ Create the master flat images """
    if not bool(flats_dic):
        logger.warning("No flats are available to median combine")
        return

    for flats in flats_dic.values():
        # Create a job thread for each group of flats
        job = jobs.Job(target=create_master_flat, args=(flats, mdarks_dic, output_dir))
        jobs.push_job(job)

    # Start processing the job queue and wait
    jobs.start_jobs()
    jobs.wait_done()


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
    for img in imgs: # Copy the raw light to a new file, then (dark correct and flat correct
        file_path = os.path.join(output_dir, on \
            + "-" + img.date_obs.replace("-", "").replace("T", "at").replace(":", "") \
            + "-Temp" + str(int(round(img.ccd_temp))).replace("-", "m") \
            + "-Bin" + str(img.binning) \
            + "-Exp" + str(et).replace(".", "s") \
            + "-" + fl \
            + ".fts")
        cimg = arimage.ARImage(file_path, new_file=True)
        cimg.fits_header = img.fits_header
        cimg.loadValues()
        if mdark is not None:
            dark_correct_arimg(img, mdark)
        else:
            logger.warning("No dark image found for light: " + cimg.getFullPath())
        if mflat is not None:
            flat_correct_arimg(img, mflat)
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

    for key, imgs in imgs_dic.items():
        # Create a job thread for each group of lights
        job = jobs.Job(target=create_corrected_img, args=(key, imgs, mdarks_dic, mflats_dic, output_dir))
        jobs.push_job(job)

    # Start processing the job queue and wait
    jobs.start_jobs()
    jobs.wait_done()


def reduce(darks_dir="./darks", mdarks_dir="./mdarks", flats_dir="./flats", \
           mflats_dir="./mflats", raw_dir="./lights", output_dir="./output", \
           stack=False, level=0):

    if level < 1:
        # Create master darks
        print ("Creating master darks in " + mdarks_dir + " from " + darks_dir)
        darks = arimage.find_arimgs_in_dir(darks_dir)
        darks_sorted = sort_arimgs_as_kind(darks, ImageKind.DARK)
        create_master_darks(darks_sorted, mdarks_dir)

    # Find master darks and sort
    mdarks = arimage.find_arimgs_in_dir(mdarks_dir)
    mdarks_sorted = sort_arimgs_as_kind(mdarks, ImageKind.DARK)

    if level < 2:
        # Create master flats
        print ("Creating master flats in " + mflats_dir + " from " + flats_dir)
        flats = arimage.find_arimgs_in_dir(flats_dir)
        flats_sorted = sort_arimgs_as_kind(flats, ImageKind.FLAT)
        create_master_flats(flats_sorted, mdarks_sorted, mflats_dir)

    mflats = arimage.find_arimgs_in_dir(mflats_dir)
    mflats_sorted = sort_arimgs_as_kind(mflats, ImageKind.FLAT)

    # Find and correct the light images
    raw_lights = arimage.find_arimgs_in_dir(raw_dir)
    raw_sorted = sort_arimgs_as_kind(raw_lights, ImageKind.LIGHT)
    print ("Correcting light images from " + raw_dir)
    print ("             with darks from " + mdarks_dir)
    print ("              and flats from " + mflats_dir)
    create_corrected_images(raw_sorted, mdarks_sorted, mflats_sorted, output_dir, stack)
