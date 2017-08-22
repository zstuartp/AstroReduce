import argparse
import datetime
import getopt
import logging
import os
import readline
import sys

from . import env
from . import flatfield as ff
from . import log
from . import version

PROGRAM_NAME = "AstroReduce"

CURRENT_DATE_TIME = datetime.datetime.now().strftime("%y-%m-%dT%H:%M:%S")

def print_version():
    """ Print the version of the script """
    print (PROGRAM_NAME + ": v" + version.__version__)


def usage():
    """ Print the usage of the script """
    print_version()
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
    print ("    -L run_level    0 -> Process darks, flats, and lights")
    print ("                    1 -> Process flats and lights using only existing master darks")
    print ("                    2 -> Process lights using only existing darks and flats")


def main():
    light_dir = "./lights"
    dark_dir = "./darks"
    mdark_dir = "./mdarks"
    flat_dir = "./flats"
    mflat_dir = "./mflats"
    output_dir = "./output"
    level = 0

    OPTIONS = "vhiVl:d:D:f:F:o:L:k"
    LONG_OPTIONS = [
        "version",
        "help",
        "verbose",
        "light-dir",
        "dark-dir",
        "mdark-dir",
        "flat-dir",
        "mflat-dir",
        "output-dir"
    ]

    try:
        opts, args = getopt.getopt(sys.argv[1:], OPTIONS, LONG_OPTIONS)
    except getopt.GetoptError as e:
        print (str(e))
        usage()
        sys.exit(1)
    for o, a in opts:
        if o in ("-V", "--verbose"):
            # Enable verbose logging output
            env.set("VERBOSE",  "True")
        elif o in ("-i"):
            flags.is_interactive = True
        elif o in ("-L"):
            level = int(a)
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
            print_version()
            sys.exit(0)
        elif o in ("-h", "--help"):
            usage()
            sys.exit(1)
        elif o in ("-k"):
            env.set("OK_MODE", "True")

    env.import_sys_env()
    
    ff.reduce(
        darks_dir=dark_dir,
        mdarks_dir=mdark_dir,
        flats_dir=flat_dir,
        mflats_dir=mflat_dir,
        raw_dir=light_dir,
        output_dir=output_dir,
        stack=False,
        level=level
    )

    return

if __name__ == "__main__" and not sys.flags.interactive:
    main()
