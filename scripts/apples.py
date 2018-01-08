class Apple(object):
    pass


def send_message(message):
    d = Deferred()
    
    # Pretend this is doing some I/O instead of just saying call this function
    # in 3 seconds.
    # In this example the Event loop, which is the thing that happens when you
    # do reactor.run() will eventually (in 3.5) seconds, call d.callback(True)
    # or d.callback(None) depending on the message. In the I/O case it would 
    # be a protocol doing this because the eventloop saw some more data and
    # called the protocl methods, instead of a call later.
    if message == "do you have apples":
        reactor.callLater(3.5, d.callback, True)
    else:
        reactor.callLater(3.5, d.callback, [Apple(), Apple(), Apple()])

    return d


def ask_if_apples():
    # send_message would return a Deferred, at this point the value is nothing
    # because it hasn't resolved it.
	has_apples_d = send_message("do you have apples")

    # We're just returning the Deferred, because we don't know what to do with
    # it yet.
	return has_apples_d

def possibly_request_apples(has_apples):
    # At this point, we know that the ask_if_apples function has returned
    # and gotten the value that was passed to callback() (assuming nothing else
    # in the callback chain has modified the return value since then.
	if has_apples:
		requested_d = send_message("I would like 3 apples")
        requested_d.addCallback(lambda _: print("Pretend I did something with the apples"))



d = ask_if_apples()
d.addCallback(possibly_request_apples)
