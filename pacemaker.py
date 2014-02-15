#!/usr/bin/env python

import subprocess
import socket
import sys
import re

bin_monitor = "/usr/sbin/crm_mon"
bin_status = "/usr/bin/cl_status"
summary = {}


def end(status, message):
    if status == "OK":
        print "OK: %s" % message
        sys.exit(0)
    elif status == "WARNING":
        print "WARNING: %s" % message
        sys.exit(1)
    elif status == "CRITICAL":
        print "CRITICAL: %s" % message
        sys.exit(2)
    else:
        print "UNKNOWN: %s" % message
        sys.exit(3)


def status_info(code, info, nagios_output):
    if code in summary:
        summary[code] += ", %s" % info
    else:
        summary[code] = info
    if nagios_output:
        if "CRITICAL" in summary:
            if "WARNING" in summary:
                summary['CRITICAL'] += ", %s" % summary['WARNING']
            end("CRITICAL", summary["CRITICAL"])
        elif "WARNING" in summary:
            end("WARNING", summary["WARNING"])
        elif "OK" in summary:
            end("OK", summary["OK"])
        elif "UNKNOWN" in summary:
            end("UNKNOWN", summary["UNKNOWN"])


try:
    # summary of cluster's current state
    cmd_monitor = subprocess.Popen([bin_monitor, "-1rf"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

except OSError as errmsg:
    end("UNKNOWN", "%s: %s" % (bin_monitor, errmsg))

else:
    for line in cmd_monitor.stdout:
        # check cluster connected
        if "Connection to cluster failed:" in line:
            end("CRITICAL", "Connection to cluster failed")

        # check for Designated Controller
        if "Current DC:" in line:
            # check for Quorum
            if "partition with quorum" in line:
                status_info("OK", "All resources configured", False)
            else:
                status_info("CRITICAL", "No quorum", False)

        # check offline nodes
        m = re.match(r'OFFLINE:\s*\[\s*(\S.*?)\s*\]', line)
        if m:
            nodes = m.groups()[0]
            count = len(nodes.split(" "))
            status_info("CRITICAL", "%s node(s) OFFLINE: %s" % (str(count), nodes), False)

        # check Master/Slave Stopped
        m = re.match(r'\s*Stopped\:\s*\[(.*)\]', line)
        if m:
            drbd = m.groups()[0]
            status_info("CRITICAL", "%s Stopped" % drbd, False)

        # check Resources Stopped
        m = re.match(r'\s*(\w+)\s+\(\S+\)\:\s+Stopped', line)
        if m:
            resources = m.groups()[0]
            status_info("CRITICAL", "%s Stopped" % resources, False)

        # check Resources FAILED
        m = re.match(r'\s*(\w+)\s+\(\S+\)\:.+FAILED', line)
        if m:
            resources = m.groups()[0]
            status_info("CRITICAL", "%s FAILED" % resources, False)

        # check fail-count
        m = re.match(r'\s*(.+)\:\s+migration-threshold=(\d+)\s+fail-count=(\d+)', line)
        if m:
            resource = m.groups()[0]
            threshold = m.groups()[1]
            fcounts = m.groups()[2]
            # number of critical fail-counts
            fccrit = 10
            # number of warning fail-counts
            fcwarn = 5
            if int(fcounts) > fccrit:
                status_info("CRITICAL", "%s %s fail-count(s) of %s detected" % (resource, fcounts, threshold), False)
            elif int(fcounts) > fcwarn:
                status_info("WARNING", "%s %s fail-count(s) of %s detected" % (resource, fcounts, threshold), False)
            else:
                continue

        # check Unmanaged
        m = re.match(r'\s*(\w+)\s+\(.+\)\:\s+\w+\s+\S+\s+\(unmanaged\)', line)
        if m:
            unmanaged = m.groups()[0]
            status_info("WARNING", "%s unmanaged" % unmanaged, False)

try:
    cmd_hbstatus = subprocess.Popen([bin_status, "hbstatus"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
except OSError as errmsg:
    end("UNKNOWN", "%s: %s" % (bin_status, errmsg))
else:
    # check to see if heartbeat is running
    for line in cmd_hbstatus.stdout:
        if "stopped" in line:
            end("CRITICAL", "Heartbeat is stopped on this machine")

    hblinks = {}
    # find only 'normal' type nodes
    cmd_listnodes = subprocess.Popen([bin_status, "listnodes", "-n"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for node in cmd_listnodes.stdout:
        # strip newlines and blanks
        node = node.strip()
        if node:
            # list hostnames except $(hostname)
            if socket.gethostname() not in node:
                # find network interfaces used as heartbeat links
                cmd_listhblinks = subprocess.Popen([bin_status, "listhblinks", node], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                for link in cmd_listhblinks.stdout:
                    # strip newlines and blanks
                    link = link.strip()
                    if link:
                        # remove duplicated links
                        node_link = node,link
                        if node_link not in hblinks:
                            hblinks[node_link] = True
                            # check status of a heartbeat link
                            cmd_hblinkstatus = subprocess.Popen([bin_status, "hblinkstatus", node, link], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                            for line in cmd_hblinkstatus.stdout:
                                if "dead" in line:
                                    status_info("CRITICAL", "dead hblink %s to %s" % (link, node) , False)
                                elif "up" in line:
                                    status_info("OK", "hblink %s to %s is up" % (link, node), False)
                                else:
                                    status_info("UNKNOWN", "Something is wrong with hblinks...", False)

status_info("", "", True)
