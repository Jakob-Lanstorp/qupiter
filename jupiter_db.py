# -*- coding: utf-8 -*-
"""
    Jupiter db access layer class
    Jakob Lanstorp, MST 14-09-2017

    NOTE:
        -QGIS crashes hard on any db error
        -It is JupiterDb responsibility to quote strings
        -Always encapsulate sql in double quotes "", since single quotes '' are reserved for add string params to sql
"""

import psycopg2
import psycopg2.extras
import sys
import time
from jupiter_aux import *
import base64

from qgis.core import QgsDataSourceURI


class JupiterDb(object):
    """  Provides database access via psycopy2 and  QgsDataSourceURI """

    CURRENT_SCHEMA = 'jupiter'

    def __init__(self):
        pass

    def getUri(self):
        """ Prepare connection to database """
        params = self.get_dbparams()
        uri = QgsDataSourceURI()
        uri.setConnection(params['host'], str(params['port']), params['dbname'], params['user'], params['password'])
        return uri

    def test_connection(self):
        """ Test database connection """
        conn = None
        try:
            conn = psycopg2.connect(**self.get_dbparams())
            conn.close()
            return True
        except:
            return False
        finally:
            if conn:
                conn.close()

    def get_version(self):
        """ Get version of PostgreSQL"""
        sql = 'SELECT Version()'

        cur = self.execute_sql(sql, dict_cursor=False)
        row_tuple = cur.fetchone()
        ver = row_tuple[0]
        return ver

    def execute_sql(self, sql, data=None, dict_cursor=True, print_sql=False):
        """ Execute a SQL query
        :param sql: SQL to be executed
        :param data: Data to query in where clause
        :param dict_cursor: Flag indicating if cursor is a dict or not. Use false for scalar queries
        :param print_sql: Flag indicating if sql is to be printet
        :return: returns a cursor
        """

        if print_sql: print sql
        database = psycopg2.connect(**self.get_dbparams())

        if dict_cursor:
            cur = database.cursor(cursor_factory=psycopg2.extras.DictCursor)
        else:
            cur = database.cursor()

        try:
            if data == None:
                cur.execute(sql)
            else:
                cur.execute(sql, data)

            return cur

            #cur.close()
            #database.close()

        except psycopg2.DatabaseError, e:
            JupiterAux.log_error('psycopg2.DatabaseError jalan error {}'.format(e))
            sys.exit(1)
        finally:
            pass
            # TODO
            # if conn:
            #    conn.close()

    def mogrify(self, sql, dict_cursor=True):
        """ Test how psycopg2 renderes the sql before sending it to the database a SQL query
        :param sql: SQL to be testet
        :param dict_cursor: Flag indicating if cursor is a dict or not. Use false for scalar queries
        :return: returns checked sql string
        """

        conn = psycopg2.connect(**self.get_dbparams())

        if dict_cursor:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        else:
            cur = conn.cursor()

        try:
            check_sql = cur.mogrify(sql)
            return check_sql
        except psycopg2.DatabaseError, e:
            print 'MST DB Error {}'.format(e)
            GrukosAux.log_error('MST DB Error {}'.format(e))
            sys.exit(1)
        finally:
            pass
            if conn:
                conn.close()

    def get_compound(self, compondType, wkt, dateFrom=None, dateTo=None, dateLatest=None):
        """
        :param compondType:
        :param wkt:
        :param dateFrom:
        :param dateTo:
        :param dateLatest:
        """
        pass

    def boring_not_in_csv(self, dguno_str, dguno_arr):
        """
        :param dguno_str: '167.  511, 168.  299, 168.  376'
        :param dguno_arr: [u'167.  511', u'168.  299', u'168.  376']
        :return: boreholeno not found in borehole table
        """
        sql = 'SELECt boreholeno from {}.borehole WHERE boreholeno in ({});'.format(self.CURRENT_SCHEMA, dguno_str)

        dictcur = self.execute_sql(sql)
        rows_list = dictcur.fetchall()

        if not rows_list:
            return None

        # boreholes found
        list_boreholes = []
        for row in rows_list:
            boreholeno = str(row['boreholeno'])
            list_boreholes.append(boreholeno)

        dictcur.close()

        # boreholes not found
        list_boreholes_not_found = [b for b in dguno_arr if b not in list_boreholes]

        #JupiterAux.msg_box('len(dguno_arr): {}'.format(len(dguno_arr)))
        #JupiterAux.msg_box('len(rows_list): {}'.format(len(rows_list)))
        #JupiterAux.msg_box('len(list_boreholes_not_found): {}'.format(len(list_boreholes_not_found)))

        return list_boreholes_not_found

    def get_style(self, style_name):
        sql = "SELECT styleqml FROM public.layer_styles WHERE stylename = '{}';".format(style_name)

        #JupiterAux.enable_qgis_log(haltApp=True)

        cur = self.execute_sql(sql)
        dictrow = cur.fetchone()  # type DictRow

        return unicode(dictrow[0])

    def get_unit(self, sampleid, compound_name):
        sql = "SELECT unit FROM {}.mst_compoundname_to_unit({}, '{}');".format(self.CURRENT_SCHEMA, sampleid, compound_name)

        #JupiterAux.enable_qgis_log(haltApp=True)

        dictcur = self.execute_sql(sql)

        rec = dictcur.fetchone()

        if not rec:
            return None

        unit = rec['unit']
        dictcur.close()

        return unit

    def get_unit_quess(self, compound_no):
        """
        Return the unit that is used the most for a compound
        :param compound_no:
        :return:
        """

        sql = """
                SELECT
                  c.longtext, count(*) AS count_units
                FROM
                  jupiter.grwchemanalysis gca
                INNER JOIN jupiter.code c ON c.code::NUMERIC = gca.unit AND c.codetype = 752
                WHERE gca.compoundno = {}
                GROUP BY c.longtext
                ORDER BY count_units DESC
                LIMIT 1;
      """.format(compound_no)

        #JupiterAux.enable_qgis_log(haltApp=True)

        dictcur = self.execute_sql(sql, dict_cursor=True)

        rec = dictcur.fetchone()

        if not rec:
            return None

        dictcur.close()

        return rec['longtext']

    def count_compound_units(self, compound_name):
        """ Returns count of unit and unit for a given compound"""
        sql = "SELECT antal, unit FROM {}.mst_count_compound_units('{}');".format(self.CURRENT_SCHEMA, compound_name)

        #JupiterAux.enable_qgis_log(haltApp=True)

        dictcur = self.execute_sql(sql)
        rows_list = dictcur.fetchall()

        if not rows_list:
            return None

        list_of_tuples = []
        for row in rows_list:
            count = int(row['antal'])
            unit = str(row['unit']).encode('utf-8')

            list_of_tuples.append((count, unit))

        dictcur.close()

        return list_of_tuples


    def compoundname_to_no(self, compound_name):
        sql = "SELECT {}.mst_compoundname_to_no('{}');".format(self.CURRENT_SCHEMA, compound_name)

        #JupiterAux.enable_qgis_log(haltApp=True)

        dictcur = self.execute_sql(sql)
        rec = dictcur.fetchone()

        if not rec:
            return None

        compoundno = rec[0]
        dictcur.close()

        return compoundno


    def compoundno_to_name(self, compound_id):
        sql = "SELECT {}.mst_compoundno_to_name({});".format(self.CURRENT_SCHEMA, compound_id)

        #JupiterAux.enable_qgis_log(haltApp=True)

        dictcur = self.execute_sql(sql)

        rec = dictcur.fetchone()

        if not rec:
            return None

        compoundname = rec[0]
        dictcur.close()

        return compoundname


    def database_youngest_insert_in_days(self):
        '''
        :return: age in days since youngest sample inserted in database
        '''
        sql = "SELECT {}.db_age_in_days();".format(self.CURRENT_SCHEMA)

        #JupiterAux.enable_qgis_log(haltApp=True)

        dictcur = self.execute_sql(sql)
        rec = dictcur.fetchone()

        if not rec:
            return None

        days = rec[0]
        dictcur.close()

        return days


    def database_geus_export_time_in_days(self):
        '''
        :return: age in days since complete database export from geus
        '''
        sql = "SELECT extract(days from now() - exporttime) AS dage FROM {}.exporttime;".format(self.CURRENT_SCHEMA)

        #JupiterAux.enable_qgis_log(haltApp=True)

        dictcur = self.execute_sql(sql)
        rec = dictcur.fetchone()

        if not rec:
            return None

        days = rec[0]
        dictcur.close()

        return days


    def database_dbsync_success_in_days(self):
        '''
        :return: age in days of last succesfull dbsync run
        '''
        #sql = "SELECT extract(days from now() - endtime) AS dage FROM {}.synchronizationlog WHERE success = TRUE ORDER BY endtime DESC LIMIT 1;".format(self.CURRENT_SCHEMA)

        sql = """
          SELECT 
            extract(days from now() - endtime) AS dage 
          FROM 
            {}.synchronizationlog 
          WHERE success = TRUE 
          ORDER BY endtime DESC 
          LIMIT 1;
        """

        sql = sql.format(self.CURRENT_SCHEMA)

        #JupiterAux.enable_qgis_log(haltApp=True)

        dictcur = self.execute_sql(sql)
        rec = dictcur.fetchone()

        if not rec:
            return None

        days = rec[0]
        dictcur.close()

        return days


    def get_timeserie(self, boreholeno, compound, datefrom=None, dateto=None):
        """  TODO: move function to plpgsql - currrently hardcoded schema
            Intake query is disabled - all intake used
        """
        from datetime import datetime

        input_data = (
            compound,
            boreholeno,
            datetime.strptime(datefrom, '%Y-%m-%d'),
            datetime.strptime(dateto, '%Y-%m-%d')
        )

        sql = """
            SELECT
              ca.amount,
              cs.sampledate
            FROM jupiter.borehole b
            INNER JOIN jupiter.grwchemsample cs USING (boreholeno)
            INNER JOIN jupiter.grwchemanalysis ca ON ca.sampleid = cs.sampleid
            INNER JOIN jupiter.compoundlist cl ON ca.compoundno = cl.compoundno
            WHERE cl.long_text ilike %s AND 
                  b.boreholeno = %s AND 
                  cs.sampledate >= %s AND 
                  cs.sampledate <= %s 
            ORDER BY cs.sampledate;
        """

        cur = self.execute_sql(sql, data=input_data, dict_cursor=False)
        result_data = cur.fetchall()
        cur.close()

        if (len(result_data)) > 0:
            amount, dt = zip(*result_data)
            return amount, dt

        return None, None

    def get_scatter_array_bbox(self, compoundno_x, compoundno_y, bbox, datefrom, dateto, compoundname_x, compoundname_y):
        """
        :param compoundno_x: Compound number for x-ax
        :param compoundno_y: Compound number for y-ax
        :param bbox: QGIS boundingbox for query boreholes
        :param datefrom: extract data from this date
        :param dateto: extract data to this date
        :return: tuple of two arrays with analysis amount of the two quried compounds
        """
        from datetime import datetime

        data_arg = {
            'cmpno_x': compoundno_x,
            'cmpno_y': compoundno_y,
            'cmpname_x': compoundname_x,
            'cmpname_y': compoundname_y,
            'datefrom': datetime.strptime(datefrom, '%Y-%m-%d'),
            'dateto': datetime.strptime(dateto, '%Y-%m-%d'),
            'xmin': bbox.xMinimum(),
            'ymin': bbox.yMinimum(),
            'xmax': bbox.xMaximum(),
            'ymax': bbox.yMaximum()
        }

        sql = """
            WITH compound1 AS (
                SELECT
                  boreholeno,
                  sampleid, 
                  amount
                FROM jupiter.mstmvw_bulk_grwchem_alldates
                WHERE compoundno = %(cmpno_x)s AND 
                      sampledate >= %(datefrom)s AND sampledate <= %(dateto)s AND 
                      geom && ST_MakeEnvelope(%(xmin)s, %(ymin)s, %(xmax)s, %(ymax)s, 25832)
            ),
            compound2 AS (
                SELECT
                  sampleid, 
                  amount
                FROM jupiter.mstmvw_bulk_grwchem_alldates
                WHERE compoundno = %(cmpno_y)s AND 
                      sampledate >= %(datefrom)s AND sampledate <= %(dateto)s AND 
                      geom && ST_MakeEnvelope(%(xmin)s, %(ymin)s, %(xmax)s, %(ymax)s, 25832)            
            )
            SELECT 
              c1.boreholeno,
              c1.amount AS {},
              c2.amount AS {}
            FROM compound1 c1
            INNER JOIN compound2 c2 USING (sampleid) 
        """.format(compoundname_x, compoundname_y)

        cur = self.execute_sql(sql, data=data_arg, dict_cursor=False)
        data_result = cur.fetchall()
        cur.close()

        if (len(data_result)) > 0:
            boreholeno, x, y = zip(*data_result)  # zip list of record tuples to three single arrays
            return x, y, boreholeno  # array of sodium, array of sulphor, array of boreholeno

        return None, None, None

    def get_scatter_array_wkt(self, compoundno_x, compoundno_y, wkt, datefrom, dateto, compoundname_x, compoundname_y):
        """
        :param compoundno_x: Compound number for x-ax
        :param compoundno_y: Compound number for y-ax
        :param wkt: WKT geometry for query boreholes
        :param datefrom: extract data from this date
        :param dateto: extract data to this date
        :return: tuple of two arrays with analysis amount of the two quried compounds
        """
        from datetime import datetime

        data_arg = {
            'cmpno_x': compoundno_x,
            'cmpno_y': compoundno_y,
            'cmpname_x': compoundname_x,
            'cmpname_y': compoundname_y,
            'datefrom': datetime.strptime(datefrom, '%Y-%m-%d'),
            'dateto': datetime.strptime(dateto, '%Y-%m-%d'),
            'wkt': wkt
        }
        # where_sql = "ST_WITHIN(geom , ST_GeomFromText('{}', 25832))".format(wkt)

        sql = """
            WITH compound1 AS (
                SELECT
                  boreholeno,
                  sampleid, 
                  amount
                FROM jupiter.mstmvw_bulk_grwchem_alldates
                WHERE compoundno = %(cmpno_x)s AND 
                      sampledate >= %(datefrom)s AND sampledate <= %(dateto)s AND 
                      ST_WITHIN(geom , ST_GeomFromText(%(wkt)s, 25832))
            ),
            compound2 AS (
                SELECT
                  sampleid, 
                  amount
                FROM jupiter.mstmvw_bulk_grwchem_alldates
                WHERE compoundno = %(cmpno_y)s AND 
                      sampledate >= %(datefrom)s AND sampledate <= %(dateto)s AND 
                      ST_WITHIN(geom , ST_GeomFromText(%(wkt)s, 25832))            
            )
            SELECT 
              c1.boreholeno,
              c1.amount AS {},
              c2.amount AS {}
            FROM compound1 c1
            INNER JOIN compound2 c2 USING (sampleid) 
        """.format(compoundname_x, compoundname_y)

        cur = self.execute_sql(sql, data=data_arg, dict_cursor=False)
        data_result = cur.fetchall()
        cur.close()

        if (len(data_result)) > 0:
            boreholeno, x, y = zip(*data_result)
            return x, y, boreholeno  # array of sodium, array of sulphor

        return None, None, None


    def get_xy(self, boreholeno):
        sql = """
            SELECT
              ST_X(geom) AS x,
              ST_Y(geom) AS y
            FROM jupiter.borehole
            WHERE boreholeno = '{}'
        """.format(boreholeno)

        cur = self.execute_sql(sql)
        row = cur.fetchone()

        cur.close()

        if row:
            x = row['x']
            y = row['y']
            return x, y

        return None, None

    def get_dbparams(self):
        # Get db connections params #
        return {'host': 'localhost', 'port': 5432, 'dbname': 'pcjupiterxl', 'user': 'jupiter_user', 'password': 'jupiter_user'}

    '''
    def get_dbparams(self):
        # Get db connections params #
        # Use this for multiple user support and log access for personal queries #

        import getpass

        bno = getpass.getuser().upper()

        dict_user = {
            'B020574': {'host': 'localhost', 'port': 5432, 'dbname': 'pcjupiterxl', 'user': 'jupiter_jalan', 'password': 'bfa4e464-0e8e-43f8-a982-f3456e954c90'},
            'B006303': {'host': 'C1400020', 'port': 5432, 'dbname': 'pcjupiterxl', 'user': 'jupiter_trini', 'password': '55b553d5-a22b-4417-974f-a80bb680cf4a'},
            'B028026': {'host': 'C1400020', 'port': 5432, 'dbname': 'pcjupiterxl', 'user': 'jupiter_nalje', 'password': '9a0f5cc3-a8cb-41b0-b2b3-35d32c607988'},
            'B005556': {'host': 'C1400020', 'port': 5432, 'dbname': 'pcjupiterxl', 'user': 'jupiter_jehan', 'password': 'b4c83817-799d-492c-bbb4-57e7320ede6f'},
            'B006337': {'host': 'C1400020', 'port': 5432, 'dbname': 'pcjupiterxl', 'user': 'jupiter_zicos', 'password': '2f8a47e6-5e3c-479e-b8ac-8f65ef5b9786'},
            'B005625': {'host': 'C1400020', 'port': 5432, 'dbname': 'pcjupiterxl', 'user': 'jupiter_josiv', 'password': '66fc890f-8b68-469c-bb4a-cfa936f60987'}
        }

        credentials = dict_user[bno]

        if credentials == None:
            JupiterAux.msg_box(u'{} er ikke bruger på Qupiter. Kontakt jalan@mst.dk for oprettelse'.format(bno))
            return None
        else:
           return credentials
    '''