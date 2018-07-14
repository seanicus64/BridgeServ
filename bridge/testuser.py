class Foo:
    def __init__(self):
        self.users = []
    def __delitem__(self, key):
        self.users.remove(key)
    def __add__(self, toadd):
        self.users.append(toadd)
cat = Foo()
cat.users.append(34)
cat.users.append(2)
print(cat.users)
del cat[34]
print(cat.users)
cat + 999
print(cat.users)
