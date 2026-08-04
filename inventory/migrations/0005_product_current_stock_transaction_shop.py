# Hand-written migration — no auto-generated defaults needed.
#
# Context (verified before authoring):
#   Product.objects.count()     == 0  → RenameField is zero-risk
#   Transaction.objects.count() == 0  → AddField (shop FK) needs no RunPython
#
# Changes:
#   1. Rename Product.quantity → Product.current_stock (field type unchanged).
#   2. Add Transaction.shop ForeignKey (NOT NULL, preserve_default=False).
#      The placeholder default=1 is only used by the ALTER TABLE statement;
#      since the table is empty it is never written to any row.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0004_product_shop_fk"),
    ]

    operations = [
        # 1. Rename Product.quantity → Product.current_stock.
        migrations.RenameField(
            model_name="product",
            old_name="quantity",
            new_name="current_stock",
        ),
        # 2. Add Transaction.shop FK.
        #    preserve_default=False: the default=1 is only used for the
        #    ALTER TABLE; it is NOT kept on the model field definition.
        migrations.AddField(
            model_name="transaction",
            name="shop",
            field=models.ForeignKey(
                default=1,
                help_text="Denormalised from product.shop for query efficiency. Set automatically by the view.",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="transactions",
                to="inventory.shop",
            ),
            preserve_default=False,
        ),
    ]
