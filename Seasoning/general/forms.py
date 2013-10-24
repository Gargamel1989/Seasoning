from django import forms

class ContactForm(forms.Form):
    
    subject = forms.CharField()
    your_email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)
        