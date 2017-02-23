# -*- coding: utf-8 -*-

from gevent.monkey import patch_all
patch_all()

import time
import socket
import sys
import signal
import gevent
from wsgiref.handlers import format_date_time
from gevent.server import StreamServer
from gevent.socket import (
    create_connection,
    gethostbyname,
)

LISTEN_PORT = 1235
SS_PORT = 9876
BUFFER_SIZE = 1024


class MixedTCPServer(StreamServer):

    def __init__(self, listen_port, tcp_forward_port, **kwargs):
        super().__init__('0.0.0.0:{}'.format(listen_port), **kwargs)
        self.tcp_service = '127.0.0.1:{}'.format(tcp_forward_port)

    def handle(self, source, address):
        init_data = source.recv(BUFFER_SIZE)
        try:
            if len(init_data) > 3 and init_data[:3] == b'GET':
                source.sendall(b'HTTP/1.1 200 OK\r\n' + format_date_time(time.time()).encode() + b'\r\n\r\nOK')
                return
            else:
                dest = create_connection(self.tcp_service)
        except IOError as ex:
            sys.stderr.write('Error on create connection: {}'.format(ex))
            return
        forwarders = (
            gevent.spawn(forward, source, dest, self),
            gevent.spawn(forward, dest, source, self),
        )
        gevent.joinall(forwarders)

    def close(self):
        if not self.closed:
            sys.stderr.write('Closing...')
            super().close()


def forward(source, dest, server):
    try:
        while True:
            try:
                data = source.recv(BUFFER_SIZE)
                if not data:
                    break
                dest.sendall(data)
            except KeyboardInterrupt:
                if not server.closed:
                    server.close()
                break
            except socket.error:
                if not server.closed:
                    server.close()
                break
    finally:
        source.close()
        dest.close()
        server = None


def main():
    server = MixedTCPServer(LISTEN_PORT, SS_PORT)
    gevent.signal(signal.SIGTERM, server.close)
    gevent.signal(signal.SIGINT, server.close)
    server.start()
    gevent.wait()


if __name__ == '__main__':
    main()
