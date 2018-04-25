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
from jupiter_qgis import JupiterQGIS

class RemoveCanvasItemsGeoAlgorithm(GeoAlgorithm):
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

    REMOVECANVASITEMS = 'REMOVECANVASITEMS'

    def __init__(self, compoundname, compoundgroup):
        self.compoundname = compoundname
        self.compoundgroup = compoundgroup

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

        self.addParameter(ParameterBoolean(
                self.REMOVECANVASITEMS,
                self.tr(u'Fjern markering fra kort'),
                True,
                optional=False))

    #def help(self):
        #pass

    def getIcon(self):
        """Load icon """
        return QIcon(os.path.join(JupiterAux.pluginpath(), 'pix', 'jupiter_green.png'))

    def shortHelp(self):
        return self._formatHelp(u'''Fjern kortmarkeringer<p>Fjerner den kortmarkering som kommer i kort efter plotdiagram interaktion<p>''')

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""

        progress.setInfo(u'Fjerner markeringer fra kort')
        progress.setPercentage(40)

        remove = self.getParameterValue(self.REMOVECANVASITEMS)

        if remove:
            qgis = JupiterQGIS()
            qgis.remove_canvas_items(vertexmarker=True)

        progress.setInfo(u'Fjerning af markeringer i kort færdig')
        progress.setPercentage(100)

