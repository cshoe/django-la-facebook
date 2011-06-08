import facebook

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect
from django.db.models import get_model
from django.template.defaultfilters import slugify
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.conf import settings

from la_facebook.la_fb_logging import logger
from la_facebook.models import UserAssociation, Friend
from la_facebook.utils.graph_api import get_friends_on_facebook

FACEBOOK_SETTINGS = getattr(settings, 'FACEBOOK_ACCESS_SETTINGS', {})

class BaseFacebookCallback(object):

    FACEBOOK_GRAPH_TARGET = "https://graph.facebook.com/me"
    def __call__(self, request, token):
        user_data = self.fetch_user_data(token)
        expires = hasattr(token, "expires") and token.expires or None
        user_assoc = self.lookup_user_assoc(user_data['id'])
        #user was not logged in to Lofty when they logged into FB
        if request.user.is_authenticated():
            if user_assoc:
                #update token and expires
                self.update_user_association(user_assoc, token, expires)
            else:
                #create UserAssociation tied to request.user
                self.create_user_association(request.user, token, expires, user_data)
        else:
            #find a user based on email if we got it from FB (we should in Lofty).
            #making this general for now so I can move it over to la_facebook later
            if user_assoc:
                #We know this account, update user get associated user and login
                self.update_user_association(user_assoc, token, expires)
                user = self.lookup_user(user_assoc.identifier)
            else:
                if 'email' in user_data:
                    user = self.lookup_user_by_email(user_data['email'])
                    if user:
                        self.create_user_association(user, token, expires, user_data)
                        #Do we want to update profile?
                        #self.update_profile(user, user_data, profile)
                    else:
                        user = self.create_user(request, token, expires, user_data)
                else:
                    user = self.create_user(request, token, expires, user_data)
            self.login_user(request, user)
        try:
            do_friends = FACEBOOK_SETTINGS['STORE_FRIENDS']
        except KeyError:
            pass
        else:
            if do_friends:
                self.do_friends_update(request.user)
        return redirect(self.redirect_url(request))
    
    def do_friends_update(self, user):
        logger.debug('Starting friends update.')
        friends_on_facebook = []
        print 'here'
        for friend in get_friends_on_facebook(user):
            friends_on_facebook.append(friend['uid'])
        print 'here2'
        
        print friends_on_facebook
        friend_ids_on_site = Friend.objects.filter(uid1=user).values_list('uid2', flat=True)
        friend_user_associations = UserAssociation.objects.filter(user__pk__in=friend_ids_on_site)
        
        friends_to_delete = []
        print friend_user_associations
        for ua in friend_user_associations:
            id = ua.identifier
            try:
                friends_on_facebook.index(id)
            except ValueError:
                try:
                    logger.debug('Removing {0} from add list.'.format(id))
                    friends_on_facebook.remove(id)
                except ValueError:
                    logger.debug('Error removing id from friends list.')
                    pass
            else:
                if id not in friends_on_facebook:
                    logger.debug('Adding {0} to delete list.'.format(id))
                    friends_to_delete.append(id)
                
        logger.debug('Adding friends with facebook ids: {0}'.format(friends_on_facebook))
        
        #get user associations for facebook friends to add.
        users = list(UserAssociation.objects.filter(identifier__in=friends_on_facebook).select_related('user'))
        print users
        for u in users:
            Friend.objects.create(uid1=user, uid2=u.user)
            Friend.objects.create(uid1=u.user, uid2=user)
            
        
        #get user associations for facebook friends to delete
        logger.debug('Deleting friends with facebook ids: {0}'.format(friends_to_delete))
        users = list(UserAssociation.objects.filter(identifier__in=friends_to_delete).select_related('user'))
        for u in users:
            Friend.objects.delete(uid1=user, uid2=u.user)
            Friend.objects.delete(uid1=u.user, uid2=user)
    
    def fetch_user_data(self, token):
        graph = facebook.GraphAPI(token)
        return graph.get_object('me')
    
    def lookup_user_assoc(self, fb_id):
        """ Find out UserAssociation object for FB id """
        try:
            assoc = UserAssociation.objects.get(identifier=fb_id)
        except UserAssociation.DoesNotExist:
            return None
        return assoc
    
    def lookup_user(self, fb_id):
        """ Find a user object for a FB id """
        queryset = UserAssociation.objects.all()
        queryset = queryset.select_related("user")
        try:
            assoc = UserAssociation.objects.get(identifier=fb_id)
        except UserAssociation.DoesNotExist:
            return None
        return assoc.user
    
    def lookup_user_by_email(self, fb_email):
        try:
            user = User.objects.get(email=fb_email)
        except User.DoesNotExist:
            return None
        return user
    
    def create_profile(self, user, user_data):
        """ Create user profile if one is defined """
        if hasattr(settings, 'AUTH_PROFILE_MODULE'):
            profile_model = get_model(*settings.AUTH_PROFILE_MODULE.split('.'))

            profile, created = profile_model.objects.get_or_create(
              user = user,
            )
            profile = self.update_profile(user_data, profile)
            profile.save()

        else:
            # Do nothing because users have no site profile defined
            # TODO - should we pass a warning message? Raise a SiteProfileNotAvailable error?
            logger.warning("DefaultFacebookCallback.create_profile: unable to" \
                    "create/update profile as no AUTH_PROFILE_MODULE setting" \
                    "has been defined")
            pass
    
    def update_profile(self, user_data, profile):
        for k, v in user_data.items():
            if k !='id' and hasattr(profile, k):
                setattr(profile, k, v)
                logger.debug("DefaultFacebookCallback.update_profile_from_graph"\
                        ": updating profile %s to %s" % (k,v))
        return profile
    
    def login_user(self, request, user):
        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)
        
    def create_user_association(self, user, token, expires, user_data):
        """ Create UserAssociation """
        assoc = UserAssociation (
                user=user,
                token=str(token),
                expires=expires,
                identifier=user_data['id']
        )
        assoc.save()
        return assoc
        
    def update_user_association(self, assoc, token, expires):
        """ Update UserAssociation token and expires date """
        assoc.token = str(token)
        assoc.expires = expires
        assoc.save()
        
    def create_user(self, request, token, expires, user_data):
        """
        Create a user object for new user that registered via Facebook.
        Do not use this for linking existing Lofty accounts to Facebook
        accounts.
        """
        username = self.get_facebook_username(user_data)
        username = self.validate_facebook_username(username)
        user = User(username=username)
        if 'email' in user_data:
            user.email = user_data['email']
        user.save()
        
        self.create_profile(user, user_data)
        self.create_user_association(user, token, expires, user_data)
        return user
    
    def get_facebook_username(self, user_data):
        """
        user link = http://www.facebook.com/<unique_username>
        This returns <unique_username>
        """
        link = user_data['link']
        id_spot = link.find('profile.php?id=')
        if id_spot == -1:
            return link.split('http://www.facebook.com/')[1]
        return link.split('http://www.facebook.com/profile.php?id=')[1]
    
    def validate_facebook_username(self, fb_username):
        """ Check to see if FB username is already in use on Lofty.com """
        username = fb_username
        count = 1
        while User.objects.filter(username=username).count():
            username = ('{0}{1}').format(username, count)
            count = count + 1
        return username
            
    def get_facebook_locale(self, user_data):
        """
        Return the first 2 letters of the FB locale data
        """
        locale = user_data['locale']
        locale = locale[:1]
        #make sure you support the user's language.

    def redirect_url(self, request, fallback_url=settings.LOGIN_REDIRECT_URL, 
            redirect_field_name="next", session_key_value="redirect_to"):
        """
        Returns the URL to be used in login procedures by looking at different
        values in the following order:

        - a REQUEST value, GET or POST, named "next" by default.
        - LOGIN_REDIRECT_URL - the URL in the setting
        - LOGIN_REDIRECT_URLNAME - the name of a URLconf entry in the settings
        """

        redirect_to = request.REQUEST.get(redirect_field_name)
        if not redirect_to:
            # try the session if available
            if hasattr(request, "session"):
                redirect_to = request.session.get(session_key_value)
        # light security check -- make sure redirect_to isn't garabage.
        if not redirect_to or "://" in redirect_to or " " in redirect_to:
            redirect_to = fallback_url
        return redirect_to

base_facebook_callback = BaseFacebookCallback()