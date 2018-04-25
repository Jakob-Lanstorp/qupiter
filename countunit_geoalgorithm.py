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

class CountUnitGeoAlgorithm(GeoAlgorithm):
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

    def shortHelp(self):
        return self._formatHelp(u'''Tæl enheder<p>Tøl hvor mange gange som en enhed optræder for et given stof<p>''')

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
            self.COMPOUND,
            self.tr(u'Indtast komponentnavn - for eksempel bly - som enhed ønskes for'), ''))

        #Det kræver at man manuelt åbner result viewer i menu
        #self.addOutput(OutputHTML(self.OUTPUT, 'Result log'))


    #def help(self):
        #pass

    def getIcon(self):
        """Load icon """
        return QIcon(os.path.join(JupiterAux.pluginpath(), 'pix', 'jupiter_green.png'))

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""

        #import sys
        #reload(sys)
        #sys.setdefaultencoding('utf-8')

        progress.setInfo(u'Start querying "{}" in PCJupiterXL...'.format(self.name))
        progress.setPercentage(40)

        compound_name = self.getParameterValue(self.COMPOUND)

        db = JupiterDb()
        result_list = db.count_compound_units(compound_name)

        progress.setInfo(u'End querying "{}" in PCJupiterXL...'.format(self.name))
        progress.setPercentage(100)

        progress.setText(u'<br><b>RESULTAT:</b>')

        if not result_list:
            progress.setText(u'<br><b>Der er ikke fundet nogle enheder for komponent med navn: {}</b><br>'.format(compound_name))
            return

        if len(result_list) == 1:
            progress.setText(u'<br><b>Der er 1 resultat:</b><br>')
        else:
            progress.setText(u'<br><b>Der er {} resultater. Måske er der datafejl i Jupiter?!!</b><br>'.format(len(result_list)))

        # OutputHTML er for ringe
        #output = self.getOutputValue(self.OUTPUT)  #https://docs.qgis.org/2.2/en/docs/training_manual/processing/log.html
        #f = open(output, 'w')

        for item in result_list:
            count, unit = item

            progress.setText(u'<b>Enhed for {} er [{}]. Enheden optræder i Jupiter {} gange for {}.</b><br>'.format(compound_name, unit, count, compound_name))

            #f.write('<pre>')
            #f.write(u'<b>Enhed for {} er [{}].<br>Enheden optræder i Jupiter {} gange for {}.</b><br>'.format(compound_name, unit, count, compound_name))
            #f.write('</pre>')

        #f.close()
