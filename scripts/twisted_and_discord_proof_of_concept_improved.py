#!/usr/bin/env python3
#runciter on #twisted @ freenode's improvement on my proof of concept.
# There is a new idiomatic way to use twisted than the way I've been using it
# we should learn this way to make our code better, eventually.
# he misunderstood my code to be an actual IRC bot

# this token obviously won't work.
token = "token"
import discord
import asyncio
from twisted.internet import asyncioreactor
myloop = asyncio.get_event_loop()
asyncioreactor.install(myloop)

from twisted.words.protocols import irc
from twisted.internet.protocol import ClientFactory
from twisted.internet import defer, endpoints, task

# This must be defined before all the coroutines are used.
client = discord.Client()

class MyBot(irc.IRCClient):
    """IRC Client to an arbitrary server.  Sends and receives arbitary data."""
    # Your IRC bot's nickname
    nickname = "YourBot"
    def connectionMade(self):
        """ Runs when connection is made to server."""
        super().connectionMade()
        print("connection made")
    def privmsg(self, user, channel, message):
        print("Message received", user, channel, message)
class MyFactory(ClientFactory):
    """Necessary to create a protocol.  This is where all the
        permanent data is supposed to be stored."""
    protocol = MyBot
    def send_to_protocol(self, message):
        """ Simply relays a message to the server we are talking to,"""
        if self.my_protocol:
            self.my_protocol.sendMsg(message)
    def buildProtocol(self, *args, **kwargs):
        """
        Retain a reference to the last constructed protocol.
        """
        self.my_protocol = super().buildProtocol(*args, **kwargs)
        return self.my_protocol


async def mainTask(reactor, loop):
    my_factory = MyFactory()
    async def on_ready():
        """Everything that happens when the discord bot connects initially."""
        print("Logged in as: {}".format(client.user.name))
    client.event(on_ready)
    async def on_message(message):
        """Everything that happens when a message is sent on the discord server."""
        my_factory.send_to_protocol(message.content)
        print(message.content)
    client.event(on_message)
    # honestly not sure how to describe this but
    # just read this: http://discordpy.readthedocs.io/en/latest/migrating.html#running-the-client
    ep = endpoints.HostnameEndpoint(reactor, "irc.freenode.net", 6667)
    await ep.connect(my_factory)
    await client.login(token)
    await client.connect()
    return defer.Deferred()


def main(reactor, loop):
    return defer.ensureDeferred(mainTask(reactor, loop))


task.react(main, [myloop])
