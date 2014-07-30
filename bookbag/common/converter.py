import os
import urllib

from django.conf import settings

def convert_upload(id, uid, course_id, upload_path, reconvert, format, pdf_version, port):
    outpath = os.path.join(settings.COURSEWARE_CONVERT_DIR, str(uid), course_id, '%d.mrf' % id)
    ## urlencode can not take unicode
    params = urllib.urlencode({
        'id': id,
        'inpath': upload_path.encode('utf-8'),
        'outpath': outpath.encode('utf-8'),
        'reconvert': reconvert and 1 or 0,
        'format': format,
        'pdf_version': pdf_version,
        'port': port,
        })
    urllib.urlopen(settings.DOC_CONVERT_SERVER+'/convert', params)
    return outpath

def deliver_file(id, uid, path, crypt_key):
    filename = os.path.basename(path)
    dirname = os.path.dirname(path)
    outpath = os.path.join(dirname, str(uid), filename)
    ## urlencode can not take unicode
    params = urllib.urlencode({
        'inpath': path.encode('utf-8'),
        'outpath': outpath.encode('utf-8'),
        'key': crypt_key
        })
    d = urllib.urlopen(settings.DOC_CONVERT_SERVER+'/deliver', params)
    ret = d.read()
    if ret != 'ok':
        raise Exception(ret)
    return outpath

