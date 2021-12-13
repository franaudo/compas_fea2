import inspect
from pathlib import Path
from pprint import pprint
from compas_fea2.backends.abaqus import Model
from compas_fea2.backends.abaqus import Part
from compas_fea2.backends.abaqus import Node
from compas_fea2.backends.abaqus import ElasticIsotropic
from compas_fea2.backends.abaqus import CircularSection
from compas_fea2.backends.abaqus import BeamElement
from compas_fea2.backends.abaqus import ShellElement
from compas_fea2.backends.abaqus import NodesGroup

from compas_fea2.backends.abaqus import Problem
from compas_fea2.backends.abaqus import PinnedDisplacement
from compas_fea2.backends.abaqus import ShellSection
from compas_fea2.backends.abaqus import PointLoad
from compas_fea2.backends.abaqus import GravityLoad
from compas_fea2.backends.abaqus import FieldOutput
from compas_fea2.backends.abaqus import GeneralStaticStep

from compas_fea2.backends.abaqus import Results

from compas_fea2.interfaces.viewer import ModelViewer
from compas_fea2.interfaces.viewer import ProblemViewer


from compas_fea2 import TEMP
from compas_fea2.backends.abaqus.model import nodes
from compas_fea2.backends.abaqus.problem.bcs import GeneralDisplacement

##### ----------------------------- MODEL ----------------------------- #####
# Initialise the assembly object
model = Model(name='structural_model')

# Add a Part to the model
model.add_part(Part(name='part-1'))
# Add nodes to the part
model.add_node(Node(xyz=[-5., -5., 0.]), part='part-1')
for node in [[5., -5., 0.], [5., 5., 0.], [-5., 5., 0.], [0., 0., 5.]]:
    model.add_node(Node(xyz=node), part='part-1')
# Define materials
model.add_material(ElasticIsotropic(name='mat_elastic', E=10*10**9, v=0.3, p=1500))

# Define sections
model.add_section(CircularSection(name='sec_circ', material='mat_elastic', r=0.010))
model.add_section(ShellSection(name='sec_shell', material='mat_elastic', t=0.005))

# Generate elements between nodes
elements = []
for conn in [[0, 4], [1, 4], [2, 4], [3, 4]]:
    elements.append((BeamElement(connectivity=conn, section='sec_circ')))
model.add_elements(elements=elements, part='part-1')
model.add_element(element=ShellElement(connectivity=[0, 1, 4], section='sec_shell'), part='part-1')

# Define sets for boundary conditions and loads
bset_base = NodesGroup(name='nset_base', selection=[0, 1, 2, 3], stype='nset')
model.add_instance_set(bset_base, instance='part-1-1')
model.add_instance_set(NodesGroup(name='nset_a', selection=[0], stype='nset'), instance='part-1-1')
model.add_instance_set(NodesGroup(name='nset_bcd', selection=[1, 2, 3], stype='nset'), instance='part-1-1')
nset_top = NodesGroup(name='nset_top', selection=[4], stype='nset')
model.add_instance_set(nset_top, instance='part-1-1')
model.add_instance_set(NodesGroup(name='elset_beams', selection=[0, 1, 2, 3], stype='elset'), instance='part-1-1')
model.add_instance_set(NodesGroup(name='elset_shell', selection=[4], stype='elset'), instance='part-1-1')
# model.summary()


##### ----------------------------- PROBLEM ----------------------------- #####

# Create the Problem object
problem = Problem(name='test_structure', model=model)

pin = PinnedDisplacement(name='bc_pinned', bset=bset_base)
# Assign boundary conditions to the node stes
problem.add_bc(pin)

# Assign a point load to the node set
step_0 = GeneralStaticStep(name='step_gravity')
step_1 = GeneralStaticStep(name='step_pload')
problem.add_load(PointLoad(name='load_point', lset=nset_top, x=10000, z=-10000), step_0)
problem.add_load(GravityLoad(name='load_gravity'), step_0)
problem.add_displacements([GeneralDisplacement('disp_pinned', 'nset_a', x=0, y=0, z=-0.05),
                           pin], step_1)

# Define the field outputs required
fout = FieldOutput(name='fout')
problem.add_output(fout, step_0)
problem.add_output(fout, step_1)

# Define the analysis step (there should be a message skipping the step, since they were already added)
problem.add_steps([step_0, step_1])

# problem.summary()
# v = ProblemViewer(problem)
# v.show()

# Solve the problem

problem.analyse(path=Path(TEMP).joinpath(problem.name))

# # ##### --------------------- POSTPROCESS RESULTS -------------------------- #####
# results = Results.from_problem(problem, fields=['u'])
# pprint(results.nodal)
