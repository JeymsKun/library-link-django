# myDjangoAdmin/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from myDjangoAdmin.authentication import LibraryUserJWTAuthentication
from myDjangoAdmin.serializers import LibraryUserSerializer, BookSerializer
from .serializers import LibraryUserTokenObtainPairSerializer, MobileTokenObtainPairSerializer
from myserver.serializers import RecentlyViewedSerializer, BookingCartSerializer
from myDjangoAdmin.authentication import LibraryUserJWTAuthentication
from myserver.models import FavoriteBook, RecentlyViewed, BookingCart, BorrowedBook, ReservedBook
from rest_framework.generics import RetrieveAPIView
from .models import Book
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from myDjangoAdmin.models import UserSessionLog, LibraryUserOutstandingToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status, permissions
from rest_framework_simplejwt.settings import api_settings
from rest_framework import serializers
from myDjangoAdmin.models import LibraryUser, Genre
from django.db.models import Q
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.http import JsonResponse
from .serializers import GenreSerializer

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def borrow_book(request, user_id):
    if request.user.id != user_id:
        return Response({'detail': 'Unauthorized.'}, status=status.HTTP_403_FORBIDDEN)

    book_id = request.data.get('book_id')
    if not book_id:
        return Response({'detail': 'book_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    if BorrowedBook.objects.filter(user_id=user_id, book_id=book_id).exists():
        return Response({'detail': 'Book already borrowed.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        book = Book.objects.get(id=book_id)
        borrowed = BorrowedBook.objects.create(user_id=user_id, book=book)
        return Response({'detail': 'Book borrowed successfully.'}, status=status.HTTP_201_CREATED)
    except Book.DoesNotExist:
        return Response({'detail': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reserve_book(request, user_id):
    if request.user.id != user_id:
        return Response({'detail': 'Unauthorized.'}, status=status.HTTP_403_FORBIDDEN)

    book_id = request.data.get('book_id')
    if not book_id:
        return Response({'detail': 'book_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    if ReservedBook.objects.filter(user_id=user_id, book_id=book_id).exists():
        return Response({'detail': 'Book already reserved.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        book = Book.objects.get(id=book_id)
        reserved = ReservedBook.objects.create(user_id=user_id, book=book)
        return Response({'detail': 'Book reserved successfully.'}, status=status.HTTP_201_CREATED)
    except Book.DoesNotExist:
        return Response({'detail': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def favorite_books(request, user_id):
    favorites = FavoriteBook.objects.filter(user__id=user_id).select_related('book')
    books = [fav.book for fav in favorites]
    serializer = BookSerializer(books, many=True)
    return Response(serializer.data)

@api_view(["GET"])
def genre_list(request):
    genres = Genre.objects.all().order_by('name')
    return Response(GenreSerializer(genres, many=True).data)

@api_view(["GET"])
def books_by_genre(request):
    search = request.GET.get("search", "")
    user_id = request.GET.get("user_id")

    data = {}
    for genre in Genre.objects.all():
        books = Book.objects.filter(genres=genre)
        if search:
            books = books.filter(Q(title__icontains=search) | Q(author__icontains=search))

        books_data = BookSerializer(books, many=True, context={"request": request}).data

        if user_id:
            favorite_ids = FavoriteBook.objects.filter(user_id=user_id).values_list("book_id", flat=True)
            for book in books_data:
                book["is_favorite"] = book["id"] in favorite_ids

        data[genre.name] = books_data

    return Response(data)


def api_root(request):
    return JsonResponse({"message": "LibraryLink Expo API is running."})

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

    def post(self, request, user_id):
        if str(request.user.id) != str(user_id):
            return Response({"detail": "Not authorized"}, status=403)
        
        book_id = request.data.get('book_id')
        if not book_id:
            return Response({"detail": "book_id is required"}, status=400)
        
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"detail": "Book not found"}, status=404)
        
        recently_viewed, created = RecentlyViewed.objects.get_or_create(
            user_id=user_id,
            book=book,
            defaults={'viewed_at': timezone.now()}
        )
        
        if not created:
            recently_viewed.viewed_at = timezone.now()
            recently_viewed.save(update_fields=['viewed_at'])
        
        return Response({"detail": "Book view recorded"}, status=200)

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

    def post(self, request, user_id):
        if str(request.user.id) != str(user_id):
            return Response({"detail": "Not authorized"}, status=403)
        book_id = request.data.get('book_id')
        if not book_id:
            return Response({'error': 'book_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = LibraryUser.objects.get(id=user_id)
            book = Book.objects.get(id=book_id)
            favorite, created = FavoriteBook.objects.get_or_create(user=user, book=book)
            if created:
                return Response({'success': 'Book added to favorites'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'info': 'Book already in favorites'}, status=status.HTTP_200_OK)
        except LibraryUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, user_id):
        if str(request.user.id) != str(user_id):
            return Response({"detail": "Not authorized"}, status=403)
        book_id = request.data.get('book_id')
        if not book_id:
            return Response({'error': 'book_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = LibraryUser.objects.get(id=user_id)
            book = Book.objects.get(id=book_id)
            fav = FavoriteBook.objects.filter(user=user, book=book)
            deleted, _ = fav.delete()
            if deleted:
                return Response({'success': 'Book removed from favorites'}, status=status.HTTP_200_OK)
            else:
                return Response({'info': 'Book was not in favorites'}, status=status.HTTP_200_OK)
        except LibraryUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

class MobileTokenObtainPairView(TokenObtainPairView):
    serializer_class = MobileTokenObtainPairSerializer

class UserBookingCartAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        if request.user.id != user_id:
            return Response({'detail': 'Unauthorized.'}, status=status.HTTP_403_FORBIDDEN)
        cart_items = BookingCart.objects.filter(user_id=user_id)
        serializer = BookingCartSerializer(cart_items, many=True)
        return Response(serializer.data)

    def post(self, request, user_id):
        if request.user.id != user_id:
            return Response({'detail': 'Unauthorized.'}, status=status.HTTP_403_FORBIDDEN)
        book_id = request.data.get('book_id')
        if not book_id:
            return Response({'detail': 'book_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if BookingCart.objects.filter(user_id=user_id, book_id=book_id).exists():
            return Response({'detail': 'Book already in cart.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({'detail': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)
        cart_item = BookingCart.objects.create(user_id=user_id, book=book)
        serializer = BookingCartSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        if request.user.id != user_id:
            return Response({'detail': 'Unauthorized.'}, status=status.HTTP_403_FORBIDDEN)
        
        book_id = request.data.get('book_id')
        if not book_id:
            return Response({'detail': 'book_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cart_item = BookingCart.objects.get(user_id=user_id, book_id=book_id)
            cart_item.delete()
            return Response({'detail': 'Book removed from cart.'}, status=status.HTTP_204_NO_CONTENT)
        except BookingCart.DoesNotExist:
            return Response({'detail': 'Book not found in cart.'}, status=status.HTTP_404_NOT_FOUND)


# Create your views here.
