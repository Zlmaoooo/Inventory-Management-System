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
    list_display = ("name", "sku", "current_stock", "unit_price", "category", "reorder_level", "shop", "created_at")
    search_fields = ("name", "sku", "category")
    list_filter = ("category", "shop")
    # current_stock must NEVER be hand-edited in the admin — it is the
    # exclusive responsibility of the Transaction post_save signal.
    # Listing it in readonly_fields means it is visible for inspection
    # but cannot be modified through the admin panel.
    readonly_fields = ("current_stock", "created_at", "updated_at")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("product", "shop", "type", "quantity", "supplier", "created_by", "timestamp")
    list_filter = ("type", "shop")
    search_fields = ("product__name", "product__sku")
    # Transactions are immutable — all fields are read-only after creation.
    # The admin can view history but cannot alter any transaction record.
    readonly_fields = ("product", "shop", "type", "quantity", "notes", "supplier", "created_by", "timestamp")

    def has_change_permission(self, request, obj=None):
        """Prevent any edits to existing Transaction records through the admin."""
        return False
