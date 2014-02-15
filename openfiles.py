#! /usr/bin/env python

import os
import sys
import psutil
import optparse

"""
    Nagios check to monitor the number of files opened by a process.

    Usage:
        -p -f /var/run/mydaemon.pid
        OK: Process 13403 has 4037 file descriptors opened|num_fds=4037;6000;6000;;

        http://exchange.nagios.org/directory/Plugins/Operating-Systems/Linux/check_num_fds/details

"""

usage = """
            Typically %prog is invoked by the nrpe service that runs as the user nagios:

            sudo %prog -p -f /var/run/mydaemon.pid
        """
parser = optparse.OptionParser(usage=usage)
parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                  help="verbose mode.")
parser.add_option("-p", "--proc", action="store_true", dest="proc",
                  help="to use the soft/hard limits from /proc/pid as the warning/critical thresholds.")
parser.add_option("-f", "--file", dest="file", type="string",
                  help=".pid file containing the process pid.")
parser.add_option("-w", "--warn", dest="warn_value", default="-1", type="int",
                  help="warning threshold.")
parser.add_option("-c", "--crit", dest="crit_value", default="-1", type="int",
                  help="critical threshold.")
(options, args) = parser.parse_args()

if len(args) != 0:
    sys.exit(parser.print_help())

if options.verbose:
    print "Checking if the provided string: " + options.file + " is really a file."

assert os.path.isfile(options.file)

try:
    if options.verbose :
        print "Opening file: " + options.file
    pidfile = open(options.file, 'r')
    pid = int(pidfile.readline())
    if options.verbose:
        print "Found pid: " + str(pid)
    if options.verbose:
        print "Checking if the pid=" + str(pid) + " is a live process."
    assert psutil.pid_exists( pid )

except IOError:
    print "Can't open the file %s", options.file
    sys.exit(1)

if options.proc:
    try:
        if options.verbose:
            print "Opening the file: /proc/" + str(pid) + "/limits"

        procfile = open('/proc/' + str(pid) + '/limits', 'r')

        for line in procfile:
            if options.verbose:
                print "Searching for the 'Max open files' settings in: " + line

            if "Max open files" in line:
                mylist = [int(s) for s in line.split() if s.isdigit()]
                options.warn_value = mylist[0]
                options.crit_value = mylist[1]
                if options.verbose:
                    print "Found soft limit: " + str(options.warn_value)
                if options.verbose:
                    print "Found hard limit: " + str(options.crit_value)
                break

    except IOError:
        print "Can't open the file %s", options.file
        sys.exit(1)


# Getting the number of files opened by pid
num_fds = psutil.Process(pid).get_num_fds()


assert options.warn_value > 0
assert options.crit_value > 0

# Nagios possible states

status_dict = {
    0: "OK",
    1: "WARNING",
    2: "CRITICAL",
    3: "UNKNOWN"
}

if num_fds > options.crit_value:
    status = 2
elif num_fds > options.warn_value:
    status = 1
else:
    status = 0

print "{0}: Process {1} has {2} file descriptors opened|num_fds={2};{3};{4};;".format(status_dict[status], str(pid), str(num_fds), str(options.warn_value), str(options.crit_value))
exit(status)