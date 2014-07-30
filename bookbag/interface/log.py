from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.utils.encoding import force_unicode

def log_addition(user, object, msg):
    _log(user, object, ADDITION, msg)
        
def log_change(user, object, msg):
    _log(user, object, CHANGE, msg)

def log_deletion(user, object, msg):
    _log(user, object, DELETION, msg)
    
def _log(user, object, action, msg):
    if object:
        content_type = ContentType.objects.get_for_model(object)
    else:
        content_type = None
    LogEntry.objects.log_action(
        user_id         = user.pk,
        content_type_id = content_type and content_type.pk or None,
        object_id       = object and object.pk or None,
        object_repr     = force_unicode(object),
        action_flag     = action,
        change_message  = msg
    )
    
