#!/usr/bin/env python3
import asyncio
import configparser
import discord
import api
my_api = api.API("127.0.0.1", 5959)
client = discord.Client()
config = configparser.ConfigParser()
config.read("bot.conf")
token = config["DEFAULT"]["discord_token"]

async def my_background_task():
    while True:
        lines = my_api.receive()
        for l in lines:
            print(l)
        
        # need an await here so rest of program can run
        # (i.e., can't rely on delay from select() in 
        # api.receive())
        await asyncio.sleep(.05)

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    content = message.clean_content
    nick = message.author.display_name
    try:
        my_api.privmsg(nick, "#banana", content)
    except:
        pass

    
@client.event
async def on_ready():
    members = list(client.get_all_members())
    for m in members:
        print("display_name: {}, name: {}, nick: {}".format(m.display_name, m.name, m.nick))
#        nick = m.display_name
        nick = m.nick if m.nick else m.display_name
        try:
            my_api.register_user(nick, m.id, "{}@discordbridge".format(m.name), m.name)
        except:
            pass

        my_api.join(nick, "#banana")
            

print(token)
    
#loop = asyncio.get_event_loop()
#sync_future = asyncio.Future()
#client.login(token)
client.loop.create_task(my_background_task())

client.run(token)
