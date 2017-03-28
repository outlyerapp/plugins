#!/opt/dataloop/embedded/bin/python

import sys
import re
import subprocess
from StringIO import StringIO

DF_REGEX = r'^(?P<fs>[^\s]*)\s+(?P<size>\d+)\s+(?P<used>\d+)\s+(?P<free>\d+)\s+(?P<pct>\d+)%\s+(?P<mount>.*)$'
STAT_REGEX = r'^(?P<fs>[^\s]*)\s+(?P<rmb>[\d.]+)\s+(?P<wmb>[\d.]+)\s+(?P<rops>[\d.]+)\s+(?P<wops>[\d.]+)\s+(?P<fo>[\d.]+)\s+(?P<fc>[\d.]+)\s+(?P<fd>[\d.]+)'

buf = StringIO()


def sanitize_fsname(fs_name):
    return re.sub(r'[/\\]+', '-', fs_name).lstrip('-')

try:
    output = subprocess.check_output("df -t cifs --block-size 1M", shell=True, universal_newlines=True)
except subprocess.CalledProcessError as ex:
    print 'CRITICAL | command failed: ' + ex.message
    sys.exit(2)
    
for m in re.finditer(DF_REGEX, output, flags=re.MULTILINE):
    fs_name = sanitize_fsname(m.group('fs'))
    buf.write('{0}.size={1};;;; '.format(fs_name, m.group('size')))
    buf.write('{0}.used={1};;;; '.format(fs_name, m.group('used')))
    buf.write('{0}.avail={1};;;; '.format(fs_name, m.group('free')))
    buf.write('{0}.used_pct={1};;;; '.format(fs_name, m.group('pct')))

try:
    output = subprocess.check_output("cifsiostat -m 1 2", shell=True, universal_newlines=True)
except subprocess.CalledProcessError as ex:
    print 'CRITICAL | command failed: ' + ex.message
    sys.exit(2)

count = len(re.findall(STAT_REGEX, output, flags=re.MULTILINE))

i = 0
for m in re.finditer(STAT_REGEX, output, flags=re.MULTILINE):
    if i >= count // 2:
        fs_name = sanitize_fsname(m.group('fs'))
        buf.write('{0}.read_mbps={1};;;; '.format(fs_name, m.group('rmb')))
        buf.write('{0}.write_mbps={1};;;; '.format(fs_name, m.group('wmb')))
        buf.write('{0}.read_ops={1};;;; '.format(fs_name, m.group('rops')))
        buf.write('{0}.write_ops={1};;;; '.format(fs_name, m.group('wops')))
        buf.write('{0}.files_opened={1};;;; '.format(fs_name, m.group('fo')))
        buf.write('{0}.files_closed={1};;;; '.format(fs_name, m.group('fc')))
        buf.write('{0}.files_deleted={1};;;; '.format(fs_name, m.group('fd')))
    i += 1

print 'OK | ' + buf.getvalue()

