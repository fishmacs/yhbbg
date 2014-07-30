from django.db import models
from django.contrib.auth.models import User

from common.models import Courseware

class FavoriteStuff(models.Model):
    user = models.ForeignKey(User)
    courseware = models.ForeignKey(Courseware, blank=True, null=True)
    type = models.CharField(max_length=20)
    detail = models.TextField(blank=True, null=True)
    detail_hash = models.CharField(max_length=64, blank=True, null=True)
    save_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'favorite'


class TempFile(models.Model):
    type = models.CharField(max_length=16)
    obj_id = models.IntegerField()
    user = models.ForeignKey(User, blank=True, null=True)
    path = models.CharField(max_length=128)
    modified_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tempfile'
        unique_together = ('type', 'obj_id',)

