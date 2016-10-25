import six

# An "abstract" representation of a connection.
Connection = None
class Connection(six.Iterator):
    _Self = lambda: Connection

    # __init__ ############################################
    def __init__(self, sock, sockaddr, Self=_Self):
        if type(self) is Self():
            raise TypeError("Direct instantiation of this class is prohibited.")

        self._socket_address = sockaddr
        self._socket = sock

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
