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

##################
# to_socket_type #
##################
def to_socket_type(trans_type):
    """Converts a "transmission type" string to a socket.SOCK_* constant."""

    # Logic used to see if the transmission type is explicitly UDP.
    def is_definitely_udp(tt):
        if isinstance(tt, basestring):
            tt = tt.lower()
        return tt == "udp" or tt == socket.SOCK_DGRAM

    # Default to TCP.  UDP must be explicitly specified.
    if is_definitely_udp(trans_type):
        return socket.SOCK_DGRAM
    else:
        return socket.SOCK_STREAM

##############
# to_address #
##############
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

############################
# initialize_server_socket #
############################
def initialize_server_socket(sock, address_or_port, listen):
    assert isinstance(sock, socket.socket)
    if sock is not None:
        sock.bind(to_address(address_or_port))
        sock.listen(listen)

###############
#             #
#   Classes   #
#             #
###############

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
class SocketBridge(object):

    # Constructor ############################################################
    def __init__(self, fsock, tsock):

        # Convert any sockets to indirect sockets.
        if isinstance(fsock, socket.socket):
            fsock = IndirectSocket(fsock)
        if isinstance(tsock, socket.socket):
            tsock = IndirectSocket(tsock)

        assert isinstance(fsock, IndirectSocket)
        assert isinstance(tsock, IndirectSocket)

        self.__from_socket_indirect = fsock
        self.__to_socket_indirect   = tsock
        self.__twin                 = None

    # get_from_socket_indirect ###############################################
    def get_from_socket_indirect(self):
        """Gets the "from" IndirectSocket object associated with this bridge."""
        return self.__from_socket_indirect

    # get_to_socket_indirect #################################################
    def get_to_socket_indirect(self):
        """Gets the "to" IndirectSocket object associated with this bridge."""
        return self.__to_socket_indirect

    # get_from_socket ########################################################
    def get_from_socket(self):
        """Gets the actual "from" socket."""
        return self.get_from_socket_indirect().socket()

    # get_to_socket ##########################################################
    def get_to_socket(self):
        """Gets the actual "to" socket."""
        return self.get_to_socket_indirect().socket()

    # close ##################################################################
    def close(self):
        """Closes this bridge, releasing its associated sockets."""
        self.get_from_socket_indirect().close()
        self.get_to_socket_indirect().close()

    # is_valid_bridge ########################################################
    def is_valid_bridge(self):
        """Checks to see if this bridge is valid.

        A valid bridge is a bridge such that its to and from sockets are
        not dummy sockets.
        """
        return self.get_from_socket_indirect().is_valid_socket() and \
               self.get_to_socket_indirect().is_valid_socket()

    # is_valid_twin ##########################################################
    def is_valid_twin(self, t):
        """Checks to see if the given SocketBridge is a potential twin.

        The constraint is that this SocketBridge's direction of communication
        must move in the exact opposite of the other SocketBridge's
        direction.  Also, they must use the same IndirectSocket objects.
        """
        if isinstance(t, SocketBridge):
            if self.get_from_socket_indirect() is t.get_to_socket_indirect():
                if self.get_to_socket_indirect() is t.get_from_socket_indirect():
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
            if t is None:
                t = self.create_twin()

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
        else:
            return SocketBridge(self.get_to_socket_indirect(),
                                self.get_from_socket_indirect())

####################
# SocketBridgePair #
####################
class SocketBridgePair(object):

    # Constructor ############################################################
    def __init__(self, primary, secondary=None):
        assert isinstance(primary, SocketBridge) and primary.get_twin() is None

        if secondary is None:
            secondary = primary.create_twin()

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
class PortToSocketBridgeServer(threading.Thread):
    """A class that bridges inbound ports with outbound sockets."""

    # Constructor ############################################################
    def __init__(self, in_trans_type, in_address, out_trans_type, out_address, listen=5):
        threading.Thread.__init__(self)

        # Outbound socket information.
        self.__out_socket_type  = to_socket_type(out_trans_type)
        self.__out_address      = to_address(out_address)

        # Get all meaningful information needed to create a socket to listen on.
        self.__server_socket_type = to_socket_type(in_trans_type)
        self.__server_address     = to_address(in_address)
        self.__server_listen      = listen
        self.__server_socket  = None

        # Prepare a socket to listen on the inbound port.
        self.__create_server_socket()

    # __create_server_socket #################################################
    def __create_server_socket(self):
        """Creates the server socket, if one doesn't already exist."""
        if self.__server_socket is None:
            self.__server_socket = socket.socket(socket.AF_INET,
                                                 self.__server_socket_type)
            initialize_server_socket(self.__server_socket,
                                     self.__server_address,
                                     self.__server_listen)
