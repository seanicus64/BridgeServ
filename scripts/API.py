#!/usr/bin/env python3
# A simple way to directly talk to the bridge service
# using a python API.
# This doesn't actually receive commands back, so an async
# framework like twisted or asyncio should be used instead
# if we, down the line, want to make an easy python module
import socket
import json

class API:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(("localhost", 5959))
        
    def send_command(self, data):
        data = json.dumps(data)
        self.socket.send(bytes(data.encode("utf-8")))
    def register_user(self, nick="nick", username="username", hostname="hostname", realname="realname"):
        data = {}
        data["command"] = "register"
        data["nick"] = nick
        data["username"] = username
        data["hostname"] = hostname
        data["realname"] = realname
        self.send_command(data)
        pass
    def join(self, nick, channel):
        data = {}
        data["command"] = "join"
        data["nick"] = nick
        data["channel"] = channel
        self.send_command(data)
    def privmsg(self, nick, destination, message):
        data = {}
        data["command"] = "privmsg"
        data["nick"] = nick
        data["destination"] = destination
        data["message"] = message
        self.send_command(data)

myapi = API()
myapi.register_user("test1")
myapi.join("test1", "#banana")
myapi.privmsg("test1", "#banana", "api test message")
