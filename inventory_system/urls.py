"""
URL configuration for inventory_system project.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("inventory.urls")),
    path("admin/", admin.site.urls),
]

handler404 = "inventory.views.custom_404_view"
