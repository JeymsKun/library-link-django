from django.db import models
from myDjangoAdmin.models import LibraryUser, Book

class FavoriteBook(models.Model):
    user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE, related_name='favorite_books')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')

    def __str__(self):
        return f"{self.user.email} - {self.book.title}"

# Create your models here.
