#!/usr/bin/env python
from __future__ import division
import atexit
import gettext
import xmlrpclib
import httplib
import socket
import sys
import urllib
from xml.dom import minidom
import time
import ssl

# SETTINGS
host = 'localhost'
username = 'root'
password = ''

warning = 85
critical = 90

perfdata_format = 'pnp4nagios'

translation = gettext.translation('xen-xm', fallback = True)

API_VERSION_1_1 = '1.1'
API_VERSION_1_2 = '1.2'

class Failure(Exception):
    def __init__(self, details):
        self.details = details

    def __str__(self):
        try:
            return str(self.details)
        except Exception, exn:
            import sys
            print >>sys.stderr, exn
            return "Xen-API failure: %s" % str(self.details)

    def _details_map(self):
        return dict([(str(i), self.details[i])
                     for i in range(len(self.details))])


# Just a "constant" that we use to decide whether to retry the RPC
_RECONNECT_AND_RETRY = object()


class UDSHTTPConnection(httplib.HTTPConnection):
    """HTTPConnection subclass to allow HTTP over Unix domain sockets. """
    def connect(self):
        path = self.host.replace("_", "/")
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(path)


class UDSHTTP(httplib.HTTP):
    _connection_class = UDSHTTPConnection


class UDSTransport(xmlrpclib.Transport):
    def __init__(self, use_datetime=0):
        self._use_datetime = use_datetime
        self._extra_headers=[]
    def add_extra_header(self, key, value):
        self._extra_headers += [ (key,value) ]
    def make_connection(self, host):
        # Python 2.4 compatibility
        if sys.version_info[0] <= 2 and sys.version_info[1] < 6:
            return UDSHTTP(host)
        else:
            return UDSHTTPConnection(host)
    def send_request(self, connection, handler, request_body):
        connection.putrequest("POST", handler)
        for key, value in self._extra_headers:
            connection.putheader(key, value)


class Session(xmlrpclib.ServerProxy):
    """A server proxy and session manager for communicating with xapi using
    the Xen-API.

    Example:

    session = Session('http://localhost/')
    session.login_with_password('me', 'mypassword')
    session.xenapi.VM.start(vm_uuid)
    session.xenapi.session.logout()
    """

    def __init__(self, uri, transport=None, encoding=None, verbose=0,
                 allow_none=1):
        xmlrpclib.ServerProxy.__init__(self, uri, transport, encoding,
                                       verbose, allow_none, context=ssl._create_unverified_context())
        self.transport = transport
        self._session = None
        self.last_login_method = None
        self.last_login_params = None
        self.API_version = API_VERSION_1_1


    def xenapi_request(self, methodname, params):
        if methodname.startswith('login'):
            self._login(methodname, params)
            return None
        elif methodname == 'logout' or methodname == 'session.logout':
            self._logout()
            return None
        else:
            retry_count = 0
            while retry_count < 3:
                full_params = (self._session,) + params
                result = _parse_result(getattr(self, methodname)(*full_params))
                if result is _RECONNECT_AND_RETRY:
                    retry_count += 1
                    if self.last_login_method:
                        self._login(self.last_login_method,
                                    self.last_login_params)
                    else:
                        raise xmlrpclib.Fault(401, 'You must log in')
                else:
                    return result
            raise xmlrpclib.Fault(
                500, 'Tried 3 times to get a valid session, but failed')


    def _login(self, method, params):
        result = _parse_result(getattr(self, 'session.%s' % method)(*params))
        if result is _RECONNECT_AND_RETRY:
            raise xmlrpclib.Fault(
                500, 'Received SESSION_INVALID when logging in')
        self._session = result
        self.last_login_method = method
        self.last_login_params = params
        self.API_version = self._get_api_version()

    def _logout(self):
        try:
            if self.last_login_method.startswith("slave_local"):
                return _parse_result(self.session.local_logout(self._session))
            else:
                return _parse_result(self.session.logout(self._session))
        finally:
            self._session = None
            self.last_login_method = None
            self.last_login_params = None
            self.API_version = API_VERSION_1_1

    def _get_api_version(self):
        pool = self.xenapi.pool.get_all()[0]
        host = self.xenapi.pool.get_master(pool)
        major = self.xenapi.host.get_API_version_major(host)
        minor = self.xenapi.host.get_API_version_minor(host)
        return "%s.%s"%(major,minor)

    def __getattr__(self, name):
        if name == 'handle':
            return self._session
        elif name == 'xenapi':
            return _Dispatcher(self.API_version, self.xenapi_request, None)
        elif name.startswith('login') or name.startswith('slave_local'):
            return lambda *params: self._login(name, params)
        else:
            return xmlrpclib.ServerProxy.__getattr__(self, name)

# Per VM dictionary (used by RRDUpdates to look up column numbers by variable names)
class VMReport(dict):
    """Used internally by RRDUpdates"""
    def __init__(self, uuid):
        self.uuid = uuid

# Per Host dictionary (used by RRDUpdates to look up column numbers by variable names)
class HostReport(dict):
    """Used internally by RRDUpdates"""
    def __init__(self, uuid):
        self.uuid = uuid

class RRDUpdates:
    """ Object used to get and parse the output the http://localhost/rrd_udpates?...
    """
    def __init__(self):
        # params are what get passed to the CGI executable in the URL
        self.params = dict()
        self.params['start'] = int(time.time()) - 1000 # For demo purposes!
        self.params['host'] = 'true'   # include data for host (as well as for VMs)
        self.params['cf'] = 'AVERAGE'  # consolidation function, each sample averages 12 from the 5 second RRD
        self.params['interval'] = '60'

    def get_nrows(self):
        return self.rows

    def get_vm_list(self):
        return self.vm_reports.keys()

    def get_vm_param_list(self, uuid):
        report = self.vm_reports[uuid]
        if not report:
            return []
        return report.keys()

    def get_vm_data(self, uuid, param, row):
        report = self.vm_reports[uuid]
        col = report[param]
        return self.__lookup_data(col, row)

    def get_host_uuid(self):
        report = self.host_report
        if not report:
            return None
        return report.uuid

    def get_host_param_list(self):
        report = self.host_report
        if not report:
            return []
        return report.keys()

    def get_host_data(self, param, row):
        report = self.host_report
        col = report[param]
        return self.__lookup_data(col, row)

    def get_row_time(self,row):
        return self.__lookup_timestamp(row)

    # extract float from value (<v>) node by col,row
    def __lookup_data(self, col, row):
        # Note: the <rows> nodes are in reverse chronological order, and comprise
        # a timestamp <t> node, followed by self.columns data <v> nodes
        node = self.data_node.childNodes[self.rows - 1 - row].childNodes[col+1]
        return float(node.firstChild.toxml()) # node.firstChild should have nodeType TEXT_NODE

    # extract int from value (<t>) node by row
    def __lookup_timestamp(self, row):
        # Note: the <rows> nodes are in reverse chronological order, and comprise
        # a timestamp <t> node, followed by self.columns data <v> nodes
        node = self.data_node.childNodes[self.rows - 1 - row].childNodes[0]
        return int(node.firstChild.toxml()) # node.firstChild should have nodeType TEXT_NODE

    def refresh(self, session, override_params = {}, server = 'http://localhost'):
        params = override_params
        params['session_id'] = session
        params.update(self.params)
        paramstr = "&".join(["%s=%s"  % (k,params[k]) for k in params])
        url = "%s/rrd_updates?%s" % (server, paramstr)

        #print "RRD Query:\n %s" % url
        # this is better than urllib.urlopen() as it raises an Exception on http 401 'Unauthorised' error
        # rather than drop into interactive mode
        sock = urllib.URLopener(context=ssl._create_unverified_context()).open(url)
        xmlsource = sock.read()
        sock.close()
        xmldoc = minidom.parseString(xmlsource)
        self.__parse_xmldoc(xmldoc)
        # Update the time used on the next run
        self.params['start'] = self.end_time + 1 # avoid retrieving same data twice

    def __parse_xmldoc(self, xmldoc):

        # The 1st node contains meta data (description of the data)
        # The 2nd node contains the data
        self.meta_node = xmldoc.firstChild.childNodes[0]
        self.data_node = xmldoc.firstChild.childNodes[1]

        def lookup_metadata_bytag(name):
            return int (self.meta_node.getElementsByTagName(name)[0].firstChild.toxml())

        # rows = number of samples per variable
        # columns = number of variables
        self.rows = lookup_metadata_bytag('rows')
        self.columns = lookup_metadata_bytag('columns')

        # These indicate the period covered by the data
        self.start_time = lookup_metadata_bytag('start')
        self.step_time  = lookup_metadata_bytag('step')
        self.end_time   = lookup_metadata_bytag('end')

        # the <legend> Node describes the variables
        self.legend = self.meta_node.getElementsByTagName('legend')[0]

        # vm_reports matches uuid to per VM report
        self.vm_reports = {}

        # There is just one host_report and its uuid should not change!
        self.host_report = None

        # Handle each column.  (I.e. each variable)
        for col in range(self.columns):
            self.__handle_col(col)

    def __handle_col(self, col):
        # work out how to interpret col from the legend
        col_meta_data = self.legend.childNodes[col].firstChild.toxml()

        # vm_or_host will be 'vm' or 'host'.  Note that the Control domain counts as a VM!
        (cf, vm_or_host, uuid, param) = col_meta_data.split(':')

        if vm_or_host == 'vm':
            # Create a report for this VM if it doesn't exist
            if not self.vm_reports.has_key(uuid):
                self.vm_reports[uuid] = VMReport(uuid)

            # Update the VMReport with the col data and meta data
            vm_report = self.vm_reports[uuid]
            vm_report[param] = col

        elif vm_or_host == 'host':
            # Create a report for the host if it doesn't exist
            if not self.host_report:
                self.host_report = HostReport(uuid)
            elif self.host_report.uuid != uuid:
                raise PerfMonException, "Host UUID changed: (was %s, is %s)" % (self.host_report.uuid, uuid)

            # Update the HostReport with the col data and meta data
            self.host_report[param] = col

        else:
            raise PerfMonException, "Invalid string in <legend>: %s" % col_meta_data


def xapi_local():
    return Session("http://_var_xapi_xapi/", transport=UDSTransport())

def _parse_result(result):
    if type(result) != dict or 'Status' not in result:
        raise xmlrpclib.Fault(500, 'Missing Status in response from server' + result)
    if result['Status'] == 'Success':
        if 'Value' in result:
            return result['Value']
        else:
            raise xmlrpclib.Fault(500,
                                  'Missing Value in response from server')
    else:
        if 'ErrorDescription' in result:
            if result['ErrorDescription'][0] == 'SESSION_INVALID':
                return _RECONNECT_AND_RETRY
            else:
                raise Failure(result['ErrorDescription'])
        else:
            raise xmlrpclib.Fault(
                500, 'Missing ErrorDescription in response from server')


# Based upon _Method from xmlrpclib.
class _Dispatcher:
    def __init__(self, API_version, send, name):
        self.__API_version = API_version
        self.__send = send
        self.__name = name

    def __repr__(self):
        if self.__name:
            return '<XenAPI._Dispatcher for %s>' % self.__name
        else:
            return '<XenAPI._Dispatcher>'

    def __getattr__(self, name):
        if self.__name is None:
            return _Dispatcher(self.__API_version, self.__send, name)
        else:
            return _Dispatcher(self.__API_version, self.__send, "%s.%s" % (self.__name, name))

    def __call__(self, *args):
        return self.__send(self.__name, args)

def logout():
    try:
        session.xenapi.session.logout()
    except:
        pass

atexit.register(logout)

def humanize_bytes(bytes, precision=2, suffix=True, format="pnp4nagios"):

    if format == "pnp4nagios":
        abbrevs = (
            (1<<30L, 'Gb'),
            (1<<20L, 'Mb'),
            (1<<10L, 'kb'),
            (1,      'b')
        )
    else:
        abbrevs = (
            (1<<50L, 'P'),
            (1<<40L, 'T'),
            (1<<30L, 'G'),
            (1<<20L, 'M'),
            (1<<10L, 'k'),
            (1,      'b')
        )

    if bytes == 1:
        return '1 b'
    for factor, _suffix in abbrevs:
        if bytes >= factor:
            break

    if suffix:
        return '%.*f%s' % (precision, bytes / factor, _suffix)
    else:
        return '%.*f' % (precision, bytes / factor)

def performancedata(sr_name, suffix, total, alloc, warning, critical, performancedata_format="pnp4nagios"):

    if performancedata_format == "pnp4nagios":
        performance_line = "'"+sr_name + suffix + "'=" + \
            str(humanize_bytes(alloc,    precision=1, suffix=True, format=performancedata_format)).replace(".",",") + ";" + \
            str(humanize_bytes(warning,  precision=1, suffix=True, format=performancedata_format)).replace(".",",") + ";" + \
            str(humanize_bytes(critical, precision=1, suffix=True, format=performancedata_format)).replace(".",",") + ";0.00;" + \
            str(humanize_bytes(total,    precision=1, suffix=True, format=performancedata_format)).replace(".",",") +""
    else:
        performance_line = "'"+sr_name + suffix + "'=" + \
            str(alloc).replace(".",",") + "B;" + \
            str(warning).replace(".",",")+ ";" + \
            str(critical).replace(".",",") + ";0;" + \
            str(total).replace(".",",") +""

    return(performance_line)

def compute(name, size, util, free, warning, critical, performancedata_format, format_suffix):

    total_bytes_b    = int(size)
    total_alloc_b    = int(util)
    free_space_b	 = int(free)
    used_percent     = 100*float(total_alloc_b)/float(total_bytes_b)
    warning_b        = int((int(total_bytes_b)    / 100) * float(warning))
    critical_b       = int((float(total_bytes_b)  / 100) * float(critical))

    info = {}
    info['performance'] = performancedata(name, format_suffix,
        total_bytes_b,
        total_alloc_b,
        warning_b,
        critical_b,
        performancedata_format)

    info['service'] =  "%s %s%%, size %s, used %s, free %s" % (name,
                                    str(round(used_percent,2)),
                                    str(humanize_bytes(total_bytes_b, precision=0)),
                                    str(humanize_bytes(total_alloc_b, precision=0)),
                                    str(humanize_bytes(free_space_b, precision=0))
                                    )

    return (used_percent, info, total_bytes_b, total_alloc_b)

def mem(session, host, warning, critical, performancedata_format):

    if host:
        hostname          = session.xenapi.host.get_name_label(host)
        mem_size          = session.xenapi.host_metrics.get_record(session.xenapi.host.get_record(host)['metrics'])['memory_total']
        mem_free          = session.xenapi.host_metrics.get_record(session.xenapi.host.get_record(host)['metrics'])['memory_free']

        used_percent, outputdata , total, alloc = compute(hostname, mem_size, str(int(mem_size) - int(mem_free)), mem_free, warning, critical, performancedata_format, "_used_mem")

        if float(used_percent) >= float(critical):
            status = "CRITICAL: MEM "+ hostname
            exitcode = 2
        elif float(used_percent) >= float(warning):
            status = "WARNING: MEM "+ hostname
            exitcode = 1
        else:
            status = "OK: MEM "+ hostname
            exitcode = 0

        return(exitcode, status, outputdata['service'], outputdata['performance'], total, alloc)

    else:
        print "CRITICAL: Cant get mem, check configuration"
        sys.exit(3)

# First acquire a valid session by logging in:
try:
    session = Session("https://"+host)
    session.xenapi.login_with_password(username, password)
except Failure, e:
    if e.details[0] == "HOST_IS_SLAVE":
        session=Session('https://'+e.details[1])
        session.xenapi.login_with_password(username, password)
    else:
        print "CRITICAL - XenAPI Error : " + e.details[0]
        sys.exit(2)

except:
    print "CRITICAL - Connection Error"
    sys.exit(2)



# Initialiaze local variables
finalexit = 0
output = {}
total_mem = 0
total_used = 0
critical_hosts = []
warning_hosts = []

hosts = session.xenapi.host.get_all()
for host in hosts:
    hostname = session.xenapi.host.get_name_label(host)
    exitcode, status, servicedata, perfdata, total, used = mem(session, host, warning, critical, perfdata_format)
    if exitcode > finalexit:
        finalexit = exitcode

    if exitcode == 2 :
        critical_hosts.append(hostname)

    if exitcode == 1 :
        warning_hosts.append(hostname)

    output[hostname] = {}
    output[hostname]['service'] = servicedata
    output[hostname]['perf'] = perfdata

    total_mem += total
    total_used += used

performance = performancedata("Total", "_mem_used",
            total_mem,
            total_used,
            (total_mem/100)*float(warning),
            (total_mem/100)*float(critical),
            perfdata_format)


if finalexit == 2:
    prefix = "CRITICAL: Memory Usage "
    prefix += " / Critical on Hosts = ["+", ".join(critical_hosts)+"]"
    prefix += " / Warning on Hosts = ["+", ".join(warning_hosts)+"]"
elif finalexit == 1:
    prefix = "WARNING: Memory Usage"
    prefix += " / Warning on Hosts = ["+", ".join(warning_hosts)+"]"
else:
    prefix = "OK: Memory Usage"

print prefix + " | " + performance + "\n" + ";\n".join([output[hostname]['service'] for hostname in output]) +	"; | " + " ".join([output[hostname]['perf'] for hostname in output])

sys.exit(finalexit)