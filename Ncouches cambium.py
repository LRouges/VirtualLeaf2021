import math
import numpy as np
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os


def generer_structure_n_cercles(nom_fichier_sortie, fichier_structure_vierge=None,
                                rayon_interne=10, nombre_cercles=3,
                                param_a=12, param_b=15):
    """
    Génère une structure à n cercles concentriques avec des rayons calculés selon les règles spécifiées.

    Args:
        nom_fichier_sortie: Chemin du fichier XML de sortie
        fichier_structure_vierge: Fichier XML vierge optionnel pour les paramètres d'affichage
        rayon_interne: Rayon du cercle intérieur (cercle 0)
        nombre_cercles: Nombre total de cercles (n+1 en comptant le cercle 0)
        param_a: Paramètre a pour les cercles intermédiaires
        param_b: Paramètre b pour le cercle extérieur
    """
    # Chargement du fichier vierge si fourni
    root_vierge = None
    if fichier_structure_vierge and os.path.exists(fichier_structure_vierge):
        try:
            tree_vierge = ET.parse(fichier_structure_vierge)
            root_vierge = tree_vierge.getroot()
        except Exception as e:
            print(f"Erreur lors du chargement du fichier vierge: {e}")
            print("Utilisation des paramètres par défaut.")

    # Création de la structure XML de base
    root = ET.Element("leaf")

    # ======= CALCUL DES RAYONS =======
    rayons = [rayon_interne]

    # Calcul des rayons des cercles intermédiaires (1 à n-1)
    for i in range(1, nombre_cercles - 1):
        # rayon(i) = rayon(i-1) / (1 - π/(2a))
        rayon = rayons[i - 1] / (1 - math.pi / (2 * param_a))
        rayons.append(rayon)

    # Calcul du rayon du cercle extérieur (n)
    if nombre_cercles > 1:
        # rayon(n) = rayon(n-1) × (1 + 2π/b)
        rayon_exterieur = rayons[-1] * (1 + 2 * math.pi / param_b)
        rayons.append(rayon_exterieur)

    print(f"Rayons calculés: {[round(r, 2) for r in rayons]}")

    # ======= CRÉATION DES NŒUDS =======
    nodes = []
    node_index = 0
    cell_index = 0
    cells = []

    # Création de la cellule centrale (si nécessaire)
    if nombre_cercles > 1:
        # Cellule centrale (cellule 0)
        central_cell_nodes = []
        num_points_cercle_interne = param_a  # Utilisation du paramètre a pour le cercle interne

        for i in range(num_points_cercle_interne):
            angle = 2 * math.pi * i / num_points_cercle_interne
            x = rayons[0] * math.cos(angle)
            y = rayons[0] * math.sin(angle)

            nodes.append({
                "nr": node_index,
                "x": x,
                "y": y,
                "radius": rayons[0]
            })
            central_cell_nodes.append(node_index)
            node_index += 1

        cells.append({
            "index": cell_index,
            "nodes": central_cell_nodes,
            "boundary": False,
            "radius": 0  # Centre
        })
        cell_index += 1

    # Création des cercles intermédiaires (1 à n-2 si n > 2)
    for circle_idx in range(1, nombre_cercles - 1):
        num_points = param_a  # Utilisation du paramètre a pour les cercles intermédiaires
        circle_nodes = []

        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            # Décalage d'angle pour mieux distribuer les points entre cercles
            if circle_idx % 2 == 1:
                angle += math.pi / num_points

            x = rayons[circle_idx] * math.cos(angle)
            y = rayons[circle_idx] * math.sin(angle)

            nodes.append({
                "nr": node_index,
                "x": x,
                "y": y,
                "radius": rayons[circle_idx]
            })
            circle_nodes.append(node_index)
            node_index += 1

        # Création des cellules pour ce cercle
        for i in range(num_points):
            cell_nodes = []

            # Nœuds du cercle actuel
            n1 = circle_nodes[i]
            n2 = circle_nodes[(i + 1) % num_points]
            cell_nodes.extend([n1, n2])

            # Pour les cercles intermédiaires, connectons aussi avec le cercle interne et externe
            if circle_idx > 0:
                # Connexion avec le cercle intérieur
                inner_circle_index = circle_idx - 1
                inner_num_points = param_a  # Même nombre de points sur les cercles intermédiaires

                # Trouver les 2 nœuds les plus proches sur le cercle intérieur
                inner_start_idx = (i * inner_num_points) // num_points
                inner_n1 = inner_start_idx + (circle_idx - 1) * inner_num_points
                inner_n2 = (inner_start_idx + 1) % inner_num_points + (circle_idx - 1) * inner_num_points

                cell_nodes.extend([inner_n1, inner_n2])

            cells.append({
                "index": cell_index,
                "nodes": cell_nodes,
                "boundary": False,
                "radius": rayons[circle_idx]
            })
            cell_index += 1

    # Création du cercle extérieur (n-1)
    if nombre_cercles > 1:
        num_points_externe = param_b  # Utilisation du paramètre b pour le cercle externe
        external_circle_nodes = []

        for i in range(num_points_externe):
            angle = 2 * math.pi * i / num_points_externe
            x = rayons[-1] * math.cos(angle)
            y = rayons[-1] * math.sin(angle)

            nodes.append({
                "nr": node_index,
                "x": x,
                "y": y,
                "radius": rayons[-1]
            })
            external_circle_nodes.append(node_index)
            node_index += 1

        # Création des cellules pour le cercle externe
        for i in range(num_points_externe):
            cell_nodes = []

            # Nœuds du cercle externe
            n1 = external_circle_nodes[i]
            n2 = external_circle_nodes[(i + 1) % num_points_externe]
            cell_nodes.extend([n1, n2])

            # Connexion avec le cercle intérieur précédent
            inner_circle_idx = nombre_cercles - 2
            inner_num_points = param_a  # Pour le cercle juste avant l'externe

            # Trouver les 2 nœuds les plus proches sur le cercle intérieur
            inner_start_idx = (i * inner_num_points) // num_points_externe
            if inner_circle_idx > 0:
                start_node = sum(param_a for _ in range(inner_circle_idx))
                inner_n1 = start_node + inner_start_idx
                inner_n2 = start_node + ((inner_start_idx + 1) % inner_num_points)
                cell_nodes.extend([inner_n1, inner_n2])

            cells.append({
                "index": cell_index,
                "nodes": cell_nodes,
                "boundary": True,  # Le cercle externe est la frontière
                "radius": rayons[-1]
            })
            cell_index += 1

    # ======= GÉNÉRATION DU XML =======
    # Ajouter les nœuds au XML
    nodes_elem = ET.SubElement(root, "nodes")
    nodes_elem.set("n", str(len(nodes)))

    for node in nodes:
        node_elem = ET.SubElement(nodes_elem, "node")
        node_elem.set("index", str(node["nr"]))
        node_elem.set("x", f"{node['x']:.4f}")
        node_elem.set("y", f"{node['y']:.4f}")

    # Ajouter les cellules au XML
    cells_elem = ET.SubElement(root, "cells")
    cells_elem.set("n", str(len(cells)))

    for cell in cells:
        cell_elem = ET.SubElement(cells_elem, "cell")
        cell_elem.set("index", str(cell["index"]))
        cell_elem.set("boundary", "true" if cell["boundary"] else "false")

        # Nœuds de la cellule
        nodelist = ET.SubElement(cell_elem, "nodelist")
        for node_idx in cell["nodes"]:
            node_ref = ET.SubElement(nodelist, "noderef")
            node_ref.set("node", str(node_idx))

        # Facteurs chimiques (vides par défaut)
        chem_elem = ET.SubElement(cell_elem, "chemicals")

    # Génération des murs
    walls = []
    wall_index = 0

    # Fonction pour vérifier si deux nœuds sont alignés radialement
    def sont_alignes(n1, n2):
        node1 = next(node for node in nodes if node["nr"] == n1)
        node2 = next(node for node in nodes if node["nr"] == n2)

        # Calculer l'angle entre la ligne qui connecte les nœuds et la ligne radiale
        dx = node2["x"] - node1["x"]
        dy = node2["y"] - node1["y"]

        # Vecteur radial du centre au premier nœud
        rx = node1["x"]
        ry = node1["y"]

        # Produit scalaire
        dot_product = dx * rx + dy * ry
        len1 = math.sqrt(dx ** 2 + dy ** 2)
        len2 = math.sqrt(rx ** 2 + ry ** 2)

        if len1 * len2 == 0:
            return False

        cos_angle = dot_product / (len1 * len2)

        # Alignés si l'angle est proche de 0° ou 180°
        return abs(cos_angle) > 0.9

    # Fonction pour trouver les cellules adjacentes à un mur
    def trouver_cellules_adjacentes(n1, n2, cells):
        cellules = []

        for cell in cells:
            nodes_cell = cell["nodes"]
            if n1 in nodes_cell and n2 in nodes_cell:
                cellules.append(cell["index"])

        # Si deux cellules trouvées, les retourner
        if len(cellules) == 2:
            return cellules[0], cellules[1]
        # Si une seule cellule trouvée, c'est une frontière
        elif len(cellules) == 1:
            return cellules[0], -1
        # Aucune cellule trouvée
        return -2, -2

    # Création des murs pour chaque paire de nœuds adjacents dans chaque cercle
    for circle_idx in range(nombre_cercles):
        if circle_idx == 0 and nombre_cercles > 1:
            # Cercle intérieur
            num_points = param_a
            start_node = 0
        elif circle_idx == nombre_cercles - 1:
            # Cercle extérieur
            num_points = param_b
            start_node = sum(param_a for _ in range(circle_idx))
        else:
            # Cercles intermédiaires
            num_points = param_a
            start_node = sum(param_a for _ in range(circle_idx))

        # Murs le long du cercle
        for i in range(num_points):
            n1 = start_node + i
            n2 = start_node + ((i + 1) % num_points)

            c1, c2 = trouver_cellules_adjacentes(n1, n2, cells)

            if c1 != -2:  # Au moins une cellule trouvée
                walls.append({
                    "index": wall_index,
                    "c1": c1,
                    "c2": c2,
                    "n1": n1,
                    "n2": n2
                })
                wall_index += 1

        # Murs radiaux entre cercles
        if circle_idx < nombre_cercles - 1:
            inner_num_points = param_a if circle_idx == 0 else param_a
            outer_num_points = param_b if circle_idx == nombre_cercles - 2 else param_a

            inner_start = sum(param_a for _ in range(circle_idx))
            outer_start = sum(param_a for _ in range(circle_idx + 1)) if circle_idx < nombre_cercles - 2 else sum(
                param_a for _ in range(circle_idx + 1))

            for i in range(inner_num_points):
                n1 = inner_start + i

                # Trouver le nœud radial correspondant sur le cercle extérieur
                angle_proportion = i / inner_num_points
                j = int(angle_proportion * outer_num_points) % outer_num_points

                n2 = outer_start + j

                # Vérifier si ce sont des nœuds différents et qu'ils sont alignés radialement
                if n1 != n2 and sont_alignes(n1, n2):
                    c1, c2 = trouver_cellules_adjacentes(n1, n2, cells)

                    if c1 != -2:  # Au moins une cellule trouvée
                        walls.append({
                            "index": wall_index,
                            "c1": c1,
                            "c2": c2,
                            "n1": n1,
                            "n2": n2
                        })
                        wall_index += 1

    # Création de la section walls dans le XML
    walls_elem = ET.SubElement(root, "walls")
    walls_elem.set("n", str(len(walls)))

    for wall in walls:
        wall_elem = ET.SubElement(walls_elem, "wall")
        wall_elem.set("index", str(wall["index"]))
        wall_elem.set("c1", str(wall["c1"]))
        wall_elem.set("c2", str(wall["c2"]))
        wall_elem.set("n1", str(wall["n1"]))
        wall_elem.set("n2", str(wall["n2"]))
        wall_elem.set("wall_type", "normal")
        wall_elem.set("viz_flux", "0")

        # Calculer la longueur du mur
        node1 = next(node for node in nodes if node["nr"] == wall["n1"])
        node2 = next(node for node in nodes if node["nr"] == wall["n2"])
        length = math.sqrt((node1["x"] - node2["x"]) ** 2 + (node1["y"] - node2["y"]) ** 2)
        wall_elem.set("length", f"{length:.4f}")

        # Ajouter les transporteurs (vides)
        transp1_elem = ET.SubElement(wall_elem, "transporters1")
        transp2_elem = ET.SubElement(wall_elem, "transporters2")

    # Ajout des nodesets (vide)
    nodesets_elem = ET.SubElement(root, "nodesets")
    nodesets_elem.set("n", "0")

    # Copier les paramètres d'affichage du fichier vierge ou créer par défaut
    try:
        settings = root_vierge.find("settings")
        if settings is not None:
            root.append(settings)
        else:
            raise Exception("Paramètres d'affichage non trouvés dans le fichier vierge")
    except:
        settings_elem = ET.SubElement(root, "settings")
        settings_elem.append(ET.Element("setting", {"name": "show_cell_centers", "val": "true"}))
        settings_elem.append(ET.Element("setting", {"name": "show_nodes", "val": "true"}))
        settings_elem.append(ET.Element("setting", {"name": "show_node_numbers", "val": "false"}))
        settings_elem.append(ET.Element("setting", {"name": "show_cell_numbers", "val": "true"}))
        settings_elem.append(ET.Element("setting", {"name": "show_borders_cells", "val": "false"}))
        settings_elem.append(ET.Element("setting", {"name": "show_cell_axes", "val": "false"}))
        settings_elem.append(ET.Element("setting", {"name": "show_cell_strain", "val": "false"}))
        settings_elem.append(ET.Element("setting", {"name": "show_fluxes", "val": "false"}))
        settings_elem.append(ET.Element("setting", {"name": "show_walls", "val": "false"}))
        settings_elem.append(ET.Element("setting", {"name": "save_movie_frames", "val": "true"}))
        settings_elem.append(ET.Element("setting", {"name": "show_only_leaf_boundary", "val": "false"}))
        settings_elem.append(ET.Element("setting", {"name": "cell_growth", "val": "true"}))
        settings_elem.append(ET.Element("setting", {"name": "hide_cells", "val": "false"}))
        viewport_elem = ET.SubElement(settings_elem, "viewport")
        viewport_elem.set("m11", "2.5")
        viewport_elem.set("m12", "0")
        viewport_elem.set("m21", "0")
        viewport_elem.set("m22", "2.5")
        viewport_elem.set("dx", "0")
        viewport_elem.set("dy", "0")

    # Conversion en chaîne XML et formatage
    rough_string = ET.tostring(root, encoding='UTF-8')
    reparsed = minidom.parseString(rough_string)

    # Écriture du XML formaté dans un fichier
    with open(nom_fichier_sortie, 'w', encoding='UTF-8') as f:
        f.write(reparsed.toprettyxml(indent="   ", encoding='UTF-8').decode('UTF-8'))

    print(f"Fichier '{nom_fichier_sortie}' généré avec succès.")
    return nom_fichier_sortie


# Exemple d'utilisation
if __name__ == "__main__":
    # Pour créer une structure à 5 cercles
    nom_fichier = generer_structure_n_cercles(
        nom_fichier_sortie="structure_n_cercles.xml",
        fichier_structure_vierge="structure_vierge.xml",
        rayon_interne=10,
        nombre_cercles=4,
        param_a=12,  # Nombre de points sur les cercles intermédiaires
        param_b=24  # Nombre de points sur le cercle extérieur
    )
    print(f"Fichier '{nom_fichier}' généré avec succès.")