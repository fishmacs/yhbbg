from stompest.config import StompConfig
from stompest.async import Stomp

STOMP_SERVER = 'tcp://localhost:61613'
STOMP_USERNAME = 'user1'
STOMP_PASSWORD = 'test1'
BROKER_NAME = 'mybroker'
SYNC_QUEUE = '/queue/sync_daemon'


def get_stomp_client():
    conf = StompConfig(STOMP_SERVER, login=STOMP_USERNAME,
                       passcode=STOMP_PASSWORD)  # , version='1.1')
    return Stomp(conf)
