"""
virtualleaf_xml_model.py
Comprehensive objectification of the VirtualLeaf tissue XML format
(5 main blocks: parameter, nodes, cells, walls, settings).
Author: Rami Ardati · 2025-05-09
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Union, Optional, Any

from lxml import etree, objectify


# ─────────────────────────────────────────────────────────────────────────────
# Helper conversions
# ─────────────────────────────────────────────────────────────────────────────
def _to_float_if_num(s: str) -> Union[int, float, str]:
    try:
        i = int(s); return i
    except ValueError:
        try:
            f = float(s); return f
        except ValueError:
            return s


def _to_bool(s: str | None, default: bool = False) -> bool:
    if s is None:
        return default
    return s.lower() in ("true", "1", "yes")

# ─────────────────────────────────────────────────────────────────────────────
# 0)  Leaf section
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class LeafSection:
    """
    Wrapper around the <leaf> root element,
    exposing its 'name', 'date', and 'simtime' attributes.
    """
    elem: objectify.ObjectifiedElement = field(repr=False)

    @property
    def name(self) -> str:
        """Return the leaf’s name."""
        return self.elem.attrib.get("name", "")

    @name.setter
    def name(self, new_name: str) -> None:
        """Set the leaf’s name."""
        self.elem.attrib["name"] = new_name

    @property
    def date(self) -> str:
        """Return the leaf’s date (YYYY-MM-DD)."""
        return self.elem.attrib.get("date", "")

    @date.setter
    def date(self, new_date: str) -> None:
        """Set the leaf’s date (YYYY-MM-DD)."""
        self.elem.attrib["date"] = new_date

    @property
    def simtime(self) -> float:
        """Return the leaf’s simulation time."""
        return float(self.elem.attrib.get("simtime", "0"))

    @simtime.setter
    def simtime(self, new_time: Union[float, int, str]) -> None:
        """Set the leaf’s simulation time."""
        self.elem.attrib["simtime"] = str(new_time)




# ─────────────────────────────────────────────────────────────────────────────
# 1)  Parameter section
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Parameter:
    name: str
    value: Union[int, float, str, List[float]]
    elem: objectify.ObjectifiedElement = field(repr=False)


@dataclass
class ParameterSection:
    """
    Wrapper around the ``<parameter>`` XML block.

    Implements container-like behaviour so that you can:

    * Get number of parameters with ``len()``
    * Iterate over Parameter objects with a for loop
    * List all parameter names with ``names()`` method

    Examples:
        # Assuming 'model' is a VirtualLeaf_XML instance:
        model.parameter.names()        # liste les noms de paramètres
        len(model.parameter)           # nombre de paramètres
        for p in model.parameter:      # itère sur les objets Parameter
            print(p.name, p.value)
    """
    elem: objectify.ObjectifiedElement = field(repr=False)
    parameters: List[Parameter] = field(init=False)

    # ─── Construction ────────────────────────────────────────────────────
    def __post_init__(self):
        self.parameters = []
        for par in self.elem.xpath("./par"):
            if "val" in par.attrib:                                # scalar
                val = _to_float_if_num(par.attrib["val"])
            else:                                                  # array
                vals = [float(v.attrib["v"]) for v in par.xpath("./valarray/val")]
                if not vals:
                    text = par.xpath("./valarray/text()")
                    vals = [float(tok) for tok in text[0].split()] if text else []
                val = vals
            self.parameters.append(Parameter(par.attrib.get("name", ""), val, par))

    # ─── Python-container conveniences ───────────────────────────────────
    def __len__(self) -> int:
        """Return the total number of parameters."""
        return len(self.parameters)

    def __iter__(self):
        """Iterate over :class:`Parameter` objects in their XML order."""
        return iter(self.parameters)

    def names(self) -> List[str]:
        """
        Return a list with all parameter *names* in the order they appear
        in the XML.

        :rtype: list[str]
        """
        return [p.name for p in self.parameters]

    # (existing get_*/set_* helpers stay unchanged below)
    # ──────────────────────────────────────────────────────────────────────
    def get_parameter(self, name: str) -> Optional[Union[int, float, str]]:
        for p in self.parameters:
            if p.name == name and not isinstance(p.value, list):
                return p.value
        return None

    def set_parameter(self, name: str, value: Union[int, float, str]) -> None:
        for p in self.parameters:
            if p.name == name and not isinstance(p.value, list):
                p.value = value
                p.elem.attrib["val"] = str(value)
                return
        # create new
        new_par = objectify.Element("par", name=name, val=str(value))
        self.elem.append(new_par)
        self.parameters.append(Parameter(name, value, new_par))

    def get_parameter_array(self, name: str) -> Optional[List[float]]:
        for p in self.parameters:
            if p.name == name and isinstance(p.value, list):
                return p.value
        return None

    def set_parameter_array(self, name: str, values: List[float]) -> None:
        for p in self.parameters:
            if p.name == name and isinstance(p.value, list):
                p.value[:] = values
                # rebuild child list
                va = p.elem.xpath("./valarray")
                va_elem = va[0] if va else objectify.SubElement(p.elem, "valarray")
                va_elem.clear()
                for v in values:
                    objectify.SubElement(va_elem, "val", v=f"{v:.6g}")
                return
        # create new
        par_elem = objectify.Element("par", name=name)
        va_elem = objectify.SubElement(par_elem, "valarray")
        for v in values:
            objectify.SubElement(va_elem, "val", v=f"{v:.6g}")
        self.elem.append(par_elem)
        self.parameters.append(Parameter(name, values, par_elem))


# ─────────────────────────────────────────────────────────────────────────────
# 2)  Node section
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Node:
    nr: int
    x: float
    y: float
    sam: bool
    boundary: bool
    fixed: bool
    elem: objectify.ObjectifiedElement = field(repr=False)


@dataclass
class NodeSection:
    elem: objectify.ObjectifiedElement = field(repr=False)
    nodes: List[Node] = field(init=False)

    def __post_init__(self):
        self.nodes = [
            Node(
                nr=int(n.attrib["nr"]),
                x=float(n.attrib["x"]),
                y=float(n.attrib["y"]),
                sam=_to_bool(n.attrib.get("sam")),
                boundary=_to_bool(n.attrib.get("boundary")),
                fixed=_to_bool(n.attrib.get("fixed")),
                elem=n,
            )
            for n in self.elem.xpath("./node")
        ]

    def get_by_nr(self, nr: int) -> Optional[Node]:
        return next((n for n in self.nodes if n.nr == nr), None)

    def __len__(self) -> int:
        return len(self.nodes)


# ─────────────────────────────────────────────────────────────────────────────
# 3)  Cell section
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Cell:
    id: int
    attributes: Dict[str, Any]
    vertices: List[int]
    elem: objectify.ObjectifiedElement = field(repr=False)

    # Common shorthands
    @property
    def area(self) -> float:
        return float(self.attributes.get("area", 0.0))

    @property
    def cell_type(self) -> int:
        return int(self.attributes.get("cell_type", 0))


@dataclass
class CellSection:
    elem: objectify.ObjectifiedElement = field(repr=False)
    cells: List[Cell] = field(init=False)

    def __post_init__(self):
        def collect_vertices(c) -> List[int]:
            """Return the ordered list of node indices that bound this cell."""
            verts: List[int] = []

            # format <node n="42"/>
            for v in c.xpath("./node[@n]"):
                verts.append(int(v.attrib["n"]))

            return verts

        # ─── build cell list ────────────────────────────────────────────
        self.cells = []
        for c in self.elem.xpath("./cell"):
            verts = collect_vertices(c)
            self.cells.append(
                Cell(
                    id=int(c.attrib.get("id", c.attrib.get("nr", 0))),
                    attributes=dict(c.attrib),
                    vertices=verts,
                    elem=c,
                )
            )
    def __len__(self):
        return len(self.cells)


# ─────────────────────────────────────────────────────────────────────────────
# 4)  Wall section (minimal)
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Wall:
    id: int
    attributes: Dict[str, Any]
    elem: objectify.ObjectifiedElement = field(repr=False)


@dataclass
class WallSection:
    elem: objectify.ObjectifiedElement = field(repr=False)
    walls: List[Wall] = field(init=False)

    def __post_init__(self):
        self.walls = [
            Wall(id=i, attributes=dict(w.attrib), elem=w)
            for i, w in enumerate(self.elem.xpath("./wall"))
        ]

    def __len__(self):
        return len(self.walls)


# ─────────────────────────────────────────────────────────────────────────────
# 5)  Settings section
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Setting:
    name: str
    value: Union[int, float, str]
    elem: objectify.ObjectifiedElement = field(repr=False)


@dataclass
class SettingsSection:
    elem: objectify.ObjectifiedElement = field(repr=False)
    settings: List[Setting] = field(init=False)

    def __post_init__(self):
        self.settings = [
            Setting(k.attrib["name"], _to_float_if_num(k.attrib["val"]), k)
            for k in self.elem.xpath("./setting")
        ]

    def get_setting(self, name: str) -> Optional[Union[str, int, float]]:
        """Get a setting value by its name."""
        for s in self.settings:
            if s.name == name:
                return s.value
        return None

    def set_setting(self, name: str, value: Union[str, int, float]) -> None:
        """Set a setting value by name, or create if it doesn't exist."""
        # Try to find existing setting
        for s in self.settings:
            if s.name == name:
                s.value = value
                s.elem.attrib["val"] = str(value)
                return

        # Create new setting if not found
        new_elem = objectify.Element("setting", name=name, val=str(value))
        self.elem.append(new_elem)
        self.settings.append(Setting(name, value, new_elem))


# ─────────────────────────────────────────────────────────────────────────────
# 6)  High-level façade
# ─────────────────────────────────────────────────────────────────────────────
class VirtualLeaf_XML:
    """
    Reads the XML once and exposes sections:
        .leaf       – LeafSection
        .parameter  – ParameterSection
        .nodes      – NodeSection
        .cells      – CellSection
        .walls      – WallSection
        .settings   – SettingsSection
    """
    def __init__(self, path: str):
        self.path = path
        parser = objectify.makeparser(remove_blank_text=False)
        self.tree = objectify.parse(path, parser)
        self.root = self.tree.getroot()

        # Wrap the <leaf> element (the document root)
        self.leaf      = LeafSection(self.root)

        # Existing sections
        self.parameter = ParameterSection(self.root.find("parameter"))
        self.nodes     = NodeSection(self.root.find("nodes"))
        self.cells     = CellSection(self.root.find("cells"))
        self.walls     = WallSection(self.root.find("walls"))
        self.settings  = SettingsSection(self.root.find("settings"))

    def save(self, outfile: Optional[str] = None):
        print(f"Saving to {outfile or self.path}")
        self.tree.write(
            outfile or self.path,
            pretty_print=True,
            encoding="UTF-8",
            xml_declaration=True,
            standalone=False,
        )

    def __repr__(self):
        return (
            f"VirtualLeaf_XML('{self.path}', "
            f"leaf='{self.leaf.name}', date='{self.leaf.date}', simtime={self.leaf.simtime}, "
            f"{len(self.nodes)} nodes, {len(self.cells)} cells, {len(self.walls)} walls)"
        )