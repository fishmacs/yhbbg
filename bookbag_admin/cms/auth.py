from django.contrib.auth.backends import ModelBackend

from bookbag.common import global_def as common_def

class AuthBackend(ModelBackend):
    def authenticate(self, username=None, password=None):
        user = ModelBackend.authenticate(self, username, password)
        if user:
            profile = user.get_profile()
            if profile.usertype < common_def.USERTYPE_TEACHER:
                user= None
        return user
