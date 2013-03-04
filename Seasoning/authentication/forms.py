from django.contrib.auth.forms import UserCreationForm, AuthenticationForm,\
    PasswordResetForm, SetPasswordForm
from django import forms
from django.contrib.auth import authenticate, REDIRECT_FIELD_NAME
from django.contrib.auth.models import User
from captcha.fields import ReCaptchaField
from django.forms.fields import BooleanField
from django.utils.safestring import mark_safe
from django.conf import settings

required_string = "Dit veld is verplicht."

class EmailAuthenticationForm(AuthenticationForm):
    """
    Override the default AuthenticationForm to force email-as-username behavior.
    """
    email = forms.EmailField(label="E-mail", max_length=75, error_messages={'required': 'Dit veld is verplicht', 'invalid': 'Geef een geldig e-mail adres'})
    password = forms.CharField(label="Wachtwoord", widget=forms.PasswordInput, error_messages={'required': 'Dit veld is verplicht'})
    next = forms.CharField(label=REDIRECT_FIELD_NAME, widget=forms.HiddenInput, initial=settings.LOGIN_REDIRECT_URL)
    message_incorrect_password = "Gelieve een geldige e-mail en wachtwoord combinatie in te voeren."
    message_inactive = mark_safe('Dit account is nog niet geactiveerd. Volg de instructies in de activatie e-mail om het te activeren. Indien u na 15' + \
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
    
class EmailUserCreationForm(UserCreationForm):
    """
    Override error messages for language reasons
    """
    error_messages = {
        'duplicate_username': "De opgegeven gebruikersnaam is reeds in gebruik.",
        'password_mismatch': "De opgegeven wachtwoorden kwamen niet overeen.",
    }
    
    
    username = forms.RegexField(label="Gebruikersnaam", max_length=30,
                                regex=r'^[\w.@+-]+$',
                                help_text = "",
                                error_messages = {'invalid': "De gebruikersnaam mag enkel letters, nummers en @/./+/-/_ bevatten.",
                                                  'required': required_string})
   
    captcha = ReCaptchaField(attrs={'theme': 'clean',
                                    'tabindex': 5},
                             error_messages = {'required': required_string})
    
    terms = BooleanField(error_messages = {'required': "U moet de voorwaarden en het privacybeleid aanvaarden"})
   
    """
    Override the default UserCreationForm to force email-as-username behavior.
    """
    
    email = forms.EmailField(label="E-mail", max_length=75,
                             error_messages = {'invalid': "Gelieve een geldig e-mail adres op te geven.",
                                               'required': required_string})

    class Meta:
        model = User
        fields = ("username", "email",)

    def __init__(self, *args, **kwargs):
        super(EmailUserCreationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].label = "Wachtwoord"
        self.fields['password1'].error_messages['required'] = required_string
        self.fields['password2'].label = "Bevestig Wachtwoord"
        self.fields['password2'].error_messages['required'] = required_string
        self.fields['password2'].help_text = ""

    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            User.objects.get(email=email)
            raise forms.ValidationError("Het opgegeven e-mail adres is reeds in gebruik.")
        except User.DoesNotExist:
            return email
    
    def clean(self):
        cleaned_data = super(EmailUserCreationForm, self).clean()
        
#        if not cleaned_data.get("terms"):
#            raise forms.ValidationError("U moet de voorwaarden en het privacybeleid aanvaarden")
                
        return cleaned_data
    
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
        
class CustomPasswordResetForm(PasswordResetForm):
    
    error_messages = {
        'unknown': "Het opgegeven e-mail adres werd niet gevonden. "
                     "Hebt u zich reeds geregistreerd?",
        'unusable': "O-o, het wachtwoord van dit account kan niet veranderd worden.",
    }
     
    email = forms.EmailField(label="E-mail", max_length=75,
                             error_messages = {'invalid': "Gelieve een geldig e-mail adres op te geven.",
                                               'required': required_string})
    
class CustomSetPasswordForm(SetPasswordForm):
    
    error_messages = {
        'password_mismatch': "De opgegeven wachtwoorden kwamen niet overeen.",
    }
    
    new_password1 = forms.CharField(label="Nieuw Wachtwoord",
                                    widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Bevestig Wachtwoord",
                                    widget=forms.PasswordInput)