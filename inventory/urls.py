from django.urls import path

from .views import (
    dashboard_view,
    inventory_view,
    landing_view,
    login_view,
    logout_view,
    products_view,
    profile_edit_view,
    profile_view,
    register_view,
    reports_view,
    root_redirect_view,
    settings_view,
    shop_create_view,
    suppliers_view,
    transactions_view,
    users_view,
)

urlpatterns = [
    path("", landing_view, name="landing"),
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("logout/", logout_view, name="logout"),
    path("shop/create/", shop_create_view, name="shop_create"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("products/", products_view, name="products"),
    path("inventory/", inventory_view, name="inventory"),
    path("transactions/", transactions_view, name="transactions"),
    path("suppliers/", suppliers_view, name="suppliers"),
    path("reports/", reports_view, name="reports"),
    path("users/", users_view, name="users"),
    path("settings/", settings_view, name="settings"),
    path("profile/", profile_view, name="profile"),
    path("profile/edit/", profile_edit_view, name="profile_edit"),
]
