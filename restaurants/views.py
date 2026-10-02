from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.shortcuts import render
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from datetime import datetime, timedelta
from datetime import date
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, F, Q
from django.core.paginator import Paginator
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import DiningTable, MenuItem, Offer, Order, OrderItem, Review, TableBooking


@ensure_csrf_cookie
def storefront(request):
    return render(request, "restaurants/storefront.html", {
        "stall_name": settings.STALL_NAME,
        "stall_phone": settings.STALL_PHONE,
        "stall_whatsapp": settings.STALL_WHATSAPP,
        "stall_address": settings.STALL_ADDRESS,
        "stall_hours": settings.STALL_HOURS,
        "delivery_fee": settings.DELIVERY_FEE,
    })


def menu_item_detail(request, item_id):
    item = get_object_or_404(MenuItem, pk=item_id, is_available=True)
    return render(request, "restaurants/menu_item_detail.html", {
        "stall_name": settings.STALL_NAME,
        "item": item,
    })


def customer_login(request):
    if request.user.is_authenticated:
        return redirect("storefront")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.get_user())
        return redirect("storefront")
    return render(request, "restaurants/customer_auth.html", {"form": form, "mode": "login", "stall_name": settings.STALL_NAME})


def customer_register(request):
    if request.user.is_authenticated:
        return redirect("storefront")
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        auth_login(request, user)
        messages.success(request, "Your account is ready. Welcome!")
        return redirect("storefront")
    return render(request, "restaurants/customer_auth.html", {"form": form, "mode": "register", "stall_name": settings.STALL_NAME})


@login_required(login_url="customer_login")
def customer_logout(request):
    if request.method == "POST":
        auth_logout(request)
    return redirect("storefront")


@staff_member_required(login_url="/admin/login/")
def staff_dashboard(request):
    today = timezone.localdate()
    today_orders = Order.objects.filter(created_at__date=today)
    month_orders = Order.objects.filter(created_at__date__gte=today.replace(day=1))
    today_sales = OrderItem.objects.filter(order__in=today_orders.exclude(status="cancelled")).aggregate(total=Sum(F("quantity") * F("unit_price")))["total"] or 0
    month_sales = OrderItem.objects.filter(order__in=month_orders.exclude(status="cancelled")).aggregate(total=Sum(F("quantity") * F("unit_price")))["total"] or 0
    best_sellers = OrderItem.objects.exclude(order__status="cancelled").values("name").annotate(quantity=Sum("quantity")).order_by("-quantity")[:5]
    max_seller_count = best_sellers[0]["quantity"] if best_sellers else 1
    return render(request, "restaurants/staff_dashboard.html", {
        "stall_name": settings.STALL_NAME,
        "today": today,
        "today_orders": today_orders.count(),
        "today_sales": today_sales,
        "month_sales": month_sales,
        "pending_orders": Order.objects.filter(status__in=["placed", "confirmed", "preparing"]).count(),
        "completed_orders": Order.objects.filter(status="completed").count(),
        "cancelled_orders": Order.objects.filter(status="cancelled").count(),
        "today_bookings": TableBooking.objects.filter(date=today, status__in=["pending", "confirmed"]).count(),
        "recent_orders": Order.objects.order_by("-created_at")[:8],
        "best_sellers": best_sellers,
        "max_seller_count": max_seller_count,
    })


@staff_member_required(login_url="/admin/login/")
def staff_orders(request):
    status_choices = Order._meta.get_field("status").choices
    payment_choices = Order._meta.get_field("payment_status").choices
    if request.method == "POST":
        order = get_object_or_404(Order, pk=request.POST.get("order_id"))
        new_status = request.POST.get("status")
        new_payment = request.POST.get("payment_status")
        valid_statuses = {value for value, _label in status_choices}
        valid_payment_states = {value for value, _label in payment_choices}
        if new_status in valid_statuses and new_payment in valid_payment_states:
            order.status = new_status
            order.payment_status = new_payment
            order.save(update_fields=["status", "payment_status"])
            messages.success(request, f"Order #{order.id} updated.")
        else:
            messages.error(request, "Choose a valid order and payment status.")
        filters = request.POST.get("filters", "")
        return redirect(f"/staff/orders/{'?' + filters if filters else ''}")

    query = request.GET.get("q", "").strip()
    selected_status = request.GET.get("status", "")
    selected_fulfillment = request.GET.get("fulfillment", "")
    orders = Order.objects.all().prefetch_related("items").order_by("-created_at")
    if query:
        order_filter = Q(customer_name__icontains=query) | Q(phone__icontains=query)
        if query.isdigit():
            order_filter |= Q(id=int(query))
        order_filter |= Q(items__name__icontains=query)
        orders = orders.filter(order_filter).distinct()
    if selected_status in {value for value, _label in status_choices}:
        orders = orders.filter(status=selected_status)
    if selected_fulfillment in {"delivery", "pickup"}:
        orders = orders.filter(fulfillment=selected_fulfillment)
    page = Paginator(orders, 20).get_page(request.GET.get("page"))
    totals = {
        "all": Order.objects.count(),
        "new": Order.objects.filter(status="placed").count(),
        "preparing": Order.objects.filter(status="preparing").count(),
        "completed": Order.objects.filter(status="completed").count(),
    }
    filters_query = request.GET.copy()
    filters_query.pop("page", None)
    return render(request, "restaurants/staff_orders.html", {
        "stall_name": settings.STALL_NAME,
        "orders": page,
        "query": query,
        "selected_status": selected_status,
        "selected_fulfillment": selected_fulfillment,
        "status_choices": status_choices,
        "payment_choices": payment_choices,
        "filters": filters_query.urlencode(),
        "totals": totals,
    })


@staff_member_required(login_url="/admin/login/")
def kitchen_board(request):
    kitchen_orders = Order.objects.filter(status__in=["placed", "confirmed", "preparing", "ready"]).prefetch_related("items").order_by("created_at")
    return render(request, "restaurants/kitchen_board.html", {"stall_name": settings.STALL_NAME, "orders": kitchen_orders})

@api_view(["GET"])
def health(request):
    return Response({"status": "ok", "app": "Restaurant App", "message": "API is ready"})


@api_view(["GET"])
def menu(request):
    items = MenuItem.objects.filter(is_available=True)
    data = [{
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "category": item.category,
        "price": str(item.current_price),
        "original_price": str(item.price),
        "discount_percent": item.discount_percent,
        "image_url": item.display_image_url,
        "is_vegetarian": item.is_vegetarian,
        "is_bestseller": item.is_bestseller,
        "is_new": item.is_new,
        "spice_level": item.spice_level,
        "preparation_minutes": item.preparation_minutes,
        "rating": str(item.rating),
    } for item in items]
    return Response(data)


@api_view(["POST"])
def orders(request):
    name = str(request.data.get("customer_name", "")).strip()
    phone = str(request.data.get("phone", "")).strip()
    fulfillment = str(request.data.get("fulfillment", "delivery"))
    address = str(request.data.get("delivery_address", "")).strip()
    payment_method = str(request.data.get("payment_method", "cash_on_delivery"))
    coupon_code = str(request.data.get("coupon_code", "")).strip().upper()
    requested_items = request.data.get("items", [])
    if not name or not phone or fulfillment not in ("delivery", "pickup"):
        return Response({"error": "Name, phone, and a valid fulfillment choice are required."}, status=status.HTTP_400_BAD_REQUEST)
    if payment_method not in ("cash_on_delivery", "pay_at_stall"):
        return Response({"error": "Choose cash on delivery or pay at the stall."}, status=status.HTTP_400_BAD_REQUEST)
    if fulfillment == "delivery" and not address:
        return Response({"error": "Delivery address is required for delivery."}, status=status.HTTP_400_BAD_REQUEST)
    if not isinstance(requested_items, list) or not requested_items:
        return Response({"error": "Add at least one menu item."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        quantities = {}
        for row in requested_items:
            item_id, quantity = int(row["menu_item_id"]), int(row["quantity"])
            if quantity < 1 or quantity > 20:
                raise ValueError
            quantities[item_id] = quantities.get(item_id, 0) + quantity
        if any(quantity > 20 for quantity in quantities.values()):
            raise ValueError
    except (TypeError, ValueError, KeyError):
        return Response({"error": "Each item needs a valid ID and quantity from 1 to 20."}, status=status.HTTP_400_BAD_REQUEST)
    available = {item.id: item for item in MenuItem.objects.filter(id__in=quantities, is_available=True)}
    if len(available) != len(quantities):
        return Response({"error": "One or more items are unavailable. Refresh the menu and try again."}, status=status.HTTP_400_BAD_REQUEST)
    subtotal = sum((available[item_id].current_price * quantity for item_id, quantity in quantities.items()))
    discount = 0
    if coupon_code:
        offer = Offer.objects.filter(code__iexact=coupon_code, is_active=True).first()
        if not offer or (offer.expires_at and offer.expires_at <= timezone.now()) or subtotal < offer.minimum_order:
            return Response({"error": "That offer code is invalid, expired, or your order is below its minimum."}, status=status.HTTP_400_BAD_REQUEST)
        discount = subtotal * offer.discount_percent / 100
    delivery_fee = settings.DELIVERY_FEE if fulfillment == "delivery" else 0
    grand_total = subtotal - discount + delivery_fee
    with transaction.atomic():
        order = Order.objects.create(customer_name=name, phone=phone, delivery_address=address, fulfillment=fulfillment,
            payment_method=payment_method, delivery_fee=delivery_fee, coupon_code=coupon_code, total_amount=grand_total)
        for item_id, quantity in quantities.items():
            item = available[item_id]
            row = next(row for row in requested_items if int(row.get("menu_item_id", 0)) == item_id)
            OrderItem.objects.create(order=order, menu_item=item, name=item.name, quantity=quantity,
                unit_price=item.current_price, special_instructions=str(row.get("special_instructions", ""))[:240])
    return Response({"order_id": order.id, "tracking_token": str(order.tracking_token), "status": order.status,
        "subtotal": str(subtotal), "delivery_fee": str(delivery_fee), "discount": str(discount), "total": str(grand_total)}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def track_order(request, token):
    order = get_object_or_404(Order, tracking_token=token)
    items = list(order.items.all())
    subtotal = sum((line.unit_price * line.quantity for line in items), start=0)
    return Response({
        "order_id": order.id,
        "status": order.status,
        "fulfillment": order.fulfillment,
        "created_at": order.created_at.isoformat(),
        "customer_name": order.customer_name,
        "phone": order.phone,
        "delivery_address": order.delivery_address,
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "items": [{"name": line.name, "quantity": line.quantity, "unit_price": str(line.unit_price),
                   "line_total": str(line.unit_price * line.quantity), "special_instructions": line.special_instructions} for line in items],
        "subtotal": str(subtotal),
        "delivery_fee": str(order.delivery_fee),
        "total": str(order.total_amount) if order.total_amount else None,
    })


@api_view(["POST"])
def cancel_order(request, token):
    with transaction.atomic():
        order = get_object_or_404(Order.objects.select_for_update(), tracking_token=token)
        if order.status not in ("placed", "confirmed"):
            return Response({"error": "This order can no longer be cancelled."}, status=status.HTTP_409_CONFLICT)
        order.status = "cancelled"
        order.save(update_fields=["status"])
    return Response({"order_id": order.id, "status": order.status})


@api_view(["GET"])
def offers(request):
    now = timezone.now()
    active = Offer.objects.filter(is_active=True).filter(models_q_expiry(now))
    return Response([{"code": offer.code, "title": offer.title, "description": offer.description,
        "discount_percent": offer.discount_percent, "minimum_order": str(offer.minimum_order)} for offer in active])


def models_q_expiry(now):
    from django.db.models import Q
    return Q(expires_at__isnull=True) | Q(expires_at__gt=now)


@api_view(["GET"])
def tables(request):
    try:
        day = datetime.strptime(request.query_params["date"], "%Y-%m-%d").date()
        slot = datetime.strptime(request.query_params["time"], "%H:%M").time()
        guests = int(request.query_params.get("guests", 1))
    except (KeyError, ValueError):
        return Response({"error": "Choose a valid date and time."}, status=status.HTTP_400_BAD_REQUEST)
    if guests < 1 or guests > 20:
        return Response({"error": "Guest count must be between 1 and 20."}, status=status.HTTP_400_BAD_REQUEST)
    busy = []
    for booking in TableBooking.objects.filter(date=day, status__in=["pending", "confirmed"]).select_related("table"):
        before = datetime.combine(day, booking.time)
        after = datetime.combine(day, slot)
        if abs((before - after).total_seconds()) < 90 * 60:
            busy.append(booking.table_id)
    available = DiningTable.objects.filter(is_active=True, capacity__gte=guests).exclude(id__in=busy)
    return Response([{"id": table.id, "number": table.number, "capacity": table.capacity, "location": table.location} for table in available])


@api_view(["POST"])
def bookings(request):
    try:
        table_id = int(request.data.get("table_id"))
        guests = int(request.data.get("guests", 0))
        day = datetime.strptime(str(request.data.get("date", "")), "%Y-%m-%d").date()
        slot = datetime.strptime(str(request.data.get("time", "")), "%H:%M").time()
    except (TypeError, ValueError):
        return Response({"error": "Provide a date, time, guest count, and available table."}, status=status.HTTP_400_BAD_REQUEST)
    name, phone = str(request.data.get("customer_name", "")).strip(), str(request.data.get("phone", "")).strip()
    table = DiningTable.objects.filter(id=table_id, is_active=True, capacity__gte=guests).first()
    if day < timezone.localdate() or not name or not phone or not table or guests < 1 or guests > 20:
        return Response({"error": "Check the booking details and available table."}, status=status.HTTP_400_BAD_REQUEST)
    for existing in TableBooking.objects.filter(table=table, date=day, status__in=["pending", "confirmed"]):
        if abs((datetime.combine(day, existing.time) - datetime.combine(day, slot)).total_seconds()) < 90 * 60:
            return Response({"error": "That table was just booked. Please choose another."}, status=status.HTTP_409_CONFLICT)
    booking = TableBooking.objects.create(table=table, date=day, time=slot, guests=guests, customer_name=name,
        phone=phone, notes=str(request.data.get("notes", ""))[:240])
    return Response({"booking_id": booking.id, "booking_token": str(booking.booking_token), "status": booking.status,
        "table": table.number}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def track_booking(request, token):
    booking = get_object_or_404(TableBooking.objects.select_related("table"), booking_token=token)
    return Response({"booking_id": booking.id, "status": booking.status, "customer_name": booking.customer_name,
        "date": booking.date.isoformat(), "time": booking.time.strftime("%H:%M"), "guests": booking.guests,
        "table": booking.table.number})


@api_view(["GET", "POST"])
def reviews(request):
    if request.method == "GET":
        return Response([{"customer_name": review.customer_name, "rating": review.rating, "comment": review.comment}
            for review in Review.objects.filter(is_approved=True)[:8]])
    name = str(request.data.get("customer_name", "")).strip()[:80]
    comment = str(request.data.get("comment", "")).strip()[:300]
    try:
        rating = int(request.data.get("rating", 0))
    except (ValueError, TypeError):
        rating = 0
    if not name or not comment or rating < 1 or rating > 5:
        return Response({"error": "Enter your name, a comment, and a rating from 1 to 5."}, status=status.HTTP_400_BAD_REQUEST)
    Review.objects.create(customer_name=name, comment=comment, rating=rating)
    return Response({"status": "submitted"}, status=status.HTTP_201_CREATED)
