#!/usr/bin/env python3
import random
import sys
import discord
import configparser
import json
import asyncio

client = discord.Client()
config = configparser.ConfigParser()
config.read("bot.conf")
token = config["DEFAULT"]["discord_token"]

class Bridge_Client:
    is_connected = False
    discord_channel = None

    def __init__(self, discord_client, sync_future):
        self.discord_client = discord_client
        self.sync_future = sync_future

    async def connect_to_listener(self, host, port, loop, future):
        self.reader, self.writer = await asyncio.open_connection(host, port, loop=loop)
        future.set_result((self.reader, self.writer))

    async def test(self):
        name = "fred" + str(random.randrange(10000))
        await self.register_user(name, name, name, name)
        await self.join(name, "#banana")
        await self.privmsg(name, "#banana", "ACTION something")
        await self.privmsg(name, "#banana", "something")
        await self.privmsg(name, "#banana", "")
        await self.privmsg(name, "#banana", "fdas")
        await self.privmsg(name, "#banana", "")
        await self.privmsg(name, "#banana", "fda ")

    async def receive(self):
        await asyncio.wait_for(self.sync_future, None)
#        await self.test()
        while True:
            is_action = False
            line = await self.reader.readline()
            line = line.decode()
            try:
                data = json.loads(line)
            except: continue
            print(data)
            if data["command"] == "privmsg":
                await self.handle_privmsg(data["nick"], data["recipient"], data["message"])
                

    async def handle_privmsg(self, nick, destination, message):
        if message[0] == "\x01" and message[-1] == '\x01':
            message = message.strip("\x01")
            words = message.split()
            if words[0] == "ACTION":
                line_to_send = "*{} {}*".format(nick, " ".join(words[1:]))
                await self.discord_client.send_message(self.discord_channel, line_to_send)
                return
            # Let's skip other CTCP stuff for now
            else:
                return
        else:
            line_to_send = "**<{}>**: {}".format(nick, message)

        await self.discord_client.send_message(self.discord_channel, line_to_send)


    async def send(self, message):
        message += "\n"
        self.writer.write(message.encode())

    async def authenticate(self):
        data = {}
        data["command"] = "authenticate"
        data["password"] = config["DEFAULT"]["bridge_password"]
        data = json.dumps(data)
        await self.send(data)

    async def register_user(self, nick, username, hostname, realname):
        data = {}
        data["command"] = "register"
        data["nick"] = nick
        data["username"] = username
        data["hostname"] = hostname
        data["realname"] = realname
        #print("Sent {}".format(data))
        data = json.dumps(data)
        await self.send(data)

    async def join(self, nick, channel):
        data = {}
        data["command"] = "join"
        data["channel"] = channel
        data["nick"] = nick
        data = json.dumps(data)
        await self.send(data)
    async def privmsg(self, nick, recipient, message):
        data = {}
        data["command"] = "privmsg"
        data["nick"] = nick
        data["destination"] = recipient
        data["message"] = message
        data = json.dumps(data)
        print(data)
        await self.send(data)
def fix_nick(nick):
    number = random.randrange(10000)
    nick = nick.strip()
    nick = nick.replace(" ", "_")
    nick += "_"
#    nick += str(number)
    nick += "D"
    return nick


@client.event 
async def on_message(message):
    if message.author == client.user:
        return
    nick = nick_translation[message.author]
    content = message.clean_content
    await bridge_client.privmsg(nick, "#banana", content)

@client.event
async def on_ready():
    members = list(client.get_all_members())
    for m in members:
        newnick = fix_nick(m.name)
        nick_translation[m] = newnick
        await bridge_client.register_user(newnick, "discord", "discord", "discord")
        await bridge_client.join(newnick, "#banana")

    for c in client.get_all_channels():
        if c.name == "bot-test":
            bridge_client.discord_channel = c
            break
    sync_future.set_result(True)
#    await bridge_client.send("hello world 12345")
nick_translation = {}

loop = asyncio.get_event_loop()
sync_future = asyncio.Future()
bridge_client = Bridge_Client(client, sync_future)
future = asyncio.Future()

task1 = asyncio.ensure_future(client.login(token))
task2 = asyncio.ensure_future(bridge_client.connect_to_listener("127.0.0.1", 5959, loop, future))
loop.run_until_complete(asyncio.wait((task1, task2)))

task1 = asyncio.ensure_future(client.connect())
task2 = asyncio.ensure_future(bridge_client.receive())
tasks = [task1, task2]
loop.run_until_complete(asyncio.wait(tasks))
