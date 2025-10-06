
from django.urls import path
from . import views

urlpatterns = [
    path("", views.daemon_dashboard, name="daemon_dashboard"),
]
