from django.contrib.auth.models import AbstractBaseUser
from django.db import models


class User(AbstractBaseUser):
    USERNAME_FIELD = "username"
    username = models.TextField(blank=False)
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    institution = models.TextField(blank=True)
    REQUIRED_FIELDS = ["email"]
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.username
