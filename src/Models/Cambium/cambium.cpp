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

#include "parameter.h"
#include "pi.h"

#include "wallbase.h"
#include "cellbase.h"
#include "cambium.h"
#include "node.h"

static const std::string _module_id("$Id$");

/*
Cell Types and Their Behavior:

CellType(0) : Bark Cells
- Can grow slightly (prevents potential bugs if restricted completely).
- Cannot divide.
- Stiffness = 5 × Cambium stiffness.

CellType(1) : Cambium Cells
- Can grow until a specific threshold is reached.
- Upon reaching the threshold, the cell divides:
    - If only one daughter cell is in contact with the bark, it becomes CellType(1) (Cambium), and the other becomes CellType(2) (Growing Xylem).
    - If both daughter cells are in contact with the bark, both become CellType(1).

CellType(2) : Growing Xylem Cells
- Can grow until they reach a threshold of 3 × BaseArea().
- Cannot divide.
- When growth limit is reached, they transform into CellType(3) (Mature Xylem).

CellType(3) : Mature Xylem Cells
- Cannot grow or divide.
- Stiffness = 5 × Cambium stiffness.
*/



QString cambium::ModelID(void) {
  // specify the name of your model here
  return QString( "Cambium" );
}

// return the number of chemicals your model uses
int cambium::NChem(void) { return 0; }

// Constructor - initializes the bark_cells vector
cambium::cambium() {
//    // Initialize bark cells with the original values
//    bark_cells = {}; // Bark cells list
//    GX_cells = {}; // Growing Xylem list
//    MX_cells{}; // Mature Xylem list

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
  const double cambium_added_stiffness = 0;  // Base stiffness (used by cambium)
  const double bark_added_stiffness = 0;  // Additional stiffness for bark cells
  const double mature_xylem_added_stiffness = 0;  // Additional stiffness for mature xylem

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

    // Calculate growth progress (0.0 to 1.0)
    double progress = (c->Area() - c->BaseArea()) / (2.0 * c->BaseArea());
    progress = std::min(1.0, std::max(0.0, progress)); // Clamp between 0 and 1

    // Gradually increase stiffness from default to higher values as the cell grows
    // Add up to 0.5 additional stiffness as the cell reaches full growth
    double stiffness = mature_xylem_added_stiffness * progress;
    double* p_stiffness = &stiffness;

    c->LoopWallElements([p_stiffness](auto wallElementInfo){
      wallElementInfo->getWallElement()->setStiffness(*p_stiffness);
    });
  }
  else { // Mature Xylem Cells (Type 3)
    c->SetLambdaLength(0);

    // Set stiffness to default + added stiffness for mature xylem
    double stiffness = mature_xylem_added_stiffness;
    double* p_stiffness = &stiffness;

    c->LoopWallElements([p_stiffness](auto wallElementInfo){
      wallElementInfo->getWallElement()->setStiffness(*p_stiffness);
    });
  }
}

void cambium::SetCellColor(CellBase *c, QColor *color) {
  //cell Coloring depending on type
  if (c->CellType()==0){
    color->setNamedColor("red");
  }
  else if (c->CellType()==1){
        color->setNamedColor("seagreen");
  }
  else if (c->CellType()==2){
        color->setNamedColor("green");
  }
  else if (c->CellType()==3){
        color->setNamedColor("darkorange");
  }
  else {
        color->setNamedColor("Blue");
  }
}




//void cambium::OnDivide(ParentInfo *parent_info, CellBase *daughter1, CellBase *daughter2) {
//    // Rules to be executed after cell division
//
//    // Check if this is a special division
//    int parent_id1 = daughter1->Index(); // Get parent ID via daughter cell
//    int parent_id2 = daughter2->Index();
//    if (special_division_cells.find(parent_id1) != special_division_cells.end() or special_division_cells.find(parent_id2) != special_division_cells.end() ) {
//        // Determine which daughter cell is closer to the exterior
//        bool d1_more_exposed = false;
//
//        // Count exposed nodes for each daughter cell
//        int d1_exposed_nodes = 0;
//        int d2_exposed_nodes = 0;
//
//        for (auto node_it = daughter1->getNodes().begin(); node_it != daughter1->getNodes().end(); ++node_it) {
//            if ((*node_it)->BoundaryP()) d1_exposed_nodes++;
//        }
//
//        for (auto node_it = daughter2->getNodes().begin(); node_it != daughter2->getNodes().end(); ++node_it) {
//            if ((*node_it)->BoundaryP()) d2_exposed_nodes++;
//        }
//
//        d1_more_exposed = (d1_exposed_nodes > d2_exposed_nodes);
//
//        // Transform the more exposed cell into bark, the other remains cambium
//        if (d1_more_exposed) {
//            daughter1->SetCellType(0);  // Bark
//            daughter2->SetCellType(1);  // Cambium
//
//            // Add the new bark cell to our list
//            bark_cells.push_back(daughter1->Index());
//        } else {
//            daughter1->SetCellType(1);  // Cambium
//            daughter2->SetCellType(0);  // Bark
//
//            // Add the new bark cell to our list
//            bark_cells.push_back(daughter2->Index());
//        }
//
//        // Remove the cell from our set after processing
//        special_division_cells.erase(parent_id1);
//        special_division_cells.erase(parent_id2);
//        return;
//    }
//
//
//    // Construct neighbor lists for both daughter cells
//    daughter1->GetNeighborIndices();
//    daughter2->GetNeighborIndices();
//    // Get neighbor indices for both daughter cells
//    std::vector<int> d1_neighbor_indices = daughter1->GetNeighborIndices();
//    std::vector<int> d2_neighbor_indices = daughter2->GetNeighborIndices();
//
//    // Check if daughter cells are neighbors with any bark cells
//    bool d1_neighbors_bark = false;
//    bool d2_neighbors_bark = false;
//
//    // Check daughter1's neighbors
//    for (auto idx : d1_neighbor_indices) {
//        if (std::find(bark_cells.begin(), bark_cells.end(), idx) != bark_cells.end()) {
//            d1_neighbors_bark = true; // daughter1 has a neighbor bark cell
//        }
//    }
//
//    // Check daughter2's neighbors
//    for (auto idx : d2_neighbor_indices) {
//        if (std::find(bark_cells.begin(), bark_cells.end(), idx) != bark_cells.end()) {
//            d2_neighbors_bark = true; // daughter1 has a neighbor bark cell
//        }
//    }
//
//    // Handle the case where both daughter cells are neighbors to bark cells
//    if (d1_neighbors_bark && d2_neighbors_bark) {
//        // Both cells become type 1 (Cambium cells)
//        daughter1->SetCellType(1);
//        daughter2->SetCellType(1);
//    }
//    // Handle cases where only one daughter cell is neighbor to bark cells
//    else if (d1_neighbors_bark) { // Daughter 1 is neighbor to a bark cell
//        daughter1->SetCellType(1); // Daughter 1 becomes a Cambium cell on division
//        daughter2->SetCellType(2); // Daughter 2 becomes a Growing Xylem on division
//    }
//    else if (d2_neighbors_bark) {// Daughter 2 is neighbor to a bark cell
//        daughter1->SetCellType(2);// Daughter 1 becomes a Growing Xylem on division
//        daughter2->SetCellType(1);// Daughter 2 becomes a Cambium cell on division
//    }
//    else { // Neither are neighbor to a bark cell.
//        daughter1->SetCellType(2);// Daughter 1 becomes a Growing Xylem cell on division
//        daughter2->SetCellType(2);// Daughter 2 becomes a Growing Xylem cell on division
//    }
//}


void cambium::CellHouseKeeping(CellBase *c) { // How cells behave after division
  // Set initial area on first call to this function for each cell

    cell_registry[c->Index()] = c;
    static std::set<int> initialized_cells;

    if (initialized_cells.find(c->Index()) == initialized_cells.end()) {
        c->SetInitialArea();
        initialized_cells.insert(c->Index());
    }

    UpdateCellTypeLists(c->Index(), c->CellType());

    if (c->CellType() == 1 || c->CellType()==2) {

        if (c->CellType() == 1 && c->Area() > 500) {
            std::vector<int> neighbors = c->GetNeighborIndices();
            bool has_type3_neighbor = false;
            bool has_type4_neighbor = false;
            for (int idx : neighbors) {
            CellBase* neighbor = GetCellByIndex(idx);
                if (!neighbor) continue;
                if (neighbor->CellType() == 3) has_type3_neighbor = true;
                if (neighbor->CellType() == 4) has_type4_neighbor = true;
        }
    if (has_type3_neighbor && has_type4_neighbor ) {
        special_division_cells.insert(c->Index());
        c->Divide();
        return;
    }
}
    if (c->CellType() == 2) {
        std::vector<int> neighbors = c->GetNeighborIndices();
        bool has_type1_neighbor = false;
        for (int idx : neighbors) {
            CellBase* neighbor = GetCellByIndex(idx);
            if (neighbor && neighbor->CellType() == 1) {
                has_type1_neighbor = true;
                break;
            }
        }
        if (!has_type1_neighbor) {
            c->SetCellType(0); // Devient une cellule de type 0 (bark)
            UpdateCellTypeLists(c->Index(), 0);
            return;
        }
    }

    c->EnlargeTargetArea(par->cell_expansion_rate);
    if (c->Area() > par->rel_cell_div_threshold * c->BaseArea()) {
      c->Divide();
    }
//    std::pair<double, double> lengthAndWidth = c->GetLengthAndWidth();
//    double longueur = lengthAndWidth.first;
//    double largeur  = lengthAndWidth.second;
//    std::cout << "Longueur : " << longueur << ", Largeur : " << largeur << std::endl;
//
//    if (c->Area() > par->rel_cell_div_threshold * c->BaseArea()) || (largeur / longueur <= 0.25) {
//    // Critère atteint, déclencher la division
//    cell->Divide(); // ou la méthode appropriée pour diviser la cellule
//    }

  }
  else if(c->CellType() == 3) { // If cell is a type 3, grow until it reach 3*BaseArea then transform into a Type 4
    if (c->Area() > 500) {
        std::vector<int> neighbors = c->GetNeighborIndices();
        bool has_type2_neighbor = false;
        for (int idx : neighbors) {
            CellBase* neighbor = GetCellByIndex(idx);
            if (neighbor && neighbor->CellType() == 2) {
                has_type2_neighbor = true;
                break;
            }
        }

        if (has_type2_neighbor) {
            // Déclencher la division spéciale
            special_division_cells.insert(c->Index());
            c->Divide();
            return;
        }
    }
    else if (c->Area() < 3 * c->BaseArea()) {
      c->EnlargeTargetArea(par->cell_expansion_rate);
    }

    else {
      c->SetCellType(4); // Set grown Type 2 cell to a Type 3
    }
  }


  else if (c->CellType() == 0) {
  /* If the cell is a bark cell (type 0), we need to slightly enlarge it to prevent excessive stretching,
     which could cause issues in the simulation. This adjustment ensures stability during runtime. */
    if (c->Area() > 500){
    std::vector<int> neighbors = c->GetNeighborIndices();
    bool has_type1_neighbor = false;

    for (int idx : neighbors) {
        CellBase* neighbor = GetCellByIndex(idx);
        if (neighbor && neighbor->CellType() == 1) {
            has_type1_neighbor = true;
            break;
        }
    }

    if (has_type1_neighbor) {
        // Déclencher la division spéciale
        special_division_cells.insert(c->Index());
        c->Divide();
        return;
    }
    }
    else {
        c->EnlargeTargetArea(par->cell_expansion_rate);
    }


//  // Get current area values
//  double area = c->Area();
//  double baseArea = c->BaseArea();
//
//  // Use static maps to store growth data for each cell by its index
//  static std::map<int, double> growth_additions;
//  static std::map<int, int> last_growth_step;
//  static int current_step = 0;
//
//  // Increment step counter each time function is called (simulation step)
//  current_step++;
//
//  // Initialize growth addition for this cell if not present
//  if (growth_additions.find(c->Index()) == growth_additions.end()) {
//    growth_additions[c->Index()] = 0.0;
//    last_growth_step[c->Index()] = 0;
//  }
//
//  // Check if we need to increase the growth_addition (every 500 simulation steps)
//  if (current_step - last_growth_step[c->Index()] >= 200) {
//
//    // Increase growth_addition by 25% of baseArea
//    growth_additions[c->Index()] += baseArea * 0.25;
//    // Update last growth step
//    last_growth_step[c->Index()] = current_step;
//
//    if (c->Index() == 28) {
//      qDebug() << "Cell 28 - GROWTH UPDATE - Step:" << current_step
//               << "New Growth Addition:" << growth_additions[c->Index()];
//    }
//  }
//
//  // Use effective base area (original baseArea + growth_addition)
//  double effective_base_area = baseArea + growth_additions[c->Index()];
//
//  // Maintain effective base area if cell has shrunk
//  if (area < effective_base_area) {
//    // Gradually increase target area to reach effective base area
//    c->EnlargeTargetArea(par->cell_expansion_rate);
//
//    if (c->Index() == 28) {
//      qDebug() << "Cell 28 - ENLARGING TARGET AREA - Step:" << current_step
//               << "Effective base area:" << effective_base_area
//               << "Current area:" << area
//               << "Target area:" << c->TargetArea()
//               << "Rate:" << par->cell_expansion_rate;
//    }
//  }
}
}



//Test rouges

// src/Models/Cambium/cambium.cpp

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
    qDebug() <<"Parent type"<< parent_info->ParentCellType;
    qDebug() <<"Parent centroid"<< parent_info->ParentCentroid;

    if (fabs(d1 - d_parent) < tol && fabs(d2 - d_parent) < tol) {
        // Les deux filles gardent le type du parent
        daughter1->SetCellType(ParentCellType);
        daughter2->SetCellType(ParentCellType);

    }
    else {
        if (ParentCellType == 1) {
            // La plus éloignée reste 1, l'autre devient 3
            if (d1 > d2) {
                daughter1->SetCellType(1);
                daughter2->SetCellType(3);
            } else {
                daughter1->SetCellType(3);
                daughter2->SetCellType(1);
            }
        } else if (ParentCellType == 2) {
        qDebug() << "je susi dans la boucle de selection des types";
            // La plus proche reste 2, l'autre devient 0
            if (d1 < d2) {
                daughter1->SetCellType(2);
                daughter2->SetCellType(0);
            } else {
                daughter1->SetCellType(0);
                daughter2->SetCellType(2);
            }
        }
        // Ajoute d'autres cas si besoin
    }
    int parent_id1 = daughter1->Index();
    int parent_id2 = daughter2->Index();

    if (special_division_cells.find(parent_id1) != special_division_cells.end() ||
        special_division_cells.find(parent_id2) != special_division_cells.end()) {
        if (ParentCellType == 3) {
            // Cherche si une des filles touche une cellule de type 2
            bool d1_touche_type2 = false;
            bool d2_touche_type2 = false;

            std::vector<int> d1_neighbors = daughter1->GetNeighborIndices();
            std::vector<int> d2_neighbors = daughter2->GetNeighborIndices();

            for (int idx : d1_neighbors) {
                CellBase* neighbor = GetCellByIndex(idx);
                if (neighbor && neighbor->CellType() == 2) {
                    d1_touche_type2 = true;
                    break;
                }
            }
            for (int idx : d2_neighbors) {
                CellBase* neighbor = GetCellByIndex(idx);
                if (neighbor && neighbor->CellType() == 2) {
                    d2_touche_type2 = true;
                    break;
                }
            }

            // Applique la règle : la fille touchant type 2 devient type 1, l’autre type 3
            if (d1_touche_type2 && !d2_touche_type2) {
                daughter1->SetCellType(1);
                daughter2->SetCellType(3);
            }
            else if (!d1_touche_type2 && d2_touche_type2) {
                daughter1->SetCellType(3);
                daughter2->SetCellType(1);
            }
            else {
                // Si aucune ou les deux touchent type 2, comportement par défaut
                daughter1->SetCellType(3);
                daughter2->SetCellType(3);
            }

            // Nettoyage du set
            special_division_cells.erase(parent_id1);
            special_division_cells.erase(parent_id2);

            // Met à jour les listes de types
            UpdateCellTypeLists(daughter1->Index(), daughter1->CellType());
            UpdateCellTypeLists(daughter2->Index(), daughter2->CellType());
            return;
        }

        else if (ParentCellType == 0) {
        // Cherche si une des filles touche une cellule de type 2
            bool d1_touche_type1 = false;
            bool d2_touche_type1 = false;

            std::vector<int> d1_neighbors = daughter1->GetNeighborIndices();
            std::vector<int> d2_neighbors = daughter2->GetNeighborIndices();

            for (int idx : d1_neighbors) {
                CellBase* neighbor = GetCellByIndex(idx);
                if (neighbor && neighbor->CellType() == 1) {
                    d1_touche_type1 = true;
                    break;
                }
            }
            for (int idx : d2_neighbors) {
                CellBase* neighbor = GetCellByIndex(idx);
                if (neighbor && neighbor->CellType() == 1) {
                    d2_touche_type1 = true;
                    break;
                }
            }

            // Applique la règle : la fille touchant type 2 devient type 1, l’autre type 3
             // Applique la règle : la fille touchant type 1 devient type 2, l’autre type 0
            if (d1_touche_type1 && !d2_touche_type1) {
                daughter1->SetCellType(2);
                daughter2->SetCellType(0);
            }
            else if (!d1_touche_type1 && d2_touche_type1) {
                daughter1->SetCellType(0);
                daughter2->SetCellType(2);
            }
            else {
                daughter1->SetCellType(0);
                daughter2->SetCellType(0);
            }

            // Nettoyage du set
            special_division_cells.erase(parent_id1);
            special_division_cells.erase(parent_id2);

            // Met à jour les listes de types
            UpdateCellTypeLists(daughter1->Index(), daughter1->CellType());
            UpdateCellTypeLists(daughter2->Index(), daughter2->CellType());
            return;
            }

        else if (ParentCellType == 0) {
        // Cherche si une des filles touche une cellule de type 2
            bool d1_touche_type1 = false;
            bool d2_touche_type1 = false;

            std::vector<int> d1_neighbors = daughter1->GetNeighborIndices();
            std::vector<int> d2_neighbors = daughter2->GetNeighborIndices();

            for (int idx : d1_neighbors) {
                CellBase* neighbor = GetCellByIndex(idx);
                if (neighbor && neighbor->CellType() == 1) {
                    d1_touche_type1 = true;
                    break;
                }
            }
            for (int idx : d2_neighbors) {
                CellBase* neighbor = GetCellByIndex(idx);
                if (neighbor && neighbor->CellType() == 1) {
                    d2_touche_type1 = true;
                    break;
                }
            }

            // Applique la règle : la fille touchant type 2 devient type 1, l’autre type 3
             // Applique la règle : la fille touchant type 1 devient type 2, l’autre type 0
            if (d1_touche_type1 && !d2_touche_type1) {
                daughter1->SetCellType(2);
                daughter2->SetCellType(0);
            }
            else if (!d1_touche_type1 && d2_touche_type1) {
                daughter1->SetCellType(0);
                daughter2->SetCellType(2);
            }
            else {
                daughter1->SetCellType(0);
                daughter2->SetCellType(0);
            }

            // Nettoyage du set
            special_division_cells.erase(parent_id1);
            special_division_cells.erase(parent_id2);

            // Met à jour les listes de types
            UpdateCellTypeLists(daughter1->Index(), daughter1->CellType());
            UpdateCellTypeLists(daughter2->Index(), daughter2->CellType());
            return;
            }

        else if (ParentCellType == 1) {
            // Cherche si une des filles touche une cellule de type 4
            bool d1_touche_type4 = false;
            bool d2_touche_type4 = false;

            std::vector<int> d1_neighbors = daughter1->GetNeighborIndices();
            std::vector<int> d2_neighbors = daughter2->GetNeighborIndices();

            for (int idx : d1_neighbors) {
                CellBase* neighbor = GetCellByIndex(idx);
                if (neighbor && neighbor->CellType() == 4) {
                    d1_touche_type4 = true;
                    break;
                }
            }
            for (int idx : d2_neighbors) {
                CellBase* neighbor = GetCellByIndex(idx);
                if (neighbor && neighbor->CellType() == 4) {
                    d2_touche_type4 = true;
                    break;
                }
            }

            // Applique la règle : la fille touchant type 4 devient type 3, l’autre type 1
            if (d1_touche_type4 && !d2_touche_type4) {
                daughter1->SetCellType(3);
                daughter2->SetCellType(1);
            } else if (!d1_touche_type4 && d2_touche_type4) {
                daughter1->SetCellType(1);
                daughter2->SetCellType(3);
            } else {
                // Si aucune ou les deux touchent type 4, comportement par défaut
                daughter1->SetCellType(1);
                daughter2->SetCellType(1);
            }

            // Nettoyage du set
            special_division_cells.erase(parent_id1);
            special_division_cells.erase(parent_id2);

            // Met à jour les listes de types
            UpdateCellTypeLists(daughter1->Index(), daughter1->CellType());
            UpdateCellTypeLists(daughter2->Index(), daughter2->CellType());
            return;
        }
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

void cambium::UpdateCellTypeLists(int idx, int type) { // Gestion des listes des types cellulaire pour la division
    // Retirer l'index de l'ancienne liste si le type a changé
    if (last_cell_types.count(idx) && last_cell_types[idx] != type) {
        int old_type = last_cell_types[idx];
        std::vector<int>* old_list = nullptr;
        if (old_type == 0) old_list = &bark_cells;
        else if (old_type == 1) old_list = &cambium_cells;
        else if (old_type == 2) old_list = &gx_cells;
        else if (old_type == 3) old_list = &mx_cells;
        if (old_list) {
            old_list->erase(std::remove(old_list->begin(), old_list->end(), idx), old_list->end());
        }
    }
    // Ajouter l'index à la bonne liste si absent
    std::vector<int>* new_list = nullptr;
    if (type == 0) new_list = &bark_cells;
    else if (type == 1) new_list = &cambium_cells;
    else if (type == 2) new_list = &gx_cells;
    else if (type == 3) new_list = &mx_cells;
    if (new_list && std::find(new_list->begin(), new_list->end(), idx) == new_list->end()) {
        new_list->push_back(idx);
    }
    last_cell_types[idx] = type;
}
//Q_EXPORT_PLUGIN2(cambium, cambium)