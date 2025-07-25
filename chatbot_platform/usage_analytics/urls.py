# usage_tracking/urls.py

from django.urls import path
from . import views

app_name = 'usage_analytics'

urlpatterns = [
    path('dashboard/', views.usage_dashboard_view, name='usage_dashboard'),
]