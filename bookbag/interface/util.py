#encoding=utf8

import os
import re

from django.conf import settings

def upload_dir(uid, course_id):
    d = os.path.join(settings.COURSEWARE_UPLOAD_DIR, uid, course_id)
    if not os.path.exists(d):
        os.makedirs(d)
    return d

def handle_upload(f, d):
    fn_nospace = re.sub(r'\s+', '_', f.name)
    filename = os.path.join(d, fn_nospace)
    #print >>sys.stderr, 'uploading...', filename
    ### utf8 for apache
    des = open(filename.encode('utf8'), 'wb+')
    ### don't need encode now, set LANG/LC_ALL when start apache
    #des = open(filename, 'wb+')
    try:
        for chunk in f.chunks():
            des.write(chunk)
    finally:
        des.close()
    return filename
