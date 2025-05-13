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
- Stiffness = 10 × Cambium stiffness.

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
- Stiffness = 100 × Cambium stiffness.
*/



QString cambium::ModelID(void) {
  // specify the name of your model here
  return QString( "Cambium" );
}

// return the number of chemicals your model uses
int cambium::NChem(void) { return 0; }

// Constructor - initializes the bark_cells vector
cambium::cambium() {
    // Initialize bark cells with the original values
    bark_cells = {13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30};
}

// Display node information for a cell
void cambium::AfficherNoeuds(CellBase *c) {
    int i = 0;
    for (list<Node *>::const_iterator it = c->getNodes().begin(); it != c->getNodes().end(); ++it, ++i) {
        // Node operations can be added here if needed
    }
}

void cambium::SetCellTypeProperties(CellBase *c) { // Set cell properties
/* SetLambdaLength property notes:
   - High values (>2) cause cells to "flow"
   - Very low values (<0.01) for bark prevent cells from moving between bark cells
   - This is the elasticity coefficient of the wall, allowing it to extend to lambda * initial value
*/
  if (c->CellType()==0){
    c-> SetWallStiffness(1);
    c-> SetLambdaLength(0);
  }
  else if (c->CellType()==1){
    c-> SetWallStiffness(1);
    c-> SetLambdaLength(0);
  }
  else if (c->CellType()==2){
    c-> SetWallStiffness(1);
    c-> SetLambdaLength(0);
  }
  else {
    c-> SetWallStiffness(1);
    c-> SetLambdaLength(0);
  }
}

void cambium::SetCellColor(CellBase *c, QColor *color) {
  //cell Coloring depending on type
  if (c->CellType()==0){
    color->setNamedColor("cornflowerblue");
  }
  else if (c->CellType()==1){
        color->setNamedColor("seagreen");
  }
  else if (c->CellType()==2){
        color->setNamedColor("darkorange");
  }
  else {
        color->setNamedColor("blue");
  }
}


void cambium::OnDivide(ParentInfo *parent_info, CellBase *daughter1, CellBase *daughter2) {
    // Rules to be executed after cell division

    // Check if this is a special division
    int parent_id1 = daughter1->Index(); // Get parent ID via daughter cell
    int parent_id2 = daughter2->Index();
    if (special_division_cells.find(parent_id1) != special_division_cells.end() or special_division_cells.find(parent_id2) != special_division_cells.end() ) {
        // Determine which daughter cell is closer to the exterior
        bool d1_more_exposed = false;

        // Count exposed nodes for each daughter cell
        int d1_exposed_nodes = 0;
        int d2_exposed_nodes = 0;

        for (auto node_it = daughter1->getNodes().begin(); node_it != daughter1->getNodes().end(); ++node_it) {
            if ((*node_it)->BoundaryP()) d1_exposed_nodes++;
        }

        for (auto node_it = daughter2->getNodes().begin(); node_it != daughter2->getNodes().end(); ++node_it) {
            if ((*node_it)->BoundaryP()) d2_exposed_nodes++;
        }

        d1_more_exposed = (d1_exposed_nodes > d2_exposed_nodes);

        // Transform the more exposed cell into bark, the other remains cambium
        if (d1_more_exposed) {
            daughter1->SetCellType(0);  // Bark
            daughter2->SetCellType(1);  // Cambium

            // Add the new bark cell to our list
            bark_cells.push_back(daughter1->Index());
        } else {
            daughter1->SetCellType(1);  // Cambium
            daughter2->SetCellType(0);  // Bark

            // Add the new bark cell to our list
            bark_cells.push_back(daughter2->Index());
        }

        // Remove the cell from our set after processing
        special_division_cells.erase(parent_id1);
        special_division_cells.erase(parent_id2);
        return;
    }


    // Construct neighbor lists for both daughter cells
    daughter1->GetNeighborIndices();
    daughter2->GetNeighborIndices();
    // Get neighbor indices for both daughter cells
    std::vector<int> d1_neighbor_indices = daughter1->GetNeighborIndices();
    std::vector<int> d2_neighbor_indices = daughter2->GetNeighborIndices();

    // Check if daughter cells are neighbors with any bark cells
    bool d1_neighbors_bark = false;
    bool d2_neighbors_bark = false;

    // Check daughter1's neighbors
    for (auto idx : d1_neighbor_indices) {
        if (std::find(bark_cells.begin(), bark_cells.end(), idx) != bark_cells.end()) {
            d1_neighbors_bark = true; // daughter1 has a neighbor bark cell
        }
    }

    // Check daughter2's neighbors
    for (auto idx : d2_neighbor_indices) {
        if (std::find(bark_cells.begin(), bark_cells.end(), idx) != bark_cells.end()) {
            d2_neighbors_bark = true; // daughter1 has a neighbor bark cell
        }
    }

    // Handle the case where both daughter cells are neighbors to bark cells
    if (d1_neighbors_bark && d2_neighbors_bark) {
        // Both cells become type 1 (Cambium cells)
        daughter1->SetCellType(1);
        daughter2->SetCellType(1);
    }
    // Handle cases where only one daughter cell is neighbor to bark cells
    else if (d1_neighbors_bark) { // Daughter 1 is neighbor to a bark cell
        daughter1->SetCellType(1); // Daughter 1 becomes a Cambium cell on division
        daughter2->SetCellType(2); // Daughter 2 becomes a Growing Xylem on division
    }
    else if (d2_neighbors_bark) {// Daughter 2 is neighbor to a bark cell
        daughter1->SetCellType(2);// Daughter 1 becomes a Growing Xylem on division
        daughter2->SetCellType(1);// Daughter 2 becomes a Cambium cell on division
    }
    else { // Neither are neighbor to a bark cell.
        daughter1->SetCellType(2);// Daughter 1 becomes a Growing Xylem cell on division
        daughter2->SetCellType(2);// Daughter 2 becomes a Growing Xylem cell on division
    }
}

//void cambium::CellHouseKeeping(CellBase *c) { // Simple test function
//  // Simple test: if cell Index is 3, double its size and divide
//  if (c->Index() == 10) {
//    // Double the target area
//    c->EnlargeTargetArea(par->cell_expansion_rate);
//    if (c->Area() > par->rel_cell_div_threshold * c->BaseArea()) {
//      c->Divide();
//    }
//  }
//}

void cambium::CellHouseKeeping(CellBase *c) { // How cells behave after division
  qDebug() << "Cell elastic limit :" << c->elastic_limit() ;

  SetCellTypeProperties(c);

  // Check if a cambium cell is no longer adjacent to the bark, if not it has to be transformed into a Growing Xylem cell
  if (c->CellType() == 1) {
    // Solution #1 for cambium cells touching the exterior:
    // The cambium cell divides in two and the cell closest to the exterior
    // transforms into a bark cell.

    // Check if any of the cell's nodes are exposed to the exterior
    AfficherNoeuds(c);

    // Check all nodes of the cell
    for (list<Node *>::const_iterator it = c->getNodes().begin(); it != c->getNodes().end(); ++it) {
        Node* noeud = *it;
        if (noeud->BoundaryP()) {

            // Force division along this axis
//            c->Divide();

            // OnDivide will handle the rest
            special_division_cells.insert(c->Index());
            return;  // Exit after initiating division
        }
    }

    // Normal behavior for cambium cells
    c->EnlargeTargetArea(par->cell_expansion_rate);
    if (c->Area() > par->rel_cell_div_threshold * c->BaseArea()) {
      c->Divide();
    }
  }
  else if(c->CellType() == 2) { // If cell is a type 2, grow until it reach 3*BaseArea then transform into a Type 3
    if (c->Area() < 3 * c->BaseArea()) {
      c->EnlargeTargetArea(par->cell_expansion_rate);
    }
    else {
      c->SetCellType(3); // Set grown Type 2 cell to a Type 3
    }
  }
  else if (c->CellType() == 0) {
  /* If the cell is a bark cell (type 0), we need to slightly enlarge it to prevent excessive stretching,
     which could cause issues in the simulation. This adjustment ensures stability during runtime. */

  // Get current area values
  double area = c->Area();
  double baseArea = c->BaseArea();

  // Use static maps to store growth data for each cell by its index
  static std::map<int, double> growth_additions;
  static std::map<int, int> last_growth_step;
  static int current_step = 0;

  // Increment step counter each time function is called (simulation step)
  current_step++;

  // Initialize growth addition for this cell if not present
  if (growth_additions.find(c->Index()) == growth_additions.end()) {
    growth_additions[c->Index()] = 0.0;
    last_growth_step[c->Index()] = 0;
  }

  // Check if we need to increase the growth_addition (every 500 simulation steps)
  if (current_step - last_growth_step[c->Index()] >= 200) {
    // Increase growth_addition by 5% of baseArea
    growth_additions[c->Index()] += baseArea * 0.15;
    // Update last growth step
    last_growth_step[c->Index()] = current_step;

    if (c->Index() == 28) {
      qDebug() << "Cell 28 - GROWTH UPDATE - Step:" << current_step
               << "New Growth Addition:" << growth_additions[c->Index()];
    }
  }

  // Use effective base area (original baseArea + growth_addition)
  double effective_base_area = baseArea + growth_additions[c->Index()];

  // Maintain effective base area if cell has shrunk
  if (area < effective_base_area) {
    // Gradually increase target area to reach effective base area
    c->EnlargeTargetArea(par->cell_expansion_rate);

    if (c->Index() == 28) {
      qDebug() << "Cell 28 - ENLARGING TARGET AREA - Step:" << current_step
               << "Effective base area:" << effective_base_area
               << "Current area:" << area
               << "Target area:" << c->TargetArea()
               << "Rate:" << par->cell_expansion_rate;
    }
  }
}
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

//Q_EXPORT_PLUGIN2(cambium, cambium)