#!/usr/bin/env python3
import string
class User(object):
    def __init__(self, uid, nick, user, host, real, link_id = None, bridge_id = 0):
        self._user_list = None
        self.uid = uid
        self.nick = nick
        self.user = user
        self.host = host
        self.real = real
        self.link_id = link_id
        self.bridge_id = bridge_id
    def __setattr__(self, name, value):
        if name == "uid" and self._user_list:
            raise KeyError
        if name == "nick" and self._user_list:
            if value in self._user_list:
                raise KeyError
        super().__setattr__(name, value)


    def __eq__(self, key):
        if self.uid == key:
            return True
        return False
    def __repr__(self):
        return "([{}] {} {} {} :{} <{}>)".format(self.uid, self.nick, self.user, self.host, self.real, self.link_id)

class Users:
    def __init__(self):
        self._users = list()

    def get_link(self, alien):
        for user in self._users:
            if user.link_id == alien:
                return user
        return None
        
    def get_by_nick(self, nick):
        for u in self._users:
            if u.nick == nick:
                return u
        raise Exception("No such nick in userlist: {}".format(nick))
    def get_by_link_id(self, link_id):
        if not link_id:
            raise Exception("link_id can't be None")
        for u in self._users:
            if u.link_id == link_id:
                return u
        raise Exception("No such link_id: {}".format(link_id))
    def islegal(self, nick):
        allowed = string.ascii_letters + string.digits + "_-|[]\\`^{}"
        for char in nick:
            if char not in allowed:
                return False
        if nick.startswith("-") or nick[0].isdigit():
            return False
        if len(nick) > 30:
            return False
        return True
    def nick_exists(self, nick):
        if nick in [u.nick for u in self._users]:
            return True
        return False
    def append(self, uid, nick, user, host, real, link = None):
        user = User(uid, nick, user, host, real, link)
        if self.nick_exists(nick):
            raise KeyError("nick {} is already in userdict".format(nick))
        if user in self._users:
            raise KeyError("uid {} is already in userdict".format(uid))

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
            
    def __iter__(self):
        for item in self._users:
            yield item
    def __getitem__(self, key):
        if key in self:
            for u in self._users:
                if u == key:
                    return u
        raise KeyError

            
