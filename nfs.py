#!/usr/env/bin python

import os
import re

"""
This plugin will check fstab for declared nfs mount points and /proc/mount for
actual mounted nfs shares.
It will touch a temporary file to each discovered NFS share as proof it is mounted
and operating correctly
"""


FSTAB = "/etc/fstab"
MOUNTS = "/proc/mounts"
TOUCH_BIN = "/usr/bin/touch"
TEMP_FILE = "tomash/outlyer.nfstest"   # This is the path once on the NFS Share
ERROR = 0
E_MESSAGE = ""


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)


def detect_fstab_nfs():
    # get all NFS mountpoints defined in fstab
    nfs = {}
    with open(FSTAB, 'r') as fstab:
        for line in fstab:
            if len(line.strip()) == 0:
                pass
            elif re.match('^#.*$', line):
                pass
            else:
                if line.split()[2] == 'nfs':
                    nfs[line.split()[1]] = line.split()[0]
    return nfs


def detect_mounted_nfs():
    # detect mounted NFS filesystems
    nfs = {}
    with open(MOUNTS, 'r') as mounts:
        for line in mounts:
            if len(line.strip()) == 0:
                pass
            elif re.match('^#.*$', line):
                pass
            else:
                if line.split()[2] == 'nfs':
                    nfs[line.split()[1]] = line.split()[0]
    return nfs


fstab = detect_fstab_nfs()
mounted = detect_mounted_nfs()

if len(mounted) < 1:
    ERROR = 1
    E_MESSAGE = " - no NFS mountpoints found"

# ensure fstabs are mounted
for path, device in fstab.iteritems():
    if path in mounted.keys():
        if mounted[path] != device:
            ERROR = 2
            E_MESSAGE += " - %s incorrectly mounted" % path



# write to nfs shares that _are_ mounted
for path in mounted.keys():
    TOUCHME = path + "/" + TEMP_FILE
    TOUCHDIR = "/".join(TOUCHME.split('/')[:-1])
    try:
        if os.path.isdir(TOUCHDIR):
            touch(TOUCHME)
        else:
            ERROR = 2
            E_MESSAGE += " - directory %s does not exist" % (TOUCHDIR)
    except:
        ERROR = 2
        E_MESSAGE += " - failed to touch file %s" % (TOUCHME)


if ERROR == 0:
    print "OK - nfs mounts ok"
    exit(0)
if ERROR == 1:
    print "WARNING %s" % E_MESSAGE
elif ERROR == 2:
    print "CRITICAL %s" % E_MESSAGE
    exit(2)
else:
    print "UNKNOWN - Something went wrong"
    exit(3)
