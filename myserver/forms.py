# myserver/forms.py
from django import forms
from myDjangoAdmin.models import LibraryUser, Book, Genre
from django.forms.widgets import FileInput

class LibraryUserSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = LibraryUser  
        fields = ['full_name', 'id_number', 'email', 'password']

        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'id_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match")

class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class BookForm(forms.ModelForm):
    extra_image_1 = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        required=False
    )
    extra_image_2 = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        required=False
    )
    extra_image_3 = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        required=False
    )
    extra_image_4 = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        required=False
    )
    extra_image_5 = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        required=False
    )

    genres = forms.ModelChoiceField(
        queryset=Genre.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    class Meta:
        model = Book
        fields = [
            'title', 'author', 'genres', 'isbn', 'publisher', 'published_date',
            'copies', 'cover_image', 'barcode_code', 'barcode_image', 'description',
            'extra_image_1', 'extra_image_2', 'extra_image_3', 'extra_image_4', 'extra_image_5'
        ]
        widgets = {
            'cover_image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'barcode_code': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
        }