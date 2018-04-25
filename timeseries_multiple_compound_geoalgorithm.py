# -*- coding: utf-8 -*-

"""
/***************************************************************************
 PCJupiterXL
                                 A QGIS plugin
 PCJupiterXL data plugin
                              -------------------
        begin                : 2018-01-19
        copyright            : (C) 2018 by Miljøstyrelsen
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
__date__ = '2018-01-19'
__copyright__ = '(C) 2018 by Miljøstyrelsen'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QIcon

import os

from qgis.core import QgsVectorFileWriter

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterExtent, \
    ParameterFile, ParameterString, ParameterVector, ParameterBoolean, ParameterSelection
from processing.core.outputs import OutputVector, OutputFile, OutputHTML
from processing.tools import dataobjects, vector

from datetime import date

from jupiter_aux import JupiterAux
from jupiter_matplot import JupiterMatplot

class TimeSeriesMultiplecompoundGeoAlgorithm(GeoAlgorithm):
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    BOREHOLE = 'BOREHOLE'
    COMPOUND = 'COMPOUND'
    SKIP_UNITS = 'SKIP_UNITS'
    INTAKE = 'INTAKE'
    DATE_TO = 'DATE_TO'
    DATE_FROM = 'DATE_FROM'

    def __init__(self, dktablename, groupname,
                 thememap=False, fractileplot=False, depthplot=False, scatterplot=False):
        """
        :param dktablename: itemname in processing gui also used as pseudo tablename
        :param groupname:  group to place item in
        """
        self.dktablename = dktablename
        self.groupname = groupname


        GeoAlgorithm.__init__(self)

    def __str__(self):
        return 'Group: {}, Compound: {}'.format(self.group, self.name)

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
        self.addParameter(ParameterString(
                self.COMPOUND,
                self.tr(u'Angiv et eller flere stoffer. Flere stoffer adskilles med semikolon'),
                ''))

        self.addParameter(ParameterString(
                self.BOREHOLE,
                self.tr(u'Angiv et (og kun et) dgunummer'),
                '',
                optional=False))

        self.addParameter(ParameterString(
                self.INTAKE,
                self.tr(u'Angiv indtag for stofanalyse'),
                '',
                optional=False))

        self.addParameter(ParameterBoolean(
                self.SKIP_UNITS,
                self.tr(u'Undlad stofenhed - for hurtig kørsel'),
                optional=True))

        self.addParameter(ParameterString(
                self.DATE_FROM,
                self.tr(u'Angiv start-prøvedato [YYYY-MM-DD]'),
                '1900-01-01',
                optional=False))

        self.addParameter(ParameterString(
                self.DATE_TO,
                self.tr(u'Angiv slut prøvedato [YYYY-MM-DD]'),
                date.today(),
                optional=False))


    def getIcon(self):
        """Load icon """
        return QIcon(os.path.join(JupiterAux.pluginpath(), 'pix', 'jupiter_violet.png'))

    def shortHelp(self):
        return self._formatHelp(u'''Tidsserieplot. En boring flere stoffer<p>Enten trækkes et rektangel eller der bruges en eksisterende tabel med en valgt polygongeometri som afgrænsning<p>''')

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""

        progress.setInfo(u'Start querying "{}" in PCJupiterXL...'.format(self.name))

        # Get user input
        compounds = self.getParameterValue(self.COMPOUND)
        boreholeno = self.getParameterValue(self.BOREHOLE)
        skip_unit = self.getParameterValue(self.SKIP_UNITS)
        intake = self.getParameterValue(self.INTAKE)
        date_from = self.getParameterValue(self.DATE_FROM)
        date_to = self.getParameterValue(self.DATE_TO)

        progress.setText(u'<br><b>Data hentes og graf beregnes....</b><br>')

        mapplot = JupiterMatplot()

        #result, not_found = self.test_oneborehole_multiplecompounds1()
        #result, not_found = self.test_oneborehole_multiplecompounds2()

        result, not_found = mapplot.timeseries_oneborehole_multiplecompounds(
            boreholeno, intake, compounds, date_from, date_to, skip_unit=skip_unit, progress=progress)

        if result and len(not_found) == 0:
            progress.setText(u'<b>Tidsserie for stof: "{}" - indtag: "{}" i boring: "{}" oprettet.<br></b><br>'.format(
                compounds.replace(';', ','),
                intake,
                boreholeno))
        elif result and len(not_found) > 0:
            progress.setText(u'<b>Tidsserie for stoffer: "{}" i boring: "{}" - indtag: "{}" er oprettet.<br>Stof som ikke findes i boring: "{}".</b><br>'.format(
                compounds.replace(';', ','),
                boreholeno,
                intake,
                ', '.join(not_found)))
        else:
            progress.setText(u'<b>NO DATE: Boring: "{}", indtag: "{}" har ingen analyser for {} i tidsperioden {} til {}.<br></b><br>'.
                             format(boreholeno, intake, compounds.replace(';', ','), date_from, date_to))

        progress.setPercentage(100)


    def test_oneborehole_multiplecompounds1(self):
        """
            Test multiple compounds. Iron not existing for borehole '230.  205'
        """
        mapplot = JupiterMatplot()

        return mapplot.timeseries_oneborehole_multiplecompounds(
            '230.  205',
            1,
            'Nitrat; Sulfat; Chlorid; Jern; kobber',
            '1900-01-01',
            str(date.today()),
            skip_unit=False,
            progress=None)

    def test_oneborehole_multiplecompounds2(self):
        """
            Test multiple compounds. Kobber has two units for borehole '230.  206'
        """
        mapplot = JupiterMatplot()

        return mapplot.timeseries_oneborehole_multiplecompounds(
            '230.  206',
            1,
            'Kobber',
            '1900-01-01',
            str(date.today()),
            skip_unit=False,
            progress=None)

    def test_graph1(self):
        """
        http://data.geus.dk/JupiterWWW/borerapport.jsp?atlasblad=0&loebenr=0&bogstav=&dgunr=230.++205&submit=Vis+boringsdata
        https://www.linuxquestions.org/questions/programming-9/python-matplotlib-postgresql-xaxis-as-dates-4175445040/
        TODO: Why is test_graph1 faster than test_graph2 ?
        """
        from jupiter_db import JupiterDb
        import psycopg2
        from matplotlib import pyplot as plot, dates

        db = JupiterDb()
        params = db.get_dbparams()
        conn = psycopg2.connect(**params)  #psycopg2.connect('dbname=foo user=bar')
        cur = conn.cursor()
        cur.execute("""
            SELECT
              ca.amount,
              cs.sampledate
            FROM jupiter.borehole b
            INNER JOIN jupiter.intake i USING (boreholeno)
            INNER JOIN jupiter.grwchemsample cs USING (boreholeno)
            INNER JOIN jupiter.grwchemanalysis ca ON ca.sampleid = cs.sampleid
            INNER JOIN jupiter.compoundlist cl ON ca.compoundno = cl.compoundno
            --INNER JOIN kort.lolland l ON st_dwithin(b.geom, l.geom, 0)
            WHERE cl.long_text ilike 'nitrat' AND b.boreholeno = '230.  205'
            ORDER BY cs.sampledate
        """)

        data = cur.fetchall()
        cur.close()
        conn.close()

        ms, dt = zip(*data)
        dt = dates.date2num(dt)
        plot.plot_date(dt, ms)
        plot.xticks(rotation='vertical')
        plot.show()

        return True


    def test_graph2(self):
        """
        http://data.geus.dk/JupiterWWW/borerapport.jsp?atlasblad=0&loebenr=0&bogstav=&dgunr=230.++205&submit=Vis+boringsdata
        https://www.linuxquestions.org/questions/programming-9/python-matplotlib-postgresql-xaxis-as-dates-4175445040/
        """
        from jupiter_db import JupiterDb
        import psycopg2
        from matplotlib import pyplot as plot, dates

        db = JupiterDb()
        params = db.get_dbparams()
        conn = psycopg2.connect(**params)  #psycopg2.connect('dbname=foo user=bar')
        cur = conn.cursor()
        cur.execute("""
            SELECT
              amount,
              sampledate
            FROM 
              jupiter.mstmvw_chemanalysis
            WHERE
              long_text ilike 'nitrat' AND 
              boreholeno = '230.  205'
        """)

        data = cur.fetchall()
        cur.close()
        conn.close()

        ms, dt = zip(*data)
        dt = dates.date2num(dt)
        plot.plot_date(dt, ms)
        plot.xticks(rotation='vertical')
        plot.show()

        return True

