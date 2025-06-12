/*
 *  $Id$
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
#include <QString>
#include <set>
#include "simplugin.h"
#include <QDomElement>




class cambium : public QObject, SimPluginInterface {
	Q_OBJECT
	Q_INTERFACES(SimPluginInterface);
        Q_PLUGIN_METADATA(IID "org.virtualleaf.cambium")

public:
	cambium();
	virtual QString ModelID(void);

	// Executed after the cellular mechanics steps have equilibrium
	virtual void CellHouseKeeping (CellBase *c);

    virtual void AfficherNoeuds (CellBase *c);


	// Differential equations describing transport of chemicals from cell to cell
	virtual void CelltoCellTransport(Wall *w, double *dchem_c1, double *dchem_c2);

	// Differential equations describing chemical reactions taking place at or near the cell walls
	// (e.g. PIN accumulation)
	virtual void WallDynamics(Wall *w, double *dw1, double *dw2);

	// Differential equations describing chemical reactions inside the cells
	virtual void CellDynamics(CellBase *c, double *dchem);

	// to be executed after a cell division
	virtual void OnDivide(ParentInfo *parent_info, CellBase *daughter1, CellBase *daughter2);

	// to be executed for coloring a cell
	virtual void SetCellColor(CellBase *c, QColor *color);
	// return number of chemicals
	virtual int NChem(void);
	virtual QString DefaultLeafML(void) { return QString("cambium_nCercles.XML"); }

	virtual void SetCellTypeProperties(CellBase *c);

    //Test nouveau tissu Rouges
    CellBase* GetCellByIndex(int idx);

    // Pour lire le temps de simulation depuis le XML
//    virtual void XMLReadSimtime(const QDomElement &root_node);
//
	// For internal use; not to be redefined by end users
//    virtual void SetParameters(Parameter *pass_pars) { par = pass_pars; }
//    virtual void SetCellsStaticDatamembers (CellsStaticDatamembers *cells_static_data_members_of_main);
//
//protected:
//    class Parameter *par;

private:
	// bark_cells should be defined in cambium.h, not here
	 void UpdateCellTypeLists(int idx, int type); // Gestion des listes des cellules pour la division
     std::vector<int> bark_cells;
     std::vector<int> cambium_cells;
     std::vector<int> gx_cells;
     std::vector<int> mx_cells;
     std::map<int, int> last_cell_types; // index -> dernier type connu

     std::map<int, CellBase*> cell_registry;
     std::set<int> special_division_cells;  // Pour stocker les ID des cellules qui doivent se diviser de manière spéciale
     double simulation_time; // Variable pour stocker le temps de simulation
     double aire_instant_t0 = 0.0; // Aire à t = 0

};