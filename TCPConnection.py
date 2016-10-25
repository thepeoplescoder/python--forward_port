from Connection import Connection

BUFFER_SIZE = 1024

# An object representing a TCP connection from a source.
class TCPConnection(Connection):

    # __init__ ############################################
    def __init__(self, sock, sockaddr):
        super(TCPConnection, self).__init__(sock, sockaddr)
        self.__i_can_receive_more = True                            # Yep.

    # i_can_receive_more ##################################
    def i_can_receive_more(self):
        """Can I get meaningful data from a call to receive()?"""
        return self.__i_can_receive_more

    # send ################################################
    def send(self, data):
        """Send data to the destination."""
        return self._socket.send(data)

    # receive #############################################
    def receive(self, BUFFER_SIZE=BUFFER_SIZE):
        """Receive data from the connection."""
        data = self._socket.recv(BUFFER_SIZE)                   # Get the data.
        self.__i_can_receive_more = len(data) >= BUFFER_SIZE    # Can we keep going?
        return data                                             # Okay, NOW return the data. :)

del BUFFER_SIZE
