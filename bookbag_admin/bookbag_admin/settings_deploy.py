import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(PROJECT_DIR, 'media/')

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static/')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'bookbag_y',                      # Or path to database file if using sqlite3.
        'USER': 'bookbag',                      # Not used with sqlite3.
        'PASSWORD': 'teladmin',                  # Not used with sqlite3.
        'HOST': 'db',                      # Set to empty string for localhost. Not used with sqlite3.
        # 'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

from mongoengine import connection

connection.connect('bookbag')

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
#         'LOCATION': '127.0.0.1:11211',
#         'TIMEOUT': 180
#     }
# }

BASE_DOWNLOAD_URL = '/dl/getfile'

COURSEWARE_UPLOAD_DIR = '/mnt/courseware_doc3/upload'
COURSEWARE_CONVERT_DIR = '/mnt/courseware_doc3/output'

DEFAULT_COURSE_IMAGE = '/media/images/courses/default.jpg'
DEFAULT_COURSEWARE_IMAGE = '/media/images/coursewares/default.jpg'

DOC_CONVERT_SERVER = 'http://172.16.91.93:8080'

PUSH_URL = {
    'appdev': 'https://localhost:8080/notify-dev.php',
    'apprel': 'https://localhost:8080/notify.php',
    'entdev': 'https://localhost:8080/entnotify-dev.php',
    'entrel': 'https://localhost:8080/entnotify.php',
}

# after 3 days, even offline mode needs login
DEFAULT_OFFLINE_TIMEOUT = 259200

BATCH_INFORM_COUNT = 100

# message queue/stomp
MESSAGE_QUEUE = {
    'url': 'tcp://localhost:61613',
    'ws_url': 'ws://k12.telecomedu.com:61623',
    'broker': 'mybroker',
    'username': 'user1',
    'password': 'test1',
    'vote_queue': '/queue/vote'
}
