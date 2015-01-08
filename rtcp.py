#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Authored by:
# evilcos <evilcos@gmail.com>
# Arnie97 <me@arnie97.progr.am>

'Usage: ./rtcp.py [l@[host]:port | c@[host]:port]'

import sys
from time import sleep
from socket import *
from threading import Thread

streams = [None, None]
threads = []
TIME_BEFORE_RETRY = 36
MAX_RETRY = QUIT = 199
BUFFER_SIZE = 1024


def _wait_for_stream(id):
    'Wait until streams[id] is available.'
    while 1:
        if streams[id] == QUIT:
            sys.exit(2)
        elif streams[id]:
            return streams[id]
        else:
            sleep(1)


def _relay(id):
    'Relay packets from source to target.'
    global streams
    source, target = streams[id], streams[1-id]
    try:
        while 1:
            buffer = source.recv(BUFFER_SIZE)
            buffer_length = len(buffer)
            if buffer_length == 0:
                print('*%d remote closed' % id)
                break
            else:
                print('>%d %d received' % (id, buffer_length))
            target.sendall(buffer)
            print('<%d %d sent' % (1 - id, buffer_length))
    except:
        print('*%d connection closed' % id)
    for pos in range(2):
        try:
            streams[pos].shutdown(SHUT_RDWR)
            streams[pos].close()
        except:
            print('!%d unable to close a socket' % pos)
        else:
            print('*%d socket closed' % pos)


def _listen(port, id, host='0.0.0.0'):
    'Listen an local TCP port as a stream.'
    srv = socket(AF_INET, SOCK_STREAM)
    srv.bind((host, port))
    srv.listen(1)
    while 1:
        conn, addr = srv.accept()
        print(':%d connected from %s:%i' % (id, addr[0], addr[1]))
        streams[id] = conn
        another_stream = _wait_for_stream(1 - id)
        _relay(id)


def _connect(port, id, host='localhost'):
    'Connect to a remote TCP port as a stream.'
    retry_count = 0
    while 1:
        if retry_count > MAX_RETRY:
            streams[id] = QUIT
            print('!%d request time out' % id)
            return None
        conn = socket(AF_INET, SOCK_STREAM)
        try:
            conn.connect((host, port))
        except:
            print('!%d failed to connect %s:%i' % (id, host, port))
            retry_count += 1
            sleep(TIME_BEFORE_RETRY)
        else:
            print(':%d connected to %s:%i' % (id, host, port))
            streams[id] = conn
            another_stream = _wait_for_stream(1 - id)
            _relay(id)


if __name__ == '__main__':
    try:
        argv = sys.argv[1:]
        assert len(argv) == 2
        for pos in range(2):
            type = argv[pos].lower().split('@')
            assert len(type) == 2
            assert type[0] in 'lc'
            addr = type[1].rpartition(':')
            kwargv = {'id': pos, 'port': int(addr[-1])}
            if addr[0]:
                kwargv['host'] = addr[0]
            threads.append(Thread(
                target = _connect if type[0]=='c' else _listen,
                kwargs = kwargv
            ))
            threads[pos].start()
        for thread in threads:
            thread.join()
        sys.exit(0)
    except AssertionError:
        print(__docs__)
        sys.exit(1)
