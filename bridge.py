import sys
sys.path.append(".")
from twisted.python import log
from twisted.internet import reactor
from services import IRCService, IRCFactory, ListenFactory, ListenService
from twisted.application import service, internet
import configparser

# get rid of "#" as a comment in the config file, because that will 
# probably be a very common one.
config = configparser.ConfigParser(comment_prefixes=(";"))
config.read("bridge.conf")
IRC_config = config["SERVER SETTINGS"]
_sections = list(filter(lambda section: 
            section.partition(" ")[0].lower() == "links", 
            config.sections()))
sections = [config[s] for s in _sections]

top_service = service.MultiService()
IRC_service = IRCService(IRC_config, sections)
IRC_service.setServiceParent(top_service)

connection_config = config["CONNECTION"]
irc_server = connection_config["irc_server"]
irc_port = int(connection_config["irc_port"])
irc_factory = IRCFactory(IRC_service)
tcp_service = internet.TCPClient(irc_server, irc_port, irc_factory)
tcp_service.setServiceParent(top_service)

bridge_server = connection_config["bridge_server"]
bridge_port = int(connection_config["bridge_port"])
listen_service = ListenService()
listen_service.setServiceParent(top_service)
listen_factory = ListenFactory(listen_service)
listen_tcp_service = internet.TCPServer(bridge_port, listen_factory, interface = bridge_server)
listen_tcp_service.setServiceParent(top_service)

irc_factory.listen_factory = listen_factory
listen_factory.irc_factory = irc_factory

if __name__ == '__main__':
    print("Please run from twistd")
else:
    application = service.Application("IRC bridge")
    top_service.setServiceParent(application)

log.msg("Everything loaded correctly")
