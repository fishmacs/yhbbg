import json
from django.conf import settings

from stompest.config import StompConfig
from stompest.sync import Stomp


def send(data):
    mqcfg = settings.MESSAGE_QUEUE
    config = StompConfig(mqcfg['url'],
                         login=mqcfg['username'],
                         passcode=mqcfg['password'])
    stomp = Stomp(config)
    stomp.connect(host=mqcfg['broker'])
    stomp.send(mqcfg['vote_queue'], json.dumps(data))
    stomp.disconnect()
