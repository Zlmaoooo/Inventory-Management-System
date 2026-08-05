from allauth.account.adapter import DefaultAccountAdapter

from .auth_utils import get_post_auth_redirect_url


class InventoryAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        return get_post_auth_redirect_url(request, request.user)