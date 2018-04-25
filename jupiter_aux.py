# -*- coding: utf-8 -*-
"""
***************************************************************************
 Jupiter general auxillary methods
***************************************************************************
"""
from qgis.core import QgsMessageLog
from qgis.utils import iface
from PyQt4 import QtGui

import ConfigParser
import os

import sys
reload(sys)
sys.setdefaultencoding('utf8')

class JupiterAux(object):
    JUPITER = 'Qupiter'

    @staticmethod
    def startdebugging():
        #import sys
        #sys.path.append(r'C:\Program Files\JetBrains\PyCharm 2017.2.3\debug-eggs\pycharm-debug.egg')
        #import pydevd
        #pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True)
        pass


    @staticmethod
    def pluginpath():
        return os.path.dirname(os.path.realpath(__file__))

    @staticmethod
    def showLogMessagePanel():
        from PyQt4.QtGui import QDockWidget
        log = iface.mainWindow().findChild(QDockWidget, "MessageLog")
        log.setVisible(True)  # log.show()

    @staticmethod
    def get_meta_name():
        config = ConfigParser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__),'metadata.txt'))

        name = str(config.get('general', 'name'))
        #GrukosAux.log_info('{}'.format(name))

        return name

    @staticmethod
    def get_meta_version():
        config = ConfigParser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'metadata.txt'))

        version = str(config.get('general', 'version'))
        return version

    @staticmethod
    def log_info(msg, progress=None, bold=False, popup=False):

        str_msg = str(msg).encode('cp1252')
        QgsMessageLog.logMessage(str_msg, JupiterAux.JUPITER, 0)
        if progress and bold:
            progress.setInfo(u'<br><b>{}</b><br>'.format(str_msg))
        if progress and not bold:
            progress.setInfo(u'{}'.format(str_msg))
        if popup:
            JupiterAux.msg_box(msg)

    @staticmethod
    def log_warning(msg):
        str_msg = str(msg).encode('cp1252')
        QgsMessageLog.logMessage(str_msg, JupiterAux.JUPITER, 1)

    @staticmethod
    def log_error(msg, progress=None, bold=False, popup=False):
        str_msg = str(msg).encode('cp1252')
        QgsMessageLog.logMessage(str_msg, JupiterAux.JUPITER, 2)

        if progress and bold:
            progress.setInfo(u'<br><b>{}</b><br>'.format(str_msg))
        if progress and not bold:
            progress.setInfo(u'{}'.format(str_msg))
        if popup:
            JupiterAux.msg_box(msg)

        JupiterAux.showLogMessagePanel()

    @staticmethod
    def msg_box(msg):
        QtGui.QMessageBox.information(
            None,
            JupiterAux.JUPITER,
            "{}".format(msg.encode('cp1252')),
            QtGui.QMessageBox.Ok)

    @staticmethod
    def msg_box_yes_no(msg):
        reply = QtGui.QMessageBox.question(None,
                                           'Vælg'.encode('cp1252'),
                                           "{}".format(msg.encode('cp1252')),
                                       QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
        if reply == QtGui.QMessageBox.Yes:
            return True
        else:
            return False

    @staticmethod
    def enable_qgis_log(filename='C:\Temp\gqis_jupiter.log', haltApp = False, haltMsg = 'stop'):
        """ Very useful when QGIS crashes on PGSQL error
        :param filename: Filename and path for log file
        :param haltApp: Halts the application with a modal dialog
        :param haltMsg: Message to user when showing model stopping dialog
        :rtype: None
        """
        def write_log_message(message, tag, level):
            with open(filename, 'a') as logfile:
                logfile.write('{tag}({level}): {message}'.format(tag=tag, level=level, message=message))

        QgsMessageLog.instance().messageReceived.connect(write_log_message)

        if haltApp:
            QtGui.QMessageBox.information(None, JupiterAux.JUPITER, "{}".format(haltMsg.encode('cp1252')), QtGui.QMessageBox.Ok)
