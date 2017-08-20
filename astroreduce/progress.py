import sys

from . import env

def update(progress):
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
    if env.get("OK_MODE"): # Reverse the loading bar for fun (-k option)
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
