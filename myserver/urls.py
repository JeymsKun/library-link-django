# myserver/urls.py
from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('', lambda request: redirect('login/')),
    path('signup/user/email-confirmation/', views.otp_confirm, name='otp_confirm'),
    path('user/forgot-password/', views.forgot_password_request, name='forgot_password'),
    path('user/reset-password/', views.reset_password, name='reset_password'),
    path('login/', views.login_page, name='login'),
    path("login/staff/", views.login_staff, name="login_staff"),
    path("staff/home/", views.staff_home, name="staff_home"),
    path("staff/addbook/", views.staff_addbook, name="staff_addbook"),
    path("staff/barcode/", views.staff_barcode, name="staff_barcode"),
    path("staff/transaction/", views.staff_transaction, name="staff_transaction"),
    path("staff/booklist", views.staff_booklist, name="staff_booklist"),
    path('staff/logout/', views.logout_staff, name='logout_staff'),
    path('login/user/', views.login_user, name='login_user'),
    path('signup/user/', views.user_signup, name='user_signup'),
    path("user/home/", views.user_home, name="user_home"),
    path("user/booking/", views.user_booking, name="user_booking"),
    path("user/library/", views.user_library, name="user_library"),
    path('user/library/book/<uuid:pk>/', views.book_detail, name='book_detail'),
    path('user/logout/', views.logout_user, name='logout_user'),
]
