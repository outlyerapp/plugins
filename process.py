#!/usr/bin/env python
import psutil
import sys

"""
update required_processes with a dictionary of process name and how many should be running
"""

required_processes = {"bash": 5,
                      "launchd": 4}


# wrap getting the process name with exception handling
def get_proc_name(proc):
    try:
        return proc.name()
    except psutil.AccessDenied:
        # IGNORE: we don't have permission to access this process
        pass
    except psutil.NoSuchProcess:
        # IGNORE: process has died between listing and getting info
        pass
    except Exception, e:
        print "error accessing process info: %s" % e
    return None


# get all of the process counts
running_processes = {}
for p in psutil.process_iter():
    process_name = get_proc_name(p)
    if get_proc_name(p) in running_processes:
        running_processes[process_name] += 1
    else:
        running_processes[process_name] = 1

# print the counts and exit correctly
output = ""
exit_status = 0
for process, number in required_processes.iteritems():
    if process in running_processes and required_processes[process] == running_processes[process]:
        # the process name and count are correct
        output += str(process) + '.count=' + str(running_processes[process]) + ';;;; '
    else:
        # the process is running but the count is wrong
        if process in running_processes:
            output += str(process) + '.count=' + str(running_processes[process]) + ';;;; '
            exit_status = 2
        # the process isn't running at all
        else:
            output += str(process) + '.count=0;;;; '
            exit_status = 2

if exit_status == 0:
    print "OK | " + output
    sys.exit(0)
else:
    print "FAIL | " + output
    sys.exit(2)