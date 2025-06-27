from datetime import date, datetime
from collections import defaultdict
from lxml import etree, objectify
import numpy as np
from virtualleaf_xml_model import VirtualLeaf_XML, Node
import math

doc = VirtualLeaf_XML("data/leaves/cambium.xml")
doc.leaf.name = "Cambium_01"
doc.leaf.date = str(date.today())
doc.leaf.simtime = 0

output_xml = "data/leaves/cambium.xml"
datadir = "/home/ardati/Data_VirtualLeaf/Cambium_01"
# Parameters
doc.parameter.set_parameter(name='datadir',value=datadir)
doc.parameter.set_parameter(name='maxt',value="10000")

# Settings
doc.settings.set_setting(name='save_movie_frames',value="true")

# Add random target_length to each node
import random

print("Adding random target_length (2.0-2.5) to each node...")
for node in doc.nodes.nodes:
    # Generate random value between 2.0 and 2.5
    random_length = random.uniform(2.0, 2.5)
    # Set the attribute on the node element
    node.elem.set("target_length", f"{random_length:.6g}")

# ── housekeeping and save ────────────────────────────────────────────────
objectify.deannotate(doc.root, cleanup_namespaces=True)
etree.indent(doc.tree, space="   ")
doc.save(output_xml)


#
#
# # Other
# double_mesh = False
#
# coords = {n.nr: (n.x, n.y) for n in doc.nodes.nodes}
# # add at the top of the script, near the imports, for convenience
# id2node = {n.nr: n for n in doc.nodes.nodes}   # nr → Node dataclass
# nodes_elem = doc.nodes.elem
# next_nr = max(coords) + 1
#
#
# if double_mesh:
#     # ── STEP 1 & 2 – global edge dictionary ──────────────────────────────────
#     edge2mid = {}   # { (min(a,b), max(a,b)) : mid_id }
#
#     for cell in doc.cells.cells:
#         verts = cell.vertices
#         for a, b in zip(verts, verts[1:] + verts[:1]):       # closed ring
#             key = tuple(sorted((a, b)))
#             if key in edge2mid:
#                 continue                                    # midpoint already made
#
#             # ----------------------------------------------------------------------
#             # create ONE midpoint node for this geometric edge  (shared by both cells)
#             # ----------------------------------------------------------------------
#             x1, y1 = coords[a];
#             x2, y2 = coords[b]
#             mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
#
#             na, nb = id2node[a], id2node[b]  # Node dataclasses
#
#             sam_flag = na.sam and nb.sam  # TRUE only if both endpoints
#             boundary_flag = na.boundary and nb.boundary  # are TRUE
#             fixed_flag = na.fixed and nb.fixed
#
#             new_node_elem = etree.Element(
#                 "node",
#                 nr=str(next_nr),
#                 x=f"{mx:.6g}",
#                 y=f"{my:.6g}",
#                 sam="true" if sam_flag else "false",
#                 boundary="true" if boundary_flag else "false",
#                 fixed="true" if fixed_flag else "false",
#             )
#
#             nodes_elem.append(new_node_elem)
#             new_nd = Node(next_nr, mx, my, sam_flag, boundary_flag, fixed_flag, new_node_elem)
#             doc.nodes.nodes.append(new_nd)
#             id2node[next_nr] = new_nd  # keep lookup in sync
#             coords[next_nr] = (mx, my)
#             edge2mid[key] = next_nr
#             next_nr += 1
#
#     # ── STEP 3 & 4 – rebuild every cell with shared midpoints ────────────────
#     indent_tail = "\n         "
#
#     for cell in doc.cells.cells:
#         old_ring = cell.vertices
#         new_ring = []
#
#         for a, b in zip(old_ring, old_ring[1:] + old_ring[:1]):
#             new_ring.append(a)
#             new_ring.append(edge2mid[tuple(sorted((a, b)))])
#
#         cell.vertices = new_ring  # keep Python object in sync
#
#         # keep the walls to re-attach later
#         walls = cell.elem.xpath("./wall")
#
#         # 2) remove every existing child exactly once
#         for child in list(cell.elem.getchildren()):  # make a real Python list first
#             cell.elem.remove(child)  # no duplicates → no ValueError
#
#         # --------------------------------------------------------------------------
#         # 3) choose a geometry-aware sort key  ←  REPLACE THIS SINGLE LINE
#         # --------------------------------------------------------------------------
#
#         # OLD (pure numeric, gave ugly ordering):
#         # for idx in sorted(set(new_ring)):
#
#         # NEW (angle about cell centroid):
#         vx, vy = zip(*(coords[i] for i in new_ring))  # coordinates of vertices
#         cx, cy = sum(vx) / len(vx), sum(vy) / len(vy)  # centroid
#
#
#         def polar_angle(i):
#             x, y = coords[i]
#             return math.atan2(y - cy, x - cx)
#
#
#         for idx in sorted(set(new_ring), key=polar_angle):
#             n_elem = etree.SubElement(cell.elem, "node", n=str(idx))
#             n_elem.tail = indent_tail
#
#         # re-attach walls
#         for w in walls:
#             cell.elem.append(w)
#             w.tail = indent_tail


# # ──────────────────────────────────────────────────────────────────────────
# #  SORT CELLS BY (radius, angle)   →   re-assign sequential indices
# # --------------------------------------------------------------------------
# 1)  centroid of the *whole* tissue  – average of all node coords
# tx, ty = np.mean(list(coords.values()), axis=0)
#
# # ───────────────────────────────────────────────────────────────────────────
# #  CLUSTER + RADIAL-ANGULAR SORT → reassign cell.index & cell.id
# # ───────────────────────────────────────────────────────────────────────────
# def kmeans1d(points: np.ndarray, k: int, max_iter: int = 100):
#     """
#     Very simple 1-D k-means clustering.
#     Returns
#     -------
#     labels : np.ndarray of shape (n,)
#         label in [0..k-1] for each point
#     centers : np.ndarray of shape (k,)
#         the final cluster centers
#     """
#     pts = points.copy()
#     # init centers evenly
#     centers = np.linspace(pts.min(), pts.max(), k)
#     for _ in range(max_iter):
#         # assign to nearest center
#         dists = np.abs(pts[:, None] - centers[None, :])
#         labels = np.argmin(dists, axis=1)
#         new_centers = np.array([
#             pts[labels == i].mean() if np.any(labels==i) else centers[i]
#             for i in range(k)
#         ])
#         if np.allclose(new_centers, centers):
#             break
#         centers = new_centers
#     # final assignment
#     dists = np.abs(pts[:, None] - centers[None, :])
#     labels = np.argmin(dists, axis=1)
#     return labels, centers
#
# # 1) compute (radius, angle) for each cell, keep original order
# cell_info = []   # will hold tuples (radius, angle, cell)
# radii = []
# for c in doc.cells.cells:
#     # centroid of the cell
#     vx, vy = zip(*(coords[i] for i in c.vertices))
#     cx, cy = sum(vx)/len(vx), sum(vy)/len(vy)
#     # vector from tissue center
#     # tissue center = mean of ALL node coords (or use weighted centroid if you prefer)
#     dx, dy = cx - tx, cy - ty
#     r = math.hypot(dx, dy)
#     θ = math.atan2(dy, dx)
#     cell_info.append((r, θ, c))
#     radii.append(r)
#
# radii = np.array(radii)
#
# # 2) cluster radii into k rings
# k = 3  # <-- set this to the number of concentric rings you expect
# labels, centers = kmeans1d(radii, k)
#
# # reorder cluster IDs so that label "0" is the innermost center, etc.
# order = np.argsort(centers)                  # e.g. [2,0,1] if center-radii say [84,1,54]
# cluster_rank = {old: new for new, old in enumerate(order)}
# ranks = np.array([cluster_rank[l] for l in labels])
#
# # 3) build a list of (ring, angle, cell) and sort
# clustered = [
#     (ranks[i], cell_info[i][1], cell_info[i][2])
#     for i in range(len(cell_info))
# ]
# clustered.sort(key=lambda t: (t[0], t[1]))   # first by ring, then CCW angle
#
# # 4) reassign indices in that new order - innermost gets highest index
# total_cells = len(doc.cells.cells)
# for i, (ring, angle, c) in enumerate(clustered):
#     # Reverse the indexing: innermost cells (ring 0) get highest indices
#     new_idx = total_cells - 1 - i  # Counts down from (total_cells-1)
#     c.elem.attrib["index"] = str(new_idx)
#     if "id" in c.elem.attrib:
#         c.elem.attrib["id"] = str(new_idx)
# ────────────────────────────────────────────────────────────────────────────
#  Reorder <cell> tags under <cells> to match their 'index' attribute
# ────────────────────────────────────────────────────────────────────────────

# cells_parent = doc.root.find("cells")                # top-level <cells> element
# all_cells    = list(cells_parent.findall("cell"))    # snapshot of originals
#
# # sort the Element proxies by their integer index
# sorted_cells = sorted(
#     all_cells,
#     key=lambda c: int(c.attrib.get("index", c.attrib.get("id", 0)))
# )
#
# # remove all originals in one pass
# for c in all_cells:
#     cells_parent.remove(c)
#
# # append back in the new order
# for c in sorted_cells:
#     cells_parent.append(c)
# #
# # ────────────────────────────────────────────────────────────────────────────
# #  COMPUTE & ATTACH  target_length  TO  <nodes>
# # ────────────────────────────────────────────────────────────────────────────
#
# # 1) collect unique edges from *refined* cells
# edge_set = set()
# for c in doc.cells.cells:
#     verts = c.vertices
#     for a, b in zip(verts, verts[1:] + verts[:1]):  # closed loop
#         edge_set.add(tuple(sorted((a, b))))
#
# # 2) compute lengths
# lengths = []
# for a, b in edge_set:
#     x1, y1 = coords[a]
#     x2, y2 = coords[b]
#     lengths.append(math.hypot(x2 - x1, y2 - y1))
#
# # 3) mean segment length and target length (half of mean)
# mean_len = sum(lengths) / len(lengths) if lengths else 0.0
# target_len = mean_len/2
# print(f"Mean segment length: {mean_len:.6g}")
# print(f"Target length (half mean): {target_len:.6g}")
# # 4) attach as attribute on <nodes>
# nodes_elem.attrib["target_length"] = f"{target_len:.6g}"
# # 5) add the new number of nodes to the <nodes> element
# nodes_elem.attrib["n"] = str(len(doc.nodes.nodes))
# #
# # ────────────────────────────────────────────────────────────────────────────
# #  RESET  <boundary_polygon>  CHILDREN TO THE REFINED BOUNDARY LOOP
# # ────────────────────────────────────────────────────────────────────────────
#
# # 1) find the boundary_polygon element
# poly = doc.cells.elem.find("boundary_polygon")
# if poly is None:
#     raise RuntimeError("No <boundary_polygon> found under <cells>.")
#
# # 2) collect all nodes flagged boundary="true"
# b_nodes = [n for n in doc.nodes.nodes if n.boundary]
#
# # 3) sort them CCW around tissue centre (tx,ty from before)
# def angle_about_center(node):
#     x, y = node.x, node.y
#     return math.atan2(y - ty, x - tx)
#
# b_nodes.sort(key=angle_about_center)
#
# # 4) wipe existing children and append fresh <node n="…"/> entries
# for ch in list(poly.getchildren()):
#     poly.remove(ch)
#
# tail = "\n         "    # matches the indent in your file
# for n in b_nodes:
#     elem = etree.SubElement(poly, "node", n=str(n.nr))
#     elem.tail = tail
#
# # reposition the boundary polygon
# cells_elem = doc.root.find("cells")
# poly = cells_elem.find("boundary_polygon")
# if poly is not None:
#     cells_elem.remove(poly)
#     cells_elem.append(poly)
#
#
# # ────────────────────────────────────────────────────────────────────────────
# # REBUILD WALLS AS CONTIGUOUS SEGMENTS BETWEEN CELL PAIRS
# # ────────────────────────────────────────────────────────────────────────────
#
#
# # 1) locate and clear the existing walls
# walls_parent = doc.root.find("walls")
# for w in list(walls_parent.getchildren()):
#     walls_parent.remove(w)
#
# # 2) collect every undirected edge → the two cells sharing it
# edge2cells: dict[tuple[int,int], list[int]] = {}
# for c in doc.cells.cells:
#     ci    = int(c.elem.get("index"))
#     verts = c.vertices
#     for a, b in zip(verts, verts[1:] + verts[:1]):
#         key = tuple(sorted((a, b)))
#         edge2cells.setdefault(key, []).append(ci)
#
# # 3) group edges by the pair of cells (interior walls only)
# pair2edges: dict[tuple[int,int], list[tuple[int,int]]] = {}
# for edge, cells in edge2cells.items():
#     if len(cells) == 2:
#         pair2edges.setdefault(tuple(sorted(cells)), []).append(edge)
#
# new_walls = []
#
# for (c1, c2), edges in pair2edges.items():
#     # build adjacency for this wall
#     adj: dict[int, list[int]] = defaultdict(list)
#     for u, v in edges:
#         adj[u].append(v)
#         adj[v].append(u)
#
#     # find endpoints (degree == 1)
#     endpoints = [n for n, nbrs in adj.items() if len(nbrs) == 1]
#     if len(endpoints) == 2:
#         start, end = endpoints
#     else:
#         # fallback: pick the first edge’s nodes
#         start, end = edges[0]
#
#     # traverse from start to end
#     ordered = [start]
#     prev, curr = None, start
#     while curr != end:
#         nbrs = adj[curr]
#         # pick the neighbor that isn’t the previous node
#         nxt = nbrs[0] if nbrs[0] != prev else nbrs[1]
#         ordered.append(nxt)
#         prev, curr = curr, nxt
#
#     # compute total wall length
#     length = 0.0
#     for u, v in zip(ordered, ordered[1:]):
#         x1, y1 = coords[u]
#         x2, y2 = coords[v]
#         length += math.hypot(x2 - x1, y2 - y1)
#
#     # emit the <wall> element
#     w = etree.SubElement(walls_parent, "wall",
#         length=f"{length:.6g}",
#         c1=str(c1), c2=str(c2),
#         n1=str(ordered[0]), n2=str(ordered[-1]),
#         wall_type="normal",
#         viz_flux="0"
#     )
#     # ─── Add the transporter tags ───────────────────────────────────
#     etree.SubElement(w, "transporters1")
#     etree.SubElement(w, "transporters2")
#
#     new_walls.append(w)
#
# # 4) assign sequential indices and refresh the count
# for idx, w in enumerate(new_walls):
#     w.set("index", str(idx))
# walls_parent.set("n", str(len(new_walls)))
#
#
# # ──────────────────────────────────────────────────────────────────────────
# # FINAL SORT: reorder <wall> tags by c1, then reindex & recount
# # ──────────────────────────────────────────────────────────────────────────
# walls_parent = doc.root.find("walls")
#
# # 1) snapshot and sort by integer c1
# orig_walls = list(walls_parent.findall("wall"))
# sorted_walls = sorted(orig_walls, key=lambda w: int(w.get("c1", 0)))
#
# # 2) remove all originals
# for w in orig_walls:
#     walls_parent.remove(w)
#
# # 3) append back in sorted order
# for w in sorted_walls:
#     walls_parent.append(w)
#
# # 4) reassign sequential index and refresh count
# for idx, w in enumerate(walls_parent.findall("wall")):
#     w.set("index", str(idx))
# walls_parent.set("n", str(len(walls_parent.findall("wall"))))
#
#
#
#
# # ────────────────────────────────────────────────────────────────────────────
# # REINDEX NODES BY FIRST APPEARANCE IN CELLS  →  new 0..M-1 ordering
# # ────────────────────────────────────────────────────────────────────────────
# from lxml import etree
#
# # 1) build mapping old_nr → new_nr by scanning cells
# mapping: dict[int,int] = {}
# next_id = 0
# for cell in doc.cells.cells:
#     for old_nr in cell.vertices:
#         if old_nr not in mapping:
#             mapping[old_nr] = next_id
#             next_id += 1
#
# # print(f"mapping: {mapping}")
# # 2) any nodes not in any cell (e.g. orphan or boundary_poly) come last
# for n in doc.nodes.nodes:
#     old_nr = n.nr
#     if old_nr not in mapping:
#         mapping[old_nr] = next_id
#         next_id += 1
#
# # 3) reorder & rename <node> elements under <nodes>
# nodes_parent = doc.root.find("nodes")
# orig_nodes   = {int(elem.get("nr")): elem for elem in nodes_parent.findall("node")}
#
# # clear existing
# for elem in list(nodes_parent.getchildren()):
#     nodes_parent.remove(elem)
#
# # append back in new order
# for old_nr, new_nr in sorted(mapping.items(), key=lambda kv: kv[1]):
#     elem = orig_nodes[old_nr]
#     elem.set("nr", str(new_nr))
#     elem.tail = "\n      "
#     nodes_parent.append(elem)
#
# # 4) rebuild coords and doc.nodes.nodes list
# new_coords = {}
# new_node_list = []
# for elem in nodes_parent.findall("node"):
#     nr = int(elem.get("nr"))
#     x, y = float(elem.get("x")), float(elem.get("y"))
#     sam = elem.get("sam") == "true"
#     boundary = elem.get("boundary") == "true"
#     fixed = elem.get("fixed") == "true"
#     new_coords[nr] = (x, y)
#     new_node_list.append(Node(nr, x, y, sam, boundary, fixed, elem))
# coords.clear(); coords.update(new_coords)
# doc.nodes.nodes[:] = new_node_list
#
# # 5) remap every cell’s membership list (Python + XML)
# for cell in doc.cells.cells:
#     old_verts = cell.vertices
#     new_verts = [mapping[old] for old in old_verts]
#     cell.vertices = new_verts
#     # update XML <node n="…"/>
#     for n_elem in cell.elem.findall("node"):
#         old = int(n_elem.get("n"))
#         n_elem.set("n", str(mapping[old]))
#
# # 6) remap every wall’s endpoints n1/n2
# walls_parent = doc.root.find("walls")
# for w in walls_parent.findall("wall"):
#     for attr in ("n1", "n2"):
#         old = int(w.get(attr))
#         w.set(attr, str(mapping[old]))
#
#
#
# # ────────────────────────────────────────────────────────────────────────────
# #  RESET  <boundary_polygon>  CHILDREN TO THE REFINED BOUNDARY LOOP
# # ────────────────────────────────────────────────────────────────────────────
#
# # 1) find the boundary_polygon element
# poly = doc.cells.elem.find("boundary_polygon")
# if poly is None:
#     raise RuntimeError("No <boundary_polygon> found under <cells>.")
#
# # 2) collect all nodes flagged boundary="true"
# b_nodes = [n for n in doc.nodes.nodes if n.boundary]
#
# # 3) sort them CCW around tissue centre (tx,ty from before)
# def angle_about_center(node):
#     x, y = node.x, node.y
#     return math.atan2(y - ty, x - tx)
#
# b_nodes.sort(key=angle_about_center)
#
# # 4) wipe existing children and append fresh <node n="…"/> entries
# for ch in list(poly.getchildren()):
#     poly.remove(ch)
#
# tail = "\n         "    # matches the indent in your file
# for n in b_nodes:
#     elem = etree.SubElement(poly, "node", n=str(n.nr))
#     elem.tail = tail
#
# # reposition the boundary polygon
# cells_elem = doc.root.find("cells")
# poly = cells_elem.find("boundary_polygon")
# if poly is not None:
#     cells_elem.remove(poly)
#     cells_elem.append(poly)
#
#
# # ▶︎ 1) map each cell to its incident walls
# cell2walls: dict[int, list[int]] = defaultdict(list)
# walls_parent = doc.root.find("walls")
#
# for w in walls_parent.findall("wall"):
#     idx = int(w.get("index"))
#     c1  = int(w.get("c1"))
#     c2  = int(w.get("c2"))
#     cell2walls[c1].append(idx)
#     cell2walls[c2].append(idx)
#
# # ▶︎ 2) rewrite each cell’s <wall> children
# for cell in doc.cells.cells:
#     ci = int(cell.elem.get("index"))
#     # remove all existing <wall> tags
#     for w_elem in cell.elem.findall("wall"):
#         cell.elem.remove(w_elem)
#
#     # append new ones in sorted order
#     for widx in sorted(cell2walls.get(ci, [])):
#         we = etree.SubElement(cell.elem, "wall", w=str(widx))
#         we.tail = "\n         "  # match your cell indentation
#


# # ── housekeeping and save ────────────────────────────────────────────────
# objectify.deannotate(doc.root, cleanup_namespaces=True)
# etree.indent(doc.tree, space="   ")
# doc.save(output_xml)
