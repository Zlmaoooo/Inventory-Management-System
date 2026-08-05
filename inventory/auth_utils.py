from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Profile


def get_post_auth_redirect_url(request, user, next_url=""):
    if not user.is_authenticated:
        return reverse("landing")

    try:
        profile = user.profile
        if profile.shop is None:
            return reverse("shop_create")
    except Profile.DoesNotExist:
        return reverse("shop_create")

    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url

    return reverse("dashboard")