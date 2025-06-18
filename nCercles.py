import math as math
import matplotlib.pyplot as plt
from random import *

# ----------------------------------------------------------------------------------------------------------#
# ------------- CONVERSION POLAIRE-CARTÉSIEN ---------------------------------------------------------------#
# ----------------------------------------------------------------------------------------------------------#

def polaire_vers_cartesien(k_noeuds_n_cercle_polaire):
    """Convertit les coordonnées polaires des noeuds en coordonnées cartésiennes.

    Args:
        k_noeuds_n_cercle_polaire: Liste des noeuds en coordonnées polaires pour chaque cercle

    Returns:
        Liste des noeuds en coordonnées cartésiennes pour chaque cercle
    """
    return [
        {
            "x": noeud["r"] * math.cos(noeud["theta"]),
            "y": noeud["r"] * math.sin(noeud["theta"]),
            "index": noeud["index"],
            "initial": noeud["initial"],
            "sam": noeud["sam"],
            "boundary": noeud["boundary"],
            "fixed": noeud["fixed"]
        }
        for cercle in k_noeuds_n_cercle_polaire
        for noeud in cercle
    ]



#-----------------------------------------------------------------------------------------------------#
#------------ GÉNÉRATION DES RAYONS ------------------------------------------------------------------#
#-----------------------------------------------------------------------------------------------------#

def n_cercles(n, rayon_0, a, rapport_R_T, debug=False):
    """Calcule les rayons de n cercles concentriques.

    Args:
        n: Nombre de cercles à générer
        rayon_0: Rayon du premier cercle (le plus interne)
        a: Liste des nombres de points/cellules par cercle
        rapport_R_T: Liste des rapports entre rayon et longueur de corde
        debug: Active/désactive l'affichage des informations de débogage

    Returns:
        Liste des rayons des cercles générés
    """
    if n <= 0:
        return []

    rayon_n_cercles = [rayon_0]  # Initialisation avec le premier rayon

    if debug:
        print(f"cercle 0: rayon = {rayon_0}\n")

    for i in range(1, n):
        rayon_precedent = rayon_n_cercles[i - 1]

        # Sélection de l'indice correct pour a
        a_idx = i - 1 if i < n - 1 or len(a) <= i - 1 else i - 2

        # Facteur multiplicatif pour calculer l'incrément de rayon

        # Calcul du nouveau rayon
        sin_term = math.sin(math.pi / a[a_idx])
        increment = rapport_R_T[i - 1] * 2 * sin_term * rayon_precedent
        nouveau_rayon = rayon_precedent + increment
        rayon_n_cercles.append(nouveau_rayon)

        if debug:
            print(f"cercle {i}:")
            print(f"rayon précédent = {rayon_precedent}")
            print(f"nouveau rayon = {nouveau_rayon}")
            print(f"incrément = {increment}")
            if i < n - 1:
                ratio_calcule = (nouveau_rayon - rayon_precedent) / (2 * sin_term * rayon_precedent)
                print(f"ratio R/T calculé = {ratio_calcule}")
                print(f"ratio R/T attendu = {rapport_R_T[i]}")
            else:
                ratio_calcule = (nouveau_rayon - rayon_precedent) / (sin_term * rayon_precedent)
                print(f"ratio R/T = {ratio_calcule}")
            print(f"a[{a_idx}] = {a[a_idx]}\n")

    return rayon_n_cercles





#----------------------------------------------------------------------------------------------------#
#---------- CRÉATION DES NOEUDS INITIAUX ------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#

def creer_noeuds_initiaux(n, rayon_n_cercles, a):
    """Crée les nœuds initiaux sans fusion.

    Args:
        n: Nombre de cercles
        rayon_n_cercles: Liste des rayons de chaque cercle
        a: Liste des nombres de points/cellules par cercle

    Returns:
        Tuple contenant:
            - Liste des noeuds en coordonnées polaires pour chaque cercle
            - Nombre total de noeuds créés
    """
    k_noeuds_n_cercle_polaire = []
    index_noeud = 0

    # Fonction auxiliaire pour créer un nœud
    def creer_noeud(r, theta, boundary=False, fixed=False):
        nonlocal index_noeud
        noeud = {
            "r": r,
            "theta": theta,
            "index": index_noeud,
            "initial": True,
            "sam": False,
            "boundary": boundary,
            "fixed": fixed
        }
        index_noeud += 1
        return noeud

    for i in range(n):
        rayon = rayon_n_cercles[i]
        cercle_noeuds = []

        if i == 0:
            # Premier cercle - tous les nœuds sont fixes
            cercle_noeuds = [
                creer_noeud(
                    r=rayon,
                    theta=2 * math.pi * j / a[i],
                    fixed=True
                ) for j in range(a[i])
            ]

        elif 0 < i < n - 1:
            # Cercles intermédiaires
            # D'abord les points alignés avec le cercle précédent
            cercle_noeuds.extend([
                creer_noeud(
                    r=rayon,
                    theta=2 * math.pi * j / a[i-1]
                ) for j in range(a[i-1])
            ])

            # Puis les points propres à ce cercle
            cercle_noeuds.extend([
                creer_noeud(
                    r=rayon,
                    theta=2 * math.pi * j / a[i]
                ) for j in range(a[i])
            ])

        else:
            # Dernier cercle - tous les points sont sur la frontière
            cercle_noeuds = [
                creer_noeud(
                    r=rayon,
                    theta=2 * math.pi * j / a[i-1],
                    boundary=True
                ) for j in range(a[i-1])
            ]

        k_noeuds_n_cercle_polaire.append(cercle_noeuds)

    return k_noeuds_n_cercle_polaire, index_noeud



#----------------------------------------------------------------------------------------------------#
#------------- FUSION DES NOEUDS PROCHES ------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#

def fusionner_noeuds(k_noeuds_n_cercle_polaire, n, index_noeud_depart=0, seuil_distance=5):
    """ Fusionne les nœuds qui se chevauchent.

        Args:
            k_noeuds_n_cercle_polaire: Liste des noeuds en coordonnées polaires
            n: Nombre de cercles
            index_noeud_depart: Index de départ pour les nouveaux noeuds créés
            seuil_distance: Distance minimale entre deux noeuds pour les considérer distincts

        Returns:
            Tuple contenant:
                - Liste mise à jour des noeuds en coordonnées polaires
                - Dictionnaire de correspondance des indices fusionnés """

    index_noeud = index_noeud_depart

    # Trier chaque sous-liste par ordre croissant de theta
    for i in range(len(k_noeuds_n_cercle_polaire)):
        k_noeuds_n_cercle_polaire[i].sort(key=lambda noeud: noeud["theta"])

    # Collecter tous les nœuds avec leur cercle d'origine
    tous_noeuds = []
    for i, cercle in enumerate(k_noeuds_n_cercle_polaire):
        for noeud in cercle:
            r = noeud["r"]
            theta = noeud["theta"]
            idx = noeud["index"]
            initial = noeud["initial"]
            sam = noeud["sam"]
            boundary = noeud["boundary"]
            fixed = noeud["fixed"]
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            tous_noeuds.append((x, y, r, theta, idx, i, initial, sam,boundary,fixed))

    # Identifier les paires de nœuds qui se chevauchent
    map_indices = {}
    noeuds_a_fusionner = []

    for i in range(len(tous_noeuds)):
        x1, y1, r1, theta1, idx1, cercle1, initial1,sam1,boundary1,fixed1 = tous_noeuds[i]

        for j in range(i + 1, len(tous_noeuds)):
            x2, y2, r2, theta2, idx2, cercle2, initial2,sam2,boundary2,fixed2 = tous_noeuds[j]

            # Distance entre les nœuds
            distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

            if distance < seuil_distance:
                print(f"Nœuds à fusionner : {idx1} et {idx2} (distance={distance:.3f})")
                noeuds_a_fusionner.append((i, j))

    # Création des nouveaux nœuds
    nouveaux_noeuds = []
    indices_a_supprimer = set()

    for i, j in noeuds_a_fusionner:
        x1, y1, r1, theta1, idx1, cercle1, initial1,sam1,boundary1,fixed1 = tous_noeuds[i]
        x2, y2, r2, theta2, idx2, cercle2, initial2,sam2,boundary2,fixed2 = tous_noeuds[j]

        # Créer le nœud entre les deux
        x_nouveau = (x1 + x2) / 2
        y_nouveau = (y1 + y2) / 2
        r_nouveau = math.sqrt(x_nouveau ** 2 + y_nouveau ** 2)
        theta_nouveau = math.atan2(y_nouveau, x_nouveau)

        if theta_nouveau < 0:
            theta_nouveau += 2 * math.pi

        nouvel_indice = index_noeud
        index_noeud += 1

        # Un nœud est initial seulement si tous les nœuds fusionnés sont initiaux
        initial_nouveau = initial1 and initial2
        boundary_nouveau = boundary1 or  boundary2
        sam_nouveau = False
        fixed_nouveau = False
        # Création du nouveau nœud
        nouveau_noeud = {
            "r": r_nouveau,
            "theta": theta_nouveau,
            "index": nouvel_indice,
            "initial": initial_nouveau,
            "sam":sam_nouveau,
            "boundary":boundary_nouveau,
            "fixed": fixed_nouveau
        }

        nouveaux_noeuds.append((nouveau_noeud, cercle1, cercle2))

        map_indices[idx1] = nouvel_indice
        map_indices[idx2] = nouvel_indice

        indices_a_supprimer.add(i)
        indices_a_supprimer.add(j)

    # Reconstruction des nœuds sans ceux qui sont supprimés
    nouveau_k_noeuds_n_cercle_polaire = [[] for _ in range(n)]

    # Ajouter les nœuds non supprimés
    for i, (x, y, r, theta, idx, cercle, initial,  sam,boundary, fixed) in enumerate(tous_noeuds):
        if i not in indices_a_supprimer:
            nouveau_k_noeuds_n_cercle_polaire[cercle].append({
                "r": r,
                "theta": theta,
                "index": idx,
                "initial": initial,
                "sam": sam,
                "boundary": boundary,
                "fixed": fixed
            })

    # Ajouter les nouveaux nœuds
    for nouveau_noeud, cercle1, cercle2 in nouveaux_noeuds:
        nouveau_k_noeuds_n_cercle_polaire[cercle1].append(nouveau_noeud.copy())
        if cercle1 != cercle2:
            nouveau_k_noeuds_n_cercle_polaire[cercle2].append(nouveau_noeud.copy())

    # Trier à nouveau
    for i in range(len(nouveau_k_noeuds_n_cercle_polaire)):
        nouveau_k_noeuds_n_cercle_polaire[i].sort(key=lambda noeud: noeud["theta"])

    print(f"Nombre de nouveaux nœuds créés: {len(nouveaux_noeuds)}")

    return nouveau_k_noeuds_n_cercle_polaire, map_indices



# ----------------------------------------------------------------------------------------------------#
# ------------ CRÉATION DES CELLULES AVEC NOEUDS INTERMÉDIAIRES ---------------------------------------#
# ----------------------------------------------------------------------------------------------------#
def creer_cellules(rayon_n_cercles, k_noeuds_n_cercle_polaire, n, a):

    """Crée des cellules à 4 nœuds entre cercles consécutifs.

    Args:
        rayon_n_cercles: Liste des rayons des cercles
        k_noeuds_n_cercle_polaire: Coordonnées polaires des nœuds pour chaque cercle
        n: Nombre de cercles
        a: Liste des nombres de cellules entre chaque paire de cercles consécutifs

    Returns:
        Liste des cellules, chaque cellule étant définie par une liste de noeuds (indices)
    """
    # Fonction auxiliaire pour la comparaison d'angles
    def angles_equivalents(a1, a2, tolerance=0.001):
        a1_norm = a1 % (2 * math.pi)
        a2_norm = a2 % (2 * math.pi)
        diff = min(abs(a1_norm - a2_norm), 2 * math.pi - abs(a1_norm - a2_norm))
        return diff < tolerance

    # Fonction pour vérifier si un angle est entre deux autres
    def est_entre_angles(theta, debut, fin, tolerance=0.001):
        theta_norm = theta % (2 * math.pi)
        debut_norm = debut % (2 * math.pi)
        fin_norm = fin % (2 * math.pi)

        if debut_norm <= fin_norm:
            return debut_norm - tolerance <= theta_norm <= fin_norm + tolerance
        else:
            return theta_norm >= debut_norm - tolerance or theta_norm <= fin_norm + tolerance

    # Prétraitement : indexer et trier les nœuds par angle pour chaque cercle
    noeuds_par_cercle = []
    for i in range(n):
        if i < len(k_noeuds_n_cercle_polaire):
            noeuds_par_cercle.append(sorted(k_noeuds_n_cercle_polaire[i], key=lambda noeud: noeud["theta"]))
        else:
            noeuds_par_cercle.append([])

    cellules_temp = []  # Liste temporaire pour les cellules

    # Création de la cellule centrale (cercle 0)
    if n > 0 and len(k_noeuds_n_cercle_polaire) > 0:
        noeuds_cercle_0 = [noeud["index"] for noeud in noeuds_par_cercle[0]]

        cellule_centrale = {
            "index": 0,
            "noeuds": noeuds_cercle_0,
            "boundary": 0,
            "cell_type": 1,
            "target_area": 100.0,
            "lambda_celllength": 0,
            "at_boundary": True,
            "dead": False,
            "target_length": 0,
            "stiffness": 1,
            "source": False,
            "pin_fixed": False,
            "area": 0.0,
            "fixed": False,
            "div_counter": 0,
            "cercle": 0,
            "angle": 0
        }

        cellules_temp.append(cellule_centrale)
        print(f"Cellule centrale créée avec {len(noeuds_cercle_0)} noeuds")

    # Création des cellules entre les cercles
    for i in range(n - 1):
        nb_cellules = a[i] if i < len(a) else a[-1]

        for j in range(nb_cellules):
            angle_j = 2 * j * math.pi / nb_cellules
            angle_j_moins_1 = 2 * (j - 1) * math.pi / nb_cellules
            if angle_j_moins_1 < 0:
                angle_j_moins_1 += 2 * math.pi

            # Variables pour stocker les informations des nœuds trouvés
            noeud1, noeud2, noeud3, noeud4 = None, None, None, None
            angle1, angle2, angle3, angle4 = None, None, None, None
            r1, r2, r3, r4 = None, None, None, None
            tolerance = 0.001

            # Recherche optimisée des nœuds aux angles spécifiques
            for point in noeuds_par_cercle[i]:
                theta = point["theta"]
                if noeud1 is None and angles_equivalents(theta, angle_j, tolerance):
                    noeud1, angle1, r1 = point["index"], theta, point["r"]
                elif noeud2 is None and angles_equivalents(theta, angle_j_moins_1, tolerance):
                    noeud2, angle2, r2 = point["index"], theta, point["r"]

                # Si les deux nœuds sont trouvés, on peut passer au cercle suivant
                if noeud1 is not None and noeud2 is not None:
                    break

            for point in noeuds_par_cercle[i + 1]:
                theta = point["theta"]
                if noeud3 is None and angles_equivalents(theta, angle_j_moins_1, tolerance):
                    noeud3, angle3, r3 = point["index"], theta, point["r"]
                elif noeud4 is None and angles_equivalents(theta, angle_j, tolerance):
                    noeud4, angle4, r4 = point["index"], theta, point["r"]

                if noeud3 is not None and noeud4 is not None:
                    break

            # Si tous les nœuds principaux sont trouvés
            if noeud1 is not None and noeud2 is not None and noeud3 is not None and noeud4 is not None:
                # Calculer le centre de la cellule
                x1, y1 = r1 * math.cos(angle1), r1 * math.sin(angle1)
                x2, y2 = r2 * math.cos(angle2), r2 * math.sin(angle2)
                x3, y3 = r3 * math.cos(angle3), r3 * math.sin(angle3)
                x4, y4 = r4 * math.cos(angle4), r4 * math.sin(angle4)

                centre_x = (x1 + x2 + x3 + x4) / 4
                centre_y = (y1 + y2 + y3 + y4) / 4
                angle_centre = math.atan2(centre_y, centre_x)
                if angle_centre < 0:
                    angle_centre += 2 * math.pi

                # Recherche des nœuds intermédiaires
                noeuds_arc_sup = []
                for point in noeuds_par_cercle[i]:
                    theta, index = point["theta"], point["index"]
                    if index != noeud1 and index != noeud2:
                        if (est_entre_angles(theta, angle2, angle1, tolerance) or
                            angles_equivalents(theta, angle1, tolerance) or
                            angles_equivalents(theta, angle2, tolerance)):
                            noeuds_arc_sup.append((theta, index))

                noeuds_arc_sup.sort(reverse=True)
                noeuds_arc_sup = [idx for _, idx in noeuds_arc_sup]

                noeuds_arc_inf = []
                for point in noeuds_par_cercle[i + 1]:
                    theta, index = point["theta"], point["index"]
                    if index != noeud3 and index != noeud4:
                        if (est_entre_angles(theta, angle3, angle4, tolerance) or
                            angles_equivalents(theta, angle3, tolerance) or
                            angles_equivalents(theta, angle4, tolerance)):
                            noeuds_arc_inf.append((theta, index))

                noeuds_arc_inf.sort()
                noeuds_arc_inf = [idx for _, idx in noeuds_arc_inf]

                # Construction des noeuds de la cellule dans l'ordre
                tous_noeuds = [noeud1] + noeuds_arc_sup + [noeud2, noeud3] + noeuds_arc_inf + [noeud4]

                cellule = {
                    "index": len(cellules_temp),
                    "noeuds": tous_noeuds,
                    "boundary": 0,
                    "cell_type": 0 if i == n - 2 else (3 if i == 0 else 0),
                    "target_area": 100.0,
                    "lambda_celllength": 0,
                    "at_boundary": True if i == n - 2 else False,
                    "dead": False,
                    "target_length": 0,
                    "stiffness": 1,
                    "source": False,
                    "pin_fixed": False,
                    "area": 0.0,
                    "fixed": False,
                    "div_counter": 0,
                    "cercle": i + 1,
                    "angle": angle_centre
                }

                cellules_temp.append(cellule)
            else:
                print(f"Impossible de créer la cellule à i={i}, j={j}: nœuds manquants")
                print(f"Nœuds trouvés: {noeud1}, {noeud2}, {noeud3}, {noeud4}")

    # Organiser les cellules par cercle puis par angle
    cellules_par_cercle = {}
    for cellule in cellules_temp:
        cercle = cellule.get("cercle", 0)
        if cercle not in cellules_par_cercle:
            cellules_par_cercle[cercle] = []
        cellules_par_cercle[cercle].append(cellule)

    # Trier et réassembler les cellules
    cellules_triees = []
    for cercle in sorted(cellules_par_cercle.keys()):
        cellules_par_cercle[cercle].sort(key=lambda c: c.get("angle", 0))
        cellules_triees.extend(cellules_par_cercle[cercle])

    # Réindexer les cellules triées
    cellules = []
    for i, cellule in enumerate(cellules_triees):
        cellule_copy = cellule.copy()
        cellule_copy["index"] = i
        cellules.append(cellule_copy)

    print("cellules", cellules)
    return cellules


# ----------------------------------------------------------------------------------------------------#
# ---------- RAFFINNAGE DU MAILLAGE (AJOUT DE NOEUDS) --------------------------------------------------------------#
# ----------------------------------------------------------------------------------------------------#

def raffiner_maillage_separe(k_noeuds_n_cercle_polaire, n, cellules, longueur_seuil_cercle, longueur_seuil_radial,
                             rayons_n_cercles, seuil_proximite):
    # Copier les données initiales
    nouveau_k_noeuds_n_cercle_polaire = [[] for _ in range(n)]
    for i in range(min(n, len(k_noeuds_n_cercle_polaire))):
        for noeud in k_noeuds_n_cercle_polaire[i]:
            nouveau_k_noeuds_n_cercle_polaire[i].append(noeud.copy())

    nouvelles_cellules = [cellule.copy() for cellule in cellules]

    # Tableau pour stocker les nœuds intermédiaires radiaux (qui ne sont pas sur les cercles)
    noeuds_radiaux = []

    # Identifier les noeuds avec tag spécial
    noeuds_speciaux = {}
    for i_cercle, cercle in enumerate(nouveau_k_noeuds_n_cercle_polaire):
        for noeud in cercle:
            if noeud.get("tag_special", False):
                r = noeud["r"]
                theta = noeud["theta"]
                x = r * math.cos(theta)
                y = r * math.sin(theta)
                noeuds_speciaux[noeud["index"]] = (x, y, r, theta)

    # Phase 1: Remaillage des cercles (segments circulaires)
    iterations_cercles = 0
    segments_cercles_raffines = True

    while segments_cercles_raffines and iterations_cercles < 5:
        iterations_cercles += 1
        segments_cercles_raffines = False

        # Convertir en coordonnées cartésiennes pour le calcul des distances
        noeuds_cartesien = {}
        for i_cercle in range(len(nouveau_k_noeuds_n_cercle_polaire)):
            for noeud in nouveau_k_noeuds_n_cercle_polaire[i_cercle]:
                r = noeud["r"]
                theta = noeud["theta"]
                index = noeud["index"]
                initial = noeud["initial"]
                boundary = noeud["boundary"]
                x = r * math.cos(theta)
                y = r * math.sin(theta)
                noeuds_cartesien[index] = (x, y, r, theta, i_cercle, initial, boundary)

        # Ajouter les noeuds radiaux à la liste des noeuds cartésiens
        for noeud in noeuds_radiaux:
            r = noeud["r"]
            theta = noeud["theta"]
            index = noeud["index"]
            initial = noeud["initial"]
            boundary = noeud["boundary"]
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            noeuds_cartesien[index] = (x, y, r, theta, -1, initial, boundary)  # -1 indique un noeud radial

        # Dictionnaire pour stocker les nouveaux noeuds à ajouter sur les cercles
        segments_cercles_a_raffiner = {}

        # Vérifier les segments sur un même cercle
        for i_cercle in range(n):
            if i_cercle >= len(nouveau_k_noeuds_n_cercle_polaire):
                continue

            cercle_noeuds = nouveau_k_noeuds_n_cercle_polaire[i_cercle]
            nb_noeuds = len(cercle_noeuds)

            for i in range(nb_noeuds):
                idx1 = cercle_noeuds[i]["index"]
                idx2 = cercle_noeuds[(i + 1) % nb_noeuds]["index"]

                if idx1 in noeuds_cartesien and idx2 in noeuds_cartesien:
                    x1, y1, r1, theta1, _, _, boundary1 = noeuds_cartesien[idx1]
                    x2, y2, r2, theta2, _, _, boundary2 = noeuds_cartesien[idx2]

                    # Distance euclidienne entre les deux noeuds
                    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

                    if distance > longueur_seuil_cercle:
                        # Gestion de l'interpolation angulaire
                        if theta1 < 0: theta1 += 2 * math.pi
                        if theta2 < 0: theta2 += 2 * math.pi

                        # Gérer le cas où l'arc traverse la ligne θ=0
                        if abs(theta1 - theta2) > math.pi:
                            if theta1 > theta2:
                                theta2 += 2 * math.pi
                            else:
                                theta1 += 2 * math.pi

                        # Interpolation angulaire en respectant le rayon du cercle
                        theta_new = (theta1 + theta2) / 2
                        r_new = rayons_n_cercles[i_cercle]  # Utiliser le rayon exact du cercle

                        # Normaliser l'angle entre 0 et 2π
                        if theta_new >= 2 * math.pi:
                            theta_new -= 2 * math.pi

                        # Calculer les coordonnées cartésiennes
                        x_new = r_new * math.cos(theta_new)
                        y_new = r_new * math.sin(theta_new)

                        # Vérifier proximité avec noeuds spéciaux
                        trop_proche = False
                        for _, (x_special, y_special, _, _) in noeuds_speciaux.items():
                            dist_special = math.sqrt((x_new - x_special) ** 2 + (y_new - y_special) ** 2)
                            if dist_special < seuil_proximite:
                                trop_proche = True
                                break

                        if not trop_proche:
                            # Hériter le statut boundary si au moins un des nœuds est boundary
                            is_boundary = boundary1 or boundary2
                            segments_cercles_a_raffiner[tuple(sorted([idx1, idx2]))] = (x_new, y_new, r_new, theta_new, i_cercle, is_boundary)
                            segments_cercles_raffines = True

        # Assigner des indices aux nouveaux noeuds
        indices_max = [noeud["index"] for cercle in nouveau_k_noeuds_n_cercle_polaire for noeud in cercle]
        indices_max.extend([noeud["index"] for noeud in noeuds_radiaux])
        prochain_indice = max(indices_max) + 1 if indices_max else 0

        # Ajouter les nouveaux noeuds aux cercles et créer le mappage
        map_segments_cercles_indices = {}
        for segment_key, (x_new, y_new, r_new, theta_new, cercle, is_boundary) in segments_cercles_a_raffiner.items():
            idx1, idx2 = segment_key

            nouveau_noeud = {
                "r": r_new,
                "theta": theta_new,
                "index": prochain_indice,
                "initial": False,  # Nouveau nœud intermédiaire
                "sam": False,
                "boundary": is_boundary,  # Hériter le statut boundary
                "fixed": False
            }

            # Ajouter au cercle correspondant
            nouveau_k_noeuds_n_cercle_polaire[cercle].append(nouveau_noeud)

            # Mapper le segment au nouvel indice pour mise à jour des cellules
            map_segments_cercles_indices[segment_key] = prochain_indice
            prochain_indice += 1

        # Trier les noeuds de chaque cercle par angle
        for i in range(n):
            if i < len(nouveau_k_noeuds_n_cercle_polaire):
                nouveau_k_noeuds_n_cercle_polaire[i].sort(key=lambda point: point["theta"])

        # Mettre à jour les cellules
        maj_cellules = []
        for cellule in nouvelles_cellules:
            nouvelle_liste_noeuds = []
            noeuds = cellule["noeuds"]

            for i in range(len(noeuds)):
                idx1 = noeuds[i]
                idx2 = noeuds[(i + 1) % len(noeuds)]

                nouvelle_liste_noeuds.append(idx1)

                # Vérifier si ce segment a été raffiné (cercle)
                segment_key = tuple(sorted([idx1, idx2]))
                if segment_key in map_segments_cercles_indices:
                    nouvelle_liste_noeuds.append(map_segments_cercles_indices[segment_key])

            nouvelle_cellule = cellule.copy()
            nouvelle_cellule["noeuds"] = nouvelle_liste_noeuds
            maj_cellules.append(nouvelle_cellule)

        nouvelles_cellules = maj_cellules

    # Phase 2: Remaillage des segments radiaux entre nœuds UNIQUEMENT où des segments radiaux existent déjà
    iterations_radiaux = 0
    segments_radiaux_raffines = True

    while segments_radiaux_raffines and iterations_radiaux < 5:
        iterations_radiaux += 1
        segments_radiaux_raffines = False

        # Convertir en coordonnées cartésiennes pour le calcul des distances
        noeuds_cartesien = {}
        for i_cercle in range(len(nouveau_k_noeuds_n_cercle_polaire)):
            for noeud in nouveau_k_noeuds_n_cercle_polaire[i_cercle]:
                r = noeud["r"]
                theta = noeud["theta"]
                index = noeud["index"]
                initial = noeud["initial"]
                boundary = noeud["boundary"]
                x = r * math.cos(theta)
                y = r * math.sin(theta)
                noeuds_cartesien[index] = (x, y, r, theta, i_cercle, initial, boundary)

        # Ajouter les noeuds radiaux à la liste des noeuds cartésiens
        for noeud in noeuds_radiaux:
            r = noeud["r"]
            theta = noeud["theta"]
            index = noeud["index"]
            initial = noeud["initial"]
            boundary = noeud["boundary"]
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            noeuds_cartesien[index] = (x, y, r, theta, -1, initial, boundary)

        # Collecter les segments radiaux existants dans les cellules
        segments_radiaux_existants = set()
        for cellule in nouvelles_cellules:
            noeuds = cellule["noeuds"]
            for i in range(len(noeuds)):
                idx1 = noeuds[i]
                idx2 = noeuds[(i + 1) % len(noeuds)]

                if idx1 in noeuds_cartesien and idx2 in noeuds_cartesien:
                    x1, y1, r1, theta1, cercle1, _, _ = noeuds_cartesien[idx1]
                    x2, y2, r2, theta2, cercle2, _, _ = noeuds_cartesien[idx2]

                    # Vérifier si c'est un segment radial (rayons différents)
                    if abs(r1 - r2) > 0.001:  # Tolérance pour éviter erreurs d'arrondi
                        segments_radiaux_existants.add(tuple(sorted([idx1, idx2])))

        # Dictionnaire pour stocker les nouveaux nœuds à ajouter
        segments_radiaux_a_raffiner = {}

        # Pour chaque segment radial existant
        for segment in segments_radiaux_existants:
            idx1, idx2 = segment

            if idx1 in noeuds_cartesien and idx2 in noeuds_cartesien:
                x1, y1, r1, theta1, cercle1, initial1, boundary1 = noeuds_cartesien[idx1]
                x2, y2, r2, theta2, cercle2, initial2, boundary2 = noeuds_cartesien[idx2]

                # Distance euclidienne entre les deux noeuds
                distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

                # Si la distance est supérieure au seuil, on ajoute un nœud intermédiaire
                if distance > longueur_seuil_radial:
                    # Calculer la position du nouveau nœud intermédiaire
                    x_new = (x1 + x2) / 2
                    y_new = (y1 + y2) / 2
                    r_new = math.sqrt(x_new**2 + y_new**2)
                    theta_new = math.atan2(y_new, x_new)
                    if theta_new < 0:
                        theta_new += 2 * math.pi

                    # Hériter le statut boundary si l'un des nœuds est boundary
                    is_boundary = boundary1 or boundary2

                    # Sauvegarder les coordonnées du nouveau nœud
                    segments_radiaux_a_raffiner[segment] = (x_new, y_new, r_new, theta_new, is_boundary)
                    segments_radiaux_raffines = True

        # Assigner des indices aux nouveaux noeuds radiaux
        indices_max = [noeud["index"] for cercle in nouveau_k_noeuds_n_cercle_polaire for noeud in cercle]
        indices_max.extend([noeud["index"] for noeud in noeuds_radiaux])
        prochain_indice = max(indices_max) + 1 if indices_max else 0

        # Créer les nouveaux noeuds radiaux
        map_segments_radiaux_indices = {}
        for segment_key, (x_new, y_new, r_new, theta_new, is_boundary) in segments_radiaux_a_raffiner.items():
            idx1, idx2 = segment_key

            nouveau_noeud = {
                "r": r_new,
                "theta": theta_new,
                "index": prochain_indice,
                "initial": False,  # Nouveau nœud intermédiaire
                "sam": False,
                "boundary": False,  # Hériter le statut boundary
                "fixed": False
            }

            # Ajouter aux nœuds radiaux
            noeuds_radiaux.append(nouveau_noeud)

            # Mapper le segment au nouvel indice pour mise à jour des cellules
            map_segments_radiaux_indices[segment_key] = prochain_indice
            prochain_indice += 1

        # Mettre à jour les cellules avec les nouveaux noeuds radiaux
        maj_cellules = []
        for cellule in nouvelles_cellules:
            nouvelle_liste_noeuds = []
            noeuds = cellule["noeuds"]

            for i in range(len(noeuds)):
                idx1 = noeuds[i]
                idx2 = noeuds[(i + 1) % len(noeuds)]

                nouvelle_liste_noeuds.append(idx1)

                # Vérifier si ce segment a été raffiné (radialement)
                segment_key = tuple(sorted([idx1, idx2]))
                if segment_key in map_segments_radiaux_indices:
                    nouvelle_liste_noeuds.append(map_segments_radiaux_indices[segment_key])

            nouvelle_cellule = cellule.copy()
            nouvelle_cellule["noeuds"] = nouvelle_liste_noeuds
            maj_cellules.append(nouvelle_cellule)

        nouvelles_cellules = maj_cellules

    k_noeuds_n_cercle_polaire_final = []
    for cercle in nouveau_k_noeuds_n_cercle_polaire:
        k_noeuds_n_cercle_polaire_final.append(cercle)

    # Créer un cercle virtuel pour les noeuds radiaux (permet de rester compatible avec le format attendu)
    if noeuds_radiaux:
        k_noeuds_n_cercle_polaire_final.append(noeuds_radiaux)

    return k_noeuds_n_cercle_polaire_final, nouvelles_cellules






#----------------------------------------------------------------------------------------------------#
#-------------------------------------walls-------------------------------------------#
#----------------------------------------------------------------------------------------------------#

def generer_walls_initiaux(k_noeuds_n_cercle_cartesien, cellules_list):
    """
    Génère les walls (parois) entre les cellules adjacentes.

    Args:
        k_noeuds_n_cercle_cartesien: Liste des noeuds en coordonnées cartésiennes
        cellules_list: Liste des cellules

    Returns:
        Liste des walls générés
    """
    # Créer un dictionnaire pour accès rapide aux noeuds
    noeuds_dict = {}
    for noeud in k_noeuds_n_cercle_cartesien:
        noeuds_dict[noeud["index"]] = (noeud["x"], noeud["y"], noeud.get("initial", False),
                                       noeud.get("boundary", False))

    # Identifier les segments et les cellules qui les partagent
    segments_par_cellule = {}
    for cellule in cellules_list:
        noeuds = cellule["noeuds"]
        cell_index = cellule["index"]

        # Pour chaque paire de noeuds consécutifs
        for i in range(len(noeuds)):
            n1 = noeuds[i]
            n2 = noeuds[(i + 1) % len(noeuds)]
            segment = tuple(sorted([n1, n2]))

            # Ajouter la cellule à ce segment
            if segment not in segments_par_cellule:
                segments_par_cellule[segment] = []
            segments_par_cellule[segment].append(cell_index)

    # Générer les walls uniquement pour les segments partagés par deux cellules
    walls_liste = []
    wall_index = 0

    for segment, cellules in segments_par_cellule.items():
        # Un wall ne peut exister qu'entre deux cellules
        if len(cellules) == 2:
            n1, n2 = segment
            c1, c2 = sorted(cellules)

            # Vérifier que les noeuds existent et sont initiaux
            if n1 in noeuds_dict and n2 in noeuds_dict:
                _, _, initial1, boundary1 = noeuds_dict[n1]
                _, _, initial2, boundary2 = noeuds_dict[n2]

                # Vérifier que les deux noeuds sont initiaux
                if initial1 and initial2:
                    # Ne pas créer de wall si les deux noeuds sont sur la frontière
                    if boundary1 and boundary2:
                        continue

                    # Calculer la longueur du wall
                    (x1, y1, _, _), (x2, y2, _, _) = noeuds_dict[n1], noeuds_dict[n2]
                    longueur = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

                    # Créer le wall avec exactement la structure demandée
                    wall = {
                        "length": f"{longueur:.4f}",
                        "c1": str(c1),
                        "c2": str(c2),
                        "n1": str(n1),
                        "n2": str(n2),
                        "wall_type": "normal",
                        "viz_flux": "0",
                        "index": str(wall_index)
                    }

                    walls_liste.append(wall)
                    wall_index += 1

    return walls_liste


#----------------------------------------------------------------------------------------------------#
#------------------------- Aire cellules ---------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#

def shoelace_formula(cellules_list, noeuds_list, absoluteValue=True):
    """
    Calcule l'aire de chaque cellule en utilisant la formule de Shoelace (Gauss).

    Args:
        cellules_list: Liste des cellules à traiter
        noeuds_list: Liste des noeuds avec leurs coordonnées
        absoluteValue: Si True, retourne la valeur absolue de l'aire

    Returns:
        Liste des cellules avec l'aire calculée
    """
    # Optimisation par précalcul du dictionnaire de coordonnées
    noeuds_dict = {}
    for noeud in noeuds_list:
        noeuds_dict[noeud["index"]] = (noeud["x"], noeud["y"])

    # Préallocation de la liste de résultat
    n_cellules = len(cellules_list)
    cellules_avec_aire = [None] * n_cellules

    # Traitement optimisé par cellule
    for i, cellule in enumerate(cellules_list):
        indices_noeuds = cellule["noeuds"]
        nb_noeuds = len(indices_noeuds)

        # Traitement rapide des polygones dégénérés
        if nb_noeuds < 3:
            cellule_maj = cellule.copy()
            cellule_maj["area"] = 0.0
            cellules_avec_aire[i] = cellule_maj
            continue

        # Extraction optimisée des coordonnées avec gestion d'erreur intégrée
        try:
            # Extraction en une seule fois pour éviter les accès répétés
            coords = [noeuds_dict[idx] for idx in indices_noeuds]

            # Boucle unifiée pour le calcul de l'aire (sans allocation supplémentaire)
            somme = 0.0
            for j in range(nb_noeuds):
                k = (j + 1) % nb_noeuds
                # Formule de Shoelace optimisée
                somme += coords[j][0] * coords[k][1] - coords[k][0] * coords[j][1]

            # Calcul final avec une seule multiplication
            aire = abs(somme * 0.5) if absoluteValue else somme * 0.5

        except KeyError:
            # En cas d'indice invalide, attribuer une aire nulle
            aire = 0.0

        # Minimiser les copies en utilisant copy() au lieu de deepcopy()
        cellule_maj = cellule.copy()
        cellule_maj["area"] = aire
        cellules_avec_aire[i] = cellule_maj

    return cellules_avec_aire


def calculer_aire_totale_boundary(noeuds_list, absoluteValue=True):
    """
    Calcule l'aire totale du tissu en utilisant uniquement les noeuds marqués comme boundary.
    Version optimisée.

    Args:
        noeuds_list: Liste des noeuds avec leurs coordonnées
        absoluteValue: Si True, retourne la valeur absolue de l'aire

    Returns:
        Aire totale du tissu délimité par les noeuds boundary
    """
    # Extraction directe des noeuds boundary (plus efficace qu'une compréhension de liste)
    noeuds_boundary = []
    for noeud in noeuds_list:
        if noeud.get("boundary", False):
            noeuds_boundary.append(noeud)

    # Vérification rapide du nombre de noeuds
    n_noeuds = len(noeuds_boundary)
    if n_noeuds < 3:
        return 0.0

    # Calcul du véritable centroïde (dans la version originale, il était initialisé à 0,0)
    centre_x = sum(noeud["x"] for noeud in noeuds_boundary) / n_noeuds
    centre_y = sum(noeud["y"] for noeud in noeuds_boundary) / n_noeuds

    # Pré-calcul des angles pour le tri (évite les calculs répétés)
    noeuds_avec_angle = []
    for noeud in noeuds_boundary:
        dx = noeud["x"] - centre_x
        dy = noeud["y"] - centre_y
        angle = math.atan2(dy, dx)
        if angle < 0:
            angle += 2 * math.pi
        noeuds_avec_angle.append((noeud, angle))

    # Tri efficace
    noeuds_avec_angle.sort(key=lambda x: x[1])

    # Préextraction des coordonnées pour un accès plus rapide
    coords_x = []
    coords_y = []
    for noeud, _ in noeuds_avec_angle:
        coords_x.append(noeud["x"])
        coords_y.append(noeud["y"])

    # Formule de Shoelace optimisée en une seule passe
    aire = 0.0
    for i in range(n_noeuds):
        j = (i + 1) % n_noeuds
        # Version optimisée de la formule
        aire += (coords_x[i] * coords_y[j]) - (coords_x[j] * coords_y[i])

    # Division par 2 une seule fois à la fin
    aire *= 0.5

    return abs(aire) if absoluteValue else aire

#----------------------------------------------------------------------------------------------------#
#--------- VISUALISATION DES POINTS ET CERCLES ------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#

def tracer_points_cercles(k_noeuds, n, a, cellules=None):
    """ Visualise les noeuds, les cercles et les segments radiaux.

        Args:
            k_noeuds_n_cercle_polaire: Liste des noeuds en coordonnées polaires
            n: Nombre de cercles
            a: Liste des nombres de cellules/points par cercle

        Returns:
            None. Affiche un graphique avec matplotlib.  """

    plt.figure(figsize=(10, 10))

    # Couleurs différentes pour chaque cercle
    couleurs = ['r', 'g', 'b', 'm', 'c', 'y', 'k', 'orange', 'purple', 'brown']
    couleur_radiale = 'gray'  # Couleur pour les segments radiaux
    est_format_cartesien = not isinstance(k_noeuds[0], list)
    # Grouper les noeuds par rayon pour identifier les cercles
    noeuds_par_rayon = {}
    if est_format_cartesien:
        # Traitement des noeuds cartésiens (liste plate)
        for noeud in k_noeuds:
            # Calculer r pour le groupement
            if "r" in noeud:
                r = noeud["r"]
            else:
                r = math.sqrt(noeud["x"] ** 2 + noeud["y"] ** 2)

            if r not in noeuds_par_rayon:
                noeuds_par_rayon[r] = []

            # S'assurer que les coordonnées cartésiennes sont présentes
            if "x" not in noeud or "y" not in noeud:
                noeud["x"] = r * math.cos(noeud["theta"])
                noeud["y"] = r * math.sin(noeud["theta"])

            noeuds_par_rayon[r].append(noeud)
    else:
        # Traitement original pour les noeuds polaires (liste de listes)
        for i_cercle in range(len(k_noeuds)):
            for point in k_noeuds[i_cercle]:
                r = point["r"]
                if r not in noeuds_par_rayon:
                    noeuds_par_rayon[r] = []

                # Ajouter les coordonnées cartésiennes calculées
                x = r * math.cos(point["theta"])
                y = r * math.sin(point["theta"])
                point_avec_xy = point.copy()
                point_avec_xy["x"] = x
                point_avec_xy["y"] = y
                noeuds_par_rayon[r].append(point_avec_xy)

    # Dictionnaire pour accès rapide aux coordonnées
    noeuds_dict = {}
    for rayon, points in noeuds_par_rayon.items():
        for point in points:
            noeuds_dict[point["index"]] = (point["x"], point["y"], rayon)


    # Segments déjà tracés (pour éviter les doublons)
    segments_traces = set()

    # Tracer chaque cercle et ses points
    for i, (rayon, points) in enumerate(sorted(noeuds_par_rayon.items())):
        # Séparer les nœuds initiaux des nœuds raffinés
        points_initiaux = [point for point in points if point.get("initial", False)]
        points_raffines = [point for point in points if not point.get("initial", False)]

        # Tracer les points initiaux
        x_init = [p["x"] for p in points_initiaux]
        y_init = [p["y"] for p in points_initiaux]
        indices_init = [p["index"] for p in points_initiaux]
        if x_init:
            plt.scatter(x_init, y_init, color=couleurs[i % len(couleurs)], marker='o',
                        label=f'Cercle {i} (initial)' if i == 0 else "")

        # Tracer les points raffinés
        x_raff = [p["x"] for p in points_raffines]
        y_raff = [p["y"] for p in points_raffines]
        indices_raff = [p["index"] for p in points_raffines]
        if x_raff:
            plt.scatter(x_raff, y_raff, color=couleurs[i % len(couleurs)], marker='x',
                        label=f'Cercle {i} (raffiné)' if i == 0 else "")

        # Afficher les indices des nœuds
        for j in range(len(x_init)):
            plt.text(x_init[j] + 0.3, y_init[j] + 0.3, str(indices_init[j]), fontsize=8,
                     bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
        for j in range(len(x_raff)):
            plt.text(x_raff[j] + 0.3, y_raff[j] + 0.3, str(indices_raff[j]), fontsize=8,
                     bbox=dict(facecolor='lightyellow', alpha=0.7, edgecolor='none'))

    # Tracer les segments à partir des cellules
    if cellules:
        rayons_tries = sorted(noeuds_par_rayon.keys())
        for cellule in cellules:
            noeuds = cellule["noeuds"]
            for i in range(len(noeuds)):
                idx1 = noeuds[i]
                idx2 = noeuds[(i + 1) % len(noeuds)]

                segment_key = tuple(sorted([idx1, idx2]))
                if segment_key in segments_traces:
                    continue

                if idx1 in noeuds_dict and idx2 in noeuds_dict:
                    x1, y1, rayon1 = noeuds_dict[idx1]
                    x2, y2, rayon2 = noeuds_dict[idx2]

                    # Tracer le segment selon le type
                    if rayon1 == rayon2:  # Segment sur le même cercle
                        i_couleur = rayons_tries.index(rayon1) % len(couleurs)
                        plt.plot([x1, x2], [y1, y2],
                                 color=couleurs[i_couleur],
                                 linestyle='-', linewidth=1)
                    else:  # Segment radial
                        plt.plot([x1, x2], [y1, y2],
                                 color=couleur_radiale,
                                 linestyle='--', linewidth=0.8)

                    segments_traces.add(segment_key)

    plt.grid(True)
    plt.axis('equal')
    plt.title('Visualisation des cercles (o=initial, x=raffiné)')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.show()




#----------------------------------------------------------------------------------------------------#
#---------- VISUALISATION DES CELLULES --------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
def tracer_cellules(points, cellules):
    """ Visualise les cellules avec leur indice au centre.

        Args:
            k_noeuds_n_cercle_cartesien: Liste des noeuds en coordonnées cartésiennes
            cellules: Liste des cellules définies par leurs indices de noeuds

        Returns:
            None. Affiche un graphique avec matplotlib. """

    plt.figure(figsize=(10, 10))

    # Couleurs différentes pour colorer les cellules par groupe
    couleurs = ['r', 'g', 'b', 'm', 'c', 'y', 'k', 'orange', 'purple', 'brown']


    noeuds_dict = {} # Créer un dictionnaire pour accéder rapidement aux coordonnées des noeuds
    noeuds_initiaux = set()  # Pour distinguer les noeuds initiaux des noeuds raffinés

    for point in points:
        if isinstance(point, dict) and "index" in point:
            # Récupérer les coordonnées cartésiennes du point
            if "x" in point and "y" in point:
                noeuds_dict[point["index"]] = (point["x"], point["y"])
            elif "r" in point and "theta" in point:
                # Convertir de polaire à cartésien
                r = point["r"]
                theta = point["theta"]
                x = r * math.cos(theta)
                y = r * math.sin(theta)
                noeuds_dict[point["index"]] = (x, y)

            # Marquer les noeuds initiaux
            if point.get("initial", False):
                noeuds_initiaux.add(point["index"])

    # Identifier les rayons pour grouper les cellules (code existant)
    rayons_cellules = {}
    for cellule in cellules:
        # Code de groupement inchangé
        cell_type = cellule.get("cell_type", 0)
        if cell_type not in rayons_cellules:
            rayons_cellules[cell_type] = []
        rayons_cellules[cell_type].append(cellule)

    # Tracer les polygones des cellules
    for i, (rayon, groupe_cellules) in enumerate(sorted(rayons_cellules.items())):
        couleur = couleurs[i % len(couleurs)]
        for cellule in groupe_cellules:
            # Récupérer les coordonnées des noeuds de la cellule
            coords = []
            for noeud_idx in cellule["noeuds"]:
                if noeud_idx in noeuds_dict:
                    coords.append(noeuds_dict[noeud_idx])

            # Tracer le polygone
            if len(coords) >= 3:
                xs, ys = zip(*coords)
                plt.fill(xs, ys, alpha=0.5, color=couleur, edgecolor='black')

                # Ajouter l'indice de la cellule au centre
                centre_x = sum(xs) / len(xs)
                centre_y = sum(ys) / len(ys)
                plt.text(centre_x, centre_y, str(cellule["index"]),
                         ha='center', va='center', fontweight='bold')

    # Tracer tous les noeuds
    for noeud_idx, (x, y) in noeuds_dict.items():
        # Utiliser un marqueur différent selon le type de noeud
        marker = 'o' if noeud_idx in noeuds_initiaux else 'x'
        plt.scatter(x, y, color='black', marker=marker, s=30, zorder=3)
        plt.text(x + 0.2, y + 0.2, str(noeud_idx), fontsize=8,
                 bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

    # Tracer les segments entre noeuds consécutifs de chaque cellule
    segments_traces = set()
    for cellule in cellules:
        noeuds = cellule["noeuds"]
        for i in range(len(noeuds)):
            idx1 = noeuds[i]
            idx2 = noeuds[(i + 1) % len(noeuds)]

            segment_key = tuple(sorted([idx1, idx2]))
            if segment_key not in segments_traces and idx1 in noeuds_dict and idx2 in noeuds_dict:
                x1, y1 = noeuds_dict[idx1]
                x2, y2 = noeuds_dict[idx2]
                plt.plot([x1, x2], [y1, y2], 'k-', linewidth=1, alpha=0.7, zorder=2)
                segments_traces.add(segment_key)

    plt.grid(True)
    plt.axis('equal')
    plt.title('Visualisation des cellules avec noeuds intermédiaires')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.show()



#----------------------------------------------------------------------------------------------------#
#------------------------- MAIN ---------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------#
""" Programme principal. """


def generer_donnees():
    rayon_0 = 200
    a = [25,25,30]
    n = len(a)+1
    rapport_R_T = [1,1,0.5]
    seuil_proximite = 1
    longueur_max_cercles = 10 # Seuil pour les segments circulaires
    longueur_max_radiaux = 10 # Seuil pour les segments radiaux
    maillage = True

    rayons_n_cercles = n_cercles(n, rayon_0, a, rapport_R_T)
    k_noeuds_n_cercle_polaire_initial, index_noeud_max = creer_noeuds_initiaux(n, rayons_n_cercles, a)
    k_noeuds_n_cercle_polaire, map_indices = fusionner_noeuds(k_noeuds_n_cercle_polaire_initial, n, index_noeud_max)
    cellules_list = creer_cellules(rayons_n_cercles, k_noeuds_n_cercle_polaire, n, a)
    if not(maillage):

        #Walls
        k_noeuds_n_cercle_cartesien = polaire_vers_cartesien(k_noeuds_n_cercle_polaire)
        liste_walls = generer_walls_initiaux(k_noeuds_n_cercle_cartesien, cellules_list)
        cellules_finales = shoelace_formula(cellules_list, k_noeuds_n_cercle_cartesien)
        basearea = calculer_aire_totale_boundary(k_noeuds_n_cercle_cartesien) / (len(cellules_finales))
        #Tracé
        # tracer_points_cercles(k_noeuds_n_cercle_polaire, n, a, cellules_list)
        # tracer_cellules(polaire_vers_cartesien(k_noeuds_n_cercle_polaire, n, a), cellules_list)
        #
        # print(f"Aire totale du tissu : {basearea:.4f}")

        return k_noeuds_n_cercle_cartesien, cellules_finales, liste_walls, basearea

    else :
        k_noeuds_n_cercle_polaire_raffine, cellules_list_raffine = raffiner_maillage_separe(
            k_noeuds_n_cercle_polaire, n, cellules_list,
            longueur_max_cercles, longueur_max_radiaux,
            rayons_n_cercles, seuil_proximite
        )

        #Walls
        k_noeuds_n_cercle_cartesien_raffine = polaire_vers_cartesien(k_noeuds_n_cercle_polaire_raffine)
        liste_walls = generer_walls_initiaux(k_noeuds_n_cercle_cartesien_raffine, cellules_list_raffine)
        cellules_finales = shoelace_formula(cellules_list_raffine, k_noeuds_n_cercle_cartesien_raffine)
        basearea = calculer_aire_totale_boundary(k_noeuds_n_cercle_cartesien_raffine) / (len(cellules_finales))
        print(f"Aire totale du tissu : {basearea:.4f}")

        # Tracé
        k_noeuds_n_cercle_cartesien_raffine = polaire_vers_cartesien(k_noeuds_n_cercle_polaire_raffine)
        tracer_points_cercles(k_noeuds_n_cercle_polaire_raffine, n, a, cellules_list_raffine)
        # tracer_cellules(polaire_vers_cartesien(k_noeuds_n_cercle_polaire_raffine, n, a), cellules_list_raffine)

        return k_noeuds_n_cercle_cartesien_raffine, cellules_finales, liste_walls, basearea





    # k_noeuds_renommes, cellules_renommees, walls_renommes = reindexer_noeuds_par_cellule(
    #     k_noeuds_n_cercle_cartesien_raffine,
    #     cellules_list_raffine,
    #     liste_walls
    # )












generer_donnees()