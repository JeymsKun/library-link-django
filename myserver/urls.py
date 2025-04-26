# myserver/urls.py
from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('', lambda request: redirect('login/')),
    path('login/', views.login_page, name='login'),
    path("login/staff/", views.login_staff, name="login_staff"),
    path("staff/home/", views.staff_home, name="staff_home"),
    path('staff/logout/', views.logout_staff, name='logout_staff'),
    path('login/user/', views.login_user, name='login_user'),
    path('signup/user/', views.user_signup, name='user_signup'),
    path('user/logout/', views.logout_user, name='logout_user'),
    path("user/home/", views.user_home, name="user_home"),
]
