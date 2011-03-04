from django import template
from django.contrib.auth.models import User

from la_facebook.models import UserAssociation

register = template.Library()


@register.filter
def authed_via(user):
    if user.is_authenticated():
        try:
            assoc = UserAssociation.objects.get(user=user)
        except UserAssociation.DoesNotExist:
            return False
        return assoc.expired()
    else:
        return False
    
@register.simple_tag
def profile_pic_src(user_obj, image_type='normal'):
    """
    Returns url for user's Facebook profile. The url format is:
    
        http://graph.facebook.com/<fb id>/picture?type=<type>
        
    Valid type values are: small, normal, large.
    """
    if isinstance(user_obj, User):
        try:
            user_assoc = UserAssociation.objects.get(user=user_obj)
        except UserAssociation.DoesNotExist:
            return ''
    elif isinstance(user_obj, UserAssociation):
        user_assoc = user_obj
    else:
        return ''
    return user_assoc.facebook_avatar_src(image_type)