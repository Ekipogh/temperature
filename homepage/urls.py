from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/temperature/', views.temeperature_data, name='temperature_data'),
    path('api/historical/', views.historical_data, name='historical_data'),
]
