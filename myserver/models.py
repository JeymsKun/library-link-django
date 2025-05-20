# myserver/models.py
from django.db import models
from django.utils import timezone
from datetime import timedelta
from myDjangoAdmin.models import LibraryUser, Book

class FavoriteBook(models.Model):
    user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE, related_name='favorite_books')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')

    def __str__(self):
        return f"{self.user.email} - {self.book.title}"
    
class RecentlyViewed(models.Model):
    user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE, related_name='recently_viewed_books')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.user.email} viewed {self.book.title}"
    
class BookingCart(models.Model):
    user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE, related_name='booking_cart')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='in_carts')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.email} → {self.book.title}"
    
class BorrowedBook(models.Model):
    user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE, related_name='borrowed_books')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrowed_instances')
    borrowed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-borrowed_at']

    def __str__(self):
        return f"{self.user.email} borrowed {self.book.title}"

class ReservedBook(models.Model):
    user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE, related_name='reserved_books')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reserved_instances')
    reserved_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-reserved_at']

    def __str__(self):
        return f"{self.user.email} reserved {self.book.title}"
    
# Create your models here.
