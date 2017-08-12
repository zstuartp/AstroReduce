import os

import pkg_resources

_resource_package = __name__
__version__ = pkg_resources.resource_string(_resource_package, "VERSION").strip().decode()
