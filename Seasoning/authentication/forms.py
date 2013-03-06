from django.contrib.auth.forms import AuthenticationForm,PasswordResetForm, SetPasswordForm
from django import forms
from django.contrib.auth import authenticate, REDIRECT_FIELD_NAME
from django.contrib.auth.models import User
from captcha.fields import ReCaptchaField
from django.forms.fields import BooleanField
from django.utils.safestring import mark_safe
from django.conf import settings
from registration.forms import RegistrationFormUniqueEmail
from django.utils.translation import ugettext_lazy as _

required_string = "Dit veld is verplicht."

class EmailAuthenticationForm(AuthenticationForm):
    """
    Override the default AuthenticationForm to force email-as-username behavior.
    """
    email = forms.EmailField(label="E-mail", max_length=75, error_messages={'required': 'Dit veld is verplicht', 'invalid': 'Geef een geldig e-mail adres'})
    password = forms.CharField(label="Wachtwoord", widget=forms.PasswordInput, error_messages={'required': 'Dit veld is verplicht'})
    next = forms.CharField(label=REDIRECT_FIELD_NAME, widget=forms.HiddenInput, initial=settings.LOGIN_REDIRECT_URL)
    message_incorrect_password = "Gelieve een geldige e-mail en wachtwoord combinatie in te voeren."
    message_inactive = mark_safe('Deze account is nog niet geactiveerd. Volg de instructies in de activatie e-mail om het te activeren. Indien u na 15' + \
        ' minuten nog steeds geen activatiemail hebt gekregen, gebruik dan <a href="/activate/resend/">dit formulier</a> om een nieuwe te verzenden.')

    def __init__(self, request=None, *args, **kwargs):
        super(EmailAuthenticationForm, self).__init__(request, *args, **kwargs)
        del self.fields['username']
        self.fields.keyOrder = ['email', 'password', 'next']
        if request and request.method == 'GET':
            if REDIRECT_FIELD_NAME in request.GET:
                self.fields['next'].initial = request.GET[REDIRECT_FIELD_NAME]
        elif not request or not request.method == 'GET' or not REDIRECT_FIELD_NAME in request.GET:
            del self.fields['next']

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(email=email, password=password)
            if (self.user_cache is None):
                raise forms.ValidationError(self.message_incorrect_password)
            if not self.user_cache.is_active:
                raise forms.ValidationError(self.message_inactive)
        self.check_for_test_cookie()
        return self.cleaned_data
    
class EmailUserCreationForm(RegistrationFormUniqueEmail):
    """
    Subclass of ``RegistrationFormUniqueEmail`` which adds a required checkbox
    for agreeing to a site's Terms of Service and a recaptcha.
    
    """
    tos = forms.BooleanField(widget=forms.CheckboxInput(attrs=attrs_dict),
                             label=_(u'I have read and agree to the Terms of Service'),
                             error_messages={'required': _("You must agree to the terms to register")})
                             
    captcha = ReCaptchaField(attrs={'theme': 'clean',
                                    'tabindex': 5},
                             error_messages = {'required': _("You must enter the correct ReCaptcha characters")})

    
class ResendActivationEmailForm(forms.Form):
    
    email = forms.EmailField(label="E-mail", max_length=75,
                             error_messages = {'invalid': "Gelieve een geldig e-mail adres op te geven.",
                                               'required': required_string})
    
    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            user = User.objects.get(email=email)
            profiles = user.registrationprofile_set.all()
            
            if len(profiles) <= 0 or user.is_active:
                raise forms.ValidationError("Het account horende bij het opgegeven e-mail adres is reeds geactiveerd.")
            
            if profiles[0].activation_key_expired():
                raise forms.ValidationError("Het account horende bij het opgegeven e-mail adres is vervallen ten gevolge van langdurige inactiviteit.")
            
            return profiles[0]
        
        except User.DoesNotExist:
            raise forms.ValidationError("Het opgegeven e-mail adres werd niet gevonden. (" + self.cleaned_data["email"] + ").")
