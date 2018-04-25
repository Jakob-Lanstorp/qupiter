# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Qupiter
        A QGIS processing plugin for GEUS Jupiter well database
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
 This script initializes the plugin, making it known to QGIS.
"""

__author__ = 'Miljøstyrelsen'
__date__ = '2017-03-14'
__copyright__ = '(C) 2017 by Miljøstyrelsen'


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load PCJupiterXL class from file PCJupiterXL.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .qupiter import QupiterPlugin
    return QupiterPlugin()
