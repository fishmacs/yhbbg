#import sys
import json
from datetime import date

from django.core.files.uploadhandler import FileUploadHandler
from django.core.cache import cache


def get_grade_year(grade):
    today = date.today()
    year = today.year - grade
    if today.month > 8:
        year += 1
    return year


def jsondumps(d):
    return json.dumps(d, ensure_ascii=False)
    

def fail(msg):
    return jsondumps({'result': 'fail', 'reason': msg, 'data': None})

    
def error(msg):
    return jsondumps({'result': 'error', 'reason': msg, 'data': None})


class ProgressUploadHandler(FileUploadHandler):
    CACHE_TIMEOUT = 300
    
    def receive_data_chunk(self, raw_data, start):
        try:
            self.data[0] += self.chunk_size  # start+len(raw_data)#
            if self.data[0] > self.data[1]:
                self.data[0] = self.data[1]
                if self.upload_key:
                    cache.set(self.upload_key, self.data, self.CACHE_TIMEOUT)
        except:
            pass
        #print >>sys.stderr, 'zwwwwwww', len(raw_data), start, self.upload_key
        return raw_data

    def handle_raw_input(self, input, META, content_length, boundary, encoding):
        upload_id = self.request.GET.get('upload_id', '')
        if upload_id:
            self.upload_key = 'upload_id:' + upload_id
            self.data = [0, content_length]
            cache.set(self.upload_key, self.data, self.CACHE_TIMEOUT)
            #print >>sys.stderr, 'zwwwwww file size', content_length, self.upload_key
        else:
            self.upload_key = ''

    def file_complete(self, file_size):
        #print >>sys.stderr, 'zwwwwwww', self.data
        if self.upload_key:
            cache.delete(self.upload_key)
