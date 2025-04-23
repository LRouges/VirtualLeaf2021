/*
 *
 *  This file is part of the Virtual Leaf.
 *
 *  The Virtual Leaf is free software: you can redistribute it and/or modify
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

#include "parameter.h"

#include "wallbase.h"
#include "cellbase.h"
#include "cambium.h"

static const std::string _module_id("$Id$");

QString cambium::ModelID(void) {
  // specify the name of your model here
  return QString( "Cambium" );
}

// return the number of chemicals your model uses
int cambium::NChem(void) { return 0; }
// Constructor - add this code to initialize the bark_cells vector
cambium::cambium() {
    // Initialize bark cells with the original values
    bark_cells = {0, 15, 27, 28, 21, 20, 29, 16, 17, 18, 19, 24, 25, 23, 22, 26, 14, 1};
}

// To be executed after cell division
void cambium::OnDivide(ParentInfo *parent_info, CellBase *daughter1, CellBase *daughter2) {
    // Rules to be executed after cell division go here
    // (e.g., cell differentiation rules)
    // Get neighbor indices for both daughter cells
    std::vector<int> d1_neighbor_indices = daughter1->GetNeighborIndices();
    std::vector<int> d2_neighbor_indices = daughter2->GetNeighborIndices();

    // Check if daughter cells are neighbors with any bark cells
    bool d1_neighbors_bark = false;
    bool d2_neighbors_bark = false;
    bool d1_neighbors_cell30 = false;
    bool d2_neighbors_cell30 = false;

    // Check daughter1's neighbors
    for (auto idx : d1_neighbor_indices) {
        if (std::find(bark_cells.begin(), bark_cells.end(), idx) != bark_cells.end()) {
            d1_neighbors_bark = true;
            qDebug() << "Daughter1 (ID:" << daughter1->Index() << ") is neighbor with bark cell ID:" << idx;
        }
        if (idx == 30) {
            d1_neighbors_cell30 = true;
            qDebug() << "Daughter1 (ID:" << daughter1->Index() << ") is neighbor with cell 30";
        }
    }

    // Check daughter2's neighbors
    for (auto idx : d2_neighbor_indices) {
        if (std::find(bark_cells.begin(), bark_cells.end(), idx) != bark_cells.end()) {
            d2_neighbors_bark = true;
            qDebug() << "Daughter2 (ID:" << daughter2->Index() << ") is neighbor with bark cell ID:" << idx;
        }
        if (idx == 30) {
            d2_neighbors_cell30 = true;
            qDebug() << "Daughter2 (ID:" << daughter2->Index() << ") is neighbor with cell 30";
        }
    }

    // Handle the case where both daughter cells are neighbors to bark cells
    if (d1_neighbors_bark && d2_neighbors_bark) {
        // Check if both cells are also neighbors to cell 30
        if (d1_neighbors_cell30 && d2_neighbors_cell30) {
            qWarning() << "WARNING: Both daughter cells are neighbors to bark cells AND cell 30!";
        }

        // Set cell types based on which one neighbors cell 30
        if (d1_neighbors_cell30) {
            daughter1->SetCellType(3);
            daughter2->SetCellType(1);
            bark_cells.push_back(daughter2->Index());
        } else if (d2_neighbors_cell30) {
            daughter1->SetCellType(1);
            daughter2->SetCellType(3);
            bark_cells.push_back(daughter1->Index());
        } else {
            // Default behavior if neither neighbors cell 30
            daughter1->SetCellType(1);
            bark_cells.push_back(daughter1->Index());
            daughter2->SetCellType(3);
        }
    }
    // Handle cases where only one daughter cell is neighbor to bark cells
    else if (d1_neighbors_bark) {
        daughter1->SetCellType(1);
        bark_cells.push_back(daughter1->Index());
        daughter2->SetCellType(3);
    }
    else if (d2_neighbors_bark) {
        daughter2->SetCellType(1);
        bark_cells.push_back(daughter2->Index());
        daughter1->SetCellType(3);
    }


    // Debug print to confirm new cell types
    qDebug() << "New cell types - Daughter1 (ID:" << daughter1->Index() << ") is now type:" << daughter1->CellType()
             << ", Daughter2 (ID:" << daughter2->Index() << ") is now type:" << daughter2->CellType();

    // Print all bark cell IDs after division
    qDebug() << "Bark cells after division:" << bark_cells.size() << "cells:";
    for (auto id : bark_cells) {
        qDebug() << "  Bark cell ID:" << id;
    }
}


void cambium::SetCellColor(CellBase *c, QColor *color) {
  // Simplified cell coloring rules without chemical dependencies
  if (c->CellType()==3){
    color->setNamedColor("red");
  }
  else {
    if (c->Area() < 0.8 * c->BaseArea()) {
      color->setNamedColor("yellow");
    } else {
      color->setNamedColor("blue");
    }
  }
}




void cambium::CellHouseKeeping(CellBase *c) {
  // add cell behavioral rules here
	if (c->CellType()==3) {
		c->EnlargeTargetArea(par->cell_expansion_rate);
		if (c->Area() > par->rel_cell_div_threshold * c->BaseArea()) {
			c->Divide();
		}
	}
	else if (c->CellType()==0) {
		if (c->Area() < 0.8 * c->BaseArea()) {
			qDebug() << "Type 0 cell being enlarged: Area =" << c->Area()
				<< ", BaseArea =" << c->BaseArea()
				<< ", Threshold =" << 0.8 * c->BaseArea()
				<< ", Expansion rate =" << par->cell_expansion_rate;
			c->EnlargeTargetArea(par->cell_expansion_rate);
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
