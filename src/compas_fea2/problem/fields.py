from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from compas_fea2.base import FEAData

from compas_fea2 import UNITS
from compas_fea2.units._utils import convert_to_magnitude
from compas_fea2.units._utils import assign_default_units
from compas_fea2.units._utils import to_default_units

class _PrescribedField(FEAData):
    """Base class for all predefined initial conditions.

    Note
    ----
    Fields are registered to a :class:`compas_fea2.problem.Step`.
    """

    def __init__(self, name=None, **kwargs):
        super(_PrescribedField, self).__init__(name=name, **kwargs)


class PrescribedTemperatureField(_PrescribedField):
    """Temperature field
    """

    def __init__(self, temperature, name=None, **kwargs):
        super(PrescribedTemperatureField, self).__init__(name, **kwargs)
        self._t = assign_default_units(temperature, 'K')

    @property
    def temperature(self):
        return self._t

    @temperature.setter
    def temperature(self, value):
        self._t = value
