from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import matplotlib.pyplot as plt
import numpy as np
from compas.geometry import Frame
from compas.geometry import Transformation
from compas.geometry import Vector

from compas_fea2.base import FEAData
from compas_fea2.model import ElasticIsotropic


class Result(FEAData):
    """Result object defined at the nodes or elements. This ensures that the results from all
    the backends are consistently stored.

    Parameters
    ----------
    location : :class:`compas_fea2.model.Node` | :class:`compas_fea2.model._Element`
        The location of the result. It can be either a Node or an Element.
    components : dict
        A dictionary with {"component name": component value} for each component of the result.
    invariants : dict
        A dictionary with {"invariant name": invariant value} for each invariant of the result.

    Attributes
    ----------
    location : :class:`compas_fea2.model.Node` | :class:`compas_fea2.model._Element`
        The location of the result. I can be either a Node or an Element.
    components : dict
        A dictionary with {"component name": component value} for each component of the result.
    invariants : dict
        A dictionary with {"invariant name": invariant value} for each invariant of the result.

    """

    def __init__(self, **kwargs):
        super(Result, self).__init__(**kwargs)
        self._title = None
        self._registration = None
        self._components = {}
        self._invariants = {}

    @property
    def title(self):
        return self._title

    @property
    def location(self):
        return self._registration

    @property
    def reference_point(self):
        return self.location.reference_point

    @property
    def components(self):
        return self._components

    @property
    def invariants(self):
        return self._invariants

    def to_file(self, *args, **kwargs):
        raise NotImplementedError("this function is not available for the selected backend")

    def safety_factor(self, component, allowable):
        """Compute the safety factor (absolute ration value/limit) of the displacement.

        Parameters
        ----------
        component : int
            The component of the displacement vector. Either 1, 2, or 3.
        allowable : float
            Limit to compare with.

        Returns
        -------
        float
            The safety factor. Values higher than 1 are not safe.
        """
        return abs(self.vector[component] / allowable) if self.vector[component] != 0 else 1


class NodeResult(Result):
    """NodeResult object.

    Parameters
    ----------
    node : :class:`compas_fea2.model.Node`
        The location of the result.
    components : dict
        A dictionary with {"component name": component value} for each component of the result.
    invariants : dict
        A dictionary with {"invariant name": invariant value} for each invariant of the result.

    Attributes
    ----------
    location : :class:`compas_fea2.model.Node`
        The location of the result.
    node : :class:`compas_fea2.model.Node`
        The location of the result.
    components : dict
        A dictionary with {"component name": component value} for each component of the result.
    invariants : dict
        A dictionary with {"invariant name": invariant value} for each invariant of the result.

    Notes
    -----
    NodeResults are registered to a :class:`compas_fea2.model.Node`
    """

    def __init__(self, node, title, x=None, y=None, z=None, xx=None, yy=None, zz=None, **kwargs):
        super(NodeResult, self).__init__(**kwargs)
        self._registration = node
        self._title = title
        self._x = x
        self._y = y
        self._z = z
        self._xx = xx
        self._yy = yy
        self._zz = zz
        self._results_func = "find_node_by_key"

    @property
    def node(self):
        return self._registration

    @property
    def components(self):
        return {self._title + component: getattr(self, component) for component in ["x", "y", "z", "xx", "yy", "zz"]}

    @property
    def vector(self):
        return Vector(self._x, self._y, self._z)

    @property
    def vector_rotation(self):
        return Vector(self._xx, self._yy, self._zz)

    @property
    def magnitude(self):
        return self.vector.length


class DisplacementResult(NodeResult):
    """DisplacementResult object.

    Notes
    -----
    DisplacementResults are registered to a :class:`compas_fea2.model.Node`
    """

    def __init__(self, node, x=0.0, y=0.0, z=0.0, xx=0.0, yy=0.0, zz=0.0, **kwargs):
        super(DisplacementResult, self).__init__(node, "u", x, y, z, xx, yy, zz, **kwargs)


class AccelerationResult(NodeResult):
    """AccelerationResult object.

    Notes
    -----
    DisplacementResults are registered to a :class:`compas_fea2.model.Node`
    """

    def __init__(self, node, x=0.0, y=0.0, z=0.0, xx=0.0, yy=0.0, zz=0.0, **kwargs):
        super(AccelerationResult, self).__init__(node, "a", x, y, z, xx, yy, zz, **kwargs)


class VelocityResult(NodeResult):
    """AccelerationResult object.

    Notes
    -----
    DisplacementResults are registered to a :class:`compas_fea2.model.Node`
    """

    def __init__(self, node, x=0.0, y=0.0, z=0.0, xx=0.0, yy=0.0, zz=0.0, **kwargs):
        super(VelocityResult, self).__init__(node, "v", x, y, z, xx, yy, zz, **kwargs)


class ReactionResult(NodeResult):
    """DisplacementResult object.

    Parameters
    ----------
    node : :class:`compas_fea2.model.Node`
        The location of the result.
    rf1 : float
        The x component of the reaction vector.
    rf2 : float
        The y component of the reaction vector.
    rf3 : float
        The z component of the reaction vector.

    Attributes
    ----------
    location : :class:`compas_fea2.model.Node` `
        The location of the result.
    node : :class:`compas_fea2.model.Node`
        The location of the result.
    components : dict
        A dictionary with {"component name": component value} for each component of the result.
    invariants : dict
        A dictionary with {"invariant name": invariant value} for each invariant of the result.
    rf1 : float
        The x component of the reaction vector.
    rf2 : float
        The y component of the reaction vector.
    rf3 : float
        The z component of the reaction vector.
    vector : :class:`compas.geometry.Vector`
        The displacement vector.
    magnitude : float
        The absolute value of the displacement.

    Notes
    -----
    ReactionResults are registered to a :class:`compas_fea2.model.Node`
    """

    def __init__(self, node, x, y, z, xx, yy, zz, **kwargs):
        super(ReactionResult, self).__init__(node, "rf", x, y, z, xx, yy, zz, **kwargs)


# ---------------------------------------------------------------------------------------------
# Element Results
# ---------------------------------------------------------------------------------------------


class ElementResult(Result):
    """Element1DResult object."""

    def __init__(self, element, **kwargs):
        super(ElementResult, self).__init__(**kwargs)
        self._registration = element
        self._results_func = "find_element_by_key"

    @property
    def element(self):
        return self._registration


class SectionForcesResult(ElementResult):
    """SectionForcesResult object.

    Parameters
    ----------
    element : :class:`compas_fea2.model.Element`
        The element to which the result is associated.
    Fx_1, Fy_1, Fz_1 : float
        Components of the force vector at the first end of the element.
    Mx_1, My_1, Mz_1 : float
        Components of the moment vector at the first end of the element.
    Fx_2, Fy_2, Fz_2 : float
        Components of the force vector at the second end of the element.
    Mx_2, My_2, Mz_2 : float
        Components of the moment vector at the second end of the element.

    Attributes
    ----------
    end_1 : :class:`compas_fea2.model.Node`
        The first end node of the element.
    end_2 : :class:`compas_fea2.model.Node`
        The second end node of the element.
    force_vector_1 : :class:`compas.geometry.Vector`
        The force vector at the first end of the element.
    moment_vector_1 : :class:`compas.geometry.Vector`
        The moment vector at the first end of the element.
    force_vector_2 : :class:`compas.geometry.Vector`
        The force vector at the second end of the element.
    moment_vector_2 : :class:`compas.geometry.Vector`
        The moment vector at the second end of the element.
    forces : dict
        Dictionary containing force vectors for both ends of the element.
    moments : dict
        Dictionary containing moment vectors for both ends of the element.
    net_force : :class:`compas.geometry.Vector`
        The net force vector across the element.
    net_moment : :class:`compas.geometry.Vector`
        The net moment vector across the element.

    Notes
    -----
    SectionForcesResults are registered to a :class:`compas_fea2.model._Element`.

    Methods
    -------
    to_dict()
        Export the section forces and moments to a dictionary.
    """

    def __init__(self, element, Fx_1, Fy_1, Fz_1, Mx_1, My_1, Mz_1, Fx_2, Fy_2, Fz_2, Mx_2, My_2, Mz_2, **kwargs):
        super(SectionForcesResult, self).__init__(element, **kwargs)

        self._end_1 = element.nodes[0]
        self._force_vector_1 = Vector(Fx_1, Fy_1, Fz_1)
        self._moment_vector_1 = Vector(Mx_1, My_1, Mz_1)

        self._end_2 = element.nodes[1]
        self._force_vector_2 = Vector(Fx_2, Fy_2, Fz_2)
        self._moment_vector_2 = Vector(Mx_2, My_2, Mz_2)

    def __repr__(self):
        """String representation of the SectionForcesResult."""
        return (
            f"SectionForcesResult(\n"
            f"  Element: {self.element},\n"
            f"  End 1 Force: {self.force_vector_1}, Moment: {self.moment_vector_1},\n"
            f"  End 2 Force: {self.force_vector_2}, Moment: {self.moment_vector_2},\n"
            f"  Net Force: {self.net_force}, Net Moment: {self.net_moment}\n"
            f")"
        )

    @property
    def end_1(self):
        """Returns the first end node of the element."""
        return self._end_1

    @property
    def end_2(self):
        """Returns the second end node of the element."""
        return self._end_2

    @property
    def force_vector_1(self):
        """Returns the force vector at the first end of the element."""
        return self._force_vector_1

    @property
    def moment_vector_1(self):
        """Returns the moment vector at the first end of the element."""
        return self._moment_vector_1

    @property
    def force_vector_2(self):
        """Returns the force vector at the second end of the element."""
        return self._force_vector_2

    @property
    def moment_vector_2(self):
        """Returns the moment vector at the second end of the element."""
        return self._moment_vector_2

    @property
    def forces(self):
        """Returns a dictionary of force vectors for both ends."""
        return {
            self.end_1: self.force_vector_1,
            self.end_2: self.force_vector_2,
        }

    @property
    def moments(self):
        """Returns a dictionary of moment vectors for both ends."""
        return {
            self.end_1: self.moment_vector_1,
            self.end_2: self.moment_vector_2,
        }

    @property
    def net_force(self):
        """Returns the net force vector across the element."""
        return self.force_vector_2 + self.force_vector_1

    @property
    def net_moment(self):
        """Returns the net moment vector across the element."""
        return self.moment_vector_2 + self.moment_vector_1

    def plot_stress_distribution(self, end="end_1", nx=100, ny=100):
        """
        Plot the axial stress distribution along the element.

        Parameters
        ----------
        location : str, optional
            The end of the element ('end_1' or 'end_2'). Default is 'end_1'.
        nx : int, optional
            Number of points to plot along the element. Default is 100.
        """
        force_vector = self.force_vector_1 if end == "end_1" else self.force_vector_2
        moment_vector = self.moment_vector_1 if end == "end_1" else self.moment_vector_2
        N = force_vector.z  # Axial force
        Vx = force_vector.x  # Shear force in x-direction
        Vy = force_vector.y  # Shear force in y-direction
        Mx = moment_vector.x  # Bending moment about x-axis
        My = moment_vector.y  # Bending moment about y-axis

        self.element.section.plot_stress_distribution(N, Vx, Vy, Mx, My, nx=nx, ny=ny)

    def sectional_analysis_summary(self, end="end_1"):
        """
        Generate a summary of sectional analysis for the specified end.

        Parameters
        ----------
        location : str, optional
            The end of the element ('end_1' or 'end_2'). Default is 'end_1'.

        Returns
        -------
        dict
            A dictionary summarizing the results of the sectional analysis.
        """
        return None
        return {
            "normal_stress": self.compute_normal_stress(end),
            "shear_stress": self.compute_shear_stress(end),
            "utilization": self.compute_utilization(end),
            "interaction_check": self.check_interaction(end),
        }

    def to_dict(self):
        """Export the section forces and moments to a dictionary."""
        return {
            "element": self.element,
            "end_1": {
                "force": self.force_vector_1,
                "moment": self.moment_vector_1,
            },
            "end_2": {
                "force": self.force_vector_2,
                "moment": self.moment_vector_2,
            },
            "net_force": self.net_force,
            "net_moment": self.net_moment,
        }

    def to_json(self, file_path):
        """Export the result to a JSON file.

        Parameters
        ----------
        file_path : str
            Path to the JSON file.
        """
        import json

        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=4)

    def to_csv(self, file_path):
        """Export the result to a CSV file.

        Parameters
        ----------
        file_path : str
            Path to the CSV file.
        """
        import csv

        with open(file_path, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["End", "Fx", "Fy", "Fz", "Mx", "My", "Mz"])
            writer.writerow(["End 1", self.force_vector_1.x, self.force_vector_1.y, self.force_vector_1.z, self.moment_vector_1.x, self.moment_vector_1.y, self.moment_vector_1.z])
            writer.writerow(["End 2", self.force_vector_2.x, self.force_vector_2.y, self.force_vector_2.z, self.moment_vector_2.x, self.moment_vector_2.y, self.moment_vector_2.z])


class StressResult(ElementResult):
    """StressResult object.

    Parameters
    ----------
    element : :class:`compas_fea2.model._Element`
        The location of the result.
    s11 : float
        The 11 component of the stress tensor in local coordinates.
    s12 : float
        The 12 component of the stress tensor in local coordinates.
    s13 : float
        The 13 component of the stress tensor in local coordinates.
    s22 : float
        The 22 component of the stress tensor in local coordinates.
    s23 : float
        The 23 component of the stress tensor in local coordinates.
    s33 : float
        The 33 component of the stress tensor in local coordinates.


    Attributes
    ----------
    element : :class:`compas_fea2.model._Element`
        The location of the result.
    s11 : float
        The 11 component of the stress tensor in local coordinates.
    s12 : float
        The 12 component of the stress tensor in local coordinates.
    s13 : float
        The 13 component of the stress tensor in local coordinates.
    s22 : float
        The 22 component of the stress tensor in local coordinates.
    s23 : float
        The 23 component of the stress tensor in local coordinates.
    s33 : float
        The 33 component of the stress tensor in local coordinates.
    local_stress : numpy array
        The stress tensor in local coordinates.
    global_stress : numpy array
        The stress tensor in global coordinates.
    global_strains : numpy array
        The strsin tensor in global coordinates.
    I1 : numpy array
        First stress invariant.
    I2 : numpy array
        Second stress invariant.
    I3 : numpy array
        Second stress invariant.
    J2 : numpy array
        Second stress invariant of the deviatoric part.
    J3 : numpy array
        Second stress invariant of the deviatoric part.
    hydrostatic_stress : numpy array
        Hydrostatic stress.
    deviatoric_stress : numpy array
        Deviatoric stress.
    octahedral_stress : numpy array
        Octahedral normal and shear stresses
    principal_stresses_values : list(float)
        The eigenvalues sorted from low to high.
    principal_stresses_vectors : list(:class:`compas.geometry.Vector`)
        The eigenvectors sorted as according to the eigenvalues.
    principal_stresses : zip obj
        Iterator providing the eigenvalue/eigenvector pair.
    smin : float
        Minimum principal stress.
    smid : float
        Middle principal stress.
    smax : float
        Maximum principal stress.
    von_mises_stress : float
        Von Mises stress.

    Notes
    -----
    StressResults are registered to a :class:`compas_fea2.model._Element
    """

    def __init__(self, element, *, s11, s12, s13, s22, s23, s33, **kwargs):
        super(StressResult, self).__init__(element, **kwargs)
        self._local_stress = np.array([[s11, s12, s13], [s12, s22, s23], [s13, s23, s33]])
        self._global_stress = self.transform_stress_tensor(self._local_stress, Frame.worldXY())
        self._components = {f"S{i+1}{j+1}": self._local_stress[i][j] for j in range(len(self._local_stress[0])) for i in range(len(self._local_stress))}

    @property
    def local_stress(self):
        # In local coordinates
        return self._local_stress

    @property
    def global_stress(self):
        # In global coordinates
        return self._global_stress

    @property
    def global_strain(self):
        if not isinstance(self.location.section.material, ElasticIsotropic):
            raise NotImplementedError("This function is currently only available for Elastic Isotropic materials")

        # For brevity
        s = self.global_stress
        v = self.element.section.material.v
        E = self.element.section.material.E

        dim = len(s)
        strain_tensor = np.zeros((dim, dim))

        # Calculate the strain tensor using Hooke's Law
        for i in range(dim):
            for j in range(dim):
                if i == j:  # Normal components
                    strain_tensor[i, j] = (s[i, j] - v * (self.I1 - s[i, j])) / E
                else:  # Shear components
                    strain_tensor[i, j] = (1 + v) * s[i, j] / E

        return strain_tensor

    @property
    # First invariant
    def I1(self):
        return np.trace(self.global_stress)

    @property
    # Second invariant
    def I2(self):
        return 0.5 * (self.I1**2 - np.trace(np.dot(self.global_stress, self.global_stress)))

    @property
    # Third invariant
    def I3(self):
        return np.linalg.det(self.global_stress)

    @property
    # Second invariant of the deviatoric stress tensor: J2
    def J2(self):
        return 0.5 * np.trace(np.dot(self.deviatoric_stress, self.deviatoric_stress))

    @property
    # Third invariant of the deviatoric stress tensor: J3
    def J3(self):
        return np.linalg.det(self.deviatoric_stress)

    @property
    def hydrostatic_stress(self):
        return self.I1 / len(self.global_stress)

    @property
    def deviatoric_stress(self):
        return self.global_stress - np.eye(len(self.global_stress)) * self.hydrostatic_stress

    @property
    # Octahedral normal and shear stresses
    def octahedral_stresses(self):
        sigma_oct = self.I1 / 3
        tau_oct = np.sqrt(2 * self.J2 / 3)
        return sigma_oct, tau_oct

    @property
    def principal_stresses_values(self):
        eigenvalues = np.linalg.eigvalsh(self.global_stress)
        sorted_indices = np.argsort(eigenvalues)
        return eigenvalues[sorted_indices]

    @property
    def principal_stresses(self):
        return zip(self.principal_stresses_values, self.principal_stresses_vectors)

    @property
    def smax(self):
        return max(self.principal_stresses_values)

    @property
    def smin(self):
        return min(self.principal_stresses_values)

    @property
    def smid(self):
        if len(self.principal_stresses_values) == 3:
            return [x for x in self.principal_stresses_values if x != self.smin and x != self.smax]
        else:
            return None

    @property
    def principal_stresses_vectors(self):
        eigenvalues, eigenvectors = np.linalg.eig(self.global_stress)
        # Sort the eigenvalues/vectors from low to high
        sorted_indices = np.argsort(eigenvalues)
        eigenvectors = eigenvectors[:, sorted_indices]
        eigenvalues = eigenvalues[sorted_indices]
        return [Vector(*eigenvectors[:, i].tolist()) * abs(eigenvalues[i]) for i in range(len(eigenvalues))]

    @property
    def von_mises_stress(self):
        return np.sqrt(self.J2 * 3)

    @property
    def tresca_stress(self):
        return max(abs(self.principal_stresses_values - np.roll(self.principal_stresses_values, -1)))

    @property
    def safety_factor_max(self, allowable_stress):
        # Simple safety factor analysis based on maximum principal stress
        return abs(allowable_stress / self.smax) if self.smax != 0 else 1

    @property
    def safety_factor_min(self, allowable_stress):
        # Simple safety factor analysis based on maximum principal stress
        return abs(allowable_stress / self.smin) if self.smin != 0 else 1

    @property
    def strain_energy_density(self):
        """
        Calculates the strain energy density for linear elastic and isotropic materials.
        :return: The strain energy density value.
        """
        if not isinstance(self.location.section.material, ElasticIsotropic):
            raise NotImplementedError("Strain energy density calculation is currently only available for Elastic Isotropic materials")

        # Calculate strain energy density
        s = self.global_stress  # Stress tensor
        e = self.global_strain  # Strain tensor

        # For isotropic materials, using the formula: U = 1/2 * stress : strain
        U = 0.5 * np.tensile(s, e)

        return U

    def transform_stress_tensor(self, tensor, new_frame):
        """
        Transforms the stress tensor to a new frame using the provided 3x3 rotation matrix.
        This function works for both 2D and 3D stress tensors.

        Parameters:
        -----------
        new_frame : `class`:"compas.geometry.Frame"
            The new refernce Frame

        Returns:
        numpy array
            Transformed stress tensor as a numpy array of the same dimension as the input.
        """

        R = Transformation.from_change_of_basis(self.element.frame, new_frame)
        R_matrix = np.array(R.matrix)[:3, :3]

        return R_matrix @ tensor @ R_matrix.T

    def stress_along_direction(self, direction):
        """
        Computes the stress along a given direction.
        :param direction: A list or array representing the direction vector.
        :return: The normal stress along the given direction.
        """
        unit_direction = np.array(direction) / np.linalg.norm(direction)
        return unit_direction.T @ self.global_stress @ unit_direction

    def compute_mohr_circles_3d(self):
        """
        Computes the centers and radii of the three Mohr's circles for a 3D stress state.
        :return: A list of tuples, each containing the center and radius of a Mohr's circle.
        """
        # Ensure we're dealing with a 3D stress state
        if self.global_stress.shape != (3, 3):
            raise ValueError("Mohr's circles computation requires a 3D stress state.")

        # Calculate the centers and radii of the Mohr's circles
        circles = []
        for i in range(3):
            sigma1 = self.principal_stresses_values[i]
            for j in range(i + 1, 3):
                sigma2 = self.principal_stresses_values[j]
                center = (sigma1 + sigma2) / 2
                radius = abs(sigma1 - sigma2) / 2
                circles.append((center, radius))

        return circles

    def compute_mohr_circle_2d(self):
        # Ensure the stress tensor is 2D
        if self.global_stress.shape != (2, 2):
            raise ValueError("The stress tensor must be 2D for Mohr's Circle.")

        # Calculate the center and radius of the Mohr's Circle
        sigma_x, sigma_y, tau_xy = self.global_stress[0, 0], self.global_stress[1, 1], self.global_stress[0, 1]
        center = (sigma_x + sigma_y) / 2
        radius = np.sqrt(((sigma_x - sigma_y) / 2) ** 2 + tau_xy**2)

        # Create the circle
        theta = np.linspace(0, 2 * np.pi, 100)
        x = center + radius * np.cos(theta)
        y = radius * np.sin(theta)
        return x, y, center, radius, sigma_x, sigma_y, tau_xy

    def draw_mohr_circle_2d(self):
        """
        Draws the three Mohr's circles for a 3D stress state.
        """
        x, y, center, radius, sigma_x, sigma_y, tau_xy = self.compute_mohr_circle_2d()
        # Plotting
        plt.figure(figsize=(8, 8))
        plt.plot(x, y, label="Mohr's Circle")

        # Plotting the principal stresses
        plt.scatter([center + radius, center - radius], [0, 0], color="red")
        plt.text(center + radius, 0, "$\\sigma_1$")
        plt.text(center - radius, 0, "$\\sigma_2$")

        # Plotting the original stresses
        plt.scatter([sigma_x, sigma_y], [tau_xy, -tau_xy], color="blue")
        plt.text(sigma_x, tau_xy, "($\\sigma_x$, $\\tau$)")
        plt.text(sigma_y, -tau_xy, "($\\sigma_y$, $-\\tau$)")

        # Axes and grid
        plt.axhline(0, color="black", linewidth=0.5)
        plt.axvline(center, color="grey", linestyle="--", linewidth=0.5)
        plt.grid(color="gray", linestyle="--", linewidth=0.5)
        plt.xlabel("Normal Stress ($\\sigma$)")
        plt.ylabel("Shear Stress ($\\tau$)")
        plt.title("Mohr's Circle")
        plt.axis("equal")
        plt.legend()
        plt.show()

    def draw_mohr_circles_3d(self):
        """
        Draws the three Mohr's circles for a 3D stress state.
        """
        circles = self.compute_mohrs_circles_3d()

        # Create a figure and axis for the plot
        fig, ax = plt.subplots(figsize=(8, 8))

        # Plot each circle
        for i, (center, radius) in enumerate(circles, 1):
            circle = plt.Circle((center, 0), radius, fill=False, label=f"Circle {i}")
            ax.add_artist(circle)

            # Plot the center of the circle
            plt.scatter(center, 0, color="red")
            plt.text(center, 0, f"C{i}")

        # Set the limits and labels of the plot
        max_radius = max(radius for _, radius in circles)
        max_center = max(center for center, _ in circles)
        min_center = min(center for center, _ in circles)
        plt.xlim(min_center - max_radius - 10, max_center + max_radius + 10)
        plt.ylim(-max_radius - 10, max_radius + 10)
        plt.axhline(0, color="black", linewidth=0.5)
        plt.axvline(0, color="black", linewidth=0.5)
        plt.xlabel("Normal Stress ($\\sigma$)")
        plt.ylabel("Shear Stress ($\\tau$)")
        plt.title("Mohr's Circles for 3D Stress State")
        plt.legend()
        plt.grid(True)
        plt.axis("equal")

        # Show the plot
        plt.show()

    # =========================================================================
    #                               Yield Criteria
    # =========================================================================
    def mohr_coulomb(self, c, phi):
        return self.smax - self.smin - 2 * c * np.cos(phi) / (1 - np.sin(phi))

    # Drucker-Prager Criterion
    def drucker_prager(self, c, phi):
        # Convert angle from degrees to radians
        phi_radians = np.radians(phi)
        # Calculate material constants alpha and k from cohesion and internal friction angle
        alpha = np.sqrt(3) * (2 * np.sin(phi_radians)) / (3 - np.sin(phi_radians))
        k = np.sqrt(3) * c * (3 - np.sin(phi_radians)) / (3 * np.sin(phi_radians))
        return alpha * self.I1 + np.sqrt(self.J2) - k

    # Rankine Criterion
    def rankine(self, tensile_strength, compressive_strength):
        return max(self.smax - tensile_strength, abs(self.smin) - compressive_strength)

    # Bresler-Pister Criterion (simplified version)
    def bresler_pister(self, tensile_strength, compressive_strength):
        return max(self.smax / tensile_strength, abs(self.smin) / compressive_strength)

    # Modified Mohr Criterion (simplified version)
    def modified_mohr(self, tensile_strength):
        return (self.smax - self.smin) / 2 - tensile_strength

    # Griffith Criterion
    def griffith(self, fracture_toughness):
        return self.smax**2 / (2 * fracture_toughness)

    # Lade-Duncan Criterion (simplified version)
    def lade_duncan(self, c):
        return self.I1 - 3 * c

    def thermal_stress_analysis(self, temperature_change):
        # Simple thermal stress analysis for isotropic material
        if not isinstance(self.location.section.material, ElasticIsotropic):
            raise NotImplementedError("This function is only available for Elastic Isotropic materials")
        # Delta_sigma = E * alpha * Delta_T
        return self.location.section.material.E * self.location.section.material.expansion * temperature_change


class MembraneStressResult(StressResult):
    def __init__(self, element, s11, s12, s22, **kwargs):
        super(MembraneStressResult, self).__init__(element, s11=s11, s12=s12, s13=0, s22=s22, s23=0, s33=0, **kwargs)
        self._title = "s2d"


class ShellStressResult(Result):
    """
    ShellStressResult object.

    Parameters
    ----------
    element : :class:`compas_fea2.model._Element`
        The location of the result.
    s11 : float
        The 11 component of the stress tensor in local coordinates (in-plane axial).
    s22 : float
        The 22 component of the stress tensor in local coordinates (in-plane axial).
    s12 : float
        The 12 component of the stress tensor in local coordinates (in-plane shear).

    sb11 : float
        The 11 component of the stress tensor in local coordinates due to bending on the top face.
    sb22 : float
        The 22 component of the stress tensor in local coordinates due to bending on the top face.
    t12 : float

    """

    def __init__(self, element, s11, s22, s12, sb11, sb22, sb12, tq1, tq2, **kwargs):
        super(ShellStressResult, self).__init__(**kwargs)
        self._title = "s2d"
        self._registration = element
        self._components = {}
        self._invariants = {}
        self._mid_plane_stress_result = MembraneStressResult(element, s11=s11, s12=s12, s22=s22)
        self._top_plane_stress_result = MembraneStressResult(element, s11=s11 + sb11, s12=s12, s22=s22 + sb22)
        self._bottom_plane_stress_result = MembraneStressResult(element, s11=s11 - sb11, s12=s12, s22=s22 - sb22)

    @property
    def mid_plane_stress_result(self):
        return self._mid_plane_stress_result

    @property
    def top_plane_stress_result(self):
        return self._top_plane_stress_result

    @property
    def bottom_plane_stress_result(self):
        return self._bottom_plane_stress_result

    def plane_results(self, plane):
        results = {
            "mid": self.mid_plane_stress_result,
            "top": self.top_plane_stress_result,
            "bottom": self.bottom_plane_stress_result,
        }
        return results[plane]


# TODO: double inheritance StressResult and Element3DResult
class SolidStressResult(StressResult):
    def __init__(self, element, s11, s12, s13, s22, s23, s33, **kwargs):
        super(SolidStressResult, self).__init__(element=element, s11=s11, s12=s12, s13=s13, s22=s22, s23=s23, s33=s33, **kwargs)
        self._title = "s3d"


class StrainResult(Result):
    pass


class EnergyResult(Result):
    pass
