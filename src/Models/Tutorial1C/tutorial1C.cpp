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
#include "tutorial1C.h"

#include "mesh.h"

static const std::string _module_id("$Id$");

QString Tutorial1C::ModelID(void) {
  // specify the name of your model here
  return QString( "1C: Vertical cell division" );
}

// return the number of chemicals your model uses
int Tutorial1C::NChem(void) { return 0; }

// To be executed after cell division
void Tutorial1C::OnDivide(ParentInfo *parent_info, CellBase *daughter1, CellBase *daughter2) {
  // rules to be executed after cell division go here
  // (e.g., cell differentiation rules)

  // double stiffness = 2;
  // double* p_stiffness= &stiffness;
  // if (daughter1->AtBoundaryP()) {
  //   // Apply to both daughter cells
  //   daughter1->LoopWallElements([p_stiffness](auto wallElementInfo){
  //     wallElementInfo->getWallElement()->setStiffness(*p_stiffness);
  //     (*p_stiffness)+=0.1;
  //   });
  // }
  // if (daughter2->AtBoundaryP()) {
  //   daughter2->LoopWallElements([p_stiffness](auto wallElementInfo){
  //     wallElementInfo->getWallElement()->setStiffness(*p_stiffness);
  //     (*p_stiffness)+=0.1;
  //   });
  // }
}

void Tutorial1C::SetCellColor(CellBase *c, QColor *color) { 
  // add cell coloring rules here
}

void Tutorial1C::CellHouseKeeping(CellBase *c) {
  c->SetDivisionType(SHORT_AXIS);
  cout << "Cell " << c->Index() <<  " at boundary : " << c->AtBoundaryP() << endl;
  // Count total cells in the tissue
  // int totalCells = CountCells();
  // cout << "Cell " << c->Index() << " at boundary: " << c->AtBoundaryP()
  //      << ", Total cells: " << totalCells << endl;
  // cout << "Cell lambda length: " << c->GetLambdaLength() << endl;
  double lambda = 0.1;
  double lambda_ext  = 0.5;
  // Only set high stiffness for boundary cells
  if (c->AtBoundaryP()) {
    c->SetLambdaLength(lambda_ext);
    // double stiffness = 2;
    // double* p_stiffness = &stiffness;
    //
    // c->LoopWallElements([p_stiffness](auto wallElementInfo){
    //   wallElementInfo->getWallElement()->setStiffness(*p_stiffness);
    //   (*p_stiffness)+=0.1;
    //   });
  } else {
    // Set uniform stiffness for non-boundary cells
    c->SetLambdaLength(lambda);
    // c->LoopWallElements([](auto wallElementInfo){
    //   wallElementInfo->getWallElement()->setStiffness(1);
    // });
  }

  // add cell behavioral rules here
  c->EnlargeTargetArea(par->cell_expansion_rate);
  if (c->Area() > par->rel_cell_div_threshold * c->BaseArea()) {
    c->Divide();
  }
}

void Tutorial1C::CelltoCellTransport(Wall *w, double *dchem_c1, double *dchem_c2) {
  // add biochemical transport rules here
}
void Tutorial1C::WallDynamics(Wall *w, double *dw1, double *dw2) {
  // add biochemical networks for reactions occuring at walls here
}
void Tutorial1C::CellDynamics(CellBase *c, double *dchem) { 
  // add biochemical networks for intracellular reactions here
}


//Q_EXPORT_PLUGIN2(tutorial1C, Tutorial1C)
