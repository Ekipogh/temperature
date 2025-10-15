from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("basic/", views.basic, name="basic"),
    path("manage/", views.manage_devices, name="manage_devices"),
    path("api/temperature/", views.temeperature_data, name="temperature_data"),
    path("api/historical/", views.historical_data, name="historical_data"),
    path("api/daemon/status/", views.daemon_status, name="daemon_status"),
    path("api/system/status/", views.system_status, name="system_status"),
]
