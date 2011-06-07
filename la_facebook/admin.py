from django.contrib import admin
from django.conf import settings
from la_facebook.models import Friend, UserAssociation

if settings.DEBUG:
    admin.site.register(UserAssociation)
    admin.site.register(Friend)
