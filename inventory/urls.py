from django.urls import path

from .views import (
    dashboard_view,
    inventory_view,
    login_view,
    logout_view,
    products_view,
    reports_view,
    root_redirect_view,
    settings_view,
    suppliers_view,
    transactions_view,
    users_view,
)

urlpatterns = [
    path("", root_redirect_view, name="root_redirect"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("products/", products_view, name="products"),
    path("inventory/", inventory_view, name="inventory"),
    path("transactions/", transactions_view, name="transactions"),
    path("suppliers/", suppliers_view, name="suppliers"),
    path("reports/", reports_view, name="reports"),
    path("users/", users_view, name="users"),
    path("settings/", settings_view, name="settings"),
]
