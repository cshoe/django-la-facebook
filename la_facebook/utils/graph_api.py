import json, urllib, urllib2

import facebook

from la_facebook.models import UserAssociation

def get_friends_on_site(user):
    """
    Find FB friends that are also using the site. Only works for the currently
    logged in user.
    
    Raises UserAssociation.DoesNotExist and facebook.GraphAPIError
    """
    
    fb_friends = get_friends_on_facebook(user)
    
    if fb_friends:
        # even though the FQL query says that we should only have user id's that
        # are associated with our app, we're still going to filter against our
        # data in case there is some breakage (FB has them but we don't) 
        site_friends = UserAssociation.objects.filter(identifier__in=[i['uid'] for i in fb_friends])
        return site_friends
    return None

def get_friends_on_facebook(user):
    #raises UserAssociation.DoesNotExist:
    # TODO: NEED ERROR CHECKING
    assoc = UserAssociation.objects.get(user=user)
    
    fql_query = "SELECT uid FROM user WHERE is_app_user AND uid IN (SELECT uid2 FROM friend WHERE uid1 = {0})".format(assoc.identifier)
    fb_friends = json.load(do_fql_query(fql_query, assoc.token))
    return fb_friends

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

    if response is not None:
        return response
    return