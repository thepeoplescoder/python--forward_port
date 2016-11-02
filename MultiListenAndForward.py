import threading
from ListenAndForward import ListenAndForward

# Just fleshing out an idea.
class MultiListenAndForward(object):

    # __init__ ############################################
    def __init__(self):
        """Constructor.  Initializes an empty sequence of ListenAndForward instances."""
        self.__is_running = False       # Are we running?
        self.__listeners = []           # A list of ListenAndForward instances
                                        # that are all listening on various ports.

    # __enter__ ###########################################
    def __enter__(self):
        return self

    # __exit__ ############################################
    def __exit__(self, exc_type, exc_value, traceback):
        self.kill()

    # __len__ #############################################
    def __len__(self):
        return len(self.__listeners)

    # __getitem__ #########################################
    def __getitem__(self, index):
        return self.__listeners[index]

    # __iter__ ############################################
    def __iter__(self):
        return iter(self.__listeners)

    # __run_thread ########################################
    @staticmethod
    def __run_thread(obj):
        """Runs the thread at the given index."""
        target = obj.listen_and_forward             # That's what we're going to run!
        thread = threading.Thread(target=target)    # There's that thread. ;)
        thread.start()                              # Run it.

    # append_listener #####################################
    def append_listener(self, listener):
        """Appends a ListenAndForward instance to our list."""

        # Crap out if an object of the wrong type is passed.
        if not isinstance(listener, ListenAndForward):
            raise TypeError("listener must be of type ListenAndForward")

        # Append the instance.
        self.__listeners.append(listener)

        # If we're actively listening and forwarding,
        if self.__is_running:
            self.__run_thread(self[-1])         # then go ahead and run this as a new thread.

    # Provide append() as an alias.
    append = append_listener

    # listen_and_forward ##################################
    def listen_and_forward(self):
        """Runs listen_and_forward() on all provided instances."""

        # We don't need to do this a second time.
        if not self.__is_running:

            # Okay, we're running for real.
            self.__is_running = True

            # Run all the instances in a separate thread.
            for listener in self:
                self.__run_thread(listener)

    # kill ################################################
    def kill(self):
        """Stops all threads that this object manages.
        Renders this object useless."""
        for listener in self:
            listener.kill()
