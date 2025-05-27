# myDjangoAdmin/urls.py
from django.urls import path
from .views import LibraryUserTokenObtainPairView, MeView, UserPendingBooksAPIView, UserRecentViewsAPIView, BookDetailAPIView, UserBookDetailAPIView, update_last_seen, LibraryUserTokenRefreshView, UserFavoriteBooksAPIView, book_by_barcode, api_root, genre_list, books_by_genre, UserBookingCartAPIView, borrow_book, reserve_book, user_borrowing_history
from myserver.views import forgot_password_request_mobile, reset_password_mobile, verify_otp_mobile, signup_user

urlpatterns = [
    path('', api_root, name='api-root'),
    path('me/', MeView.as_view(), name='libraryuser_me'),
    path("signup/user/", signup_user, name='signup_user'),
    path('genres/', genre_list, name='genre-list'),
    path('genres/books/', books_by_genre, name='books-by-genre'),
    path('books/<uuid:pk>/', BookDetailAPIView.as_view(), name='book-detail'),
    path('update-last-seen/', update_last_seen, name='update_last_seen'),
    path('user/<int:user_id>/borrow/', borrow_book, name='borrow-book'),
    path('user/<int:user_id>/reserve/', reserve_book, name='reserve-book'),
    path('user/verify-otp/', verify_otp_mobile, name='verify_otp_mobile'),
    path('user/reset-password/', reset_password_mobile, name='reset_password_mobile'),
    path('user/forgot-password/', forgot_password_request_mobile, name='forgot_password_mobile'),
    path('api/token/', LibraryUserTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', LibraryUserTokenRefreshView.as_view(), name='token_refresh'),
    path('books/barcode/<str:barcode>/', book_by_barcode, name='book-by-barcode'),
    path('user/<int:user_id>/history/', user_borrowing_history, name='user-borrowing-history'),
    path('user/<int:user_id>/recent-views/', UserRecentViewsAPIView.as_view(), name='user-recent-views'),
    path('user/<int:user_id>/pending-books/', UserPendingBooksAPIView.as_view(), name='user-pending-books'),
    path('user/<int:user_id>/booking-cart/', UserBookingCartAPIView.as_view(), name='user-booking-cart'),
    path('user/<int:user_id>/favorite-books/', UserFavoriteBooksAPIView.as_view(), name='user-favorite-books'),
    path('user/<int:user_id>/books/<uuid:book_id>/', UserBookDetailAPIView.as_view(), name='user-book-detail'),
]


