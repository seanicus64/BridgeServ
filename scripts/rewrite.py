#!/usr/bin/env python3
#import asyncio #discord API uses this
#from twisted.internet import asyncioreactor
#myloop = asyncio.get_event_loop()
#asyncioreactor.install(myloop)
#from twisted.internet import task
#from twisted.internet import defer
from twisted.internet import endpoints
from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
#import discord
class MyProtocol(Protocol):
    def __init__(self):
        print("hello world")
    def connectionMade(self):
#        super().connectionMade()
        print("connection made")
    def dataReceived(self, data):
        print(data)
class MyFactory(Factory):
    def __init__(self):
        print("initializd")
    def buildProtocol(self, *args, **kwargs):
#        return super().buildProtocol(*args, **kwargs)
        return MyProtocol()
#async def main_task(reactor, loop):
#    my_factory = MyFactory()
##    ep = endpoints.HostnameEndpoint(reactor, "irc.freenode.net", 6667)
#    ep = endpoints.HostnameEndpoint(my_factory, "google.com", 80)
#    await ep.connect(my_factory)
##    async def on_ready():
##        print("whatever")
##    await asyncio.sleep(3)
#    return defer.Deferred()
#
#def main(reactor, loop):
#    # ensureDeferred() turns a coroutine
#    # such as with async def function()
#    # into a deferred by itself
#    # essentially turning async code twisted friendly
#    return defer.ensureDeferred(main_task(reactor, loop))
#
##calls main() and runs reactor until main() returns a 
## deferred firing?
## defer.ensureDeferred itself returns a deferred
##task.react(main, [myloop])
my_factory = MyFactory()
ep = endpoints.HostnameEndpoint(my_factory, "irc.freenode.net", 6667)
ep.connect(my_factory)
reactor.run()
