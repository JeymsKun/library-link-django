# myserver/serializers.py
from rest_framework import serializers
from .models import RecentlyViewed, BookingCart
from myDjangoAdmin.serializers import BookSerializer

class RecentlyViewedSerializer(serializers.ModelSerializer):
    book = BookSerializer()

    class Meta:
        model = RecentlyViewed
        fields = ['book', 'viewed_at']

class BookingCartSerializer(serializers.ModelSerializer):
    book = serializers.SerializerMethodField()

    class Meta:
        model = BookingCart
        fields = ['book', 'added_at']

    def get_book(self, obj):
        return BookSerializer(obj.book, context=self.context).data