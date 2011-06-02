import urllib, urllib2

import facebook

from la_facebook.models import UserAssociation

def get_friends_on_site(user):
    """
    Find FB friends that are also using the site. Only works for the currently
    logged in user.
    
    Raises UserAssociation.DoesNotExist and facebook.GraphAPIError
    """
    #raises UserAssociation.DoesNotExist:
    assoc = UserAssociation.objects.get(user=user)
    
    graph = facebook.GraphAPI(assoc.token)
    #raises facebook.GraphAPIError:
    fb_friends = graph.get_connections(assoc.identifier, 'friends')['data']
    
    if fb_friends:
        #filter friends on UserAssociation objects
        site_friends = UserAssociation.objects.filter(identifier__in=[i['id'] for i in fb_friends])
        return site_friends
    return None

def do_fql_query(query, token=None, format='JSON'):
    """
    Perform the fql query on behalf of the given user. If the requested data
    requires a valid access token, one should be aquired before this function
    is called.

    Valid values for format are the default 'JSON' and 'XML'.
    """
    url = 'https://api.facebook.com/method/fql.query?'
    params = {
        'query': query,
        'format': format
    }
    if token is not None:
        params['token'] = token

    params = urllib.urlencode(params)
    url = '{0}{1}'.format(url, params)

    print url

    opener = urllib2.build_opener()
    req = urllib2.Request(url)
    response = opener.open(req)

    if response is not None:
        return response.read()
    return