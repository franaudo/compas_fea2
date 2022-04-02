from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from compas_fea2.model import MassElement
from compas_fea2.model import BeamElement
from compas_fea2.model import TrussElement
from compas_fea2.model import ShellElement
from compas_fea2.model import MembraneElement
from compas_fea2.model import SolidElement
from compas_fea2.model import TetrahedronElement
from compas_fea2.model import PentahedronElement
from compas_fea2.model import HexahedronElement


def _generate_jobdata(element):
    """Generates the string information for the input file.

    Parameters
    ----------
    None

    Returns
    -------
    input file data line (str).

    """
    # note: the string `*Element, type=___` is generated in the part section to group elements with the same type
    return '{0}, {1}\n'.format(element.key+1, ','.join(str(node.key+1) for node in element.nodes))


# ==============================================================================
# 0D elements
# ==============================================================================
class AbaqusMassElement(MassElement):
    """A 0D element for concentrated point mass.

    Parameters
    ----------
    key : int
        Number of the element.
    elset : str
        Name of the automatically generated element set where the masses is applied.
    mass : float
        Concentrated mass (mass of each point of the set).

    """

    def __init__(self, *, node, section, frame=None, part=None, name=None, **kwargs):
        super(AbaqusMassElement, self).__init__(nodes=[node],
                                                section=section, frame=frame, part=part, name=name, **kwargs)

    def _generate_jobdata(self):
        """Generates the string information for the input file.

        Parameters
        ----------
        None

        Returns
        -------
        input file data line (str).
        """
        return """
*ELEMENT, TYPE=MASS, ELSET={0}
{0}, {1}
*MASS, ELSET={0}
{1}
""".format(self.elset, self.node)


# ==============================================================================
# 1D elements
# ==============================================================================

class AbaqusBeamElement(BeamElement):

    def __init__(self, nodes, section, frame=[0.0, 0.0, -1.0], part=None, name=None, **kwargs):
        super(AbaqusBeamElement, self).__init__(nodes=nodes, section=section, frame=frame, part=part, name=name, **kwargs)
        self._elset = None
        self._eltype = 'B31'
        self._orientation = frame

    def _generate_jobdata(self):
        return _generate_jobdata(self)


class AbaqusTrussElement(TrussElement):
    """A 1D element that resists axial loads.
    """
    __doc__ += TrussElement.__doc__

    def __init__(self, nodes, section, part=None, name=None, **kwargs):
        super(AbaqusTrussElement, self).__init__(nodes=nodes, section=section, part=part, name=name, **kwargs)
        self._elset = None
        self._eltype = 'T3D2'
        self._orientation = None

    def _generate_jobdata(self):
        return _generate_jobdata(self)

# ==============================================================================
# 2D elements
# ==============================================================================


class AbaqusShellElement(ShellElement):
    """"""
    __doc__ += ShellElement.__doc__
    """
    Additional Parameters
    ---------------------
    reduced : bool, optional
        Reduce the integration points, by default ``False``.


    """
    __doc__ += ShellElement.__doc__

    def __init__(self, nodes, section, part=None, reduced=False, name=None, **kwargs):
        super(AbaqusShellElement, self).__init__(nodes=nodes, section=section,  part=part, name=name, **kwargs)
        self._reduced = reduced
        self._elset = None
        eltypes = {3: 'S3', 4: 'S4'}
        if not len(self.nodes) in eltypes:
            raise NotImplementedError('Shells must currently have either 3 or 4 nodes')
        self._eltype = eltypes[len(self.nodes)]
        if self._reduced:
            self._eltype += 'R'

    def _generate_jobdata(self):
        return _generate_jobdata(self)


class AbaqusMembraneElement(MembraneElement):

    def __init__(self, nodes, section, part=None, reduced=False, name=None, **kwargs):
        super(AbaqusMembraneElement, self).__init__(nodes=nodes, section=section, part=part, name=name, **kwargs)
        self._elset = None
        self._reduced = reduced
        eltypes = {3: 'M3D3', 4: 'M3D4'}
        if not len(self.nodes) in eltypes:
            raise NotImplementedError('Membrane elements must currently have either 3 or 4 nodes')
        self._eltype = eltypes[len(self.nodes)]
        if self._reduced and len(self.nodes) > 3:
            self._eltype += 'R'

    def _generate_jobdata(self):
        return _generate_jobdata(self)

# ==============================================================================
# 3D elements
# ==============================================================================


class AbaqusSolidElement(SolidElement):

    def __init__(self, nodes, section, part=None, reduced=False, name=None, **kwargs):
        super(AbaqusSolidElement, self).__init__(nodes=nodes, section=section,  part=part, name=name, **kwargs)
        eltypes = {4: 'C3D4', 6: 'C3D6', 8: 'C3D8', 10: 'C3D10'}
        self._reduced = reduced
        if not len(self.nodes) in eltypes:
            raise NotImplementedError('Solid element with {} nodes is not currently supported'.fromat(len(self.nodes)))
        self._eltype = eltypes[len(self.nodes)]
        if self._reduced:
            self._eltype += 'R'

    def _generate_jobdata(self):
        return _generate_jobdata(self)


class AbaqusTetrahedonElement(TetrahedronElement):
    def __init__(self, *, nodes, section, part=None, reduced=False, name=None, **kwargs):
        super(AbaqusTetrahedonElement, self).__init__(nodes=nodes,
                                                      section=section, frame=None, part=part, name=name, **kwargs)
        raise NotImplementedError()


class AbaqusPentahedronElement(PentahedronElement):
    def __init__(self, *, nodes, section, part=None, reduced=False, name=None, **kwargs):
        super(AbaqusPentahedronElement, self).__init__(nodes=nodes,
                                                       section=section, frame=None, part=part, name=name, **kwargs)
        raise NotImplementedError()


class AbaqusHexahedronElement(HexahedronElement):
    def __init__(self, *, nodes, section, part=None, reduced=False, name=None, **kwargs):
        super(AbaqusHexahedronElement, self).__init__(nodes=nodes,
                                                      section=section, frame=None, part=part, name=name, **kwargs)
        raise NotImplementedError()
