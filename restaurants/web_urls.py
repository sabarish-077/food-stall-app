from django.urls import path
from .views import customer_login, customer_logout, customer_register, kitchen_board, menu_item_detail, staff_dashboard, staff_orders, storefront

urlpatterns = [
    path("", storefront, name="storefront"),
    path("food/<int:item_id>/", menu_item_detail, name="menu_item_detail"),
    path("account/login/", customer_login, name="customer_login"),
    path("account/register/", customer_register, name="customer_register"),
    path("account/logout/", customer_logout, name="customer_logout"),
    path("staff/", staff_dashboard, name="staff_dashboard"),
    path("staff/orders/", staff_orders, name="staff_orders"),
    path("staff/kitchen/", kitchen_board, name="kitchen_board"),
]
