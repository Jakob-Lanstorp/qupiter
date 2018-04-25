# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Qjupiter
        A QGIS plugin Qupiter data plugin
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

from qgis.utils import iface
from qgis.core import (QgsGeometry,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsRectangle,
                       QgsDataSourceURI,
                       QgsVectorLayer,
                       QgsVectorFileWriter,
                       QgsMapLayerRegistry,
                       QgsProject,
                       QgsLayerTreeLayer,
                       QgsFeature,
                       QgsPoint)

from qgis.gui import QgsRubberBand, QgsVertexMarker
from PyQt4.QtGui import QColor

from PyQt4.QtCore import QSettings
import os

from jupiter_db import JupiterDb
from jupiter_aux import JupiterAux

from processing.tools.vector import ogrConnectionString, ogrLayerName
from processing.tools import dataobjects, vector


class JupiterQGIS:
    def __init__(self):
        pass

    def add_alphaview(self, progress, pglayername, output):
        """Load a non spatial table or view from postgresql - currently pesticide list
        :param progress: Information text and progress
        :param pglayername: Name of alpha view to load
        :param output: processing.core.outputs.OutputVector object
        :return: True if no error
        """
        db = JupiterDb()
        uri = db.getUri()
        uri.setDataSource("jupiter", pglayername, None)

        JupiterAux.log_info('Loading alphalayer: {} from URI'.format(pglayername), progress=progress)

        ok, pglayer = self.getQgsVectorLayerFromUri(uri, pglayername)
        if not ok:
            return False

        if not self.writeOutputVector(progress, pglayer, output, isSpatial=False):
            return False

        return True

    def make_dguno_spatial(self, progress, pglayername, layer, fieldname, output):
        """
        :param progress: Processing progressbar and info
        :param pglayername: PostgreSQL layer to load subset from
        :param layer: layer with dgunummer
        :param fieldname: field with dgunummer
        :param output: result output file
        :return: True if non error - else False
        """

        layerobj = dataobjects.getObjectFromUri(layer)

        dguno_list = [ft[fieldname] for ft in layerobj.getFeatures()]
        dguno_str = "'" + "', '".join(dguno_list) + "'"

        where_sql = 'boreholeno in ({})'.format(dguno_str)
        # JupiterAux.log_info('wheresql: {}'.format(where_sql))

        db = JupiterDb()

        # Find input boreholeno that have match in db
        str_no_match = ''
        list_no_boreholeno_match = db.boring_not_in_csv(dguno_str, dguno_list)
        if list_no_boreholeno_match:
            str_no_match = ''.join(list_no_boreholeno_match)
            # JupiterAux.msg_box(''.join(list_no_boreholeno_match))

        # Find input boreholeno that have duplicates
        import collections
        counter = collections.Counter(dguno_list)
        str_duplicates = ''
        if counter:
            d = dict((k, v) for k, v in counter.items() if v >= 2)
            import json
            str_duplicates = json.dumps(d)

        uri = db.getUri()
        uri.setDataSource("jupiter", pglayername, "geom", where_sql)

        ok, pglayer = self.getQgsVectorLayerFromUri(uri, pglayername)
        if not ok:
            return False

        if not self.writeOutputVector(progress, pglayer, output):
            return False

        #if not self.addStyle(pglayername, vlayer):
            #return False

        return True, str_no_match, str_duplicates

    def add_maplayer(self, progress, pglayername, output, extent, selectionLayername=None, rowid=None, where_sql2=None):
        """Adds a postgis layer to map
        :type progress: Processing progressbar and info
        :type pglayername: string name of pglayer to select from Jupiter
        :param output: processing.core.outputs.OutputVector object
        :type extent: Bounding box of query, if none use selected geom(s) as bound
        :type selectionLayername: string name of layer with selected geom to use as border in query
        :type rowid: needed for qgis to open views
        :where_sql: additional sql, not only bound search ... update doc

        WARNING: Do not use semicolon after where sql at uri.setDataSource
        """

        # import sys
        # sys.path.append(r'C:\Program Files\JetBrains\PyCharm 2017.2.3\debug-eggs\pycharm-debug.egg')
        # import pydevd
        # pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True)

        JupiterAux.log_info('add_maplayer: {}'.format(pglayername), progress)

        db = JupiterDb()
        uri = db.getUri()

        where_sql = ''
        # https://gis.stackexchange.com/questions/239601/sqlqueries-in-postgis-database-layer-using-python-and-qgis/239682#239682
        if extent == "0,0,0,0":
            ''' Query by geometry of selection in a layer '''

            wkt = self.selectedFeatureToWKT(selectionLayername)

            if not where_sql2:
                where_sql = "ST_WITHIN(geom , ST_GeomFromText('{}', 25832))".format(wkt)
            else:
                where_sql = "ST_WITHIN(geom , ST_GeomFromText('{}', 25832) ) AND {}".format(wkt, where_sql2)
        else:
            ''' Query by entered extent '''
            bbox = self.extentToBoundingbox(extent)

            if not where_sql2:
                where_sql = "geom && ST_MakeEnvelope({}, {}, {}, {}, 25832)". \
                    format(bbox.xMinimum(), bbox.yMinimum(), bbox.xMaximum(), bbox.yMaximum())
            else:
                where_sql = "geom && ST_MakeEnvelope({}, {}, {}, {}, 25832) AND {}" \
                    .format(bbox.xMinimum(), bbox.yMinimum(), bbox.xMaximum(), bbox.yMaximum(), where_sql2)

        uri.setDataSource("jupiter", pglayername, "geom", where_sql)

        JupiterAux.log_info('Loading layer: "{}" from URI with where clause: "{}"'.format(pglayername, where_sql2),
                            progress=progress)

        # Views must have defined a rowid
        if rowid:
            uri.setKeyColumn(rowid)

        ok, pglayer = self.getQgsVectorLayerFromUri(uri, pglayername)
        if not ok:
            return False

        if not self.writeOutputVector(progress, pglayer, output):
            return False

        #if not self.addStyle(pglayername, vlayer, uri):
            #return False

        # TODO  layer is not add to map until end of table_geoalgorithm.processAlgorithm
        # TODO  therefor is the showFeatureCount below not working
        # self.showFeatureCount(vlayer.name())

        return True


    def checkGeomTypeOfLayer(self, layername):
        layerObj = dataobjects.getObjectFromUri(layername)

        if layerObj.type() == QgsMapLayer.RasterLayer:
            raise Exception('Der skal være valgt et vektorlag og ikke et rasterlag')

        #geomType = layerObj.geometryType()
        geomTypeStr = QgsWKBTypes.displayString(int(layerObj.wkbType()))

        return geomTypeStr

    def countSelectedFeatures(self, layername):
        layerObj = dataobjects.getObjectFromUri(layername)

        return layerObj.selectedFeatureCount()

    def getQgsVectorLayerFromUri(self, uri, pglayername):
        """Get QgsVectorLayer from URI
        :param uri: URI to get layer from
        :param pglayername: name of new layer
        :return:
        """
        pglayer = QgsVectorLayer(uri.uri(), pglayername, "postgres")

        if not pglayer.isValid():
            # A default next val sequence and reader and writer grants must be set
            JupiterAux.log_error('MST-layer: "{}" is not valid!'.format(pglayername))

            return False, None

        return True, pglayer

    def writeOutputVector(self, progress, pglayer, output, isSpatial=True):
        """Write output
        :param pglayer: quried pg layer qgsvectorlayer to be written
        :param output: output processing object
        :param isSpatial: non spatial loads explictly
        :return: True if no error
        """
        JupiterAux.log_info('writing output vector: {}'.format(output.value))

        #error = QgsVectorFileWriter.writeAsVectorFormat(vlayer, outputfile, "utf-8", None, "ESRI Shapefile")
        #error = QgsVectorFileWriter.writeAsVectorFormat(vlayer, outputfile, "utf-8", None)

        output_writer = output.getVectorWriter(
            pglayer.fields(),
            pglayer.wkbType(),
            pglayer.crs()
        )

        outFeat = QgsFeature()
        features = vector.features(pglayer)
        total = 100.0 / len(features) if len(features) > 0 else 1
        for current, feat in enumerate(features):
            progress.setPercentage(int(current * total))

            if isSpatial:
                geom = feat.geometry()
                outFeat.setGeometry(geom)

            atMap = feat.attributes()
            atMap.append(None)
            outFeat.setAttributes(atMap)
            output_writer.addFeature(outFeat)

        del output_writer

        return True

        #if error == QgsVectorFileWriter.NoError:
        #    JupiterAux.log_info('QgsVectorFileWriter.NoError')
        #    if not isSpatial:
        #        QgsMapLayerRegistry.instance().addMapLayer(vlayer, True)
        #    return True
        #else:
        #    JupiterAux.log_info('Error writing {}'.format(output), progress=progress)
        #    return False

    def addStyle(self, pglayername, vlayer, uri):
        """Add style to layer. Assumes tablename if stylename
        :param pglayername: layer to query for in public.layer_styles
        :param vlayer: layer to apply style for
        :return: True if no error
        """

        qmlfile = os.path.join(JupiterAux.pluginpath(), 'style', 'borehole.qml')
        msg, styleloaded = vlayer.loadNamedStyle(qmlfile, True)
        iface.mapCanvas().refresh()
        iface.legendInterface().refreshLayerSymbology(vlayer)
        vlayer.triggerRepaint()

        return True

        JupiterAux.log_info(u'Loading default style from db...')
        db = JupiterDb()
        styleqml = db.get_style(pglayername)

        if styleqml:
            #vlayer.applyNamedStyle(pglayername)
            styleok = vlayer.loadNamedStyle(styleqml, True)
            iface.mapCanvas().refresh()
            iface.legendInterface().refreshLayerSymbology(vlayer)
            vlayer.triggerRepaint()
            JupiterAux.log_info(u'Style applied to: {}'.format(pglayername))
        else:
            JupiterAux.log_info(u'Table {} has no default style in db'.format(pglayername))

        return True

    def showFeatureCount(self, layername, show=True):
        """Set the feature count. TODO not working ...
        :param layername: layer to set style for
        :param show: toggle visibility
        :return: True if no error
        """
        root = QgsProject.instance().layerTreeRoot()
        for child in root.children():
            if isinstance(child, QgsLayerTreeLayer):
                JupiterAux.log_info('----- {}'.format(child.layerName()))
                if child.layerName() == layername:
                    child.setCustomProperty("showFeatureCount", show)

    def selectedFeatureToWKT(self, layername, only_allow_one_selected_feature=True):
        """
        Returns wkt geom of just one selected feature
        :param layer: Layer with just one selection
        """
        if only_allow_one_selected_feature:
            if self.countSelectedFeatures(layername) != 1:
                JupiterAux.msg_box(u'Der understøttes kun een valgt feature som forespørgelsesafgrænsning!')
                return None

            layerObj = dataobjects.getObjectFromUri(layername)

            #return layerObj.selectedFeatures()[0].geometry().exportToWkt() #? crashes qgis with a pure virtual call

            fts = layerObj.selectedFeatures()
            ft = fts[0]
            g = ft.geometry()
            wkt = g.exportToWkt()

            return wkt
        else:
            JupiterAux.msg_box(u'Der understøttes kun een valgt feature som forespørgelsesafgrænsning!')
            return None

    def extentToBoundingbox(self, extent):
        """Converts a qgis-processing four coordinate string to a QgsBoundingBox
        :param extent: string of extent. Example: '637334.021629,647399.593975,6080913.41663,6086353.10892'
        :return: QgsBoundingBox
        """
        extentarr = [float(i) for i in extent.split(',')]

        # noinspection PyCallByClass
        geometry_extent = QgsGeometry.fromRect(QgsRectangle(extentarr[0], extentarr[2], extentarr[1], extentarr[3]))
        source_crs = iface.mapCanvas().mapRenderer().destinationCrs()
        crs_transform = QgsCoordinateTransform(source_crs, QgsCoordinateReferenceSystem("EPSG:25832"))
        geometry_extent.transform(crs_transform)
        bbox = geometry_extent.boundingBox()
        return bbox

    def get_selected_boreholeno(self, borehole_table, borehole_field):
        """ Get comma separated string of boreholenum from selected geometries
        of borehole_table with column borehole_field """
        layer = dataobjects.getObjectFromUri(borehole_table)

        if layer.selectedFeatureCount() == 0:
            return None

        boreholes = []
        for ft in layer.selectedFeatures():
            boreholes.append(ft[borehole_field])

        return ','.join(boreholes)

    def remove_canvas_items(self, vertexmarker=True, rubberband=False):
        """ Clear any existing vertex markers """
        canvas_items = []
        if vertexmarker:
            canvas_items = [i for i in iface.mapCanvas().scene().items() if issubclass(type(i), QgsVertexMarker)]

        if rubberband:
            canvas_items += [i for i in iface.mapCanvas().scene().items() if issubclass(type(i), QgsRubberBand)]

        for ver in canvas_items:
            if ver in iface.mapCanvas().scene().items():
                iface.mapCanvas().scene().removeItem(ver)

    def add_rubberband_to_feature(self):
        """ Add a rubberband to all features of active layer """
        rbDict = {}  # We need this to store the rbs we'll create
        layer = iface.activeLayer()

        # Create rubber bands
        for f in layer.getFeatures():
            fId = f.id()
            rbDict[fId] = QgsRubberBand(iface.mapCanvas(), True)
            rbDict[fId].setColor(QColor(0, 255, 0, 255))
            rbDict[fId].setWidth(2)
            rbDict[fId].addGeometry(f.geometry(), None)

    def add_rubberband_borehole(self, boreholeno):
        """ Warning - this method fails silently on error """
        self.remove_canvas_vertexmarkers()

        # Add new rubberband
        points = [[QgsPoint(6640629.039, 6087146.608), QgsPoint(640629.039, 6087146.608), QgsPoint(640629.039, 6087146.608), QgsPoint(6640629.039, 6087146.608)]]  # lower left, upper right
        r = QgsRubberBand(iface.mapCanvas, True)  # True = a polygon
        r.setColor(QColor(0, 255, 0, 255))
        r.setWidth(3)
        r.setToGeometry(QgsGeometry.fromPolygon(points), None)

        JupiterAux.log_info(u'rubberband added for borehole {}'.format(boreholeno))

    def add_vertexmarker_borehole(self, boreholeno, keepExistingMarkers=False):
        """ Warning - this method fails silently on error """
        if not keepExistingMarkers:
            self.remove_canvas_items()

        db = JupiterDb()
        x, y = db.get_xy(boreholeno)

        #JupiterAux.msg_box('x,y = {}, {}'.format(x, y))

        # Add new vertexmarker
        vm = QgsVertexMarker(iface.mapCanvas())
        vm.setCenter(QgsPoint(x, y))
        vm.setColor(QColor(0, 255, 0, 255))
        vm.setIconSize(30)
        vm.setIconType(QgsVertexMarker.ICON_CROSS)  # ICON_BOX, ICON_CROSS, ICON_X
        vm.setPenWidth(2)

        #JupiterAux.log_info(u'Vertexmarker added for borehole {}'.format(boreholeno))
