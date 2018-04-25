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

import os

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterExtent, ParameterVector, ParameterString, ParameterNumber, ParameterBoolean
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector

from jupiter_qgis import JupiterQGIS
from jupiter_aux import JupiterAux
from jupiter_db import JupiterDb

from datetime import date

class CompoundQueryGeoAlgorithm(GeoAlgorithm):
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    EXTENT = 'EXTENT'
    VECTOR_SELECTION = 'VECTOR_SELECTION'
    COMPOUNDNAME = 'COMPOUNDNAME'
    COMPOUNDLIMIT = 'COMPOUNDLIMIT'
    DATE_FROM = 'DATE_FROM'
    DATE_TO = 'DATE_TO'
    LOAD_ONLY_LATEST = 'LOAD_ONLY_LATEST'
    OUTPUT = 'OUTPUT'

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
                self.COMPOUNDNAME,
                self.tr(u'Stofnavn'), ''))

        self.addParameter(ParameterNumber(
            self.COMPOUNDLIMIT,
            self.tr(u'Udtræk kun analyseværdier over (0 = alle analyser):'),
            0,
            None,
            '0',
            optional=True))

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
                self.tr(u'-eller hent kun seneste data fra hver boring'),
                optional=True))

        self.addOutput(OutputVector(self.OUTPUT, self.tr('Stoftabel')))


    def getIcon(self):
        """Load icon """
        return QIcon(os.path.join(JupiterAux.pluginpath(), 'pix', 'jupiter_red.png'))

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""
        progress.setInfo(u'Start querying "{}" in PCJupiterXL...'.format(self.name))
        progress.setPercentage(50)

        extent = self.getParameterValue(self.EXTENT)
        extent_layer = self.getParameterValue(self.VECTOR_SELECTION)
        compoundname = unicode(self.getParameterValue(self.COMPOUNDNAME))
        compoundlimit = self.getParameterValue(self.COMPOUNDLIMIT)
        date_from = self.getParameterValue(self.DATE_FROM)
        date_to = self.getParameterValue(self.DATE_TO)
        onlyload_latest = self.getParameterValue(self.LOAD_ONLY_LATEST)
        output = self.getOutputFromName(self.OUTPUT)

        where_sql = None

        db = JupiterDb()
        compoundno = db.compoundname_to_no(compoundname)
        if compoundno is None:
            JupiterAux.msg_box(u'Stoffet: "{}" findes ikke i PCJupiterXL'.format(compoundname))
            progress.setPercentage(100)
            return

        JupiterAux.log_info(u'\nprocessAlgorithm: {}'.format(self.tablename))

        output.description = compoundname

        if self.tablename == u'Søg et stof fra grundvand (boring)':
            if onlyload_latest:
                pgtablename = u'mstvw_bulk_grwchem_latestdates'
                where_sql = u"compoundno = {} AND amount > {} AND geom IS NOT NULL".format(compoundno, compoundlimit)
            else:
                pgtablename = u'mstvw_bulk_grwchem'   #is alldates
                where_sql = u"sampledate > to_date('{}', 'YYYY-MM-DD') AND sampledate < to_date('{}', 'YYYY-MM-DD') AND compoundno = {} AND amount > {} AND geom IS NOT NULL".\
                    format(date_from, date_to, compoundno, compoundlimit)
        elif self.tablename == u'Søg et stof fra vandværk (anlæg)':
            if onlyload_latest:
                pgtablename = u'mstmvw_bulk_pltchem_latestdates'
                where_sql = u"compoundno = {} AND amount > {} AND geom IS NOT NULL".format(compoundno, compoundlimit)
            else:
                pgtablename = u'mstmvw_bulk_pltchem_alldates'
                where_sql = u"sampledate > to_date('{}', 'YYYY-MM-DD') AND sampledate < to_date('{}', 'YYYY-MM-DD') AND compoundno = {} AND amount > {} AND geom IS NOT NULL".\
                    format(date_from, date_to, compoundno, compoundlimit)
        else:
            raise Exception(u'Fejl: Tabel eller view: "{}" findes ikke'.format(self.tablename))

        jq = JupiterQGIS()
        ok_add_map = jq.add_maplayer(
            progress,
            pgtablename,
            output,
            extent,
            selectionLayername=extent_layer,
            rowid='row_id',
            where_sql2=where_sql)

        if ok_add_map:
            progress.setInfo(u'End querying "{}" in PCJupiterXL...'.format(self.name))

            progress.setText(u'<br><b>RESULTAT:</b>')
            progress.setText(u'<br><b>Tabel {} er åbnet med navnet {}</b>'.format(self.tablename, compoundname))
        else:
            progress.setInfo(u'Der er sket en fejl i "{}"'.format(self.name))

    def shortHelp(self):
        return self._formatHelp(u'''Find stofanalyser<p>Enten trækkes et rektangel eller der bruges en eksisterende tabel med en valgt polygongeometri som afgrænsning<p>''')
