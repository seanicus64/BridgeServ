Summary
======================
Bridgeserve is an IRC service that allows IRCops to manage bridges to other chat services.

A *bridge* is a logical connection between the IRC network as a whole, and the other chat service.  An example of this would be a bridge between AlphaIRC and BetaDiscord.  BetaDiscord, because it is not part of our IRC network, is known as the *alien service*.  This bridge is comprised of different *links*, which is a one-to-one correspondence between an entity on one side of the bridge, and an entity on the other.  There are two types of links, *user links* and *channel links*.  A channel link connects an IRC channel with the alien channel or chat room, for example, #politics on AlphaIRC may be linked to #us-politics on BetaDiscord.  A message sent on #us-politics on BetaDiscord will be sent as a message to #politics on AlphaIRC.  

The other type of link is a user link, which connects a user of the alien service with a user on the IRC network.  These users are not already existing, but are created dynamically by BridgeServ. So when l33thacker joins BetaDiscord, an IRC user, perhaps with the nick "elitehacker" will registers to AlphaIRC.  

The advantages of this are clear after small deliberation, especially after considering the alternative (a simple traditional IRC bot simply relaying the messages).  First, it becomes clear to the IRC users which visitors are present simply by looking at the nick list.  Secondly, the chanops and IRCops will find it easier to ban and kick since the users are actually there.  Tabcompletion will actually work.  

Also, of course, Bridgeserv could help span *many* different chat services or protocols, the only real limitation being trust in the clients.  With Bridgeserv, an IRC network could allow 5 Discord servers, 3 slack servers, Twitter, Facebook, Skype, Twitch chat, two Minecraft servers, Usenet, forum discussion threads, or whatever possible way to communicate onto the servers, all simultaneously, although care has to be dedicated towards organization.  You can program a client for these alien services using the simple API.


Installation
==================================

Prerequisites
--------------------------------
* Configured and running UnrealIRCD server using 4.0.16 or greater.
* Twisted 18.4.0 or higher
* (Optional) a client using [BridgeAPI](https://github.com/seanicus64/BridgeAPI) such as [BridgeDiscord](https://github.com/seanicus64/BridgeDiscord).

BridgeServ Configuration
------------
First we need to configure Bridgeserv.  We need to edit our conf file.

    cp example.conf bridge.conf

Under [CONNECTION] change server to point to the domain name of the IRC server we want to link to.  This is probably localhost on our local machine.  Port is therefore 6667.

Under [SERVER SETTINGS] change **name** to whatever you want to call this server.  It must end with a TLD, like .com or .net, even if it doesn't resolve to a real IP.

**password** is the password this service will use to identify with the rest of the IRC network.

**sid** is the ID number for this server.  This is three characters long, first is a digit and next two are alphanumeric.  It's only important it's not being used by another server on the network.

**cloak** will be the string used to hide hostnames of people connected to our server

UnrealIRC Configuration
-----------

In your UnrealIRCD config file, create the following block:

    link bridgeserv.tld
    {
        incoming {
            mask *;
        };
        password "change_me";
        class servers;
    };

In which "bridge.tld" should be changed to **name**, and the password should be the same as **password**.

Running
----------------

Rehash UnrealIRCD.  Navigate to your unrealircd installation directory and run:

    ./unrealircd rehash

Next start up BridgeServ.  In your BridgeServ directory:

    ./quickrun.sh

BridgeServ should now be up and running.  It won't actually *do* much though until you run a client such as BridgeDiscord.



aaa
