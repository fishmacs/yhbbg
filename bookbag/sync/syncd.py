import os
import sys
import json
import logging
from datetime import timedelta

from django.utils import timezone

from twisted.internet import defer, task, reactor
from twisted.application import service

from stompest.async.listener import SubscriptionListener

import stompconf

sys.path.insert(1, os.path.abspath('..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookbag.settings")

from sync import models


class SyncDaemon(service.Service):
    CHECK_SYNC_INTERVAL = 5
    SYNC_TIMEOUT = 15
    
    def __init__(self):
        qs = models.LessonSync.objects.filter(finished=False)
        self.sync_dict = {}
        for s in qs:
            self.sync_dict[s.uuid] = timezone.now()
        self.cmd_handlers = {
            'start_sync': self.start_sync,
            'end_sync': self.end_sync
        }
        #self.check_time = timezone.datetime(2000, 1, 1)
        
    def startService(self):
        service.Service.startService(self)
        self.stomp = stompconf.get_stomp_client()
        self.process_message()
        timer = task.LoopingCall(self.timer_consumer)
        timer.start(self.CHECK_SYNC_INTERVAL)
        
    def stopService(self):
        service.Service.stopService(self)

    @defer.inlineCallbacks
    def process_message(self):
        yield self.stomp.connect(host=stompconf.BROKER_NAME)
        yield self.stomp.subscribe(stompconf.SYNC_QUEUE,
                                   headers={'id': 'sync_daemon_channel', 'ack': 'client'},
                                   listener=SubscriptionListener(self.controller_consumer))
        for id in self.sync_dict:
            sid = 'sync__' + id
            self.subscribe(sid)
            
    def subscribe(self, id):
        self.stomp.subscribe(
            '/topic/' + id,
            {'id': id, 'persistent': 'true', 'browser': 'true',
             'browser-end': 'false', 'include-seq': 'seq',
             'from-seq': 0, 'ack': 'client'},
            listener=SubscriptionListener(self.sync_consumer))
        hb_id = id + '__heartbeat'
        self.stomp.subscribe('/queue/' + hb_id,
                             headers={'id': hb_id, 'ack': 'client'},
                             listener=SubscriptionListener(self.heartbeat_consumer))

    def unsubscribe(self, id):
        frame = self.stomp.session.unsubscribe(('id', id))
        frame.headers['persistent'] = 'true'
        self.stomp.sendFrame(frame)
        self.stomp.unsubscribe(('id', id + '__heartbeat'))
        
    @defer.inlineCallbacks
    def controller_consumer(self, client, frame):
        data = json.loads(frame.body)
        cmd = data['command']
        try:
            func = self.cmd_handlers[cmd]
            yield func(data)
        except KeyError:
            logging.error('unknown command: ' + cmd)

    def add_sync_action(self, id, data):
        models.SyncAction.objects.create(sync_id=id, action=data['action'],
                                         kind=data['type'], target=data['target'],
                                         option=data.get('option', ''))
            
    #@defer.inlineCallbacks
    def sync_consumer(self, client, frame):
        id = frame.headers['subscription'].replace('sync__', '')
        if id in self.sync_dict:
            data = json.loads(frame.body)
            reactor.callInThread(self.add_sync_action, id, data)
        else:
            logging.warn('unknown sync id: ' + id)
            
    #@defer.inlineCallbacks
    def heartbeat_consumer(self, client, frame):
        id = frame.headers['subscription'].replace('sync__', '').replace('__heartbeat', '')
        if id in self.sync_dict:
            self.sync_dict[id] = timezone.now()
        else:
            logging.warn('unknown sync id: ' + id)

    def finish_sync(self, dead_ids):
        models.LessonSync.objects.filter(uuid__in=dead_ids).update(finished=True)
        
    def timer_consumer(self):
        logging.debug('timer')
        dead_ids = []
        now = timezone.now()
        for id, t in self.sync_dict.iteritems():
            if now - t > timedelta(seconds=self.SYNC_TIMEOUT):
                self.unsubscribe('sync__' + id)
                dead_ids.append(id)
        for id in dead_ids:
            del self.sync_dict[id]
        if dead_ids:
            reactor.callInThread(self.finish_sync, dead_ids)
            
    @defer.inlineCallbacks
    def start_sync(self, data):
        id = data['sync_id']
        self.sync_dict[id] = timezone.now()
        logging.info('start_sync: ' + id)
        yield self.subscribe('sync__' + id)
        
    @defer.inlineCallbacks
    def end_sync(self, data):
        id = data['sync_id']
        logging.info('end_sync: ' + id)
        if id in self.sync_dict:
            del self.sync_dict[id]
            yield self.unsubscribe('sync__' + id)
        else:
            logging.warn('unknown sync id: ' + id)
            
        
logging.basicConfig(level=logging.INFO,
                    filename='/var/log/syncd.log',
                    format='%(asctime)s - %(levelname)s - %(message)s')
daemon = SyncDaemon()
application = service.Application('sync_daemon')
daemon.setServiceParent(application)
