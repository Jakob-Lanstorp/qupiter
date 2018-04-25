# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Qupiter
        A QGIS plugin Qjupiter data plugin
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

from processing.core.AlgorithmProvider import AlgorithmProvider
from processing.core.ProcessingConfig import Setting, ProcessingConfig

from PyQt4.QtGui import QIcon

from jupiter_db import JupiterDb
from jupiter_aux import JupiterAux

from table_geoalgorithm import TableGeoAlgorithm
from tabledate_geoalgorithm import TableDateGeoAlgorithm
from countunit_geoalgorithm import CountUnitGeoAlgorithm
from samplecompoundunit_geoalgorithm import SampleCompoundUnitGeoAlgorithm
from compoundname_to_no_geoalgorithm import CompoundnameToNoGeoAlgorithm
from compoundno_to_name_geoalgorithm import CompoundnoToNameGeoAlgorithm
from compoundlist_geoalgorithm import CompoundlistGeoAlgorithm
from dgunr_geoalgorithm import DgunrGeoAlgorithm
from timeseries_multiple_borehole_geoalgorithm import TimeSeriesMultipleBoreholeGeoAlgorithm
from timeseries_multiple_compound_geoalgorithm import TimeSeriesMultiplecompoundGeoAlgorithm
from catchperm_geoalgorithm import CatchpermGeoAlgorithm
from timeseries_multiple_borehole_bymapselect_geoalgorithm import TimeSeriesMultipleBoreholeByMapSelectGeoAlgorithm
from remove_canvas_items_geoalgorithm import RemoveCanvasItemsGeoAlgorithm
from compound_query_geoalgorithm import CompoundQueryGeoAlgorithm
from all_compound_query_geoalgorithm import AllCompoundQueryGeoAlgorithm
from scatter_geoalgorithm import ScatterGeoAlgorithm
from alphanumeric_geoalgorithm import AlphanumericGeoAlgorithm

import os

class QupiterProvider(AlgorithmProvider):
    MY_DUMMY_SETTING = 'MY_DUMMY_SETTING'

    def __init__(self):
        AlgorithmProvider.__init__(self)

        ## Try to clear the message log
        # from PyQt4.QtGui import QDockWidget
        # from qgis.utils import iface
        # consoleWidget = iface.mainWindow().findChild(QDockWidget, 'PythonConsole')
        # consoleWidget.console.shellOut.clearConsole()
        # MessageLog = iface.mainWindow().findChild(QDockWidget, 'MessageLog')

        # for child in iface.mainWindow().children():
        #    JupiterAux.log_info(child.objectName())

        ## Explained: Debugger between QGIS and pyCharm
        ## For the debugger to run the four lines below must be enabled - disable for qgis startup
        ## Enable the lines - run the debugger from pyCharm - and refresh plugin in QGIS

        if 1 == 2:
            import sys
            sys.path.append(r'C:\Program Files\JetBrains\PyCharm 2017.3.2\debug-eggs\pycharm-debug.egg')
            import pydevd
            pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True)

        # Deactivate provider by default
        #self.activate = False

        JupiterAux.log_info('\n------------ Qupiter ------------')

        # Write out status information
        db = JupiterDb()
        #JupiterAux.log_info(u'Test DB connection: {}'.format(db.test_connection()))
        JupiterAux.log_info(u'{} version:\t\t{}'.format(JupiterAux.JUPITER, JupiterAux.get_meta_version()))
        JupiterAux.log_info(u'Sidste komplette restore:\t\t{} dage'.format(db.database_geus_export_time_in_days()))
        JupiterAux.log_info(u'Sidste DbSync synkronisation:\t{} dage'.format(db.database_dbsync_success_in_days()))
        JupiterAux.log_info(u'Yngste sample insert i databasen:\t{} dage'.format(db.database_youngest_insert_in_days()))

        #JupiterAux.log_info('Host: {} -- Database: {} -- User: {}'.format(

        #JupiterAux.enable_qgis_log()
        #JupiterAux.log_info('Global QGIS log enabled!')

        self.createAlgsList()

    def _loadAlgorithms(self):
        self.algs = self.preloadedAlgs

    def createAlgsList(self):
        # Load algorithms
        self.alglist = [
            # JupiterCompound(u'Manglende indtagsmummer', u'Dataudtræk'),
            # JupiterCompound(u'Manglende X/Y-koordinator', u'Dataudtræk'),
            # JupiterCompound(u'Manglende filtertop/-bund', u'Dataudtræk'),
            # JupiterCompound(u'Ekstremeværdier', u'Dataudtræk'),

            TableDateGeoAlgorithm(u'Beregn ionbalance', u'Kemi'),
            TableDateGeoAlgorithm(u'Hent uorganiske stoffer', u'Kemi'),
            TableDateGeoAlgorithm(u'Beregn vandtype', u'Kemi'),
            TableDateGeoAlgorithm(u'Kombineret kemiskudtræk', u'Kemi'),
            CompoundlistGeoAlgorithm(u'Hent stofliste og -gruppering', u'Kemi'),
            CompoundQueryGeoAlgorithm(u'Søg et stof fra grundvand (boring)', u'Kemi'),
            CompoundQueryGeoAlgorithm(u'Søg et stof fra vandværk (anlæg)', u'Kemi'),
            AllCompoundQueryGeoAlgorithm(u'Hent alle stoffer fra grundvand (boring)', u'Kemi'),
            AllCompoundQueryGeoAlgorithm(u'Hent alle stoffer fra vandværk (anlæg)', u'Kemi'),

            ScatterGeoAlgorithm(u'Plot stof mod stof', u'Scatterplot'),

            CountUnitGeoAlgorithm(u'Tæl stofenhed', u'Værktøjer'),
            SampleCompoundUnitGeoAlgorithm(u'Stofenhed for prøve', u'Værktøjer'),
            CompoundnameToNoGeoAlgorithm(u'Stofnavn til -nummer', u'Værktøjer'),
            CompoundnoToNameGeoAlgorithm(u'Stofnummer til -navn', u'Værktøjer'),
            RemoveCanvasItemsGeoAlgorithm(u'Fjern markering fra kort', u'Værktøjer'),

            TableGeoAlgorithm(u'Åbn boringstabellen', u'Boring og anlæg'),
            TableGeoAlgorithm(u'Åbn vandforsyningsboringer', u'Boring og anlæg'),
            TableGeoAlgorithm(u'Åbn miljøboringer', u'Boring og anlæg'),
            TableGeoAlgorithm(u'Åbn pejlinger', u'Boring og anlæg'),
            TableGeoAlgorithm(u'Åbn sløjfede boringer', u'Boring og anlæg'),
            TableGeoAlgorithm(u'Åbn GRUMO boringer', u'Boring og anlæg'),
            #TODO CatchpermGeoAlgorithm(u'Indvindingstilladelser', u'Boring og anlæg'),
            DgunrGeoAlgorithm(u'Åbn boringer fra CSV', u'Boring og anlæg'),
            TableGeoAlgorithm(u'Åbn anlægstabellen', u'Boring og anlæg'),

            TimeSeriesMultipleBoreholeGeoAlgorithm(u'Søg et stof i flere boringer via dgunr', u'Tidsserie'),
            TimeSeriesMultipleBoreholeByMapSelectGeoAlgorithm(u'Søg et stof i flere boringer via kort', u'Tidsserie'),
            TimeSeriesMultiplecompoundGeoAlgorithm(u'Søg flere stoffer i en boring', u'Tidsserie'),

            AlphanumericGeoAlgorithm(u'Åbn synchronizationlog', 'DbSync log'),
            AlphanumericGeoAlgorithm(u'Åbn synchronizationevent', 'DbSync log'),
            AlphanumericGeoAlgorithm(u'Åbn exporttime', 'DbSync log')
        ]

        #for alg in self.alglist:
            #alg.provider = self


    def initializeSettings(self):
        """In this method we add settings needed to configure our
        provider.

        Do not forget to call the parent method, since it takes care
        or automatically adding a setting for activating or
        deactivating the algorithms in the provider.
        """
        AlgorithmProvider.initializeSettings(self)
        ProcessingConfig.addSetting(Setting('Example algorithms',
                                            QupiterProvider.MY_DUMMY_SETTING,
                                            'Example setting', 'Default value'))

    def unload(self):
        """Setting should be removed here, so they do not appear anymore
        when the plugin is unloaded.
        """
        AlgorithmProvider.unload(self)
        ProcessingConfig.removeSetting(
            QupiterProvider.MY_DUMMY_SETTING)

    def getName(self):
        """This is the name that will appear on the toolbox group.

        It is also used to create the command line name of all the
        algorithms from this provider.
        """
        return 'Qupiter'

    def getDescription(self):
        """This is the provider full name.
        """
        return 'Qupiter Query Engine'

    def getIcon(self):
        """Load jupiter icon.
        """
        iconpath = os.path.join(JupiterAux.pluginpath(), 'pix', 'jupiter.png')
        return QIcon(iconpath)

    def _loadAlgorithms(self):
        """Here we fill the list of algorithms in self.algs.

        This method is called whenever the list of algorithms should
        be updated. If the list of algorithms can change (for instance,
        if it contains algorithms from user-defined scripts and a new
        script might have been added), you should create the list again
        here.

        In this case, since the list is always the same, we assign from
        the pre-made list. This assignment has to be done in this method
        even if the list does not change, since the self.algs list is
        cleared before calling this method.
        """
        self.algs = self.alglist
