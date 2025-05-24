# myserver/urls.py
from django.urls import path
from django.shortcuts import redirect
from .views import favorite_books
from . import views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('', lambda request: redirect('login/')),
    path('signup/user/email-confirmation/', views.otp_confirm, name='otp_confirm'),
    path('user/forgot-password/', views.forgot_password_request, name='forgot_password'),
    path('user/reset-password/', views.reset_password, name='reset_password'),
    path('login/', views.login_page, name='login'),
    path('about/', views.about, name='about'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('report-issue/', views.report_issue, name='report_issue'),
    path('help/', views.help, name='help'),
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
    path("user/borrowing-history/", views.user_borrowinghistory, name="user_borrowinghistory"),
    path("user/barcode/", views.user_barcode, name="user_barcode"),
    path("user/library/", views.user_library, name="user_library"),
    path('user/library/book/<uuid:pk>/', views.book_detail, name='book_detail'),
    path('toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('clear-recently-viewed/', views.clear_recently_viewed, name='clear_recently_viewed'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('user/book/book-cart/', views.book_cart, name='book_cart'),
    path('user/logout/', views.logout_user, name='logout_user'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/<int:user_id>/favorite-books/', favorite_books),
    path('staff/booking-requests/', views.booking_requests_view, name='booking_requests'),
    path('staff/approve-request/', views.approve_request, name='approve_request'),
    path('staff/cancel-request/', views.cancel_request, name='cancel_request'),
]
