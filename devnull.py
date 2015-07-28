import os

class _DevNull(object):
    def __init__(self):
        self.__device = open(os.devnull, "w+b")

    def __del__(self):
        self.__device.close()

    def get_device(self):
        return self.__device

_devnull_object = _DevNull()
devnull = _devnull_object.get_device()
