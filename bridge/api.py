#!/usr/bin/env python3
import socket
import select
import json
class Channel:
    def __init__(self, channel):
        self.name = channel
        self.users = []
        self.messages = []
        self.topic = ""
    def __repr__(self):
        return self.name
class API:
    def __init__(self, host, port):
        self.s = socket.socket()
        self.host = host
        self.port = port
        self.s.connect((host, port))
        self.queue = []
        self.channels = {}
    
    def receive(self):
        r, w, e = select.select([self.s], [], [], 0)
        buff = ""
        if r:
            data = self.s.recv(1024)
            buff += data.decode("utf-8")
            while buff.find("\n") != -1:
                line, buff = buff.split("\n", 1)
                self.parse_line(line)
                print(line)

                yield line
        return 

    def parse_line(self, line):
        try:
            data = json.loads(line)
        except:
            print(line)
            return
        print(data)
        if data["command"] == "join":
            channel = data["channel"]
            if channel not in self.channels.keys():
                channel = Channel(channel)
                self.channels[channel] = channel
                print(self.channels)
            else:
                channel = self.channels[channel]
            nick = data["nick"]
            channel.users.append(nick)
            

        if data["command"] == "privmsg":
            recipient = data["recipient"]
            if recipient in self.channels.keys():
                channel = self.channels[data["channel"]]
                channel.messages.append(data["message"])
            


    def register_user(self, nick, username, hostname, realname):
        data = {}
        data["command"] = "register"
        data["nick"] = nick
        data["username"] = username
        data["hostname"] = hostname
        data["realname"] = realname
        data = json.dumps(data)
        self.s.send(data.encode() + '\n'.encode())
    def join(self, nick, channel):
        data = {}
        data["command"] = "join"
        data["channel"] = channel
        data["nick"] = nick
        data = json.dumps(data)
        self.s.send(data.encode() + "\n".encode())
    def privmsg(self, nick, recipient, message):
        data = {}
        data["command"] = "privmsg"
        data["nick"] = nick
        data["destination"] = recipient
        data["message"] = message
        data = json.dumps(data)
        self.s.send(data.encode())
