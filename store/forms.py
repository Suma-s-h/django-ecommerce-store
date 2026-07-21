from django import forms
from .models import Review


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'class': 'form-input', 'placeholder': 'Your name'}))
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': 'form-input', 'placeholder': 'Your email'}))
    subject = forms.CharField(max_length=150, widget=forms.TextInput(
        attrs={'class': 'form-input', 'placeholder': 'Subject'}))
    message = forms.CharField(widget=forms.Textarea(
        attrs={'class': 'form-input', 'placeholder': 'How can we help?', 'rows': 5}))


class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, i) for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'star-radio'}),
    )

    class Meta:
        model = Review
        fields = ['rating', 'title', 'body']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Summary of your review'}),
            'body': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Tell others about this product…', 'rows': 4}),
        }
