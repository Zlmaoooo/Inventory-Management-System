from django.contrib.auth.models import User
from django.db import models
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver


class Shop(models.Model):
    """Represents a business / shop that owns this Invenza account."""

    SHOP_TYPE_CHOICES = [
        ("Grocery", "Grocery"),
        ("Retail", "Retail"),
        ("Pharmacy", "Pharmacy"),
        ("Electronics", "Electronics"),
        ("Other", "Other"),
    ]

    name = models.CharField(max_length=120)
    shop_type = models.CharField(max_length=20, choices=SHOP_TYPE_CHOICES)
    location = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=30)
    description = models.TextField(blank=True)
    currency_symbol = models.CharField(max_length=5, default="$")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.shop_type})"


class Profile(models.Model):
    """Extends the built-in User with shop membership and role information."""

    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("worker", "Worker"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    shop = models.ForeignKey(
        Shop, on_delete=models.SET_NULL, null=True, blank=True, related_name="members"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="owner")

    def __str__(self):
        return f"{self.user.username} — {self.role}"


class Supplier(models.Model):
    """A vendor or supply partner who provides stock to the shop."""

    name = models.CharField(max_length=120)
    contact_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    """A product/SKU tracked in inventory.

    Every product belongs to exactly one Shop — this is the core data-isolation
    boundary. The shop FK is set automatically by the view (never exposed in
    the UI form) so a user can only ever see and manage products belonging to
    their own shop.

    current_stock is the live quantity on hand. It must NEVER be edited
    directly via any form or the admin panel — it is only updated atomically
    by the post_save signal on Transaction. This invariant is enforced by:
      - ProductForm / ProductEditForm not including current_stock in fields.
      - ProductAdmin listing current_stock in readonly_fields.
    """

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="products",
        help_text="The shop this product belongs to. Set automatically from the logged-in user's profile.",
    )
    name = models.CharField(max_length=120)
    # sku is unique *within* a shop, not globally — two shops may use the same
    # SKU scheme independently.
    sku = models.CharField(max_length=50)
    # current_stock is managed exclusively via Transactions — never edit directly.
    current_stock = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=80, blank=True)
    reorder_level = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        # Enforce SKU uniqueness per shop (not globally)
        unique_together = [["shop", "sku"]]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def is_low_stock(self):
        return self.current_stock <= self.reorder_level

    @property
    def stock_status(self):
        if self.current_stock == 0:
            return "critical"
        if self.current_stock <= self.reorder_level:
            return "low"
        return "ok"

    @property
    def stock_value(self):
        return self.current_stock * self.unit_price


class Transaction(models.Model):
    """Records every stock movement (IN or OUT) for a full audit trail.

    Transactions are immutable once created — no edits, no deletes.
    The post_save signal below is the single source of truth for updating
    Product.current_stock. This means the invariant holds regardless of
    whether the Transaction is created via the app views, Django admin,
    a management command, or a future API.
    """

    TYPE_CHOICES = [
        ("IN", "Stock In"),
        ("OUT", "Stock Out"),
    ]

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="transactions"
    )
    # Denormalised shop FK for efficient shop-scoped queries — must always
    # match product.shop. Set automatically by the view from the session.
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="transactions",
        help_text="Denormalised from product.shop for query efficiency. Set automatically by the view.",
    )
    type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    notes = models.TextField(blank=True)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
        help_text="Only applicable for Stock In",
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="transactions"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.get_type_display()} — {self.quantity}x {self.product.name}"


# ---------------------------------------------------------------------------
# Signal: atomically update Product.current_stock after every Transaction save
# ---------------------------------------------------------------------------

@receiver(post_save, sender=Transaction)
def update_product_stock(sender, instance, created, **kwargs):
    """Atomically adjusts Product.current_stock using F() to prevent race
    conditions on concurrent updates.

    Only fires on creation — transactions are immutable (no edits allowed).
    This signal is the single source of truth for stock movement: it fires
    regardless of how a Transaction is created (view, admin, management
    command, future API), so the invariant is always enforced.
    """
    if not created:
        return

    if instance.type == "IN":
        Product.objects.filter(pk=instance.product_id).update(
            current_stock=F("current_stock") + instance.quantity
        )
    elif instance.type == "OUT":
        # Guard against going negative — validation in the form/view must
        # check current_stock BEFORE allowing an OUT transaction to be saved.
        Product.objects.filter(pk=instance.product_id).update(
            current_stock=F("current_stock") - instance.quantity
        )
