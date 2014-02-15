#!/usr/bin/env python

import string
import urllib2
import getopt
import sys


def usage():
    print """check_nginx is a Nagios to monitor nginx status
   Usage:

   check_nginx [-h|--help][-U|--url][-P|--path][-u|--user][-p|--passwd][-w|--warning][-c|--critical]

   Options:
          --help|-h)
            print check_nginx help.
          --url|-U)
            Sets nginx status url.
          --path|-P)
            Sets nginx status url path. Default is: off
          --user|-u)
            Sets nginx status BasicAuth user. Default is: off
          --passwd|-p)
            Sets nginx status BasicAuth passwd. Default is: off
          --warning|-w)
            Sets a warning level for nginx Active connections. Default is: off
          --critical|-c)
            Sets a critical level for nginx Active connections. Default is: off
    Example:
            The url is www.nginxs.com/status
            ./check_nginx -U www.nginxs.com -P /status -u eric -p nginx -w 1000 -c 2000
            if dont't have password:
            ./check_nginx -U www.nginxs.com -P /status -w 1000 -c 2000
            if don't have path and password:
            ./check_nginx -U www.nginxs.com -w 1000 -c 2000"""

    sys.exit(3)

try:
    options, args = getopt.getopt(sys.argv[1:], "hU:P:u:p:w:c:", ["help", "url=", "path=", "user=", "passwd=", "warning=", "critical="])

except getopt.GetoptError:
    usage()
    sys.exit(3)

for name,value in options:
    if name in ("-h","--help"):
        usage()
    if name in ("-U","--url"):
        url = "http://"+value
    if name in ("-P","--path"):
        path = value
    if name in ("-u","--user"):
        user = value
    if name in ("-p","--passwd"):
        passwd = value
    if name in ("-w","--warning"):
        warning = value
    if name in ("-c","--critical"):
        critical = value
try:
    if 'path' in dir():
        req = urllib2.Request(url+path)
    else:
        req = urllib2.Request(url)
    if 'user' in dir() and 'passwd' in dir():
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url+path, user, passwd)
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)
    response = urllib2.urlopen(req)
    the_page = response.readline()
    conn = the_page.split()
    ActiveConn = conn[2]
    the_page1 = response.readline()
    the_page2 = response.readline()
    the_page3 = response.readline()
    response.close()
    b = the_page3.split()
    reading = b[1]
    writing = b[3]
    waiting = b[5]
    output = 'ActiveConn:%s,reading:%s,writing:%s,waiting:%s' % (ActiveConn,reading,writing,waiting)
    perfdata = 'ActiveConn:%s,reading:%s,writing:%s,waiting:%s' % (ActiveConn,reading,writing,waiting)

except Exception:
    print "NGINX STATUS unknown: Error while getting Connection"
    sys.exit(3)
if 'warning' in dir() and 'critical' in dir():
    if ActiveConn >= warning:
        print 'WARNING - %s|%s' % (output,perfdata)
        sys.exit(2)
    elif ActiveConn >= critical:
        print 'CRITICAL - %s|%s' % (output,perfdata)
        sys.exit(1)
    else:
        print 'OK - %s|%s' % (output,perfdata)
        sys.exit(0)
else:
    print 'OK - %s|%s' % (output,perfdata)
    sys.exit(0)
