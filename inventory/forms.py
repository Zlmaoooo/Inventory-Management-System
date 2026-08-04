from django import forms

from .models import Product, Shop, Supplier, Transaction


class ProductForm(forms.ModelForm):
    """Add a new product to the catalog."""

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


class ProductEditForm(forms.ModelForm):
    """Edit an existing product (same fields, separate form for clarity)."""

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


class SupplierForm(forms.ModelForm):
    """Add or edit a supplier."""

    class Meta:
        model = Supplier
        fields = ["name", "contact_email", "phone", "address"]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "name": "Supplier Name",
            "contact_email": "Contact Email",
            "phone": "Phone Number",
            "address": "Address",
        }


class TransactionInForm(forms.Form):
    """Stock-In form: move stock into inventory."""

    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        empty_label="Select a product…",
        label="Product",
    )
    quantity = forms.IntegerField(min_value=1, label="Quantity to Add")
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.all(),
        required=False,
        empty_label="No supplier (optional)…",
        label="Supplier",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Optional notes…"}),
        label="Notes",
    )


class TransactionOutForm(forms.Form):
    """Stock-Out form: remove stock from inventory."""

    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        empty_label="Select a product…",
        label="Product",
    )
    quantity = forms.IntegerField(min_value=1, label="Quantity to Remove")
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Optional notes…"}),
        label="Notes",
    )

    def clean(self):
        cleaned = super().clean()
        product = cleaned.get("product")
        qty = cleaned.get("quantity")
        if product and qty and qty > product.quantity:
            raise forms.ValidationError(
                f"Cannot remove {qty} units — only {product.quantity} in stock."
            )
        return cleaned


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
        fields = ["name", "shop_type", "location", "contact_number", "description", "currency_symbol"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "name": "Shop Name",
            "shop_type": "Shop Type",
            "location": "Location / Address",
            "contact_number": "Contact Number",
            "description": "Description",
            "currency_symbol": "Currency Symbol",
        }
