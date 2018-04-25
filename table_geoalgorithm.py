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

class TableGeoAlgorithm(GeoAlgorithm):
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

        self.addOutput(OutputVector(self.OUTPUT, self.tr(self.name)))

    def getIcon(self):
        """Load icon """
        return QIcon(os.path.join(JupiterAux.pluginpath(), 'pix', 'jupiter_cyan.png'))

    def shortHelp(self):
        return self._formatHelp(
            u'''<b>PCJupiterXL</b>
            <p>Enten trækkes et rektangel eller der bruges en eksisterende tabel med een (og kun en) valgt polygongeometri som afgrænsning.<p>
            <a href="jupiter.geus.dk/TabellerKoder/">Link til tabeller og kodelister i PCJupiterXL datamodellen hos GEUS</a>''')

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place
        """
        progress.setInfo(u'Start querying "{}" in PCJupiterXL...'.format(self.name))
        progress.setPercentage(10)

        # Get user input
        extent = self.getParameterValue(self.EXTENT)
        maplayerselection = self.getParameterValue(self.VECTOR_SELECTION)

        output = self.getOutputFromName(self.OUTPUT)  #<class 'processing.core.outputs.OutputVector'>

        rowid = None            # rowid on view is compulsory
        where_sql = None        # Time interval query

        if self.dktablename == u'Åbn boringstabellen':
            output.description = u'Boringer'
            pgtablename = u'borehole'
        elif self.dktablename == u'Åbn miljøboringer':
            output.description = u'Miljoeboringer'
            pgtablename = u'borehole'
            where_sql = "(geom is not null) and (use = 'L' or purpose = 'L')"
        elif self.dktablename == u'Åbn sløjfede boringer':
            output.description = u'Sloejfede boringer'
            rowid = 'objectid'
            pgtablename = u'mstmvw_boring_canceled'
        elif self.dktablename == u'Åbn GRUMO boringer':
            output.description = u'GRUMO boringer'
            rowid = 'row_id1'
            pgtablename = u'mstmvw_grumo_boringer'
        elif self.dktablename == u'Åbn anlægstabellen':
            output.description = u'Anlaeg'
            pgtablename = u'drwplant'
        elif self.dktablename == u'Åbn vandforsyningsboringer':
            output.description = u'Vandforsyningsboringer'
            rowid = 'row_id1'
            pgtablename = u'mstmvw_vandforsyningsboringer'
        elif self.dktablename == u'Åbn pejlinger':
            output.description = u'Pejlinger'
            rowid = 'row_id'
            pgtablename = u'mstmvw_waterlevel_all_dates'
        else:
            raise Exception(u'Tabel eller view: {} findes ikke i metoden_geoalgorithm.processAlgotithm'.format(self.dktablename))

        JupiterAux.log_info(u'Valgt tabel eller view: {} med pgtablename: {}\n'.format(self.dktablename, pgtablename))

        qgis = JupiterQGIS()
        ok_add_map = qgis.add_maplayer(
            progress,
            pgtablename,
            output,
            extent,
            selectionLayername=maplayerselection,
            rowid=rowid,
            where_sql2=where_sql)

        progress.setPercentage(100)

        if ok_add_map:
            progress.setInfo(u'End querying "{}" in PCJupiterXL...'.format(self.name))

            progress.setText(u'<br><b>RESULTAT:</b>')
            progress.setText(u'<br><b>Tabel med databasenavn: {} er åbnet som: {}</b>'.format(pgtablename, output.description))
        else:
            progress.setText(u'<br><b>Fejl i udtræk. Se log:</b>')