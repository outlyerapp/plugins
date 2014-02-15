#!/usr/bin/python

from subprocess import Popen, PIPE
import sys
from pynag.Plugins import PluginHelper


def main():
    p = PluginHelper()

    # Warn on inactive
    level = 2

    service_status = get_service_status(sys.argv[1])

    if loaded(service_status)[0] is False:
        p.exit(3,
               "%s - %s" % (service_status['name'],
                            loaded(service_status)[1]),
               "\n" + service_status['unparsed'])

    active = service_status['headers']['Active'][0]
    if active.startswith("inactive") or active.startswith('failed'):
        p.add_status(level)
    elif active.startswith("active"):
        p.add_status(0)
    else:
        p.add_status(3)

    p.add_summary("%s - %s" % ( service_status['name'], active))
    p.add_long_output("\n" + service_status['unparsed'])
    p.exit()


def loaded(stat):
    if stat['headers']['Loaded']:
        if stat['headers']['Loaded'][0].startswith("error"):
            return False, stat['headers']['Loaded'][0]
    return True, stat['headers']['Loaded'][0]


def get_service_status(service):
    stdout = Popen(["systemctl", "status", service], stdout=PIPE).communicate()[0]
    stdout_lines = stdout.split("\n")
    name = stdout_lines.pop(0).split()[0]

    headers = {}

    while len(stdout_lines):
        l = stdout_lines.pop(0).strip()

        if l == "":
            break

        k, v = l.split(': ', 1)
        if k in headers:
            headers[k].append(v)
        else:
            headers[k] = [v]

    return {"name": name, "headers": headers, "journal": stdout_lines, "unparsed": stdout}


main()

