import debugsocket as socket
import threading

# An "abstract" implementation for listening on a port and forwarding its data.
ListenAndForward = None                 # Declare the name now,
class ListenAndForward(object):         # so that we can
    _Self = lambda: ListenAndForward    # do this.

    # __init__ ############################################
    def __init__(self, listen_on, forward_to, Self=_Self):
        if type(self) is Self():
            raise TypeError("Direct instantiation of %s prohibited." % (type(self).__name__,))

        # Save general information for this task.
        self.__running      = False
        self.__dest_address = forward_to
        self._my_address    = listen_on     # get_server_socket may update this.

    # __repr__ ############################################
    def __repr__(self):
        return "<%s at %x>" % (str(self), id(self))

    # __str__ #############################################
    def __str__(self):
        return "%s(listen_on=%r, forward_to=%r)" % (
            type(self).__name__,
            self.get_my_address(),
            self.get_destination_address(),
        )

    # __enter__ ###########################################
    def __enter__(self):
        return self

    # __exit__ ############################################
    def __exit__(self, exc_type, exc_value, traceback):
        self.kill()
        return False            # Not necessary, but I want to explicitly state that exceptions will be reraised.

    # kill ################################################
    def kill(self):
        """Inform this object instance to stop listening and forwarding."""
        self.__shutdown()
        self.__running = False

    # __shutdown ##########################################
    def __shutdown(self):
        """Perform any necessary shutdown operations for this object."""

        # Destroy any server socket.  This means a server socket
        # must be created for every object.
        server_socket = self.get_server_socket()
        if server_socket:

            x = lambda: None
            x.__doc__ = type(self).get_server_socket.__doc__
            self.get_server_socket = x

            if hasattr(server_socket, "close"):
                server_socket.close()

    # get_my_address ######################################
    def get_my_address(self):
        """What's my local address?"""
        self.get_server_socket()                        # Okay, we HAVE to get the server socket.
        self.get_my_address = lambda: self._my_address  # So we can get straight to the point next time.
        return self.get_my_address()                    # Watch it in action!

    # get_destination_address #############################
    def get_destination_address(self):
        """What address am I forwarding data to?"""
        return self.__dest_address

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
        raise NotImplementedError("Please override this method in a subclass.")

    # get_new_source_connection ###########################
    def get_new_source_connection(self):
        """Gets a new connection from the source."""
        raise NotImplementedError("Please override this method in a subclass.")

    # get_new_destination_connection ######################
    def get_new_destination_connection(self):
        """Gets a new connection from the destination."""
        raise NotImplementedError("Please override this method in a subclass.")

    # log_data ############################################
    def log_data(self, count, data, _from, _to):
        """Logs data received from the source.  This is called before
        forwarding the data to the destination."""
        pass

    # handle_forwarding_once_and_cleanup ##################
    def handle_forwarding_once_and_cleanup(self, source_connection):

        # transmit ##############
        def transmit(_from, _to):
            """Transmits data from _from to _to."""

            # Gather as many chunks of data as we can.
            for count, data in enumerate(_from):

                # Shall we terminate early?  (This allows for abrupt termination in threads.)
                if not self.__running:
                    return False

                # Otherwise, log the data and send it.
                self.log_data(count, data, _from, _to)
                _to.send(data)

            # We're good.  Keep going.
            return True

        # roundtrip ##############
        def roundtrip(_from, _to):
            """The first parameter is the sender, the second parameter is the receiver
            (not regarding this machine).  Sends data like so:

            first -> second -> first"""

            # Only go in the reverse direction if we can keep running.
            if transmit(_from, _to):
                transmit(_to, _from)
            return _from, _to

        # I need to declare this variable here since
        # I use it in the finally block, and there's a
        # chance that it may be used before the assignment
        # in the try suite.
        pair = ""               # I need it to be iterable.

        # Send the data in both directions.
        try:
            pair = roundtrip(source_connection, self.get_new_destination_connection())

        # Every time we finish forwarding, whether successful
        # or not, make sure to clean up after ourselves.
        finally:
            for obj in pair:
                obj.close()

    # listen_and_forward ##################################
    def listen_and_forward(self):
        """This is the method that performs all of the magic.  It's basically
        a loop that does what the name of the method says ;)"""
        try:
            try:
                new_connection = self.get_new_source_connection
                forward_one    = self.handle_forwarding_once_and_cleanup

                # Keep running until explicitly killed.
                self.__running = True                       # I'm going in!!!
                while self.__running:
                    forward_one(new_connection())

            # This is in place now, until I decide that I need to
            # implement custom exception handling here.
            except:
                raise

        # Shut down our object.
        finally:
            self.__shutdown()

# A mixin class to allow ListenAndForward instances
# to handle forwarding in a separate thread.
class ThreadingMixIn(object):

    # __init__ ############################################
    def __init__(self, is_daemon_thread=False, ListenAndForward=ListenAndForward):
        self.__target = lambda src: ListenAndForward.handle_forwarding_once_and_cleanup(self, src)
        self.__is_daemon_thread = is_daemon_thread

    # handle_forwarding_once_and_cleanup ##################
    def handle_forwarding_once_and_cleanup(self, source_connection):
        thread = threading.Thread(target=self.__target, args=(source_connection,))
        thread.daemon = self.__is_daemon_thread
        thread.start()
