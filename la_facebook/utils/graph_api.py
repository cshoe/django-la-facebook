import json, facebook, urllib, urllib2

from django.conf import settings

from la_facebook.models import Friend, UserAssociation
from la_facebook.la_fb_logging import logger
FACEBOOK_SETTINGS = getattr(settings, 'FACEBOOK_ACCESS_SETTINGS', {})

def get_friends_on_site(user):
    """ Find FB friends that are also using the site. """
    try:
        get_friends_internally = FACEBOOK_SETTINGS['STORE_FRIENDS']
    except KeyError:
        get_friends_internally = False

    if get_friends_internally:
        logger.debug('Getting friends internally for {0}'.format(user))
        friend_ids_on_site = Friend.objects.filter(uid1=user).values_list('uid2', flat=True)
        friend_user_associations = UserAssociation.objects.filter(user__pk__in=friend_ids_on_site).all()
        return friend_user_associations
    else:
        logger.debug('Getting friends from Facebook for {0}'.format(user))
        # going to FB for friendships.
        fb_friends = get_friends_on_facebook(user)
        if fb_friends:
            # even though the FQL query says that we should only have user id's that
            # are associated with our app, we're still going to filter against our
            # data in case there is some breakage (FB has them but we don't) 
            site_friends = UserAssociation.objects.filter(identifier__in=[i['uid'] for i in fb_friends])
            return site_friends
    return []

def get_friends_on_facebook(user):
    """
    Go to Facebook to find a user's friends that have registered with the app.
    """
    try:
        assoc = UserAssociation.objects.get(user=user)
    except UserAssociation.DoesNotExist:
        logger.debug('No UserAssociation for {0}'.format(user))
        return None
    
    fql_query = "SELECT uid FROM user WHERE is_app_user AND uid IN (SELECT uid2 FROM friend WHERE uid1 = {0})".format(assoc.identifier)
    fb_friends = json.load(do_fql_query(fql_query, assoc.token))
    if 'error_code' not in fb_friends:
        return fb_friends
    return []

def do_fql_query(query, token=None, format='JSON'):
    """
    Perform the fql query on behalf of the given user. If the requested data
    requires a valid access token, one should be aquired before this function
    is called.

    Valid values for format are the default 'JSON' and 'XML'.
    """
    
    #TODO: NEED ERROR CHECKING
    
    url = 'https://api.facebook.com/method/fql.query?'
    params = {
        'query': query,
        'format': format
    }
    if token is not None:
        params['access_token'] = token

    params = urllib.urlencode(params)
    url = '{0}{1}'.format(url, params)

    opener = urllib2.build_opener()
    req = urllib2.Request(url)
    response = opener.open(req)

    # let error responses out so that other functions can handle them in their own way?
    if response is not None:
        return response
    return