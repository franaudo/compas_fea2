from math import pi
from math import sqrt
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

import compas
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Scale
from compas.geometry import Transformation
from compas.geometry import Vector
from compas.geometry import bounding_box
from compas.geometry import centroid_points, centroid_points_weighted
from compas.geometry import distance_point_point_sqrd
from compas.geometry import is_point_in_polygon_xy
from compas.geometry import is_point_on_plane
from compas.tolerance import TOL
from scipy.spatial import KDTree

import compas_fea2
from compas_fea2.base import FEAData

from .elements import BeamElement
from .elements import HexahedronElement
from .elements import ShellElement
from .elements import TetrahedronElement
from .elements import _Element
from .elements import _Element1D
from .elements import _Element2D
from .elements import _Element3D
from .groups import ElementsGroup
from .groups import FacesGroup
from .groups import NodesGroup
from .materials.material import _Material
from .nodes import Node
from .releases import _BeamEndRelease
from .sections import ShellSection
from .sections import SolidSection
from .sections import _Section


class _Part(FEAData):
    """Base class for Parts.

    Parameters
    ----------
    name : str, optional
        Unique identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.

    Attributes
    ----------
    name : str
        Unique identifier. If not provided it is automatically generated. Set a
        name if you want a more human-readable input file.
    model : :class:`compas_fea2.model.Model`
        The parent model of the part.
    nodes : Set[:class:`compas_fea2.model.Node`]
        The nodes belonging to the part.
    nodes_count : int
        Number of nodes in the part.
    gkey_node : Dict[str, :class:`compas_fea2.model.Node`]
        Dictionary that associates each node and its geometric key.
    materials : Set[:class:`compas_fea2.model._Material`]
        The materials belonging to the part.
    sections : Set[:class:`compas_fea2.model._Section`]
        The sections belonging to the part.
    elements : Set[:class:`compas_fea2.model._Element`]
        The elements belonging to the part.
    element_types : Dict[:class:`compas_fea2.model._Element`, List[:class:`compas_fea2.model._Element`]]
        Dictionary with the elements of the part for each element type.
    element_count : int
        Number of elements in the part.
    nodesgroups : Set[:class:`compas_fea2.model.NodesGroup`]
        The groups of nodes belonging to the part.
    elementsgroups : Set[:class:`compas_fea2.model.ElementsGroup`]
        The groups of elements belonging to the part.
    facesgroups : Set[:class:`compas_fea2.model.FacesGroup`]
        The groups of element faces belonging to the part.
    boundary_mesh : :class:`compas.datastructures.Mesh`
        The outer boundary mesh enveloping the Part.
    discretized_boundary_mesh : :class:`compas.datastructures.Mesh`
        The discretized outer boundary mesh enveloping the Part.

    Notes
    -----
    Parts are registered to a :class:`compas_fea2.model.Model`.

    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._nodes: Set[Node] = set()
        self._gkey_node: Dict[str, Node] = {}
        self._sections: Set[_Section] = set()
        self._materials: Set[_Material] = set()
        self._elements: Set[_Element] = set()
        self._releases: Set[_BeamEndRelease] = set()

        self._nodesgroups: Set[NodesGroup] = set()
        self._elementsgroups: Set[ElementsGroup] = set()
        self._facesgroups: Set[FacesGroup] = set()

        self._boundary_mesh = None
        self._discretized_boundary_mesh = None
        self._bounding_box = None

    @property
    def __data__(self):
        return {
            "class": self.__class__.__base__,
            "ndm": self.ndm or None,
            "ndf": self.ndf or None,
            "nodes": [node.__data__ for node in self.nodes],
            "gkey_node": {key: node.__data__ for key, node in self.gkey_node.items()},
            "materials": [material.__data__ for material in self.materials],
            "sections": [section.__data__ for section in self.sections],
            "elements": [element.__data__ for element in self.elements],
            "releases": [release.__data__ for release in self.releases],
            "nodesgroups": [group.__data__ for group in self.nodesgroups],
            "elementsgroups": [group.__data__ for group in self.elementsgroups],
            "facesgroups": [group.__data__ for group in self.facesgroups],
        }

    @classmethod
    def __from_data__(cls, data):
        """Create a part instance from a data dictionary.

        Parameters
        ----------
        data : dict
            The data dictionary.

        Returns
        -------
        _Part
            The part instance.
        """
        part = cls()
        part._ndm = data.get("ndm", None)
        part._ndf = data.get("ndf", None)

        uid_node = {node_data["uid"]: Node.__from_data__(node_data) for node_data in data.get("nodes", {})}

        for material_data in data.get("materials", []):
            mat = part.add_material(material_data.pop("class").__from_data__(material_data))
            mat.uid = material_data["uid"]

        for section_data in data.get("sections", []):
            if mat := part.find_material_by_uid(section_data["material"]["uid"]):
                section_data.pop("material")
                section = part.add_section(section_data.pop("class")(material=mat, **section_data))
                section.uid = section_data["uid"]
            else:
                raise ValueError("Material not found")

        for element_data in data.get("elements", []):
            if sec := part.find_section_by_uid(element_data["section"]["uid"]):
                element_data.pop("section")
                nodes = [uid_node[node_data["uid"]] for node_data in element_data.pop("nodes")]
                for node in nodes:
                    node._registration = part
                element = element_data.pop("class")(nodes=nodes, section=sec, **element_data)
                part.add_element(element, checks=False)
            else:
                raise ValueError("Section not found")
        # for element in data.get("elements", []):
        #     part.add_element(element.pop("class").__from_data__(element))

        return part

    @property
    def nodes(self) -> Set[Node]:
        return self._nodes

    @property
    def points(self) -> List[List[float]]:
        return [node.xyz for node in self.nodes]

    @property
    def elements(self) -> Set[_Element]:
        return self._elements

    @property
    def sections(self) -> Set[_Section]:
        return self._sections

    @property
    def materials(self) -> Set[_Material]:
        return self._materials

    @property
    def releases(self) -> Set[_BeamEndRelease]:
        return self._releases

    @property
    def nodesgroups(self) -> Set[NodesGroup]:
        return self._nodesgroups

    @property
    def elementsgroups(self) -> Set[ElementsGroup]:
        return self._elementsgroups

    @property
    def facesgroups(self) -> Set[FacesGroup]:
        return self._facesgroups

    @property
    def gkey_node(self) -> Dict[str, Node]:
        return self._gkey_node

    @property
    def boundary_mesh(self):
        return self._boundary_mesh

    @property
    def discretized_boundary_mesh(self):
        return self._discretized_boundary_mesh

    @property
    def bounding_box(self) -> Optional[Box]:
        try:
            return Box.from_bounding_box(bounding_box([n.xyz for n in self.nodes]))
        except Exception:
            print("WARNING: BoundingBox not generated")
            return None

    @property
    def center(self) -> Point:
        """The geometric center of the part."""
        return centroid_points(self.bounding_box.points)

    @property
    def centroid(self) -> Point:
        """The geometric center of the part."""
        self.compute_nodal_masses()
        return centroid_points_weighted([node.point for node in self.nodes], [sum(node.mass) / len(node.mass) for node in self.nodes])

    @property
    def bottom_plane(self) -> Plane:
        return Plane.from_three_points(*[self.bounding_box.points[i] for i in self.bounding_box.bottom[:3]])

    @property
    def top_plane(self) -> Plane:
        return Plane.from_three_points(*[self.bounding_box.points[i] for i in self.bounding_box.top[:3]])

    @property
    def volume(self) -> float:
        self._volume = 0.0
        for element in self.elements:
            if element.volume:
                self._volume += element.volume
        return self._volume

    @property
    def weight(self) -> float:
        self._weight = 0.0
        for element in self.elements:
            if element.weight:
                self._weight += element.weight
        return self._weight

    @property
    def model(self):
        return self._registration

    @property
    def results(self):
        return self._results

    @property
    def nodes_count(self) -> int:
        return len(self.nodes) - 1

    @property
    def elements_count(self) -> int:
        return len(self.elements) - 1

    @property
    def element_types(self) -> Dict[type, List[_Element]]:
        element_types = {}
        for element in self.elements:
            element_types.setdefault(type(element), []).append(element)
        return element_types

    def assign_keys(self, start=1):
        [setattr(node, "_key", c) for c, node in enumerate(self.nodes, start)]
        [setattr(element, "_key", c) for c, element in enumerate(self.elements, start)]
        [setattr(section, "_key", c) for c, section in enumerate(self.sections, start)]
        [setattr(material, "_key", c) for c, material in enumerate(self.materials, start)]

    def transform(self, transformation: Transformation) -> None:
        """Transform the part.

        Parameters
        ----------
        transformation : :class:`compas.geometry.Transformation`
            The transformation to apply.

        """
        for node in self.nodes:
            node.transform(transformation)

    def transformed(self, transformation: Transformation) -> "_Part":
        """Return a transformed copy of the part.

        Parameters
        ----------
        transformation : :class:`compas.geometry.Transformation`
            The transformation to apply.
        """
        part = self.copy()
        part.transform(transformation)
        return part

    def elements_by_dimension(self, dimension: int = 1) -> Iterable[_Element]:
        if dimension == 1:
            return filter(lambda x: isinstance(x, _Element1D), self.elements)
        elif dimension == 2:
            return filter(lambda x: isinstance(x, _Element2D), self.elements)
        elif dimension == 3:
            return filter(lambda x: isinstance(x, _Element3D), self.elements)
        else:
            raise ValueError("dimension not supported")

    # =========================================================================
    #                       Constructor methods
    # =========================================================================

    @classmethod
    def from_compas_lines(
        cls,
        lines: List["compas.geometry.Line"],
        element_model: str = "BeamElement",
        xaxis: List[float] = [0, 1, 0],
        section: Optional["_Section"] = None,
        name: Optional[str] = None,
        **kwargs,
    ) -> "_Part":
        """Generate a part from a list of :class:`compas.geometry.Line`.

        Parameters
        ----------
        lines : list[:class:`compas.geometry.Line`]
            The lines to be converted.
        element_model : str, optional
            Implementation model for the element, by default 'BeamElement'.
        xaxis : list[float], optional
            The x-axis direction, by default [0,1,0].
        section : :class:`compas_fea2.model.BeamSection`, optional
            The section to be assigned to the elements, by default None.
        name : str, optional
            The name of the part, by default None (one is automatically generated).

        Returns
        -------
        :class:`compas_fea2.model.Part`
            The part.

        """
        import compas_fea2

        prt = cls(name=name)
        mass = kwargs.get("mass", None)
        for line in lines:
            frame = Frame(line.start, xaxis, line.vector)
            nodes = [prt.find_nodes_around_point(list(p), 1, single=True) or Node(list(p), mass=mass) for p in [line.start, line.end]]
            prt.add_nodes(nodes)
            element = getattr(compas_fea2.model, element_model)(nodes=nodes, section=section, frame=frame)
            if not isinstance(element, _Element1D):
                raise ValueError("Provide a 1D element")
            prt.add_element(element)
        return prt

    @classmethod
    def shell_from_compas_mesh(cls, mesh, section: ShellSection, name: Optional[str] = None, **kwargs) -> "_Part":
        """Creates a DeformablePart object from a :class:`compas.datastructures.Mesh`.

        To each face of the mesh is assigned a :class:`compas_fea2.model.ShellElement`
        object. Currently, the same section is applied to all the elements.

        Parameters
        ----------
        mesh : :class:`compas.datastructures.Mesh`
            Mesh to convert to a DeformablePart.
        section : :class:`compas_fea2.model.ShellSection`
            Shell section assigned to each face.
        name : str, optional
            Name of the new part. If ``None``, a unique identifier is assigned
            automatically.

        Returns
        -------
        :class:`compas_fea2.model.Part`
            The part.

        """
        implementation = kwargs.get("implementation", None)
        ndm = kwargs.get("ndm", None)
        part = cls(name=name, ndm=ndm) if ndm else cls(name=name)
        vertex_node = {vertex: part.add_node(Node(mesh.vertex_coordinates(vertex))) for vertex in mesh.vertices()}

        for face in mesh.faces():
            nodes = [vertex_node[vertex] for vertex in mesh.face_vertices(face)]
            element = ShellElement(nodes=nodes, section=section, implementation=implementation)
            part.add_element(element)

        part._boundary_mesh = mesh
        part._discretized_boundary_mesh = mesh

        return part

    @classmethod
    def from_gmsh(cls, gmshModel, section: Optional[Union[SolidSection, ShellSection]] = None, name: Optional[str] = None, **kwargs) -> "_Part":
        """Create a Part object from a gmshModel object.

        According to the `section` type provided, :class:`compas_fea2.model._Element2D` or
        :class:`compas_fea2.model._Element3D` elements are created.
        The same section is applied to all the elements.

        Parameters
        ----------
        gmshModel : object
            gmsh Model to convert. See [1]_.
        section : Union[SolidSection, ShellSection], optional
            `compas_fea2` :class:`SolidSection` or :class:`ShellSection` sub-class
            object to apply to the elements.
        name : str, optional
            Name of the new part.
        split : bool, optional
            If ``True`` create an additional node in the middle of the edges of the
            elements to implement more refined element types. Check for example [2]_.
        verbose : bool, optional
            If ``True`` print a log, by default False.
        check : bool, optional
            If ``True`` performs sanity checks, by default False. This is a quite
            resource-intense operation! Set to ``False`` for large models (>10000
            nodes).

        Returns
        -------
        _Part
            The part meshed.

        Notes
        -----
        The gmshModel must have the right dimension corresponding to the section provided.

        References
        ----------
        .. [1] https://gitlab.onelab.info/gmsh/gmsh/blob/gmsh_4_9_1/api/gmsh.py
        .. [2] https://web.mit.edu/calculix_v2.7/CalculiX/ccx_2.7/doc/ccx/node33.html

        Examples
        --------
        >>> mat = ElasticIsotropic(name="mat", E=29000, v=0.17, density=2.5e-9)
        >>> sec = SolidSection("mysec", mat)
        >>> part = DeformablePart.from_gmsh("part_gmsh", gmshModel, sec)

        """
        import numpy as np

        part = cls(name=name)

        gmshModel.heal()
        gmshModel.generate_mesh(3)
        model = gmshModel.model

        # add nodes
        node_coords = model.mesh.get_nodes()[1].reshape((-1, 3), order="C")
        fea2_nodes = np.array([part.add_node(Node(coords)) for coords in node_coords])

        # add elements
        gmsh_elements = model.mesh.get_elements()
        dimension = 2 if isinstance(section, SolidSection) else 1
        ntags_per_element = np.split(gmsh_elements[2][dimension] - 1, len(gmsh_elements[1][dimension]))  # gmsh keys start from 1

        verbose = kwargs.get("verbose", False)
        rigid = kwargs.get("rigid", False)
        implementation = kwargs.get("implementation", None)

        for ntags in ntags_per_element:
            if kwargs.get("split", False):
                raise NotImplementedError("this feature is under development")
            element_nodes = fea2_nodes[ntags]

            if ntags.size == 3:
                part.add_element(ShellElement(nodes=element_nodes, section=section, rigid=rigid, implementation=implementation))
            elif ntags.size == 4:
                if isinstance(section, ShellSection):
                    part.add_element(ShellElement(nodes=element_nodes, section=section, rigid=rigid, implementation=implementation))
                else:
                    part.add_element(TetrahedronElement(nodes=element_nodes, section=section))
                    part.ndf = 3  # FIXME try to move outside the loop
            elif ntags.size == 8:
                part.add_element(HexahedronElement(nodes=element_nodes, section=section))
            else:
                raise NotImplementedError(f"Element with {ntags.size} nodes not supported")
            if verbose:
                print(f"element {ntags} added")

        if not part._boundary_mesh:
            gmshModel.generate_mesh(2)  # FIXME Get the volumes without the mesh
            part._boundary_mesh = gmshModel.mesh_to_compas()

        if not part._discretized_boundary_mesh:
            part._discretized_boundary_mesh = part._boundary_mesh

        if rigid:
            point = part._discretized_boundary_mesh.centroid()
            part.reference_point = Node(xyz=[point.x, point.y, point.z])

        return part

    @classmethod
    def from_boundary_mesh(cls, boundary_mesh, name: Optional[str] = None, **kwargs) -> "_Part":
        """Create a Part object from a 3-dimensional :class:`compas.datastructures.Mesh`
        object representing the boundary envelope of the Part. The Part is
        discretized uniformly in Tetrahedra of a given mesh size.
        The same section is applied to all the elements.

        Parameters
        ----------
        boundary_mesh : :class:`compas.datastructures.Mesh`
            Boundary envelope of the DeformablePart.
        name : str, optional
            Name of the new Part.
        target_mesh_size : float, optional
            Target mesh size for the discretization, by default 1.
        mesh_size_at_vertices : dict, optional
            Dictionary of vertex keys and target mesh sizes, by default None.
        target_point_mesh_size : dict, optional
            Dictionary of point coordinates and target mesh sizes, by default None.
        meshsize_max : float, optional
            Maximum mesh size, by default None.
        meshsize_min : float, optional
            Minimum mesh size, by default None.

        Returns
        -------
        _Part
            The part.

        """
        from compas_gmsh.models import MeshModel

        target_mesh_size = kwargs.get("target_mesh_size", 1)
        mesh_size_at_vertices = kwargs.get("mesh_size_at_vertices", None)
        target_point_mesh_size = kwargs.get("target_point_mesh_size", None)
        meshsize_max = kwargs.get("meshsize_max", None)
        meshsize_min = kwargs.get("meshsize_min", None)

        gmshModel = MeshModel.from_mesh(boundary_mesh, targetlength=target_mesh_size)

        if mesh_size_at_vertices:
            for vertex, target in mesh_size_at_vertices.items():
                gmshModel.mesh_targetlength_at_vertex(vertex, target)

        if target_point_mesh_size:
            gmshModel.heal()
            for point, target in target_point_mesh_size.items():
                tag = gmshModel.model.occ.addPoint(*point, target)
                gmshModel.model.occ.mesh.set_size([(0, tag)], target)

        if meshsize_max:
            gmshModel.options.mesh.meshsize_max = meshsize_max
        if meshsize_min:
            gmshModel.options.mesh.meshsize_min = meshsize_min

        part = cls.from_gmsh(gmshModel=gmshModel, name=name, **kwargs)

        del gmshModel

        return part

    @classmethod
    def from_step_file(cls, step_file: str, name: Optional[str] = None, **kwargs) -> "_Part":
        """Create a Part object from a STEP file.

        Parameters
        ----------
        step_file : str
            Path to the STEP file.
        name : str, optional
            Name of the new Part.
        mesh_size_at_vertices : dict, optional
            Dictionary of vertex keys and target mesh sizes, by default None.
        target_point_mesh_size : dict, optional
            Dictionary of point coordinates and target mesh sizes, by default None.
        meshsize_max : float, optional
            Maximum mesh size, by default None.
        meshsize_min : float, optional
            Minimum mesh size, by default None.

        Returns
        -------
        _Part
            The part.

        """
        from compas_gmsh.models import MeshModel

        mesh_size_at_vertices = kwargs.get("mesh_size_at_vertices", None)
        target_point_mesh_size = kwargs.get("target_point_mesh_size", None)
        meshsize_max = kwargs.get("meshsize_max", None)
        meshsize_min = kwargs.get("meshsize_min", None)

        print("Creating the part from the step file...")
        gmshModel = MeshModel.from_step(step_file)

        if mesh_size_at_vertices:
            for vertex, target in mesh_size_at_vertices.items():
                gmshModel.mesh_targetlength_at_vertex(vertex, target)

        if target_point_mesh_size:
            gmshModel.heal()
            for point, target in target_point_mesh_size.items():
                tag = gmshModel.model.occ.addPoint(*point, target)
                gmshModel.model.occ.mesh.set_size([(0, tag)], target)

        if meshsize_max:
            gmshModel.heal()
            gmshModel.options.mesh.meshsize_max = meshsize_max
        if meshsize_min:
            gmshModel.heal()
            gmshModel.options.mesh.meshsize_min = meshsize_min

        part = cls.from_gmsh(gmshModel=gmshModel, name=name, **kwargs)

        del gmshModel
        print("Part created.")

        return part

    # =========================================================================
    #                           Materials methods
    # =========================================================================

    def find_materials_by_name(self, name: str) -> List[_Material]:
        """Find all materials with a given name.

        Parameters
        ----------
        name : str

        Returns
        -------
        List[_Material]
        """
        return [material for material in self.materials if material.name == name]

    def find_material_by_uid(self, uid: str) -> Optional[_Material]:
        """Find a material with a given unique identifier.

        Parameters
        ----------
        uid : str

        Returns
        -------
        Optional[_Material]
        """
        for material in self.materials:
            if material.uid == uid:
                return material
        return None

    def contains_material(self, material: _Material) -> bool:
        """Verify that the part contains a specific material.

        Parameters
        ----------
        material : _Material

        Returns
        -------
        bool
        """
        return material in self.materials

    def add_material(self, material: _Material) -> _Material:
        """Add a material to the part so that it can be referenced in section and element definitions.

        Parameters
        ----------
        material : _Material

        Returns
        -------
        _Material

        Raises
        ------
        TypeError
            If the material is not a material.
        """
        if not isinstance(material, _Material):
            raise TypeError(f"{material!r} is not a material.")

        self._materials.add(material)
        material._registration = self
        return material

    def add_materials(self, materials: List[_Material]) -> List[_Material]:
        """Add multiple materials to the part.

        Parameters
        ----------
        materials : List[_Material]

        Returns
        -------
        List[_Material]
        """
        return [self.add_material(material) for material in materials]

    def find_material_by_name(self, name: str) -> Optional[_Material]:
        """Find a material with a given name.

        Parameters
        ----------
        name : str

        Returns
        -------
        Optional[_Material]
        """
        for material in self.materials:
            if material.name == name:
                return material
        return None

    # =========================================================================
    #                        Sections methods
    # =========================================================================

    def find_sections_by_name(self, name: str) -> List[_Section]:
        """Find all sections with a given name.

        Parameters
        ----------
        name : str

        Returns
        -------
        List[_Section]
        """
        return [section for section in self.sections if section.name == name]

    def find_section_by_uid(self, uid: str) -> Optional[_Section]:
        """Find a section with a given unique identifier.

        Parameters
        ----------
        uid : str

        Returns
        -------
        Optional[_Section]
        """
        for section in self.sections:
            if section.uid == uid:
                return section
        return None

    def contains_section(self, section: _Section) -> bool:
        """Verify that the part contains a specific section.

        Parameters
        ----------
        section : _Section

        Returns
        -------
        bool
        """
        return section in self.sections

    def add_section(self, section: _Section) -> _Section:
        """Add a section to the part so that it can be referenced in element definitions.

        Parameters
        ----------
        section : :class:`compas_fea2.model.Section`

        Returns
        -------
        _Section

        Raises
        ------
        TypeError
            If the section is not a section.

        """
        if not isinstance(section, _Section):
            raise TypeError("{!r} is not a section.".format(section))

        self.add_material(section.material)
        self._sections.add(section)
        section._registration = self._registration
        return section

    def add_sections(self, sections: List[_Section]) -> List[_Section]:
        """Add multiple sections to the part.

        Parameters
        ----------
        sections : list[:class:`compas_fea2.model.Section`]

        Returns
        -------
        list[:class:`compas_fea2.model.Section`]
        """
        return [self.add_section(section) for section in sections]

    def find_section_by_name(self, name: str) -> Optional[_Section]:
        """Find a section with a given name.

        Parameters
        ----------
        name : str

        Returns
        -------
        Optional[_Section]
        """
        for section in self.sections:
            if section.name == name:
                return section
        return

    # =========================================================================
    #                           Nodes methods
    # =========================================================================
    def find_node_by_uid(self, uid: str) -> Optional[Node]:
        """Retrieve a node in the part using its unique identifier.

        Parameters
        ----------
        uid : str
            The node's unique identifier.

        Returns
        -------
        Optional[Node]
            The corresponding node, or None if not found.

        """
        for node in self.nodes:
            if node.uid == uid:
                return node
        return None

    def find_node_by_key(self, key: int) -> Optional[Node]:
        """Retrieve a node in the model using its key.

        Parameters
        ----------
        key : int
            The node's key.

        Returns
        -------
        Optional[Node]
            The corresponding node, or None if not found.

        """
        for node in self.nodes:
            if node.key == key:
                return node
        return None

    def find_node_by_inputkey(self, input_key: int) -> Optional[Node]:
        """Retrieve a node in the model using its input key.

        Parameters
        ----------
        input_key : int
            The node's input key.

        Returns
        -------
        Optional[Node]
            The corresponding node, or None if not found.

        """
        for node in self.nodes:
            if node.input_key == input_key:
                return node
        return None

    def find_nodes_by_name(self, name: str) -> List[Node]:
        """Find all nodes with a given name.

        Parameters
        ----------
        name : str

        Returns
        -------
        List[Node]
            List of nodes with the given name.

        """
        return [node for node in self.nodes if node.name == name]

    def find_nodes_around_point(
        self, point: List[float], distance: float, plane: Optional[Plane] = None, report: bool = False, single: bool = False, **kwargs
    ) -> Union[List[Node], Dict[Node, float], Optional[Node]]:
        """Find all nodes within a distance of a given geometrical location.

        Parameters
        ----------
        point : List[float]
            A geometrical location.
        distance : float
            Distance from the location.
        plane : Optional[Plane], optional
            Limit the search to one plane.
        report : bool, optional
            If True, return a dictionary with the node and its distance to the
            point, otherwise, just the node. By default is False.
        single : bool, optional
            If True, return only the closest node, by default False.

        Returns
        -------
        Union[List[Node], Dict[Node, float], Optional[Node]]
            List of nodes, or dictionary with nodes and distances if report=True,
            or the closest node if single=True.

        """
        d2 = distance**2
        nodes = self.find_nodes_on_plane(plane) if plane else self.nodes
        if report:
            return {node: sqrt(distance_point_point_sqrd(node.xyz, point)) for node in nodes if distance_point_point_sqrd(node.xyz, point) < d2}
        nodes = [node for node in nodes if distance_point_point_sqrd(node.xyz, point) < d2]
        if not nodes:
            if compas_fea2.VERBOSE:
                print(f"No nodes found at {point}")
            return [] if not single else None
        return nodes[0] if single else nodes

    def find_nodes_around_node(
        self, node: Node, distance: float, plane: Optional[Plane] = None, report: bool = False, single: bool = False
    ) -> Union[List[Node], Dict[Node, float], Optional[Node]]:
        """Find all nodes around a given node (excluding the node itself).

        Parameters
        ----------
        node : Node
            The given node.
        distance : float
            Search radius.
        plane : Optional[Plane], optional
            Limit the search to one plane.
        report : bool, optional
            If True, return a dictionary with the node and its distance to the point, otherwise, just the node. By default is False.
        single : bool, optional
            If True, return only the closest node, by default False.

        Returns
        -------
        Union[List[Node], Dict[Node, float], Optional[Node]]
            List of nodes, or dictionary with nodes and distances if report=True, or the closest node if single=True.
        """
        nodes = self.find_nodes_around_point(node.xyz, distance, plane, report=report, single=single)
        if nodes and isinstance(nodes, Iterable):
            if node in nodes:
                del nodes[node]
        return nodes

    def find_closest_nodes_to_point(self, point: List[float], number_of_nodes: int = 1, report: bool = False) -> Union[List[Node], Dict[Node, float]]:
        """
        Find the closest number_of_nodes nodes to a given point in the part.

        Parameters
        ----------
        point : List[float]
            List of coordinates representing the point in x, y, z.
        number_of_nodes : int
            The number of closest points to find.
        report : bool
            Whether to return distances along with the nodes.

        Returns
        -------
        List[Node] or Dict[Node, float]
            A list of the closest nodes, or a dictionary with nodes
            and distances if report=True.
        """
        if number_of_nodes <= 0:
            raise ValueError("The number of nodes to find must be greater than 0.")
        if number_of_nodes > len(self.nodes):
            raise ValueError("The number of nodes to find exceeds the available nodes.")

        tree = KDTree(self.points)
        distances, indices = tree.query(point, k=number_of_nodes)
        if number_of_nodes == 1:
            distances = [distances]
            indices = [indices]
        closest_nodes = [list(self.nodes)[i] for i in indices]

        if report:
            # Return a dictionary with nodes and their distances
            return {node: distance for node, distance in zip(closest_nodes, distances)}

        return closest_nodes

    def find_closest_nodes_to_node(self, node: Node, number_of_nodes: int = 1, report: Optional[bool] = False) -> List[Node]:
        """Find the n closest nodes around a given node (excluding the node itself).

        Parameters
        ----------
        node : Node
            The given node.
        distance : float
            Distance from the location.
        number_of_nodes : int
            Number of nodes to return.
        plane : Optional[Plane], optional
            Limit the search to one plane.

        Returns
        -------
        List[Node]
            List of the closest nodes.
        """
        return self.find_closest_nodes_to_point(node.xyz, number_of_nodes, report=report)

    def find_nodes_by_attribute(self, attr: str, value: float, tolerance: float = 0.001) -> List[Node]:
        """Find all nodes with a given value for the given attribute.

        Parameters
        ----------
        attr : str
            Attribute name.
        value : float
            Appropriate value for the given attribute.
        tolerance : float, optional
            Tolerance for numeric attributes, by default 0.001.

        Returns
        -------
        List[Node]
            List of nodes with the given attribute value.
        """
        return list(filter(lambda x: abs(getattr(x, attr) - value) <= tolerance, self.nodes))

    def find_nodes_on_plane(self, plane: Plane, tolerance: float = 1.0) -> List[Node]:
        """Find all nodes on a given plane.

        Parameters
        ----------
        plane : Plane
            The plane.
        tolerance : float, optional
            Tolerance for the search, by default 1.0.

        Returns
        -------
        List[Node]
            List of nodes on the given plane.
        """
        return list(filter(lambda x: is_point_on_plane(Point(*x.xyz), plane, tolerance), self.nodes))

    def find_nodes_in_polygon(self, polygon: "compas.geometry.Polygon", tolerance: float = 1.1) -> List[Node]:
        """Find the nodes of the part that are contained within a planar polygon.

        Parameters
        ----------
        polygon : compas.geometry.Polygon
            The polygon for the search.
        tolerance : float, optional
            Tolerance for the search, by default 1.1.

        Returns
        -------
        List[Node]
            List of nodes within the polygon.
        """
        if not hasattr(polygon, "plane"):
            try:
                polygon.plane = Frame.from_points(*polygon.points[:3])
            except Exception:
                polygon.plane = Frame.from_points(*polygon.points[-3:])

        S = Scale.from_factors([tolerance] * 3, polygon.frame)
        T = Transformation.from_frame_to_frame(Frame.from_plane(polygon.plane), Frame.worldXY())
        nodes_on_plane = self.find_nodes_on_plane(Plane.from_frame(polygon.plane))
        polygon_xy = polygon.transformed(S)
        polygon_xy = polygon.transformed(T)
        return list(filter(lambda x: is_point_in_polygon_xy(Point(*x.xyz).transformed(T), polygon_xy), nodes_on_plane))

    def find_nodes_where(self, conditions: List[str]) -> List[Node]:
        """Find the nodes where some conditions are met.

        Parameters
        ----------
        conditions : List[str]
            List with the strings of the required conditions.

        Returns
        -------
        List[Node]
            List of nodes meeting the conditions.
        """
        import re

        nodes = []
        for condition in conditions:
            part_nodes = self.nodes if not nodes else list(set.intersection(*nodes))
            try:
                eval(condition)
            except NameError as ne:
                var_name = re.findall(r"'([^']*)'", str(ne))[0]
                nodes.append(set(filter(lambda n: eval(condition.replace(var_name, str(getattr(n, var_name)))), part_nodes)))
        return list(set.intersection(*nodes))

    def contains_node(self, node: Node) -> bool:
        """Verify that the part contains a given node.

        Parameters
        ----------
        node : Node
            The node to check.

        Returns
        -------
        bool
            True if the node is in the part, False otherwise.
        """
        return node in self.nodes

    def add_node(self, node: Node) -> Node:
        """Add a node to the part.

        Parameters
        ----------
        node : :class:`compas_fea2.model.Node`
            The node.

        Returns
        -------
        :class:`compas_fea2.model.Node`
            The identifier of the node in the part.

        Raises
        ------
        TypeError
            If the node is not a node.

        Notes
        -----
        By adding a Node to the part, it gets registered to the part.

        Examples
        --------
        >>> part = DeformablePart()
        >>> node = Node(xyz=(1.0, 2.0, 3.0))
        >>> part.add_node(node)

        """
        if not isinstance(node, Node):
            raise TypeError("{!r} is not a node.".format(node))

        if compas_fea2.VERBOSE:
            if self.contains_node(node):
                print("NODE SKIPPED: Node {!r} already in part.".format(node))
            return node

        if not compas_fea2.POINT_OVERLAP:
            existing_node = self.find_nodes_around_point(node.xyz, distance=compas_fea2.GLOBAL_TOLERANCE)
            if existing_node:
                if compas_fea2.VERBOSE:
                    print("NODE SKIPPED: Part {!r} has already a node at {}.".format(self, node.xyz))
                return existing_node[0]

        if self.model:
            self._key = len(self.model.nodes)
        self._nodes.add(node)
        self._gkey_node[node.gkey] = node
        node._registration = self
        if compas_fea2.VERBOSE:
            print("Node {!r} registered to {!r}.".format(node, self))
        return node

    def add_nodes(self, nodes: List[Node]) -> List[Node]:
        """Add multiple nodes to the part.

        Parameters
        ----------
        nodes : list[:class:`compas_fea2.model.Node`]
            The list of nodes.

        Returns
        -------
        list[:class:`compas_fea2.model.Node`]

        Examples
        --------
        >>> part = DeformablePart()
        >>> node1 = Node([1.0, 2.0, 3.0])
        >>> node2 = Node([3.0, 4.0, 5.0])
        >>> node3 = Node([3.0, 4.0, 5.0])
        >>> nodes = part.add_nodes([node1, node2, node3])

        """
        return [self.add_node(node) for node in nodes]

    def remove_node(self, node: Node) -> None:
        """Remove a :class:`compas_fea2.model.Node` from the part.

        Warnings
        --------
        Removing nodes can cause inconsistencies.

        Parameters
        ----------
        node : :class:`compas_fea2.model.Node`
            The node to remove.

        """
        if self.contains_node(node):
            self.nodes.remove(node)
            self._gkey_node.pop(node.gkey)
            node._registration = None
            if compas_fea2.VERBOSE:
                print(f"Node {node!r} removed from {self!r}.")

    def remove_nodes(self, nodes: List[Node]) -> None:
        """Remove multiple :class:`compas_fea2.model.Node` from the part.

        Warnings
        --------
        Removing nodes can cause inconsistencies.

        Parameters
        ----------
        nodes : list[:class:`compas_fea2.model.Node`]
            List with the nodes to remove.

        """
        for node in nodes:
            self.remove_node(node)

    def is_node_on_boundary(self, node: Node, precision: Optional[float] = None) -> bool:
        """Check if a node is on the boundary mesh of the DeformablePart.

        Parameters
        ----------
        node : :class:`compas_fea2.model.Node`
            The node to evaluate.
        precision : float, optional
            Precision for the geometric key comparison, by default None.

        Returns
        -------
        bool
            `True` if the node is on the boundary, `False` otherwise.

        Notes
        -----
        The `discretized_boundary_mesh` of the part must have been previously defined.

        """
        if not self.discretized_boundary_mesh:
            raise AttributeError("The discretized_boundary_mesh has not been defined")
        if not node.on_boundary:
            node._on_boundary = TOL.geometric_key(node.xyz, precision) in self.discretized_boundary_mesh.gkey_vertex()
        return node.on_boundary

    def compute_nodal_masses(self) -> List[float]:
        """Compute the nodal mass of the part.

        Warnings
        --------
        Rotational masses are not considered.

        Returns
        -------
        list
            List with the nodal masses.

        """
        # clear masses
        for node in self.nodes:
            for i in range(len(node.mass)):
                node.mass[i] = 0.0

        for element in self.elements:
            for node in element.nodes:
                node.mass = [a + b for a, b in zip(node.mass, element.nodal_mass[:3])] + [0.0, 0.0, 0.0]
        return [sum(node.mass[i] for node in self.nodes) for i in range(3)]

    # =========================================================================
    #                           Elements methods
    # =========================================================================
    def find_element_by_key(self, key: int) -> Optional[_Element]:
        """Retrieve an element in the model using its key.

        Parameters
        ----------
        key : int
            The element's key.

        Returns
        -------
        Optional[_Element]
            The corresponding element, or None if not found.
        """
        for element in self.elements:
            if element.key == key:
                return element
        return None

    def find_element_by_inputkey(self, input_key: int) -> Optional[_Element]:
        """Retrieve an element in the model using its input key.

        Parameters
        ----------
        input_key : int
            The element's input key.

        Returns
        -------
        Optional[_Element]
            The corresponding element, or None if not found.
        """
        for element in self.elements:
            if element.input_key == input_key:
                return element
        return None

    def find_elements_by_name(self, name: str) -> List[_Element]:
        """Find all elements with a given name.

        Parameters
        ----------
        name : str

        Returns
        -------
        List[_Element]
            List of elements with the given name.
        """
        return [element for element in self.elements if element.name == name]

    def contains_element(self, element: _Element) -> bool:
        """Verify that the part contains a specific element.

        Parameters
        ----------
        element : _Element

        Returns
        -------
        bool
        """
        return element in self.elements

    def add_element(self, element: _Element, checks=True) -> _Element:
        """Add an element to the part.

        Parameters
        ----------
        element : _Element
            The element instance.
        checks : bool, optional
            Perform checks before adding the element, by default True.
            Turned off during copy operations.

        Returns
        -------
        _Element

        Raises
        ------
        TypeError
            If the element is not an instance of _Element.
        """
        if checks and (not isinstance(element, _Element) or self.contains_element(element)):
            if compas_fea2.VERBOSE:
                print(f"SKIPPED: {element!r} is not an element or already in part.")
            return element

        self.add_nodes(element.nodes)
        for node in element.nodes:
            node.connected_elements.add(element)
        self.add_section(element.section)
        self.elements.add(element)
        element._registration = self

        if compas_fea2.VERBOSE:
            print(f"Element {element!r} registered to {self!r}.")

        return element

    def add_elements(self, elements: List[_Element]) -> List[_Element]:
        """Add multiple elements to the part.

        Parameters
        ----------
        elements : List[_Element]

        Returns
        -------
        List[_Element]
        """
        return [self.add_element(element) for element in elements]

    def remove_element(self, element: _Element) -> None:
        """Remove an element from the part.

        Parameters
        ----------
        element : _Element
            The element to remove.

        Warnings
        --------
        Removing elements can cause inconsistencies.
        """
        if self.contains_element(element):
            self.elements.remove(element)
            element._registration = None
            for node in element.nodes:
                node.connected_elements.remove(element)
            if compas_fea2.VERBOSE:
                print(f"Element {element!r} removed from {self!r}.")

    def remove_elements(self, elements: List[_Element]) -> None:
        """Remove multiple elements from the part.

        Parameters
        ----------
        elements : List[_Element]
            List of elements to remove.

        Warnings
        --------
        Removing elements can cause inconsistencies.
        """
        for element in elements:
            self.remove_element(element)

    def is_element_on_boundary(self, element: _Element) -> bool:
        """Check if the element belongs to the boundary mesh of the part.

        Parameters
        ----------
        element : _Element
            The element to check.

        Returns
        -------
        bool
            True if the element is on the boundary, False otherwise.
        """
        from compas.geometry import centroid_points

        if element.on_boundary is None:
            if not self._discretized_boundary_mesh.centroid_face:
                centroid_face = {}
                for face in self._discretized_boundary_mesh.faces():
                    centroid_face[TOL.geometric_key(self._discretized_boundary_mesh.face_centroid(face))] = face
            if isinstance(element, _Element3D):
                if any(TOL.geometric_key(centroid_points([node.xyz for node in face.nodes])) in self._discretized_boundary_mesh.centroid_face for face in element.faces):
                    element.on_boundary = True
                else:
                    element.on_boundary = False
            elif isinstance(element, _Element2D):
                if TOL.geometric_key(centroid_points([node.xyz for node in element.nodes])) in self._discretized_boundary_mesh.centroid_face:
                    element.on_boundary = True
                else:
                    element.on_boundary = False
        return element.on_boundary

    # =========================================================================
    #                           Faces methods
    # =========================================================================

    def find_faces_on_plane(self, plane: Plane) -> List["compas_fea2.model.Face"]:
        """Find the faces of the elements that belong to a given plane, if any.

        Parameters
        ----------
        plane : :class:`compas.geometry.Plane`
            The plane where the faces should belong.

        Returns
        -------
        list[:class:`compas_fea2.model.Face`]
            List with the faces belonging to the given plane.

        Notes
        -----
        The search is limited to solid elements.
        """
        faces = []
        for element in filter(lambda x: isinstance(x, (_Element2D, _Element3D)) and self.is_element_on_boundary(x), self._elements):
            for face in element.faces:
                if all(is_point_on_plane(node.xyz, plane) for node in face.nodes):
                    faces.append(face)
        return faces

    # =========================================================================
    #                           Groups methods
    # =========================================================================

    def find_groups_by_name(self, name: str) -> List[Union[NodesGroup, ElementsGroup, FacesGroup]]:
        """Find all groups with a given name.

        Parameters
        ----------
        name : str
            The name of the group.

        Returns
        -------
        List[Union[NodesGroup, ElementsGroup, FacesGroup]]
            List of groups with the given name.
        """
        return [group for group in self.groups if group.name == name]

    def contains_group(self, group: Union[NodesGroup, ElementsGroup, FacesGroup]) -> bool:
        """Verify that the part contains a specific group.

        Parameters
        ----------
        group : Union[NodesGroup, ElementsGroup, FacesGroup]
            The group to check.

        Returns
        -------
        bool
            True if the group is in the part, False otherwise.
        """
        if isinstance(group, NodesGroup):
            return group in self._nodesgroups
        elif isinstance(group, ElementsGroup):
            return group in self._elementsgroups
        elif isinstance(group, FacesGroup):
            return group in self._facesgroups
        else:
            raise TypeError(f"{group!r} is not a valid Group")

    def add_group(self, group: Union[NodesGroup, ElementsGroup, FacesGroup]) -> Union[NodesGroup, ElementsGroup, FacesGroup]:
        """Add a node or element group to the part.

        Parameters
        ----------
        group : :class:`compas_fea2.model.NodesGroup` | :class:`compas_fea2.model.ElementsGroup` | :class:`compas_fea2.model.FacesGroup`

        Returns
        -------
        :class:`compas_fea2.model.Group`

        Raises
        ------
        TypeError
            If the group is not a node or element group.

        """

        if isinstance(group, NodesGroup):
            self.add_nodes(group.nodes)
        elif isinstance(group, ElementsGroup):
            self.add_elements(group.elements)

        if self.contains_group(group):
            if compas_fea2.VERBOSE:
                print("SKIPPED: Group {!r} already in part.".format(group))
            return group
        if isinstance(group, NodesGroup):
            self._nodesgroups.add(group)
        elif isinstance(group, ElementsGroup):
            self._elementsgroups.add(group)
        elif isinstance(group, FacesGroup):
            self._facesgroups.add(group)
        else:
            raise TypeError("{!r} is not a valid group.".format(group))
        group._registration = self  # BUG wrong because the members of the group might have a different registration
        return group

    def add_groups(self, groups: List[Union[NodesGroup, ElementsGroup, FacesGroup]]) -> List[Union[NodesGroup, ElementsGroup, FacesGroup]]:
        """Add multiple groups to the part.

        Parameters
        ----------
        groups : list[:class:`compas_fea2.model.Group`]

        Returns
        -------
        list[:class:`compas_fea2.model.Group`]

        """
        return [self.add_group(group) for group in groups]

    # ==============================================================================
    # Results methods
    # ==============================================================================

    def sorted_nodes_by_displacement(self, step: "_Step", component: str = "length") -> List[Node]:  # noqa: F821
        """Return a list with the nodes sorted by their displacement

        Parameters
        ----------
        step : :class:`compas_fea2.problem._Step`
            The step.
        component : str, optional
            One of ['x', 'y', 'z', 'length'], by default 'length'.

        Returns
        -------
        list[:class:`compas_fea2.model.Node`]
            The nodes sorted by displacement (ascending).

        """
        return sorted(self.nodes, key=lambda n: getattr(Vector(*n.results[step.problem][step].get("U", None)), component))

    def get_max_displacement(self, problem: "Problem", step: Optional["_Step"] = None, component: str = "length") -> Tuple[Node, float]:  # noqa: F821
        """Retrieve the node with the maximum displacement

        Parameters
        ----------
        problem : :class:`compas_fea2.problem.Problem`
            The problem.
        step : :class:`compas_fea2.problem._Step`, optional
            The step, by default None. If not provided, the last step of the
            problem is used.
        component : str, optional
            One of ['x', 'y', 'z', 'length'], by default 'length'.

        Returns
        -------
        :class:`compas_fea2.model.Node`, float
            The node and the displacement.

        """
        step = step or problem._steps_order[-1]
        node = self.sorted_nodes_by_displacement(step=step, component=component)[-1]
        displacement = getattr(Vector(*node.results[problem][step].get("U", None)), component)
        return node, displacement

    def get_min_displacement(self, problem: "Problem", step: Optional["_Step"] = None, component: str = "length") -> Tuple[Node, float]:  # noqa: F821
        """Retrieve the node with the minimum displacement

        Parameters
        ----------
        problem : :class:`compas_fea2.problem.Problem`
            The problem.
        step : :class:`compas_fea2.problem._Step`, optional
            The step, by default None. If not provided, the last step of the
            problem is used.
        component : str, optional
            One of ['x', 'y', 'z', 'length'], by default 'length'.

        Returns
        -------
        :class:`compas_fea2.model.Node`, float
            The node and the displacement.

        """
        step = step or problem._steps_order[-1]
        node = self.sorted_nodes_by_displacement(step=step, component=component)[0]
        displacement = getattr(Vector(*node.results[problem][step].get("U", None)), component)
        return node, displacement

    def get_average_displacement_at_point(
        self,
        problem: "Problem",  # noqa: F821
        point: List[float],
        distance: float,
        step: Optional["_Step"] = None,  # noqa: F821
        component: str = "length",
        project: bool = False,  # noqa: F821
    ) -> Tuple[List[float], float]:
        """Compute the average displacement around a point

        Parameters
        ----------
        problem : :class:`compas_fea2.problem.Problem`
            The problem.
        step : :class:`compas_fea2.problem._Step`, optional
            The step, by default None. If not provided, the last step of the
            problem is used.
        component : str, optional
            One of ['x', 'y', 'z', 'length'], by default 'length'.
        project : bool, optional
            If True, project the point onto the plane, by default False.

        Returns
        -------
        List[float], float
            The point and the average displacement.

        """
        step = step or problem._steps_order[-1]
        nodes = self.find_nodes_around_point(point=point, distance=distance, report=True)
        if nodes:
            displacements = [getattr(Vector(*node.results[problem][step].get("U", None)), component) for node in nodes]
            return point, sum(displacements) / len(displacements)
        return point, 0.0

    # ==============================================================================
    # Viewer
    # ==============================================================================

    def show(self, scale_factor: float = 1, draw_nodes: bool = False, node_labels: bool = False, solid: bool = False):
        """Draw the parts.

        Parameters
        ----------
        scale_factor : float, optional
            Scale factor for the visualization, by default 1.
        draw_nodes : bool, optional
            If `True` draw the nodes of the part, by default False.
        node_labels : bool, optional
            If `True` add the node labels, by default False.
        solid : bool, optional
            If `True` draw all the elements (also the internal ones) of the part
            otherwise just show the boundary faces, by default False.
        """

        from compas_fea2.UI.viewer import FEA2Viewer

        v = FEA2Viewer(self, scale_factor=scale_factor)

        if solid:
            v.draw_solid_elements(filter(lambda x: isinstance(x, _Element3D), self.elements), show_vertices=draw_nodes)
        else:
            if self.discretized_boundary_mesh:
                v.app.add(self.discretized_boundary_mesh, use_vertex_color=True)
        v.draw_shell_elements(
            filter(lambda x: isinstance(x, ShellElement), self.elements),
            show_vertices=draw_nodes,
        )
        v.draw_beam_elements(filter(lambda x: isinstance(x, BeamElement), self.elements), show_vertices=draw_nodes)
        # if draw_nodes:
        #     v.draw_nodes(self.nodes, node_labels)
        v.show()


class DeformablePart(_Part):
    """Deformable part."""

    __doc__ += _Part.__doc__
    __doc__ += """
    Additional Attributes
    ---------------------
    materials : Set[:class:`compas_fea2.model._Material`]
        The materials belonging to the part.
    sections : Set[:class:`compas_fea2.model._Section`]
        The sections belonging to the part.
    releases : Set[:class:`compas_fea2.model._BeamEndRelease`]
        The releases belonging to the part.

    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def materials(self) -> Set[_Material]:
        return self._materials
        return set(section.material for section in self.sections if section.material)

    @property
    def sections(self) -> Set[_Section]:
        return self._sections
        return set(element.section for element in self.elements if element.section)

    @property
    def releases(self) -> Set[_BeamEndRelease]:
        return self._releases

    # =========================================================================
    #                       Constructor methods
    # =========================================================================
    @classmethod
    def frame_from_compas_mesh(cls, mesh: "compas.datastructures.Mesh", section: "compas_fea2.model.BeamSection", name: Optional[str] = None, **kwargs) -> "_Part":
        """Creates a DeformablePart object from a :class:`compas.datastructures.Mesh`.

        To each edge of the mesh is assigned a :class:`compas_fea2.model.BeamElement`.
        Currently, the same section is applied to all the elements.

        Parameters
        ----------
        mesh : :class:`compas.datastructures.Mesh`
            Mesh to convert to a DeformablePart.
        section : :class:`compas_fea2.model.BeamSection`
            Section to assign to the frame elements.
        name : str, optional
            Name of the new part.

        Returns
        -------
        _Part
            The part created from the mesh.
        """
        part = cls(name=name, **kwargs)
        vertex_node = {vertex: part.add_node(Node(mesh.vertex_coordinates(vertex))) for vertex in mesh.vertices()}

        for edge in mesh.edges():
            nodes = [vertex_node[vertex] for vertex in edge]
            faces = mesh.edge_faces(edge)
            normals = [mesh.face_normal(f) for f in faces if f is not None]
            if len(normals) == 1:
                normal = normals[0]
            else:
                normal = normals[0] + normals[1]
            direction = list(mesh.edge_direction(edge))
            frame = normal
            frame.rotate(pi / 2, direction, nodes[0].xyz)
            part.add_element(BeamElement(nodes=nodes, section=section, frame=frame))

        return part

    @classmethod
    def from_gmsh(cls, gmshModel: object, section: Union["compas_fea2.model.SolidSection", "compas_fea2.model.ShellSection"], name: Optional[str] = None, **kwargs) -> "_Part":
        """Create a Part object from a gmshModel object.

        Parameters
        ----------
        gmshModel : object
            gmsh Model to convert.
        section : Union[compas_fea2.model.SolidSection, compas_fea2.model.ShellSection]
            Section to assign to the elements.
        name : str, optional
            Name of the new part.

        Returns
        -------
        _Part
            The part created from the gmsh model.
        """
        return super().from_gmsh(gmshModel, section=section, name=name, **kwargs)

    @classmethod
    def from_boundary_mesh(
        cls, boundary_mesh: "compas.datastructures.Mesh", section: Union["compas_fea2.model.SolidSection", "compas_fea2.model.ShellSection"], name: Optional[str] = None, **kwargs
    ) -> "_Part":
        """Create a Part object from a 3-dimensional :class:`compas.datastructures.Mesh`
        object representing the boundary envelope of the Part.

        Parameters
        ----------
        boundary_mesh : :class:`compas.datastructures.Mesh`
            Boundary envelope of the DeformablePart.
        section : Union[compas_fea2.model.SolidSection, compas_fea2.model.ShellSection]
            Section to assign to the elements.
        name : str, optional
            Name of the new part.

        Returns
        -------
        _Part
            The part created from the boundary mesh.
        """
        return super().from_boundary_mesh(boundary_mesh, section=section, name=name, **kwargs)

    # =========================================================================
    #                           Releases methods
    # =========================================================================

    def add_beam_release(self, element: BeamElement, location: str, release: _BeamEndRelease) -> _BeamEndRelease:
        """Add a :class:`compas_fea2.model._BeamEndRelease` to an element in the part.

        Parameters
        ----------
        element : :class:`compas_fea2.model.BeamElement`
            The element to release.
        location : str
            'start' or 'end'.
        release : :class:`compas_fea2.model._BeamEndRelease`
            Release type to apply.

        Returns
        -------
        :class:`compas_fea2.model._BeamEndRelease`
            The release applied to the element.
        """
        if not isinstance(release, _BeamEndRelease):
            raise TypeError(f"{release!r} is not a beam release element.")
        release.element = element
        release.location = location
        self._releases.add(release)
        return release


class RigidPart(_Part):
    """Rigid part."""

    __doc__ += _Part.__doc__
    __doc__ += """
    Additional Attributes
    ---------------------
    reference_point : :class:`compas_fea2.model.Node`
        A node acting as a reference point for the part, by default `None`. This
        is required if the part is rigid as it controls its movement in space.

    """

    def __init__(self, reference_point: Optional[Node] = None, **kwargs):
        super().__init__(**kwargs)
        self._reference_point = reference_point

    @property
    def __data__(self):
        data = super().__data__()
        data.update(
            {
                "class": self.__class__.__name__,
                "reference_point": self.reference_point.__data__ if self.reference_point else None,
            }
        )
        return data

    @classmethod
    def __from_data__(cls, data):
        """Create a part instance from a data dictionary.

        Parameters
        ----------
        data : dict
            The data dictionary.

        Returns
        -------
        _Part
            The part instance.
        """
        from compas_fea2.model import Node

        part = cls(reference_point=Node.__from_data__(data["reference_point"]))
        for element_data in data.get("elements", []):
            part.add_element(_Element.__from_data__(element_data))
        return part

    @property
    def reference_point(self) -> Optional[Node]:
        return self._reference_point

    @reference_point.setter
    def reference_point(self, value: Node):
        self._reference_point = self.add_node(value)
        value._is_reference = True

    @classmethod
    def from_gmsh(cls, gmshModel: object, name: Optional[str] = None, **kwargs) -> "_Part":
        """Create a RigidPart object from a gmshModel object.

        Parameters
        ----------
        gmshModel : object
            gmsh Model to convert.
        name : str, optional
            Name of the new part.

        Returns
        -------
        _Part
            The part created from the gmsh model.
        """
        kwargs["rigid"] = True
        return super().from_gmsh(gmshModel, name=name, **kwargs)

    @classmethod
    def from_boundary_mesh(cls, boundary_mesh: "compas.datastructures.Mesh", name: Optional[str] = None, **kwargs) -> "_Part":
        """Create a RigidPart object from a 3-dimensional :class:`compas.datastructures.Mesh`
        object representing the boundary envelope of the Part.

        Parameters
        ----------
        boundary_mesh : :class:`compas.datastructures.Mesh`
            Boundary envelope of the RigidPart.
        name : str, optional
            Name of the new part.

        Returns
        -------
        _Part
            The part created from the boundary mesh.
        """
        kwargs["rigid"] = True
        return super().from_boundary_mesh(boundary_mesh, name=name, **kwargs)

    # =========================================================================
    #                        Elements methods
    # =========================================================================
    # TODO this can be removed and the checks on the rigid part can be done in _part

    def add_element(self, element: _Element) -> _Element:
        # type: (_Element) -> _Element
        """Add an element to the part.

        Parameters
        ----------
        element : :class:`compas_fea2.model._Element`
            The element instance.

        Returns
        -------
        :class:`compas_fea2.model._Element`

        Raises
        ------
        TypeError
            If the element is not an element.

        """
        if not hasattr(element, "rigid"):
            raise TypeError("The element type cannot be assigned to a RigidPart")
        if not getattr(element, "rigid"):
            raise TypeError("Rigid parts can only have rigid elements")
        return super().add_element(element)
