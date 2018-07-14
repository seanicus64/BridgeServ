#!/usr/bin/env python3
import socket
import select
s = socket.socket()
s.connect(("127.0.0.1", 12345))
#s.setblocking(0)
for i in range(400):
    r, w, e = select.select([s], [], [], 0.05)
    if r:
        data = s.recv(1024)
        print(data)
    print(i)

