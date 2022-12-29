from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from compas_fea2.base import FEAData
from compas_fea2.units._utils import convert_to_magnitude
from compas_fea2.units._utils import assign_default_units
from compas_fea2.units._utils import to_default_units

class _Material(FEAData):
    """
    Note
    ----
    Materials are registered to a :class:`compas_fea2.model.Model`. The same
    material can be assigned to multiple sections and in different elements and
    parts.

    Parameters
    ----------
    denisty : float
        Density of the material.
    expansion : float, optional
        Thermal expansion coefficient, by default None.
    name : str, optional
        Uniqe identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.

    Other Parameters
    ----------------
    **kwargs : dict
        Backend dependent keyword arguments.
        See the individual backends for more information.

    Attributes
    ----------
    name : str, optional
        Uniqe identifier.
    density : float
        Density of the material.
    expansion : float
        Thermal expansion coefficient.
    key : int
        The key index of the material. It is automatically assigned to material
        once it is added to the model.
    model : :class:`compas_fea2.model.Model`
        The Model where the material is assigned.
    """

    def __init__(self, *, density, expansion=None, name=None, **kwargs):
        super(_Material, self).__init__(name=name, **kwargs)
        self._key = None
        self.density = assign_default_units(density, 'density')
        self.expansion = assign_default_units(expansion, 'expansion')

    @property
    def key(self):
        return self._key

    @property
    def model(self):
        return self._registration

    def __str__(self):
        return """
{}
{}
name        : {}
density     : {}
expansion   : {}
""".format(self.__class__.__name__,
           len(self.__class__.__name__) * '-',
           self.name,
           to_default_units(self.density, 'density'),
           to_default_units(self.expansion, 'expansion')
           )

    def __html__(self):
        return """<html>
<head></head>
<body><p>Hello World!</p></body>
</html>"""



# ==============================================================================
# linear elastic
# ==============================================================================
class ElasticOrthotropic(_Material):
    """Elastic, orthotropic and homogeneous material.
    """
    __doc__ += _Material.__doc__
    __doc__ += """
    Additional Parameters
    ---------------------
    Ex : float
        Young's modulus Ex in x direction.
    Ey : float
        Young's modulus Ey in y direction.
    Ez : float
        Young's modulus Ez in z direction.
    vxy : float
        Poisson's ratio vxy in x-y directions.
    vyz : float
        Poisson's ratio vyz in y-z directions.
    vzx : float
        Poisson's ratio vzx in z-x directions.
    Gxy : float
        Shear modulus Gxy in x-y directions.
    Gyz : float
        Shear modulus Gyz in y-z directions.
    Gzx : float
        Shear modulus Gzx in z-x directions.

    Additional Attributes
    ---------------------
    Ex : float
        Young's modulus Ex in x direction.
    Ey : float
        Young's modulus Ey in y direction.
    Ez : float
        Young's modulus Ez in z direction.
    vxy : float
        Poisson's ratio vxy in x-y directions.
    vyz : float
        Poisson's ratio vyz in y-z directions.
    vzx : float
        Poisson's ratio vzx in z-x directions.
    Gxy : float
        Shear modulus Gxy in x-y directions.
    Gyz : float
        Shear modulus Gyz in y-z directions.
    Gzx : float
        Shear modulus Gzx in z-x directions.
    """

    def __init__(self, *, Ex, Ey, Ez, vxy, vyz, vzx, Gxy, Gyz, Gzx, density, expansion=None, name=None, **kwargs):
        super(ElasticOrthotropic, self).__init__(density=density, expansion=expansion, name=name, **kwargs)
        self.Ex = assign_default_units(Ex, 'stress')
        self.Ey = assign_default_units(Ey, 'stress')
        self.Ez = assign_default_units(Ez, 'stress')
        self.vxy = vxy
        self.vyz = vyz
        self.vzx = vzx
        self.Gxy = assign_default_units(Gxy, 'stress')
        self.Gyz = assign_default_units(Gyz, 'stress')
        self.Gzx = assign_default_units(Gzx, 'stress')

    def __str__(self):
        return """
{}
{}
name        : {}
density     : {}
expansion   : {}

Ex  : {}
Ey  : {}
Ez  : {}
vxy : {}
vyz : {}
vzx : {}
Gxy : {}
Gyz : {}
Gzx : {}
""".format(self.__class__.__name__, len(self.__class__.__name__) * '-',
           self.name,
           to_default_units(self.density, 'density'),
           to_default_units(self.expansion, 'expansion'),
           to_default_units(self.Ex, 'stress'),
           to_default_units(self.Ey, 'stress'),
           to_default_units(self.Ez, 'stress'),
           self.vxy,
           self.vyz,
           self.vzx,
           to_default_units(self.Gxy, 'stress'),
           to_default_units(self.Gyz, 'stress'),
           to_default_units(self.Gzx, 'stress')
           )


class ElasticIsotropic(_Material):
    """Elastic, isotropic and homogeneous material.
    """
    __doc__ += _Material.__doc__
    __doc__ += """
    Additional Parameters
    ---------------------
    E : float
        Young's modulus E.
    v : float
        Poisson's ratio v.

    Additional Attributes
    ---------------------
    E : float
        Young's modulus E.
    v : float
        Poisson's ratio v.
    G : float
        Shear modulus (automatically computed from E and v)
    """

    def __init__(self, *, E, v, density, expansion=None, name=None, **kwargs):
        super(ElasticIsotropic, self).__init__(density=density, expansion=expansion, name=name, **kwargs)
        self.E = assign_default_units(E, 'stress')
        self.v = v

    def __str__(self):
        return """
ElasticIsotropic Material
-------------------------
name        : {}
density     : {}
expansion   : {}

E : {}
v : {}
G : {}
""".format(self._name,
           to_default_units(self.density, 'density'),
           to_default_units(self.expansion, 'expansion'),
           to_default_units(self.E, 'stress'),
           self.v,
           to_default_units(self.G, 'stress')
)

    @property
    def G(self):
        return 0.5 * self.E / (1 + self.v)

class Stiff(_Material):
    """Elastic, very stiff and massless material.
    """
    def __init__(self, *, density, expansion=None, name=None, **kwargs):
        raise NotImplementedError()


# ==============================================================================
# non-linear general
# ==============================================================================
class ElasticPlastic(ElasticIsotropic):
    """Elastic and plastic, isotropic and homogeneous material.
    """
    __doc__ += _Material.__doc__
    __doc__ += """
    Additional Parameters
    ---------------------
    E : float
        Young's modulus.
    v : float
        Poisson's ratio.
    strain_stress : list[tuple[float, float]]
        Strain-stress data, including elastic and plastic behaviour,
        in the form of strain/stress value pairs.

    Additional Attributes
    ---------------------
    E : float
        Young's modulus.
    v : float
        Poisson's ratio.
    G : float
        Shear modulus (automatically computed from E and v)
    strain_stress : list[tuple[float, float]]
        Strain-stress data, including elastic and plastic behaviour,
        in the form of strain/stress value pairs.
    """

    def __init__(self, *, E, v, density, strain_stress, expansion=None, name=None, **kwargs):
        super(ElasticPlastic, self).__init__(E=E, v=v, density=density, expansion=expansion, name=name, **kwargs)
        self.strain_stress = strain_stress

    def __str__(self):
        return """
ElasticPlastic Material
-----------------------
name        : {}
density     : {}
expansion   : {}

E  : {}
v  : {}
G  : {}

strain_stress : {}
""".format(self.name,
           to_default_units(self.density, 'density'),
           to_default_units(self.expansion, 'expansion'),
           to_default_units(self.E, 'stress'),
           self.v,
           to_default_units(self.G, 'stress'),
           self.strain_stress)


# ==============================================================================
# User-defined Materials
# ==============================================================================
class UserMaterial(FEAData):
    """ User Defined Material. Tho implement this type of material, a
    separate subroutine is required

    """

    def __init__(self, name=None, **kwargs):
        super(UserMaterial, self).__init__(self, name=name, **kwargs)
        raise NotImplementedError('This class is not available for the selected backend plugin')
