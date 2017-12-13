#!/usr/bin/env python3
from twisted.words.protocols.irc import IRC
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory, Factory
from twisted.python import log
import configparser
import random
import time
import json
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
        self.sendLine("PASS {}".format(self.factory.server_pass))
        self.sendLine("PROTOCTL NICKv2 VHP NICKIP UMODE2 SJOIN SJOIN2 SJ3 NOQUIT TKLEXT ESVID MLOCK")
        self.sendLine("PROTOCTL EAUTH={}".format(self.factory.name))
        self.sendLine("PROTOCTL SID={}".format(self.factory.sid))
        self.sendLine("SERVER {} 1 :{}".format(self.factory.name, self.factory.descr))
        self.sendLine(":{} EOS".format(self.factory.sid))
        self.test()
    def test(self):
        self.relay_register_user("hank2", "hank", "DISCORD", "hank from discord")
        self.relay_join_user("hank2", "#banana")
        self.relay_privmsg("hank2", "#banana", "hello world!")
        self.relay_privmsg("hank2", "sean", "hello world!")
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

    def irc_PING(self, prefix, params):
        """Sends a PONG to a received PING."""
        response = params[0]
        self.sendLine("PONG {}".format(response))
    def irc_unknown(self, prefix, command, params):
        print(prefix, command, params)
#        log.msg("{} {} {}".format(prefix, command, " ".join(params)))
    def irc_UID(self, prefix, params):
        print("New user signed on: {}".format(params))
        nick = params[0]
        username = params[3]
        hostname = params[4]
        uid = params[5]
        real_name = params[11]
        self.factory.used_nicks.add(nick)
        print(nick, username, hostname, uid, real_name)
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
        self.uids = set()
        self.used_nicks = set()
        self.uid_counter = 0
        self.users = set()
    def get_uid(self):
        """Returns an unused uid."""
        # TODO: This is very hacky and prone to fault for async. Fix it!
        while True:
            if self.uid_counter not in self.uids:
                self.uids.add(self.uid_counter)
                return str(self.uid_counter).zfill(6)
            self.uid_counter += 1
    def buildProtocol(self, addr):
        """Creates a connection to the IRC network."""
        protocol = ServicesProtocol(self, self.settings)
        self.protocol = protocol
        return protocol	
class IncomingFactory(Factory):
    def __init__(self, services_factory):
        self.services_factory = services_factory
    def buildProtocol(self, addr):
        protocol = IncomingProtocol(self.services_factory)
        return IncomingProtocol(self.services_factory)
class IncomingProtocol(LineReceiver):
    def __init__(self, services_factory):
        self.services_factory = services_factory
    def connectionMade(self):
        print("there is a connection to port 5959")
    def dataReceived(self, data):
        data = data.decode("ascii")
        
        for d in data.split("\n"):
            print("@@@@@")
            print(d)

            print("#####")
            self.parse_line(d)
    def parse_line(self, data):
        try:data = json.loads(data)
        except:
            print("-----------")
            print(data)
            print("="*15)
            return
#        self.transport.send(bytes(data.encode("utf-8")))
        self.sendLine(bytes(str(data).encode("utf-8")))
        
        if data["command"] == "register":
            nick = data["nick"]
            username = data["username"]
            hostname = data["hostname"]
            realname = data["realname"]
            print("REGISTERING USER")
            #TODO: check if the nick is already used on the network.
            # also use a Deferred to check if nick is legal or any other issues
            # maybe even send back a nick that is legal

            self.services_factory.protocol.relay_register_user(nick, username, hostname, realname)
        elif data["command"] == "join":
            nick = data["nick"]
            channel = data["channel"]
            self.services_factory.protocol.relay_join_user(nick, channel)
#            pass
        elif data["command"] == "privmsg":
            nick = data["nick"]
#            nick = "hank2"
            destination = data["destination"]
            message = data["message"]
            self.services_factory.protocol.relay_privmsg(nick, destination, message)
            print("PRIVMSG: {}".format(message))
            print("testtesttest")
#            pass
        #print(json.loads(data.decode("utf-8")))


        #string = json.loads(data.decode("utf-8"))
#    def lineReceived(self, line):
#        """takes in json data, then calls ServicesProtocl methods
#        to relay messages to IRC."""
        #print(line)
        #print(repr(line))
        #split = line.split()

        #print(split)
config = configparser.ConfigParser()
config.read("bridge.conf")
server = config["CONNECTION"]["server"]
port = int(config["CONNECTION"]["port"])

factory = ServicesFactory(config["SERVER SETTINGS"])
reactor.connectTCP(server, port, factory)
reactor.listenTCP(5959, IncomingFactory(factory))
#import sys

#log.startLogging(open("bridge.log", "w"))
#log.startLogging(sys.stdout)
reactor.run()
