from django import forms
from .models import ContactMessage, NewsletterSubscriber, Order


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Votre nom complet'}),
            'email': forms.EmailInput(attrs={'placeholder': 'votre@email.com'}),
            'subject': forms.TextInput(attrs={'placeholder': 'Sujet du message'}),
            'message': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Votre message...'}),
        }


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Votre adresse email'}),
        }


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'email', 'phone', 'delivery_address', 'wilaya',
                  'notes', 'payment_method', 'transaction_screenshot', 'transaction_ref']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Nom et prénom'}),
            'email': forms.EmailInput(attrs={'placeholder': 'votre@email.com'}),
            'phone': forms.TextInput(attrs={'placeholder': '+253 77 XX XX XX'}),
            'delivery_address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Quartier, rue, repère...'}),
            'wilaya': forms.TextInput(attrs={'placeholder': 'Quartier / Zone'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Instructions particulières (optionnel)'}),
        }
