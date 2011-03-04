import facebook

from la_facebook.models import UserAssociation

def get_friends_on_site(user):
    """
    Find FB friends that are also using the site. Only works for the currently
    logged in user.
    """
    try:
        assoc = UserAssociation.objects.get(user=user)
    except UserAssociation.DoesNotExist:
        return None
    graph = facebook.GraphAPI(assoc.token)
    
    #'me' here designates the currently logged in user
    fb_friends = graph.get_connections('me', 'friends')['data']
    if fb_friends:
        #filter friends on UserAssociation objects
        site_friends = UserAssociation.objects.filter(identifier__in=[i['id'] for i in fb_friends])
        return site_friends
    return None    