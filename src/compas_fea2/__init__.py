"""
********************************************************************************
compas_fea2
********************************************************************************

.. currentmodule:: compas_fea2


API Packages
============

.. toctree::
    :maxdepth: 1

    compas_fea2.model
    compas_fea2.problem
    compas_fea2.results
    compas_fea2.job
    compas_fea2.postprocess
    compas_fea2.utilities
    compas_fea2.units

Dev Packages
============

.. toctree::
    :maxdepth: 1

    compas_fea2.UI

"""
import os
from collections import defaultdict

import os
from dotenv import load_dotenv
from .units import get_registry, DEFAULT_UNITS_DICT

__author__ = ["Francesco Ranaudo"]
__copyright__ = "Block Research Group"
__license__ = "MIT License"
__email__ = "ranaudo@arch.ethz.ch"
__version__ = "0.1.0"


HERE = os.path.dirname(__file__)

HOME = os.path.abspath(os.path.join(HERE, "../../"))
DATA = os.path.abspath(os.path.join(HOME, "data"))
UMAT = os.path.abspath(os.path.join(DATA, "umat"))
DOCS = os.path.abspath(os.path.join(HOME, "docs"))
TEMP = os.path.abspath(os.path.join(HOME, "temp"))

def init_fea2():
    """Create a default environment file.
    """
    import shutil
    shutil.copyfile(os.path.abspath(os.path.join(DATA, "__templates", ".env")),
                    os.path.abspath(os.path.join(HERE, ".env")))
    out = load_dotenv(os.path.join(HERE, ".env"))
    if not out:
        raise FileNotFoundError("the environment file could not be loaded")

def set_default_units(system):
    """Set the default units from the given units system. You can see
    the list of default units by running:

        from compas_fea2 import DEFAULT_UNITS
        print(DEFAULT_UNITS)

    Parameters
    ----------
    system : str
        Units system. It can be one of the following: 'SI', 'SI_mm', 'imperial', 'US'
    """
    global DEFAULT_UNITS
    DEFAULT_UNITS = DEFAULT_UNITS_DICT['metric' if system in ['SI', 'SI_mm'] else 'imperial']

def set_units(system):
    """Set the units system.

    Parameters
    ----------
    system : str
        Units system. It can be one of the following: 'SI', 'SI_mm', 'imperial', 'US'

    Returns
    -------
    :class:`pint.Quantity`
        The value in the default units for the units system.
    """
    global UNITS
    UNITS = get_registry(system=system)
    set_default_units(system)
    return UNITS

def change_units(system):
    """Change the units system.

    Parameters
    ----------
    system : str
        New units system. It can be one of the following: 'SI', 'SI_mm', 'imperial', 'US'

    Returns
    -------
    :class:`pint.Quantity`
        The value in the default units for the units system.

    Raises
    ------
    ValueError
        If the units system is not among those supported.
    """
    if system not in ['SI', 'SI_mm', 'imperial', 'US']:
        raise ValueError('The units system must be one of the following [SI, SI_mm, imperial, US]')
    UNITS.default_system = system
    global DEFAULT_UNITS
    DEFAULT_UNITS = DEFAULT_UNITS_DICT[system]
    return UNITS

def set_precision(precision):
    """Define the approximation tolerance.

    Parameters
    ----------
    precision : str
        approximation tolerance
    """
    global PRECISION
    PRECISION = precision

# pluggable function
def _register_backend():
    """Create the class registry for the plugin.

    Raises
    ------
    NotImplementedError
        This function is implemented within the backend plugin implementation.
    """
    raise NotImplementedError

def set_backend(plugin):
    """Set the backend plugin to be used.

    Parameters
    ----------
    plugin : str
        Name of the plugin library. You can find some backend plugins on the
        official ``compas_fea2`` website.

    Raises
    ------
    ImportError
        If the plugin library is not found.
    """
    import importlib
    global BACKEND
    BACKEND = plugin
    try:
        importlib.import_module(plugin)._register_backend()
    except:
        raise ImportError('backend plugin not found. Make sure that you have installed it before.')

def _get_backend_implementation(cls):
    """Get the name of the corresponding backend class.

    Parameters
    ----------
    cls : str
        Base class name to find.

    Returns
    -------
    str
        The name of the corresponding backend class.
    """
    return BACKENDS[BACKEND].get(cls)

# load the environmental variables
if not load_dotenv(os.path.join(HERE, ".env")):
    init_fea2()

VERBOSE = os.getenv('VERBOSE').lower() == 'true'
POINT_OVERLAP = os.getenv('POINT_OVERLAP').lower() == 'true'
GLOBAL_TOLERANCE = os.getenv('GLOBAL_TOLERANCE')
PRECISION = os.getenv('PRECISION')
BACKEND = None
BACKENDS = defaultdict(dict)

# Set the units
set_units(system=os.getenv('UNITS_SYSTEM'))
set_default_units(system=os.getenv('UNITS_SYSTEM'))





__all__ = ["HOME", "DATA", "DOCS", "TEMP"]

