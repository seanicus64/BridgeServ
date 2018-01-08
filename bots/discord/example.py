#!/usr/bin/env python3
from twisted.internet.defer import Deferred
from twisted.internet import reactor
import random
def is_it_used(nick):
    answer = random.choice([True, False])
    #if not answer:
    #    bad_nick(nick)
    #else:
    #    good_nick(nick)
    return answer
def register(name):

    print("REGISTER {}".format(name))
    reactor.callLater(1.0, is_it_used, name)
def bad_nick(nick):
    # add an underscore and try registering again
    pass
def good_nick(nick):
    pass

def register_users():
    d_dict = {}
    for u in users:
        d = Deferred()
        d.addCallback(register)
        d_dict = 
        register(u) 

initial_users = [
    "abby", "bobby", "charlie", "dave"]
users = []
for j in range(20):
    for i in initial_users:
        users.append(i+str(j))

reactor.callLater(.01, register_users)
reactor.run()
