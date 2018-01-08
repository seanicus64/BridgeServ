#!/usr/bin/env python3
from twisted.words.protocols.irc import IRC
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor, defer
from twisted.internet.protocol import ClientFactory, Factory
from twisted.python import log
import configparser
import random
import time
import json
import sys
class ServicesProtocol(IRC):
    def __init__(self, factory, config):
        self.factory = factory
        self.config = config
    #TODO: how to log all the lines that come in?
    # can't have this method here
#    def dataReceived(self, line):
#        print("------------")
#        print(line)
#        print("------------")
#        super().dataReceived(line)
    def connectionMade(self):
        """Automatically runs as soon as the connection is made."""
        print("connection made")
        self.register()
    def register(self):
        """Registers this service as a server to the IRC network."""
        print(dir(self))
        self.sendLine("PASS {}".format(self.factory.server_pass))
        self.sendLine("PROTOCTL NICKv2 VHP NICKIP UMODE2 SJOIN SJOIN2 SJ3 NOQUIT TKLEXT ESVID MLOCK")
        self.sendLine("PROTOCTL EAUTH={}".format(self.factory.name))
        self.sendLine("PROTOCTL SID={}".format(self.factory.sid))
        self.sendLine("SERVER {} 1 :{}".format(self.factory.name, self.factory.descr))
        self.sendLine(":{} EOS".format(self.factory.sid))
        self.test()
    def test(self):
        self.relay_register_user("hank2", "hank", "DISCORD", "hank from discord")
        self.relay_register_user("hank3", "hank", "DISCORD", "hank from discord")
        self.relay_join_user("hank2", "#banana")
        self.relay_join_user("hank2", "#fdasfdas")
        self.relay_join_user("hank3", "#fdasfdas")
        self.relay_privmsg("hank2", "#banana", "hello world!")
        #self.relay_privmsg("hank2", "sean", "hello world!")
        import random
        #self.relay_mode("#banana", "+o", ["sean"])

        self.relay_mode("#banana", "+o", ["hank2"])
        self.relay_topic("#banana", "mopic{}".format(random.randrange(10000)), "hank2")
        self.relay_topic("#banana", "mopic{}".format(random.randrange(10000)), "sean")
    def relay_mode(self, recipient, mode, args=None, sender=None):
        to_send = ""
        if sender:
            to_send += ":{} ".format(sender)
        to_send += "MODE {} {}".format(recipient, mode)
        if args:
            to_send += " :" + " ".join(args)
        print(to_send)
        self.sendLine(to_send)
    def relay_topic(self, channel, topic=None, user=None):
        """Changes the topic of a channel, or merely returns topic"""
        if user:
            self.sendLine(":{} TOPIC {} :{}".format(user, channel, topic))
        else:
            self.sendLine("TOPIC {} :{}".format(channel, topic))
    def relay_join_user(self, nick, channel):
        """Joins a user to a channel."""
        self.sendLine(":{} JOIN {}".format(nick, channel))
    def relay_privmsg(self, source, target, message):
        """Sends a message from a user to another user or channel."""
        self.sendLine(":{} PRIVMSG {} :{}".format(source, target, message))
        print("@@@@PRIVMSG: {}".format(message))
    def relay_register_user(self, nick, username, hostname, real_name):
        """Registers a user to the network."""
        current_time = int(time.time())
        uid = self.factory.get_uid()
        self.sendLine(":{} UID {} 0 {} {} {} {}{} 0 +ixw {} * :{}".format(self.factory.sid, nick, current_time, username, hostname, self.factory.sid, uid, self.factory.cloak, real_name))
    def irc_SJOIN(self, prefix, params):
        """Server join...joins users to channels implicitely when server connects."""
        # time stamp, channame,  modes (excluding bans), list of chan members with @ and +'s
        # ['1512443363', '#banana', '+t', '@00192DP0D 001RUNW0C ']
        creation_date = params[0]
        channel = params[1]
        if len(params) == 4:
            modes = params[2]
            users = set(params[3].split())
        else:
            modes = ""
            users = set(params[2].split())
        if channel not in self.factory.channels.keys():
            self.factory.channels[channel] = {
                "creation_date": creation_date,
                "modes": modes,
                "users": users
                }
        else:
            self.factory.channels[channel]["users"].update(users)
        print(channel) 
        print(self.factory.channels[channel])
    def irc_PART(self, prefix, params):
        """Handles users parting channels"""
        channel = params[0]
        message = params[1]
        users = self.factory.channels[channel]["users"].copy()
        for u in users:
            stripped_user = u.strip("~&@%+")
            if stripped_user == prefix:
                self.factory.channels[channel]["users"].remove(u)
        if len(self.factory.channels[channel]["users"]) == 0:
            del self.factory.channels[channel]
    def irc_QUIT(self, prefix, params):
        message = params[0]
        channels_joined_to = self.factory.channels_joined_to(prefix)
        for channel in channels_joined_to:
            self.irc_PART(prefix, [channel, message])
        nick = self.factory.uids[prefix][0]
        self.factory.used_nicks.remove(nick)
        del self.factory.uids[prefix]
    def irc_PING(self, prefix, params):
        """Sends a PONG to a received PING."""
        response = params[0]
        self.sendLine("PONG {}".format(response))
    def irc_unknown(self, prefix, command, params):
        message = "\033[31m{}\033[32m{} \033[33m {}\033[0m".format(prefix + " " if prefix else "", command, " ".join(params))
        print(message)
    def irc_UID(self, prefix, params):
        """Message that a user is newly registered."""
        nick = params[0]
        username = params[3]
        hostname = params[4]
        uid = params[5]
        real_name = params[11]
        self.factory.used_nicks.add(nick)
        self.factory.uids[uid] = [nick, username, hostname, real_name]
        print("{}: {}!{}@{} :{}".format(uid, nick, username, hostname, real_name))
    def irc_PRIVMSG(self, prefix, params):
        print(prefix)
        print(params)
        data = {}
        data["command"] = "privmsg"
        data["user"] = prefix
        data["recipient"] = params[0]
        data["message"] = params[1]
        data = json.dumps(data)
        #data = data.encode("utf-8")
        self.sendLine(data)
        #self.sendLine(json.dumps(data).encode("utf-8"))


class ServicesFactory(ClientFactory):
    def __init__(self, settings):
        self.settings = settings
        self.protocol = None
        self.server_pass = settings["password"]
        self.name = settings["name"]
        self.server_pass = settings["password"]
        self.name = settings["name"]
        self.descr = settings["description"]
        self.sid = settings["sid"]
        self.cloak = settings["cloak"]
#        self.uids = set()
        self.uids = dict()
        self.used_nicks = set()
        self.uid_counter = 0
        self.users = set()
        self.channels = {}
    def channels_joined_to(self, nick):
        joined_to = []
        print(nick)
        for key, value in self.channels.items():
            print(key)
            for user in value["users"]:
                print("{}\t{}\t{}".format(nick, key, user))
                user = user.strip("~&@%+")
                if user == nick:
                    joined_to.append(key)
                    break
        return joined_to
    def get_uid(self):
        """Returns an unused uid."""
        # TODO: This is very hacky and prone to fault for async. Fix it!
        while True:
            #if self.uid_counter not in self.uids:
            if self.uid_counter not in self.uids.keys():
                #self.uids.add(self.uid_counter)
                #self.uids[self.uid_counter] = {}
                
                return str(self.uid_counter).zfill(6)
            self.uid_counter += 1
    def buildProtocol(self, addr):
        """Creates a connection to the IRC network."""
        protocol = ServicesProtocol(self, self.settings)
        self.protocol = protocol
        return protocol	
class IncomingFactory(Factory):
    def __init__(self, services_factory, settings):
        self.services_factory = services_factory
        self.settings = settings
    def buildProtocol(self, addr):
        protocol = IncomingProtocol(self.services_factory, self.settings)
        return protocol
class IncomingProtocol(LineReceiver):
    def __init__(self, services_factory, settings):
        self.services_factory = services_factory
        self.settings = settings
        self.is_authenticated = False
        self.nick_conversion = {}
    def connectionMade(self):
        print("there is a connection to port 5959")
    def dataReceived(self, data):
        data = data.decode("ascii")
        for d in data.split("\n"):
            self.parse_line(d)
        self.sendLine(bytes("I GOT DATA".encode("utf-8")))
    def parse_line(self, data):
        print(data)
        try: data = json.loads(data)
        except json.JSONDecodeError as e:
#            message = data.decode("utf-8")
            message = data
            self.services_factory.protocol.relay_privmsg("hank2", "#banana", message)
            return
        if data["command"] == "authenticate" and not self.is_authenticated:
            if data["password"] == self.settings["password"]:
                self.is_authenticated = True
                print("connection is accepted")
            else:
                self.transport.loseConnection()
        if not self.is_authenticated:
            return
        if data["command"] == "register":
            nick = data["nick"]
            username = data["username"]
            hostname = data["hostname"]
            realname = data["realname"]
            newnick = nick
            if nick in self.services_factory.used_nicks:
                newnick += "-"
            self.nick_conversion[nick] = newnick
            self.services_factory.protocol.relay_register_user(newnick, username, hostname, realname)
        elif data["command"] == "join":
            nick = self.nick_conversion[data["nick"]]
            channel = data["channel"]
            self.services_factory.protocol.relay_join_user(nick, channel)
        elif data["command"] == "privmsg":
            nick = self.nick_conversion[data["nick"]]
            destination = data["destination"]
            message = data["message"]
            self.services_factory.protocol.relay_privmsg(nick, destination, message)
config = configparser.ConfigParser()
config.read("bridge.conf")
server = config["CONNECTION"]["server"]
port = int(config["CONNECTION"]["port"])

factory = ServicesFactory(config["SERVER SETTINGS"])
reactor.connectTCP(server, port, factory)
listen_factory = IncomingFactory(factory, config["LISTEN SETTINGS"])
reactor.listenTCP(5959, listen_factory)
reactor.run()
