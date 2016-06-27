#!/usr/bin/env python
import subprocess
import csv
import sys

# set to the name of the process as shown by task manager under details i.e not the display name
PROCESS = ''

p_tasklist = subprocess.Popen('tasklist.exe /fo csv',
                              stdout=subprocess.PIPE,
                              universal_newlines=True)

pythons_tasklist = []
for p in csv.DictReader(p_tasklist.stdout):
    if p['Image Name'] == PROCESS:
        sys.exit(0)

sys.exit (2)
