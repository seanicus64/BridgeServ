#!/usr/bin/env python3
import string
class User(object):
    def __init__(self, uid, nick, user, host, real, alien_id = None):
        # alien_id is a unique string assigned by whatever the foreign service is
        # to identify it, it always begins with "="
        self._user_list = None
        self.uid = uid
        self.nick = nick
        self.user = user
        self.host = host
        self.real = real
        self.alien_id = alien_id
    def __setattr__(self, name, value):
        if name == "uid" and self._user_list:
            return
        if name == "nick" and self._user_list:
            if value in self._user_list:
                return
        super().__setattr__(name, value)


    def __eq__(self, key):
        if key == self.uid or key == self.nick:
            return True
        return False
    def __repr__(self):
        return "([{}:{}] {} {} {} :{})".format(self.uid, type(self.uid), self.nick, self.user, self.host, self.real)

class Users:
    def __init__(self):
        self._users = list()

#    def append(self, user):
    def islegal(self, nick):
        allowed = string.ascii_letters + string.digits + "_-|[]\\`^{}"
        for char in nick:
            if char not in allowed:
                print("char not allowed: {}".format(char))
                return False
        if nick.startswith("-") or nick[0].isdigit():
            print("bad start digit")
            return False
        if len(nick) > 30:
            print("too long")
            return False
        print("is legal")
        return True
    def append(self, uid, nick, user, host, real, alien_id = None):
        user = User(uid, nick, user, host, real, alien_id = None)
        if user in self._users:
            raise KeyError
        self._users.append(user)
        user._user_list = self

    def __delitem__(self, key):
        if key in self._users:
            self._users.remove(key)

    def __contains__(self, value):
        for u in self._users:
            if u == value:
                return True
        return False
    def __repr__(self):
        return " ".join([str(u) for u in self._users])
            
    def __getitem__(self, key):
        if key in self:
            for u in self._users:
                if u == key:
                    return u
        raise KeyError

            
