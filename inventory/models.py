from django.db import models


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
