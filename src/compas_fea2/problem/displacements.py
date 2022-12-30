from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from compas_fea2.base import FEAData

from compas_fea2 import UNITS
from compas_fea2.units._utils import convert_to_magnitude
from compas_fea2.units._utils import assign_default_units
from compas_fea2.units._utils import to_default_units

class GeneralDisplacement(FEAData):
    """GeneralDisplacement object.

    Note
    ----
    Displacements are registered to a :class:`compas_fea2.problem.Step`.

    Parameters
    ----------
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    x : float, optional
        x component of force, by default 0.
    y : float, optional
        y component of force, by default 0.
    z : float, optional
        z component of force, by default 0.
    xx : float, optional
        xx component of moment, by default 0.
    yy : float, optional
        yy component of moment, by default 0.
    zz : float, optional
        zz component of moment, by default 0.
    axes : str, optional
        BC applied via 'local' or 'global' axes, by default 'global'.

    Attributes
    ----------
    name : str
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    x : float, optional
        x component of force, by default 0.
    y : float, optional
        y component of force, by default 0.
    z : float, optional
        z component of force, by default 0.
    xx : float, optional
        xx component of moment, by default 0.
    yy : float, optional
        yy component of moment, by default 0.
    zz : float, optional
        zz component of moment, by default 0.
    axes : str, optional
        BC applied via 'local' or 'global' axes, by default 'global'.
    """

    def __init__(self, x=0, y=0, z=0, xx=0, yy=0, zz=0, axes='global', name=None, **kwargs):
        super(GeneralDisplacement, self).__init__(name=name, **kwargs)
        self.x = assign_default_units(x, 'mm')
        self.y = assign_default_units(y, 'mm')
        self.z = assign_default_units(z, 'mm')
        self.xx = assign_default_units(xx, 'rad')
        self.yy = assign_default_units(yy, 'rad')
        self.zz = assign_default_units(zz, 'rad')
        self._axes = axes

    @property
    def axes(self):
        return self._axes

    @axes.setter
    def axes(self, value):
        self._axes = value

    @property
    def components(self):
        return {c: getattr(self, c) for c in ['x', 'y', 'z', 'xx', 'yy', 'zz']}
