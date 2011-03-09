import datetime
from django.test import TestCase

try:
    from mock import Mock, patch
except ImportError:
    raise ImportError("Mock is a requirement for la_facebook tests")

try:
    from django.test.client import RequestFactory
except ImportError:
    raise ImportError("callback tests require Django > 1.3 for RequestFactory")

from django.contrib.auth.models import User, AnonymousUser

from la_facebook.access import OAuthAccess, OAuth20Token
from la_facebook.callbacks.base import BaseFacebookCallback
from la_facebook.models import UserAssociation

factory = RequestFactory()

mock_fetch_user_data = Mock()
mock_fetch_user_data.return_value = {
       "id": "8675309",
       "name": "Herpa Derp",
       "first_name": "Herpa",
       "last_name": "Derp",
       "link": "http://www.facebook.com/herpaderp",
       "gender": "male",
       "locale": "fr_FR"
}

class BaseCallbackTest(TestCase):
    
    urls = 'la_facebook.tests.urls'

    def setUp(self):
        self.request = factory.get('/callback',data={'next':'dummy'})
        test_user = User()
        test_user.username = 'test'
        test_user.email = 'test@test.com'
        test_user.save()
        self.test_user = test_user
        self.anon_user = AnonymousUser()
        self.request.user = test_user
        assoc = UserAssociation()
        assoc.user = test_user
        assoc.token = 'facebooktokenstring'
        assoc.identifier = 'facebookid'
        assoc.expires = datetime.datetime.now() + datetime.timedelta(1)
        assoc.save()
        self.token = OAuth20Token(str(assoc.token), 5555)
        self.access = OAuthAccess()
        
    def test_call(self):
        """ Make sure we get a 302 back from the callback. """
        basecallback = BaseFacebookCallback()
        ret = basecallback(self.request, self.token)
        self.assertEquals(ret.status_code, 302)
        # logger.debug(str(ret._headers['location'][1]))
        self.assertEquals(ret._headers['location'][1], '/dummy' )
        
    def test_redirect_url(self):
        callback = BaseFacebookCallback()
        resp = callback.redirect_url(self.request)
        self.assertEquals(resp,'dummy')
        
    def test_lookup_user_exists(self):
        """ Ok. I guess we'll test this... """
        """ *Crosses fingers* I hope the things I just put in the db in the
        setup method are there """
        callback = BaseFacebookCallback()
        user = callback.lookup_user('facebookid')
        self.assertEquals(user, self.test_user)

    def test_lookup_user_does_not_exist(self):
        """ Ok. I guess we'll test this... """
        callback = BaseFacebookCallback()
        user = callback.lookup_user({'id':'bad-id'})
        self.assertEquals(user,None)
        
    def test_lookup_user_assoc(self):
        """ Ok, I guess we'....nevermind """
        callback = BaseFacebookCallback()
        assoc = callback.lookup_user_assoc('facebookid')
        self.assertEquals(assoc, UserAssociation.objects.get(user=self.test_user))
        
    def test_lookup_user_by_email(self):
        """ Derp... """
        callback = BaseFacebookCallback()
        user = callback.lookup_user_by_email('test@test.com')
        self.assertEquals(user, self.test_user)
        
    
