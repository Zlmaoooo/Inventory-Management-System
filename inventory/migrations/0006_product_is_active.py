# Hand-written migration — safe for existing data.
#
# Adds Product.is_active (BooleanField, default=True).
# All existing Product rows become is_active=True automatically — no RunPython
# data migration needed.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0005_product_current_stock_transaction_shop"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
