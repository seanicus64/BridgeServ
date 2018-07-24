#!/usr/bin/env python3
class Channel:
    link = None
    name = ""
    topic = ""
    users = []
    def __repr__(self):
        return "<Channel: {}, link_id: {}, users: {}>".format(self.name, self.link_id, [u.nick for u in self.users])
    def __init__(self, name, alien_name=None, link_id=None):
        self.name = name
        self.alien_name = alien_name
        self.link_id = link_id

    def join(self, user):
        if user not in self.users:
            self.users.append(user)
    def part(self, user):
        if user in self.users:
            self.users.remove(user)
class Channels:
    _channels = []
    def __init__(self):
        
        pass
    def get_by_link_id(self, link_id):
        for ch in self._channels:
            if ch.link_id == link_id:
                return ch
        raise Exception("No such link id: {}".format(link_id))
    def find_link(self, link):
    
        for ch in self._channels:
            print("link: {} channel: {} channel.link: {}".format(link, ch, ch.link))
            if ch.link_id == link:
                return ch
        return None
    def append(self, channel):
        if channel not in self._channels:
            self._channels.append(channel)
    def __iter__(self):
        for ch in self._channels:
            yield ch
        return

    def __repr__(self):
        string = ""
        for ch in self._channels:
            string += str(ch) + "\n"
        return string
    def __getitem__(self, channame):
        for ch in self._channels:
            if channame == ch.name:
                return ch
        raise KeyError
