import threading
from ListenAndForward import ListenAndForward

# Just fleshing out an idea.
class MultiListenAndForward(object):
    def __init__(self):
        self.__is_running = False
        self.__listeners = []

    def append_listener(self, listener):
        if not isinstance(listener, ListenAndForward):
            raise TypeError("listener must be of type ListenAndForward")
        self.__listeners.append(listener)
        if self.__is_running:
            self.__run_thread(-1)

    def __run_thread(self, index):
        target = self.__listeners[index].listen_and_forward
        thread = threading.Thread(target=target)
        thread.start()

    def listen_and_forward(self):
        self.__is_running = True
        for index, value in enumerate(self.__listeners):
            self.__run_thread(index)

    def kill(self):
        for listener in self.__listeners:
            listener.kill()
