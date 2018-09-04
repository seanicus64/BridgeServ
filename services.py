from twisted.words.protocols.irc import IRC
from twisted.internet.protocol import ClientFactory, Factory
from twisted.application import service
from twisted.python import log
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver
from twisted.internet.defer import Deferred
import json
import string
import userdict
import channeldict
import random
class Error(Exception):
    pass
class UserError(Error):
    def __init__(self, message):
        self.message = message
class ListenProtocol(protocol.Protocol):
    def __init__(self):
        """Listens to clients (typically bots) that want to 
        connect to the IRC network through this bridge.
        Recieves formatted JSON.  Will translate JSON into
        IRC-legal commands to the server.  Also responsible
        for passing on IRC events back to the client."""
        log.msg("Listen protocol set up")
    def connectionMade(self):
        """When a client connects to the bridge, add it to the factory."""
        self.factory.protocols.append(self)
        log.msg("Listening socket has a connect to the client.")
    def connectionLost(self, reason):
        """What happens when the connection is lost to the client."""
        log.msg("Connection has been lost.")
        userdict = self.factory.irc_factory.userdict._users.copy()
        for u in userdict:
            #TODO: this should be by bridge_id
            if u.uid.startswith(self.factory.irc_factory.sid):
                for ch in self.factory.irc_factory.chandict:
                    if u in ch.users:
                        ch.part(u)
                self.factory.irc_factory.protocol.relay_quit(u.nick, "Lost connection with bridge.")
                del self.factory.irc_factory.userdict[u.uid]


                

    def dataReceived(self, data):
        """Receive and react to data to the port."""
        data = data.decode("ascii")
        data = data.strip()
        lines = data.split("\n")
        for l in lines:
            try:
                self.parse_line(l)
            except Exception as e:
            #TODO: send error messages to client
                print("\033[31mERROR:\033[0m")
                print(l)
                print(e.args)
                print("\033[31m----------\033[0m")
            
    def parse_line(self, line):
        """Make sense of the data coming into the server,
        dispatch to other methods."""
        obj = json.loads(line)
        assert type(obj) is dict
        obj = self.translation(obj)
        method_dict = {
            "register": self.handle_register,
            "quit": self.handle_quit,
            "get_users": self.handle_get_users,
            "get_channels": self.handle_get_channels,
            "part": self.handle_part,
            "join": self.handle_join,
            "privmsg_channel": self.handle_privmsg_channel
            }
        protocol = self.factory.irc_factory.protocol
        method_dict[obj["command"]](obj, protocol)
        return

    def translation(self, obj):
        """If the command has a link in it, add the actual object to it."""
        userdict = self.factory.irc_factory.userdict
        chandict = self.factory.irc_factory.chandict
        if "user_link_id" in obj.keys():
            user_link_id = obj["user_link_id"]
            user = userdict.get_by_link_id(user_link_id)
            obj["user"] = user
        if "channel_link_id" in obj.keys():
            channel_link_id = obj["channel_link_id"]
            channel = chandict.get_by_link_id(channel_link_id)
            obj["channel"] = channel
        return obj

    def handle_register(self, obj, protocol):
        nick = obj["nick"]
        username = obj["username"]
        hostname = obj["hostname"]
        realname = obj["realname"]
        response_id = obj["response_id"]

        uid = protocol.factory.get_uid()
        i = 0
        newnick = nick
        while True:
            try:
                assert not self.factory.irc_factory.userdict.nick_exists(newnick)
                break
            except:
                newnick = nick + "_" + str(i)
            i += 1
        nick = newnick
#        if not self.factory.irc_factory.userdict.islegal(nick):
#            nick = "temp_" + str(uid)
        link_id = protocol.factory.get_link_id()
        self.factory.irc_factory.userdict.append(uid, nick, username, hostname, realname, link_id)
        protocol.relay_register_user(uid, nick, username, hostname, realname)
        obj["nick"] = newnick
        obj["link_id"] = link_id
        self.send_response(obj)
        
    def handle_quit(self, obj, protocol):
        user = obj["user"]
        message = obj["message"]
        for channel in self.factory.irc_factory.chandict:
            for u in channel.users:
                if u == user:
                    channel.part(u)
        #TODO: delete user
        data = obj.copy()
        protocol.relay_quit(user.nick, message)
        self.send_response(data)

    def handle_get_users(self, obj, protocol):
        all_users = []
        for user in self.factory.irc_factory.userdict:
            u = (user.nick, user.user, user.host, user.real, user.link_id)
            all_users.append(u)
        data = obj.copy()
        data["all_users"] = all_users
        self.send_response(data)
    def handle_get_channels(self, obj, protocol):
        data = obj.copy()
        all_channels = []
        
        for chan in self.factory.irc_factory.chandict:
            ch = (chan.name, chan.topic, [u.nick for u in chan.users], chan.link_id, chan.alien_name)
            all_channels.append(ch)

        data["all_channels"] = all_channels
        self.send_response(data)
    def handle_part(self, obj, protocol):
        user = obj["user"]
        channel = obj["user"]
        message = obj["message"]
        nick = user.nick

        channel.part(user)
        protocol.relay_part(nick, channel.name, message)
        data = obj.copy()
        self.send_response(data)
    def handle_join(self, obj, protocol):
        user = obj["user"]
        channel = obj["channel"]
        nick = user.nick

        can_join = True

        protocol.relay_join_user(nick, channel.name)
        data = obj.copy()
        if can_join:
            channel.join(user)
            self.send_response(data)
    def handle_privmsg_channel(self, obj, protocol):
        data = obj.copy()
        user = obj["user"]
        channel = obj["channel"]
        message = obj["message"]
        nick = user.nick
        can_privmsg = True
        if can_privmsg:
            protocol.relay_privmsg(nick, channel.name, message)
            self.send_response(data)

    def send_response(self, data):
        """Send messages back to client."""
        data["type"] = "response"
        for string in ["user", "channel"]:
            try:
                del data[string]
            except:
                pass
        self.transport.write((json.dumps(data)+"\n").encode())
    def send_error(self, message):
        data = {}
        data["error"] = message
        self.send(data)
    def send_event(self, data):
        data["type"] = "event"
        self.transport.write((json.dumps(data)+"\n").encode())
        


class ListenFactory(Factory):
    protocol = ListenProtocol
    protocols = []
    index = 1
    def __init__(self, service):
        """Factory for the listening protocol.
        Doesn't really have to do much, since
        most of the logic is handled by the IRC factory."""
        self.service = service
        log.msg("Listen Factory set up")
    def buildProtocol(self, addr):
        self.my_protocol = self.protocol()
        self.my_protocol.factory = self
        self.my_protocol.bridge_id = self.index
        self.index += 1
        return self.my_protocol


class ListenService(service.Service):
    def startService(self):
        service.Service.startService(self)

class IRCProtocol(IRC):
    def __init__(self):
        log.msg("IRC protocol has been set up.")
    def connectionMade(self):
        """What happens when a connection is made to the IRC network."""
        log.msg("Connection has been made to IRC network.")
        self.factory.protocols.append(self)
        self.register()
    def register(self):
        """Registers the server as an IRC server to the network."""
        self.sendLine("PASS {}".format(self.factory.service.password))
        self.sendLine("PROTOCTL NICKv2 VHP NICKIP UMODE2 SJOIN SJOIN2 SJ3 NOQUIT TKLEXT ESVID MLOCK")
        self.sendLine("PROTOCTL EAUTH={}".format(self.factory.service.name))
        self.sendLine("PROTOCTL SID={}".format(self.factory.service.sid))
        self.sendLine("SERVER {} 1 :{}".format(self.factory.service.name, self.factory.service.descr))
        self.sendLine(":{} EOS".format(self.factory.service.sid))
        
    # This relay block takes messages from the client and propagates them to the IRC network.
    def relay_part(self, nick, channel, message):
        line = ":{} PART {} :{}".format(nick, channel, message)
        self.sendLine(line)
    def relay_quit(self, nick, message):
        line = ":{} QUIT :{}".format(nick, message)
        self.sendLine(line)

    def relay_register_user(self, uid, nick, username, hostname, real_name):
        """Registers a user to the IRC network."""
        #TODO: 
        current_time = 0
        # set -x off to turn off cloaking.  Cloaking isn't necessary over a bridge, and
        # disabling it makes it easier to see whom is connected over bridge.
        line = ":{} UID {} 0 {} {} {} {} 0 +iw-x * {} * :{}".format(
            self.factory.sid, nick, current_time, username, 
            hostname, uid, self.factory.cloak, 
            real_name)
        self.sendLine(line)

    def relay_quit_user(self, uid, message="Quit"):
        """Quits a user from the IRC network."""
        line = ":{} QUIT :{}".format(uid, message)
        self.sendLine(line)
    def relay_join_user(self, nick, channel):
        """Joins a user to a channel."""
        # TODO: if themessage is sent by a server, a user WILL join that channel
        # regardless of a ban. Therefore, such checks need to be done here.
        # also, check if channel exists

        # TODO: for now, alien users cannot create their own irc channels.
        # They must already exist on the IRC server AND be linked to the alien server
        #link = self.factory.chandict.find_link(channel)
        #if not link:
        #    return
        #channel = link
            
        can_join = True

        
        if can_join:
            self.sendLine(":{} JOIN {}".format(nick, channel))
        if can_join: 
            return True
            
    def relay_privmsg(self, nick, destination, message):
        """Sends a message from a user to another user or channel."""
        self.sendLine(":{} PRIVMSG {} :{}".format(nick, destination, message))
        return True

    # this irc_ block's methods are what is run when a command comes from the IRC side.
    # so it takes the IRC commands from the network and relays it BACK to the client
    def irc_EOS(self, prefix, params):
        #TODO: probably shouldnt allow anything until finished synching
        print("The chan dict is")
        print(self.factory.chandict)
    def irc_unknown(self, prefix, command, params):
        print("Unknown command: \033[31m{}\033[32m {}\033[33m {}\033[0m".format(prefix, command, " ".join(params)))
    def irc_NOTICE(self, prefix, params):
        #TODO: send to client
        """Prints out a NOTICE from the network."""
        notice = " ".join(params)
        print(prefix + " " + notice)
    def irc_KILL(self, prefix, params):
        del self.factory.userdict[params[0]]
    def irc_PING(self, prefix, params):
        """Responds back to a PING (a check if we're still connected to network."""
        self.sendLine("PONG {}".format(params[0]))
    def irc_UID(self, prefix, params):
        """Responds to the network telling us about a user."""
        nick, hop, timestamp, username, hostname = params[0:5]
        uid, servicestamp, umodes, virthost, cloakedhost = params[5:10]
        ip, gecos = params[10:12]
        try:
            self.factory.userdict.append(uid, nick, username, hostname, gecos)
        except:
            print("{} IS ALREADY USED".format((uid, nick)))
            print(self.factory.userdict)
        for p in self.factory.listen_factory.protocols:
            data = {}
            data["event"] = "uid"
            data["nick"] = nick
            data["username"] = username
            data["hostname"] = hostname
            data["realname"] = gecos
            p.send_event(data)
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


        try:
            chan_obj = self.factory.chandict[channel]
        except KeyError:
            chan_obj = channeldict.Channel(channel)
            self.factory.chandict.append(chan_obj)

        
        chan_users = []
        for u in users:
            uid = u.strip("@!+&~")
            if uid in self.factory.userdict:
                user = self.factory.userdict[uid]
                chan_users.append(user)
                chan_obj.join(user)
        
        for p in self.factory.listen_factory.protocols:
            data = {}
            data["event"] = "sjoin"
            data["nicks"] = [u.nick for u in chan_users]
            data["channel"] = channel
            p.send_event(data)
    def irc_QUIT(self, prefix, params):
        #TODO: send info to client
        del self.factory.userdict[prefix]

    def irc_PART(self, prefix, params):
        #TODO: send info to client
        """Handle the network telling us a user left a channel."""
        channel = params[0]
    def irc_PRIVMSG(self, prefix, params):
        #TODO: handle user PRIVMSGs
        """Handle the network telling us about a message."""
        for p in self.factory.listen_factory.protocols:
            data = {}
            data["type"] = "event"
            data["event"] = "privmsg"
            data["nick"] = prefix
            channel = params[0] 
            channel_link_id = None
            for ch in self.factory.chandict:
                if ch.name == channel:
                    channel_link_id = ch.link_id
                    break
            if not channel_link_id:
                return
            data["channel_link_id"] = channel_link_id
            data["recipient"] = params[0]
            data["message"] = params[1]
            p.send_event(data)
    def irc_JOIN(self, prefix, params):
        """Handle the network telling us about a join."""
        for p in self.factory.listen_factory.protocols:
            data = {}
            data["command"] = "join"
            data["nick"] = prefix
            data["channel"] = params[0]
            p.send_event(data)

class IRCFactory(ClientFactory):
    protocol = IRCProtocol
    uid_counter = 0
    link_id = 0
    uids = dict()
    userdict = userdict.Users()
    chandict = channeldict.Channels()
    protocol = None
    protocols = []
    def __init__(self, service):
        self.service = service
        self.sid = self.service.sid
        self.cloak = self.service.cloak

        # Set up the channel links for each bridge we will have connected
        self.link_sections = self.service.link_sections
        for bridge in self.service.link_sections:
            for e, l in enumerate(bridge):
                channel = channeldict.Channel(bridge[l], l, e)
                self.chandict._channels.append(channel)
        log.msg("IRC factory set up.")
    def get_link_id(self):
        self.link_id += 1
        return self.link_id
    def buildProtocol(self, addr):
        self.protocol = IRCProtocol()
        self.protocol.factory = self
        log.msg("IRC protocol built.")
        return self.protocol

    def get_uid(self):
        """Returns an unused uid."""
        uid = 0
        while True:
            uid = random.randrange(999999)
            uid_text = self.sid + str(uid).zfill(6)
            if uid_text in self.userdict:
                continue
            return uid_text

            

class IRCService(service.Service):
    def __init__(self, config, link_sections):
        self.password = config["password"]
        self.name = config["name"]
        self.descr = config["description"]
        self.sid = config["sid"]
        self.cloak = config["cloak"]
        self.link_sections = link_sections
        log.msg("IRC service set up.")
    def startService(self):
        service.Service.startService(self)

"""
TODO
links between channels
links between users

BridgeServ user
    list bridges
        (Discord1, reddit, gmail, Skype)
    links <bridge>
        (IRC#politics <-> Discord1#politics)
    link_channel <IRC> <not-IRC>
    info <bridge>
nick translation (mention of IRC name (sean_D) could turn into discord mention on other side)
    (obviously make this opt-in)


"""
