import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom


def creer_fichier_xml_vierge(nom_fichier="structure_vierge.xml"):
    """
    Crée un fichier XML vierge avec la même structure que le fichier 'structure_vierge.xml'.
    """
    # Racine du document
    root = ET.Element("leaf")
    root.set("name", "")
    root.set("date", "")
    root.set("simtime", "")

    # Section des paramètres
    parameter = ET.SubElement(root, "parameter")

    # Liste complète des paramètres simples
    parametres_simples = [
        "arrowcolor", "arrowsize", "textcolor", "cellnumsize", "nodenumsize",
        "node_mag", "outlinewidth", "cell_outline_color", "resize_stride",
        "export_interval", "export_fn_prefix", "storage_stride", "xml_storage_stride",
        "datadir", "T", "lambda_length", "yielding_threshold", "lambda_celllength",
        "target_length", "cell_expansion_rate", "cell_div_expansion_rate",
        "auxin_dependent_growth", "ode_accuracy", "mc_stepsize", "mc_cell_stepsize",
        "energy_threshold", "bend_lambda", "alignment_lambda", "rel_cell_div_threshold",
        "rel_perimeter_stiffness", "collapse_node_threshold", "morphogen_div_threshold",
        "morphogen_expansion_threshold", "copy_wall", "source", "k1", "k2", "r", "kr",
        "km", "Pi_tot", "transport", "ka", "pin_prod", "pin_prod_in_epidermis",
        "pin_breakdown", "pin_breakdown_internal", "aux1prod", "aux1prodmeso",
        "aux1decay", "aux1decaymeso", "aux1transport", "aux_cons", "aux_breakdown",
        "kaux1", "kap", "leaf_tip_source", "sam_efflux", "sam_auxin",
        "sam_auxin_breakdown", "van3prod", "van3autokat", "van3sat", "k2van3", "dt",
        "rd_dt", "potential_slide_angle", "elastic_modulus", "movie", "nit",
        "compatibility_level", "maxt", "rseed", "constituous_expansion_limit",
        "vessel_inh_level", "vessel_expansion_rate", "d", "e", "f", "c", "mu", "nu",
        "rho0", "rho1", "c0", "gamma", "eps", "betaN", "gammaN", "betaD", "gammaD",
        "betaR", "gammaR", "tau", "kt", "kc", "krs", "i1", "i2", "b4", "dir1", "dir2"
    ]

    # Ajouter les paramètres simples
    for nom in parametres_simples:
        par = ET.SubElement(parameter, "par")
        par.set("name", nom)
        par.set("val", "")

    # Ajouter les paramètres avec tableaux
    array_params = ["D", "initval", "k"]
    for nom_array in array_params:
        par = ET.SubElement(parameter, "par")
        par.set("name", nom_array)
        valarray = ET.SubElement(par, "valarray")

        # Créer 15 éléments vides pour chaque tableau
        for _ in range(15):
            val = ET.SubElement(valarray, "val")
            val.set("v", "")

    # Section des nœuds
    nodes = ET.SubElement(root, "nodes")
    nodes.set("n", "")
    nodes.set("target_length", "")

    # Ajouter un nœud vide
    node = ET.SubElement(nodes, "node")
    node.set("nr", "")
    node.set("x", "")
    node.set("y", "")
    node.set("fixed", "")
    node.set("boundary", "")
    node.set("sam", "")

    # Forcer l'utilisation d'un commentaire vide pour garder la structure <node></node>
    node.text = ""

    # Section des cellules
    cells = ET.SubElement(root, "cells")
    cells.set("n", "")
    cells.set("offsetx", "")
    cells.set("offsety", "")
    cells.set("magnification", "")
    cells.set("base_area", "")
    cells.set("nchem", "")

    # Ajouter une cellule vide
    cell = ET.SubElement(cells, "cell")
    cell.set("index", "")
    cell.set("cell_type", "")
    cell.set("area", "")
    cell.set("target_area", "")
    cell.set("target_length", "")
    cell.set("lambda_celllength", "")
    cell.set("stiffness", "")
    cell.set("fixed", "")
    cell.set("pin_fixed", "")
    cell.set("boundary", "")
    cell.set("at_boundary", "")
    cell.set("dead", "")
    cell.set("source", "")
    cell.set("div_counter", "")

    # Forcer la structure <cell></cell>
    cell.text = "\n  "
    cell.tail = "\n  "

    # Ajouter le polygone de frontière
    boundary_polygon = ET.SubElement(cells, "boundary_polygon")
    boundary_polygon.set("index", "")
    boundary_polygon.set("cell_type", "")
    boundary_polygon.set("area", "")
    boundary_polygon.set("target_area", "")
    boundary_polygon.set("target_length", "")
    boundary_polygon.set("lambda_celllength", "")
    boundary_polygon.set("stiffness", "")
    boundary_polygon.set("fixed", "")
    boundary_polygon.set("pin_fixed", "")
    boundary_polygon.set("boundary", "")
    boundary_polygon.set("at_boundary", "")
    boundary_polygon.set("dead", "")
    boundary_polygon.set("source", "")
    boundary_polygon.set("div_counter", "")
    # Forcer la structure <boundary_polygon></boundary_polygon>
    boundary_polygon.text = "\n  "
    boundary_polygon.tail = "\n"

    # Section des parois
    walls = ET.SubElement(root, "walls")
    walls.set("n", "")
    # Forcer la structure <walls></walls>
    walls.text = "\n"

    # Section des nodesets
    nodesets = ET.SubElement(root, "nodesets")
    nodesets.set("n", "")

    # Section des paramètres d'affichage
    settings = ET.SubElement(root, "settings")

    # Paramètres d'affichage
    affichages = [
        "show_cell_centers",
        "show_nodes",
        "show_node_numbers",
        "show_cell_numbers",
        "show_border_cells",
        "show_cell_axes",
        "show_cell_strain",
        "show_fluxes",
        "show_walls",
        "save_movie_frames",
        "show_only_leaf_boundary",
        "cell_growth",
        "hide_cells"
    ]

    for nom in affichages:
        setting = ET.SubElement(settings, "setting")
        setting.set("name", nom)
        setting.set("val", "")

    # Viewport
    viewport = ET.SubElement(settings, "viewport")
    viewport.set("m11", "")
    viewport.set("m12", "")
    viewport.set("m21", "")
    viewport.set("m22", "")
    viewport.set("dx", "")
    viewport.set("dy", "")

    # Convertir en chaîne XML bien formatée
    xml_str = ET.tostring(root, encoding='utf-8')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ")

    # Enregistrer le fichier
    with open(nom_fichier, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    print(f"Fichier '{nom_fichier}' créé avec succès.")


# Créer le fichier XML vierge
creer_fichier_xml_vierge()