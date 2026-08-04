from django.contrib.auth.models import User
from django.db import models


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


class Product(models.Model):
	name = models.CharField(max_length=120)
	sku = models.CharField(max_length=50, unique=True)
	quantity = models.PositiveIntegerField(default=0)
	unit_price = models.DecimalField(max_digits=10, decimal_places=2)
	category = models.CharField(max_length=80, blank=True)
	reorder_level = models.PositiveIntegerField(default=0)
	description = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"{self.name} ({self.sku})"
