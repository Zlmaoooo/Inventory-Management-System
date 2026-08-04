from django import forms

from .models import Product, Shop, Supplier, Transaction


class ProductForm(forms.ModelForm):
    """Add a new product to the catalog.

    current_stock is deliberately excluded — new products start at 0 and
    stock is only ever adjusted via Transactions. The shop field is also
    excluded and injected by the view from the logged-in user's session.
    """

    class Meta:
        model = Product
        fields = [
            "name",
            "sku",
            "unit_price",
            "category",
            "reorder_level",
            "description",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "Optional product description…"}),
            "name": forms.TextInput(attrs={"placeholder": "e.g. Basmati Rice 5kg"}),
            "sku": forms.TextInput(attrs={"placeholder": "e.g. RICE-001"}),
            "unit_price": forms.NumberInput(attrs={"step": "0.01", "placeholder": "0.00"}),
            "category": forms.TextInput(attrs={"placeholder": "e.g. Grains"}),
        }
        labels = {
            "sku": "SKU (Stock Keeping Unit)",
            "unit_price": "Unit Price",
            "reorder_level": "Reorder Level",
        }


class ProductEditForm(forms.ModelForm):
    """Edit existing product metadata.

    current_stock is excluded — it is read-only and managed exclusively
    via Transactions. The shop field is injected by the view.
    """

    class Meta:
        model = Product
        fields = [
            "name",
            "sku",
            "unit_price",
            "category",
            "reorder_level",
            "description",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "sku": "SKU (Stock Keeping Unit)",
            "unit_price": "Unit Price",
            "reorder_level": "Reorder Level",
        }


class StockInForm(forms.Form):
    """Record a stock-IN movement (stock arriving into inventory).

    The product queryset is scoped to the user's shop at instantiation time
    — the class-level queryset is overridden in __init__ to prevent cross-shop
    product leakage.
    """

    product = forms.ModelChoiceField(
        queryset=Product.objects.none(),   # overridden in __init__
        empty_label="Select a product…",
        label="Product",
    )
    quantity = forms.IntegerField(min_value=1, label="Quantity to Add")
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Optional notes…"}),
        label="Notes",
    )

    def __init__(self, *args, shop=None, **kwargs):
        super().__init__(*args, **kwargs)
        if shop is not None:
            self.fields["product"].queryset = Product.objects.filter(shop=shop)


class StockOutForm(forms.Form):
    """Record a stock-OUT movement (stock leaving inventory).

    Validates that the requested quantity does not exceed current_stock.
    The product queryset is shop-scoped at instantiation, same as StockInForm.
    """

    product = forms.ModelChoiceField(
        queryset=Product.objects.none(),   # overridden in __init__
        empty_label="Select a product…",
        label="Product",
    )
    quantity = forms.IntegerField(min_value=1, label="Quantity to Remove")
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Optional notes…"}),
        label="Notes",
    )

    def __init__(self, *args, shop=None, **kwargs):
        super().__init__(*args, **kwargs)
        if shop is not None:
            self.fields["product"].queryset = Product.objects.filter(shop=shop)

    def clean(self):
        cleaned = super().clean()
        product = cleaned.get("product")
        qty = cleaned.get("quantity")
        if product and qty and qty > product.current_stock:
            raise forms.ValidationError(
                f"Cannot remove {qty} unit(s) — only {product.current_stock} in stock."
            )
        return cleaned


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
