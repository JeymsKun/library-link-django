# myserver/forms.py

from django import forms
from myDjangoAdmin.models import LibraryUser  

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
