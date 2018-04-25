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
__date__ = '2017-11-24'
__copyright__ = '(C) 2017 by Miljøstyrelsen'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QIcon

import os

from qgis.core import QgsVectorFileWriter

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterExtent, \
    ParameterFile, ParameterString, ParameterVector, ParameterBoolean
from processing.core.outputs import OutputVector, OutputFile, OutputHTML
from processing.tools import dataobjects, vector

from datetime import date

from jupiter_aux import JupiterAux
from jupiter_db import JupiterDb

class SampleCompoundUnitGeoAlgorithm(GeoAlgorithm):
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    COMPOUND = 'COMPOUND'
    SAMPLE = 'SAMPLE'
    OUTPUT = 'OUTPUT'

    def __init__(self, compoundname, compoundgroup,
                 thememap=False, fractileplot=False, depthplot=False, scatterplot=False):
        self.compoundname = compoundname
        self.compoundgroup = compoundgroup

        self.thememap = thememap
        self.fractileplot = fractileplot
        self.depthplot = depthplot
        self.scatterplot = scatterplot


        GeoAlgorithm.__init__(self)

    def __str__(self):
        return 'Group: {}, Compound: {}'.format(self.group, self.name)

    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        # The name that the user will see in the toolbox
        self.name = self.compoundname

        # The branch of the toolbox under which the algorithm will appear
        self.group = self.compoundgroup

        self.addParameter(
            ParameterString(
            self.SAMPLE,
            self.tr(u'Indtast samplenid - prøvenummer - som enhed ønskes for'), ''))

        self.addParameter(
            ParameterString(
            self.COMPOUND,
            self.tr(u'Indtast komponentnavn - for eksempel bly - som enhed ønskes for'), ''))


    def getIcon(self):
        """Load icon """
        return QIcon(os.path.join(JupiterAux.pluginpath(), 'pix', 'jupiter_green.png'))

    def shortHelp(self):
        return self._formatHelp(u'''Enhed til stof i prøve<p>Hent den enhed som er anvendt til et givet stof i en given prøve<p>''')

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""

        progress.setInfo(u'Start querying "{}" in PCJupiterXL...'.format(self.name))
        progress.setPercentage(40)

        sampleid = self.getParameterValue(self.SAMPLE)
        compound_name = self.getParameterValue(self.COMPOUND)

        db = JupiterDb()
        unit = db.get_unit(sampleid, compound_name)

        progress.setInfo(u'End querying "{}" in PCJupiterXL...'.format(self.name))
        progress.setPercentage(100)

        progress.setText('<br><b>RESULTAT:</b><br>')

        if unit:
            progress.setText(u'<b>Enhed for {} i prøve {} er [{}].<br></b><br>'.format(compound_name, sampleid, unit))
        else:
            progress.setText(u'<b>Enheden for {} i prøve {} findes ikke. Tjek dit sampleno og komponentnavn igen.<br></b><br>'.format(compound_name, sampleid, unit))

