from pint import Quantity
from typing import Iterable


def convert_to_magnitude(value):
    from compas_fea2 import UNITS
    from compas_fea2 import DEFAULT_UNITS
    if isinstance(value, Iterable):
        converted_value=[]
        for v in value:
            if not isinstance(v, Quantity):
                converted_value.append((value*UNITS).to_base_units().magnitude)
            else:
                converted_value.append(value.to_base_units().magnitude)
        return converted_value
    else:
        if isinstance(value, Quantity):
            return (value*UNITS).to_base_units().magnitude
        else:
            return value.to_base_units().magnitude


def assign_default_units(value, unit_type):
    """Convert a value of a give dimensionality to the default units. You can see
    the list of default units for the chosen system of units by running:

        from compas_fea2 import DEFAULT_UNITS
        print(DEFAULT_UNITS)

    Parameters
    ----------
    value : float
        The value to convert.
    unit_type : str
        Dimensionality. It can be one of the following ['length', 'mass', 'time', 'temperature']

    Returns
    -------
    :class:`pint.Quantity`
        The value in the default units for the units system.
    """
    from compas_fea2 import UNITS
    from compas_fea2 import DEFAULT_UNITS
    if isinstance(value, Iterable):
        converted_value=[]
        for v in value:
            if not isinstance(v, Quantity):
                if v:
                    converted_value.append(v*UNITS[DEFAULT_UNITS[unit_type.lower()]])
                else:
                    converted_value.append(v)
            else:
                converted_value.append(v)
        return converted_value
    else:
        if not isinstance(value, Quantity):
            if value:
                return value*UNITS[DEFAULT_UNITS[unit_type.lower()]]
            else:
                return value
        else:
            return value

def to_default_units(value, units_type):
    from compas_fea2 import DEFAULT_UNITS
    if isinstance(value, Quantity):
        return value.to(DEFAULT_UNITS[units_type])
    else:
        return value
