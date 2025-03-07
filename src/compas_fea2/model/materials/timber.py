from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from compas_fea2.base import FEAData


class Timber(FEAData):
    """Base class for Timber material"""

    def __init__(self, *, density, **kwargs):
        """
        Parameters
        ----------
        density : float
            Density of the timber material [kg/m^3].
        name : str, optional
            Name of the material.
        """
        super(Timber, self).__init__(density=density, **kwargs)
