#!/usr/bin/python
import ctypes
import random
import bitstruct
from io import BytesIO
from stup import utils as Utils
from stup import config as Config
from stup import crypto


'''
STUP packet

|<---------------------------------------16bits--------------------------------------->|
|                                 IV              (16bits)                             |
|--------------------------------------------------------------------------------------|
|  VER(3)  |             NONCE(6)            | URG | LIV | ACK | PSH | RST | SYN | FIN |
|--------------------------------------------------------------------------------------|
|                                 SEQ NUMBER      (16bits)                             |
|                                 SEQ NUMBER      (16bits)                             |
|--------------------------------------------------------------------------------------|
|                                 ACK NUMBER      (16bits)                             |
|                                 ACK NUMBER      (16bits)                             |
|--------------------------------------------------------------------------------------|
|                                          DATA                                        |
|--------------------------------------------------------------------------------------|

'''


class Packet(ctypes.Structure, object):
    _pack_ = 1
    _fields_ = [
        ('ver', ctypes.c_uint, 3),
        ('nonce', ctypes.c_uint, 6),
        ('urg', ctypes.c_uint, 1),
        ('liv', ctypes.c_uint, 1),
        ('ack', ctypes.c_uint, 1),
        ('psh', ctypes.c_uint, 1),
        ('rst', ctypes.c_uint, 1),
        ('syn', ctypes.c_uint, 1),
        ('fin', ctypes.c_uint, 1),
        ('seq_number', ctypes.c_uint, 32),
        ('ack_number', ctypes.c_uint, 32),
    ]

    STRUCT_FORMAT_STR = "<u3u6" + "u1" * 7 + "u32" * 2
    STRUCT_SIZE = 10

    cipher = crypto.cipher.AESCrypto_ECB_with_IV(Config.CRYPTO_KEY)

    def __init__(self, data=b''):
        assert isinstance(data, bytes)
        self._data = data

    @classmethod
    def deserialize(self, buffer):
        msg = Packet()
        msg.unpack(buffer)
        return msg

    @classmethod
    def serialize(self, packet):
        return packet.pack()

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    def size(self):
        return self.STRUCT_SIZE + len(self._data)

    def unpack(self, bytes):
        iv = bytes[:2]
        bytes = bytes[2:]
        bytes = self.cipher.decrypt(iv, bytes)

        header = bytes[:self.STRUCT_SIZE]
        self.data = bytes[self.STRUCT_SIZE:]

        (self.ver,
            self.nonce,
            self.urg,
            self.liv,
            self.ack,
            self.psh,
            self.rst,
            self.syn,
            self.fin,
            self.seq_number,
            self.ack_number) = bitstruct.unpack(self.STRUCT_FORMAT_STR, header)

        self.data = self.data[:-self.nonce]

    def pack(self):
        iv = crypto.cipher.nonce(2)
        length = self.STRUCT_SIZE + len(self._data)
        extra = random.randint(1, 16)
        padding, padding_length = self.cipher.padding(length, extra)

        assert 0 < padding_length < (1 << 6) - 1
        self.nonce = padding_length

        header = bitstruct.pack(self.STRUCT_FORMAT_STR,
            self.ver,
            self.nonce,
            self.urg,
            self.liv,
            self.ack,
            self.psh,
            self.rst,
            self.syn,
            self.fin,
            self.seq_number,
            self.ack_number)
        plain_bytes = header + self._data + padding
        return iv + self.cipher.encrypt(iv, plain_bytes)

    def to_dict(self):
        field_names = set([item[0] for item in self._fields_]) ^ set(['data'])
        d = dict(
            [(key, getattr(self, key)) for key in field_names]
        )
        if Utils.istext(d['data']):
            if len(d['data']) > 10:
                d['data'] = d['data'][:10] + '...(%d)' % len(d['data'])
        else:
            d['data'] = 'BIN[%d]' % len(d['data'])
        return d

    def __str__(self):
        return str(self.to_dict())
