#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''./rtcp.py stream[0] stream[1]
stream - [l:port | c:host:port]
l:port表示监听指定的本地端口
c:host:port表示监听远程指定的端口
'''

import sys
import time
from socket import *
from threading import Thread

streams = [None, None]
debug = 1
time_before_retry = 36
max_retry = 199


def _usage():
    print('Usage: ./rtcp.py [l:port | c:host:port]')


def _get_another_stream(i):
    '从streams获取另外一个流对象，如果当前为空，则等待'
    if i == 0:
        i = 1
    elif i == 1:
        i = 0
    else:
        raise OSError

    while 1:
        if streams[i] == 'quit':
            print('cannot connect to the target, quit now!')
            sys.exit(1)
        if streams[i]:
            return streams[i]
        else:
            time.sleep(1)


def exchange(num, s1, s2):
    '''交换两个流的数据。
    num为当前流编号,主要用于调试目的，区分两个回路状态用。'''
    try:
        while 1:
            # 注意，recv函数会阻塞，直到对端完全关闭（close后还需要一定时间才能关闭，最快关闭方法是shutdown）
            buff = s1.recv(1024)
            if debug:
                print(num, 'recv')
            if len(buff) == 0:  # 对端关闭连接，读不到数据
                print(num, 'one closed')
                break
            s2.sendall(buff)
            if debug:
                print(num, 'sendall')
    except:
        print(num, 'one connect closed.')

    try:
        s1.shutdown(SHUT_RDWR)
        s1.close()
        s2.shutdown(SHUT_RDWR)
        s2.close()
    except:
        pass
    streams[0] = streams[1] = None
    print(num, 'CLOSED')


def _listen(port, i):
    srv = socket(AF_INET, SOCK_STREAM)
    srv.bind(('0.0.0.0', port))
    srv.listen(1)
    while 1:
        conn, addr = srv.accept()
        print('connected from:', addr)
        streams[i] = conn  # 放入本端流对象
        s2 = _get_another_stream(i)  # 获取另一端流对象
        exchange(i, conn, s2)


def _connect(host, port, i):
    retry_count = 0
    while 1:
        if retry_count > max_retry:
            streams[i] = 'quit'
            print('Time Out')
            return None
        conn = socket(AF_INET, SOCK_STREAM)
        try:
            conn.connect((host, port))
        except:
            print('Failed to connect %s:%s!' % (host, port))
            retry_count += 1
            time.sleep(time_before_retry)
        else:
            print('connected to %s:%i' % (host, port))
            streams[i] = conn
            s2 = _get_another_stream(i)  # 获取另一端流对象
            exchange(i, conn, s2)


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
