from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authenticate against settings.AUTH_USER_MODEL using either a username or an email.
    An identifier containing '@' is looked up as an email (case-insensitive; an exact-case
    match wins if legacy rows differ only by case); otherwise as a username (exact match
    first, then a unique case-insensitive match). Inactive users are rejected.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get('email')
        if not username or not password:
            return None

        field = 'email' if '@' in username else 'username'
        user = UserModel.objects.filter(**{field: username}).first()
        if user is None:
            candidates = list(UserModel.objects.filter(**{f'{field}__iexact': username})[:2])
            user = candidates[0] if len(candidates) == 1 else None

        if user is None:
            # Run the hasher anyway so response time does not reveal whether the account exists.
            UserModel().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
