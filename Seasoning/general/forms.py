from django import forms
from captcha.fields import ReCaptchaField
from django.utils.translation import ugettext_lazy as _

class ContactForm(forms.Form):
    
    subject = forms.CharField()
    your_email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)
                             
    captcha = ReCaptchaField(attrs={'theme': 'red'},
                             error_messages = {'required': _("You must enter the correct ReCaptcha characters")})
    
    def __init__(self, *args, **kwargs):
        logged_in = kwargs.pop('logged_in', False)
        super(ContactForm, self).__init__(*args, **kwargs)
        if logged_in:
            del self.fields['your_email']
            del self.fields['captcha']