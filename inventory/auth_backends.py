from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


class UsernameOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        login_value = username or kwargs.get("email") or kwargs.get("login")
        if not login_value or not password:
            return None

        user = User.objects.filter(
            Q(username__iexact=login_value) | Q(email__iexact=login_value)
        ).first()
        if user is None:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None