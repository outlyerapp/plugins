#!/opt/dataloop/embedded/bin/python

import os
import sys
from StringIO import StringIO

#####################
# SCRIPT PARAMETERS #
#####################

# The SQL query you want to run. It should return two columns:
# a string and a number. The string will be used as the metric
# name. 
#
# For example, the query "select ename, sal from scott.emp"
# will create metrics like this:
#
#       oracle_query.salary.SMITH = 800
#       oracle_query.salary.JONES = 2975
# etc.
#
SQL = """
    select ename, sal from scott.emp
"""

# Details of your Oracle installation
#
ORACLE_HOME = "/u01/app/oracle/product/11.2.0/dbhome_1"
ORACLE_USER = "scott"
ORACLE_PASSWORD = "tiger"
ORACLE_HOST = "localhost"
ORACLE_PORT = 1521
ORACLE_SID = "ORCL"

# Additional prefix to add to metric names. The generated metrics
# will be named like "oracle_query.PREFIX.name = value".
#
PREFIX="salary"


##################################
# DO NOT CHANGE BELOW THIS POINT #
##################################

if 'ORACLE_HOME' not in os.environ:
    os.environ['ORACLE_HOME'] = ORACLE_HOME
    os.environ['LD_LIBRARY_PATH'] = ORACLE_HOME + '/lib'
    try:
        os.execv(sys.argv[0], sys.argv)
    except Exception, exc:
        print 'Failed re-exec:', exc
        sys.exit(1)

try:
    import cx_Oracle

    dsn = cx_Oracle.makedsn(ORACLE_HOST, ORACLE_PORT, ORACLE_SID)
    con = cx_Oracle.connect('{user}/{password}@{dsn}'.format(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=dsn))

    cur = con.cursor()
    cur.execute(SQL)

    buf = StringIO()
    for result in cur:
        buf.write("{prefix}.{name}={value};;;; ".format(prefix=PREFIX, name=result[0], value=result[1]))

    cur.close()
    con.close()

    print 'OK | ' + buf.getvalue()
    sys.exit(0)

except ImportError as ex:
    print 'CRITICAL | Unable to import cx_Oracle: ' + str(ex)
    
except cx_Oracle.DatabaseError as ex:
    print 'CRITICAL | Oracle database error: ' + str(ex.message)
    sys.exit(2)

