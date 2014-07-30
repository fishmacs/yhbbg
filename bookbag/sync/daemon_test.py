import os
import sys
import time
import uuid
import json
import unittest
from unittest import TestCase

from django.conf import settings

sys.path.insert(1, os.path.abspath('..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookbag.settings")

from sync import models
import msgq


def read_last_log():
    with open('/var/log/syncd.log') as f:
        f.seek(-1024, 2)
        ss = [s[33:].strip() for s in f.readlines()[-2:]]
        if ss[-1] == 'timer':
            return ss[-2]
        return ss[-1]
        
        
class SyncDaemonTest(TestCase):
    def __init__(self, *args):
        super(SyncDaemonTest, self).__init__(*args)
        self.course_id = 1
        self.class_id = 1
        self.user_id = 1

    def start_sync(self):
        self.uuid = uuid.uuid1().get_hex()
        models.LessonSync.objects.create(
            uuid=self.uuid,
            course_id=self.course_id,
            myclass_id=self.class_id,
            creator_id=self.user_id
        )
        destination = '/topic/course__{0}_{1}'.format(self.class_id, self.course_id)
        data = {'command': 'start_sync',
                'sync_id': self.uuid,
                'destination': '/dsub/sync__{0}'.format(self.uuid),
                'message_queue': settings.MESSAGE_QUEUE}
        msgq.send(destination, data)
        
    def end_sync(self):
        sync = models.LessonSync.objects.get(uuid=self.uuid)
        #sync.delete()
        sync.finished = True
        sync.save()
        destination = '/topic/course__{0}_{1}'.format(sync.myclass_id, sync.course_id)
        data = {'command': 'end_sync',
                'sync_id': self.uuid,
                'destination': '/dsub/sync__{0}'.format(self.uuid),
                'message_queue': settings.MESSAGE_QUEUE}
        msgq.send(destination, data)

    def test_start_end(self):
        self.start_sync()
        time.sleep(0.1)
        self.assertEqual(read_last_log(), 'start_sync: ' + self.uuid)

        self.end_sync()
        time.sleep(0.1)
        self.assertEqual(read_last_log(), 'end_sync: ' + self.uuid)

    def test_sync_action(self):
        self.start_sync()
        time.sleep(0.1)
        data = {'type': 'test', 'action': 'action',
                'target': 'target', 'option': 'option'}
        msgq.send('/dsub/sync__' + self.uuid, data, False)
        time.sleep(2)
        self.end_sync()
        
    def test_sync_hearbeat1(self):
        self.start_sync()
        data = {'sync_id': self.uuid, 'type': 'heartbeat'}
        msgq.send('/queue/sync__{0}__heartbeat'.format(self.uuid), data, False)
        time.sleep(2)
        self.end_sync()

    def test_sync_hearbeat2(self):
        self.start_sync()
        data = {'sync_id': self.uuid, 'type': 'heartbeat'}
        msgq.send('/queue/sync__{0}__heartbeat'.format(self.uuid), data, False)
        time.sleep(20)
        s = models.LessonSync.objects.get(uuid=self.uuid)
        self.assertEqual(s.finished, True)
        
if __name__ == '__main__':
    unittest.main()
