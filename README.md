# About AstroReduce
This is a flat-field correction script which makes use of the Astropy and Numpy
libraries. The script automatically median combines raw dark fits images with
matching exposure times (rounded to the nearest second).  Next, it dark-corrects
each raw flat image by exposure time and median combines the flat images by
filter. Finally, the corrected dark and flat images are used to correct the
light images.

# Use
The current Python package requirements are:
```
astropy==2.0
numpy==1.13.1
```
You should be able to use these versions or newer with AstroReduce, but to
be safe you should use a virtual environment which can be setup by running
the "setup.sh" shell script.

To use this script directly without needing to specify specific directories or 
files, place "reduce.py" in a directory with ALL of the following folders:

| Directory  | Contents                     |
|------------|------------------------------|
| ./lights/  | Raw light images             |
| ./darks/   | Dark images                  |
| ./flats/   | Flat images                  |
| ./mdarks/  | Master dark images output    |
| ./mflats/  | Master flat images output    |
| ./output/  | Corrected light image output |

Then run the program using:
```
python3 reduce.py
```

For information about running the script with a different directory
structure, run the program with either the "-h" or "--help" options.

While it is technically possible to use this script with interactive python,
that isn't the intended use. AstroReduce is currently intended to run in
the directory structure described above, or as part of some other process which
invokes this script and specifies other directories.

# Contributing
Feel free to contact me via email or on GitHub with any questions,
corrections, or improvements.

