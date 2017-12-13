#!/usr/bin/env python3
#coded by runciter on #twisted at freenode
# proof of concept to interact with a twisted client as it's going.
import sys

from twisted.internet import defer, endpoints, protocol, task
from twisted.python import log, failure
from twisted.protocols import basic
from twisted.words.protocols import irc


class CommandableBot(irc.IRCClient):
    nickname = 'MyFirstIrcBot'

    def __init__(self):
        self.disconnected = defer.Deferred()

    def connectionLost(self, reason):
        self.disconnected.errback(reason)

    def signedOn(self):
        self.factory.messageReceived(b"Connected")
        self.factory.connected.callback(self)

    def privmsg(self, user, channel, message):
        self.factory.messageReceived(
            "{} {} {}".format(user, channel, message).encode('ascii'))
    def lineReceived(self, line):
        print(line)


class CommandableBotFactory(protocol.ReconnectingClientFactory):
    protocol = CommandableBot

    def __init__(self, messageReceived):
        self.messageReceived = messageReceived
        self.connected = defer.Deferred()

    def buildProtocol(self, *args, **kwargs):
        proto = protocol.ReconnectingClientFactory.buildProtocol(
            self, *args, **kwargs)
        self.protocol = proto
        return proto

    def clientConnectionLost(self, connector, reason):
        self.connected = defer.Deferred()
        self.protocol = None
        return CommandableBotFactory.clientConnectionLost(
            self, connector, reason)

    def sendMessage(self, target, msg, nick=None):
        if nick:
            msg = "%s, %s" % (nick, msg)

        def _send(ignore):
            self.protocol.msg(target, msg)

        if self.protocol is None:
            return self.connected.addCallback(_send)
        return defer.succeed(_send(None))

    def joinChannel(self, channel):
        def _join(ignore):
            self.protocol.join(channel)

        if self.protocol is None:
            return self.connected.addCallback(_join)
        return defer.succeed(_join(None))

    def disconnect(self):
        self.stopTrying()
        if self.protocol is None:
            return defer.succeed(None)
        self.protocol.transport.loseConnection()
        return self.protocol.disconnected


class Command(basic.LineReceiver):
    delimiter = b'\n'

    def lineReceived(self, line):
        command, args = line.split(None, 1)
        method = getattr(self, "do_" + command.decode('ascii'), None)
        if not method:
            self.sendLine(b"Don't know how to " + command)
            return
        else:
            try:
                method(args).addErrback(self.terminate)
            except:
                self.terminate(failure.Failure())

    def terminate(self, reason):
        self.sendLine(b"Terminating: " + str(reason).encode('ascii'))
        self.transport.loseConnection()

    def connectionLost(self, reason):
        self.factory.disconnected.callback(reason)

    def do_join(self, args):
        channel = args.decode('ascii')
        return self.factory.ircFactory.joinChannel(channel)

    def do_send(self, args):
        argsAsList = [arg.decode('ascii') for arg in args.split()]
        return self.factory.ircFactory.sendMessage(*argsAsList)


class CommandFactory(protocol.Factory):
    protocol = Command

    def __init__(self, disconnected):
        self.disconnected = disconnected

    def buildProtocol(self, *args, **kwargs):
        proto = protocol.Factory.buildProtocol(self, *args, **kwargs)
        self.protocol = proto
        return proto


def main(reactor, description):
    disconnected = defer.Deferred()
    print(disconnected.__dict__)
    stdioEndpoint = endpoints.StandardIOEndpoint(reactor)
    stdioFactory = CommandFactory(disconnected)
    stdioConnected = stdioEndpoint.listen(stdioFactory)
    print("1")

    def connectToIRC(ignored):
        ircFactory = CommandableBotFactory(stdioFactory.protocol.sendLine)
        stdioFactory.ircFactory = ircFactory
        endpoint = endpoints.clientFromString(reactor, description)
        return endpoint.connect(ircFactory)

    stdioConnected.addCallback(connectToIRC)
    print(2)
    print(disconnected.__dict__)
    return disconnected


if __name__ == '__main__':
    log.startLogging(sys.stderr)
    task.react(main, ['tcp:irc.freenode.net:6667'])
    print(3)

