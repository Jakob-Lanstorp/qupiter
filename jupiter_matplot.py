# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Qjupiter
        A QGIS plugin Qupiter data plugin
                              -------------------
        begin                : 2018-01-22
        copyright            : (C) 2018 by Miljøstyrelsen
        email                : jalan@mst.dk
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Miljøstyrelsen'
__date__ = '2018-01-22'
__copyright__ = '(C) 2018 by Miljøstyrelsen'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import psycopg2
from matplotlib import pyplot as plt, dates
from jupiter_db import JupiterDb
from jupiter_aux import JupiterAux
from jupiter_qgis import JupiterQGIS

import numpy as np

class JupiterMatplot:
    def __init__(self):
        pass

    def timeseries_oneborehole_multiplecompounds(self, boreholeno, compoundlist, datefrom, dateto,
                                                 skip_unit=False, progress=None):
        """ Based of matplotlib.plot_date
             Multiple compounds and one borehole
         """
        # General Figure
        plt.figure(1)
        fig = plt.figure(1)
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.15)

        # General Axis
        ax = fig.add_subplot(1, 1, 1)

        # X-Axis
        ax.set_xlabel(u'År')

        # Y-Axis
        ax.set_ylabel('Koncentration')
        ax.yaxis.grid()

        db = JupiterDb()
        compounds = compoundlist.split(';')

        not_found = []
        compound_index = 0
        for c in compounds:
            compound_index += 1
            if progress is not None:
                progress.setPercentage(compound_index * 100 / len(compounds))
            c = c.strip()
            # Get amount and dates for compound
            amount, dt = db.get_timeserie(boreholeno, c, datefrom, dateto)
            if amount is None:
                not_found.append(c)
                if len(compounds) == 1:
                    return False, None
                else:
                    continue

            if skip_unit:
                label_legend = c
            else:
                # Get unit for legend label - time consuming part
                unit_tuple_list = db.count_compound_units(c)
                if unit_tuple_list is None:
                    # No unit for compound - not likely
                    label_legend = '{} [???]'.format(c)
                else:
                    if len(unit_tuple_list) == 1:
                        # Perfect - just one unit for compound
                        unit_count, unit = unit_tuple_list[0]
                        label_legend = '{} [{}]'.format(c, unit)
                    elif len(unit_tuple_list) > 1:
                        # More than one unit pr compound
                        units = []
                        for unit_count, unit in unit_tuple_list:
                            units.append('{}?'.format(unit))
                        label_legend = '{} [{}]'.format(c, ' '.join(units))

            # Convert datetime to matplot numbers
            dt = dates.date2num(dt)
            plt.plot_date(dt, amount, linestyle='-', markersize=3, label=label_legend)

        plt.xticks(rotation='vertical')
        plt.title('Tidsserie for boring: {}'.format(boreholeno))
        plt.legend(loc='upper center', shadow=True)

        plt.show()

        return True, not_found


    def timeseries_onecompound_multipleborehole(self, boreholenolist, compound, datefrom, dateto, progress=None):
        """ Based of matplotlib.plot_date. Multiple borehole and one compound """

        from datetime import datetime

        def onclick(event):
            JupiterAux.msg_box('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
                               ('double' if event.dblclick else 'single', event.button,
                                event.x, event.y, event.xdata, event.ydata))

        def onpick(event):
            thisline = event.artist
            borehole_graph_pick = thisline.get_label()

            #JupiterAux.msg_box('Picked borehole graph: {}'.format(borehole_graph_pick))

            #xdata = thisline.get_xdata()  #convert to  dates.num2date(dt)
            #ydata = thisline.get_ydata()
            #ind = event.ind
            #points = tuple(zip(xdata[ind], ydata[ind]))
            #JupiterAux.msg_box('{} - onpick points: {}'.format(borehole_graph_selection, points))

            qgis = JupiterQGIS()
            qgis.add_vertexmarker_borehole(borehole_graph_pick)

        # General Figure
        plt.figure(1)
        fig = plt.figure(1)
        plt.subplots_adjust(left=0.1, right=0.75, top=0.9, bottom=0.15)

        #cid = fig.canvas.mpl_connect('button_press_event', onclick)
        cid = fig.canvas.mpl_connect('pick_event', onpick)

        # General Axis
        ax = fig.add_subplot(1, 1, 1)

        # Draw compound limit as a horizontal line
        #plt.axhline(y=2.7)  only relevant for drwplant, no boreholes

        # X-Axis
        ax.set_xlabel(u'År')

        # Y-Axis - get unit of compound
        db = JupiterDb()
        unit_tuple_list = db.count_compound_units(compound)
        ax_ylabel = compound.title()
        if unit_tuple_list is None:
            # No unit for compound - not likely
            ax_ylabel += u' [???]'
            JupiterAux.msg_box(u'Bemærk der findes ingen enhed for stoffet: {} i PCJupiterXL'.format(compound))
        else:
            if len(unit_tuple_list) == 1:
                # Perfect - just one unit for compound
                unit_count, unit = unit_tuple_list[0]
                ax_ylabel += u' [{}]'.format(unit)
            elif len(unit_tuple_list) > 1:
                # More than one unit pr compound
                units = []
                for unit_count, unit in unit_tuple_list:
                    units.append(u'{}?'.format(unit))

                ax_ylabel = u' [{}]'.format(' '.join(units))
                JupiterAux.msg_box(
                    u'Bemærk stoffet: {} har flere enheder: ({}) i PCJupiterXL'.format(compound, ', '.join(units)))

        ax.set_ylabel(ax_ylabel)

        ax.yaxis.grid()

        boreholes = boreholenolist.split(',')
        not_found = []
        borehole_index = 0

        for b in boreholes:
            borehole_index += 1

            if progress is not None:
                progress.setPercentage(borehole_index * 100 / len(boreholes))

            b = b.strip()

            # Get amount and dates for compound and boreholes
            amount, dt = db.get_timeserie(b, compound, datefrom, dateto)
            if amount is None:
                not_found.append(b)
                if len(boreholes) == 1:
                    return False, None
                else:
                    continue

            # Convert datetime to matplot numbers
            dt = dates.date2num(dt)
            plt.plot_date(dt, amount, linestyle='-', markersize=3, label=b, picker=5)

        plt.xticks(rotation='vertical')
        plt.title('Tidsserie')
        plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0., shadow=True)

        plt.show()

        return True, not_found

    def scatterplot(self, extent_or_wkt, compoundname_x, compoundname_y, datefrom, dateto,
                    extent_layer=None, x_marker=None, y_marker=None, showannotations=False):
        """
        Create a scatter plot Either from boreholes in bbox or wkt selected geometries
        :param extent_or_wkt: Either a extent string or a wkt geometry
        :param compoundname_x: Compound name for x axe
        :param compoundname_y: Compound name for y axe
        :param datefrom: Query from date
        :param dateto: Query to date
        :param extent_layer: layername with selection. Only relevant if WKT bound.
        :param x_marker: marker line for given value
        :param y_marker: marker line for given value
        :return: True if no error
        :param showannotations: Show boreholeno label for each scatter point
        """
        def onpick(event):
            # Warning matplotlib fails in silence - https://matplotlib.org/examples/event_handling/pick_event_demo.html
            index = event.ind
            borehole_arr_pick = np.take(boreholenos, index)
            #JupiterAux.msg_box('onpick scatter: {}'.format(borehole_arr_pick))

            qgis = JupiterQGIS()
            for j, b in enumerate(borehole_arr_pick):
                if j == 0:
                    qgis.add_vertexmarker_borehole(b)
                else:
                    qgis.add_vertexmarker_borehole(b, keepExistingMarkers=True)

        db = JupiterDb()
        compoundno_x = db.compoundname_to_no(compoundname_x)
        compoundno_y = db.compoundname_to_no(compoundname_y)

        unit_x = db.get_unit_quess(compoundno_x)
        unit_y = db.get_unit_quess(compoundno_y)

        if compoundno_x is None or compoundno_y is None:
            JupiterAux.msg_box('Et af de to indtastede stoffer: "{}, {}" findes ikke i PCJupiterXL'.format(compoundname1, compoundname2))
            return

        qgis = JupiterQGIS()
        qgis.remove_canvas_items()  # Remove marker from a previous plot

        boreholenos = []
        if extent_or_wkt != '0,0,0,0':
            bbox = qgis.extentToBoundingbox(extent_or_wkt)
            x, y, boreholenos = db.get_scatter_array_bbox(compoundno_x, compoundno_y, bbox, datefrom, dateto, compoundname_x, compoundname_y)
        else:
            wkt = qgis.selectedFeatureToWKT(extent_layer)
            x, y, boreholenos = db.get_scatter_array_wkt(compoundno_x, compoundno_y, wkt, datefrom, dateto, compoundname_x, compoundname_y)

        # General Figure
        plt.figure(1)
        fig = plt.figure(1)

        # Connect pick event on plot
        cid = fig.canvas.mpl_connect('pick_event', onpick)

        plt.scatter(x, y, alpha=0.8, picker=True)  # plt.scatter(x, y, s=area, c=colors, alpha=0.5)

        ax = fig.add_subplot(1, 1, 1)
        ax.set_xlabel('{} [{}]'.format(compoundname_x, unit_x))
        ax.set_ylabel('{} [{}]'.format(compoundname_y, unit_y))

        ax.xaxis.grid()
        ax.yaxis.grid()

        # label points in scatter plot
        if showannotations:
            for i, txt in enumerate(boreholenos):
                ax.annotate(str(txt), (x[i], y[i]))

        plt.axhline(y=y_marker)
        plt.axvline(x=x_marker)
        plt.title('Scatterplot')

        plt.show()

        return True

    def test1_timeseries(self, boreholeno, compound, datefrom, dateto):
        """ Based of matplotlib.plot_date
            TEST: No use of ax - one borehole multiple compounds
        """
        # Here we just use one figure
        plt.figure(1)

        db = JupiterDb()

        # Test compound - overwrites gui input
        compound = 'Nitrat; Sulfat'

        compounds = compound.split(';')
        for c in compounds:
            amount, dt = db.get_timeserie(boreholeno, c.strip(), datefrom, dateto)
            if amount is None:
                return False

            dt = dates.date2num(dt)
            plt.plot_date(dt, amount, linestyle='-', label=c)

        plt.xticks(rotation='vertical')
        plt.title('{}-tidsserie for boring: {}'.format(compound, boreholeno))

        plt.legend(loc='upper center', shadow=True)
        plt.grid(True)

        plt.show()

        return True

    def test2_timeseries(self, boreholeno, compound, datefrom, dateto):
        """ Based of matplotlib.plot_date
            TEST: Use of ax - one borehole multiple compounds
        """
        # Figure 1
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        from mpl_toolkits.axes_grid1.axes_divider import make_axes_area_auto_adjustable

        plt.figure(1)
        ax = plt.axes([0, 0, 1, 1])
        # ax = plt.subplot(111)

        ax.set_yticks([0.5])
        ax.set_yticklabels(["very long label"])

        make_axes_area_auto_adjustable(ax)

        plt.show()

        # Figure 2
        plt.figure(2)
        ax1 = plt.axes([0, 0, 1, 0.5])
        ax2 = plt.axes([0, 0.5, 1, 0.5])

        ax1.set_yticks([0.5])
        ax1.set_yticklabels(["very long label"])
        ax1.set_ylabel("Y label")

        ax2.set_title("Title")

        make_axes_area_auto_adjustable(ax1, pad=0.1, use_axes=[ax1, ax2])
        make_axes_area_auto_adjustable(ax2, pad=0.1, use_axes=[ax1, ax2])

        # Figure 3
        fig = plt.figure(3)
        ax1 = plt.axes([0, 0, 1, 1])
        divider = make_axes_locatable(ax1)

        ax2 = divider.new_horizontal("100%", pad=0.3, sharey=ax1)
        ax2.tick_params(labelleft="off")
        fig.add_axes(ax2)

        divider.add_auto_adjustable_area(use_axes=[ax1], pad=0.1,
                                         adjust_dirs=["left"])
        divider.add_auto_adjustable_area(use_axes=[ax2], pad=0.1,
                                         adjust_dirs=["right"])
        divider.add_auto_adjustable_area(use_axes=[ax1, ax2], pad=0.1,
                                         adjust_dirs=["top", "bottom"])

        ax1.set_yticks([0.5])
        ax1.set_yticklabels(["very long label"])

        ax2.set_title("Title")
        ax2.set_xlabel("X - Label")

        return True
