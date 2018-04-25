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
__date__ = '2018-04-09'
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

class AlphanumericGeoAlgorithm(GeoAlgorithm):
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

        self.addOutput(OutputVector(self.OUTPUT, self.tr(self.name)))

    def getIcon(self):
        """Load icon """
        return QIcon(os.path.join(JupiterAux.pluginpath(), 'pix', 'jupiter_cyan.png'))

    def shortHelp(self):
        return self._formatHelp(
            u'''<b>PCJupiterXL log tabeller</b>
            <p><b>Exporttime:</b> Log over alder på komplet udtræk fra GEUS som DbSync fungerer på.<p>
            <p><b>Syncronizationlog:</b> Log som beskriver hvordan det er gået med de enkelte synkroniseringer.<p>
            <p><b>Syncronizationevent:</b> Log over fejl som findes under synkronisering.<p>            
            ''')

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place
        """
        progress.setInfo(u'Start querying "{}" in PCJupiterXL...'.format(self.name))
        progress.setPercentage(10)

        # Get user input

        output = self.getOutputFromName(self.OUTPUT)  #<class 'processing.core.outputs.OutputVector'>

        pgtablename = ''

        if self.dktablename == u'Åbn synchronizationlog':
            output.description = u'synchronizationlog'
            pgtablename = u'synchronizationlog'
        elif self.dktablename == u'Åbn synchronizationevent':
            output.description = u'synchronizationevent'
            pgtablename = u'synchronizationevent'
        elif self.dktablename == u'Åbn exporttime':
            output.description = u'exporttime'
            pgtablename = u'exporttime'

        JupiterAux.log_info(u'Valgt alphanumeric tabel med pgtablename: {}\n'.format(pgtablename))

        qgis = JupiterQGIS()
        ok_add_alphatable = qgis.add_alphaview(
            progress,
            pgtablename,
            output)

        progress.setPercentage(100)

        if ok_add_alphatable:
            progress.setInfo(u'End querying "{}" in PCJupiterXL...'.format(self.name))

            progress.setText(u'<br><b>RESULTAT:</b>')
            progress.setText(u'<br><b>Tabel med databasenavn: {} er åbnet som: {}</b>'.format(pgtablename, output.description))
        else:
            progress.setText(u'<br><b>Fejl i udtræk. Se log:</b>')