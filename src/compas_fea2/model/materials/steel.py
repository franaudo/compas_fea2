from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import compas_fea2
from .material import _Material, ElasticIsotropic
from compas_fea2.units._utils import convert_to_magnitude
from compas_fea2.units._utils import assign_default_units
from compas_fea2.units._utils import to_default_units

class Steel(ElasticIsotropic):
    """Bi-linear steel with given yield stress.
    """
    __doc__ += _Material.__doc__
    __doc__ += """
    Additional Parameters
    ---------------------
    E : float
        Young's modulus E.
    v : float
        Poisson's ratio v.
    fy : float
        Yield stress.
    fu : float
        Ultimate stress.
    eu : float
        Ultimate strain.

    Attributes
    ----------
    E : float
        Young's modulus E.
    v : float
        Poisson's ratio v.
    G : float
        Shear modulus G.
    fy : float
        Yield stress.
    fu : float
        Ultimate stress.
    eu : float
        Ultimate strain.
    ep : float
        Plastic strain.

    """

    def __init__(self, *, E, v, density, fy, fu=None, eu=None, name=None, **kwargs):
        super(Steel, self).__init__(E=E, v=v, density=density, name=name, **kwargs)

        fu = fu or fy

        ep = eu - fy / E
        f = [fy, fu]
        e = [0, ep]
        fc = [-i for i in f]
        ec = [-i for i in e]

        self.fy = fy
        self.fu = fu
        self.eu = eu
        self.ep = ep
        self.E = E
        self.v = v
        self.tension = {'f': f, 'e': e}
        self.compression = {'f': fc, 'e': ec}

    def __str__(self):
        return """
Steel Material
--------------
name    : {}
density : {:~.0f}

E  : {:~.0f}
G  : {:~.0f}
fy : {:~.0f}
fu : {:~.0f}
v  : {:.2f}
eu : {:.2f}
ep : {:.2f}
""".format(self.name,
           (self.density * units['kg/m**2']),
           (self.E * units.pascal).to('GPa'),
           (self.G * units.pascal).to('GPa'),
           (self.fy * units.pascal).to('MPa'),
           (self.fu * units.pascal).to('MPa'),
           (self.v * units.dimensionless),
           (self.eu * units.dimensionless),
           (self.ep * units.dimensionless))


    #TODO check values and make unit independent
    @classmethod
    def S355(cls, units=None):
        """Steel S355.

        Parameters
        ----------
        units : :class:`pint.UinitRegistry, optional
            The units of the Model. If not provided, the units are set to 'SI-mm' by
            default.

        Returns
        -------
        :class:`compas_fea2.model.material.Steel`
            The precompiled steel material.
        """
        units = units or compas_fea2.get_registry(system='SI_mm')
        return cls(fy=(355*units['MPa']).to_base_units(),
                   fu=None,
                   eu=20,
                   E=(210*units['GPa']).to_base_units(),
                   v=0.3,
                   density=(7850*units['kg/m**2']).to_base_units(),
                   name=None)
