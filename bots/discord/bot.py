#!/usr/bin/env python3
import discord
import asyncio
import socket
import threading
import json
import configparser
client = discord.Client()

class BridgeConnection:
    def __init__(self, socket):
        self.socket = socket
        self.receive = threading.Thread(target=self.get_data)
        self.receive.start()
                                
    def get_data(self):
        """ recieves data from the bridge, converts it to usable commands"""
        while True:
            data = self.socket.recv(4096)
            if data:
                print(data)
    def register_user(self, nick, username, hostname, realname):
        data = {}
        data["command"] = "register"
        data["nick"] = nick
        data["username"] = username
        data["hostname"] = hostname
        data["realname"] = realname
        data = json.dumps(data)
        self.send(data)
    def privmsg(self, name, target, message):
        data = {}
        data["command"] = "privmsg"
        data["nick"] = name
        data["destination"] = target
        data["message"] = message
        data = json.dumps(data)
        self.send(data)
    def join(self, name, channel):
        data = {}
        data["command"] = "join"
        data["nick"] = name
        data["channel"] = channel
        data = json.dumps(data)
        self.send(data)
    def send(self, message):
        message = bytes((message + "\n").encode("utf-8"))
        self.socket.send(message)
@client.event
async def on_ready():
    """When the client firsts connects to discord."""
    print(client.get_all_members())
    members = client.get_all_members()
    for m in members:
        print(m.display_name)
        nick = m.display_name.replace(" ", "_") + "+"
        bridge_connection.register_user(nick, "discord", "bridge", "abcdefg")
        bridge_connection.join(nick, "#banana")
@client.event
async def on_message(message):
    """What happens when a message is recieved on IRC."""
    print(message.author)
    print(message.author.display_name)
    print(message.content)
    target = "#banana"
    nick = message.author.display_name.replace(" ", "_") + "+"
    bridge_connection.privmsg(nick, target, message.content)
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
config = configparser.ConfigParser()
config.read(bot.conf)
server = config["DEFAULT"]["host"]
port = config["DEFAULT"]["port"]
token = config["DEFAULT"]["discord_token"]
socket.connect((server, port))
bridge_connection = BridgeConnection(socket)
client.run(token)
