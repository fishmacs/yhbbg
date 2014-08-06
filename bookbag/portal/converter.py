import os
import numpy
from itertools import izip
from Crypto.Cipher import AES

iv = '\x12\x34\x56\x78\x90\xab\xcd\xef\x12\x34\x56\x78\x90\xab\xcd\xef'


BUFFER_SIZE = 32 * 1024  # 2048
#MRF_BUFFER_SIZE = 32*1024


def fill_key(encode_key, size):
    n = size / len(encode_key)
    s = size % len(encode_key)
    keys0 = [c for c in encode_key]
    keys = []
    for i in xrange(n):
        keys += keys0
    for i in xrange(s):
        keys.append(encode_key[i])
    return numpy.frombuffer(''.join(keys), dtype=numpy.byte)

mrf_key = fill_key('hongkou188', BUFFER_SIZE)


def encode(s, keys):
    a = numpy.bitwise_xor(numpy.frombuffer(s, dtype=numpy.byte), keys)
    return a.tostring()


def encrypt(infile, key, outfile):
    key16 = ''.join([chr(x*16+y) for (x, y) in
                     izip(*[iter([int(c, 16) for c
                                  in key])]*2)])
    aes = AES.new(key16, AES.MODE_CBC, iv)
    with open(infile, 'rb') as f1:
        with open(outfile, 'wb') as f2:
            src = f1.read(BUFFER_SIZE)
            while src:
                if len(src) < BUFFER_SIZE:
                    src = encode(src, mrf_key[:len(src)])
                    padding = len(src) % 16
                    if padding:
                        l = 16 - padding
                        src += chr(l) * l
                else:
                    src = encode(src, mrf_key)
                f2.write(aes.encrypt(src))
                src = f1.read(BUFFER_SIZE)


def deliver_file(id, uid, path, crypt_key):
    filename = os.path.basename(path)
    dirname = os.path.dirname(path)
    outdir = os.path.join(dirname, str(uid))
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    outpath = os.path.join(outdir, filename)
    encrypt(path, crypt_key, outpath)
    return outpath
