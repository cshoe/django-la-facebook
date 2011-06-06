import datetime
import facebook

from django.db import models
from django.contrib.auth.models import User
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField
from django.utils.translation import ugettext_lazy as _

class UserAssociation(models.Model):
    
    user = models.ForeignKey(User, unique=True)
    identifier = models.CharField(max_length=255, db_index=True)
    token = models.CharField(max_length=200)
    expires = models.DateTimeField(null=True)
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    
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
        """ Silly but it makes templates so much easier for the time being """
        return self.facebook_avatar_src("large")
    
    @property
    def normal_avatar(self):
        """ Silly but it makes templates so much easier for the time being """
        return facebook_avatar_src("normal")
    
    @property
    def small_avatar(self):
        """ Silly but it makes templates so much easier for the time being """
        return facebook_avatar_src("small")
    
    def facebook_avatar_src(self, size="normal"):
        url = 'http://graph.facebook.com/{0}/picture?type={1}'
        return url.format(self.identifier, size)
    
    def __unicode__(self):
        return 'UserAssociation for {0}'.format(self.user)
    
class Friend(models.Model):
    """
    Facebook friend relationships that exist within the app.
    
    Columns are named like the Facebook Friends table.
    uid1 is the user you would typically have.
    uid2 corresponds to the friend(s) of the user you have.
    
    """
    uid1 = models.ForeignKey(User, related_name='uid1_set')
    uid2 = models.ForeignKey(User, related_name='uid2_set')
    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))
    
    def __unicode__(self):
        return '{0} is friends with {1}'.format(self.uid1, self.uid2)