import six

from closureutil import WrappedClosure

# An "abstract" representation of a connection.
Connection = None                   # In the event that I want to rename
class Connection(six.Iterator):     # this class, I only have to change the name
    _Self = lambda: Connection      # in three places.

    # __init__ ############################################
    @WrappedClosure
    def __init__(Self=_Self):
        # This is the actual constructor.  I put it in a closure so
        # I can get a reference to this exact class for the type check.
        def __init__(self, sock, sockaddr):
            if type(self) is Self():
                raise TypeError("Direct instantiation of this class is prohibited.")

            self._socket_address = sockaddr
            self._socket = sock

        # Return the actual constructor to the caller.
        return __init__

    # __iter__ ############################################
    def __iter__(self):
        """Connection objects are iterators."""
        return self

    # __str__ #############################################
    def __str__(self):
        return repr(self._socket_address)

    # __repr__ ############################################
    def __repr__(self):
        """String representation of a Connection object."""
        return "<%s%s at %x>" % (type(self).__name__, self, id(self))

    # __next__ ############################################
    def __next__(self):
        """Iterator behavior."""
        if not self.i_can_receive_more():       # Crap out or...
            raise StopIteration
        return self.receive()                   # ...keep receiving data.

    # close ###############################################
    def close(self):
        """Closes this connection object."""
        self._socket.close()

    # i_can_receive_more ##################################
    def i_can_receive_more(self):
        """Can I get meaningful results from receive()?"""
        return False

    # receive #############################################
    def receive(self):
        """Receive data from the connection."""
        raise NotImplementedError("Please override this method in a subclass.")

    # send ################################################
    def send(self, data):
        """Send data over the connection."""
        raise NotImplementedError("Please override this method in a subclass.")

    # This should be called before the first WrappedClosure method
    # is actually needed.
    WrappedClosure.unwrap_all(locals())
