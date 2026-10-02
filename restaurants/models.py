from django.db import models
from decimal import Decimalimport uuid
from urllib.parse import urlparse


class MenuItem(models.Model):
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=280, blank=True)
    category = models.CharField(max_length=80, default="Main course")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    discount_percent = models.PositiveSmallIntegerField(default=0)
    image_url = models.URLField(max_length=500, blank=True)
    is_vegetarian = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    is_bestseller = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    spice_level = models.PositiveSmallIntegerField(default=0, help_text="0 mild, 1 medium, 2 hot, 3 extra hot")
    preparation_minutes = models.PositiveSmallIntegerField(default=15)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.8)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return self.name

    @property
    def current_price(self):
        return (self.price * Decimal(100 - self.discount_percent) / Decimal(100)).quantize(Decimal("0.01"))

    @property
    def display_image_url(self):
        """Use local artwork instead of Google share pages, which are not image files."""
        url = (self.image_url or "").strip()
        host = (urlparse(url).hostname or "").lower()
        if url.startswith("https://") and host and host not in {
            "share.google", "photos.app.goo.gl", "goo.gl", "drive.google.com",
        } and not host.endswith(".google.com"):
            return url

        text = f"{self.name} {self.category}".lower()
        if any(word in text for word in ("chai", "tea", "coffee", "drink", "juice")):
            filename = "food-chai.svg"
        elif any(word in text for word in ("shawarma", "wrap", "roll", "kebab")):
            filename = "food-shawarma.svg"
        elif "chicken" in text or "nonveg" in text:
            filename = "food-chicken65.svg"
        elif any(word in text for word in ("samosa", "snack", "savoury", "savory")):
            filename = "food-samosa.svg"
        else:
            filename = "food-dosa.svg"
        return f"/static/restaurants/{filename}"


class Order(models.Model):
    tracking_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    customer_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    delivery_address = models.TextField(blank=True)
    fulfillment = models.CharField(max_length=12, choices=[("delivery", "Delivery"), ("pickup", "Pickup")])
    payment_method = models.CharField(max_length=24, choices=[("cash_on_delivery", "Cash on delivery"), ("pay_at_stall", "Pay at stall")], default="cash_on_delivery")
    payment_status = models.CharField(max_length=12, choices=[("unpaid", "Unpaid"), ("paid", "Paid")], default="unpaid")
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    coupon_code = models.CharField(max_length=40, blank=True)
    status = models.CharField(max_length=20, choices=[
        ("placed", "Placed"), ("confirmed", "Confirmed"), ("preparing", "Preparing"),
        ("ready", "Ready for pickup"), ("out_for_delivery", "Out for delivery"),
        ("completed", "Completed"), ("cancelled", "Cancelled"),
    ], default="placed")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.pk} — {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=120)
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    special_instructions = models.CharField(max_length=240, blank=True)


class DiningTable(models.Model):
    number = models.CharField(max_length=20, unique=True)
    capacity = models.PositiveSmallIntegerField()
    location = models.CharField(max_length=80, default="Main area")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"Table {self.number} ({self.capacity} seats)"


class TableBooking(models.Model):
    STATUS_CHOICES = [("pending", "Pending"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled"), ("completed", "Completed")]
    booking_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    customer_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    table = models.ForeignKey(DiningTable, on_delete=models.PROTECT, related_name="bookings")
    date = models.DateField()
    time = models.TimeField()
    guests = models.PositiveSmallIntegerField()
    notes = models.CharField(max_length=240, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "time"]

    def __str__(self):
        return f"Booking #{self.pk} — {self.customer_name} · {self.date} {self.time}"


class Offer(models.Model):
    code = models.CharField(max_length=40, unique=True)
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=240)
    discount_percent = models.PositiveSmallIntegerField(default=0)
    minimum_order = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.code} — {self.title}"


class Review(models.Model):
    customer_name = models.CharField(max_length=80)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.CharField(max_length=300)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer_name} · {self.rating}/5"
