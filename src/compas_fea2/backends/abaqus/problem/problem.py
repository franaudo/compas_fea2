from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import pickle
import sys

from compas_fea2.backends._base.problem import ProblemBase

from compas_fea2.backends.abaqus.job.input_file import InputFile
from compas_fea2.backends.abaqus.job.send_job import launch_process
from compas_fea2.backends.abaqus.job.read_results import extract_data

# Author(s): Francesco Ranaudo (github.com/franaudo)

__all__ = [
    'Problem',
]

class Problem(ProblemBase):
    """Initialises the Problem object.

    Parameters
    ----------
    name : str
        Name of the Structure.
    model : obj
        model object.

    Attributes
    ----------
    name : str
        Name of the Structure.
    parts : list
        List of the parts in the model.
    model : obj
        model object.
    bc : list
        List containing the boundary conditions objects.
    interactions : list
        List containing the interaction objects.
    steps : list
        List containing the Steps objects.

    """
    def __init__(self, name, model):
        super(Problem, self).__init__(name=name, model=model)
        self.parts              = model.parts.values()
        # self.interactions       = model.interactions


    # =========================================================================
    #                         Analysis methods
    # =========================================================================

    def write_input_file(self, path='C:/temp', output=True, save=False, ):
        """Writes abaqus input file.

        Parameters
        ----------
        path : str
            Path to the folder where the input file will be saved.
        output : bool
            Print terminal output.
        save : bool
            Save structure to .cfea before file writing.

        Returns
        -------
        None

        """

        if not os.path.exists(path):
            os.makedirs(path)
        filepath = '{0}/{1}.inp'.format(path, self.name)

        if save:
            self.save_to_cfea()

        input_file = InputFile(self, filepath)
        input_file.write_to_file()
        if output:
            print('***** Input file generated: {0} *****\n'.format(filepath))

    # this should be an abstract method of the base class
    def analyse(self, path, exe=None, cpus=1, output=True, overwrite=True,
                user_mat=False, save=False):
        """Runs the analysis through abaqus.

        Parameters
        ----------

        exe : str
            Full terminal command to bypass subprocess defaults.
        cpus : int
            Number of CPU cores to use.
        output : bool
            Print terminal output.
        user_mat : str TODO: REMOVE!
            Name of the material defined through a subroutine (currently only one material is supported)
        save : bool
            Save structure to .cfea before file writing.

        Returns
        -------
        None

        """
        self.write_input_file(path=path, output=output, save=save)
        launch_process(self, path=path, exe=exe, cpus=cpus, output=output,
                       overwrite=overwrite, user_mat=user_mat)


    # =========================================================================
    #                         Results methods
    # =========================================================================

    # # this should be an abstract method of the base class
    # def extract(self, fields='u', steps='all', exe=None, sets=None, license='research', output=True,
    #                  return_data=True, components=None):
    #     """Extracts data from the analysis output files.

    #     Parameters
    #     ----------
    #     fields : list, str
    #         Data field requests.
    #     steps : list
    #         Loads steps to extract from.
    #     exe : str
    #         Full terminal command to bypass subprocess defaults.
    #     sets : list
    #         -
    #     license : str
    #         Software license type: 'research', 'student'.
    #     output : bool
    #         Print terminal output.
    #     return_data : bool
    #         Return data back into structure.results.
    #     components : list
    #         Specific components to extract from the fields data.

    #     Returns
    #     -------
    #     None

    #     """
    #     extract_data(self, fields=fields, exe=exe, output=output, return_data=return_data,
    #                         components=components)

    # # this should be an abstract method of the base class
    # def analyse_and_extract(self, fields='u', exe=None, cpus=4, license='research', output=True, save=False,
    #                         return_data=True, components=None, user_mat=False, overwrite=True):
    #     """Runs the analysis through the chosen FEA software / library and extracts data.

    #     Parameters
    #     ----------
    #     fields : list, str
    #         Data field requests.
    #     exe : str
    #         Full terminal command to bypass subprocess defaults.
    #     cpus : int
    #         Number of CPU cores to use.
    #     license : str
    #         Software license type: 'research', 'student'.
    #     output : bool
    #         Print terminal output.
    #     save : bool
    #         Save the structure to .obj before writing.
    #     return_data : bool
    #         Return data back into structure.results.
    #     components : list
    #         Specific components to extract from the fields data.
    #     user_sub : bool
    #         Specify the user subroutine if needed.
    #     delete : bool
    #         If True, the analysis results are deleted after being read. [Not Implemented yet]

    #     Returns
    #     -------
    #     None

    #     """

    #     self.analyse(exe=exe, fields=fields, cpus=cpus, license=license, output=output, user_mat=user_mat,
    #                 overwrite=overwrite, save=save)

    #     self.extract(fields=fields, exe=exe, license=license, output=output,
    #                 return_data=return_data, components=components)

    # # this should be stored in a more generic way
    # def get_nodal_results(self, step, field, nodes='all'):
    #     """Extract nodal results from self.results.

    #     Parameters
    #     ----------
    #     step : str
    #         Step to extract from.
    #     field : str
    #         Data field request.
    #     nodes : str, list
    #         Extract 'all' or a node set/list.

    #     Returns
    #     -------
    #     dict
    #         The nodal results for the requested field.
    #     """
    #     data  = {}
    #     rdict = self.results[step]['nodal']

    #     if nodes == 'all':
    #         keys = list(self.nodes.keys())
    #     elif isinstance(nodes, str):
    #         keys = self.sets[nodes].selection
    #     else:
    #         keys = nodes

    #     for key in keys:
    #         data[key] = rdict[field][key]

    #     return data


    # def get_element_results(self, step, field, elements='all'):
    #     """Extract element results from self.results.

    #     Parameters
    #     ----------
    #     step : str
    #         Step to extract from.
    #     field : str
    #         Data field request.
    #     elements : str, list
    #         Extract 'all' or an element set/list.

    #     Returns
    #     -------
    #     dict
    #         The element results for the requested field.

    #     """
    #     data  = {}
    #     rdict = self.results[step]['element']

    #     if elements == 'all':
    #         keys = list(self.elements.keys())
    #     elif isinstance(elements, str):
    #         keys = self.sets[elements].selection
    #     else:
    #         keys = elements

    #     for key in keys:
    #         data[key] = rdict[field][key]

    #     return data
