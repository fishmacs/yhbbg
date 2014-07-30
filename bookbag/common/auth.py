from django.contrib.auth.backends import ModelBackend

import global_def

class AuthBackend(ModelBackend):
    def authenticate(self, username=None, password=None):
        user = ModelBackend.authenticate(self, username, password)
        if user:
            profile = user.userprofile
            if profile.usertype in [global_def.USERTYPE_STUDENT, global_def.USERTYPE_TEACHER, global_def.USERTYPE_PARENT]:
                return user
        return None