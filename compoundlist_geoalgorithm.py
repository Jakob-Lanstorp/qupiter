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
from processing.core.parameters import ParameterExtent, ParameterVector
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector

from jupiter_qgis import JupiterQGIS
from jupiter_aux import JupiterAux

class CompoundlistGeoAlgorithm(GeoAlgorithm):
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

        #self.addOutput(OutputVector(self.OUTPUT, self.tr(u'Output vektor fil')))
        self.addOutput(OutputVector(self.OUTPUT, self.tr(self.dktablename)))

    def getIcon(self):
        """Load icon """
        return QIcon(os.path.join(JupiterAux.pluginpath(), 'pix', 'jupiter_red.png'))

    def shortHelp(self):
        return self._formatHelp(u'''Hent Stofliste og gruppering<p>Gruppert liste af stoffer efter pesticider, sporstoffer og urganiske komponenter<p>''')

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""
        progress.setInfo(u'Start querying "{}" in PCJupiterXL...'.format(self.name))
        progress.setPercentage(50)

        pgtablename = u'mst_bekendtgoerelse_pesticide_list'
        output = self.getOutputFromName(self.OUTPUT)  #<class 'processing.core.outputs.OutputVector'>

        JupiterAux.log_info('Valgte tabel eller view: {}\n'.format(self.dktablename))

        jq = JupiterQGIS()
        ok_added = jq.add_alphaview(progress, pgtablename, output)

        if ok_added:
            progress.setInfo(u'End querying "{}" in PCJupiterXL...'.format(self.name))
            progress.setPercentage(100)

            progress.setText(u'<br><b>RESULTAT:</b>')
            progress.setText(u'<br><b>Tabel: {} er åbnet med navnet: {}</b>'.format(self.dktablename, pgtablename))
        else:
            progress.setInfo(u'Der er sket en fejl i "{}"'.format(self.name))
            progress.setPercentage(100)
