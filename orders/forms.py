from django import forms
from .models import Order


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'address', 'city', 'postal_code', 'country', 'notes']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email address'}),
            'address': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Street address'}),
            'city': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'City'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Postal / ZIP code'}),
            'country': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Country'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Order notes (optional)', 'rows': 3}),
        }
