# Hand-written migration — no auto-generated default needed.
#
# Context: Product.objects.count() == 0 was verified in the live database
# before this migration was authored, so there are no existing rows to
# backfill. The migration therefore does a plain AddField with no RunPython
# data step.
#
# Changes:
#   1. Add shop ForeignKey (NOT NULL) to inventory_product.
#   2. Remove the old global unique index on sku.
#   3. Add unique_together constraint [shop, sku].

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "inventory",
            "0003_supplier_product_updated_at_shop_currency_symbol_and_more",
        ),
    ]

    operations = [
        # 1. Add the shop FK column.
        #    preserve_default=False means the default is only used during the
        #    ALTER TABLE (for any hypothetical existing rows) and is NOT kept
        #    on the model field.  Since the table is empty this default is
        #    never actually written to any row.
        migrations.AddField(
            model_name="product",
            name="shop",
            field=models.ForeignKey(
                help_text="The shop this product belongs to. Set automatically from the logged-in user's profile.",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="products",
                to="inventory.shop",
                default=1,          # placeholder; table is empty — never used
            ),
            preserve_default=False,
        ),
        # 2. Drop the old global unique index on sku.
        migrations.AlterField(
            model_name="product",
            name="sku",
            field=models.CharField(max_length=50),
        ),
        # 3. Add per-shop SKU uniqueness.
        migrations.AlterUniqueTogether(
            name="product",
            unique_together={("shop", "sku")},
        ),
    ]
