from datetime import date, datetime
from collections import defaultdict
from lxml import etree, objectify
import numpy as np
from virtualleaf_xml_model import VirtualLeaf_XML, Node
import math
from test_XML import generer_donnees

doc = VirtualLeaf_XML("data/leaves/cambium.xml")
doc.leaf.name = "Cambium_New"
doc.leaf.date = str(date.today())
doc.leaf.simtime = 0

output_xml = "data/leaves/cambium_new.xml"
datadir = "/home/rojas/Cambium_New01"
# Parameters
doc.parameter.set_parameter(name='datadir',value=datadir)
doc.parameter.set_parameter(name='maxt',value="10000")


#Remove nodes, cells, walls



# Remove Nodes
nodes_parent = doc.root.find("nodes")
for node in list(nodes_parent.findall("node")):
    nodes_parent.remove(node)


 # Récupérer les noeuds et cellules générés
k_noeuds_n_cercle_cartesien_raffine, cellules, liste_walls, basearea = generer_donnees()
print("liste noeuds : ",k_noeuds_n_cercle_cartesien_raffine,"\n")
print("nombre éléments noeuds : ",len(k_noeuds_n_cercle_cartesien_raffine))

# Dictionnaire pour stocker les coordonnées des noeuds
coords = {}
next_nr = 0  # compteur pour les indices de noeuds

# Ajouter tous les noeuds au XML
for noeud in k_noeuds_n_cercle_cartesien_raffine:

    # print(noeud['index'])
    mx = noeud['x']
    my = noeud['y']
    sam_flag = noeud['sam']
    boundary_flag = noeud['boundary']
    fixed_flag = noeud['fixed']
    # Créer l'élément XML pour le noeud
    new_node_elem = etree.SubElement(
        nodes_parent,
        "node",
        nr=str(noeud['index']),
        x=f"{mx:.6g}",
        y=f"{my:.6g}",
        sam=str(noeud['sam']).lower(),  # Conversion en "true" ou "false"
        boundary=str(noeud['boundary']).lower(),
        fixed=str(noeud['fixed']).lower(),
    )

    # Stocker les coordonnées pour la création des murs
    coords[next_nr] = (mx, my)
    # Ajouter à la liste de noeuds du document
    doc.nodes.nodes.append(Node(
        next_nr, mx, my, sam_flag, boundary_flag, fixed_flag, new_node_elem
    ))

    next_nr += 1


# Mettre à jour le nombre total de noeuds
nodes_parent.set("n", str(next_nr))

#----------------------------------------------------------------------------------------------------#
#------------------------- Cellules -----------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#

#------------------------Balise parent cells---------------------------------------------------------#
# Supprimer l'élément cells existant s'il existe déjà
cells_parent = doc.root.find("cells")
if cells_parent is not None:
    doc.root.remove(cells_parent)

# Créer le nouvel élément cells
cells_elem = etree.Element(
    "cells",
    n=str(len(cellules)),
    magnfication="1",
    nchem="0",
    offsetx="0",
    offsety="0",
    base_area= str(basearea)
)

# Ne pas essayer d'ajouter les dictionnaires de cellules directement ici
# Les cellules seront ajoutées plus tard avec SubElement

# Rechercher l'élément walls
walls_elem = doc.root.find("walls")

if walls_elem is not None:
    # Si walls existe, insérer cells avant walls
    parent = walls_elem.getparent()
    index = parent.index(walls_elem)
    parent.insert(index, cells_elem)
else:
    # Rechercher nodes pour insérer après
    nodes_elem = doc.root.find("nodes")
    if nodes_elem is not None:
        parent = nodes_elem.getparent()
        index = parent.index(nodes_elem)
        parent.insert(index + 1, cells_elem)
    else:
        # Si aucun repère n'est trouvé, ajouter à la fin
        doc.root.append(cells_elem)

# Mettre à jour la référence à cells dans doc
doc.cells = cells_elem

# Dictionnaire pour stocker les arêtes entre les cellules
pair2edges = defaultdict(list)



#------------------------Balise enfant Cell---------------------------------------------------------#

# Créer les cellules à partir de la variable cellules existante
for cellule in cellules:
    # Créer l'élément XML pour la cellule avec toutes les propriétés
    cell_elem = etree.SubElement(
        cells_elem,
        "cell",
        index=str(cellule["index"]),
        boundary=str(cellule["boundary"]),
        cell_type=str(cellule["cell_type"]),
        target_area=str(cellule["area"]),
        lambda_celllength=str(cellule["lambda_celllength"]),
        at_boundary="true" if cellule["at_boundary"] else "false",
        dead="true" if cellule["dead"] else "false",
        target_length=str(cellule["target_length"]),
        stiffness=str(cellule["stiffness"]),
        source="true" if cellule["source"] else "false",
        pin_fixed="true" if cellule["pin_fixed"] else "false",
        area=str(cellule["area"]),
        fixed="true" if cellule["fixed"] else "false",
        div_counter=str(cellule["div_counter"]),
    )
    cell_idx = cellule["index"]
    cell_nodes = cellule["noeuds"]
    # Ajouter les nœuds à la cellule (une seule fois)
    for i, node_id in enumerate(cell_nodes):
        # Créer l'élément nœud pour la cellule
        etree.SubElement(cell_elem, "node", n=str(node_id))

        # Enregistrer l'arête pour la création des murs
        next_node = cell_nodes[(i + 1) % len(cell_nodes)]
        if cell_idx < 0:  # Cellule externe
            pair2edges[(cell_idx, 0)].append((cellule(""), next_node))
        else:
            pair2edges[(min(cell_idx, 0), max(cell_idx, 0))].append((node_id, next_node))



#------------------------Boundary_Polygon----------------------------------------------
# Supprimer l'ancien élément walls s'il existe
boundary_polygon = doc.root.find("cell/boundary_polygon")
if boundary_polygon is not None:
    doc.root.remove(boundary_polygon)
# Créer un nouveau boundary_polygon avec les bons nœuds (uniquement ceux marqués boundary=true)
boundary_nodes = []
print("boundary nodes",boundary_nodes)
print("k_noeuds_n_cercle_cartesien_raffine",k_noeuds_n_cercle_cartesien_raffine)
for i, noeud in enumerate(k_noeuds_n_cercle_cartesien_raffine):
    # Vérification stricte: l'attribut doit être exactement True (booléen)
    if noeud.get('boundary') is True:
        boundary_nodes.append(noeud['index'])

# print(f"Nœuds de frontière détectés: {boundary_nodes}")

# Créer le boundary_polygon avec seulement ces nœuds
boundary_polygon = etree.SubElement(
    cells_elem, "boundary_polygon",
    index="-1",
    boundary="0",
    cell_type="0",
    target_area=str(basearea*len(cellules)),
    lambda_celllength="0",
    at_boundary="true",
    dead="false",
    target_length="0",
    stiffness="1",
    source="false",
    pin_fixed="false",
    area=str(basearea*len(cellules)),
    fixed="false",
    div_counter="0"
)

# Ajouter seulement les nœuds de frontière actuels au boundary_polygon
for node_nr in boundary_nodes:
    etree.SubElement(boundary_polygon, "node", n=str(node_nr))

print("boundary nodes",boundary_nodes)

#---------Walls------------------------------------------------------#


# Supprimer l'ancien élément walls s'il existe
walls_elem = doc.root.find("walls")
if walls_elem is not None:
    doc.root.remove(walls_elem)

# Créer le nouvel élément walls sans l'ajouter immédiatement au document
walls_elem = etree.Element("walls", n=str(len(liste_walls)))

# Trouver l'élément cells
cells_elem = doc.root.find("cells")
if cells_elem is None:
    # print("Erreur: élément cells non trouvé dans le document XML")
    # Créer l'élément cells si nécessaire
    cells_elem = etree.SubElement(doc.root, "cells", n="0")
else:
    # Insérer walls juste après cells
    parent = cells_elem.getparent()
    index = parent.index(cells_elem)
    parent.insert(index + 1, walls_elem)

# Regrouper les murs par cellule
walls_by_cell = defaultdict(list)
for wall in liste_walls:
    walls_by_cell[wall['c1']].append(wall['index'])
    walls_by_cell[wall['c2']].append(wall['index'])

# Ajouter les références aux murs dans chaque cellule
for cell_elem in cells_elem.findall("cell"):
    cell_idx = cell_elem.get("index")
    if cell_idx in walls_by_cell:
        for wall_idx in walls_by_cell[cell_idx]:
            etree.SubElement(cell_elem, "wall", w=str(wall_idx))

# Ajouter chaque wall avec ses attributs
for wall_data in liste_walls:
    wall = etree.SubElement(
        walls_elem, "wall",
        length=str(wall_data["length"]),
        c1=str(wall_data["c1"]),
        c2=str(wall_data["c2"]),
        n1=str(wall_data["n1"]),
        n2=str(wall_data["n2"]),
        wall_type=str(wall_data["wall_type"]),
        viz_flux=str(wall_data["viz_flux"]),
        index=str(wall_data["index"])
    )

    # Ajouter les éléments transporters (vides)
    etree.SubElement(wall, "transporters1")
    etree.SubElement(wall, "transporters2")

# print(f"{len(liste_walls)} murs ajoutés au document XML")





# Settings
doc.settings.set_setting(name='save_movie_frames',value="true")
doc.settings.set_setting(name='show_node_numbers',value="true")

# ── housekeeping and save ────────────────────────────────────────────────
objectify.deannotate(doc.root, cleanup_namespaces=True)
etree.indent(doc.tree, space="   ")
doc.save(output_xml)

print(f"Fichier XML créé avec succès: {output_xml}")
