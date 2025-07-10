# webapp/urls.py

from django.urls import path
from webapp import views

urlpatterns = [
    path("upload/", views.home_view, name="upload"),
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("proceed/<int:kb_id>/", views.proceed_view, name="proceed"),
    path("chat/<slug:widget_slug>/", views.chat_widget_view, name="chat_widget"),
    path("api/chat/<str:widget_slug>/", views.chat_api_view, name="chat_api"),
    path("get-widget-api/<slug:widget_slug>/", views.get_widget_api_view, name="get_widget_api"),
    path("delete/<int:kb_id>/", views.delete_kb_view, name="delete_kb"),
]
