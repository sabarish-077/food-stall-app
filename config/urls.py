from django.contrib import admin
from django.conf import settings
from django.urls import include, path

admin.site.site_header = f"{settings.STALL_NAME} · Staff"
admin.site.site_title = f"{settings.STALL_NAME} Staff Portal"
admin.site.index_title = "Manage your food stall"

urlpatterns = [path("", include("restaurants.web_urls")), path("admin/", admin.site.urls), path("api/", include("restaurants.urls"))]
