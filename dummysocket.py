# Imports
import socket

###############
# DummySocket #
###############
class DummySocket(socket.socket):
    """Class to "look, feel, and smell" like a socket, but does nothing."""

    def __init__(self, family=None, type=None, proto=None):
        pass

    def accept(self):
        return (DummySocket.SOCKET, DummySocket.SOCKET_ADDRESS)

    def bind(self, address):
        pass

    def close(self):
        pass

    def connect(self, address):
        pass

    def connect_ex(self, address):
        return 0

    def fileno(self):
        return devnull.devnull.fileno()

    def getpeername(self):
        return DummySocket.SOCKET_ADDRESS

    def getsockname(self):
        return self.getpeername()

    def getsockopt(self, level, optname, buflen=None):
        if buflen is None:
            return -1
        else:
            return ""

    def ioctl(self, control, option):
        pass

    def listen(self, backlog):
        pass

    def makefile(self, mode=None, bufsize=None):
        return devnull.devnull

    def recv(self, bufsize, flags=None):
        return ""

    def recvfrom(self, bufsize, flags=None):
        return ("", DummySocket.SOCKET_ADDRESS)

    def recvfrom_into(self, buffer, nbytes=None, flags=None):
        return (0, DummySocket.SOCKET_ADDRESS)

    def recv_into(self, buffer, nbytes=None, flags=None):
        return 0

    def send(self, string, flags=None):
        return 0

    def sendall(self, string, flags=None):
        return None

    def sendto(self, string, flags, address=None):
        return 0

    def setblocking(self, flag):
        pass

    def settimeout(self, value):
        pass

    def gettimeout(self):
        return 0

# Late binding on these "constants."
DummySocket.SOCKET = DummySocket()
DummySocket.SOCKET_ADDRESS = ("0.0.0.0", 0)
