import os
from compas_fea2.backends.abaqus import Model
from compas_fea2.backends.abaqus import ElasticIsotropic
from compas_fea2.backends.abaqus import ShellSection
from compas_fea2.backends.abaqus import NodesGroup

from compas_fea2.backends.abaqus import Problem
from compas_fea2.backends.abaqus import FixedDisplacement
from compas_fea2.backends.abaqus import RollerDisplacementXZ
from compas_fea2.backends.abaqus import PointLoad
from compas_fea2.backends.abaqus import FieldOutput
from compas_fea2.backends.abaqus import GeneralStaticStep
from compas_fea2.backends.abaqus import Results

from compas_fea2.postprocessor.stresses import principal_stresses

from compas_fea2 import DATA
from compas_fea2 import TEMP

import gmsh
import sys
from math import degrees, atan2
from compas.datastructures import Mesh
from compas.geometry import centroid_points
import matplotlib.pyplot as plt


def gmsh_geometry(x, y, lc, path):
    gmsh.initialize(sys.argv)
    gmsh.model.add("t1")

    gmsh.model.geo.addPoint(0, 0, 0, lc, 1)
    gmsh.model.geo.addPoint(x, 0, 0, lc, 2)
    gmsh.model.geo.addPoint(x, y, 0, lc, 3)
    p4 = gmsh.model.geo.addPoint(0, y, 0, lc)
    gmsh.model.geo.addLine(1, 2, 1)
    gmsh.model.geo.addLine(3, 2, 2)
    gmsh.model.geo.addLine(3, p4, 3)
    gmsh.model.geo.addLine(4, 1, p4)
    gmsh.model.geo.addCurveLoop([4, 1, -2, 3], 1)
    gmsh.model.geo.addPlaneSurface([1], 1)

    gmsh.model.geo.synchronize()
    gmsh.model.addPhysicalGroup(1, [1, 2, 4], 5)
    ps = gmsh.model.addPhysicalGroup(2, [1])
    gmsh.model.setPhysicalName(2, ps, "My surface")

    # We can then generate a 2D mesh...
    gmsh.model.mesh.generate(2)
    print(gmsh.model.mesh.getNode(nodeTag=10))
    element = gmsh.model.mesh.getElement(10)
    # gmsh.model.mesh.getElementFaceNodes()
    # print(gmsh.model.mesh.getKeysForElement(1,'Lagrange'))

    # ... and save it to disk
    gmsh.write(path)
    gmsh.finalize()


def plot_vectors(problem, spr, e, scale):

    centroids = [centroid_points([problem.model.parts['part-1'].nodes[i].xyz for i in element.connectivity])
                 for element in problem.model.parts['part-1'].elements]
    x = [c[0] for c in centroids]
    y = [c[1] for c in centroids]

    for stype in ['max', 'min']:
        color = 'gray'  # if stype == 'max' else 'b'
        u = e[sp][stype][0]*spr['sp1'][stype]/2
        v = e[sp][stype][1]*spr['sp1'][stype]/2
        plt.quiver(x, y, u, v, color=color, width=1*10**-3)
        plt.quiver(x, y, -u, -v, color=color, width=1*10**-3)
    plt.axis('equal')
    plt.show()


# Generate a cantilever beam using gmsh
lx = 1000
ly = 3000
gmsh_geometry(lx, ly, 100, DATA+"/t1.stl")
mesh = Mesh.from_stl(DATA+"/t1.stl")

##### ----------------------------- MODEL ----------------------------- #####
# Initialise the assembly object
model = Model(name='cantilever_gmsh')

# Define materials
model.add_material(ElasticIsotropic(name='mat_A', E=29000, v=0.17, p=2.5e-9))

# Define sections
shell_20 = ShellSection(name='section_A', material='mat_A', t=20)

# Create a shell model from a mesh
model.shell_from_mesh(mesh=mesh, shell_section=shell_20)

# Find nodes in the model for the boundary conditions
n_fixed = model.get_node_from_coordinates([0, 0, 0, ], 1)
n_roller = model.get_node_from_coordinates([lx, 0, 0], 1)
n_load = model.get_node_from_coordinates([lx, ly, 0, ], 1)

# Define sets for boundary conditions and loads
model.add_instance_set(NodesGroup(name='fixed', selection=[n_fixed['part-1']], stype='nset'), instance='part-1-1')
model.add_instance_set(NodesGroup(name='roller', selection=[n_roller['part-1']], stype='nset'), instance='part-1-1')
model.add_instance_set(NodesGroup(name='pload', selection=[n_load['part-1']], stype='nset'), instance='part-1-1')

model.summary()

##### ----------------------------- PROBLEM ----------------------------- #####
folder = 'C:/temp/'
name = 'principal_stresses'

# Create the Problem object
problem = Problem(name='cantilever_gmsh', model=model)

# Assign boundary conditions to the node stes
problem.add_bcs(bcs=[RollerDisplacementXZ(name='bc_roller', bset='roller'),
                     FixedDisplacement(name='bc_fix', bset='fixed')])

# Assign a point load to the node set
problem.add_load(load=PointLoad(name='pload', lset='pload', x=1000))

# Define the field outputs required
problem.add_field_output(fout=FieldOutput(name='fout'))

# Define the analysis step
problem.add_step(step=GeneralStaticStep(name='gstep', loads=['pload']))

problem.summary()
# Solve the problem
problem.analyse(path=folder)
# print(os.path.join(problem.path, '{}-results.pkl'.format(problem.name)))

##### --------------------- POSTPROCESS RESULTS -------------------------- #####
results = Results.from_problem(problem, fields=['s'], output=True)
spr, e = principal_stresses(results.element['gstep'])

sp = 'sp5'
stype = 'max'

# check the results for an element
id = 0
print(f'the {stype} principal stress for element {id} is: ', spr[sp][stype][id])
print('principal axes (basis):\n', e[sp][stype][:, id])
print('and its inclination w.r.t. World is: ', degrees(atan2(*e[sp][stype][:, id][::-1])))

plot_vectors(problem, spr, e, 10)
