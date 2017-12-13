#!/usr/bin/env python3
# Proof of concept to use discord API and twisted simulteanously.
# this token obviously won't work.
token = "token"
import discord
import asyncio
from twisted.internet.protocol import Protocol
from twisted.internet.protocol import ClientFactory
from twisted.internet import asyncioreactor
# For some reason, you must install an asyncioreactor before
# you import reactor.
myloop = asyncio.get_event_loop()
asyncioreactor.install(myloop)
from twisted.internet import reactor

# This must be defined before all the coroutines are used.
client = discord.Client()

class MyProtocol(Protocol):
    """Client to an arbitrary server.  Sends and receives arbitary data."""
    def connectionMade(self):
        """ Runs when connection is made to server."""
        print("connection made")
    def dataReceived(self, data):
        """Runs when data is received from server."""
        print("data:")
        print(data)
    def send_message(self, message):
        """This will send a message to the server."""
        self.transport.write(message)
        print("I sent out: {}".format(message))
class MyFactory(ClientFactory):
    """Necessary to create a protocol.  This is where all the
        permanent data is supposed to be stored."""
    def __init__(self):
        self.protocol = None
    def send_to_protocol(self, message):
        """ Simply relays a message to the server we are talking to,"""
        if self.my_protocol:
            self.my_protocol.send_message(message.encode("utf-8"))
    def buildProtocol(self, addr):
        """Actually creates the protocol, when ran with reactor.run()"""
        self.my_protocol = MyProtocol()
        return self.my_protocol

# Creating this factory before the coroutines because send_to_protocol
# could theoretically be run before connection is established.
my_factory = MyFactory()


@client.event
async def on_ready():
    """Everything that happens when the discord bot connects initially."""
    print("Logged in as: {}".format(client.user.name))
@client.event
async def on_message(message):
    """Everything that happens when a message is sent on the discord server."""
    my_factory.send_to_protocol(message.content)    
    print(message.content)
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
reactor.connectTCP("irc.freenode.net", 6667, my_factory)
reactor.run()

