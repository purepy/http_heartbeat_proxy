# -*- coding: utf-8 -*-

import socket

LISTEN_PORT = 1235
HTTP_PORT = 8000
SS_PORT = 9876
BUFFER_SIZE = 1024

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('0.0.0.0', LISTEN_PORT))
s.listen(5)
print('Starting proxy server on: 0.0.0.0:{}.'.format(LISTEN_PORT))

while True:
    conn, addr = s.accept()
    data = b''

    while True:
        part = conn.recv(BUFFER_SIZE)
        data += part
        if len(part) < BUFFER_SIZE:
            if len(data) > 3 and data[:3] == b'GET':
                print('Recv heartbeat.')
                port = HTTP_PORT
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as c:
                c.connect(('127.0.0.1', port))
                c.sendall(data)
                while True:
                    data2 = c.recv(1024)
                    if not data2:
                        break
                    try:
                        conn.send(data2)
                    except:
                        break
            break
        port = SS_PORT
