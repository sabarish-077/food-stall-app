import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("restaurants", "0002_menuitem_image_url")]

    operations = [
        migrations.AddField("menuitem", "discount_percent", models.PositiveSmallIntegerField(default=0)),
        migrations.AddField("menuitem", "is_bestseller", models.BooleanField(default=False)),
        migrations.AddField("menuitem", "is_new", models.BooleanField(default=False)),
        migrations.AddField("menuitem", "spice_level", models.PositiveSmallIntegerField(default=0, help_text="0 mild, 1 medium, 2 hot, 3 extra hot")),
        migrations.AddField("menuitem", "preparation_minutes", models.PositiveSmallIntegerField(default=15)),
        migrations.AddField("menuitem", "rating", models.DecimalField(decimal_places=1, default=4.8, max_digits=3)),
        migrations.AddField("order", "payment_method", models.CharField(choices=[("cash_on_delivery", "Cash on delivery"), ("pay_at_stall", "Pay at stall")], default="cash_on_delivery", max_length=24)),
        migrations.AddField("order", "payment_status", models.CharField(choices=[("unpaid", "Unpaid"), ("paid", "Paid")], default="unpaid", max_length=12)),
        migrations.AddField("order", "delivery_fee", models.DecimalField(decimal_places=2, default=0, max_digits=8)),
        migrations.AddField("order", "coupon_code", models.CharField(blank=True, max_length=40)),
        migrations.AddField("orderitem", "special_instructions", models.CharField(blank=True, max_length=240)),
        migrations.CreateModel(
            name="DiningTable",
            fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("number", models.CharField(max_length=20, unique=True)), ("capacity", models.PositiveSmallIntegerField()),
                ("location", models.CharField(default="Main area", max_length=80)), ("is_active", models.BooleanField(default=True))],
            options={"ordering": ["number"]},
        ),
        migrations.CreateModel(
            name="Offer",
            fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=40, unique=True)), ("title", models.CharField(max_length=120)),
                ("description", models.CharField(max_length=240)), ("discount_percent", models.PositiveSmallIntegerField(default=0)),
                ("minimum_order", models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ("is_active", models.BooleanField(default=True)), ("expires_at", models.DateTimeField(blank=True, null=True))],
        ),
        migrations.CreateModel(
            name="Review",
            fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("customer_name", models.CharField(max_length=80)), ("rating", models.PositiveSmallIntegerField(default=5)),
                ("comment", models.CharField(max_length=300)), ("is_approved", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True))],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="TableBooking",
            fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("booking_token", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("customer_name", models.CharField(max_length=120)), ("phone", models.CharField(max_length=30)),
                ("date", models.DateField()), ("time", models.TimeField()), ("guests", models.PositiveSmallIntegerField()),
                ("notes", models.CharField(blank=True, max_length=240)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled"), ("completed", "Completed")], default="pending", max_length=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("table", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bookings", to="restaurants.diningtable"))],
            options={"ordering": ["date", "time"]},
        ),
    ]
