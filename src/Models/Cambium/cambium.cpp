/*
 *
 *  This file is part of the Virtual Leaf.
 *
 *  The Virtual Leaf is free software: you can tealistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  The Virtual Leaf is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with the Virtual Leaf.  If not, see <http://www.gnu.org/licenses/>.
 *
 *  Copyright 2010 Roeland Merks.
 *
 */

#include <QObject>
#include <QtGui>
#include <set>
#include <algorithm>

#include "parameter.h"
#include "pi.h"


#include "wallbase.h"
#include "cellbase.h"
#include "cambium.h"
#include "node.h"

static const std::string _module_id("$Id$");


/*
Cell Types and Their Behavior:

CellType(0): Bark Cells
- Elasticity defined by SetLambdaLength(0)
- Stiffness = bark_added_stiffness (default value = 1)
- Expansion rate = cell_expansion_rate * 1
- Division threshold = 10, ratio = 2
- Can transform into type 1 (Bark Cambium) if surrounded only by:
  * Type 2 cells
  * A combination of types 0 and 2
  * A combination of types 0, 1, and 2

CellType(1): Bark Cambium
- Elasticity defined by SetLambdaLength(0)
- Stiffness = cambium_added_stiffness (default value = 1)
- Expansion rate = cell_expansion_rate * 1
- Division threshold = 1, ratio = 1
- Can transform into:
  * Type 0 (Bark) if surrounded by type 0 cells or types 0 and 1
  * Type 2 (Xylem Cambium) if surrounded by cells of types 1 and 2
- During division, the daughter cell farther from the center becomes type 0, the other remains type 1

CellType(2): Xylem Cambium
- Elasticity defined by SetLambdaLength(0)
- Stiffness = cambium_added_stiffness (default value = 1)
- Expansion rate = cell_expansion_rate * 2
- Division threshold = 1, ratio = 1
- Complex transformations based on neighbors:
  * Type 1 if surrounded only by type 1
  * Type 3 if surrounded only by type 3
  * Type 4 if surrounded only by type 4 (and different from index 0)
  * Type 3 if surrounded by types 3 and 4, or types 2, 3, 4 without index 0
  * Type 3 if surrounded by more than 2 neighbors of type 3
- During division, the daughter cell farther from the center remains type 2, the other becomes type 3

CellType(3): Growing Xylem
- Elasticity defined by SetLambdaLength(0)
- Stiffness = 1.5 (fixed)
- Expansion rate = cell_expansion_rate * 2
- Can transform into type 2 if surrounded by:
  * Types 1 and 2 without other types
  * Only type 4
  * Types 1, 2, and 3 without type 4
  * Types 1, 3, and 4 without type 2
- Transforms into type 4 (Mature Xylem) when:
  * Its area exceeds 4000
  * T > 0 and R/T > 3 and area < 4000

CellType(4): Mature Xylem
- Elasticity defined by SetLambdaLength(0)
- Stiffness = mature_xylem_added_stiffness * 2 (default value = 2)
- No division (terminal cells)
- If area < 4000, expansion rate = cell_expansion_rate * 5 // Keep cell area
(it should'nt move bcs of encreased stiffness but doesnt work)

Additional Notes:
- Division rules depend on the ratio between radial (R) and tangential (T) dimensions
- If both daughter cells are at equivalent distance from the center (±5%), they retain the parent's type
- Stiffness values and expansion rates can be adjusted via model parameters
- Radial/tangential orientation is calculated by comparing the cell's principal axis with the radial direction
*/


QString cambium::ModelID(void) {
  // specify the name of your model here
  return QString( "Cambium" );
}

// return the number of chemicals your model uses
int cambium::NChem(void) { return 0; }


cambium::cambium() {

}

// Display node information for a cell
void cambium::AfficherNoeuds(CellBase *c) {
    int i = 0;
    for (list<Node *>::const_iterator it = c->getNodes().begin(); it != c->getNodes().end(); ++it, ++i) {
        // Node operations can be added here if needed
    }
}


void PrintWallStiffness(CellBase *c) {
    qDebug() << "Cell" << c->Index() << "wall stiffness values:";
    int wall_count = 0;

    c->LoopWallElements([&wall_count](auto wallElementInfo){
        double stiffness = wallElementInfo->getWallElement()->getStiffness();
        qDebug() << "  Wall element" << wall_count++ << "stiffness:" << stiffness;
    });
}

void cambium::SetCellTypeProperties(CellBase *c) { // Set cell properties
/* SetLambdaLength property notes:
   - Default value 0 for all cell mode 0
   - High values (>2) cause cells to "flow"
   - Very low values (<0.01) for bark prevent cells from moving between bark cells
   - This is the elasticity coefficient of the wall, allowing it to extend to lambda * initial value
*/
  // Define stiffness parameters for different cell types
  const double cambium_added_stiffness = 1;  // Base stiffness (used by cambium)
  const double bark_added_stiffness = 1;  // Additional stiffness for bark cells
  const double mature_xylem_added_stiffness = 1;  // Additional stiffness for mature xylem

  if (c->CellType()==0) { // Bark Cells
    c->SetLambdaLength(0);

    // Set stiffness to default + added stiffness for bark
    double stiffness =  bark_added_stiffness;
    double* p_stiffness = &stiffness;

    c->LoopWallElements([p_stiffness](auto wallElementInfo){
      wallElementInfo->getWallElement()->setStiffness(*p_stiffness);
    });
  }
  else if (c->CellType()==1 || c->CellType()==2) { // Cambium Cells
    c->SetLambdaLength(0);

    // Set stiffness to default (no modification)
    double stiffness = cambium_added_stiffness;
    double* p_stiffness = &stiffness;

    c->LoopWallElements([p_stiffness](auto wallElementInfo){
      wallElementInfo->getWallElement()->setStiffness(*p_stiffness);
    });
  }
  else if (c->CellType()==3) { // Growing Xylem Cells
    c->SetLambdaLength(0);

//    // Calculate growth progress (0.0 to 1.0)
//    double progress = (c->Area() - 4000) / (2.0 * 4000);
//    progress = std::min(1.0, std::max(0.0, progress)); // Clamp between 0 and 1
//
//    // Gradually increase stiffness from default to higher values as the cell grows
//    // Add up to 0.5 additional stiffness as the cell reaches full growth
//    double stiffness = mature_xylem_added_stiffness *(1+progress);
    double stiffness = 1.5;
    double* p_stiffness = &stiffness;

    c->LoopWallElements([p_stiffness](auto wallElementInfo){
      wallElementInfo->getWallElement()->setStiffness(*p_stiffness);
    });
  }
  else { // Mature Xylem Cells (Type 3)
    c->SetLambdaLength(0);

    // Set stiffness to default + added stiffness for mature xylem
    double stiffness = mature_xylem_added_stiffness*2;
    double* p_stiffness = &stiffness;

    c->LoopWallElements([p_stiffness](auto wallElementInfo){
      wallElementInfo->getWallElement()->setStiffness(*p_stiffness);
    });
  }
}



void cambium::SetCellColor(CellBase *c, QColor *color) {
  //cell Coloring depending on type
  if (c->CellType()==0){ // Bark
    color->setNamedColor("brown");
  }
  else if (c->CellType()==1){ // Bark Cambium
        color->setNamedColor("green");
  }
  else if (c->CellType()==2){ // Wood cambium
        color->setNamedColor("seagreen");
  }
  else if (c->CellType()==3){ // growing wood
        color->setNamedColor("darkorange");
  }
  else { // mature wood
        color->setNamedColor("Blue");
  }
}


// Method to select which parameters ill enable division and which axis
DivisionType cambium::DividingRules(CellBase *c, int division_rule_case) {
    // Déterminer l'orientation radiale/tangentielle
    auto [R, T] = DetermineRadialOrientation(c);

    // Définir seuil et ratio selon le type de cellule
    int seuil = 2; // Valeur par défaut
    int ratio = 2; // Valeur par défaut

    if (c->CellType() == 0) {
        seuil = 10;
        ratio = 2;
    }
    else if (c->CellType() == 1) {
        seuil = 1;
        ratio = 1;
    }
    else if (c->CellType() == 2) {
        seuil = 1;
        ratio = 1;
    }


    Vector axis = c->Centroid();
    Vector radial_axis = axis;
    Vector tangential_axis = axis.Perp2D();

    // Vérifier si la cellule dépasse le seuil de croissance
    bool growth_condition = c->Area() > 800*seuil;

    // Vérifier les conditions de ratio
    bool tangential_biased = (T > 0 && T/R > ratio);
    bool radial_biased = (R > 0 && R/T > ratio);

    // Traiter selon le cas de règle de division
    switch(division_rule_case) {
        case 1: // Division basée uniquement sur la croissance
            if (growth_condition) {
                std::cout << "Cellule " << c->Index() << ": Cas 1 - Division par seuil de taille" << std::endl;
                c->SetDivisionType(SHORT_AXIS);
                c->Divide();
            }
            break;

        case 2: // Division basée uniquement sur le ratio T/R
            if (tangential_biased || radial_biased) {
                std::cout << "Cellule " << c->Index() << ": Cas 2 - Division par ratio T/R" << std::endl;
                c->SetDivisionType(SHORT_AXIS);
                c->Divide();
            }
            break;

        case 3: // Division radiale ou tangentielle selon le ratio
            if (tangential_biased) {
                std::cout << "Cellule " << c->Index() << ": Cas 3 - Division radiale (T/R > seuil)" << std::endl;
                c->DivideOverAxis(radial_axis);
            } else if (radial_biased) {
                std::cout << "Cellule " << c->Index() << ": Cas 3 - Division tangentielle (R/T > seuil)" << std::endl;
                c->DivideOverAxis(tangential_axis);
            }
            break;

        case 4: // Division selon l'axe de stress
            if (tangential_biased || radial_biased) {
                std::cout << "Cellule " << c->Index() << ": Cas 4 - Division basée sur les contraintes" << std::endl;
                c->SetDivisionType(MAX_STRESS_AXIS);
                c->Divide();
            }
            break;

        case 5: // Division basée sur croissance ET ratio
            if ((growth_condition && tangential_biased) || (growth_condition && radial_biased)) {
                std::cout << "Cellule " << c->Index() << ": Cas 5 - Division par taille et ratio" << std::endl;
                c->SetDivisionType(SHORT_AXIS);
                c->Divide(); // J'ai choisi division aléatoire
            }
            break;

        case 6: // Division radiale/tangentielle basée sur croissance ET ratio
            if (growth_condition && tangential_biased) {
                std::cout << "Cellule " << c->Index() << ": Cas 6 - Division radiale (croissance + T/R)" << std::endl;
                c->DivideOverAxis(radial_axis);
            } else if (growth_condition && radial_biased) {
                std::cout << "Cellule " << c->Index() << ": Cas 6 - Division tangentielle (croissance + R/T)" << std::endl;
                c->DivideOverAxis(tangential_axis);
            }
            break;

        case 7: // Division selon l'axe de stress basée sur croissance ET ratio
            if ((growth_condition && tangential_biased) || (growth_condition && radial_biased)) {
                std::cout << "Cellule " << c->Index() << ": Cas 7 - Division par contraintes (croissance + ratio)" << std::endl;
                c->SetDivisionType(MAX_STRESS_AXIS);
                c->Divide();
            }
            break;

        default:
            std::cout << "Cellule " << c->Index() << ": Cas par défaut - Aucune règle de division spécifiée" << std::endl;
            break;
    }

    // Par défaut, ne pas diviser
    return NO_DIVISION;
}






void cambium::CellHouseKeeping(CellBase *c) {
    SetCellTypeProperties(c);
    PrintWallStiffness(c);
//    Debug pour afficher les informations sur la cellule et ses voisins
//    qDebug() << "------------------------------------------";
//    qDebug() << "Cellule" << c->Index() << "de type" << c->CellType() << "- Aire:" << c->Area();
//    qDebug() << "  Voisins de la cellule" << c->Index() << ":";

    int division_type = 1;
    auto [R, T] = DetermineRadialOrientation(c);
    std::vector<int> neighbors = c->GetNeighborIndices();

    bool has_index_0 = false;

    for (int idx : neighbors) {
        if (idx == 0) {
            has_index_0 = true;
            break; // On peut sortir dès qu'on trouve l'indice 0
        }
    }

    cell_registry[c->Index()] = c;
    static std::set<int> initialized_cells;

    if (initialized_cells.find(c->Index()) == initialized_cells.end()) {
        c->SetInitialArea();
        initialized_cells.insert(c->Index());
    }

    UpdateCellTypeLists(c->Index(), c->CellType());
        // Ne pas lancer les regles tant que toutes les cellules ne sont pas initialisées dans le cell registry
        for (int idx : neighbors) {
        CellBase* neighbor = GetCellByIndex(idx);
        if (neighbor) {
            //qDebug() << "    Cellule" << idx << "de type" << neighbor->CellType();
        }
        else {
            //qDebug() << "    Cellule" << idx << "(non trouvée dans le registre)";
        return;
        }
    }
    // Une seule boucle pour vérifier tous les types de voisins
    bool has_type0_neighbor = false;
    bool has_type1_neighbor = false;
    bool has_type2_neighbor = false;
    bool has_type3_neighbor = false;
    bool has_type4_neighbor = false;
    for (int idx : neighbors) {
        CellBase* neighbor = GetCellByIndex(idx);
        if (!neighbor) continue;
        if (neighbor->CellType() == 0) has_type0_neighbor = true;
        if (neighbor->CellType() == 1) has_type1_neighbor = true;
        if (neighbor->CellType() == 2) has_type2_neighbor = true;
        if (neighbor->CellType() == 3) has_type3_neighbor = true;
        if (neighbor->CellType() == 4) has_type4_neighbor = true;
    }

    int count_type2_neighbors = 0;
    int count_type3_neighbors = 0;
    for (int idx : neighbors) {
        CellBase* neighbor = GetCellByIndex(idx);
        if (!neighbor) continue;
        if (neighbor->CellType() == 2) {
            count_type2_neighbors++;
        }
    }

    for (int idx : neighbors) {
        CellBase* neighbor = GetCellByIndex(idx);
        if (!neighbor) continue;
        if (neighbor->CellType() == 3) {
            count_type3_neighbors++;
        }
    }


    if (c->CellType() == 0) { // Bark
        //Si entourées uniquement de type 2
        if (!has_type0_neighbor &&  !has_type1_neighbor && has_type2_neighbor && !has_type3_neighbor && !has_type4_neighbor) {
            c->SetCellType(1);
            UpdateCellTypeLists(c->Index(), 1);
            return;
        }
        // Si entouré de type 0 et 2 (a desactiver pour le cambium simple de type 2, sinon transfo direct en ecorce)
        else if (has_type0_neighbor &&  !has_type1_neighbor && has_type2_neighbor && !has_type3_neighbor && !has_type4_neighbor) {
            c->SetCellType(1);
            UpdateCellTypeLists(c->Index(), 1);
            return;
        }
                // Si entouré de type 0 1 et 2
        else if (has_type0_neighbor &&  has_type1_neighbor && has_type2_neighbor && !has_type3_neighbor && !has_type4_neighbor) {
            c->SetCellType(1);
            UpdateCellTypeLists(c->Index(), 1);
            return;
        }

        else {
            c->EnlargeTargetArea(par->cell_expansion_rate*1);
            DividingRules(c, division_type);
        }
    }

    else if (c->CellType() == 1) { // Bark cambium

        int count_type1_neighbors = 0;

        for (int idx : neighbors) {
            CellBase* neighbor = GetCellByIndex(idx);
            if (!neighbor) continue;
            if (neighbor->CellType() == 1) {
                count_type1_neighbors++;
            }
        }
        // Si entouré de type 0
        if (has_type0_neighbor &&  !has_type1_neighbor && !has_type2_neighbor && !has_type3_neighbor && !has_type4_neighbor) {
            c->SetCellType(0);
            UpdateCellTypeLists(c->Index(), 0);
            return;
        }
        // Si entouré de type 0 et 1
        else if(has_type0_neighbor && has_type1_neighbor && !has_type2_neighbor &&  !has_type3_neighbor && !has_type4_neighbor) {
            c->SetCellType(0);
            UpdateCellTypeLists(c->Index(), 0);

            return;
        }
        // Si voisins type 1 et type 2
        else if (!has_type0_neighbor && has_type1_neighbor && has_type2_neighbor && !has_type3_neighbor && !has_type4_neighbor) {
            c->SetCellType(2);
            UpdateCellTypeLists(c->Index(), 2);
            return;
        }

        else {
            c->EnlargeTargetArea(par->cell_expansion_rate*1);
            DividingRules(c, division_type);
        }
    }

    else if (c->CellType() == 2) { // Xylem Cambium


        // Si entourées uniquement par type 1
        if (!has_type0_neighbor && !has_type2_neighbor && !has_type3_neighbor && !has_type4_neighbor) {
            c->SetCellType(1);
            UpdateCellTypeLists(c->Index(), 1);
            return;
        }
        // Si entourées uniquement par type 3
        else if (!has_type0_neighbor && !has_type1_neighbor && !has_type2_neighbor && has_type3_neighbor && !has_type4_neighbor) {
            c->SetCellType(3);
            UpdateCellTypeLists(c->Index(), 3);
            return;
        }
        // Si entourées uniquement par type 4 et différent de l'index 0
        else if (!has_type0_neighbor && !has_type1_neighbor && !has_type2_neighbor && !has_type3_neighbor && has_type4_neighbor && !has_index_0) {
            c->SetCellType(4);
            UpdateCellTypeLists(c->Index(), 4);
            return;
        }

        // Si entourée uniquement par type 1 et 2
        else if (!has_type0_neighbor && has_type1_neighbor && has_type2_neighbor && !has_type3_neighbor && !has_type4_neighbor) {
            c->SetCellType(2);
            UpdateCellTypeLists(c->Index(), 2);
            return;
        }
        // Si entourée uniquement par type 3 et 4
        else if (!has_type0_neighbor && !has_type1_neighbor && !has_type2_neighbor && has_type3_neighbor && has_type4_neighbor) {
            c->SetCellType(3);
            UpdateCellTypeLists(c->Index(), 3);
            return;
        }

        //Si entourée par type 2 3 et 4 sans indice 0
        else if (!has_type0_neighbor && !has_type1_neighbor && has_type2_neighbor && has_type3_neighbor && has_type4_neighbor && !has_index_0) {
            c->SetCellType(3);
            UpdateCellTypeLists(c->Index(), 3);
            return;
        }
        // Si entouré type 2 3 et 4 (=! indice 0)
        else if (!has_type0_neighbor && !has_type1_neighbor && has_type2_neighbor && has_type3_neighbor && has_type4_neighbor && !has_index_0) {
            c->SetCellType(3);
            UpdateCellTypeLists(c->Index(), 3);
            return;
        }
        else if (!has_type0_neighbor && !has_type1_neighbor && count_type3_neighbors > 2 && has_type2_neighbor && has_type3_neighbor && !has_type4_neighbor && !has_index_0) {
            c->SetCellType(3);
            UpdateCellTypeLists(c->Index(), 3);
            return;
        }
        else if (!has_type0_neighbor && !has_type1_neighbor && count_type3_neighbors >= 2 && count_type2_neighbors >=2 && has_type2_neighbor && has_type3_neighbor && !has_type4_neighbor && !has_index_0) {
            c->SetCellType(3);
            UpdateCellTypeLists(c->Index(), 3);
            return;
        }
        else if (!has_type0_neighbor && !has_type1_neighbor && has_type2_neighbor && !has_type3_neighbor && !has_type4_neighbor && !has_index_0) {
            c->SetCellType(3);
            UpdateCellTypeLists(c->Index(), 3);
            return;
        }

        else {
            c->EnlargeTargetArea(par->cell_expansion_rate*2);
            DividingRules(c, division_type);
        }
    }

    else if (c->CellType() == 3) { // Growing Xylem

        // Si entourée par un type 1 et 2
        if (!has_type0_neighbor && has_type1_neighbor && has_type2_neighbor && !has_type3_neighbor && !has_type4_neighbor) {
            c->SetCellType(2);
            UpdateCellTypeLists(c->Index(), 2);
            return;
        }

        // Si entourée par un type 1 2 et 3
        else if (!has_type0_neighbor && has_type1_neighbor && has_type2_neighbor && has_type3_neighbor && !has_type4_neighbor) {
            c->SetCellType(2);
            UpdateCellTypeLists(c->Index(), 2);
            return;
        }
//        // Si entourée par un type 0 2 3 et 4 (à activer pour le cambium simple)
//        else if (has_type0_neighbor && !has_type1_neighbor && has_type2_neighbor && has_type3_neighbor && has_type4_neighbor) {
//            c->SetCellType(2);
//            UpdateCellTypeLists(c->Index(), 2);
//            return;
//        }
//        // Si entourée par un type 0 2 3 (à activer pour le cambium simple)
//        else if (has_type0_neighbor && !has_type1_neighbor && has_type2_neighbor && has_type3_neighbor && !has_type4_neighbor) {
//            c->SetCellType(2);
//            UpdateCellTypeLists(c->Index(), 2);
//            return;
//        }
//                // Si entourée par un type 0 2 4 (à activer pour le cambium simple)
//        else if (has_type0_neighbor && !has_type1_neighbor && has_type2_neighbor && !has_type3_neighbor && has_type4_neighbor && count_type2_neighbors > 2) {
//            c->SetCellType(2);
//            UpdateCellTypeLists(c->Index(), 2);
//            return;
//        }

                // Si entourée par un type 1,2,4
        else if (!has_type0_neighbor && has_type1_neighbor && has_type2_neighbor && !has_type3_neighbor && has_type4_neighbor) {
            c->SetCellType(2);
            UpdateCellTypeLists(c->Index(), 2);
            return;
        }
        // Si entourée par un type 1 3 et 4
        else if (!has_type0_neighbor && has_type1_neighbor && !has_type2_neighbor && has_type3_neighbor && has_type4_neighbor) {
            c->SetCellType(2);
            UpdateCellTypeLists(c->Index(), 2);
            return;
        }

//        // Si entourée par un type 2 3 et 4 ( à activer pour le cambium simple)
//        else if (!has_type0_neighbor && !has_type1_neighbor && has_type2_neighbor && has_type3_neighbor && has_type4_neighbor) {
//            c->SetCellType(2);
//            UpdateCellTypeLists(c->Index(), 2);
//            return;
//        }
        else{

            if (c->Area() < 4000) {
                c->EnlargeTargetArea(par->cell_expansion_rate*2);
                return;
            }

            else if (T > 0 && R/T > 3 && c->Area() < 4000 ) {
                c->SetCellType(4);
                UpdateCellTypeLists(c->Index(),4);
                return;
            }

            else {
                c->SetCellType(4);    // Debug pour afficher les informations sur la cellule et ses voisins
                UpdateCellTypeLists(c->Index(),4);
                return;
            }
        }

    }
    else if (c->CellType() == 4) { // Mature Xylem
        // Aucune croissance ou division pour les cellules de type 4
        // Ce sont des cellules finales/terminales
        if (c->Area() < 4000) {
                c->EnlargeTargetArea(par->cell_expansion_rate*5);
        return;
        }
    }
}



void cambium::OnDivide(ParentInfo *parent_info, CellBase *daughter1, CellBase *daughter2) {
    // Centre du tissu
    Vector tissue_center(0.0, 0.0, 0.0);

    // Distances au centre
    double d_parent = (parent_info->ParentCentroid- tissue_center).Norm();
    double d1 = (daughter1->Centroid() - tissue_center).Norm();
    double d2 = (daughter2->Centroid() - tissue_center).Norm();

    // Tolérance pour "proche"
    double tol = 0.05 * d_parent; // 5% de la distance du parent

    int ParentCellType = parent_info->ParentCellType;
//    qDebug() <<"Parent type"<< parent_info->ParentCellType;
//    qDebug() <<"Parent centroid"<< parent_info->ParentCentroid;

    if (fabs(d1 - d_parent) < tol && fabs(d2 - d_parent) < tol) {
        // Les deux filles gardent le type du parent
        daughter1->SetCellType(ParentCellType);
        daughter2->SetCellType(ParentCellType);

    }
    else {
        if (ParentCellType == 1) {
            if (d1 > d2) {
                daughter1->SetCellType(0);
                daughter2->SetCellType(1);
            } else {
                daughter1->SetCellType(1);
                daughter2->SetCellType(0);
            }
        }
        else if (ParentCellType == 2) {
            if (d1 > d2) {
                daughter1->SetCellType(2);
                daughter2->SetCellType(3);
            }
            else {
                daughter1->SetCellType(3);
                daughter2->SetCellType(2);
            }
        }
        // Ajoute d'autres cas si besoin
    }
    UpdateCellTypeLists(daughter1->Index(), daughter1->CellType());
    UpdateCellTypeLists(daughter2->Index(), daughter2->CellType());
}


CellBase* cambium::GetCellByIndex(int idx) {
    auto it = cell_registry.find(idx);
    if (it != cell_registry.end()) {
        return it->second;
    }
    return nullptr;
}


void cambium::CelltoCellTransport(Wall *w, double *dchem_c1, double *dchem_c2) {
  // add biochemical transport rules here
}

void cambium::WallDynamics(Wall *w, double *dw1, double *dw2) {
  // add biochemical networks for reactions occuring at walls here
}

void cambium::CellDynamics(CellBase *c, double *dchem) {
  // add biochemical networks for intracellular reactions here
}

void cambium::UpdateCellTypeLists(int idx, int type) {
    // Retirer l'index de l'ancienne liste si le type a changé
    if (last_cell_types.count(idx) && last_cell_types[idx] != type) {
        int old_type = last_cell_types[idx];
        std::vector<int>* old_list = nullptr;
        if (old_type == 0) old_list = &bark_cells;
        else if (old_type == 1) old_list = &bark_cambium_cells;
        else if (old_type == 2) old_list = &xylem_cambium_cells;
        else if (old_type == 3) old_list = &growing_xylem_cells;
        else if (old_type == 4) old_list = &mature_xylem_cells;

        if (old_list) {
            old_list->erase(std::remove(old_list->begin(), old_list->end(), idx), old_list->end());
        }
    }

    // Ajouter l'index à la bonne liste si absent
    std::vector<int>* new_list = nullptr;
    if (type == 0) new_list = &bark_cells;
    else if (type == 1) new_list = &bark_cambium_cells;
    else if (type == 2) new_list = &xylem_cambium_cells;
    else if (type == 3) new_list = &growing_xylem_cells;
    else if (type == 4) new_list = &mature_xylem_cells;

    if (new_list && std::find(new_list->begin(), new_list->end(), idx) == new_list->end()) {
        new_list->push_back(idx);
    }

    // IMPORTANT : Mettre à jour le type dans cell_registry
    if (cell_registry.find(idx) != cell_registry.end() && cell_registry[idx]) {
        cell_registry[idx]->SetCellType(type);
    }

    last_cell_types[idx] = type;
}


std::pair<double, double> cambium::DetermineRadialOrientation(CellBase *c) {
    // Récupérer les dimensions et l'axe principal de la cellule
    auto [length, width, long_axis] = c->GetLengthAndWidthWithAxis();

    // Calculer le vecteur radial (du centre 0,0 vers le centre de la cellule)
    Vector radial_vector = c->Centroid();
    double radial_magnitude = radial_vector.Norm();

    // Éviter la division par zéro pour les cellules trop proches du centre
    if (radial_magnitude < 1e-6) {
        return std::make_pair(length, width); // Par défaut radial
    }

    // Normaliser les vecteurs pour comparer uniquement leur direction
    long_axis.Normalise();
    radial_vector.Normalise();

    // Calculer le vecteur perpendiculaire à long_axis dans le plan XY
    Vector perp_long_axis(-long_axis.y, long_axis.x, 0);

    // Calculer les angles entre le vecteur radial et les deux axes
    double dot_long = long_axis.x * radial_vector.x + long_axis.y * radial_vector.y;
    double dot_perp = perp_long_axis.x * radial_vector.x + perp_long_axis.y * radial_vector.y;

    // Limiter les produits scalaires pour éviter les erreurs numériques
    dot_long = std::min(1.0, std::max(-1.0, dot_long));
    dot_perp = std::min(1.0, std::max(-1.0, dot_perp));

    double angle_long_rad = acos(fabs(dot_long));
    double angle_perp_rad = acos(fabs(dot_perp));

    double angle_long_deg = angle_long_rad * 180.0 / M_PI;
    double angle_perp_deg = angle_perp_rad * 180.0 / M_PI;

    // Si l'angle avec long_axis est plus petit que l'angle avec l'axe perpendiculaire, orientation radiale
    bool is_radial_orientation = (angle_long_deg < angle_perp_deg);

    // Assigner les valeurs R et T selon l'orientation
    double R, T;
    if (is_radial_orientation) {
        // Le long_axis est plus aligné avec la direction radiale
        R = length;
        T = width;
    } else {
        // Le long_axis est plus aligné avec la direction tangentielle
        R = width;
        T = length;
    }

    // Afficher pour le débogage
    qDebug() << "Cellule =" << c->Index()
             << ": Base Area =" << c->GetInitialArea()
             << ": Area =" << c->Area()
             << ": Angle long_axis-radial =" << angle_long_deg
             << "°, Angle perp-radial =" << angle_perp_deg
             << "° - Orientation:" << (is_radial_orientation ? "Radiale" : "Tangentielle")
             << " R =" << R << ", T =" << T;

    return std::make_pair(R, T);
    }
//Q_EXPORT_PLUGIN2(cambium, cambium)