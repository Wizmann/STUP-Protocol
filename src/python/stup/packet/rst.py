#!/usr/bin/python
from .packet import Packet

class RstPacket(Packet):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.rst = 1
