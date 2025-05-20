# myDjangoAdmin/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from myDjangoAdmin.authentication import LibraryUserJWTAuthentication
from myDjangoAdmin.serializers import LibraryUserSerializer, BookSerializer
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import LibraryUserTokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from myserver.serializers import RecentlyViewedSerializer, BookingCartSerializer
from myDjangoAdmin.authentication import LibraryUserJWTAuthentication
from myserver.models import FavoriteBook, RecentlyViewed, BookingCart, BorrowedBook, ReservedBook
from rest_framework.generics import RetrieveAPIView
from .models import Book
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from django.utils import timezone
from myDjangoAdmin.models import UserSessionLog, LibraryUserOutstandingToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from .serializers import LibraryUserTokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework import serializers
from myDjangoAdmin.models import LibraryUser
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def book_by_barcode(request, barcode):
    user_id = request.query_params.get('user_id')

    if not user_id:
        return Response({'detail': 'user_id query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = LibraryUser.objects.get(pk=user_id)
    except LibraryUser.DoesNotExist:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        book = Book.objects.get(barcode_code=barcode)
    except Book.DoesNotExist:
        return Response({'detail': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = BookSerializer(book, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_last_seen(request):
    user = request.user
    user.last_seen = timezone.now()
    user.save()

    device_type = request.data.get('device_type', 'unknown')
    session_id = request.session.session_key or 'N/A'

    UserSessionLog.objects.create(
        library_user=user,
        session_id=session_id,
        action=f"Updated last seen from {device_type}",
    )

    return Response({'status': 'last_seen updated'})

class LibraryUserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response({"detail": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token_obj = LibraryUserOutstandingToken.objects.get(token=refresh_token, user=request.user)
            token_obj.blacklisted = True
            token_obj.save()
            return Response({"detail": "Token blacklisted successfully"}, status=status.HTTP_200_OK)
        except LibraryUserOutstandingToken.DoesNotExist:
            return Response({"detail": "Token not found"}, status=status.HTTP_400_BAD_REQUEST)

class BookDetailAPIView(RetrieveAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_serializer_context(self):
        return {'request': self.request}
    
class UserBookDetailAPIView(RetrieveAPIView):
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Book.objects.all()

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        book_id = self.kwargs.get('book_id')

        if self.request.user.id != user_id:
            raise PermissionDenied("You do not have permission to view this book.")

        try:
            book = Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Book not found.")

        return book
    
class UserRecentViewsAPIView(APIView):
    authentication_classes = [LibraryUserJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        if str(request.user.id) != str(user_id):
            return Response({"detail": "Not authorized"}, status=403)
        views = RecentlyViewed.objects.filter(user_id=user_id).select_related('book')[:10]
        serializer = RecentlyViewedSerializer(views, many=True, context={"request": request})
        return Response([v['book'] for v in serializer.data])  


class UserPendingBooksAPIView(APIView):
    authentication_classes = [LibraryUserJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        if str(request.user.id) != str(user_id):
            return Response({"detail": "Not authorized"}, status=403)
        cart_items = BookingCart.objects.filter(user_id=user_id).select_related('book')
        serializer = BookingCartSerializer(cart_items, many=True, context={"request": request})
        return Response([c['book'] for c in serializer.data])  

class UserFavoriteBooksAPIView(APIView):
    authentication_classes = [LibraryUserJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        if str(request.user.id) != str(user_id):
            return Response({"detail": "Not authorized"}, status=403)

        favorites = FavoriteBook.objects.filter(user_id=user_id).select_related('book')
        data = [BookSerializer(fav.book, context={"request": request}).data for fav in favorites]
        return Response(data)

class MeView(APIView):
    authentication_classes = [LibraryUserJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = LibraryUserSerializer(user)
        return Response(serializer.data)
    
class LibraryUserTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        refresh = self.token_class(attrs["refresh"])

        try:
            user_id = refresh[api_settings.USER_ID_CLAIM]
            user = LibraryUser.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except LibraryUser.DoesNotExist:
            raise serializers.ValidationError("User not found for refresh token")

        token_str = str(refresh)
        if LibraryUserOutstandingToken.objects.filter(token=token_str, blacklisted=True).exists():
            raise serializers.ValidationError("Token is blacklisted")

        return data
    
class LibraryUserTokenObtainPairView(TokenObtainPairView):
    serializer_class = LibraryUserTokenObtainPairSerializer

class LibraryUserTokenRefreshView(TokenRefreshView):
    serializer_class = LibraryUserTokenRefreshSerializer

# Create your views here.
