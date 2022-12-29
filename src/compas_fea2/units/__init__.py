"""

Note
----
The following is assumed:

    - force unit = 1 mass unit * 1 acceleration unit
    - acceleration unit = 1 length unit / (1 time unit)^2
    - density unit = 1 mass unit / (1 length unit)^3

"""
import os
from pint import UnitRegistry

HERE = os.path.dirname(__file__)

# U.define('@alias pascal = Pa')

DEFAULT_UNITS_DICT = {
    'metric': {
        'length': 'mm',
        'mass': 'kg',
        'temperature': 'K',
        'time': 's',
        'density': 'kg/m**3',
        'force': 'kN',
        'pressure': 'kPa',
        'stress': 'MPa',
        'energy': 'joule',
        'expansion': 'K**-1',
    },
    'imperial': {
        'length': 'foot',
        'mass': 'slug',
        'temperature': 'K',
        'time': 's',
        'force': 'kip',
        'pressure': 'ksi',
        'stress': 'ksi',
        'energy': 'lbf*ft',
    }
}

def get_registry(system='SI'):
    """Set the UnitRegisty.

    Note
    ----
    The available systems of units are ['SI', 'SI_mm', 'imperial', 'US']


    Parameters
    ----------
    system : str, optional
        The chosen system of units, by default 'SI'.

    Returns
    -------
    :clas:`pint.UnitRegistry`
        the UnitRegistry to be used.
    """
    if system not in ['SI', 'SI_mm', 'imperial', 'US']:
        raise ValueError('The units system must be one of the following [SI, SI_mm, imperial, US]')
    ureg = UnitRegistry(os.path.join(HERE, 'fea2_en.txt'), system=system)
    ureg.default_format = "~P"
    return ureg

