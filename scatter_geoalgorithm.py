# -*- coding: utf-8 -*-

"""
/***************************************************************************
 PCJupiterXL
                                 A QGIS plugin
 PCJupiterXL data plugin
                              -------------------
        begin                : 2018-02-21
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
__date__ = '2018-02-21'
__copyright__ = '(C) 2018 by Miljøstyrelsen'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QIcon

import os

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterExtent, ParameterVector, ParameterString, ParameterNumber, ParameterBoolean
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector

from jupiter_qgis import JupiterQGIS
from jupiter_aux import JupiterAux
from jupiter_db import JupiterDb
from jupiter_matplot import JupiterMatplot

from datetime import date

class ScatterGeoAlgorithm(GeoAlgorithm):
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    EXTENT = 'EXTENT'
    VECTOR_SELECTION = 'VECTOR_SELECTION'
    COMPOUNDNAME1 = 'COMPOUNDNAME1'
    COMPOUNDNAME2 = 'COMPOUNDNAME2'
    XAXELINE = 'XAXELINE'
    YAXELINE = 'YAXELINE'
    DATE_FROM = 'DATE_FROM'
    DATE_TO = 'DATE_TO'
    SHOWANNOTATIONS = 'SHOWANNOTATIONS'

    def __init__(self, tablename, groupname):
        self.tablename = tablename
        self.groupname = groupname

        GeoAlgorithm.__init__(self)

    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # The name that the user will see in the toolbox
        self.name = self.tablename

        # The branch of the toolbox under which the algorithm will appear
        self.group = self.groupname

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(ParameterExtent(
            self.EXTENT,
            self.tr(u'Definer afgrænsningen af forespørgsel for "{}".').format(self.tablename),
            default="0,0,0,0"))

        self.addParameter(ParameterVector(
            self.VECTOR_SELECTION,
            self.tr(u'- eller brug en valgt polygongeometri som afgrænsning for "{}" fra tabel').format(self.tablename),
            [ParameterVector.VECTOR_TYPE_POLYGON], False))

        self.addParameter(ParameterString(
                self.COMPOUNDNAME1,
                self.tr(u'Stof til x-aksen'), u'Sulfat'))

        self.addParameter(ParameterString(
                self.COMPOUNDNAME2,
                self.tr(u'Stof til y-aksen'), u'Nitrat'))

        self.addParameter(ParameterNumber(
            self.XAXELINE,
            self.tr(u'Marker værdi til x-aksen (vertikal linje)'),
            0,
            None,
            '31',
            optional=True))

        self.addParameter(ParameterNumber(
            self.YAXELINE,
            self.tr(u'Marker værdi til y-aksen (horisontal linje)'),
            0,
            None,
            '1',
            optional=True))

        self.addParameter(ParameterBoolean(
                self.SHOWANNOTATIONS,
                self.tr(u'Label scatter-punkter med boreholeno'),
                False,
                optional=False))

        self.addParameter(ParameterString(
                self.DATE_FROM,
                self.tr(u'Angiv prøve-startdato i formatet YYYY-MM-DD'),
                '1900-01-01',
                optional=True))

        self.addParameter(ParameterString(
                self.DATE_TO,
                self.tr(u'Angiv prøve-slutdato i formatet YYYY-MM-DD'),
                date.today(),
                optional=True))


    def getIcon(self):
        """Load icon """
        return QIcon(os.path.join(JupiterAux.pluginpath(), 'pix', 'jupiter_red.png'))

    def processAlgorithm(self, progress):
        JupiterAux.log_info(u'\nprocessAlgorithm: {}'.format(self.tablename))

        progress.setInfo(u'Start querying "{}" in PCJupiterXL...'.format(self.name))
        progress.setPercentage(30)

        extent = self.getParameterValue(self.EXTENT)
        extent_layer = self.getParameterValue(self.VECTOR_SELECTION)
        compoundname1 = unicode(self.getParameterValue(self.COMPOUNDNAME1))
        compoundname2 = unicode(self.getParameterValue(self.COMPOUNDNAME2))
        xaxeline = self.getParameterValue(self.XAXELINE)
        yaxeline = self.getParameterValue(self.YAXELINE)
        showannotations = self.getParameterValue(self.SHOWANNOTATIONS)
        date_from = self.getParameterValue(self.DATE_FROM)
        date_to = self.getParameterValue(self.DATE_TO)

        qgis = JupiterQGIS()
        if extent == "0,0,0,0":
            if qgis.countSelectedFeatures(extent_layer) != 1:
                JupiterAux.msg_box(u'Der skal være valgt een (og kun en) geometri i {}\nNår afgrænsningen er 0,0,0,0'.format(extent_layer))
                return

        # Create plot
        mapplot = JupiterMatplot()
        result = mapplot.scatterplot(
            extent,
            compoundname1,
            compoundname2,
            date_from,
            date_to,
            extent_layer=extent_layer,
            x_marker=xaxeline,
            y_marker=yaxeline,
            showannotations=showannotations)

        progress.setPercentage(100)

        #if self.tablename == u'Plot Nitrat mod sulfat':
        #    pgtablename = u'mstmvw_bulk_grwchem_alldates'
        #else:
        #    raise Exception(u'Fejl: Tabel eller view: "{}" findes ikke'.format(self.tablename))

        if result:
            progress.setInfo(u'End querying "{}" in PCJupiterXL...'.format(self.name))

            progress.setText(u'<br><b>RESULTAT:</b>')
            progress.setText(u'<br><b>Scatterplot oprettet og åbnet</b>')
        else:
            progress.setInfo(u'Der er sket en fejl i "{}"'.format(self.name))

    def shortHelp(self):
        return self._formatHelp(u'''Lav Sulfat-Nitrat scatterplot<p>Enten trækkes et rektangel eller der bruges en eksisterende tabel med een valgt polygongeometri som afgrænsning<p>''')
