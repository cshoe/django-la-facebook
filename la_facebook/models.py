import datetime
import facebook

from django.db import models

from django.contrib.auth.models import User


class UserAssociation(models.Model):
    
    user = models.ForeignKey(User, unique=True)
    identifier = models.CharField(max_length=255, db_index=True)
    token = models.CharField(max_length=200)
    expires = models.DateTimeField(null=True)
    
    def __init__(self, *args, **kwargs):
        self.fb_profile = None
        super(UserAssociation, self).__init__(*args, **kwargs)
    
    def expired(self):
        return datetime.datetime.now() < self.expires
    
    @property
    def facebook_profile(self):
        if self.fb_profile == None:
            try:
                #This is instantiated without a token in case the user's
                #session with FB is dead. We should still be able to get basic
                #profile info unless they have crazy privacy settings.
                graph = facebook.GraphAPI()
                self.fb_profile = graph.get_object(self.identifier)
            except:
                return None
        return self.fb_profile
    
    @property
    def large_avatar(self):
        """ Silly but it makes templates so much easier. """
        return self.facebook_avatar_src("large")
    
    def facebook_avatar_src(self, size="normal"):
        url = 'http://graph.facebook.com/{0}/picture?type={1}'
        return url.format(self.identifier, size)