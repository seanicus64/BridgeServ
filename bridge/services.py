from twisted.words.protocols.irc import IRC
from twisted.internet.protocol import ClientFactory, Factory
from twisted.application import service
from twisted.python import log
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver
from twisted.internet.defer import Deferred
import json
class ListenProtocol(protocol.Protocol):
    def __init__(self):
        """Listens to clients (typically bots) that want to 
        connect to the IRC network through this bridge.
        Recieves formatted JSON.  Will translate JSON into
        IRC-legal commands to the server.  Also responsible
        for passing on IRC events back to the client.
        Lastly, it informs the client of any important details
        it needs to know in order to successfully interact with
        IRC (i.e. legal nicks and chan names)"""
        pass
    def connectionMade(self):
        print("connection has been made!")
        log.msg("Listening socket has a connect to the client.")
    def dataReceived(self, data):
        data = data.decode("ascii")
        lines = data.split("\n")
        for l in lines:
            self.parse_line(l)
    def parse_line(self, line):
        try: obj = json.loads(line)
        except json.JSONDecodeError as e:
            log.msg("JSON error")
            return
        protocol = self.factory.irc_factory.protocol
        if obj["command"] == "register":
            nick = obj["nick"]
            username = obj["username"]
            hostname = obj["hostname"]
            realname = obj["realname"]
            protocol.relay_register_user(nick, username, hostname, realname)
        elif obj["command"] == "join":
            nick = obj["nick"]
            channel = obj["channel"]
            self.factory.irc_factory.protocol
            protocol.relay_join_user(nick, channel)
        elif obj["command"] == "privmsg":
            nick = obj["nick"]
            destination = obj["destination"]
            message = obj["message"]
            protocol.relay_privmsg(nick, destination, message)


class ListenFactory(Factory):
    protocol = ListenProtocol
    def __init__(self, service):
        self.service = service


class ListenService(service.Service):
    def startService(self):
        service.Service.startService(self)

class IRCProtocol(IRC):
    def connectionMade(self):
        log.msg("Connection made to IRC network.")
        self.register()
    def register(self):
        self.sendLine("PASS {}".format(self.factory.service.password))
        self.sendLine("PROTOCTL NICKv2 VHP NICKIP UMODE2 SJOIN SJOIN2 SJ3 NOQUIT TKLEXT ESVID MLOCK")
        self.sendLine("PROTOCTL EAUTH={}".format(self.factory.service.name))
        self.sendLine("PROTOCTL SID={}".format(self.factory.service.sid))
        self.sendLine("SERVER {} 1 :{}".format(self.factory.service.name, self.factory.service.descr))
        self.sendLine(":{} EOS".format(self.factory.service.sid))
        self.test()
    def test(self):
        self.relay_register_user("hank3", "hank3", "hank3", "hank3")

    def relay_register_user(self, nick, username, hostname, real_name):
        current_time = 0
        uid = self.factory.get_uid()
        line = ":{} UID {} 0 {} {} {} {}{} 0 +ixw {} * :{}".format(
            self.factory.sid, nick, current_time, username, 
            hostname, self.factory.sid, uid, self.factory.cloak, 
            real_name)
        self.sendLine(line)
    def relay_join_user(self, nick, channel):
        self.sendLine(":{} JOIN {}".format(nick, channel))
    def relay_privmsg(self, nick, destination, message):
        self.sendLine(":{} PRIVMSG {} :{}".format(nick, destination, message))
    def irc_unknown(self, prefix, command, params):
        print("Unknown command: \033[31m{}\033[32m {}\033[33m {}\033[0m".format(prefix, command, " ".join(params)))
    def irc_NOTICE(self, prefix, params):
        notice = " ".join(params)
        print(prefix + " " + notice)
    def irc_PING(self, prefix, params):
        self.sendLine("PONG {}".format(params[0]))
    def irc_UID(self, prefix, params):
        nick, hop, timestamp, username, hostname = params[0:5]
        uid, servicestamp, umodes, virthost, cloakedhost = params[5:10]
        ip, gecos = params[10:12]
        self.factory.add_new_user(params)
    def irc_SJOIN(self, prefix, params):
        timestamp, channel = params[:2]
        if len(params) == 3:
            users = params[2]
            modes = ""
        elif len(params) == 4:
            modes = params[2]
            users = params[3]
        users = users.split()
        if not self.factory.check_channel(channel):
            self.factory.add_channel(channel, timestamp, modes, users)
        else:
            for u in users:
                self.factory.add_channel_user(channel, u)
        self.factory.list_channels()
    def irc_PART(self, prefix, params):
        channel = params[0]
        self.factory.del_channel_user(channel, prefix)
        self.factory.list_channels()
    
class UserDict:
    def __init__(self):
        self.users = set()
    def get_by_position(self, value, position):
        for u in self.users:
            if u[position] == value:
                return u
        return False
    def get_by_nick(self, nick):
        return self.get_by_position(nick, 0)
    def get_by_uid(self, uid):
        return self.get_by_position(uid, 5)
    def set_user(self, user):
        if self.get_by_nick(user[0]) or \
            self.get_by_uid(user[5]):
                return False
        self.users.add(tuple(user))
        return True
        
class IRCFactory(ClientFactory):
    protocol = IRCProtocol
    uid_counter = 0
    uids = dict()
    user_dict = UserDict()
    channels = dict()
    protocol = None
    def __init__(self, service):
        self.service = service
        self.sid = self.service.sid
        self.cloak = self.service.cloak
    def buildProtocol(self, addr):
        self.protocol = IRCProtocol()
        self.protocol.factory = self
        return self.protocol
    def check_channel(self, channel):
        if channel in self.channels.keys():
            return True
        return False
    def list_channels(self):
        print("The channels are: ")
        for k, v in self.channels.items():
            string = "{}:\n\t\tCreated: {}\n\t\tModes: {}\n\t\tUsers: {}".format(k, v[0], v[1], v[2])
            print(string)
    def check_user_in_channel(self, user, channel):
        for u in self.channels[channel][2]:
            no_prefix = u.strip("@+")
            if no_prefix == user:
                return u
        return False
    def add_channel(self, channel, timestamp, modes, users):
        self.channels[channel] = (timestamp, modes, users)
    def del_channel(self, channel):
        del self.channels[channel]
    def add_channel_user(self, channel, user):
        self.channels[channel][2].append(user)
    def del_channel_user(self, channel, user):
        user_in_channel = self.check_user_in_channel(user, channel)
        if user_in_channel:
            self.channels[channel][2].remove(user_in_channel)
        if len(self.channels[channel][2]) == 0:
            del self.channels[channel]
    def add_new_user(self, user):
        self.user_dict.set_user(user)
    def get_uid(self):
        """Returns an unused uid."""
        while True:
            if self.uid_counter not in self.uids.keys():
                return str(self.uid_counter).zfill(6)
            self.uid_counter += 1

class IRCService(service.Service):
    def __init__(self, config):
        self.password = config["password"]
        self.name = config["name"]
        self.descr = config["description"]
        self.sid = config["sid"]
        self.cloak = config["cloak"]
    def startService(self):
        service.Service.startService(self)

