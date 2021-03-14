from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Author(s): Francesco Ranaudo (github.com/franaudo)

from compas_fea2.backends._base.model import ModelBase

__all__ = [
    'Model',
]


class Model(ModelBase):
    """Initialises the Model object. This is in many aspects equivalent to an
    `Assembly` in Abaqus.

    Parameters
    ----------
    name : str
        Name of the Model.

    Attributes
    ----------
    name : str
        Name of the Model.
    parts : list
        A list with the Part objects referenced in the Model.
    instances : dict
        A dictionary with the Instance objects belonging to the Model.
    parts : dict
        A dictionary with the Part objects referenced in the Model.
    surfaces : list
        A list with the Surface objects belonging to the Model.
    constraints : list
        A list with the Constraint objects belonging to the Model.
    materials : dict
        A dictionary of all the materials defined in the Model.
    sections : dict
        A dictionary of all the sections defined in the Model.
    sets : dict
        A dictionary of all the sets defined in the Model.
    """

    def __init__(self, name):
        super(Model, self).__init__(name)
        self._backend = 'abaqus'

    def _generate_data(self):
        line = '*Assembly, name={}\n**\n'.format(self.name)
        section_data = [line]
        for instance in self.instances.values():
            section_data.append(instance._generate_data())
            for iset in instance.sets:
                section_data.append(iset._generate_data())
        # for surface in self.surfaces:
        #     section_data.append(surface.data)
        # for constraint in self.constraints:
        #     section_data.append(constraint.data)
        line = '*End Assembly\n**'
        section_data.append(line)
        return ''.join(section_data)


# =============================================================================
#                               Debugging
# =============================================================================
if __name__ == "__main__":
    pass
