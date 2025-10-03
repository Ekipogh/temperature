from django.urls import path

from . import views

urlpatterns = [
    path("<str:device_name>/", views.device_detail, name="device_detail"),
]
