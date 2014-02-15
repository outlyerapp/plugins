#!/usr/bin/env python
import sys
import urllib
from optparse import OptionParser, OptionGroup

"""
This plugin expects the apache status page to be available on /server-status?auto
To enable simply add this block to your httpd.conf:

  <Location /server-status>
  SetHandler server-status
  </Location>

For more info including how to make that more secure visit http://httpd.apache.org/docs/2.2/mod/mod_status.html
"""

OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

usage = "Usage: %prog -H HOSTNAME -p PORT [-w] [-c]"
parser = OptionParser(usage, version="%prog 1.0")
parser.add_option("-H", "--hostname", type="string", dest="hostname", default="localhost",
                  help="You may define a hostname with the -H option. Default is: localhost.")
parser.add_option("-p", "--port", type="int", dest="port", default=80,
                  help="You may define a port with the -p option. Default is: 80.")
group = OptionGroup(parser, "Warning/critical thresholds",
                    "Use these options to set warning/critical thresholds for requests per second served by your Apache.")
group.add_option("-w", "--warning", type="int", dest="warning", default=-2,
                 help="Use this option if you want to use warning/critical thresholds. Make sure to set a critical value \
                   as well. Default is: -1.")
group.add_option("-c", "--critical", type="int", dest="critical", default=-1,
                 help="Use this option if you want to use warning/critical thresholds. Make sure to set a warning value as \
                  well. Default is: -2.")
parser.add_option_group(group)

(options, args) = parser.parse_args()

hostname = options.hostname
port = options.port
warning = options.warning
critical = options.critical


def end(status, message):
    """Exits the script with the first argument as the return code and the
       second as the message to generate output."""
    if status == OK:
        print "OK | %s" % message
        sys.exit(0)
    elif status == WARNING:
        print "WARNING | %s" % message
        sys.exit(1)
    elif status == CRITICAL:
        print "CRITICAL | %s" % message
        sys.exit(2)
    else:
        print "UNKNOWN | %s" % message
        sys.exit(3)


def validate_thresholds(warning, critical):
    """Validates warning and critical thresholds in several ways."""
    if critical != -1 and warning == -2:
        end(UNKNOWN, "Please also set a warning value when using warning critical thresholds!")
    if critical == -1 and warning != -2:
        end(UNKNOWN, "Please also set a critical value when using warning critical thresholds!")
    if critical <= warning:
        end(UNKNOWN, "When using thresholds the critical value has to be higher than the warning value. Please adjust your thresholds.")


def retrieve_status_page():
    """Gets the server's status page and raises an exception if it's not
       accessible."""

    statusPage = "http://%s:%s/server-status?auto" % (hostname, port)
    try:
        retrPage = urllib.urlretrieve(statusPage, '/tmp/server-status.log')
    except:
        end(CRITICAL, "Couldn't fetch the server's status page. Please " +
                      "check given hostname, port or Apache's " +
                      "configuration. We might not be allowed to access " +
                      "server-status due to your server's configuration.")


def parse_status_page():
    """Main parsing function to put the server-status file's content into
       a dictionary."""

    file = open('/tmp/server-status.log', 'r')
    line = file.readline()
    dictStatus = {}
    counter = 1

    while line:
        if "Total Accesses:" in line:
            key = "totalAcc"
        elif "Total kBytes:" in line:
            key = "totalKb"
        elif "Uptime:" in line:
            key = "uptime"
        elif "ReqPerSec:" in line:
            key = "reqPSec"
        elif "BytesPerSec:" in line:
            key = "bytesPSec"
        elif "BytesPerReq:" in line:
            key = "bytesPReq"
        elif "BusyWorkers:" in line:
            key = "busyWkrs"
        elif "IdleWorkers:" in line:
            key = "idleWkrs"
        else:
            key = str(counter)

        line = line.strip()
        dictStatus[key] = line
        counter = counter + 1
        line = file.readline()

    return dictStatus


def transform_dict(resParse):
    """Transforms the dictionary to a list and converts variables to proper
       types."""

    totalAcc = int(resParse['totalAcc'].strip(" Total Accesses:"))
    totalKb = float(resParse['totalKb'].strip(" Total kBytes:"))
    uptime = int(resParse['uptime'].strip(" Uptime:"))
    reqPSec = float(resParse['reqPSec'].strip(" ReqPerSec:")) + 0
    bytesPSec = float(resParse['bytesPSec'].strip(" BytesPerSec:"))
    if resParse.has_key('bytesPReq'):
        bytesPReq = float(resParse['bytesPReq'].strip(" BytesPerReq:"))

    busyWkrs = int(resParse['busyWkrs'].strip(" BusyWorkers:"))
    idleWkrs = int(resParse['idleWkrs'].strip(" IdleWorkers:"))

    return [reqPSec, busyWkrs, idleWkrs]


if critical != -1 or warning != -2:
    validate_thresholds(warning, critical)

retrieve_status_page()
resParse = parse_status_page()
result = transform_dict(resParse)

if critical != -1 and warning != -2:
    if result[0] >= critical:
        end(CRITICAL,
            "requests_ps=%f;;;; busy_workers=%i;;;; idle_workers=%i;;;;" % (
                result[0], result[1], result[2]))
    elif result[0] >= warning and result[0] <= critical:
        end(WARNING,
            "requests_ps=%f;;;; busy_workers=%i;;;; idle_workers=%i" % (
                result[0], result[1], result[2]))
    else:
        end(OK, "requests_ps=%f;;;; busy_workers=%i;;;; idle_workers=%i;;;;" % (
            result[0], result[1], result[2]))
else:
    end(OK,
        "requests_ps=%f;;;; busy_workers=%i;;;; idle_workers=%i;;;;" % (result[0], result[1], result[2]))

