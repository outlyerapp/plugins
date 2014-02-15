#!/usr/bin/env python

from pynagios import Plugin, Response, make_option, CRITICAL, UNKNOWN
import socket


class StatsdCheck(Plugin):
    port = make_option('-p', '--port', type='int', default=8126)
    metric = make_option('-m', '--metric', type='str', default='uptime')
    _socket = None

    def _connect(self, host, port, timeout):
        exception = None

        for (af, socktype, proto, cname, sa) in socket.getaddrinfo(
                host, port, socket.AF_UNSPEC, socket.SOCK_STREAM):

            try:
                self._socket = socket.socket(af, socktype, proto)
                self._socket.settimeout(timeout)
                self._socket.connect(sa)
                return
            except socket.error as e:
                if self._socket:
                    self._socket.close()
                    self._socket = None
                exception = e

        raise exception

    def check(self):
        timeout = self.options.timeout if self.options.timeout > 0 else 10
        metric = self.options.metric.strip().lower()

        if not self.options.hostname:
            return Response(UNKNOWN, 'Hostname is missing')

        try:
            self._connect(self.options.hostname, self.options.port, timeout)
            self._socket.sendall('stats')
            data = ''
            while True:
                data += self._socket.recv(1024)
                if data and 'END' in data:
                    break
            self._socket.close()
        except socket.error, (errno, msg):
            return Response(CRITICAL, msg)
        except socket.timeout, msg:
            return Response(CRITICAL, msg)

        data = data.strip().split('\n')
        data.remove('END')

        if not data:
            return Response(CRITICAL, 'No stats received')

        stats = {}
        for stat in data:
            k, v = stat.split(':')
            stats[k.strip().lower()] = v.strip()

        result = self.response_for_value(float(stats[metric]), '%s: %s' % (
            metric, stats[metric]))

        for k, v in stats.items():
            result.set_perf_data(k, int(v))

        return result


StatsdCheck().check().exit()
