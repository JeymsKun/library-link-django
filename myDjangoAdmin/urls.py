# myDjangoAdmin/urls.py
from django.urls import path
from .views import LibraryUserTokenObtainPairView, MeView, UserPendingBooksAPIView, UserRecentViewsAPIView, BookDetailAPIView, UserBookDetailAPIView, update_last_seen, LibraryUserTokenRefreshView, UserFavoriteBooksAPIView, book_by_barcode

urlpatterns = [
    path('me/', MeView.as_view(), name='libraryuser_me'),
    path('api/token/', LibraryUserTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', LibraryUserTokenRefreshView.as_view(), name='token_refresh'),
    path('update-last-seen/', update_last_seen, name='update_last_seen'),
    path('books/<uuid:pk>/', BookDetailAPIView.as_view(), name='book-detail'),
    path('books/barcode/<str:barcode>/', book_by_barcode, name='book-by-barcode'),
    path('user/<int:user_id>/recent-views/', UserRecentViewsAPIView.as_view(), name='user-recent-views'),
    path('user/<int:user_id>/pending-books/', UserPendingBooksAPIView.as_view(), name='user-pending-books'),
    path('user/<int:user_id>/books/<uuid:book_id>/', UserBookDetailAPIView.as_view(), name='user-book-detail'), 
    path('user/<int:user_id>/favorite-books/', UserFavoriteBooksAPIView.as_view(), name='user-favorite-books'),

]


