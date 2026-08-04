from django import forms

from .models import Product, Shop


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "sku",
            "quantity",
            "unit_price",
            "category",
            "reorder_level",
            "description",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class ShopForm(forms.ModelForm):
    """Used during the shop onboarding flow after registration."""

    class Meta:
        model = Shop
        fields = ["name", "shop_type", "location", "contact_number", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "Brief description of your shop (optional)"}),
            "name": forms.TextInput(attrs={"placeholder": "e.g. Sunrise Grocery Store"}),
            "location": forms.TextInput(attrs={"placeholder": "e.g. 12 Market Street, Nairobi"}),
            "contact_number": forms.TextInput(attrs={"placeholder": "e.g. +254 700 123 456"}),
        }
        labels = {
            "name": "Shop Name",
            "shop_type": "Shop Type",
            "location": "Location / Address",
            "contact_number": "Contact Number",
            "description": "Description",
        }


class ShopEditForm(forms.ModelForm):
    """Used in the profile edit view to update existing shop details."""

    class Meta:
        model = Shop
        fields = ["name", "shop_type", "location", "contact_number", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "name": "Shop Name",
            "shop_type": "Shop Type",
            "location": "Location / Address",
            "contact_number": "Contact Number",
            "description": "Description",
        }
