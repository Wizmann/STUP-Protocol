import Crypto.Hash.MD5

def digest(plain_text):
    h = Crypto.Hash.MD5.new()
    h.update(plain_text)
    return h.digest()
