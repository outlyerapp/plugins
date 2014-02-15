#!/usr/bin/env python

import getopt
import os
import re
import sys

"""
    This Nagios plugin will list all processes that consume more memory than the given warn / crit thresholds.
    Returns OK otherwise
"""


def kb_to_mb(value):
    return value * 1024


def kb_to_gb(value):
    return value * 1024 * 1024


def gb_to_kb(value):
    return value / 1024 / 1024


def mb_to_kb(value):
    return value / 1024


def usage():
    print "usage: [-h] [-a] [-m] [-g] -c <int>",
    print "-w <int>"
    print "    Finds processes that are using more than W or C KB"
    print
    print "optional arguments:"
    print "-a    Calculate mem totals per app instead of per pid (calc sum",
    print "for sub procs)"
    print "-c <int>     Crit threshold in KB"
    print "-g GB thresholds instead of default (KB)"
    print "-h, --help  show this help message and exit"
    print "-m MB thresholds instead of default (KB)"
    print "-w <int>     Crit threshold in KB"
    sys.exit(3)


def parse_args():
    """
    Returns a dict of the args as it's easier to work with than a list of
    tuples
    """
    return_dict = {"units": "KB"}
    units_set = False
    # Process the args and assign build the dict to return
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hac:gmw:", ["crit=", "warn="])
    except getopt.GetoptError:
        usage()
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
        elif opt in ("-a", "--app"):
            return_dict["app"] = True
        elif opt in ("-c", "--crit"):
            return_dict["crit"] = int(arg)
        elif opt in ("-g", "-G"):
            if units_set:
                print "\nERROR: -g and -m are mutually exclusive\n"
                usage()
            else:
                return_dict["units"] = "GB"
                units_set = True
        elif opt in ("-m", "-M"):
            if units_set:
                print "\nERROR: -g and -m are mutually exclusive\n"
                usage()
            else:
                return_dict["units"] = "MB"
                units_set = True
        elif opt in ("-w", "--warn"):
            return_dict["warn"] = int(arg)

    # Arg enforcement
    if not "crit" in return_dict or not "warn" in return_dict:
        print "\nERROR: Crit and Warn are required args\n"
        usage()
    elif return_dict["warn"] > return_dict["crit"]:
        print "\nERROR: Crit must be greater than Warn\n"
        usage()

    # down to GB now, we'll lose a couple significant digits
    if return_dict["units"] == "MB":
        return_dict["warn"] = kb_to_mb(return_dict["warn"])
        return_dict["crit"] = kb_to_mb(return_dict["crit"])
    elif return_dict["units"] == "GB":
        return_dict["warn"] = kb_to_gb(return_dict["warn"])
        return_dict["crit"] = kb_to_gb(return_dict["crit"])
    return return_dict


def get_all_pids():
    """
    Return a list of all pids in /proc
    """
    return_list = []
    for pid in os.walk("/proc").next()[1]:
        if re.match("\d+", pid):
            return_list.append(pid)
    return return_list


class Process:
    "Track process info we care about - pid, name, mem consumption, etc"
    name = ""
    pid = 0
    mem_consumption = 0
    units = "KB"

    def __init__(self, pid, units, name="", mem_consumption=0):
        """
        name and mem_consumption can be passed in as values.  Otherwise,
        pull the values out of /proc based on the pid
        pids that are less than 1 are assumed to denote an aggregated
        mem total
        """
        self.pid = pid
        self.units = units
        if not name:
            self.set_process_name()
            self.set_mem_consumption()
        else:
            self.name = name
            self.mem_consumption = mem_consumption

    def __cmp__(self, other):
        return cmp(self.mem_consumption, other.mem_consumption)

    def __str__(self):
        if self.units == "KB":
            tmp_consumption = self.mem_consumption
        elif self.units == "MB":
            tmp_consumption = self.mem_consumption / 1024
        elif self.units == "GB":
            tmp_consumption = self.mem_consumption / 1024 / 1024
        return_string = str(tmp_consumption) + " " + self.units + " "
        return_string += self.name
        if self.pid >= 0:
            return_string += " PID: " + str(self.pid)
        return return_string

    def get_mem_consumption(self):
        return self.mem_consumption

    def get_process_name(self):
        return self.name

    def set_mem_consumption(self):
        """
        Finds mem consumption for a process from /proc/<pid>/status (KB))
        Some procs like kthreadd don't have a VmRSS listed.  Set these as 0
        """
        # Handle the fact that some pids are short lived and can vanish.
        # Set mem_consumption to 0 so these never trigger a warn / crit
        try:
            inFile = open("/proc/" + self.pid + "/status", "r")
        except IOError:
            self.mem_consumption = 0
        else:
            for line in inFile:
                m = re.match("(VmRSS:)\s+(\d+)", line)
                if m:
                    self.mem_consumption = int(m.group(2))
                    return
            self.mem_consumption = 0
            inFile.close()

    def set_process_name(self):
        """
        Finds process name for a process from /proc/<pid>/status
        """
        # Handle the fact that some pids are short lived and can vanish.
        # Set mem_consumption to 0 so these never trigger a warn / crit
        try:
            inFile = open("/proc/" + self.pid + "/status", "r")
        except IOError:
            self.name = "pid_vanished"
            return
        else:
            for line in inFile:
                m = re.match("(Name:)\s+(\S+)", line)
                if m:
                    self.name = m.group(2)
            inFile.close()

    def is_above_mem_threshold(self, value):
        if self.mem_consumption >= value:
            return True
        else:
            return False

args = parse_args()
pids = get_all_pids()
procs = []
crit_procs = []
warn_procs = []
aggregate_dict = {}
# key = proc name, value = mem_consumption
crit_values = {}
warn_values = {}

# Walk the pids to pull mem consumption and proc names
pids = get_all_pids()
for pid in pids:
    procs.append(Process(pid, args["units"]))

# Aggregate the mem consumption for procs with the same name
# if user option is specified
if "app" in args:
    for proc in procs:
        if proc.get_process_name() in aggregate_dict:
            aggregate_dict[proc.get_process_name()] += proc.get_mem_consumption()
        else:
            aggregate_dict[proc.get_process_name()] = proc.get_mem_consumption()
    # Purge list of procs and create new list with aggregate values
    # pid = -1 because we just don't care once we've aggregated
    procs[:] = []
    for name, mem in aggregate_dict.items():
        procs.append(Process(-1, args["units"], name, mem))

# Find offending procs and put them in the appropriate crit/warn bucket
for proc in procs:
    if proc.is_above_mem_threshold(args["crit"]):
        crit_procs.append(proc)
    elif proc.is_above_mem_threshold(args["warn"]):
        warn_procs.append(proc)

# Convert warn and crit back to their original units
if args["units"] == "MB":
    args["warn"] = mb_to_kb(args["warn"])
    args["crit"] = mb_to_kb(args["crit"])
elif args["units"] == "GB":
    args["warn"] = gb_to_kb(args["warn"])
    args["crit"] = gb_to_kb(args["crit"])

# Print messages and return
if crit_procs:
    print "CRITIAL: Processes found that consume more mem than",
    print str(args["crit"]) + " " + args["units"]
    for proc in sorted(crit_procs, reverse=True):
        print str(proc)
    sys.exit(2)
elif warn_procs:
    print "WARNING: Processes found that consume more mem than",
    print str(args["warn"]) + " " + args["units"]
    for proc in sorted(warn_procs, reverse=True):
        print str(proc)
    sys.exit(1)
print "OK: All procs are consuming less than " + str(args["warn"]),
print args["units"] + " of mem"
