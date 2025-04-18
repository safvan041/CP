from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("", lambda request: redirect("login")),
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"), 
    path("proceed/<int:kb_id>/", views.proceed_view, name="proceed"),
    path('chat/<slug:widget_slug>/', views.chat_widget_view, name='chat_widget'),
    path('api/chat/<str:widget_slug>/', views.chat_api_view, name='chat_api'),
    
]
