from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("restaurants", "0003_restaurant_features")]

    operations = [
        migrations.AddField(
            model_name="order",
            name="total_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
        ),
    ]
