from compas.datastructures import Mesh
from compas.geometry import normalize_vector

from compas_fea2.backends.abaqus.model import Model
from compas_fea2.backends.abaqus.model import Part
from compas_fea2.backends.abaqus.model import Node
from compas_fea2.backends.abaqus.model import ElasticIsotropic
from compas_fea2.backends.abaqus.model import BoxSection
from compas_fea2.backends.abaqus.model import BeamElement
from compas_fea2.backends.abaqus.model import Set

from compas_fea2.backends.abaqus.problem import Problem
from compas_fea2.backends.abaqus.problem import FixedDisplacement
from compas_fea2.backends.abaqus.problem import RollerDisplacementXZ
from compas_fea2.backends.abaqus.problem import PointLoad
from compas_fea2.backends.abaqus.problem import FieldOutput
from compas_fea2.backends.abaqus.problem import GeneralStaticStep

from compas_fea2 import DATA
##### ------------------------------ MODEL ------------------------------ #####

# Initialise the assembly object
model = Model(name='hypar')

# Add a Part to the model
model.add_part(Part(name='part-1'))

mesh = Mesh.from_obj(DATA + '/hypar.obj')
for v in mesh.vertices():
    model.add_node(Node(mesh.vertex_coordinates(v)), 'part-1')

# Define materials
model.add_material(ElasticIsotropic(name='mat_A', E=29000, v=0.17, p=2.5e-9))

# Generate elements between nodes
key_index = mesh.key_index()
vertices = list(mesh.vertices())
edges = [(key_index[u], key_index[v]) for u, v in mesh.edges()]

c=0
for e in edges:
    # get elements orientation
    v = normalize_vector(mesh.edge_vector(e[0], e[1]))
    v.append(v.pop(0))
    # define sections and add element to the model
    model.add_section(BoxSection(name='section_'+str(c), material='mat_A', a=20+c, b=80+c, t1=5, t2=5, t3=5, t4=5))
    model.add_element(BeamElement(connectivity=[e[0], e[1]], section='section_'+str(c), orientation=v), part='part-1')
    c+=1

n_fixed = model.get_node_from_coordinates([5000, 0, 0,], 10)
n_roller = model.get_node_from_coordinates([0, 3000, 0,], 10)
n_load  = model.get_node_from_coordinates([0, 0, -5000], 10)

# Define sets for boundary conditions and loads
model.add_assembly_set(Set(name='fixed', selection=[n_fixed['part-1']], stype='nset'), instance='part-1-1')
model.add_assembly_set(Set(name='roller', selection=[n_roller['part-1']], stype='nset'), instance='part-1-1')
model.add_assembly_set(Set(name='pload', selection=[n_load['part-1']], stype='nset'), instance='part-1-1')


##### ----------------------------- PROBLEM ----------------------------- #####

# Create the Problem object
problem = Problem(name='hypar_variable', model=model)

# Assign boundary conditions to the node stes
problem.add_bcs(bcs=[RollerDisplacementXZ(name='bc_roller', bset='roller'),
                        FixedDisplacement(name='bc_fix', bset='fixed')])

# Assign a point load to the node set
problem.add_load(load=PointLoad(name='pload', lset='pload', y=-1000))

# Define the analysis step
problem.add_step(step=GeneralStaticStep(name='gstep', loads=['pload']))

# Solve the problem
# problem.write_input_file(path='C:/temp/test_structure')
problem.analyse(path='C:/temp/hypar_variable_sections')
