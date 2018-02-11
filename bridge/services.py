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
        """When a client connects to the bridge, add it to the factory."""
        self.factory.protocols.append(self)
        log.msg("Listening socket has a connect to the client.")
        self.transport.write("Hey, welcome to the bridge server!\n".encode("utf-8"))
    def connectionLost(self, reason):
        """What happens when the connection is lost to the client."""
        print("Connection has been lost!")
        protocol = self.factory.irc_factory.mass_quit()

    def dataReceived(self, data):
        """Receive and react to data to the port."""
        data = data.decode("ascii")
        lines = data.split("\n")
        for l in lines:
            self.parse_line(l)
    def parse_line(self, line):
        """Make sense of the data coming into the server,
        dispatch to other methods."""
        try: obj = json.loads(line)
        except json.JSONDecodeError as e:
            log.msg("JSON error")
            #TODO: inform client about this error.
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
            protocol.relay_join_user(nick, channel)
        elif obj["command"] == "privmsg":
            nick = obj["nick"]
            destination = obj["destination"]
            message = obj["message"]
            protocol.relay_privmsg(nick, destination, message)
    def send(self, message):
        """Send messages back to client."""
        self.transport.write(message.encode())


class ListenFactory(Factory):
    protocol = ListenProtocol
    protocols = []
    def __init__(self, service):
        """Factory for the listening protocol.
        Doesn't really have to do much, since
        most of the logic is handled by the IRC factory."""
        self.service = service
    def buildProtocol(self, addr):
        self.my_protocol = self.protocol()
        self.my_protocol.factory = self
        return self.my_protocol


class ListenService(service.Service):
    def startService(self):
        service.Service.startService(self)

class IRCProtocol(IRC):
    def connectionMade(self):
        """What happens when a connection is made to the IRC network."""
        self.factory.protocols.append(self)
        log.msg("Connection made to IRC network.")
        self.register()
    def register(self):
        """Registers the server as an IRC server to the network."""
        self.sendLine("PASS {}".format(self.factory.service.password))
        self.sendLine("PROTOCTL NICKv2 VHP NICKIP UMODE2 SJOIN SJOIN2 SJ3 NOQUIT TKLEXT ESVID MLOCK")
        self.sendLine("PROTOCTL EAUTH={}".format(self.factory.service.name))
        self.sendLine("PROTOCTL SID={}".format(self.factory.service.sid))
        self.sendLine("SERVER {} 1 :{}".format(self.factory.service.name, self.factory.service.descr))
        self.sendLine(":{} EOS".format(self.factory.service.sid))
        self.test()
    def test(self):
        """Example code to test things as soon as start up happens."""
        self.relay_register_user("hank3", "hank3", "hank3", "hank3")
        self.relay_join_user("hank3", "#banana")
        

    def relay_register_user(self, nick, username, hostname, real_name):
        """Registers a user to the IRC network."""
        current_time = 0
        uid = self.factory.get_uid()
        line = ":{} UID {} 0 {} {} {} {}{} 0 +ixw {} * :{}".format(
            self.factory.sid, nick, current_time, username, 
            hostname, self.factory.sid, uid, self.factory.cloak, 
            real_name)
        self.sendLine(line)
        #params are the UID message after the command.  Last argument ends with : and 
        # can contain multiple spaces.
        parted = line.strip(":").partition(":")
        params = parted[0].split()[2:]
        params.append(parted[2])
        self.factory.add_new_user(params)
    def quit_user(self, uid, message="Quit"):
        """Quits a user from the IRC network."""
        line = ":{} QUIT :{}".format(uid, message)
        self.sendLine(line)
    def relay_join_user(self, nick, channel):
        """Joins a user to a channel."""
        # TODO: if themessage is sent by a server, a user WILL join that channel
        # regardless of a ban. Therefore, such checks need to be done here.
        # also, check if channel exists
        can_join = True
        if can_join:
            self.sendLine(":{} JOIN {}".format(nick, channel))
    def relay_privmsg(self, nick, destination, message):
        """Sends a message from a user to another user or channel."""
        self.sendLine(":{} PRIVMSG {} :{}".format(nick, destination, message))
    def irc_unknown(self, prefix, command, params):
        print("Unknown command: \033[31m{}\033[32m {}\033[33m {}\033[0m".format(prefix, command, " ".join(params)))
    def irc_NOTICE(self, prefix, params):
        """Prints out a NOTICE from the network."""
        notice = " ".join(params)
        print(prefix + " " + notice)
    def irc_PING(self, prefix, params):
        """Responds back to a PING (a check if we're still connected to network."""
        self.sendLine("PONG {}".format(params[0]))
    def irc_UID(self, prefix, params):
        """Responds to the network telling us about a user."""
        ick, hop, timestamp, username, hostname = params[0:5]
        uid, servicestamp, umodes, virthost, cloakedhost = params[5:10]
        ip, gecos = params[10:12]
        self.factory.add_new_user(params)
    def irc_SJOIN(self, prefix, params):
        """Responds to network telling us about what channels users are on."""
        timestamp, channel = params[:2]
        # IF no modes are set, positions are different
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
        """Handle the network telling us a user left a channel."""
        channel = params[0]
        self.factory.del_channel_user(channel, prefix)
        self.factory.list_channels()
    def irc_PRIVMSG(self, prefix, params):
        """Handle the network telling us about a message."""
        for p in self.factory.listen_factory.protocols:
            data = {}
            data["command"] = "privmsg"
            data["nick"] = prefix
            data["recipient"] = params[0]
            data["message"] = params[1]
            data = json.dumps(data)
            data += "\n"
            p.send(data)
    
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
        print("trying to set user")
        if self.get_by_nick(user[0]) or \
            self.get_by_uid(user[5]):
                print("failed because {}".format(user))
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
    protocols = []
    def __init__(self, service):
        self.service = service
        self.sid = self.service.sid
        self.cloak = self.service.cloak
    def buildProtocol(self, addr):
        self.protocol = IRCProtocol()
        self.protocol.factory = self
        return self.protocol
    def mass_quit(self):
        self.list_channels()
        for user in self.user_dict.users:
            if user[5].startswith(self.sid):
                print("quitting {}".format(user))
                self.quit_user(user)
        print("quit all the users")
        self.list_channels()
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
    def quit_user(self, user):
        uid = user[5]
        self.protocol.quit_user(uid)
        for k, v in self.channels.items():
            print(v[2])
            print(user)
            if user in v[2]:
                self.del_channel_user(k, user)

        pass
    def get_uid(self):
        """Returns an unused uid."""
#        while True:
#            if self.uid_counter not in self.uids.keys():
#                return str(self.uid_counter).zfill(6)
#            self.uid_counter += 1
        uid = 0
        while True:
            uid_text = self.sid + str(uid).zfill(6)
            if self.user_dict.get_by_uid(uid_text):
                uid += 1 
                continue
            return str(uid).zfill(6)

            

class IRCService(service.Service):
    def __init__(self, config):
        self.password = config["password"]
        self.name = config["name"]
        self.descr = config["description"]
        self.sid = config["sid"]
        self.cloak = config["cloak"]
    def startService(self):
        service.Service.startService(self)

