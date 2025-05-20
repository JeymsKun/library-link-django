# myDjangoAdmin/urls.py

from django.urls import path
from .views import LibraryUserTokenObtainPairView, MeView, UserPendingBooksAPIView, UserRecentViewsAPIView

urlpatterns = [
    path('token/', LibraryUserTokenObtainPairView.as_view(), name='libraryuser_token_obtain_pair'),
    path('me/', MeView.as_view(), name='libraryuser_me'),
    path('user/<int:user_id>/recent-views/', UserRecentViewsAPIView.as_view(), name='user-recent-views'),
    path('user/<int:user_id>/pending-books/', UserPendingBooksAPIView.as_view(), name='user-pending-books'),
]


