# -*- coding: utf-8 -*-

"""
/***************************************************************************
 PCJupiterXL
                                 A QGIS plugin
 PCJupiterXL data plugin
                              -------------------
        begin                : 2017-03-14
        copyright            : (C) 2017 by Miljøstyrelsen
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
__date__ = '2017-03-14'
__copyright__ = '(C) 2017 by Miljøstyrelsen'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QIcon

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterExtent, ParameterVector, ParameterBoolean, ParameterString
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector

from datetime import date
import os

from jupiter_qgis import JupiterQGIS
from jupiter_aux import JupiterAux

class TableDateGeoAlgorithm(GeoAlgorithm):
    """This is an example algorithm that takes a vector layer and
    creates a new one just with just those features of the input
    layer that are selected.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the GeoAlgorithm class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    EXTENT = 'EXTENT'
    VECTOR_SELECTION = 'VECTOR_SELECTION'
    LOAD_ONLY_LATEST = 'LOAD_ONLY_LATEST'
    DATE_TO = 'DATE_TO'
    DATE_FROM = 'DATE_FROM'
    OUTPUT = 'OUTPUT'

    def __init__(self, dktablename, groupname):
        """
        :param dktablename: itemname in processing gui also used as pseudo tablename
        :param groupname:  group to place item in
        """
        self.dktablename = dktablename
        self.groupname = groupname

        GeoAlgorithm.__init__(self)

    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        # The name that the user will see in the toolbox
        self.name = self.dktablename

        # The branch of the toolbox under which the algorithm will appear
        self.group = self.groupname

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(
            ParameterExtent(
                self.EXTENT,
                self.tr(u'Definer afgrænsningen af forespørgsel for {} ').format(self.dktablename),
                default="0,0,0,0"))

        self.addParameter(
            ParameterVector(
                self.VECTOR_SELECTION,
                self.tr(u'- eller brug en valgt geometri som afgrænsning for "{}" i tabel.').format(self.dktablename),
                [ParameterVector.VECTOR_TYPE_POLYGON], False))

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

        self.addParameter(ParameterBoolean(
                self.LOAD_ONLY_LATEST,
                self.tr(u'-eller hent kun seneste - {} data fra hver boring'.format(str(self.name).lower())),
                optional=True))

        self.addOutput(OutputVector(self.OUTPUT, self.tr(self.name)))

    def getIcon(self):
        """Load icon """
        return QIcon(os.path.join(JupiterAux.pluginpath(), 'pix', 'jupiter_red.png'))

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place
        """
        progress.setInfo(u'Start querying "{}" in PCJupiterXL...'.format(self.name))
        progress.setPercentage(10)

        # Get user input
        extent = self.getParameterValue(self.EXTENT)
        maplayerselection = self.getParameterValue(self.VECTOR_SELECTION)
        date_to = self.getParameterValue(self.DATE_TO)
        date_from = self.getParameterValue(self.DATE_FROM)
        onlyload_latest = self.getParameterValue(self.LOAD_ONLY_LATEST)
        output = self.getOutputFromName(self.OUTPUT)  #<class 'processing.core.outputs.OutputVector'>

        where_sql = None        # Time interval query

        if self.dktablename == u'Beregn vandtype':
            output.description = u'Vandtype'
            if onlyload_latest:
                pgtablename = u'mstmvw_watertype4_latestdate'
            else:
                pgtablename = u'mstmvw_watertype4_alldates'
                where_sql = u"sampledate > to_date('{}', 'YYYY-MM-DD') AND sampledate < to_date('{}', 'YYYY-MM-DD')".format(date_from, date_to)
        elif self.dktablename == u'Beregn ionbalance':
            output.description = u'Ionbalance'
            if onlyload_latest:
                pgtablename = u'mstmvw_ionbalance_latest_dates'
            else:
                pgtablename = u'mstmvw_ionbalance_all_dates'
                where_sql = u"sampledate > to_date('{}', 'YYYY-MM-DD') AND sampledate < to_date('{}', 'YYYY-MM-DD')".format(date_from, date_to)
        elif self.dktablename == u'Hent uorganiske stoffer':
            output.description = u'Uorganiske stoffer'
            if onlyload_latest:
                pgtablename = u'mstmvw_inorganic_compound_latest_dates'
            else:
                pgtablename = u'mstmvw_inorganic_compound_all_dates'
                where_sql = u"sampledate > to_date('{}', 'YYYY-MM-DD') AND sampledate < to_date('{}', 'YYYY-MM-DD')".format(date_from, date_to)
        elif self.dktablename == u'Åbn pejlinger':
            output.description = u'Pejlinger'
            if onlyload_latest:
                pgtablename = u'mstmvw_waterlevel_latest_dates'
            else:
                pgtablename = u'mstmvw_waterlevel_all_dates'
                where_sql = u"pejledato > to_date('{}', 'YYYY-MM-DD') AND pejledato < to_date('{}', 'YYYY-MM-DD')".format(date_from, date_to)
        elif self.dktablename == u'Kombineret kemiskudtræk':
            output.description = u'Kemi'
            if onlyload_latest:
                pgtablename = u'mstmvw_combined_chemestry_latestdates'
            else:
                pgtablename = u'mstmvw_combined_chemestry_alldates'
                where_sql = u"sampledate > to_date('{}', 'YYYY-MM-DD') AND sampledate < to_date('{}', 'YYYY-MM-DD')".format(
                        date_from, date_to)
        else:
            raise Exception(u'Fejl. tabel eller view: {} findes ikke'.format(self.dktablename))

        JupiterAux.log_info(u'Valgt tabel eller view: {} med pgtablename: {}\n'.format(self.dktablename, pgtablename))

        jq = JupiterQGIS()
        ok_add_map = jq.add_maplayer(
            progress,
            pgtablename,
            output,
            extent,
            selectionLayername=maplayerselection,
            rowid='row_id',
            where_sql2=where_sql)

        progress.setPercentage(100)

        if ok_add_map:
            progress.setInfo(u'End querying "{}" in PCJupiterXL...'.format(self.name))

            progress.setText(u'<br><b>RESULTAT:</b>')
            progress.setText(u'<br><b>Tabel med databasenavn: {} er åbnet som: {}</b>'.format(pgtablename, output.description))
        else:
            progress.setText(u'<br><b>Fejl i udtræk. Se log:</b>')

    def shortHelp(self):
        return self._formatHelp(u'''Kemiudtræk via datperiode<p>Enten trækkes et rektangel eller der bruges en eksisterende tabel med een valgt polygongeometri som afgrænsning<p>''')