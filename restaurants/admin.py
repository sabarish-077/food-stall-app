from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html, format_html_join
from .models import DiningTable, MenuItem, Offer, Order, OrderItem, Review, TableBooking


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "discount_percent", "is_vegetarian", "is_bestseller", "is_available")
    list_filter = ("category", "is_vegetarian", "is_available")
    search_fields = ("name", "description")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("name", "quantity", "unit_price", "special_instructions")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    change_list_template = "admin/restaurants/order/change_list.html"
    list_display = ("id", "customer_name", "item_summary", "fulfillment", "payment_status", "status", "created_at")
    list_filter = ("status", "fulfillment", "created_at")
    search_fields = ("customer_name", "phone", "items__name")
    list_editable = ("payment_status", "status")
    readonly_fields = ("tracking_token", "created_at")
    inlines = (OrderItemInline,)
    date_hierarchy = "created_at"
    list_per_page = 20
    ordering = ("-created_at",)

    @admin.display(description="Order items")
    def item_summary(self, obj):
        rows = [(line.quantity, line.name) for line in obj.items.all()]
        if not rows:
            return "No items"
        return format_html_join(
            format_html("<br>"),
            '<span class="order-item-chip"><b>{} ×</b> {}</span>',
            rows[:3],
        )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("items")

    def changelist_view(self, request, extra_context=None):
        today = timezone.localdate()
        extra_context = {
            **(extra_context or {}),
            "order_metrics": {
                "today": self.get_queryset(request).filter(created_at__date=today).count(),
                "new": self.get_queryset(request).filter(status="placed").count(),
                "preparing": self.get_queryset(request).filter(status="preparing").count(),
                "completed": self.get_queryset(request).filter(status="completed").count(),
            },
        }
        return super().changelist_view(request, extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        item_names = ", ".join(f"{line.quantity} × {line.name}" for line in obj.items.all())
        detail = f" Items: {item_names}." if item_names else ""
        self.message_user(
            request,
            f"Hello, {obj.customer_name}! Order #{obj.pk} is {obj.get_status_display().lower()}.{detail}",
            level=messages.SUCCESS,
        )


@admin.register(DiningTable)
class DiningTableAdmin(admin.ModelAdmin):
    list_display = ("number", "capacity", "location", "is_active")
    list_filter = ("is_active", "location")


@admin.register(TableBooking)
class TableBookingAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "phone", "table", "date", "time", "guests", "status")
    list_filter = ("status", "date", "table")
    search_fields = ("customer_name", "phone")
    list_editable = ("status",)
    readonly_fields = ("booking_token", "created_at")


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "discount_percent", "minimum_order", "is_active", "expires_at")
    list_filter = ("is_active",)
    search_fields = ("code", "title")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "rating", "is_approved", "created_at")
    list_filter = ("is_approved", "rating")
    list_editable = ("is_approved",)
    search_fields = ("customer_name", "comment")
