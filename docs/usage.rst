=====
Usage
=====

Get ``django-la-facebook`` into your python path::

    pip install django-la-facebook
    
Add ``la_facebook`` to your INSTALLED_APPS in settings.py::

    INSTALLED_APPS = (
        ...
        'la_facebook',
        ...
        )
    
Add ``la_facebook`` to your root urlconf (urls.py)::

    urlpatterns = patterns('',
        ...,
        url(r"^la_facebook/", include("la_facebook.urls")),
        ...,        
    )

Settings
--------

In order to authenticate your site's users with Facebook, you need a unique
identifier for Facebook to associate your site with.  Facebook considers your
site an "app" and so you must acquire an ``FACEBOOK_APP_ID`` and 
``FACEBOOK_APP_SECRET`` from the
`Facebook Developer app <http://www.facebook.com/developers>`_.

You will need to enter your sites domain into the Facebook developer app, and
the site will restrict authentication requests to that domain. For initial
testing and experiments, you will want to enter "http://localhost/" for the
website URL.  For later testing, you will probably want create a staging or
testing subdomain. The domain set here must match the domain entered into
Django's sites framework.

See the documentation for :doc:`settings` about how to enter these values in your 
Django settings file.


Using the default authentication flow
-------------------------------------

By default, the la_facebook application:

 * provides a method of creating a django.contrib.auth user model for an
   authenticated facebook user

 * Updates fields in the model pointed to by the ``AUTH_PROFILE_MODULE``
   setting that match available fields in Facebook's user data.

 * Creates and manages an association object that stores the user's associated
   facebook id, authentication token (which is used to access the information
   in the users facebook profile as authorized by the user), and the expiration
   date of that token.

These steps are handled by directing a user to the la_facebook login view. By
default this view, like Django's login url ``LOGIN_URL``, will use a ``next``
querystring parameter to redirect the browser to a page after user
authenticates with Facebook.

If an error occurs during authentication, or the user denies to authenticate,
the browser is redirected to a template located at
``la_facebook/fb_error.html`` (see the provided template for some information
about what context variables may be provided in the case of an error).

If you wish a more customized behavior for Facebook authentication, see the
:doc:`callbacks` documentation.

Templates
---------

In your login page, or as part of your login form, you should include a link to
the Facebook login view, which will then redirect the user to facebook to login
and authenticate to your site.  A simple example might look like this::

     <p><a href="{% url la_facebook_login %}?next={{ next }}">Login with FaceBook</a></p>

You can used the following image provided by facebook as a graphical link::

    http://static.ak.fbcdn.net/images/fbconnect/login-buttons/connect_light_medium_long.gif

Other than the error template mentioned above, no particular templates are used
or customized.


Template Tags
-------------

TODO

