/*
 *
 *  $Id$
 *
 *  This file is part of the Virtual Leaf.
 *
 *  VirtualLeaf is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  VirtualLeaf is distributed in the hope that it will be useful,
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

#ifndef _CELL_H_
#define _CELL_H_

#include <list>
#include <vector>
#include <iostream>
#include <QString>
#include "vector.h"
#include "parameter.h"
#include "wall.h"
#include "warning.h"
#include "cellbase.h"
#include "Neighbor.h"
#include "random.h"
#include "pi.h"
//#include "cell.h"

#include <QGraphicsScene>
#include <qcolor.h>
#include <QObject>
#include <QMouseEvent>

class Cell : public CellBase 
{

  Q_OBJECT
    friend class Mesh;
  friend class FigureEditor;

 public:
  Cell(double x, double y, double z = 0.);
  Cell(void);
  Cell(const Cell &src);
  Cell operator=(const Cell &src);
  bool Cmp(Cell*) const;
  bool Eq(Cell*) const;

  inline bool IndexEquals(int i) { return i == index; }

  static void SetMagnification(const double &magn) {
    factor=magn;
  }
  static Vector Offset(void) {
    Vector offs;
    offs.x=offset[0];
    offs.y=offset[1];
    return offs;
  }

  static void Translate(const double &tx,const double &ty) {
    offset[0]+=tx;
    offset[1]+=ty;
  }

  inline static double Factor(void) {
    return factor;
  }
  static void setOffset(double ox, double oy) {
    offset[0]=ox;
    offset[1]=oy;
  }
  static double Magnification(void) {
    return factor;
  }

  static double Scale(const double scale) {
    factor*=scale;
    return factor;
  }

  void DivideOverAxis(Vector axis); // divide cell over axis

  // divide over the line (if line and cell intersect)
  bool DivideOverGivenLine(const Vector v1, const Vector v2, bool wall_fixed = false, NodeSet *node_set = 0);

  void Divide(void) { // Divide cell based on division_type
    std::cout << "Cell " << index << ": Starting division process" << std::endl;
    Vector axis;
    Length(&axis); // Get the long axis
    std::cout << "Cell " << index << ": Long axis = (" << axis.x << ", " << axis.y << ", " << axis.z << ")" << std::endl;

    switch (division_type) {
      case NO_DIVISION:
        std::cout << "Cell " << index << ": Division type = NO_DIVISION, skipping" << std::endl;
        return;
      case RANDOM_DIVISION:
      {
        std::cout << "Cell " << index << ": Division type = RANDOM_DIVISION" << std::endl;
        // Random angle between 0 and π
        double orientation = Pi*RANDOM();
        Vector divAxis(sin(orientation), cos(orientation), 0.);
        std::cout << "Cell " << index << ": Random division axis = (" << divAxis.x << ", " << divAxis.y << ", " << divAxis.z << "), orientation = " << orientation << std::endl;
        DivideOverAxis(divAxis);
      }
        break;
      case MAX_STRESS_AXIS:
        std::cout << "Cell " << index << ": Division type = MAX_STRESS_AXIS" << std::endl;
        // Calculate principal stress axis and divide along it
        {
          Vector stressAxis = CalculateDivisionPlane();
          std::cout << "Cell " << index << ": Stress division axis = (" << stressAxis.x << ", " << stressAxis.y << ", " << stressAxis.z << ")" << std::endl;
          DivideOverAxis(stressAxis);
        }
        break;
      case SHORT_AXIS:
        std::cout << "Cell " << index << ": Division type = SHORT_AXIS" << std::endl;
        // Divide over short axis (perpendicular to long axis)
        {
          Vector shortAxis = axis.Perp2D();
          std::cout << "Cell " << index << ": Short axis = (" << shortAxis.x << ", " << shortAxis.y << ", " << shortAxis.z << ")" << std::endl;
          DivideOverAxis(shortAxis);
        }
        break;
      case LONG_AXIS:
        std::cout << "Cell " << index << ": Division type = LONG_AXIS" << std::endl;
        // Divide over long axis
        std::cout << "Cell " << index << ": Using long axis for division" << std::endl;
        DivideOverAxis(axis);
        break;
      case PERP_STRESS:
        std::cout << "Cell " << index << ": Division type = PERP_STRESS" << std::endl;
        // Divide perpendicular to principal stress
        {
          Vector perpStressAxis =  CalculateDivisionPlane();
          std::cout << "Cell " << index << ": Perpendicular stress axis = (" << perpStressAxis.x << ", " << perpStressAxis.y << ", " << perpStressAxis.z << ")" << std::endl;
          DivideOverAxis(perpStressAxis);
        }
        break;
      default:
        std::cout << "Cell " << index << ": Division type = UNKNOWN (" << division_type << "), defaulting to SHORT_AXIS" << std::endl;
        // Default to short axis division
        {
          Vector shortAxis = axis.Perp2D();
          std::cout << "Cell " << index << ": Default short axis = (" << shortAxis.x << ", " << shortAxis.y << ", " << shortAxis.z << ")" << std::endl;
          DivideOverAxis(shortAxis);
        }
        break;
    }
    std::cout << "Cell " << index << ": Division complete" << std::endl;
  }

  //void CheckForGFDrivenDivision(void);
  inline int NNodes(void) const { return nodes.size(); }

  void Move(Vector T);
  void Move(double dx, double dy, double dz=0) {
    Move( Vector (dx, dy, dz) );
  }

  double Displace(double dx, double dy, double dh);
  void Displace(void);
  double Energy(void) const;
  bool SelfIntersect(void);
  bool MoveSelfIntersectsP(Node *nid, Vector new_pos);
  bool LinePieceIntersectsP(const Vector v1, const Vector v2) const;
  bool IntersectsWithLineP(const Vector v1, const Vector v2);

  void XMLAdd(QDomDocument &doc, QDomElement &cells_node) const;

  void ConstructWalls(void);
  void Flux(double *flux, double *D);

  void OnClick(QMouseEvent *e);
  inline Mesh& getMesh(void) const { return *m; }
  double MeanArea(void);

  void Apoptose(void); // Cell kills itself
  list<Wall *>::iterator RemoveWall( Wall *w );
  void AddWall( Wall *w );

  void Draw(QGraphicsScene *c, bool showStiffness, QString tooltip = "");

  // Draw a text in the cell's center
  void DrawText(QGraphicsScene *c, const QString &text) const;
  void DrawIndex(QGraphicsScene *c) const;
  void DrawCenter(QGraphicsScene *c) const;
  void DrawNodes(QGraphicsScene *c) const;
  void DrawMiddleLamella(QGraphicsScene *c, QString tooltip = "");

  void DrawAxis(QGraphicsScene *c) const;
  void DrawStrain(QGraphicsScene *c) const;
  void DrawFluxes(QGraphicsScene *c, double arrowsize = 1.);
  void DrawWalls(QGraphicsScene *c) const;
  void DrawValence(QGraphicsScene *c) const;
  void EmitValues(double t);
  void insertNodeAfterFirst(NodeBase * position1, NodeBase * position2, NodeBase * newNode);
  virtual void correctNeighbors();
  virtual WallBase* newWall(NodeBase* from,NodeBase* to,CellBase * other);
  virtual void InsertWall( WallBase *w );
  virtual CellBase* getOtherWallElementSide(NodeBase * spikeEnd,NodeBase * over);
  virtual double elastic_limit();

 signals:
  void ChemMonValue(double t, double *x);

 protected:
  void XMLAddCore(QDomDocument &doc, QDomElement &xmlcell) const;
  int XMLRead(QDomElement &cur);
  void DivideWalls(ItList new_node_locations, const Vector from, const Vector to, bool wall_fixed = false, NodeSet *node_set = 0);

 private:

  static QPen *cell_outline_pen;
  static double offset[3];
  static double factor;
  Mesh *m;
  void ConstructConnections(void);
  void SetWallLengths(void);
  void checkCellLooseWallEnds(Wall * wall,bool&n1Connected,bool&n2Connected);
  Node * followNeighborsToWall(Node * n1, Node * n2, double &distance);
  Neighbor getNeighbor(Node * node);
  Wall* getBoundaryWallAt(Node * node);
  Node * attachFreeWallEnd(Cell * cellWithOtherWalls, Cell * cellWithSingleWalls, Wall * wall, Node * loseWallNode);
  Wall * findWall(Node * n1, Node * n2);
  void splittWallElementsBetween(Node* node, Cell* daughter);

  void findBeforeAfter(Node * node, Node ** before, Node**after);
  Cell* findOtherCell(Cell*other,  Node * node,  Node * node2);
  Cell* findNeighbourCellOnDivide(Cell* daughter,Node* node,Node * before1,Node * after1 ,Node * before2,Node * after2);
  Vector CalculateDivisionPlane();

};


// Boundarypolygon is a special cell; will not increase ncells
//  and will not be part of Mesh::cells
class BoundaryPolygon : public Cell {

 public:
 BoundaryPolygon(void) : Cell() {
    NCells()--;
    index=-1;
  }

 BoundaryPolygon(double x,double y,double z=0) : Cell (x,y,z) {
    NCells()--;
    index=-1;
  }

  BoundaryPolygon &operator=(Cell &src) {
    Cell::operator=(src);
    index=-1;
    return *this;
  }
  virtual void Draw(QGraphicsScene *c, QString tooltip = "");

  virtual void XMLAdd(QDomDocument &doc, QDomElement &parent_node) const;

  virtual bool BoundaryPolP(void) const { return true; } 
};

#endif

/* finis */
