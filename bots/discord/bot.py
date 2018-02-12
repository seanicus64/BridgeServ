#!/usr/bin/env python3
# Proof of concept to use discord API and twisted simulteanously.
# this token obviously won't work.
token = "token"
import json
import discord
import asyncio
import random
from twisted.internet.protocol import Protocol
from twisted.internet.protocol import ClientFactory
from twisted.internet import asyncioreactor
from twisted.protocols.basic import LineReceiver
from twisted.internet.defer import Deferred, ensureDeferred
# For some reason, you must install an asyncioreactor before
# you import reactor.
myloop = asyncio.get_event_loop()
asyncioreactor.install(myloop)
from twisted.internet import reactor

# This must be defined before all the coroutines are used.
client = discord.Client()

class MyProtocol(LineReceiver):
    """Client to an arbitrary server.  Sends and receives arbitary data."""
    def __init__(self, factory):
        self.factory = factory
    def connectionMade(self):
        """ Runs when connection is made to server."""
        data = {}
        data["command"] = "authenticate"
        data["password"] = self.factory.settings["DEFAULT"]["bridge_password"]
        data = json.dumps(data).encode("utf-8")
        self.sendLine(data)
        print("connection made to bridge")
#        await client.send_message("Does this work?")
        #self.test_d = ensureDeferred(self.test())
#        self.test()
    async def test(self):
        print("TEST RAN")
        print(client)
        await client.send_message(self.factory.test_channel, "Does this work?")

    def lineReceived(self, line):
        line = line.decode("utf-8")

        print("line received:", line)
        try: data = json.loads(line)
        except:
            print("JSON LOAD ERROR")
            print(line)
            print("*"*40)
            return
#        client.send_message(self.factory.test_channel, data["message"])
#        await client.send_message(self.factory.test_channel, "message")
#        await client.send_message(self.factory.test_channel, data["message"])
        #send(self.factory.test_channel, "message")
#        reactor.callLater(.01, client.send_message, (self.factory.test_channel, "message434343"))
        d = ensureDeferred(client.send_message(self.factory.test_channel, data["message123"]))
        d.callback()
        reactor.callLater(.01, print, ("fdas", "hello world"))
        reactor.callLater(.01, client.send_message, (self.factory.test_channel, "hai"))
        client.send_message(self.factory.test_channel, "test test")
        print(client)
        print("$$$$$$$$$$$")
        if data["command"] == "privmsg":
            print("GOT PRIVMSG", data["message"])
            client.send_message("bot-test", data["message"])
            #except: print("couldn't send it to channel")

        
    def register_user(self, nick, user, host, real):
        data = {}
        data["command"] = "register"
        data["nick"] = nick
        data["username"] = user
        data["hostname"] = host
        data["realname"] = real
        self.send_message(data)
    def join(self, nick, channel):
        data = {}
        data["command"] = "join"
        data["nick"] = nick
        data["channel"] = channel
        self.send_message(data)
    def send_message(self, data):
        """This will send a message to the server."""
        message = bytes(json.dumps(data).encode("utf-8"))
        self.sendLine(message)
        print("I sent out:\t{}".format(message))
    def privmsg(self, nick, recipient, message):
        data = {}
        data["command"] = "privmsg"
        data["nick"] = nick
        data["destination"] = recipient
        data["message"] = message
        self.send_message(data)

class MyFactory(ClientFactory):
    """Necessary to create a protocol.  This is where all the
        permanent data is supposed to be stored."""
    def __init__(self, settings):
        self.protocol = None
        self.settings = settings
        print(self.settings)
        print(self.settings["DEFAULT"]["discord_channel"])
        self.users_to_nicks = {}
        self.users = {}
        self.synced = False
        self.to_be_resolved = {}
    def connected_to_discord(self, client):
        """
        This creates a deferred as soon as you connect to 
        Discord, so when you actually connect to the bridge
        you can actually fire the callback chain."""
        self.client = client
        self.sync_deferred = Deferred()
        self.sync_deferred.addCallback(self.register_list)
    def sync_up(self):
        members = list(self.client.get_all_members())
        self.sync_deferred.callback(members)


    def attempt_register(self, user, nick):
        self.to_be_resolved[user.id] = nick 
        self.protocol.register_user(nick, "user", "host", "real")
    
    def register_list(self, users):
        for user in users:
            print(user)
            nick = user.display_name.replace(" ", "_") + "_"
            # temporary guarantee that nick isnt on network yet.  TODO: make better
            nick += str(random.randrange(100000)).zfill(5)
            self.attempt_register(user, nick)
            print(nick)
            self.protocol.join(nick, "#banana")
            
    def send_to_protocol(self, message):
        """ Simply relays a message to the server we are talking to,"""
        if self.protocol:
            self.protocol.send_message(message.encode("utf-8"))
    def buildProtocol(self, addr):
        """Actually creates the protocol, when ran with reactor.run()"""
        self.protocol = MyProtocol(self)
        return self.protocol
    def new_message(self, message):
        print(message.content)
        author = message.author
        discord_id = message.author.id
        try: nick = self.to_be_resolved[discord_id]
        except: return
        recipient = "#banana"
        self.protocol.privmsg(nick, recipient, message.content)


# Creating this factory before the coroutines because send_to_protocol
# could theoretically be run before connection is established.
import configparser
config = configparser.ConfigParser()
config.read("bot.conf")
token = config["DEFAULT"]["discord_token"]
my_factory = MyFactory(config)


@client.event
async def on_ready():
    """Everything that happens when the discord bot connects initially."""
    print("Logged in as: {}".format(client.user.name))
    print("we are connected to discord")
    my_factory.connected_to_discord(client)
    my_factory.sync_up()
#    print(client.get_all_channels())
#    print(list(client.get_all_channels()))
    for c in list(client.get_all_channels()):
#        print(dir(c))
#        print(c.name)
        if c.name == "bot-test":
            print("\033[32m========================\033[0m")
            my_factory.test_channel = c
#            my_factory.protocol.test_d.callback(5)
            ensureDeferred(my_factory.protocol.test())
            #await client.send_message(my_factory.test_channel, "message1")
            break

@client.event
async def on_message(message):
    """Everything that happens when a message is sent on the discord server."""
    print(dir(message))
    print(message.author)
    my_factory.new_message(message)
#    await client.send_message(my_factory.test_channel, "message2")
@client.event
async def on_member_join(member):
    print(member)
    print("joined!")
@client.event
async def on_member_leave(member):
    print(member, "left!")
#    my_factory.send_to_protocol(message.content)    
# honestly not sure how to describe this but
# just read this: http://discordpy.readthedocs.io/en/latest/migrating.html#running-the-client
@asyncio.coroutine
def main_task():
    yield from client.login(token)
    yield from client.connect()
# The asyncio loop was already added to the reactor.  Now we add the main_task coroutine
# which will actually run the bot.
asyncio.ensure_future(main_task())
# We can then run the reacor normally, knowing it will also run the event loop for asyncio
#reactor.connectTCP("irc.freenode.net", 6667, my_factory)

reactor.connectTCP("localhost", 5959, my_factory)
reactor.run()
