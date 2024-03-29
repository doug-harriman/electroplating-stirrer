# gcode_doc.py
#
# Copyright (C) 2021  Doug Harriman
#
#
# Python tools for generating G-Code for laser engravers, specifically
# Laser tuning parameter test plots.
#

# This module contains code for generating GCode for characters that
# was forked from:
# https://github.com/Yoyolick/TextToGcode

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# TODO: Support reading in a G-code file and making that a generic shape.
# TODO: See if Doc, Layout and Shape can come from the same base class.

# TODO: Convert to using SciPy for spatial operations.
#       https://docs.scipy.org/doc/scipy/reference/spatial.html

# SymPy geometry: https://docs.sympy.org/latest/modules/geometry/index.html
# SciKit geometry: https://scikit-geometry.github.io/scikit-geometry/reference.html#two-dimensional-primitives
# 2D Gaming library: https://pythonhosted.org/planar/


import numpy as np
import math
from typing import Any, Union


class Layout:
    """
    Layout base class for GCode documents.
    Simplest implementation.  Objects stored in a list.
    """

    # References
    _parent = None
    _children = None

    # Padding for children
    _padding_width = 0
    _padding_height = 0

    # Layout origin. Defined to be lower left corner always.
    _x = None
    _y = None
    _z = None

    # Comments for cell
    _header = None
    _footer = None

    def __init__(self):
        self._children = []

    @property
    def x(self) -> Union[None, float]:
        """
        X coordinate in document.
        """
        return self._x

    @x.setter
    def x(self, x: float = 0.0):
        """ """
        self._x = x

    @property
    def y(self) -> Union[None, float]:
        """
        Y coordinate in document.
        """
        return self._y

    @y.setter
    def y(self, y: float = 0.0):
        self._y = y

    @property
    def z(self) -> Union[None, float]:
        """
        Z coordinate in document.
        """
        return self._z

    @z.setter
    def z(self, z: float = 0.0):
        """
        Sets layout Z coordinate (lower).
        """
        self._z = z

    @property
    def padding_width(self) -> float:
        """
        Padding distance added to each side of any child object(s).
        """
        return self._padding_width

    @padding_width.setter
    def padding_width(self, value: float):
        self._padding_width = value

    @property
    def padding_height(self):
        """
        Padding distance added to top and bottom of any child object(s).
        """
        return self._padding_height

    @padding_height.setter
    def padding_height(self, value: float):
        self._padding_height = value

    @property
    def parent(self):
        """
        Parent object.
        """
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value

    @property
    def header(self) -> Union[None, str]:
        """
        Header comment to be emmitted at start of G-code gen for this layout.
        """
        return self._header

    @header.setter
    def header(self, value: str):
        self._header = value

    @property
    def footer(self) -> Union[None, str]:
        """
        Footer comment to be emmitted at end of G-code gen for this layout.
        """
        return self._footer

    @footer.setter
    def footer(self, value: str):
        self._footer = value

    def AddChild(self, child):
        """
        Abstract method, add child layout or shape to this layout.

        Raises
        ------
        Exception
            This is an abstract method and will raise an error if called.
        """

        self._children.append(child)

        # Add fill lines if needed.
        if child.is_filled:
            child.fill(self.parent)

    def Size(self) -> tuple:
        """
        Size of layout object including padding.

        Raises
        ------
        Exception
            This is an abstract method and will raise an error if called.
        """
        # Emulating a pure virtual method that should have a concrete implementation.
        raise Exception(f"No Size method defined for class: {type(self)}")

    def GCode(self, doc):
        """
        Generate G-Code for layout object.

        Raises
        ------
        Exception
            This is an abstract method and will raise an error if called.
        """

        for child in self._children:
            child.GCode(doc)


class Layout2dOptimizer(Layout):
    """
    Layout which optimizes G-Code generation for minimum
    travel distance by schedling G-Code objects based on proximity to
    the last operation point.
    """

    def GCode(self, doc):
        """
        Generate optimized G-Code for child object.
        """

        # Deep copy the list of children
        children = self._children.copy()

        # Assume that the tool starts at the origin.
        xy = np.array([0, 0])

        def child_distance(child):
            """
            Returns distance from child to current position.
            """
            return child.distance(xy)

        # Process list of children, looking for closest to current position.
        # As each child is processed, pop it from the list.
        # TODO: Potential optimization: Look for list of children that are within
        #       a standard part pitch distance of each other.  Process as subgraphs.
        # TODO: Look for angle and distance.  Identify ~lines of objects and start at an end.
        while len(children) > 0:
            # Find closest child
            dist = list(map(child_distance, children))
            dist = np.array(dist)
            idx = np.argmin(dist)

            # Optimize & generate the child.
            child = children.pop(idx)
            child.startpoint_set(xy)
            child.GCode(doc)

            # Find the endpoint of the child.
            if child.is_closed:
                xy = child.points[0, :]
            else:
                xy = child.points[-1, :]


class LayoutTravelingSalesment(Layout):
    """
    Layout which optimizes G-Code generation for minimum
    travel distance solving the Traveling Salesman Problem
    between the centers of the child geometry objects.
    """

    def GCode(self, doc):
        """
        Generate optimized G-Code for child object.
        """
        import networkx as nx
        import networkx.algorithms.approximation as nx_app

        # Copy list elements into the NetworkX graph
        G = nx.Graph()
        for i, child in enumerate(self._children):
            G.add_node(i, pos=(child.x, child.y))

        pos = nx.get_node_attributes(G, "pos")

        # Calculating the distances between the nodes as edge's weight.
        for i in range(len(pos)):
            for j in range(i + 1, len(pos)):
                dist = math.hypot(pos[i][0] - pos[j][0], pos[i][1] - pos[j][1])
                dist = dist**2
                G.add_edge(i, j, weight=dist)

        # Assume that the tool starts at the origin.
        xy = np.array([0, 0])

        def child_distance(child):
            """
            Returns distance from child to current position.
            """
            return child.distance(xy)

        # Find closest child
        dist = list(map(child_distance, self._children))
        dist = np.array(dist)
        idx = np.argmin(dist)

        # Per: https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.approximation.traveling_salesman.traveling_salesman_problem.html
        tsp = nx_app.greedy_tsp
        node_list = tsp(G, weight="weight", source=idx)

        # tsp = nx_app.threshold_accepting_tsp
        # node_list = tsp(
        #     G,
        #     weight="weight",
        #     source=idx,
        #     init_cycle="greedy",
        #     max_iterations=1000,
        #     threshold=0.1,
        # )

        # tsp = nx_app.simulated_annealing_tsp
        # node_list = tsp(
        #     G,
        #     weight="weight",
        #     source=idx,
        #     init_cycle="greedy",
        #     temp=500,
        #     max_iterations=1000,
        # )

        node_list = list(node_list)[:-1]

        for idx in node_list:
            child = self._children[idx]
            child.GCode(doc)


class CellLayout(Layout):
    """
    Cell layout object.
    Contains a single child and adds padding.
    """

    def __init__(self):
        super().__init__()

        raise NotImplementedError("Not ported to update point list implementation.")

    def AddChild(self, child):
        """
        Set Cell child object.
        If padding is >0, Cell size will be child size plus padding.
        Will overwrite existing child object.

        Parameters
        ----------
        child: Layout, Shape
            Child object to store.
        """
        self._children = child

    def Size(self) -> tuple:
        """
        Return size of cell layout object.

        Returns
        -------
        size: tuple
            Object size: (width, height)
        """
        sz_w = 2 * self.padding_width
        sz_h = 2 * self.padding_height
        if self._children is not None:
            sz_child = self._children.Size()
            sz_w += sz_child[0]
            sz_h += sz_child[1]

        return (sz_w, sz_h)

    def GCode(self, doc):
        """
        Generates G-Code for Cell and contents.
        Cell child is called recusively.

        Parameters:
        doc: Doc
            Document into which to inject generated G-Code.
        """

        # Add header comment
        if self.header is not None:
            doc.AddLine(f"({self.header})")

        # Set child position
        self._children.x = self.x + self.padding_width
        self._children.y = self.y + self.padding_height

        # Child GCode
        if self._children is not None:
            self._children.GCode(doc)
        else:
            doc.AddLine("( *Empty Cell* )")

        # Generate GCode
        if self.footer is not None:
            doc.AddLine(f"({self.footer})")


class GridLayout(Layout):
    """
    Rectangular Grid layout object.
    Note that padding is applied to outside of grid.
    """

    # Grid size
    _rows = None
    _cols = None
    _grid = None

    # Sizing info
    _widths = None
    _heights = None

    # Cell child padding.
    _cell_padding_width = 0.0
    _cell_padding_height = 0.0

    def __init__(self, rows: int = 2, columns: int = 2):
        super().__init__()

        if rows < 1:
            raise ValueError("Must have at least 1 row.")
        if columns < 1:
            raise ValueError("Must have at least 1 column.")

        self._rows = rows
        self._cols = columns

        # Intialize grid info
        self._grid = [[0] * columns for _ in range(rows)]
        self._widths = np.zeros((rows, columns))
        self._heights = np.zeros((rows, columns))

        raise NotImplementedError("Not ported to update point list implementation.")

    @property
    def cell_padding_width(self) -> float:
        """
        Cell padding distance added to each side of any child object(s).
        """
        return self._cell_padding_width

    @cell_padding_width.setter
    def cell_padding_width(self, value: float):
        self._cell_padding_width = value

    @property
    def cell_padding_height(self):
        """
        Cell padding distance added to top and bottom of any child object(s).
        """
        return self._cell_padding_height

    @cell_padding_height.setter
    def cell_padding_height(self, value: float):
        self._cell_padding_height = value

    @property
    def rows(self) -> Union[None, int]:
        """
        Rectangular grid row count.
        """
        return self._rows

    @property
    def columns(self) -> Union[None, int]:
        """
        Rectangular grid column count.
        """
        return self._columns

    def AddChild(self, child, row: int = 0, column: int = 0):
        """
        Adds child to cell at specified row and column.
        """
        if row < 0:
            raise ValueError("Row must be >= 0")
        if column < 0:
            raise ValueError("Column must be >= 0")

        self._grid[row][column] = child

    def AddChildCell(self, child, row: int = 0, column: int = 0):
        """
        Adds child, wrapping with a cell layout object.
        This is used to apply the cell padding to the added object.
        """
        # Create cell
        cell = CellLayout()

        # Set cell padding
        cell.padding_width = self._cell_padding_width
        cell.padding_height = self._cell_padding_height

        # Add child to cell.
        cell.AddChild(child)

        # Add cell to this layout
        self.AddChild(cell, row, column)

    def Size(self) -> tuple:
        """
        Return size of rectangular grid layout object.
        """
        # Process rows and columns, finding max width for each col, max height for each row.
        for i, row in enumerate(self._grid):
            for j, col in enumerate(row):
                # Deal with empty cells
                if isinstance(col, int):
                    self._widths[i, j] = 0
                    self._heights[i, j] = 0
                else:
                    # Grid cell size.
                    # Note that if they added a cell, this will include cell padding.
                    sz = col.Size()
                    self._widths[i, j] = sz[0]
                    self._heights[i, j] = sz[1]

        # Sum for overall grid size
        sz_width = np.amax(self._widths, axis=0).sum()
        sz_height = np.amax(self._heights, axis=1).sum()

        # Pad
        sz_width += self._padding_width
        sz_height += self._padding_height

        return (sz_width, sz_height)

    def GCode(self, doc):
        """
        Generate GCode for a rectangular grid layout.
        GCode is generated left to right, top to bottom.
        """
        # Add header comment
        if self.header is not None:
            doc.AddLine(f"({self.header})")

        # Make sure we have cell sizes.
        if not self._widths.any():
            self.Size()
        if not self._heights.any():
            self.Size()

        # Base offset of all objects
        x_base = self.x + self.padding_width
        y_base = self.y + self.padding_height

        # Column widths
        widths = np.amax(self._widths, axis=0)

        # Row heights
        heights = np.amax(self._heights, axis=1)

        # Process rows and columns, finding max width for each col, max height for each row.
        for i, row in enumerate(self._grid):
            for j, col in enumerate(row):
                # Index comment
                doc.AddLine(f"(Grid cell {i},{j} )")

                if col == 0:
                    # Nothing in this grid cell.
                    # Note that and move on
                    doc.AddLine("( *Empty Cell* )")
                    continue

                # Cell lower left corner position.
                x_offset = x_base + widths[0:j].sum()
                y_offset = y_base + heights[i + 1 :].sum()

                # Center the object
                x_center_offset = (widths[j] - self._widths[i, j]) / 2
                y_center_offset = (heights[i] - self._heights[i, j]) / 2

                x_offset += x_center_offset
                y_offset += y_center_offset

                # Set its coordinates
                col.x = x_offset
                col.y = y_offset

                # Child GCode
                col.GCode(doc)

        # Generate GCode
        if self.footer is not None:
            doc.AddLine(f"({self.footer})")


class Doc:
    """
    Print job document.
    Contains document and device configuration information.
    """

    # Document origin. Defined to be lower left corner always.
    # Allows document to be placed in workspace.
    _x = 0
    _y = 0
    _z = 0

    # Laser Properties
    _laser_on = (
        "M4"
    )  # M3 for consant power regardless of speed.  M4 compensates for speed.
    _laser_off = "M5"  # Default for Grbl
    _laser_power = 0.0  # Percentage
    _laser_power_default = 80.0  # Percentage.  Default value for document.
    _device_laser_max = (
        1000.0
    )  # Maximum laser power value to use, in machine units.  Set for Sainsmart laser.

    # Device retraction
    _z_retract_enabled = False
    _z_retract_height = None

    # Positioning speed
    _speed_position = 3000.0  # We'll assume mm units.

    # Printing speed
    _speed_print = 500.0

    # End of line character
    _EOL = "\n"

    # Generated G-code
    _code = ""

    # Document comments
    _header = ""
    _footer = ""

    # Document layout
    _layout = None

    # Add job control
    _job_control = True

    def __init__(self, job_control: bool = True):
        # Set laser power to default.
        self._laser_power = self._laser_power_default

        # Set layout
        self.layout = Layout()

        # Filled objects
        self._fill_stepover = 0.1

        # Job control
        self._job_control = job_control

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, x: float = 0.0):
        """
        Sets document X coordinate (left).
        """
        self._x = x

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, y: float = 0.0):
        """
        Sets document Y coordinate (lower).
        """
        self._y = y

    @property
    def z(self) -> float:
        return self._z

    @z.setter
    def z(self, z: float = 0.0):
        """
        Sets document Z coordinate (lower).
        """
        self._z = z

    @property
    def z_retract_enabled(self) -> bool:
        """
        Enable/disable Z-retraction moves before positioning moves.
        """
        return self._z_retract_enabled

    @z_retract_enabled.setter
    def z_retract_enabled(self, value: bool):
        self._z_retract_enabled = value

    @property
    def z_retract_height(self) -> float:
        """
        Z retraction height for positioning moves.
        """
        return self._z_retract_height

    @z_retract_height.setter
    def z_retract_height(self, value: float):
        self._z_retract_height = value

    @property
    def speed_position(self) -> float:
        """
        Speed used for non-printing positioning moves.
        """
        return self._speed_position

    @speed_position.setter
    def speed_position(self, value: float):
        if value <= 0.0:
            raise ValueError("Speed must be positive.")

        self._speed_position = value

    @property
    def speed_print(self) -> float:
        """
        Document print speed.  Used as default for all shapes.
        """
        return self._speed_print

    @speed_print.setter
    def speed_print(self, value: float):
        if value <= 0.0:
            raise ValueError("Speed must be positive.")

        self._speed_print = value

    @property
    def EOL(self) -> str:
        """
        Document end of line character.
        Defaults to OS default.
        """
        return self._EOL

    @EOL.setter
    def EOL(self, value: str):
        self._EOL = value

    @property
    def code(self) -> str:
        """
        Document G-Code buffer.
        """
        return self._code

    @code.setter
    def code(self, value: str):
        self._code = value

    @property
    def laser_on(self) -> str:
        """
        Laser on G-code.
        Setter sets just the G-Code.  Valid value are M3 & M4.
        M3: Constant laser power.
        M4: Speed compensated laser power.

        Getter returns laser on G-code setting power to current power level.
        """

        code = self._laser_on
        code += f" S{(self.laser_power/100.0)*self._device_laser_max}"

        if self.laser_power < 100:
            code += f" (Laser on @ {self.laser_power:.2g}%)"
        else:
            code += f" (Laser on @ 100%)"

        return code

    @laser_on.setter
    def laser_on(self, value: str):
        value = value.upper()
        value = value.strip()
        if value not in ["M3", "M4"]:
            raise ValueError(f"Laser on G-code must be either M3 or M4, not: {value}")

        self._laser_on = value

    @property
    def laser_off(self) -> str:
        """
        Laser off G-Code.
        """
        return self._laser_off + "        (Laser off)"

    @laser_off.setter
    def laser_off(self, value: str):
        value = value.upper()
        value = value.strip()
        self._laser_off = value

    @property
    def laser_power(self) -> float:
        """
        Sets current laser power value.
        Value is a percentage of maximum device power on range [0,100].
        """

        return self._laser_power

    @laser_power.setter
    def laser_power(self, value: float):
        if value < 0 or value > 100:
            raise ValueError("Laser power must be on range [0,100]")

        self._laser_power = value

    @property
    def laser_power_default(self) -> float:
        """
        Sets laser power default value for document.
        Value is a percentage of maximum device power on range [0,100].
        """

        return self._laser_power_default

    @laser_power_default.setter
    def laser_power_default(self, value: float):
        if value < 0 or value > 100:
            raise ValueError("Laser power default must be on range [0,100]")

        self._laser_power_default = value

    @property
    def device_laser_max(self):
        """
        Device maximum laser power value in device units.
        Must be positive value.
        Laser power value will be scaled by this value for G-code generation.
        """
        return self._device_laser_max

    @device_laser_max.setter
    def device_laser_max(self, value: float):
        if value < 0:
            raise ValueError("Device laser maximum value must be positive.")

        self._device_laser_max = value

    @property
    def header(self) -> str:
        """
        Header comment to be emmitted at start of G-code gen for this layout.
        """
        return self._header

    @header.setter
    def header(self, value: str):
        self._header = value

    @property
    def footer(self) -> str:
        """
        Footer comment to be emmitted at end of G-code gen for this layout.
        """
        return self._footer

    @footer.setter
    def footer(self, value: str):
        self._footer = value

    @property
    def fill_stepover(self) -> float:
        """
        Fill stepover distance.
        """
        return self._fill_stepover

    @fill_stepover.setter
    def fill_stepover(self, value: float):
        if value <= 0:
            raise ValueError("Fill stepover must be positive.")
        self._fill_stepover = value

    @property
    def layout(self) -> Union[Layout, None]:
        """
        Document layout object.
        """
        return self._layout

    @layout.setter
    def layout(self, value: Layout):
        if not isinstance(value, Layout):
            raise ValueError("Layout must be a Layout object.")
        self._layout = value
        self._layout.parent = self

    def AddChild(self, child):
        """
        Adds child to document layout.
        """

        if self._layout is None:
            raise Exception("Document layout is not set.")

        if not isinstance(child, Shape):
            raise ValueError("Child must be a Shape object.")

        self._layout.AddChild(child)

    def AddLine(self, line: str = ""):
        """
        Adds a line to the document.
        """
        self.code += line + self.EOL

    def Save(self, filename):
        """
        Save generated GCode to file.
        """
        if len(self.code) == 0:
            # Generate GCode
            self.GCode()

        with open(filename, "w") as fp:
            fp.write(self.code)

    def Size(self) -> tuple:
        """
        Returns the overall document size.
        """
        return self._layout.Size()

    def GCode(self, filename: str = None):
        """
        Generate G-Code for document.
        Returns G-Code string and saves in document 'code' property.
        """

        self.code = ""

        # Header
        if len(self._header) > 0:
            header = self._header
            header = header.replace(self.EOL, ")" + self.EOL + "(")
            self.code += f"({header})" + self.EOL

        # Prerequisites
        if self._job_control:
            self.AddLine()
            self.AddLine("(Machine Setup)")
            self.AddLine(f"G90  (Absolute Position Mode)")
            # self.AddLine(f'G20  (Units = inches)')  # TODO: General Feature: Add property set units and select line.
            self.AddLine(f"G21  (Units = millimeters)")
            self.AddLine()

        # Contents
        self._layout.x = self.x
        self._layout.y = self.y
        self._layout.z = self.z
        self._layout.GCode(self)

        # Go home
        # self.AddLine('')
        # self.AddLine('(Return Home)')
        # self.AddLine(f'G0 F{self.speed_position:0.1f}')
        # if self.z_retract_enabled:
        #     self.AddLine(f'G0 Z{doc.z_retract_height:0.3f}')
        # self.AddLine(f'G0 X0 Y0')

        # End document
        if self._job_control:
            self.code += self.EOL
            self.code += "M2" + " (End Document)" + self.EOL

        if len(self._footer) > 0:
            self.code += f"({self._footer})" + self.EOL

        # Save the file if they gave us a file name.
        if filename is not None:
            self.Save(filename)


class Shape:
    """
    Abstract base class for drawing G-code shapes.
    All coordinate value are absolute.
    """

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        speed_print: float = None,
        laser_power=None,
    ):
        """
        Shape class initializer.
        If speed_print is not set, the document default value will be used.
        """

        self.x = x
        self.y = y
        self.z = z

        # Multi pass
        self._passes = 1
        self._stepdown = None

        # Comments
        self._header = None
        self._footer = None

        self._speed_print = speed_print
        self._laser_power = laser_power

        self._is_closed = False
        self._is_filled = False

    def GCode(self, doc: Doc) -> str:
        """
        Inserts a shape G-code preamble into the document.

        Parameters
        ----------
        doc: Doc
            Document into which to inject generated G-Code.
        """

        # Shape type header
        s = "(" + str(self).replace("(", ": ")
        doc.AddLine(s)

        if self._header is not None:
            doc.AddLine(f"({self._header})")

        # Retract Z-axis if needed.
        if doc.z_retract_enabled:
            doc.AddLine(f"G0 Z{doc.z_retract_height:0.3f} F{doc.speed_position:0.1f}")

        # Go to XY coordinate.
        pts = self.points
        doc.AddLine(f"G0 X{pts[0,0]:0.3f} Y{pts[0,1]:0.3f} F{doc.speed_position:0.1f}")

        # Set Z-axis positioning
        # Separate line in case we needed to lift to get to the XY pos.
        doc.AddLine(f"G0 Z{self.z:0.3f}")

        # Set print speed, using default if needed.
        if self.speed_print is None:
            doc.AddLine(f"G1 F{doc.speed_print:0.1f}")
        else:
            doc.AddLine(f"G1 F{self.speed_print:0.1f}")

        # Set shape specific power if specified
        if self.laser_power is not None:
            doc.laser_power = self.laser_power

        # Laser on
        doc.AddLine(doc.laser_on)

        # Process list of points that determine the perimeter.
        # Note that we're already at the first point, so skip it.
        # Custom shape G-Code only returns the start point, so we need to
        # request the code.
        if isinstance(self, Circle):
            pass

        if len(pts) > 1:
            # Have a list of some sort.
            for pt in pts[1:]:
                doc.AddLine(f"G1 X{pt[0]:0.3f} Y{pt[1]:0.3f}")

            # For closed shapes, return to the first point.
            if self.is_closed:
                doc.AddLine(f"G1 X{pts[0,0]:0.3f} Y{pts[0,1]:0.3f}")

        else:
            # Custom gcode command (circle, arc)
            try:
                doc.AddLine(self.gcode)
            except AttributeError:
                raise AttributeError(
                    f"Shape {type(self)} does not have a gcode property."
                )

        # Laser off & return to default power.
        doc.AddLine(doc.laser_off)
        doc.laser_power = doc.laser_power_default

        # Footer
        if self._footer is not None:
            doc.AddLine(f"({self._footer})")
        doc.AddLine()

        return doc.code

    @property
    def gcode(self):
        raise NotImplementedError(f"{type(self)}.gcode not implemented.")

    @property
    def points(self):
        raise NotImplementedError(f"{type(self)}.points not implemented.")

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, x: float = 0.0):
        """
        Sets shape X coordinate (left).
        """
        self._x = x

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, y: float = 0.0):
        """
        Sets shape Y coordinate (lower).
        """
        self._y = y

    @property
    def z(self) -> float:
        return self._z

    @z.setter
    def z(self, z: float = 0.0):
        """
        Sets shape Z coordinate (lower).
        """

        if z is None:
            raise ValueError("Z must be non-None.")

        self._z = z

    @property
    def speed_print(self) -> float:
        """
        Shape print speed.  Overrides document print speed if set.
        """
        return self._speed_print

    @speed_print.setter
    def speed_print(self, value: float):
        if value <= 0.0:
            raise ValueError("Speed must be positive.")

        self._speed_print = value

    @property
    def laser_power(self) -> float:
        """
        Shape print laser power.  Overrides document print laser power if set.
        Laser power must be in range [0,100].
        """
        return self._laser_power

    @laser_power.setter
    def laser_power(self, value: float):
        if value < 0 or value > 100:
            raise ValueError("Laser power must be in range [0,100]")

        self._laser_power = value

    @property
    def passes(self) -> int:
        """
        Number of passes to repeat for this shape.
        """
        return self._passes

    @passes.setter
    def passes(self, value: int):
        if value < 0:
            raise ValueError("passes must be non-negative")

        self._passes = value

    @property
    def stepdown(self) -> float:
        """
        Z stepdown used for multiple passes.
        """
        return self._stepdown

    @stepdown.setter
    def stepdown(self, value: float):
        if value < 0:
            value = -value
        self._stepdown = value

    @property
    def header(self) -> str:
        """
        Header comment to be emmitted at start of G-code gen for shape.
        """
        return self._header

    @header.setter
    def header(self, value: str):
        self._header = value

    @property
    def footer(self) -> str:
        """
        Footer comment to be emmitted at end of G-code gen for shape.
        """
        return self._footer

    @footer.setter
    def footer(self, value: str):
        self._footer = value

    @property
    def is_closed(self) -> bool:
        """
        Returns True if shape is closed (first and last point are the same).
        """
        return self._is_closed

    @property
    def is_filled(self) -> bool:
        """
        Returns True if rectangle is filled.
        """
        return self._is_filled

    @is_filled.setter
    def is_filled(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError("is_filled must be a boolean.")

        if self.is_filled and not value:
            raise ValueError("Cannot clear is_filled once set.")

        self._is_filled = value

    @property
    def fill(self, layout: Layout):
        raise NotImplementedError(f"{type(self)}.fill not implemented.")

    def closest(self, xy: np.array = np.array([0, 0])) -> np.array:
        """
        Returns shape geometry point closest to the given point.
        Used for G-code scheduling optimization.
        """
        raise NotImplementedError(f"{type(self)}.closest not implemented.")

    def distance(self, xy: np.array = np.array([0, 0])) -> float:
        """
        Returns distance from shape geometry to the given point.
        Used for G-code scheduling optimization.
        """
        raise NotImplementedError(f"{type(self)}.distance not implemented.")

    def startpoint_set(self, xy: np.array):
        """
        Modifies the internal geometry description so that G-Code start as closest
        to the specified point as possible.

        Args:
            xy (np.array): First point for G-Code generation.
        """

        # If not implemented, just skip and miss out on the potential optimization.
        pass

    def Size(self) -> tuple:
        """
        Returns tuple of bounding box size of object.
        Tuple format: (width, height)
        """
        # Emulating a pure virtual method that should have a concrete implementation.
        raise Exception(f"No Size method defined for class: {type(self)}")


class Line(Shape):
    """
    Simple line.
    """

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        length: float = 1,
        rotation: float = 0,
        speed_print: float = None,
        laser_power=None,
    ):
        """
        Initializes a line shape object.

        Parameters
        ----------
        length: float
            Length of the line.

        rotation: float
            Rotation of angle above X-axis.
            Angle units are degrees.
        """

        super().__init__(x=x, y=y, speed_print=speed_print, laser_power=laser_power)

        self.length = length
        self.rotation = rotation

    def __repr__(self):
        info = f"Line(x={self.x:0.3f},y={self.y:0.3f},l={self.length:0.3f},rotation={self.rotation:0.3f})"
        return info

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def length(self) -> float:
        """
        Length of line.
        """
        return self._length

    @length.setter
    def length(self, value: float):
        if value <= 0:
            raise ValueError("Length must be positive.")

        self._length = value

    @property
    def rotation(self) -> float:
        """
        Angle of line above X-axis in degrees.
        """
        return self._rotation

    @rotation.setter
    def rotation(self, value: float):
        self._rotation = value

    def Size(self) -> tuple:
        """
        Return size of Line shape object.
        Line width is reported as zero.
        Horizontal or vertical lines will report one size component
        as zero.
        Diagonal lines will report both size components as non-zero.

        Returns
        -------
        size: tuple
            Object size: (width, height)
        """

        theta = math.radians(self.rotation)
        sz = (self.length * math.cos(theta), self.length * math.sin(theta))
        return sz

    @property
    def points(self) -> np.array:
        """
        Returns a list of points defining the perimeter of the line.
        """
        theta = math.radians(self.rotation)
        x = self.length * math.cos(theta)
        y = self.length * math.sin(theta)
        pts = np.array([[self.x, self.y], [self.x + x, self.y + y]])
        return pts

    def _closest_index(self, xy: np.array = np.array([0, 0])) -> tuple:
        """
        Returns index of point closest to the given point.
        """

        pts = self.points
        delta = pts - xy
        dist = np.linalg.norm(delta, axis=1)
        idx = np.argmin(dist)
        return idx, dist[idx]

    def closest(self, xy: np.array = np.array([0, 0])) -> np.array:
        """
        Returns Line geometry point closest to the given point.
        Used for G-code scheduling optimization.
        """
        idx = self._closest_index(xy)[0]
        return self.points[idx, :]

    def distance(self, xy: np.array = np.array([0, 0])) -> float:
        """
        Returns distance from rectangle geometry to the given point.
        Used for G-code scheduling optimization.
        """

        return self._closest_index(xy)[1]

    def startpoint_set(self, xy: np.array):
        """
        Modifies the internal geometry description so that G-Code start as closest
        to the specified point as possible.

        Args:
            xy (np.array): First point for G-Code generation.
        """

        idx = self._closest_index(xy)[0]
        if idx == 0:
            # Already closest
            return

        # Swap line direction.
        pts = self.points
        self.x = pts[1, 0]
        self.y = pts[1, 1]
        self.rotation += 180

class PolyLine(Shape):
    """
    Segmented line object.
    """

    def __init__(self,
                 z:float=0.0,
                 points:np.array=None,
                 speed_print: float = None,
                 laser_power=None):

        super().__init__(
            z=z, speed_print=speed_print, laser_power=laser_power
        )

        if points is not None:
            self.points = points

    def __repr__(self):
        info = f"PolyLine(points={len(self.points)})"
        return info

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def points(self) -> np.array:
        # List of points in the PolyLine.
        return self._points

    @points.setter
    def points(self, points: np.array):

        if not isinstance(points, np.ndarray):
            raise ValueError("Points must be a 2D array.")

        if points.shape[1] != 2:
            raise ValueError("Points must be a 2D array with 2 columns.")

        self._points = points

    @property
    def x(self) -> float:

        # Center point via midpoint of ranges
        x = (np.min(self.points[:, 0]) + np.max(self.points[:, 0])) / 2
        return x

    @property
    def x(self) -> float:

        # Center point via midpoint of ranges
        y = (np.min(self.points[:, 1]) + np.max(self.points[:, 1])) / 2
        return y

    def distance(self, xy: np.array = np.array([0, 0])) -> float:
        """
        Returns distance from PolhyLine geometry end points to the given point.
        Used for G-code scheduling optimization.
        """

        pts = np.array([self.points[0,:], self.points[-1,:]])
        delta = pts - xy
        dist = np.linalg.norm(delta, axis=1)
        idx = np.argmin(dist)
        return dist[idx]

    def append(self,xy:np.array):
        """
        Adds a point to the PolyLine.
        """

        if not isinstance(xy, np.ndarray):
            raise ValueError("Point must be a 2D array.")
        if xy.shape[1] != 2:
            raise ValueError("Points must be a 2D array with 2 columns.")

        self._points = np.vstack([self._points,xy])

class Rectangle(Shape):
    """
    Draws a rectangle.
    x & y are the center of the rectangle.
    """

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        width: float = 1.0,
        height: float = 1.0,
        rotation: float = 0.0,
        speed_print: float = None,
        laser_power=None,
        is_filled=False,
    ):
        """
        Initializes a Rectangle object.
        """

        self._points = None
        super().__init__(
            x=x, y=y, z=z, speed_print=speed_print, laser_power=laser_power
        )

        self.height = height
        self.width = width
        self.rotation = rotation

        self._is_closed = True
        self.is_filled = is_filled

    def __repr__(self):
        info = f"Rectangle(x={self.x:0.2f},y={self.y:0.2f},width={self.width:0.2f},height={self.height:0.2f})"
        return info

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, x: float = 0.0):
        """
        Sets Rectangle center X coordinate.
        """
        self._x = x

        if self._points is not None:
            self._points_gen()

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, y: float = 0.0):
        """
        Sets Rectangle center Y coordinate.
        """
        self._y = y

        if self._points is not None:
            self._points_gen()

    @property
    def width(self) -> float:
        return self._width

    @width.setter
    def width(self, width: float = 1.0):
        """
        Box width (x dimension)
        """
        if width <= 0.0:
            raise ValueError("Width must be positive.")

        self._width = width

        if self._points is not None:
            self._points_gen()

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, height: float = 10.0):
        """
        Box height (y dimension)
        """
        if height <= 0.0:
            raise ValueError("Height must be positive.")

        self._height = height

        if self._points is not None:
            self._points_gen()

    @property
    def rotation(self) -> float:
        return self._rotation

    @rotation.setter
    def rotation(self, rotation: float = 0.0):
        """
        Box rotation in radians.
        """
        self._rotation = rotation

    def _points_gen(self):
        """
        Generates point list for rectangle.
        """

        # Generate point list.
        w = self.width / 2
        h = self.height / 2
        # Lower left, upper left, upper right, lower right
        pts = np.array([[-w, -h], [-w, h], [w, h], [w, -h]])

        # Rotate
        R = [
            [np.cos(self.rotation), -np.sin(self.rotation)],
            [np.sin(self.rotation), np.cos(self.rotation)],
        ]
        R = np.array(R)

        # Rotate each point by the rotation matrix
        pts = pts @ R.T

        # Offset
        pts += np.array([self.x, self.y])
        self._points = pts

    @property
    def points(self) -> np.array:
        """List of points defining the perimeter of the rectangle."""

        if self._points is None:
            self._points_gen()

        return self._points

    def Size(self) -> tuple:
        return (self.width, self.height)

    def fill(self, doc: Doc) -> None:
        """
        Generates Line objects to fill in square.
        """

        if not isinstance(doc, Doc):
            raise ValueError("Expected a Doc object.")

        # Number of lines to draw for fill
        n_lines = np.round((self.height - doc.fill_stepover) / doc.fill_stepover)
        n_lines = int(n_lines)

        # Line length shortened by stepover distance.
        length = self.width - 2 * doc.fill_stepover

        # Handle rotation of rectangle
        R = [
            [np.cos(self.rotation), -np.sin(self.rotation)],
            [np.sin(self.rotation), np.cos(self.rotation)],
        ]
        R = np.array(R).T

        # First line start point is offset from lower left rectangle point.
        p_start = self.points[0, :] + doc.fill_stepover * np.array([1, 1]) @ R

        # Start point position deltas based on stepover & angle.
        d_start = np.array([0, doc.fill_stepover])
        d_start = d_start @ R

        for i in range(n_lines):
            # Line start point
            line = Line(
                x=p_start[0],
                y=p_start[1],
                z=self.z,
                length=length,
                rotation=self.rotation * 180 / np.pi,
            )
            line.header = "Rectangle Fill"
            doc.AddChild(line)

            p_start += d_start

    def distance(self, xy: np.array = np.array([0, 0])) -> float:
        """
        Returns distance from Rectangle geometry to the given point.
        Used for G-code scheduling optimization.
        """

        pts = self.points
        delta = pts - xy
        dist = np.linalg.norm(delta, axis=1)
        idx = np.argmin(dist)
        return dist[idx]

    def startpoint_set(self, xy: np.array) -> None:
        """
        Modifies the internal geometry description so that G-Code start as closest
        to the specified point as possible.

        Args:
            xy (np.array): First point for G-Code generation.
        """

        # Rotate our point list so that the closest point is first.
        delta = self.points - xy
        dist = np.linalg.norm(delta, axis=1)
        idx = np.argmin(dist)
        self._points = np.roll(self.points, -idx, axis=0)


class Polygon(Shape):
    """Generic Polygon"""

    def __init__(
        self,
        points: np.array = None,
        speed_print: float = None,
        z: float = 0,
        laser_power=None,
        is_filled=False,
    ):
        """
        Initializes a Polygon object.
        """

        self._points = points

        # Center point via midpoint of ranges
        x = (np.min(points[:, 0]) + np.max(points[:, 0])) / 2
        y = (np.min(points[:, 1]) + np.max(points[:, 1])) / 2

        super().__init__(
            x=x, y=y, z=z, speed_print=speed_print, laser_power=laser_power
        )

        self._is_closed = True
        self.is_filled = is_filled

    def __repr__(self):
        return f"Polygon(n_pts={len(self.points)})"

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def points(self) -> np.array:
        """List of points defining the perimeter of the rectangle."""

        return self._points

    def distance(self, xy: np.array = np.array([0, 0])) -> float:
        """
        Returns distance from Polygon geometry to the given point.
        Used for G-code scheduling optimization.
        """

        pts = self.points
        delta = pts - xy
        dist = np.linalg.norm(delta, axis=1)
        idx = np.argmin(dist)
        return dist[idx]


class Circle(Shape):
    """Circle G-Code object"""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        radius: float = 1.0,
        speed_print: float = None,
        laser_power=None,
        is_filled=False,
    ):
        self._x = 0.0
        self._y = 0.0
        self._radius = 0.0
        self._start = np.array([[0.0, 0.0]])

        super().__init__(
            x=x, y=y, z=z, speed_print=speed_print, laser_power=laser_power
        )

        self.radius = radius

        self._is_closed = True
        self.is_filled = is_filled

        # Initial start point
        self.startpoint_set()

    def __repr__(self):
        info = f"Circle(xc={self.x:0.3f},yc={self.y:0.3f},radius={self.radius:0.3f},xs={self._start[0,0]:0.3f},ys={self._start[0,1]:0.3f})"
        return info

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def radius(self) -> float:
        return self._radius

    @radius.setter
    def radius(self, radius: float = 1.0):
        if radius <= 0.0:
            raise ValueError("Radius must be positive.")

        self._radius = radius
        self.startpoint_set()

    @property
    def x(self) -> float:
        """
        Circle center X coordinate.
        """
        return self._x

    @x.setter
    def x(self, x: float = 0.0):
        """
        Sets Circle center X coordinate.
        """
        self._x = x

        # Update start point
        self.startpoint_set()

    @property
    def y(self) -> float:
        """
        Circle center Y coordinate.
        """
        return self._y

    @y.setter
    def y(self, y: float = 0.0):
        """
        Sets Circle center Y coordinate.
        """
        self._y = y

        # Update start point
        self.startpoint_set()

    @property
    def gcode(self) -> str:
        """
        Returns custom G-Code for Circle.
        Circle is always drawn with clockwise rotation.
        """

        # ARC mode.
        # https://marlinfw.org/docs/gcode/G002-G003.html
        # G2: Clockwise
        # G3: Counter clockwise

        # ARC mode motion:
        # From the starting point, where ever the previous command left us,
        # Go to a specified XY point, while rotating around the center point.
        # The center point is specified as an offset from the start point.

        # For a cirlce, we just have to return center point.
        delta = np.array([self.x, self.y]) - self._start[0,:]
        return f"G2 X{self._start[0,0]:0.3f} Y{self._start[0,1]:0.3f} I{delta[0]:0.3f} J{delta[1]:0.3f}"

    @property
    def points(self) -> np.array:
        """
        List of points defining the perimeter of the circle.
        Returns only start point.
        """

        # Generate point list.
        pts = self._start

        return pts

    def fill(self, doc: Doc) -> None:
        """
        Generates Line objects to fill in Circle.
        """

        if not isinstance(doc, Doc):
            raise ValueError("Expected a Doc object.")

        # Number of lines to draw for fill
        # Lines are mirrors of each other, so we only need to draw half.
        n_lines = np.round((self.radius - doc.fill_stepover) / doc.fill_stepover)
        n_lines = int(n_lines)

        # Add in center/diameter line.
        line = Line(
            x=self.x - self.radius + doc.fill_stepover,
            y=self.y,
            z=self.z,
            length=2 * (self.radius - doc.fill_stepover),
        )
        line.header = "Circle Fill"
        doc.AddChild(line)

        dy = doc.fill_stepover
        theta = 0  # Initial angle
        for i in range(n_lines):
            # Assume we have a line from the center to the perimeter.
            # Calculuate the XY point on the perimeter.

            # Updated rotation angle
            theta = np.arcsin(dy / self.radius + np.sin(theta))

            # Calculate point on perimeter
            x_perimeter = self.radius * np.cos(theta)
            y_perimeter = self.radius * np.sin(theta)

            x_start = -x_perimeter + doc.fill_stepover
            length = 2 * (x_perimeter - doc.fill_stepover)

            # Line start point
            line = Line(
                x=x_start + self.x,
                y=self.y + y_perimeter,
                z=self.z,
                length=length,
            )
            line.header = "Circle Fill"
            doc.AddChild(line)

            # Mirrored Line start point
            line = Line(
                x=x_start + self.x,
                y=self.y - y_perimeter,
                z=self.z,
                length=length,
            )
            line.header = "Circle Fill"
            doc.AddChild(line)

    def distance(self, xy: np.array = np.array([0, 0])) -> np.array:
        """
        Returns distance from circle geometry to the given point.
        Used for G-code scheduling optimization.
        """

        delta = np.array([self.x, self.y]) - xy
        dist = np.linalg.norm(delta) - self.radius
        return dist

    def startpoint_set(self, xy: np.array=None) -> None:
        """
        Modifies the internal geometry description so that G-Code start as closest
        to the specified point as possible.

        Args:
            xy (np.array): First point for G-Code generation.
        """

        # Find point on perimeter that intersects the line
        # from the given point to the cirle center.

        # If not specified, start at the top of the circle.
        if xy is None:
            theta = 0
        else:
            # Find angle of line from center to given point.
            delta = xy - np.array([self.x, self.y])
            theta = np.arctan(delta[1]/delta[0])

        # Find point on perimeter at angle theta
        r = self.radius
        self._start[0] = np.array([self.x,self.y]) - r * np.array([np.cos(theta),np.sin(theta)])
        pass

class Text(Shape):
    """
    Draws characters for a text string.
    Heavily modified version of TextToGcode from:
    https://github.com/Yoyolick/TextToGcode
    """

    # TODO: Text: Character size is really in doc units (mm,in). Update to match.

    def __init__(
        self,
        text: str,
        size_mm: float = 1,
        rotation_deg: float = 0,
        x: float = 0.0,
        y: float = 0.0,
        speed_print: float = None,
        laser_power=None,
    ):
        # Shape handles a lot of pieces for us.
        super().__init__(x=x, y=y, speed_print=speed_print, laser_power=laser_power)

        # set basic passed args
        self.text = text.upper()  # Only support a single case.
        self.size_mm = size_mm
        self.rotation_rad = math.radians(rotation_deg)

        # set global class vars
        self.operations_raw = []  # Raw character points, no scaling or rotation.
        self.operations_final = []  # Scaled and rotated character points
        self.offset_x = 0

        # Finalized text extents
        self.x_min = math.inf
        self.x_max = -math.inf
        self.y_min = math.inf
        self.y_max = -math.inf

        # Set default header
        self.header = f'Text: "{self.text}"'

        raise NotImplementedError("Not ported to update point list implementation.")

        # Render the string into points
        self.CollectCharacters()
        self.RenderPoints()

    def Size(self):
        """
        Width & height of rendered text string.
        """
        return (self.x_max - self.x_min, self.y_max - self.y_min)

    def RenderPoints(self):
        """
        Converts the character string to a list of scaled and rotated points.
        Characters are vectors not rasters, so included positioning & printing moves.
        """

        for point in self.operations_raw:
            if isinstance(point, tuple):
                # Point coordinate

                # Default character size is 9 units tall.  Scale down.
                scale_factor = 1 / 9
                point = (point[0] * scale_factor, point[1] * scale_factor)

                # Perform scaling
                # Default size is 1 mm
                if self.size_mm != 1:
                    scaledPoint = (point[0] * self.size_mm, point[1] * self.size_mm)
                else:
                    scaledPoint = (point[0], point[1])

                # Perform rotation
                if self.rotation_rad != 0:
                    originX = 0
                    originY = 0
                    newpointX = (
                        originX
                        + math.cos(self.rotation_rad) * (scaledPoint[0] - originX)
                        - math.sin(self.rotation_rad) * (scaledPoint[1] - originY)
                    )
                    newpointY = (
                        originY
                        + math.sin(self.rotation_rad) * (scaledPoint[0] - originX)
                        + math.cos(self.rotation_rad) * (scaledPoint[1] - originY)
                    )
                    newpoint = (newpointX, newpointY)
                else:
                    newpoint = (scaledPoint[0], scaledPoint[1])

                self.operations_final.append(newpoint)

                # Capture extents
                if newpoint[0] > self.x_max:
                    self.x_max = newpoint[0]
                if newpoint[0] < self.x_min:
                    self.x_min = newpoint[0]
                if newpoint[1] > self.y_max:
                    self.y_max = newpoint[1]
                if newpoint[1] < self.y_min:
                    self.y_min = newpoint[1]

            elif isinstance(point, str):
                # Command
                self.operations_final.append(point)

        # Take a second pass through the points to set bounding box lower left
        # corner to (0,0)
        for idx, point in enumerate(self.operations_final):
            if isinstance(point, tuple):
                newPoint = (point[0] - self.x_min, point[1] - self.y_min)
                self.operations_final[idx] = newPoint

        # Adjust extents
        self.x_max -= self.x_min
        self.x_min = 0
        self.y_max -= self.y_min
        self.y_min = 0

    def CollectCharacters(self):
        # get and call functions for letter in given text and append them to queue

        # TODO: Text: Move x_offset updates into the character methods.
        # TODO: Text: create a character class that knows all it's stuff.
        # TODO: Text: Create a dictionary of character objects.
        # TODO: Text: Support LF/CR to allow for multiple line text, add y_offset

        for char in self.text:
            if char == " ":
                self.whiteSpace()
                self.offset_x += 8

            elif char == "A":
                self.a()
                self.offset_x += 8

            elif char == "B":
                self.b()
                self.offset_x += 8

            elif char == "C":
                self.c()
                self.offset_x += 8

            elif char == "D":
                self.d()
                self.offset_x += 8

            elif char == "E":
                self.e()
                self.offset_x += 8

            elif char == "F":
                self.f()
                self.offset_x += 8

            elif char == "G":
                self.g()
                self.offset_x += 8

            elif char == "H":
                self.h()
                self.offset_x += 8

            elif char == "I":
                self.i()
                self.offset_x += 7

            elif char == "J":
                self.j()
                self.offset_x += 7

            elif char == "K":
                self.k()
                self.offset_x += 8

            elif char == "L":
                self.l()
                self.offset_x += 8

            elif char == "M":
                self.m()
                self.offset_x += 8

            elif char == "N":
                self.n()
                self.offset_x += 8

            elif char == "O":
                self.o()
                self.offset_x += 8

            elif char == "P":
                self.p()
                self.offset_x += 8

            elif char == "Q":
                self.q()
                self.offset_x += 8

            elif char == "R":
                self.r()
                self.offset_x += 8

            elif char == "S":
                self.s()
                self.offset_x += 8

            elif char == "T":
                self.t()
                self.offset_x += 7

            elif char == "U":
                self.u()
                self.offset_x += 8

            elif char == "V":
                self.v()
                self.offset_x += 7

            elif char == "W":
                self.w()
                self.offset_x += 9

            elif char == "X":
                self.x()
                self.offset_x += 7

            elif char == "Y":
                self.y()
                self.offset_x += 7

            elif char == "Z":
                self.z()
                self.offset_x += 8

            elif char == "1":
                self.one()
                self.offset_x += 7

            elif char == "2":
                self.two()
                self.offset_x += 7

            elif char == "3":
                self.three()
                self.offset_x += 7

            elif char == "4":
                self.four()
                self.offset_x += 7

            elif char == "5":
                self.five()
                self.offset_x += 7

            elif char == "6":
                self.six()
                self.offset_x += 7

            elif char == "7":
                self.seven()
                self.offset_x += 7

            elif char == "8":
                self.eight()
                self.offset_x += 7

            elif char == "9":
                self.nine()
                self.offset_x += 7

            elif char == "0":
                self.zero()
                self.offset_x += 7

            elif char == "+":
                self.plus()
                self.offset_x += 7

            elif char == "-":
                self.minus()
                self.offset_x += 7

            elif char == ".":
                self.period()
                self.offset_x += 0

            elif char == "%":
                self.percentage()
                self.offset_x += 7

            else:
                raise ValueError(f"Unsupported character: '{char}'")

    def GCode(self, doc):
        """
        Generates G-Code for text string object.
        """

        # Shape preamble, handles shape header.
        super().GCode(doc)

        # Set shape specific power if specified
        if self.laser_power is not None:
            doc.laser_power = self.laser_power

        # replace placeholder string commands with GCODE commands
        laser_on = False
        for command in self.operations_final:
            if isinstance(command, str):
                if command == "off":
                    command = doc.laser_off
                    laser_on = False
                elif command == "on":
                    command = doc.laser_on
                    laser_on = True
                elif command == "fast":
                    command = f"F{doc.speed_position:0.1f}"
                elif command == "slow":
                    # Set print speed, using default if needed.
                    if self.speed_print is None:
                        command = f"F{doc.speed_print:0.1f}"
                    else:
                        command = f"F{self.speed_print:0.1f}"

                # Command already rendered, just capture.
                doc.AddLine(command)

            if isinstance(command, tuple):
                # Point that needs to be rendered, appying position offset
                gcmd = "G1"
                if not laser_on:
                    gcmd = "G0"

                doc.AddLine(
                    f"{gcmd} X{self.x + command[0]:0.3f} Y{self.y + command[1]:0.3f} Z0"
                )

        # Laser off & return to default power.
        doc.AddLine(doc.laser_off)  # This is likely redundant, but it's safer
        doc.laser_power = doc.laser_power_default

        # Footer
        if self._footer is not None:
            doc.AddLine(f"({self._footer})")

        return doc.code

    def appendPoints(self, points):
        """
        Appends character data to the operations list.
        """
        for point in points:
            self.operations_raw.append(point)

    #  .o88b. db   db  .d8b.  d8888b.  .d8b.   .o88b. d888888b d88888b d8888b. .d8888.
    # d8P  Y8 88   88 d8' `8b 88  `8D d8' `8b d8P  Y8 `~~88~~' 88'     88  `8D 88'  YP
    # 8P      88ooo88 88ooo88 88oobY' 88ooo88 8P         88    88ooooo 88oobY' `8bo.
    # 8b      88~~~88 88~~~88 88`8b   88~~~88 8b         88    88~~~~~ 88`8b     `Y8b.
    # Y8b  d8 88   88 88   88 88 `88. 88   88 Y8b  d8    88    88.     88 `88. db   8D
    #  `Y88P' YP   YP YP   YP 88   YD YP   YP  `Y88P'    YP    Y88888P 88   YD `8888Y'

    def whiteSpace(self):
        # whitespace function for spaces
        self.offset_x += 4

    def a(self):
        #           .   .
        #       .           .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .   .   .   .   .   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .

        xOff = self.offset_x

        points = [
            "(Character: A)",
            "on",
            "slow",
            (0 + xOff, 0),
            (0 + xOff, 7),
            (1 + xOff, 8),
            (2 + xOff, 9),
            (3 + xOff, 9),
            (4 + xOff, 8),
            (5 + xOff, 7),
            (5 + xOff, 0),
            "off",
            "fast",
            (5 + xOff, 4),
            "on",
            "slow",
            (0 + xOff, 4),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def b(self):
        #   .   .   .   .
        #   .               .
        #   .                   .
        #   .                   .
        #   .               .
        #   .   .   .   .
        #   .               .
        #   .                   .
        #   .                   .
        #   .   .   .   .   .

        xOff = self.offset_x

        points = [
            "(Character: B)",
            "fast",
            (0 + xOff, 0),
            "on",
            "slow",
            (0 + xOff, 0),
            (0 + xOff, 9),
            (3 + xOff, 9),
            (4 + xOff, 8),
            (5 + xOff, 7),
            (5 + xOff, 6),
            (4 + xOff, 5),
            (3 + xOff, 4),
            (0 + xOff, 4),
            "off",
            "fast",
            (3 + xOff, 4),
            "on",
            "slow",
            (4 + xOff, 3),
            (5 + xOff, 2),
            (5 + xOff, 1),
            (4 + xOff, 0),
            (0 + xOff, 0),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def c(self):
        #       .   .   .   .
        #   .                   .
        #   .
        #   .
        #   .
        #   .
        #   .
        #   .
        #   .                   .
        #       .   .   .   .

        xOff = self.offset_x

        points = [
            "(Character: C)",
            "fast",
            (0 + xOff, 0),
            "off",
            "fast",
            (5 + xOff, 1),
            "on",
            "slow",
            (4 + xOff, 0),
            (1 + xOff, 0),
            (0 + xOff, 1),
            (0 + xOff, 8),
            (1 + xOff, 9),
            (4 + xOff, 9),
            (5 + xOff, 8),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def d(self):
        #   .   .   .   .
        #   .               .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .               .
        #   .   .   .   .

        xOff = self.offset_x

        points = [
            "(Character: D)",
            "fast",
            (0 + xOff, 0),
            "on",
            "slow",
            (0 + xOff, 9),
            (3 + xOff, 9),
            (4 + xOff, 8),
            (5 + xOff, 7),
            (5 + xOff, 2),
            (4 + xOff, 1),
            (3 + xOff, 0),
            (0 + xOff, 0),
            (0 + xOff, 9),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def e(self):
        #   .   .   .   .   .   .
        #   .
        #   .
        #   .
        #   .   .   .   .   .   .
        #   .
        #   .
        #   .
        #   .
        #   .   .   .   .   .   .

        xOff = self.offset_x

        points = [
            "(Character: E)",
            "fast",
            (0 + xOff, 0),
            "on",
            "slow",
            (0 + xOff, 9),
            (5 + xOff, 9),
            "off",
            "fast",
            (5 + xOff, 5),
            "on",
            "slow",
            (0 + xOff, 5),
            "off",
            "fast",
            (5 + xOff, 0),
            "on",
            "slow",
            (0 + xOff, 0),
            (0 + xOff, 9),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def f(self):
        #   .   .   .   .   .   .
        #   .
        #   .
        #   .
        #   .
        #   .   .   .   .   .   .
        #   .
        #   .
        #   .
        #   .

        xOff = self.offset_x

        points = [
            "(Character: F)",
            "fast",
            (0 + xOff, 0),
            "on",
            "slow",
            (0 + xOff, 9),
            (5 + xOff, 9),
            "off",
            "fast",
            (5 + xOff, 5),
            "on",
            "slow",
            (0 + xOff, 5),
            "off",
            "fast",
            (0 + xOff, 0),
            "on",
            "slow",
            (0 + xOff, 9),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def g(self):
        #       .   .   .   .
        #   .                   .
        #   .
        #   .
        #   .
        #   .               .   .
        #   .                   .
        #   .                   .
        #   .                   .
        #       .   .   .   .

        xOff = self.offset_x

        points = [
            "(Character: G)",
            "off",
            "fast",
            (5 + xOff, 8),
            "on",
            "slow",
            (4 + xOff, 9),
            (1 + xOff, 9),
            (0 + xOff, 8),
            (0 + xOff, 1),
            (1 + xOff, 0),
            (4 + xOff, 0),
            (5 + xOff, 1),
            (5 + xOff, 4),
            (4 + xOff, 4),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def h(self):
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .   .   .   .   .   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .

        xOff = self.offset_x

        points = [
            "(Character: H)",
            "fast",
            (0 + xOff, 0),
            "on",
            "slow",
            (0 + xOff, 9),
            "off",
            "fast",
            (5 + xOff, 9),
            "on",
            "slow",
            (5 + xOff, 0),
            "off",
            "fast",
            (0 + xOff, 5),
            "on",
            "slow",
            (5 + xOff, 5),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def i(self):
        #   .   .   .   .   .
        #           .
        #           .
        #           .
        #           .
        #           .
        #           .
        #           .
        #           .
        #   .   .   .   .   .

        xOff = self.offset_x

        points = [
            "(Character: I)",
            "fast",
            (0 + xOff, 0),
            "on",
            "slow",
            (4 + xOff, 0),
            "off",
            "fast",
            (4 + xOff, 9),
            "on",
            "slow",
            (0 + xOff, 9),
            "off",
            "fast",
            (2 + xOff, 9),
            "on",
            "slow",
            (2 + xOff, 0),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def j(self):
        #   .   .   .   .   .
        #           .
        #           .
        #           .
        #           .
        #           .
        #           .
        #           .
        #           .
        #   .   .

        xOff = self.offset_x

        points = [
            "(Character: J)",
            "fast",
            (0 + xOff, 0),
            "on",
            "slow",
            (1 + xOff, 0),
            (2 + xOff, 1),
            (2 + xOff, 9),
            (0 + xOff, 9),
            "off",
            "fast",
            (2 + xOff, 9),
            "on",
            "slow",
            (4 + xOff, 9),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def k(self):
        #   .                   .
        #   .                   .
        #   .                   .
        #   .               .
        #   .           .
        #   .   .   .
        #   .           .
        #   .               .
        #   .                   .
        #   .                   .

        xOff = self.offset_x

        points = [
            "(Character: K)",
            "fast",
            (0 + xOff, 0),
            "on",
            "slow",
            (0 + xOff, 9),
            "off",
            "fast",
            (5 + xOff, 9),
            "on",
            "slow",
            (5 + xOff, 7),
            (4 + xOff, 6),
            (3 + xOff, 5),
            (2 + xOff, 4),
            (1 + xOff, 4),
            (0 + xOff, 4),
            (2 + xOff, 4),
            (3 + xOff, 3),
            (4 + xOff, 2),
            (5 + xOff, 1),
            (5 + xOff, 0),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def l(self):
        #   .
        #   .
        #   .
        #   .
        #   .
        #   .
        #   .
        #   .
        #   .
        #   .   .   .   .   .   .

        xOff = self.offset_x

        points = [
            "(Character: L)",
            "fast",
            (0 + xOff, 9),
            "on",
            "slow",
            (0 + xOff, 0),
            (5 + xOff, 0),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def m(self):
        #   .                       .
        #   .   .               .   .
        #   .       .       .       .
        #   .           .           .
        #   .           .           .
        #   .                       .
        #   .                       .
        #   .                       .
        #   .                       .
        #   .                       .

        xOff = self.offset_x

        points = [
            "(Character: M)",
            "fast",
            (0 + xOff, 0),
            "on",
            "slow",
            (0 + xOff, 9),
            (1 + xOff, 8),
            (2 + xOff, 7),
            (3 + xOff, 6),
            (3 + xOff, 5),
            (3 + xOff, 6),
            (4 + xOff, 7),
            (5 + xOff, 8),
            (6 + xOff, 9),
            (6 + xOff, 0),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def n(self):
        #   .                   . APROXIMATE, letting the cnc handle this movement
        #   . .                 .
        #   .   .               .
        #   .      .            .
        #   .                   .
        #   .        .          .
        #   .                   .
        #   .          .        .
        #   .             .     .
        #   .                .  .

        xOff = self.offset_x

        points = [
            "(Character: N)",
            "fast",
            (0 + xOff, 0),
            "on",
            "slow",
            (0 + xOff, 9),
            (5 + xOff, 0),
            (5 + xOff, 9),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def o(self):
        #       .   .   .   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #       .   .   .   .

        xOff = self.offset_x

        points = [
            "(Character: O)",
            "fast",
            (0 + xOff, 1),
            "on",
            "slow",
            (0 + xOff, 8),
            (1 + xOff, 9),
            (4 + xOff, 9),
            (5 + xOff, 8),
            (5 + xOff, 1),
            (4 + xOff, 0),
            (1 + xOff, 0),
            (0 + xOff, 1),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def p(self):
        #       .   .   .   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .   .   .   .   .
        #   .
        #   .
        #   .
        #   .

        xOff = self.offset_x

        points = [
            "(Character: P)",
            "fast",
            (0 + xOff, 0),
            "on",
            "slow",
            (0 + xOff, 8),
            (1 + xOff, 9),
            (4 + xOff, 9),
            (5 + xOff, 8),
            (5 + xOff, 5),
            (4 + xOff, 4),
            (0 + xOff, 4),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def q(self):
        #       .   .   .   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .               .
        #       .   .   .       .

        xOff = self.offset_x

        points = [
            "(Character: Q)",
            "fast",
            (0 + xOff, 1),
            "on",
            "slow",
            (0 + xOff, 8),
            (1 + xOff, 9),
            (4 + xOff, 9),
            (5 + xOff, 8),
            (5 + xOff, 2),
            (4 + xOff, 1),
            (5 + xOff, 0),
            "off",
            "fast",
            (4 + xOff, 1),
            "on",
            "slow",
            (4 + xOff, 1),
            (3 + xOff, 0),
            (1 + xOff, 0),
            (0 + xOff, 1),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def r(self):
        #       .   .   .
        #   .               .
        #   .                   .
        #   .                   .
        #   .               .
        #   .   .   .   .
        #   .               .
        #   .                   .
        #   .                   .
        #   .                   .

        xOff = self.offset_x

        points = [
            "(Character: R)",
            "fast",
            (0 + xOff, 0),
            "on",
            "slow",
            (0 + xOff, 8),
            (1 + xOff, 9),
            (3 + xOff, 9),
            (4 + xOff, 8),
            (5 + xOff, 7),
            (5 + xOff, 6),
            (4 + xOff, 5),
            (3 + xOff, 4),
            (0 + xOff, 4),
            "off",
            "fast",
            (3 + xOff, 4),
            "on",
            "slow",
            (4 + xOff, 3),
            (5 + xOff, 2),
            (5 + xOff, 0),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def s(self):
        #       .   .   .   .   .
        #   .
        #   .
        #   .
        #   .
        #       .   .   .   .
        #                       .
        #                       .
        #                       .
        #   .   .   .   .   .

        xOff = self.offset_x

        points = [
            "(Character: S)",
            "fast",
            (0 + xOff, 0),
            "on",
            "slow",
            (4 + xOff, 0),
            (5 + xOff, 1),
            (5 + xOff, 3),
            (4 + xOff, 4),
            (1 + xOff, 4),
            (0 + xOff, 5),
            (0 + xOff, 8),
            (1 + xOff, 9),
            (5 + xOff, 9),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def t(self):
        #   .   .   .   .   .
        #           .
        #           .
        #           .
        #           .
        #           .
        #           .
        #           .
        #           .
        #           .

        xOff = self.offset_x

        points = [
            "(Character: T)",
            "fast",
            (2 + xOff, 0),
            "on",
            "slow",
            (2 + xOff, 9),
            "off",
            "fast",
            (0 + xOff, 9),
            "on",
            "slow",
            (4 + xOff, 9),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def u(self):
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #   .                   .
        #       .   .   .   .

        xOff = self.offset_x

        points = [
            "(Character: U)",
            "fast",
            (0 + xOff, 9),
            "on",
            "slow",
            (0 + xOff, 1),
            (1 + xOff, 0),
            (4 + xOff, 0),
            (5 + xOff, 1),
            (5 + xOff, 9),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def v(self):
        #   .               .
        #   .               .
        #   .               .
        #   .               .
        #   .               . this one is also
        #   .               . interpolated as top left
        #   .               . bottom middle top right
        #   .               .
        #       .       .
        #           .

        xOff = self.offset_x

        points = [
            "(Character: V)",
            "fast",
            (0 + xOff, 9),
            "on",
            "slow",
            (2 + xOff, 0),
            (4 + xOff, 9),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def w(self):
        #   0   1   2   3   4  5
        # 9  o       o       o
        # 8
        # 7
        # 6
        # 5
        # 4
        # 3
        # 2
        # 1
        # 0       o       o

        points = [
            "(Character: W)",
            "fast",
            (self.offset_x + 0, 9),
            "on",
            "slow",
            (self.offset_x + 2, 0),
            (self.offset_x + 3, 9),
            (self.offset_x + 4, 0),
            (self.offset_x + 6, 9),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def x(self):
        # once again, gonna be interpolation
        #   .               .
        #
        #
        #
        #
        #           .
        #
        #
        #
        #   .               .

        xOff = self.offset_x

        points = [
            "(Character: X)",
            "fast",
            (0 + xOff, 0),
            "on",
            "slow",
            (4 + xOff, 9),
            "off",
            "fast",
            (0 + xOff, 9),
            "on",
            "slow",
            (4 + xOff, 0),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def y(self):
        #   .               .
        #   .               .
        #   .               .
        #   .               .
        #       .       .
        #           .
        #           .
        #           .
        #           .
        #           .

        xOff = self.offset_x

        points = [
            "(Character: Y)",
            "fast",
            (2 + xOff, 0),
            "on",
            "slow",
            (2 + xOff, 4),
            (0 + xOff, 6),
            (0 + xOff, 9),
            "off",
            "fast",
            (4 + xOff, 9),
            "on",
            "slow",
            (4 + xOff, 6),
            (2 + xOff, 4),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def z(self):
        # more point to point interpolation? yeah lmao
        #   .                   .
        #
        #
        #
        #
        #
        #
        #
        #
        #   .                   .

        xOff = self.offset_x

        points = [
            "(Character: Z)",
            "fast",
            (0 + xOff, 9),
            "on",
            "slow",
            (5 + xOff, 9),
            (0 + xOff, 0),
            (5 + xOff, 0),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    # d8b   db db    db .88b  d88. d8888b. d88888b d8888b. .d8888.
    # 888o  88 88    88 88'YbdP`88 88  `8D 88'     88  `8D 88'  YP
    # 88V8o 88 88    88 88  88  88 88oooY' 88ooooo 88oobY' `8bo.
    # 88 V8o88 88    88 88  88  88 88~~~b. 88~~~~~ 88`8b     `Y8b.
    # 88  V888 88b  d88 88  88  88 88   8D 88.     88 `88. db   8D
    # VP   V8P ~Y8888P' YP  YP  YP Y8888P' Y88888P 88   YD `8888Y'

    def one(self):
        #           .
        #           .
        #           .
        #           .
        #           .
        #           .
        #           .
        #           .
        #           .
        #           .

        xOff = self.offset_x

        points = [
            "(Character: 1)",
            "fast",
            (2 + xOff, 0),
            "on",
            "slow",
            (2 + xOff, 9),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def two(self):
        #           .
        #   .               .
        #
        #
        #
        #
        #
        #
        #
        #   .   .   .   .   .

        xOff = self.offset_x

        points = [
            "(Character: 2)",
            "fast",
            (4 + xOff, 0),
            "on",
            "slow",
            (0 + xOff, 0),
            (4 + xOff, 8),
            (2 + xOff, 9),
            (0 + xOff, 8),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def three(self):
        #           .
        #   .               .
        #                   .
        #                   .
        #   .   .   .   .
        #                   .
        #                   .
        #                   .
        #   .               .
        #           .

        xOff = self.offset_x

        points = [
            "(Character: 3)",
            "fast",
            (0 + xOff, 1),
            "on",
            "slow",
            (2 + xOff, 0),
            (4 + xOff, 1),
            (4 + xOff, 4),
            (3 + xOff, 5),
            (1 + xOff, 5),
            "off",
            "fast",
            (3 + xOff, 5),
            "on",
            "slow",
            (4 + xOff, 6),
            (4 + xOff, 8),
            (2 + xOff, 9),
            (0 + xOff, 8),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def four(self):
        #   .               .
        #   .               .
        #   .               .
        #   .               .
        #   .   .   .   .   .
        #                   .
        #                   .
        #                   .
        #                   .
        #                   .

        xOff = self.offset_x

        points = [
            "(Character: 4)",
            "fast",
            (0 + xOff, 9),
            "on",
            "slow",
            (0 + xOff, 5),
            (4 + xOff, 5),
            "off",
            "fast",
            (4 + xOff, 9),
            "on",
            "slow",
            (4 + xOff, 0),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def five(self):
        #   .   .   .   .   .
        #   .
        #   .
        #   .
        #   .   .   .
        #               .
        #                   .
        #                   .
        #                   .
        #   .   .   .   .

        xOff = self.offset_x

        points = [
            "(Character: 5)",
            "fast",
            (4 + xOff, 9),
            "on",
            "slow",
            (0 + xOff, 9),
            (0 + xOff, 5),
            (2 + xOff, 5),
            (4 + xOff, 3),
            (4 + xOff, 1),
            (3 + xOff, 0),
            (0 + xOff, 0),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def six(self):
        #           .   .   .
        #
        #   .
        #   .
        #   .       .
        #   .
        #   .               .
        #   .               .
        #   .
        #       .   .   .

        xOff = self.offset_x

        points = [
            "(Character: 6)",
            "fast",
            (4 + xOff, 9),
            "on",
            "slow",
            (2 + xOff, 9),
            (0 + xOff, 7),
            (0 + xOff, 1),
            (1 + xOff, 0),
            (3 + xOff, 0),
            (4 + xOff, 2),
            (4 + xOff, 3),
            (2 + xOff, 5),
            (0 + xOff, 4),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def seven(self):
        #   .               .
        #
        #
        #
        #
        #
        #
        #
        #
        #   .

        xOff = self.offset_x

        points = [
            "fast",
            "(Character: 7)",
            (0 + xOff, 0),
            "on",
            "slow",
            (4 + xOff, 9),
            (0 + xOff, 9),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def eight(self):
        #       .       .
        #   .               .
        #   .               .
        #   .               .
        #       .       .
        #   .               .
        #   .               .
        #   .               .
        #   .               .
        #       .   .   .

        xOff = self.offset_x

        points = [
            "(Character: 8)",
            "fast",
            (2 + xOff, 0),
            "on",
            "slow",
            (3 + xOff, 0),
            (4 + xOff, 1),
            (4 + xOff, 4),
            (3 + xOff, 5),
            (1 + xOff, 5),
            (0 + xOff, 6),
            (0 + xOff, 8),
            (1 + xOff, 9),
            (3 + xOff, 9),
            (4 + xOff, 8),
            (4 + xOff, 6),
            (3 + xOff, 5),
            (1 + xOff, 5),
            (0 + xOff, 4),
            (0 + xOff, 1),
            (1 + xOff, 0),
            (3 + xOff, 0),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def nine(self):
        #       .       .
        #
        #   .               .
        #
        #                   .
        #       .           .
        #                   .
        #                   .
        #                   .
        #                   .

        xOff = self.offset_x

        points = [
            "(Character: 9)",
            "fast",
            (4 + xOff, 0),
            "on",
            "slow",
            (4 + xOff, 7),
            (3 + xOff, 9),
            (1 + xOff, 9),
            (0 + xOff, 7),
            (1 + xOff, 4),
            (4 + xOff, 4),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def zero(self):
        #       .   .   .
        #   .               .
        #   .               .
        #   .               .
        #   .               .
        #   .               .
        #   .               .
        #   .               .
        #   .               .
        #       .   .   .

        xOff = self.offset_x

        points = [
            "(Character: 0)",
            "fast",
            (0 + xOff, 1),
            "on",
            "slow",
            (0 + xOff, 8),
            (1 + xOff, 9),
            (3 + xOff, 9),
            (4 + xOff, 8),
            (4 + xOff, 1),
            (3 + xOff, 0),
            (1 + xOff, 0),
            (0 + xOff, 1),
            "off",
            "fast",
        ]

        self.appendPoints(points)

    # d8888b. db    db d8b   db  .o88b. d888888b db    db  .d8b.  d888888b d888888b  .d88b.  d8b   db
    # 88  `8D 88    88 888o  88 d8P  Y8 `~~88~~' 88    88 d8' `8b `~~88~~'   `88'   .8P  Y8. 888o  88
    # 88oodD' 88    88 88V8o 88 8P         88    88    88 88ooo88    88       88    88    88 88V8o 88
    # 88~~~   88    88 88 V8o88 8b         88    88    88 88~~~88    88       88    88    88 88 V8o88
    # 88      88b  d88 88  V888 Y8b  d8    88    88b  d88 88   88    88      .88.   `8b  d8' 88  V888
    # 88      ~Y8888P' VP   V8P  `Y88P'    YP    ~Y8888P' YP   YP    YP    Y888888P  `Y88P'  VP   V8P

    # Template
    #   0   1   2   3   4  5
    # 9
    # 8
    # 7
    # 6
    # 5
    # 4
    # 3
    # 2
    # 1
    # 0

    def percentage(self):
        #   0   1   2   3   4   5   6
        # 9      o
        # 8  o       o               o
        # 7  o       o           o
        # 6      o           o
        # 5              o
        # 4          o
        # 3      o            o
        # 2  o            o        o
        # 1               o        o
        # 0                   o

        points = [
            "(Character: %)",
            "fast",
            (self.offset_x + 0, 7),  # Position for upper circle
            "on",
            "slow",
            (self.offset_x + 0, 8),  # Upper circle
            (self.offset_x + 1, 9),  # Upper circle
            (self.offset_x + 2, 8),  # Upper circle
            (self.offset_x + 2, 7),  # Upper circle
            (self.offset_x + 1, 6),  # Upper circle
            (self.offset_x + 0, 7),  # Upper circle
            "off",
            "fast",
            (self.offset_x + 0, 2),  # Position for up stroke
            "on",
            "slow",
            (self.offset_x + 5, 8),  # Up stroke
            "off",
            "fast",
            (self.offset_x + 0 + 3, 7 - 7),  # Position for lower circle
            "on",
            "slow",
            (self.offset_x + 0 + 3, 8 - 6),  # Lower circle
            (self.offset_x + 1 + 3, 9 - 6),  # Lower circle
            (self.offset_x + 2 + 3, 8 - 6),  # Lower circle
            (self.offset_x + 2 + 3, 7 - 6),  # Lower circle
            (self.offset_x + 1 + 3, 6 - 6),  # Lower circle
            (self.offset_x + 0 + 3, 7 - 6),  # Lower circle
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def plus(self):
        #   0   1   2   3   4  5
        # 9
        # 8
        # 7          +
        # 6          +
        # 5  +   +   +   +   +
        # 4          +
        # 3          +
        # 2
        # 1
        # 0

        points = [
            "(Character: +)",
            "fast",
            (self.offset_x + 0, 5),  # Position for horiz stroke
            "on",
            "slow",
            (self.offset_x + 4, 5),  # Horizontal stroke
            "off",
            "fast",
            (self.offset_x + 2, 3),  # Position for up stroke
            "on",
            "slow",
            (self.offset_x + 2, 7),  # Up stroke
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def minus(self):
        #   0   1   2   3   4  5
        # 9
        # 8
        # 7
        # 6
        # 5  +   +   +   +   +
        # 4
        # 3
        # 2
        # 1
        # 0

        points = [
            "(Character: -)",
            "fast",
            (self.offset_x + 0, 5),  # Position for horiz stroke
            "on",
            "slow",
            (self.offset_x + 4, 5),  # Horizontal stroke
            "off",
            "fast",
        ]

        self.appendPoints(points)

    def period(self):
        #   0   1   2   3   4  5
        # 9
        # 8
        # 7
        # 6
        # 5
        # 4
        # 3
        # 2
        # 1
        # 0  o  o

        points = [
            "(Character: .)",
            "fast",
            (self.offset_x - 1.5, 0),  # Position for dot
            "on",
            "slow",
            (self.offset_x - 1, 0),  # Horizontal stroke
            "off",
            "fast",
        ]

        self.appendPoints(points)


class DocSpeedPower(Doc):
    """
    Speed & power tuning document.

    Generates a grid of squares printed at different speeds
    and laser power levels to determine the optimal combination
    for engraving or cutting.
    """

    _powers = None
    _speeds = None
    _grid = None

    # Default sizes
    _square_size = None
    _text_size = None

    def __init__(
        self,
        powers: np.array = np.linspace(10, 100, 10),
        speeds: np.array = np.linspace(500, 1500, 11),
    ):
        super().__init__()

        self._speeds = np.sort(speeds)
        self._powers = np.sort(powers)

        # Generate the document layout so it can be manipulated.
        # Grid size.  Speeds on rows, power on cols
        rows = len(self._speeds)
        cols = len(self._powers)

        # Add 1 row and 1 col for labels
        rows += 1
        cols += 1

        # Directly overwrite cell layout with our grid.
        self._grid = GridLayout(rows=rows, columns=cols)

        # Set a default cell padding
        self._grid.cell_padding_height = 1  # Assumes mm
        self._grid.cell_padding_width = 1

        # Default square size.
        self.square_size = 10

        raise NotImplementedError("Not ported to update point list implementation.")

    def GCode(self, filename: str = None):
        """
        Generates speed & power tuning G-Code document.

        Parameters
        ----------
        doc: Doc
            Document into which to inject generated G-Code.

        """

        # Generate column headers showing power values
        for col_idx, power in enumerate(self._powers):
            txt = Text(f"{round(power)}%", size_mm=self._text_size)
            txt.header = f"Power Label: {round(power)}"
            self._grid.AddChildCell(txt, row=0, column=col_idx + 1)

        # Generate row headers
        # Fastest speed first.
        for row_idx, speed in enumerate(np.flip(self._speeds)):
            txt = Text(
                f"{round(speed)}", size_mm=self._text_size
            )  # TODO: Assumes mm/min speeds
            txt.header = f"Speed Label: {round(speed)}"
            self._grid.AddChildCell(txt, row=row_idx + 1, column=0)

        # Generate print squares
        for i, speed in enumerate(np.flip(self._speeds)):
            for j, power in enumerate(self._powers):
                sq = Rectangle(
                    width=self._square_size,
                    height=self._square_size,
                    speed_print=speed,
                    laser_power=power,
                )
                sq.header = f"Power={round(power)}%, Speed={round(speed)}"
                self._grid.AddChildCell(sq, row=i + 1, column=j + 1)

        # Generate axis labels
        grid_labels = GridLayout()  # Default is 2x2
        # grid_labels.cell_padding_height = self._grid.cell_padding_height
        # grid_labels.cell_padding_width  = self._grid.cell_padding_width
        grid_labels.AddChildCell(
            Text("Power", size_mm=self._text_size), column=1, row=0
        )
        grid_labels.AddChildCell(
            Text("Speed", size_mm=self._text_size, rotation_deg=90), column=0, row=1
        )
        grid_labels.AddChildCell(self._grid, row=1, column=1)

        # Put the layout into the doc.
        self.layout.AddChild(grid_labels)

        # Update header
        # Once all elements have been added, doc size can be calculated.
        header = self.header  # In case user set a header
        header += "Speed & Power Tuning Print" + self.EOL
        sz = self.Size()
        header += f"Document size: {sz[0]:.1f},{sz[1]:.1f} " + self.EOL
        header += self.EOL
        header += f"Speeds: {self._speeds}" + self.EOL
        header += f"Powers: {self._powers}" + self.EOL
        header += self.EOL
        header += f"Square Count: {len(self._speeds)*len(self._powers)}" + self.EOL
        header += f"Square Size : {self._square_size}" + self.EOL
        self.header = header

        # Now generate the code.
        super().GCode(filename)

    @property
    def square_size(self) -> float:
        """
        Size of test pattern square.
        Setting overrides text size.
        """
        return self._square_size

    @square_size.setter
    def square_size(self, value: float):
        if value <= 0:
            raise ValueError("Square size must be positive.")

        self._square_size = value
        self.text_size = value * 0.4

    @property
    def text_size(self) -> float:
        """
        Sets height of text characters.
        """
        return self._text_size

    @text_size.setter
    def text_size(self, value: float):
        if value <= 0:
            raise ValueError("Text size must be positive.")

        self._text_size = value


class DocFocus(Doc):
    """
    Laser focusing document.

    Draws lines at specified Z-height intervals to determine
    proper Z-height for optimal focus.
    """

    _length = None
    _heights = None

    def __init__(self, heights: np.array = np.linspace(-5, 5, 11), length: float = 10):
        super().__init__()

        self._heights = np.sort(heights)  # Make sure they're in order
        self._length = length

        raise NotImplementedError("Not ported to update point list implementation.")

    def GCode(self, filename: str = None):
        """
        Generates laser focus test G-Code document.

        Parameters
        ----------
        doc: Doc
            Document into which to inject generated G-Code.

        """

        # Generate grid layout for size can be determined.
        # 2 cols: label & line
        grid = GridLayout(rows=len(self._heights), columns=2)

        # Set a default cell padding
        grid.cell_padding_height = 0.75  # Assumes mm
        grid.cell_padding_width = 1

        # Text Size
        # TODO: Make configurable with reasonable default
        txt_sz = 4

        # Fill in rows of doc
        for row, z_height in enumerate(self._heights):
            sign = ""  # Gets added automatically for negative
            if z_height > 0:
                sign = "+"
            if np.isclose(z_height, 0):
                sign = "    "  # Aligns 0.0 with signed values

            # Add label
            txt = Text(f"{sign}{z_height:.1f}", size_mm=txt_sz)
            txt.header = f"Z offset: {sign}{z_height:0.1f}"
            grid.AddChildCell(txt, column=0, row=row)

            # Add line
            line = Line(length=self._length)
            line.z = z_height
            grid.AddChildCell(line, column=1, row=row)

        # Add grid to document
        self.layout.AddChild(grid)

        # Update header
        header = self.header  # In case user set a header
        header += "Laser Focus Tuning Print" + self.EOL
        sz = self.Size()
        header += f"Document size: {sz[0]:.1f},{sz[1]:.1f} " + self.EOL
        header += self.EOL
        header += f"Heights: {self._heights}" + self.EOL
        self.header = header

        # Now generate the code.
        super().GCode(filename)


if __name__ == "__main__":
    if False:
        # Speed/power doc
        # TODO: YAML config file for print
        # TODO: Command line commands to generate prints from config files.
        doc_sp = DocSpeedPower(
            powers=np.array(range(20, 80 + 10, 10)),
            speeds=np.array(range(200, 1200 + 100, 100)),
        )
        doc_sp.square_size = 5
        power_default = 40
        doc_sp.laser_power = power_default
        doc_sp.laser_power_default = power_default

        # Geneate G-code for document.
        doc_sp.GCode()
        doc_sp.Save("speed-power-tuning.nc")

    if False:
        # Laser focus test print
        doc_fc = DocFocus()  # Default heights
        doc_fc.laser_power_default = 50
        doc_fc.speed_print = 1000
        doc_fc.GCode(filename="focus-tuning.nc")

    if False:
        if False:  # Horizontal
            name = "Horizontal"
            angle = 0
            ph = 0
            pw = 2
        else:  # Vertical
            name = "Vertical"
            angle = 90
            ph = 2
            pw = 0

        # Laser mark alignment lines into spoilboard
        doc_guide = Doc()
        doc_guide.laser_power_default = 40
        doc_guide.layout.padding_height = ph
        doc_guide.layout.padding_width = pw
        line = Line(length=150, laser_power=40, rotation=angle)
        doc_guide.layout.AddChild(line)
        doc_guide.header = f"{name} Guide Line for Spoilboard"
        doc_guide.GCode()
        doc_guide.Save(f"spoilboard-guide-{name.lower()}.nc")
