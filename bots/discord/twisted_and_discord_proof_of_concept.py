#!/usr/bin/env python3
# Proof of concept to use discord API and twisted simulteanously.
# this token obviously won't work.
token = "token"
import json
import discord
import asyncio
from twisted.internet.protocol import Protocol
from twisted.internet.protocol import ClientFactory
from twisted.internet import asyncioreactor
from twisted.protocols.basic import LineReceiver
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
        print("connection made")
        data["command"] = "authenticate"
        data["password"] = self.factory.settings["DEFAULT"]["bridge_password"]
        data = json.dumps(data).encode("utf-8")
        print(data)

        self.sendLine(data)

        
#    def dataReceived(self, data):
#        """Runs when data is received from server."""
#        print("data:")
#        print(data)
    def lineReceived(self, line):
        print("line received:")
        print(line)
    def register_user(self, nick, user, host, real):
        data = {}
        data["command"] = "register"
        data["nick"] = nick
        data["username"] = user
        data["hostname"] = host
        data["realname"] = real
        self.send_message(bytes(json.loads(data).encode("utf-8")))
    def send_message(self, message):
        """This will send a message to the server."""
        self.transport.write(message)
        print("I sent out: {}".format(message))
class MyFactory(ClientFactory):
    """Necessary to create a protocol.  This is where all the
        permanent data is supposed to be stored."""
    def __init__(self, settings):
        self.protocol = None
        self.settings = settings
        self.users_to_nicks = {}
    def send_to_protocol(self, message):
        """ Simply relays a message to the server we are talking to,"""
        if self.my_protocol:
            self.my_protocol.send_message(message.encode("utf-8"))
    def buildProtocol(self, addr):
        """Actually creates the protocol, when ran with reactor.run()"""
        self.my_protocol = MyProtocol(self)
        return self.my_protocol

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
    members = client.get_all_members()
    for m in members:
        nick = m.display_name.replace(" ", "_")
        my_factory.users_to_nicks[nick]
        my_factory.protocol.register_user(nick, "discord", "bridge", "abcde")

@client.event
async def on_message(message):
    """Everything that happens when a message is sent on the discord server."""
    print(dir(message))
    print(message.author)
    print(dir(message.author))
    print(message.author.id)
    print(message.author.discriminator)
    my_factory.send_to_protocol(message.content)    
    #print(message.content)
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
"""
@client.event
async def on_ready(): 
    ""When the client firsts connects to discord.""        print(client.get_all_members())
            members = client.get_all_members()
                for m in members:
                        print(m.display_name)
                                nick = m.display_name.replace(" ", "_") #+ "|"
                                        print(nick)
                                                bridge_connection.register_user(nick, "discord", "bridge", "abcdefg")
                                                        bridge_connection.join(nick, "#banana")
"""
