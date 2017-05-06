import abc
import random
from Crypto.Cipher import DES, AES
from .Digest import digest

def nonce(length):
    return ''.join([chr(random.randint(0, 255)) for i in xrange(length)])

def padding(data_length, unit, extra):
    padded_data_length = data_length + extra
    if padded_data_length % unit != 0:
        padded_data_length += unit - padded_data_length % unit
    padding_length = padded_data_length - data_length
    return nonce(padding_length), padding_length

class Crypto(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def encrypt(self, plain_data):
        raise NotImplementedError()

    @abc.abstractproperty
    def decrypt(self, cipher_data):
        raise NotImplementedError()

class AESCrypto_ECB(Crypto):
    BLOCK_SIZE = 16

    def __init__(self, key):
        key = digest(key)[:16]
        self.aes = AES.new(key, AES.MODE_ECB)
        self.padding = \
                lambda data, extra: padding(data, self.BLOCK_SIZE, extra)

    def encrypt(self, plain_data):
        assert len(plain_data) % self.BLOCK_SIZE == 0
        return self.aes.encrypt(plain_data)

    def decrypt(self, cipher_data):
        assert len(cipher_data) % self.BLOCK_SIZE == 0
        return self.aes.decrypt(cipher_data)

class AESCrypto_ECB_with_IV(Crypto):
    KEY_SIZE = 16
    BLOCK_SIZE = 16

    def __init__(self, key, iv_size=2):
        assert iv_size < self.KEY_SIZE
        self.iv_size = iv_size
        self.key = digest(key)[:self.KEY_SIZE - iv_size]
        self.padding = \
                lambda data, extra: padding(data, self.BLOCK_SIZE, extra)

    def encrypt(self, iv, plain_data):
        fullkey = self.key + iv[:self.iv_size]
        assert len(fullkey) == self.KEY_SIZE
        assert len(plain_data) % self.BLOCK_SIZE == 0
        aes = AES.new(fullkey, AES.MODE_ECB)
        return aes.encrypt(plain_data)

    def decrypt(self, iv, cipher_data):
        fullkey = self.key + iv[:self.iv_size]
        assert len(fullkey) == self.KEY_SIZE
        assert len(cipher_data) % self.BLOCK_SIZE == 0
        aes = AES.new(fullkey, AES.MODE_ECB)
        return aes.decrypt(cipher_data)

