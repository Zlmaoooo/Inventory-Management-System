from django.contrib import admin

from .models import Product, Profile, Shop, Supplier, Transaction


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("name", "shop_type", "location", "contact_number", "created_at")
    search_fields = ("name", "location")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "shop", "role")
    list_filter = ("role",)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_email", "phone", "created_at")
    search_fields = ("name", "contact_email")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "quantity", "unit_price", "category", "reorder_level", "created_at")
    search_fields = ("name", "sku", "category")
    list_filter = ("category",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("product", "type", "quantity", "supplier", "created_by", "timestamp")
    list_filter = ("type",)
    search_fields = ("product__name", "product__sku")
    readonly_fields = ("timestamp",)
