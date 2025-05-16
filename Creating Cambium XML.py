import math
import numpy as np
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from datetime import datetime


def generer_structure_trois_cercles(nom_fichier_sortie="structure_trois_cercles.xml",
                                    fichier_structure_vierge="structure_vierge.xml",
                                    rayons=[100, 150, 250],
                                    nb_cellules_anneau1=12,
                                    nb_cellules_anneau2=15):
    """
    Génère un fichier XML avec une structure de tissu composée de trois cercles concentriques
    et deux couronnes de cellules, en important les paramètres du fichier structure_vierge.xml
    """
    # Importer les paramètres du fichier structure_vierge.xml
    try:
        tree_vierge = ET.parse(fichier_structure_vierge)
        root_vierge = tree_vierge.getroot()
        parametres = root_vierge.find("parameter")
    except Exception as e:
        print(f"Erreur lors de l'importation des paramètres: {e}")
        parametres = None

    # Création de la racine du document XML
    root = ET.Element("leaf")
    root.set("name", "structure_trois_cercles")
    root.set("date", datetime.now().strftime("%Y-%m-%d"))
    root.set("simtime", "0")

    # Ajout de la section paramètres importée
    if parametres is not None:
        root.append(parametres)
    else:
        print("Utilisation de paramètres par défaut")
        parametres_elem = ET.SubElement(root, "parameter")
        # Ajouter des paramètres par défaut si nécessaire

    # Calcul des positions des nœuds
    nodes = []
    node_index = 0
    R1, R2, R3 = rayons

    # Génération des nœuds sur le cercle intérieur (R1)
    R1_nodes = []
    for i in range(nb_cellules_anneau1):
        angle = i * (2 * math.pi / nb_cellules_anneau1)
        x = R1 * math.cos(angle)
        y = R1 * math.sin(angle)
        nodes.append({
            "nr": node_index,
            "x": x,
            "y": y,
            "radius": R1,
            "angle": angle,
            "special_tag": "special"  # Ajout du tag spécial à tous les nœuds
        })
        R1_nodes.append(node_index)
        node_index += 1

    # Génération des nœuds sur le cercle intermédiaire (R2)
    # Création d'un ensemble combiné de tous les angles nécessaires sur R2
    R2_angles = set()

    # Ajouter les angles pour le premier anneau (important: correspondance avec R1)
    for i in range(nb_cellules_anneau1):
        angle = i * (2 * math.pi / nb_cellules_anneau1)
        R2_angles.add(angle)

    # Ajouter les angles pour le second anneau (correspondance avec R3)
    for i in range(nb_cellules_anneau2):
        angle = i * (2 * math.pi / nb_cellules_anneau2)
        R2_angles.add(angle)

    # Convertir en liste et trier
    R2_angles = sorted(list(R2_angles))

    # Créer les nœuds sur le cercle intermédiaire
    R2_nodes_start_idx = node_index
    R2_nodes = []
    for angle in R2_angles:
        x = R2 * math.cos(angle)
        y = R2 * math.sin(angle)
        nodes.append({
            "nr": node_index,
            "x": x,
            "y": y,
            "radius": R2,
            "angle": angle,
            "special_tag": "special"  # Ajout du tag spécial à tous les nœuds
        })
        R2_nodes.append(node_index)
        node_index += 1

    # Génération des nœuds sur le cercle extérieur (R3)
    R3_nodes_start_idx = node_index
    R3_nodes = []
    for i in range(nb_cellules_anneau2):
        angle = i * (2 * math.pi / nb_cellules_anneau2)
        x = R3 * math.cos(angle)
        y = R3 * math.sin(angle)
        nodes.append({
            "nr": node_index,
            "x": x,
            "y": y,
            "radius": R3,
            "angle": angle,
            "boundary": True,  # Nœuds du cercle extérieur sont des nœuds de frontière
            "special_tag": "special"  # Ajout du tag spécial à tous les nœuds
        })
        R3_nodes.append(node_index)
        node_index += 1

    # Création de la section nodes
    nodes_elem = ET.SubElement(root, "nodes")
    nodes_elem.set("n", str(len(nodes)))
    nodes_elem.set("target_length", "2.5")

    for node in nodes:
        node_elem = ET.SubElement(nodes_elem, "node")
        node_elem.set("nr", str(node["nr"]))
        node_elem.set("x", str(node["x"]))
        node_elem.set("y", str(node["y"]))
        node_elem.set("sam", "false")
        node_elem.set("boundary", "true" if node.get("boundary", False) else "false")
        node_elem.set("fixed", "false")
        # Ajout du tag spécial dans le XML
        node_elem.set("special_tag", node["special_tag"])

    # Création des cellules
    cells = []
    cell_index = 0

    # Fonction pour trouver le nœud avec l'angle le plus proche
    def trouver_meilleur_noeud(angle_ref, noeuds_cercle):
        meilleur_noeud = None
        meilleure_diff = float('inf')

        for idx in noeuds_cercle:
            angle_noeud = nodes[idx]["angle"]
            # Calcul de la différence d'angle en tenant compte du rebouclage
            diff = min(abs(angle_noeud - angle_ref),
                       2*math.pi - abs(angle_noeud - angle_ref))

            if diff < meilleure_diff:
                meilleure_diff = diff
                meilleur_noeud = idx

        return meilleur_noeud

    # Premier anneau - nb_cellules_anneau1 cellules
    for k in range(nb_cellules_anneau1):
        # Nœuds du cercle intérieur pour cette cellule
        n1 = R1_nodes[k]
        n2 = R1_nodes[(k + 1) % nb_cellules_anneau1]
        angle1 = nodes[n1]["angle"]
        angle2 = nodes[n2]["angle"]

        # Trouver les nœuds de R2 qui sont entre ces deux angles
        r2_nodes_for_cell = []

        # Ajouter le nœud aligné avec angle1
        r2_node_current = trouver_meilleur_noeud(angle1, R2_nodes)
        r2_nodes_for_cell.append(r2_node_current)

        # Trouver tous les nœuds intermédiaires de R2 entre angle1 et angle2
        for r2_node in R2_nodes:
            angle_node = nodes[r2_node]["angle"]

            # Gérer le cas où on passe par 0/2π
            if angle2 > angle1:
                # Cas simple: on vérifie si l'angle est entre angle1 et angle2
                if angle1 < angle_node < angle2 and r2_node != r2_node_current:
                    r2_nodes_for_cell.append(r2_node)
            else:
                # Cas où on passe par 0/2π: l'angle doit être soit > angle1, soit < angle2
                if (angle_node > angle1 or angle_node < angle2) and r2_node != r2_node_current:
                    r2_nodes_for_cell.append(r2_node)

        # Ajouter le nœud aligné avec angle2 s'il n'est pas déjà dans la liste
        r2_node_next = trouver_meilleur_noeud(angle2, R2_nodes)
        if r2_node_next not in r2_nodes_for_cell:
            r2_nodes_for_cell.append(r2_node_next)

        # Trier les nœuds R2 par angle croissant
        r2_nodes_for_cell.sort(key=lambda idx: nodes[idx]["angle"])

        # Si on passe par 0/2π, il faut réarranger les nœuds pour avoir une séquence correcte
        if angle2 < angle1:
            # Trouver l'index du plus grand angle
            max_idx = 0
            max_angle = -1
            for i, node_idx in enumerate(r2_nodes_for_cell):
                if nodes[node_idx]["angle"] > max_angle:
                    max_angle = nodes[node_idx]["angle"]
                    max_idx = i

            # Réarranger la liste pour avoir les angles dans l'ordre correct
            r2_nodes_for_cell = r2_nodes_for_cell[max_idx + 1:] + r2_nodes_for_cell[:max_idx + 1]

        # Créer une cellule quadrilatérale en utilisant les deux nœuds de R1
        # et deux nœuds consécutifs de R2
        for i in range(len(r2_nodes_for_cell) - 1):
            r2_current = r2_nodes_for_cell[i]
            r2_next = r2_nodes_for_cell[i + 1]

            # Indices des nœuds qui forment cette cellule
            node_indices = [n1, n2, r2_next, r2_current]

            # Points pour calculer l'aire
            points = [(nodes[idx]["x"], nodes[idx]["y"]) for idx in node_indices]
            area = calculer_aire_polygone(points)

            cells.append({
                "index": cell_index,
                "area": area,
                "target_area": area,
                "nodes": node_indices
            })
            cell_index += 1



    # Deuxième anneau - nb_cellules_anneau2 cellules
    for k in range(nb_cellules_anneau2):
        # Indices des nœuds qui forment cette cellule
        angle_k = k * (2 * math.pi / nb_cellules_anneau2)
        angle_k_plus_1 = ((k + 1) % nb_cellules_anneau2) * (2 * math.pi / nb_cellules_anneau2)

        # Trouver les nœuds correspondants dans R2 et R3 avec la méthode robuste
        r2_node_k = trouver_meilleur_noeud(angle_k, R2_nodes)
        r2_node_k_plus_1 = trouver_meilleur_noeud(angle_k_plus_1, R2_nodes)
        r3_node_k = R3_nodes[k]
        r3_node_k_plus_1 = R3_nodes[(k + 1) % nb_cellules_anneau2]

        node_indices = [r2_node_k, r2_node_k_plus_1, r3_node_k_plus_1, r3_node_k]

        # Points pour calculer l'aire
        points = [(nodes[idx]["x"], nodes[idx]["y"]) for idx in node_indices]
        area = calculer_aire_polygone(points)

        cells.append({
            "index": cell_index,
            "nodes": node_indices,
            "area": area,
            "target_area": area
        })
        cell_index += 1

    # Création de la cellule externe (boundary_polygon)
    boundary_nodes = []
    for i in range(nb_cellules_anneau2):
        boundary_nodes.append(R3_nodes[i])

    boundary_area = math.pi * R3 * R3

    # Création de la section cellules
    cells_elem = ET.SubElement(root, "cells")
    cells_elem.set("n", str(len(cells) + 1))  # +1 pour le boundary_polygon
    cells_elem.set("magnification", "1")
    cells_elem.set("nchem", "0")
    cells_elem.set("offsetx", "0")
    cells_elem.set("offsety", "0")
    cells_elem.set("base_area", str(boundary_area))

    # Ajout des cellules normales
    for cell in cells:
        cell_elem = ET.SubElement(cells_elem, "cell")
        cell_elem.set("index", str(cell["index"]))
        cell_elem.set("area", str(cell["area"]))
        cell_elem.set("target_area", str(cell["target_area"]))
        cell_elem.set("cell_type", "1")  # Type de cellule standard
        cell_elem.set("boundary", "0")
        cell_elem.set("stiffness", "1")
        cell_elem.set("fixed", "false")
        cell_elem.set("target_length", "0")
        cell_elem.set("lambda_celllength", "0")
        cell_elem.set("at_boundary", "true")
        cell_elem.set("pin_fixed", "false")
        cell_elem.set("div_counter", "0")
        cell_elem.set("dead", "false")
        cell_elem.set("source", "false")

        for node_idx in cell["nodes"]:
            node_elem = ET.SubElement(cell_elem, "node")
            node_elem.set("n", str(node_idx))

    # Ajout du boundary_polygon
    boundary_elem = ET.SubElement(cells_elem, "boundary_polygon")
    boundary_elem.set("index", "-1")
    boundary_elem.set("area", str(boundary_area))
    boundary_elem.set("target_area", str(boundary_area))
    boundary_elem.set("cell_type", "0")
    boundary_elem.set("boundary", "0")
    boundary_elem.set("stiffness", "1")
    boundary_elem.set("fixed", "false")
    boundary_elem.set("target_length", "0")
    boundary_elem.set("lambda_celllength", "0")
    boundary_elem.set("at_boundary", "true")
    boundary_elem.set("pin_fixed", "false")
    boundary_elem.set("div_counter", "0")
    boundary_elem.set("dead", "false")
    boundary_elem.set("source", "false")

    for node_idx in boundary_nodes:
        node_elem = ET.SubElement(boundary_elem, "node")
        node_elem.set("n", str(node_idx))

    # Fonction pour vérifier si une arête touche le boundary_polygon
    def est_liee_au_boundary(n1, n2, cells):
        """
        Vérifie si l'arête entre n1 et n2 appartient à une cellule avec index -1 (boundary_polygon)
        """
        for cell in cells:
            cell_idx = cell.get("index", None)
            if cell_idx == -1:  # C'est le boundary_polygon
                nodes_list = [int(n.get("n")) for n in cell.findall("node")]
                if n1 in nodes_list and n2 in nodes_list:
                    return True
        return False

    # Fonction pour trouver le nœud le plus proche sur le même cercle avec tag spécial
    def trouver_noeud_plus_proche_meme_cercle(node_idx):
        node = nodes[node_idx]
        cercle_nodes = []

        # Déterminer à quel cercle appartient ce nœud
        if node_idx in R1_nodes:
            cercle_nodes = R1_nodes
        elif node_idx in R2_nodes:
            cercle_nodes = R2_nodes
        elif node_idx in R3_nodes:
            cercle_nodes = R3_nodes
        else:
            return None

        # Trouver le nœud le plus proche avec tag spécial
        min_dist = float('inf')
        closest = None
        angle_node = node["angle"]

        for other_idx in cercle_nodes:
            if other_idx == node_idx:
                continue

            other_node = nodes[other_idx]
            if other_node.get("special_tag") == "special":
                # Pour R2, vérifier l'espacement angulaire
                if node_idx in R2_nodes:
                    angle_diff = min(abs(other_node["angle"] - angle_node),
                                     2 * math.pi - abs(other_node["angle"] - angle_node))
                    # Accepter uniquement les nœuds avec espacement angulaire proche de π/12 ou π/15
                    pi_12 = math.pi / 12
                    pi_15 = math.pi / 15
                    if not (abs(angle_diff - pi_12) < 0.01 or abs(angle_diff - pi_15) < 0.01):
                        continue

                dist = min(abs(other_node["angle"] - angle_node), 2 * math.pi - abs(other_node["angle"] - angle_node))
                if dist < min_dist:
                    min_dist = dist
                    closest = other_idx

        return closest

    # Fonction pour vérifier si deux nœuds sont alignés (même angle)
    def sont_alignes(node1_idx, node2_idx, tolerance=0.01):
        node1 = nodes[node1_idx]
        node2 = nodes[node2_idx]
        angle_diff = min(abs(node1["angle"] - node2["angle"]), 2 * math.pi - abs(node1["angle"] - node2["angle"]))
        return angle_diff < tolerance

    # Fonction pour trouver les cellules adjacentes à une arête
    def trouver_cellules_adjacentes(n1, n2, cells_list):
        cell1, cell2 = -2, -2  # -2 signifie "non trouvé"

        for cell in cells_list:
            nodes_list = cell["nodes"]
            if n1 in nodes_list and n2 in nodes_list:
                # Cette cellule contient les deux nœuds
                if cell1 == -2:
                    cell1 = cell["index"]
                else:
                    cell2 = cell["index"]
                    break

        return cell1, cell2

    # Création des parois (walls)
    walls = []
    wall_index = 0

    # 1. Connexion des nœuds d'un même cercle avec leur plus proche voisin ayant le tag spécial
    # Nœuds du cercle R1
    for node_idx in R1_nodes:
        closest = trouver_noeud_plus_proche_meme_cercle(node_idx)
        if closest is not None:
            # Vérifier si ce mur existe déjà
            if not any(w["n1"] == node_idx and w["n2"] == closest or
                       w["n1"] == closest and w["n2"] == node_idx for w in walls):
                # Identifier les cellules adjacentes (sans inclure le boundary)
                c1, c2 = trouver_cellules_adjacentes(node_idx, closest, cells)

                # Ne créer le mur que si aucune des cellules n'est le boundary_polygon
                if c1 != -1 and c2 != -1:
                    walls.append({
                        "index": wall_index,
                        "c1": c1 if c1 != -2 else -1,
                        "c2": c2 if c2 != -2 else -1,
                        "n1": node_idx,
                        "n2": closest
                    })
                    wall_index += 1

    # Nœuds du cercle R2
    for node_idx in R2_nodes:
        closest = trouver_noeud_plus_proche_meme_cercle(node_idx)
        if closest is not None:
            # Vérifier si ce mur existe déjà
            if not any(w["n1"] == node_idx and w["n2"] == closest or
                       w["n1"] == closest and w["n2"] == node_idx for w in walls):
                # Identifier les cellules adjacentes
                c1, c2 = trouver_cellules_adjacentes(node_idx, closest, cells)

                # Ne créer le mur que si aucune des cellules n'est le boundary_polygon
                if c1 != -1 and c2 != -1:
                    walls.append({
                        "index": wall_index,
                        "c1": c1 if c1 != -2 else -1,
                        "c2": c2 if c2 != -2 else -1,
                        "n1": node_idx,
                        "n2": closest
                    })
                    wall_index += 1

    # Nœuds du cercle R3 - ATTENTION: Ces nœuds sont sur la frontière externe
    # On ne crée PAS de walls entre les nœuds du cercle R3, car ils pourraient
    # connecter une cellule normale au boundary_polygon

    # 2. Connexions entre les différents cercles (radiales)
    # Parcourir toutes les cellules pour trouver les connexions radiales
    for cell in cells:
        nodes_list = cell["nodes"]
        num_nodes = len(nodes_list)

        for i in range(num_nodes):
            n1 = nodes_list[i]
            n2 = nodes_list[(i + 1) % num_nodes]

            node1_info = next(node for node in nodes if node["nr"] == n1)
            node2_info = next(node for node in nodes if node["nr"] == n2)

            # Si les nœuds sont sur des cercles différents et alignés (connexion radiale)
            if abs(node1_info["radius"] - node2_info["radius"]) > 0.1 and sont_alignes(n1, n2):
                if not any(w["n1"] == n1 and w["n2"] == n2 or
                           w["n1"] == n2 and w["n2"] == n1 for w in walls):
                    # Déterminer les cellules adjacentes
                    c1, c2 = trouver_cellules_adjacentes(n1, n2, cells)

                    # IMPORTANT: Ne créer le mur que si aucune des cellules n'est le boundary_polygon
                    if c1 != -1 and c2 != -1:
                        walls.append({
                            "index": wall_index,
                            "c1": c1 if c1 != -2 else -1,
                            "c2": c2 if c2 != -2 else -1,
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


def calculer_aire_polygone(points):
    """Calcule l'aire d'un polygone en utilisant la formule des trapèzes"""
    points = np.array(points)
    x = points[:, 0]
    y = points[:, 1]
    return 0.5 * abs(np.sum(x[:-1] * y[1:] - x[1:] * y[:-1]) + x[-1] * y[0] - x[0] * y[-1])


def trouver_cellule_adjacente(index_cellule, nb_cellules_second_anneau, nb_cellules_premier_anneau):
    """Trouve la cellule du premier anneau adjacente à une cellule du second anneau"""
    angle_cellule = index_cellule * (2 * math.pi / nb_cellules_second_anneau)
    index_approx = int(angle_cellule / (2 * math.pi / nb_cellules_premier_anneau))
    return index_approx


# Exemple d'utilisation
if __name__ == "__main__":
    # Pour créer une structure à trois cercles avec 12 cellules dans le premier anneau et 15 dans le second
    nom_fichier = generer_structure_trois_cercles(
        nom_fichier_sortie="structure_trois_cercles.xml",
        fichier_structure_vierge="structure_vierge.xml",
        rayons=[10, 15, 25],
        nb_cellules_anneau1=12,
        nb_cellules_anneau2=15
    )
    print(f"Fichier '{nom_fichier}' généré avec succès.")