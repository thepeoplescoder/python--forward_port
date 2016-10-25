#!/usr/bin/env python

# Port forwarding: socket example

# Imports
import sys
import os
import six
import colorama
from ListenAndForwardTCP import ListenAndForwardTCP

# Aliases
_print = six.print_

# Get the interpreter.
INTERPRETER_NAME = os.path.splitext(os.path.basename(sys.executable))[0]

# to_socket_address #######################################
def to_socket_address(obj):
    """Converts a sequence or string to a tuple representing a (addr, port) socket address."""

    # Defaults.
    host = ""
    port = 0

    # Is this a 2 element sequence?
    if isinstance(obj, (tuple, list)) and len(obj) == 2:
        host = str(obj[0] or host)
        port = int(obj[1] or port)

    # Is this a dictionary?
    elif isinstance(obj, dict):
        host = obj.get("address", obj.get("addr", obj.get("host", obj.get("ip", host))))
        port = obj.get("port", port)

    # If it's a string, break it around the colon. ;)
    elif isinstance(obj, str):
        return to_socket_address(obj.split(":"))

    # Unknown type.
    else:
        raise TypeError("Unknown parameter type passed to to_socket_address")

    # Okay, we're good.
    return host, port

# log_data ############################################
def log_data():
    lognum = [0]

    def log_data(self, count, data, _from, _to):

        # Print header on new connection.
        if not count:
            Fore = colorama.Fore
            Style = colorama.Style
            lognum[0] += 1

            ch = "#"
            style = Fore.RED + Style.BRIGHT

            _print(style + ch * 60)
            _print(style + (" %d " % (lognum[0],)).center(60, ch))
            _print(style + ch * 60)
            _print("Sending from %r to %r\n" % (_from, _to))

        # This is the actual data from the packet(s).
        _print(data, end="")

    return log_data

# _main ###################################################
def _main(argv=sys.argv):
    """Program entry point."""

    # Gotta have the right number of arguments.
    if len(argv) < 2:
        _print("Usage: %s %s <ForwardTo>\n" % (INTERPRETER_NAME, argv[0]))
        return 1

    # Source and destination addresses.
    listen_on  = ("", 0)
    forward_to = to_socket_address(argv[1])

    # Start forwarding packets.
    try:
        with ListenAndForwardTCP(listen_on, forward_to, log_data=log_data()) as proxy:
            _print("Hello!")
            _print("I'm listening on:  %r" % (proxy.get_my_address(),))
            _print("I'm forwarding to: %r" % (proxy.get_destination_address(),))
            _print()

            proxy.listen_and_forward()

    # Exit on Ctrl-C.
    except KeyboardInterrupt:
        _print("\n\nBye!\n")

    # Reraise any unknown exceptions.
    except:
        raise

    # Return to OS
    return 0

# If we're running this as a program....
if __name__ == "__main__":
    ret = 1
    try:
        colorama.init(autoreset=True)
        ret = _main()
    finally:
        colorama.deinit()
        sys.exit(ret)
