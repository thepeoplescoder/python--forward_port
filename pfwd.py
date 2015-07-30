#!/usr/bin/python

# Imports
import threading
import socket
import sys
import tempfile
import os
import warnings

# Personal imports
import devnull
from dummysocket import DummySocket

# Some warnings can be annoying.  Uncomment this to disable them.
# warnings.simplefilter("ignore")

# Some Python 3 stuff.
if sys.version_info[0] > 2:
    basestring = str                # basestring only exists in Python 2.x

#################
#               #
#   Functions   #
#               #
#################

# coalesce ###################################################################
def coalesce(obj, f_expr):
    return obj if obj else f_expr()

# to_address #################################################################
def to_address(addr):
    """Converts a socket address or port to a tuple.  Tuples are assumed to be valid.

    This method takes tuples, strings, and integers.  The function's return
    value should be of the form (host_or_ip, port_number).

    Acceptable strings are in the form of "host_or_ip:port_number".
    Tuples must be of length 2.  Tuples are returned unmodified.
    If a single integer X is passed, then this function returns ("", X).
    """

    # If this is a string, convert it to a valid tuple: (address, port)
    if isinstance(addr, basestring):
        addr = tuple(addr.split(':')[:2])
        addr[1] = int(addr[1])

    # If we have an integer, treat it like a port available on all interfaces.
    elif isinstance(addr, int):
        addr = ("", addr)

    # This function MUST return a tuple of length 2.
    if isinstance(addr, tupble) and len(addr) == 2:
        return addr
    else:
        raise TypeError("A tuple of length 2 was expected here.")

# new_socket #################################################################
def new_socket(*args):
    """Creates a new socket.

    I know I can instantiate sockets directly, but in the event I wish to
    change the logic of how every socket is created, I can implement those
    changes here, instead of changing every line of code where a socket is
    created.
    """
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

###############
#             #
#   Classes   #
#             #
###############

################
# BaseThreadEx #
################
class BaseThreadEx(threading.Thread):

    # Constructor ############################################################
    def __init__(self):
        threading.Thread.__init__(self)
        self.__should_stay_alive = True

    # should_stay_alive ######################################################
    def should_stay_alive(self):
        """If your thread is running in a loop, use this to determine whether
        or not it should stay alive."""
        return self.__should_stay_alive

    # kill_passively #########################################################
    def kill_passively(self):
        """States the intent that you no longer want this thread to run."""
        self.__should_stay_alive = False

##################
# IndirectSocket #
##################
class IndirectSocket(object):
    """Adds another level of indirection to a socket object.

    My justification for having a class such as this is because the full
    duplex communication will be done using a pair of SocketBridge objects that
    will ultimately be sharing the same socket objects, and this simplifies
    the disposal logic.
    """

    # Constructor ############################################################
    def __init__(self, sock=None):
        if not isinstance(sock, socket.socket):
            sock = DummySocket.SOCKET

        assert isinstance(sock, socket.socket)
        self.__socket = sock

    # socket #################################################################
    def socket(self):
        """The socket object associated with this IndirectSocket."""
        return self.__socket

    # is_valid_socket ########################################################
    def is_valid_socket(self):
        """Returns true if this object refers to a valid socket, otherwise false."""
        return isinstance(self.socket(), socket.socket) and \
               not isinstance(self.socket(), DummySocket)

    # close ##################################################################
    def close(self):
        """Invalidates this object and closes the associated socket."""
        self.socket().close()
        self.__socket = DummySocket.SOCKET

################
# SocketBridge #
################
class SocketBridge(BaseThreadEx):

    # Constructor ############################################################
    def __init__(self, recv_sock, send_sock, buffer_size=512):
        BaseThreadEx.__init__(self)

        # Convert any sockets to indirect sockets.
        if isinstance(recv_sock, socket.socket):
            recv_sock = IndirectSocket(recv_sock)
        if isinstance(send_sock, socket.socket):
            send_sock = IndirectSocket(send_sock)

        assert isinstance(recv_sock, IndirectSocket)
        assert isinstance(send_sock, IndirectSocket)
        assert isinstance(buffer_size, int)

        self.__recv_socket_indirect = recv_sock
        self.__send_socket_indirect = send_sock
        self.__buffer_size          = buffer_size
        self.__twin                 = None

    # get_recv_socket_indirect ###############################################
    def get_recv_socket_indirect(self):
        """Gets the "recv" IndirectSocket object associated with this bridge."""
        return self.__recv_socket_indirect

    # get_send_socket_indirect ###############################################
    def get_send_socket_indirect(self):
        """Gets the "send" IndirectSocket object associated with this bridge."""
        return self.__send_socket_indirect

    # get_recv_socket ########################################################
    def get_recv_socket(self):
        """Gets the actual "from" socket."""
        return self.get_recv_socket_indirect().socket()

    # get_send_socket ########################################################
    def get_send_socket(self):
        """Gets the actual "send" socket."""
        return self.get_send_socket_indirect().socket()

    # close ##################################################################
    def close(self):
        """Closes this bridge, releasing its associated sockets."""
        self.get_recv_socket_indirect().close()
        self.get_send_socket_indirect().close()

    # is_valid_bridge ########################################################
    def is_valid_bridge(self):
        """Checks to see if this bridge is valid.

        A valid bridge is a bridge such that its send and recv sockets are
        not dummy sockets.
        """
        return self.get_recv_socket_indirect().is_valid_socket() and \
               self.get_send_socket_indirect().is_valid_socket()

    # is_valid_twin ##########################################################
    def is_valid_twin(self, t):
        """Checks to see if the given SocketBridge is a potential twin.

        The constraint is that this SocketBridge's direction of communication
        must move in the exact opposite of the other SocketBridge's
        direction.  Also, they must use the same IndirectSocket objects.
        """
        if isinstance(t, type(self)):
            if self.get_recv_socket_indirect() is t.get_send_socket_indirect():
                if self.get_send_socket_indirect() is t.get_recv_socket_indirect():
                    return True
        return False

    # get_twin ###############################################################
    def get_twin(self):
        """Gets the "twin" SocketBridge associated with this instance."""
        return self.__twin

    # set_twin ###############################################################
    def set_twin(self, t=None):
        """Sets the twin for this SocketBridge, if it is a potential twin.

        The other SocketBridge object uses this object as its twin.  If a twin
        object is not provided, one is automatically created and set.  If a twin
        is already set, this method does nothing.

        Returns the value of t.  If no twin is set, and t is not provided,
        then this method returns the reference to the newly created twin.
        """

        if self.get_twin() is None:
            t = coalesce(t, self.create_twin)

            assert self.is_valid_twin(t)

            self.__twin = t
            t.__twin    = self

        return t

    # create_twin ############################################################
    def create_twin(self):
        """Creates a twin SocketBridge object that conforms to the constraints
        required to be a valid twin.

        Until a twin is actually set, this method will continue to create a
        completely new twin object.  The work to prevent this did not seem
        worthwhile.
        """

        if self.get_twin() is not None:
            return self.get_twin()

        # Ensure that the twin is of the same type as the original.
        else:
            return type(self)(self.get_send_socket_indirect(),
                              self.get_recv_socket_indirect())

    def get_buffer_size(self):
        return self.__buffer_size

    def __recv(self):
        return self.get_recv_socket().recv(self.get_buffer_size())

    def __send(message):
        return self.get_send_socket().send(message)

    # wait_for_new_data_and_send #############################################
    def wait_for_new_data_and_send(self):
        bytes_sent = 0
        data = self.__recv()
        if data:
            bytes_sent = self.__send(data)
        return bytes_sent

    def run(self):
        while self.should_stay_alive():
            self.wait_for_new_data_and_send()


####################
# SocketBridgePair #
####################
class SocketBridgePair(object):

    # Constructor ############################################################
    def __init__(self, primary, secondary=None):
        assert isinstance(primary, SocketBridge) and primary.get_twin() is None

        secondary = coalesce(secondary, primary.create_twin)

        # This will force us to error out if the secondary
        # bridge is not a twin of the first.
        self.__primary_bridge   = primary
        self.__secondary_bridge = primary.set_twin(secondary)

    # get_primary ############################################################
    def get_primary(self):
        """Gets the primary SocketBridge object.

        The only difference between the primary and secondary SocketBridge
        objects is their direction of communication.  Neither object has
        priority over the other.
        """
        return self.__primary_bridge

    # get_secondary ##########################################################
    def get_secondary(self):
        """Gets the secondary SocketBridge object.

        The only difference between the primary and secondary SocketBridge
        objects is their direction of communication.  Neither object has
        priority over the other.
        """
        return self.__secondary_bridge

    # close ##################################################################
    def close(self):
        """Closes this SocketBridgePair.

        Since both SocketBridge objects refer to the same IndirectSocket
        objects, closing one SocketBridge has the effect of automatically
        closing the other.
        """
        self.get_primary().close()

############################
# PortToSocketBridgeServer #
############################
class PortToSocketBridgeServer(BaseThreadEx):
    """A class that bridges inbound ports with outbound sockets.

    Each port that we listen to needs to be tied to its own thread so
    we can listen on several ports simultaneously.
    """

    # Constructor ############################################################
    def __init__(self, in_address, out_address, listen=5):
        BaseThreadEx.__init__(self)

        # Outbound socket information.
        self.__out_address      = to_address(out_address)

        # Get all meaningful information needed to create a socket to listen on.
        self.__server_address     = to_address(in_address)
        self.__server_listen      = listen
        self.__server_socket      = None

        # Prepare a socket to listen on the inbound port.
        self.__create_server_socket()

    # __create_server_socket #################################################
    def __create_server_socket(self):
        """Creates the server socket, if one doesn't already exist."""
        if self.__server_socket is None:
            self.__server_socket = new_socket()
            self.__server_socket.bind(self.__server_address)
            self.__server_socket.listen(self.__server_listen)

    def __create_outbound_socket(self):
        s = new_socket()
        s.connect(self.__out_address)

    def __wait_for_new_socket_bridge_pair(self):
        in_sock, in_addr = self.get_server_socket().accept()
        out_sock = self.__create_outbound_socket()
        return (in_addr, SocketBridgePair(SocketBridge(in_sock, out_sock)))

    def get_server_socket(self):
        return self.__server_socket
