#!/usr/bin/env python

from __future__ import print_function
import sys
import getopt
import re
import os
import subprocess

"""
    Get the status of a git repo. Just change the WORKING_DIR.
"""

WORKING_DIR = '/update/my/path'

# Nagios return codes

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3


try:
    opts, args = getopt.getopt(sys.argv[1:], "hg:", ["git-dir="])
except getopt.GetoptError:
    print('git.py -g <git repo>')
    sys.exit(2)

for opt, arg in opts:
    if opt == '-h':
        print('check_git.py -g <git repo>')
        print('Example: ./git.py -g /usr/local/git/reponame')
        sys.exit()
    elif opt in ("-g", "--git-dir"):
        WORKING_DIR = arg


revlist = ['git', 'rev-list', 'HEAD..origin/master', '--count']
rc = 1000
output = ''
try:
    rc = 0
    output = subprocess.check_output(revlist, cwd=WORKING_DIR, stderr=subprocess.STDOUT)
except subprocess.CalledProcessError, e:
    rc = e.returncode
    output = e.output

if rc == 0:
    count = int(output)
    if count > 5:
        print("{} Commits available!".format(count))
        sys.exit(STATE_CRITICAL)
    elif count > 0:
        print("{} Commits available!".format(count))
        sys.exit(STATE_WARNING)
    else:
        print("OK. Git Repo is up to date with origin!")
        sys.exit(STATE_OK)
elif rc > 0:
    print(output, end='')
    sys.exit(STATE_UNKNOWN)
