import json
from django.conf import settings

from stompest.config import StompConfig
from stompest.sync import Stomp

DAEMON_CHANNEL = '/queue/sync_daemon'


def get_stomp_conn():
    mqcfg = settings.MESSAGE_QUEUE
    config = StompConfig(mqcfg['url'],
                         login=mqcfg['username'],
                         passcode=mqcfg['password'])
    stomp = Stomp(config)
    stomp.connect(host=mqcfg['broker'])
    return stomp

    
def send(des, data):
    stomp = get_stomp_conn()
    data = json.dumps(data)
    stomp.send(des, data)
    stomp.disconnect()
    

def subscribe_sync(id):
    stomp = get_stomp_conn()
    stomp.subscribe(
        '/topic/sync__' + id,
        {'id': 'sync__' + id, 'persistent': 'true', 'browser': 'true',
         'browser-end': 'false', 'include-seq': 'seq',
         'from-seq': 0, 'ack': 'client'})
    stomp.disconnect()
    print 'subscribe:', id

    
def unsubscribe_sync(id):
    stomp = get_stomp_conn()
    stomp.session._subscriptions[('id', 'sync__' + id)] = 0
    # client.unsubscribe does not support headers, so have to hack it:
    frame = stomp.session.unsubscribe(('id', 'sync__' + id))
    frame.headers['persistent'] = 'true'
    stomp.sendFrame(frame)
    stomp.disconnect()
    print 'unsubscribe:', id
