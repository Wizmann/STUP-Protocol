#!/usr/bin/python
from .StupPacket import Packet

class FinPacket(Packet):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.fin = 1

