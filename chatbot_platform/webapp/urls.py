# webapp/urls.py

from django.urls import path
from webapp import views

from django.contrib.auth import views as auth_views

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
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='webapp/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='webapp/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='webapp/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='webapp/password_reset_complete.html'), name='password_reset_complete'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
]
