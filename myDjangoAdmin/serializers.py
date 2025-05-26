from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from myDjangoAdmin.models import LibraryUser, Book, Genre, LibraryUserOutstandingToken
from rest_framework import serializers

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']

class LibraryUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibraryUser
        fields = ['id', 'email', 'full_name', 'is_active']

class LibraryUserTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):

        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = LibraryUser.objects.get(email=email)
            if not user.check_password(password):
               raise serializers.ValidationError({"error": "Invalid password"})
        except LibraryUser.DoesNotExist:
            raise serializers.ValidationError({"error": "User not found"})

        if not user.is_active:
           raise serializers.ValidationError({"error": "User inactive"})
        
        token = super().get_token(user)
        refresh = str(token)
        access = str(token.access_token)

        LibraryUserOutstandingToken.objects.create(user=user, token=refresh)

        return {
            'refresh': refresh,
            'access': access,
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'is_active': user.is_active,
            }
        }
    
class MobileTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email' 

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        if not user.is_active:
            raise serializers.ValidationError("User inactive")

        data.update({
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'is_active': user.is_active,
            }
        })
        return data

    
class BookSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()
    extra_image_1 = serializers.SerializerMethodField()
    extra_image_2 = serializers.SerializerMethodField()
    extra_image_3 = serializers.SerializerMethodField()
    extra_image_4 = serializers.SerializerMethodField()
    extra_image_5 = serializers.SerializerMethodField()
    barcode_image = serializers.SerializerMethodField()
    genre = serializers.CharField(source='genres.name', default=None) 

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'genre', 'isbn', 'publisher', 'published_date',
            'copies', 'cover_image', 'extra_image_1', 'extra_image_2', 'extra_image_3',
            'extra_image_4', 'extra_image_5', 'barcode_code', 'barcode_image',
            'description', 'created_at', 'images',
        ]
    
    def get_images(self, obj):
        request = self.context.get('request')
        urls = []

        if obj.cover_image and hasattr(obj.cover_image, 'url'):
            if request:
                urls.append(request.build_absolute_uri(obj.cover_image.url))
            else:
                urls.append(obj.cover_image.url)

        for i in range(1, 6):
            extra_img = getattr(obj, f'extra_image_{i}')
            if extra_img and hasattr(extra_img, 'url'):
                if request:
                    urls.append(request.build_absolute_uri(extra_img.url))
                else:
                    urls.append(extra_img.url)

        return urls
    
    def get_cover_image(self, obj):
        request = self.context.get('request')
        if obj.cover_image and hasattr(obj.cover_image, 'url'):
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            else:
                return obj.cover_image.url
        return None

    def get_extra_image_1(self, obj):
        request = self.context.get('request')
        if obj.extra_image_1 and hasattr(obj.extra_image_1, 'url'):
            if request:
                return request.build_absolute_uri(obj.extra_image_1.url)
            else:
                return obj.extra_image_1.url        
        return None

    def get_extra_image_2(self, obj):
        request = self.context.get('request')
        if obj.extra_image_2 and hasattr(obj.extra_image_2, 'url'):
            if request:
                return request.build_absolute_uri(obj.extra_image_2.url)
            else:   
                return obj.extra_image_2.url
        return None

    def get_extra_image_3(self, obj):
        request = self.context.get('request')
        if obj.extra_image_3 and hasattr(obj.extra_image_3, 'url'):
            if request:
                return request.build_absolute_uri(obj.extra_image_3.url)
            else:
                return obj.extra_image_3.url
        return None

    def get_extra_image_4(self, obj):
        request = self.context.get('request')
        if obj.extra_image_4 and hasattr(obj.extra_image_4, 'url'):
            if request:
                return request.build_absolute_uri(obj.extra_image_4.url)
            else:
                return obj.extra_image_4.url
        return None

    def get_extra_image_5(self, obj):
        request = self.context.get('request')
        if obj.extra_image_5 and hasattr(obj.extra_image_5, 'url'):
            if request:
                return request.build_absolute_uri(obj.extra_image_5.url)
            else:
                return obj.extra_image_5.url
        return None

    def get_barcode_image(self, obj):
        request = self.context.get('request')
        if obj.barcode_image and hasattr(obj.barcode_image, 'url'):
            if request:
                return request.build_absolute_uri(obj.barcode_image.url)
            else:
                return obj.barcode_image.url
        return None

