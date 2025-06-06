# myserver/models.py
from django.db import models
from django.utils import timezone
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
    returned_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-borrowed_at']

    def __str__(self):
        return f"{self.user.email} borrowed {self.book.title}"
    
    @property
    def is_returned(self):
        return self.returned_at is not None

class ReservedBook(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE, related_name='reserved_books')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reserved_instances')
    reserved_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-reserved_at']

    def __str__(self):
        return f"{self.user.email} reserved {self.book.title}"
    
# Create your models here.
