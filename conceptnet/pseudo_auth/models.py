from django.db import models

class LegacyUser(models.Model):
    username = models.CharField(max_length=30)
    password = models.CharField(max_length=128)
    salt = models.CharField(max_length=128,null=True)

    def __unicode__(self):
        return self.username
    class Meta:
        db_table = 'auth_user'
