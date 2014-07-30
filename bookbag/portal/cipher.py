from Crypto.Cipher import DES3
import base64

import pkcs7

key = 'abcdefghijklmnopqrstuvwx'
iv = 'init Vec'

def encrypt(s):
    d = DES3.new(key, DES3.MODE_CBC, iv)
    padder = pkcs7.PKCS7Encoder(k=8)
    return base64.standard_b64encode(d.encrypt(padder.encode(s)))

def decrypt(s):
    d = DES3.new(key, DES3.MODE_CBC, iv)
    padder = pkcs7.PKCS7Encoder(k=8)
    return padder.decode(d.decrypt(base64.standard_b64decode(s)))
