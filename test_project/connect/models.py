from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    
    user = models.ForeignKey(User, unique=True, related_name='profile')
    first_name = models.CharField('First Name', max_length=255)
    last_name = models.CharField('Last Name', max_length=255)
    email = models.EmailField('Email')