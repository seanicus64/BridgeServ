Summary
======================
Bridgeserv is an IRC service that allows IRCops to manage bridges to other chat services.



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

    python3 bridge.py

BridgeServ should now be up and running.  It won't actually *do* much though until you run a client such as BridgeDiscord.

