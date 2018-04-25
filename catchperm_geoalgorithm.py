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
from processing.core.parameters import ParameterExtent, ParameterVector, ParameterString, ParameterNumber, \
    ParameterBoolean
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector

from jupiter_qgis import JupiterQGIS
from jupiter_aux import JupiterAux

class CatchpermGeoAlgorithm(GeoAlgorithm):
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    PLANTIDORNAME = 'PLANTIDORNAME'
    EXTENT = 'EXTENT'
    VECTOR_SELECTION = 'VECTOR_SELECTION'
    ONLYPUBLICWATERSUPPLY = 'ONLYPUBLICWATERSUPPLY'
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

        self.addParameter(ParameterString(
                self.PLANTIDORNAME,
                self.tr(u'Anlægsnummer eller anlægsnavn'), '',
                optional=True))

        self.addParameter(
            ParameterExtent(
                self.EXTENT,
                self.tr(u'- alternativt definer afgrænsningen af forespørgsel for {} ').format(self.name),
                default="0,0,0,0",
                optional=True))

        self.addParameter(
            ParameterVector(
                self.VECTOR_SELECTION,
                self.tr(u'- alternativt brug en valgt geometri som afgrænsning for "{}"').format(self.name),
                [ParameterVector.VECTOR_TYPE_POLYGON], True))

        self.addParameter(ParameterBoolean(
                self.ONLYPUBLICWATERSUPPLY,
                self.tr(u'Hent kun tilladelser fra almene vandforsyninger'),
                optional=True))

        self.addOutput(OutputVector(self.OUTPUT, self.tr(u'Gem tilladelser som')))


    def getIcon(self):
        """Load icon """
        return QIcon(os.path.join(JupiterAux.pluginpath(), 'pix', 'jupiter_red.png'))

    def shortHelp(self):
        return self._formatHelp(u'''Indvindingstilladelser<p>Hent indvindingstilladelser for anlæg<p>''')

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""
        progress.setInfo(u'Start querying "{}" in PCJupiterXL...'.format(self.name))
        progress.setPercentage(50)

        plantinput = self.getParameterValue(self.PLANTIDORNAME)
        onlypublic_watersupply = self.getParameterValue(self.ONLYPUBLICWATERSUPPLY)
        output = self.getOutputFromName(self.OUTPUT)

        JupiterAux.log_info(u'\nprocessAlgorithm: {}'.format(self.tablename))

        pgtablename = u'mstmvw_catchperm'

        ok_add_map = True

        if ok_add_map:
            progress.setInfo(u'End querying "{}" in PCJupiterXL...'.format(self.name))
            progress.setPercentage(100)

            progress.setText(u'<br><b>RESULTAT:</b>')
            progress.setText(u'<br><b>Tabel {} er åbnet med navnet {}</b>'.format(self.tablename, self.PLANTIDORNAME))
        else:
            progress.setInfo(u'Der er sket en fejl i "{}"'.format(self.name))
            progress.setPercentage(100)

    def shortHelp(self):
        return self._formatHelp(u'''Find pesticidoverskridelse for navngivet pesticid i Jupiter!<p>Enten trækkes et rektangel eller der bruges en eksisterende tabel med en valgt geometri som afgrænsning<p>''')
