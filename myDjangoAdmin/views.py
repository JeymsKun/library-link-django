# myDjangoAdmin/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from myDjangoAdmin.authentication import LibraryUserJWTAuthentication
from myDjangoAdmin.serializers import LibraryUserSerializer
from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import LibraryUserTokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from myserver.serializers import RecentlyViewedSerializer, BookingCartSerializer
from myDjangoAdmin.authentication import LibraryUserJWTAuthentication
from myserver.models import FavoriteBook, RecentlyViewed, BookingCart, BorrowedBook, ReservedBook

class UserRecentViewsAPIView(APIView):
    authentication_classes = [LibraryUserJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        if str(request.user.id) != str(user_id):
            return Response({"detail": "Not authorized"}, status=403)
        views = RecentlyViewed.objects.filter(user_id=user_id).select_related('book')[:10]
        serializer = RecentlyViewedSerializer(views, many=True, context={"request": request})
        return Response([v['book'] for v in serializer.data])  # Only return book info


class UserPendingBooksAPIView(APIView):
    authentication_classes = [LibraryUserJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        if str(request.user.id) != str(user_id):
            return Response({"detail": "Not authorized"}, status=403)
        cart_items = BookingCart.objects.filter(user_id=user_id).select_related('book')
        serializer = BookingCartSerializer(cart_items, many=True, context={"request": request})
        return Response([c['book'] for c in serializer.data])  # Only return book info

class MeView(APIView):
    authentication_classes = [LibraryUserJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = LibraryUserSerializer(user)
        return Response(serializer.data)

class LibraryUserTokenObtainPairView(TokenObtainPairView):
    serializer_class = LibraryUserTokenObtainPairSerializer



# Create your views here.
