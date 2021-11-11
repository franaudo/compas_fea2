from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os.path
from compas_fea2.backends._base.job.input_file import InputFileBase
from compas_fea2.backends.abaqus.problem.steps import ModalStep
# Author(s): Francesco Ranaudo (github.com/franaudo)

__all__ = [
    'InputFile',
    'ParFile'
]


class InputFile(InputFileBase):
    """Input file object for standard analysis.

    Parameters
    ----------
    problem : obj
        Problem object.

    Attributes
    ----------
    name : str
        Input file name.
    job_name : str
        Name of the Abaqus job. This is the same as the input file name.

    """

    def __init__(self, problem):
        super(InputFile, self).__init__(problem)
        self._input_file_type = "Input File"
        self.name = '{}.inp'.format(problem.name)
        self._jobdata = self._generate_jobdata(problem)

    @property
    def jobdata(self):
        """This property is the representation of the object in a software-specific inout file.

        Returns
        -------
        str

        Examples
        --------
        >>>
        """
        return self._jobdata

    # ==============================================================================
    # Constructor methods
    # ==============================================================================

    def _generate_jobdata(self, problem):
        """Generate the content of the input fileself from the Problem object.

        Parameters
        ----------
        problem : obj
            Problem object.

        Resturn
        -------
        str
            content of the input file
        """
        return """** {}
*Heading
** Job name: {}
** Generated by: compas_fea2
*PHYSICAL CONSTANTS, ABSOLUTE ZERO=-273.15, STEFAN BOLTZMANN=5.67e-8
**
** PARTS
**
{}**
** ASSEMBLY
**
{}
**
** MATERIALS
**
{}**
** INTERACTION PROPERTIES
**
{}**
** INTERACTIONS
**
{}**
** BOUNDARY
**
{}**
** STEPS
{}
""".format(self.name, self.job_name, self._generate_part_section(problem), self._generate_assembly_section(problem),
           self._generate_material_section(problem), self._generate_int_props_section(problem),
           self._generate_interactions_section(problem), self._generate_bcs_section(problem),
           self._generate_steps_section(problem))

    def _generate_part_section(self, problem):
        """Generate the content relatitive the each Part for the input file.

        Parameters
        ----------
        problem : obj
            compas_fea2 Problem object.

        Returns
        -------
        str
            text section for the input file.
        """
        section_data = []
        for part in problem.model.parts.values():
            data = part._generate_jobdata()
            section_data.append(data)
        return ''.join(section_data)

    def _generate_assembly_section(self, problem):
        """Generate the content relatitive the assembly for the input file.

        Note
        ----
        in compas_fea2 the Model is for many aspects equivalent to an assembly in
        abaqus.

        Parameters
        ----------
        problem : obj
            compas_fea2 Problem object.

        Returns
        -------
        str
            text section for the input file.
        """
        return problem.model._generate_jobdata()

    def _generate_material_section(self, problem):
        """Generate the content relatitive to the material section for the input
        file.

        Parameters
        ----------
        problem : obj
            compas_fea2 Problem object.

        Returns
        -------
        str
            text section for the input file.
        """
        section_data = []
        for material in problem.model.materials.values():
            section_data.append(material.jobdata)
        return ''.join(section_data)

    def _generate_int_props_section(self, problem):
        # # Write interaction properties
        # for interaction_property in problem.model.interaction_properties:
        #     interaction_property.write_data_line(f)
        return ''

    def _generate_interactions_section(self, problem):
        #
        # # Write interactions
        # for interaction in problem.model.interactions:
        #     interaction.write_data_line(f)
        return ''

    def _generate_bcs_section(self, problem):
        """Generate the content relatitive to the boundary conditions section
        for the input file.

        Parameters
        ----------
        problem : obj
            compas_fea2 Problem object.

        Returns
        -------
        str
            text section for the input file.
        """
        section_data = []
        for bc in problem.bcs.values():
            section_data.append(bc._generate_jobdata())
        return ''.join(section_data)

    def _generate_steps_section(self, problem):
        """Generate the content relatitive to the steps section for the input
        file.

        Parameters
        ----------
        problem : obj
            compas_fea2 Problem object.

        Returns
        -------
        str
            text section for the input file.
        """
        section_data = []
        for step in problem.steps:
            if isinstance(step, ModalStep):  # TODO too messy - check!
                section_data.append(step._generate_jobdata())
            else:
                section_data.append(step._generate_jobdata(problem))

        return ''.join(section_data)


"""TODO: add cpu parallelization option
Parallel execution requested but no parallel feature present in the setup
"""


class ParFile(InputFileBase):
    """ParFile object for optimisation.

    Parameters
    ----------
    problem : obj
        Problem object.

    Attributes
    ----------
    name : str
        Par file name.
    job_name : str
        Name of the Abaqus job. This is the same as the input file name.

    """

    def __init__(self, problem):
        super(ParFile, self).__init__(problem)
        self._input_file_type = "Parameters File"
        self.name = '{}.par'.format(problem.name)
        self.input_name = '{}.inp'.format(problem.name)
        self.vf = problem.vf
        self.iter_max = problem.iter_max

        self._jobdata = self._generate_jobdata()

    @property
    def jobdata(self):
        """This property is the representation of the object in a software-specific inout file.

        Returns
        -------
        str

        Examples
        --------
        >>>
        """
        return self._jobdata

    def _generate_jobdata(self):
        """Generate the content of the parameter file from the optimisation
        settings of the Problem object.

        Parameters
        ----------
        problem : obj
            Problem object.

        Resturn
        -------
        str
            content of the .par file
        """
        return """FEM_INPUT
  ID_NAME        = OPTIMIZATION_MODEL
  FILE           = {}
END_

DV_TOPO
  ID_NAME        = design_variables
  EL_GROUP       = ALL_ELEMENTS
END_

DRESP
  ID_NAME        = DRESP_SUM_ENERGY
  DEF_TYPE       = SYSTEM
  TYPE           = STRAIN_ENERGY
  UPDATE         = EVER
  EL_GROUP       = ALL_ELEMENTS
  GROUP_OPER     = SUM
END_

DRESP
  ID_NAME        = DRESP_VOL_TOPO
  DEF_TYPE       = SYSTEM
  TYPE           = VOLUME
  UPDATE         = EVER
  EL_GROUP       = ALL_ELEMENTS
  GROUP_OPER     = SUM
END_

OBJ_FUNC
  ID_NAME        = maximize_stiffness
  DRESP          = DRESP_SUM_ENERGY
  TARGET         = MINMAX
END_

CONSTRAINT
  ID_NAME        = volume_constraint
  DRESP          = DRESP_VOL_TOPO
  MAGNITUDE      = REL
  EQ_VALUE       = {}
END_

OPTIMIZE
  ID_NAME        = topology_optimization
  DV             = design_variables
  OBJ_FUNC       = maximize_stiffness
  CONSTRAINT     = volume_constraint
  STRATEGY       = TOPO_CONTROLLER
END_

OPT_PARAM
  ID_NAME = topology_optimization_OPT_PARAM_
  OPTIMIZE = topology_optimization
  AUTO_FROZEN = LOAD
  DENSITY_UPDATE = NORMAL
  DENSITY_LOWER = 0.001
  DENSITY_UPPER = 1.
  DENSITY_MOVE = 0.25
  MAT_PENALTY = 3.
  STOP_CRITERION_LEVEL = BOTH
  STOP_CRITERION_OBJ = 0.001
  STOP_CRITERION_DENSITY = 0.005
  STOP_CRITERION_ITER = 4
  SUM_Q_FACTOR = 6.
END_


STOP
  ID_NAME        = global_stop
  ITER_MAX       = {}
END_

SMOOTH
  id_name = ISO_SMOOTHING_0_3
  task = iso
  iso_value = 0.3
  SELF_INTERSECTION_CHECK = runtime
  smooth_cycles = 10
  reduction_rate = 60
  reduction_angle = 5.0
  format = vtf
  format = stl
  format = onf
END_""".format(self.input_name, self.vf, self.iter_max)


if __name__ == "__main__":
    pass
