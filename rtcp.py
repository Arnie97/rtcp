#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''./rtcp.py stream[0] stream[1]
stream - [l:port | c:host:port]
l:port表示监听指定的本地端口
c:host:port表示监听远程指定的端口
'''

import sys
from time import sleep
from socket import *
from threading import Thread

streams = [None, None]
debug = 1
TIME_BEFORE_RETRY = 36
MAX_RETRY = QUIT = 199


def _usage():
    print('Usage: ./rtcp.py [l:port | c:host:port]')


def wait_for_stream(i):
    '从streams获取另外一个流对象，如果当前为空，则等待'
    while 1:
        if streams[i] == QUIT:
            print('cannot connect to the target, quit now!')
            sys.exit(1)
        if streams[i]:
            return streams[i]
        else:
            sleep(1)


def relay(source, target, num):
    'num为当前流编号,主要用于调试目的，区分两个回路状态用。'
    try:
        while 1:
            # 注意，recv函数会阻塞，直到对端完全关闭
            # （close后还需要一定时间才能关闭，最快关闭方法是shutdown）
            buffer = source.recv(1024)
            if debug:
                print(num, 'recv')
            if len(buffer) == 0:  # 对端关闭连接，读不到数据
                print(num, 'one closed')
                break
            target.sendall(buffer)
            if debug:
                print(num, 'sendall')
    except:
        print(num, 'An connection has been closed.')

    try:
        source.shutdown(SHUT_RDWR)
        source.close()
        target.shutdown(SHUT_RDWR)
        target.close()
    except:
        pass
    finally:
        streams[0] = streams[1] = None
        print(num, 'CLOSED')


def _listen(port, i):
    srv = socket(AF_INET, SOCK_STREAM)
    srv.bind(('0.0.0.0', port))
    srv.listen(1)
    while 1:
        conn, addr = srv.accept()
        print('connected from:', addr)
        streams[i] = conn
        s2 = wait_for_stream(1 - i)
        relay(conn, s2, i)


def _connect(host, port, i):
    retry_count = 0
    while 1:
        if retry_count > MAX_RETRY:
            streams[i] = QUIT
            print('Time Out')
            return None
        conn = socket(AF_INET, SOCK_STREAM)
        try:
            conn.connect((host, port))
        except:
            print('Failed to connect %s:%s!' % (host, port))
            retry_count += 1
            sleep(TIME_BEFORE_RETRY)
        else:
            print('connected to %s:%i' % (host, port))
            streams[i] = conn
            s2 = wait_for_stream(1 - i)
            relay(conn, s2, i)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        _usage()
        sys.exit(1)
    tlist = []  # 线程列表，最终存放两个线程对象
    for i in [0, 1]:
        argv = sys.argv[i+1].lower().split(':')
        if len(argv) == 2 and argv[0] == 'l':
            tlist.append(Thread(target=_listen, args=(int(sl[1]), i)))
        elif len(argv) == 3 and argv[0] == 'c':
            tlist.append(Thread(target=_connect, args=(sl[1], int(sl[2]), i)))
        else:
            _usage()
            sys.exit(1)
    for t in tlist:
        t.start()
    for t in tlist:
        t.join()
    sys.exit(0)
