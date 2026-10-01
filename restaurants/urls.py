from django.urls import path
from .views import bookings, health, menu, offers, orders, reviews, tables, track_booking, track_order

urlpatterns = [path("health/", health, name="health"), path("menu/", menu, name="menu"), path("orders/", orders, name="orders")]
urlpatterns += [path("orders/track/<uuid:token>/", track_order, name="track_order")]
urlpatterns += [path("offers/", offers, name="offers"), path("tables/", tables, name="tables"), path("bookings/", bookings, name="bookings"), path("reviews/", reviews, name="reviews")]
urlpatterns += [path("bookings/track/<uuid:token>/", track_booking, name="track_booking")]
