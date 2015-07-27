#!/usr/bin/python

# Imports
import threading
import socket
import sys
import tempfile
import os
import warnings

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
    """Converts a socket address or port to a tuple.  Tuples are assumed to be valid."""

    # If this is a string, convert it to a valid tuple.
    if isinstance(addr, basestring):
        addr = tuple(addr.split(':')[:2])
        addr[1] = int(addr[1])

    # If we have an integer, treat it like a port available on all interfaces.
    elif isinstance(addr, int):
        addr = ("", addr)

    if not isinstance(addr, tuple) or len(addr) != 2:
        raise TypeError("A tuple of length 2 was expected here.")
    else:
        return addr

#############################
# initialize_inbound_socket #
#############################
def initialize_inbound_socket(sock, address_or_port, listen):
    if sock is not None:
        sock.bind(to_address(address_or_port))
        sock.listen(listen)

###############
#             #
#   Classes   #
#             #
###############

######################
# PortToSocketBridge #
######################
class PortToSocketBridge(object):
    """A class that bridges inbound ports with outbound sockets."""

    def __init__(self, in_trans_type, in_address, out_trans_type, out_address, listen = 5):

        # Outbound socket information.
        self.__out_socket_type  = to_socket_type(out_trans_type)
        self.__out_address      = to_address(out_address)
        self.__outbound_sockets = []

        # Get all meaningful information needed to create a socket.
        self.__in_socket_type  = to_socket_type(in_trans_type)
        self.__in_address      = to_address(in_address)
        self.__in_listen          = listen
        self.__inbound_socket  = None

        # Prepare a socket to listen on the inbound port.

    def __create_inbound_socket(self):
        if self.__inbound_socket is None:
            self.__inbound_socket = socket.socket(socket.AF_INET, self.__in_socket_type)
            initialize_inbound_socket(self.__inbound_socket,
                                      self.__in_address,
                                      self.__in_listen)

    def __create_outbound_socket(self):
        return socket.socket(socket.AF_INET, self.__out_socket_type)

    def __register_outbound_socket(self, sock):
        if sock is not None:
            self.__outbound_sockets.append(sock)
            return True
        return False
