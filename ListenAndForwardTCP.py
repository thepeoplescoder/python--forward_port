import functools
import socket
from six import print_ as _print
from ListenAndForward import ListenAndForward, ThreadingMixIn
from TCPConnection import TCPConnection

# Listening and forwarding via TCP.
class ListenAndForwardTCP(ListenAndForward):
    def __init__(self, my_address, dest_address, **kwargs):
        super(ListenAndForwardTCP, self).__init__(my_address, dest_address)
        self.__server_socket = None
        self.__backlog = kwargs.get("backlog", 5)

        # Set a callback if we were given one.
        log_data_callback = kwargs.get("log_data", kwargs.get("log_data_callback", None))
        if log_data_callback:
            self.log_data = functools.partial(log_data_callback, self)

    # get_server_socket ###################################
    def get_server_socket(self):
        """The process for creating a server socket.  There should be
        one server socket instance per instance of this class.  Subsequent
        calls to this method must return the same object.

        Subclasses that override this method are NOT allowed to use get_my_address(),
        but instead are required to use the _my_address variable to create the
        socket, then subsequently update _my_address to the information reflected
        by the actual socket object, e.g. by a call to socket.getsockname().
        """

        # Create a server socket if one doesn't exist.
        if not self.__server_socket:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(self._my_address)         # This variable is reliable at the moment.
            sock.listen(self.__backlog)
            del self.__backlog                  # We don't need this anymore.

            # Cool.  We never have to do this again.
            self.__server_socket = sock

            # Update our address.
            self._my_address = sock.getsockname()[:2]

        # Return the saved socket.
        return self.__server_socket

    # get_new_source_connection ###########################
    def get_new_source_connection(self):
        """Get a connection from the host sending data to us."""
        return TCPConnection(*self.get_server_socket().accept())

    # get_new_destination_connection ######################
    def get_new_destination_connection(self):
        """Get a connection to the host we will be sending data to."""
        dest_address = self.get_destination_address()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(dest_address)
        return TCPConnection(sock, dest_address)

# A version of ListenAndForwardTCP that supports threading.
class ListenAndForwardTCPThreading(ThreadingMixIn, ListenAndForwardTCP):
    def __init__(self, my_address, dest_address, **kwargs):

        # analyze keyword arguments first
        ListenAndForward = kwargs.get("ListenAndForward", ListenAndForwardTCP)
        daemon           = kwargs.get("daemon", kwargs.get("is_daemon", False))

        # Okay, now let's call our superconstructors. :)
        ThreadingMixIn.__init__(self, daemon, ListenAndForward)
        ListenAndForwardTCP.__init__(self, my_address, dest_address, kwargs)
