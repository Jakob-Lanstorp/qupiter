# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Qjupiter
                                 A QGIS plugin
 Qjupiter data plugin
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

from qgis.core import QgsVectorFileWriter

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterExtent, \
    ParameterFile, ParameterString, ParameterVector, ParameterBoolean
from processing.core.outputs import OutputVector, OutputFile, OutputHTML
from processing.tools import dataobjects, vector

from datetime import date
import os

from jupiter_aux import JupiterAux
from jupiter_db import JupiterDb

class CompoundnoToNameGeoAlgorithm(GeoAlgorithm):
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

    COMPOUND = 'COMPOUND'

    def __init__(self, name, group):

        #? strange api ?
        self.xname = name
        self.xgroup = group

        GeoAlgorithm.__init__(self)

    def __str__(self):
        return 'Group: {}, Compound: {}'.format(self.group, self.name)

    def defineCharacteristics(self):

        # The name that the user will see in the toolbox
        self.name = self.xname
        # The branch of the toolbox under which the algorithm will appear
        self.group = self.xgroup

        self.addParameter(
            ParameterString(
            self.COMPOUND,
            self.tr(u'Indtast stofnummer - som stofnavn ønskes for'), ''))

    def getIcon(self):
        """Load icon """
        return QIcon(os.path.join(JupiterAux.pluginpath(), 'pix', 'jupiter_green.png'))

    def shortHelp(self):
        return self._formatHelp(u'''Stofnummer til stofnavn<p>Indtast stofnummer (compoundno) fra Jupiter og få det tilhørende stofnavn<p>''')

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""

        progress.setInfo(u'Start querying "{}" in PCJupiterXL...'.format(self.name))
        progress.setPercentage(70)

        compound_id = self.getParameterValue(self.COMPOUND)

        db = JupiterDb()
        compound_name = db.compoundno_to_name(compound_id)

        progress.setInfo(u'End querying "{}" in PCJupiterXL...'.format(self.name))
        progress.setPercentage(100)

        progress.setText(u'<br><b>RESULTAT:</b>')

        if not compound_name:
            progress.setText(u'<br><b>Indtastede stofnummer: "{}" findes ikke i PCJupiterXL</b><br>'.format(compound_id))
        else:
            progress.setText(u'<b>Indtastet stofnummer: "{}" har navnet: {}</b><br>'.format(compound_id, compound_name))

