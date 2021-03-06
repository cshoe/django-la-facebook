from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

import facebook

from la_facebook.access import OAuthAccess
from la_facebook.exceptions import MissingToken
from la_facebook.la_fb_logging import logger
from la_facebook.models import UserAssociation
from la_facebook.utils.graph_api import get_friends_on_site, do_fql_query


def facebook_login(request, redirect_field_name="next",
                        redirect_to_session_key="redirect_to"):
    """
        1. access OAuth
        2. set token to none
        3. store and redirect to authorization url
        4. redirect to OAuth authorization url
    """

    access = OAuthAccess()
    token = None
    if hasattr(request, "session"):
        logger.debug("la_facebook.views.facebook_login: request has session")
        # this session variable is used by the callback
        request.session[redirect_to_session_key] = request.GET.get(redirect_field_name)
    return HttpResponseRedirect(access.authorization_url(token))


def facebook_callback(request, error_template_name="la_facebook/fb_error.html"):
    """
        1. define RequestContext
        2. access OAuth
        3. check session
        4. autheticate token
        5. raise exception if missing token
        6. return access callback
        7. raise exception if mismatch token
        8. render error
    """
    ctx = RequestContext(request)
    access = OAuthAccess()
    # TODO: Check to make sure the session cookie is setting correctly
    unauth_token = request.session.get("unauth_token", None)
    try:
        auth_token = access.check_token(unauth_token, request.GET)
    except MissingToken:
        ctx.update({"error": "token_missing"})
        logger.error('la_facebook.views.facebook_callback: missing token')
    else:
        if auth_token:
            logger.debug('la_facebook.views.facebook_callback: token success '\
                    ', sending to callback')
            return access.callback(request, auth_token)
        else:
            # @@@ not nice for OAuth 2
            ctx.update({"error": "token_mismatch"})
            logger.error('la_facebook.views.facebook_callback: token mismatch'\
                    ', error getting token, or user denied FB login')

    # we either have a missing token or a token mismatch
    # Facebook provides some error details in the callback URL
    fb_errors = []
    for fb_error_detail in ['error', 'error_description', 'error_reason']:
        if fb_error_detail in request.GET:
            ctx['fb_' + fb_error_detail] = request.GET[fb_error_detail]
            fb_errors.append(request.GET[fb_error_detail])

    logger.warning('la_facebook.views.facebook_callback: %s'
            % ', '.join(fb_errors))

    # Can't change to 401 error because that prompts basic browser auth
    return render_to_response(error_template_name, ctx)

def facebook_friends(request, username=None,
                     success_template_name="la_facebook/friends.html",
                     no_fb_template_name="la_facebook/no_fb_profile.html",
                     token_error_template_name="la_facebook/token_error.html"):
    """ Get Facebook friends that are also on the site. """
    if username is None:
        username = request.user.username
    user = get_object_or_404(User, username=username)

    try:
        assocs = get_friends_on_site(user)
    except UserAssociation.DoesNotExist:
        #we don't know this users Facebook profile
        return render_to_response(no_fb_template_name,
                              context_instance=RequestContext(request))
    except facebook.GraphAPIError:
        #token for this user has expired or something else went wrong
        #communicating with FB.
        return render_to_response(token_error_template_name,
                              context_instance=RequestContext(request))

    return render_to_response(success_template_name, {"friend_owner": user,"friends": assocs},
                              context_instance=RequestContext(request))