from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    email is enforced unique. date_joined (from AbstractUser) tracks creation time.
    avatar and institution fields added for researcher profile support.
    """
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    institution = models.TextField(blank=True)

    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username
