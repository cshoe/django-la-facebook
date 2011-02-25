import datetime

from django.db import models

from django.contrib.auth.models import User


class UserAssociation(models.Model):
    
    user = models.ForeignKey(User, unique=True)
    identifier = models.CharField(max_length=255, db_index=True)
    token = models.CharField(max_length=200)
    expires = models.DateTimeField(null=True)
    
    def expired(self):
        return datetime.datetime.now() < self.expires
    
    @property
    def clean_identifier(self):
        """
        Strip fb- out of identifier.
        
        Should this be done in the save method? Is there a reason to store fb-?
        """
        return self.identifier.replace('fb-', '')