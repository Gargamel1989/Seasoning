from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.contrib.auth import authenticate, REDIRECT_FIELD_NAME
from django.contrib.auth.models import User
from captcha.fields import ReCaptchaField
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
    
attrs_dict = {'class': 'required'}

class EmailUserCreationForm(RegistrationFormUniqueEmail):
    """
    Form for registering a new user account.
    
    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.
    
    Subclasses should feel free to add any additional validation they
    need, but should avoid defining a ``save()`` method -- the actual
    saving of collected user data is delegated to the active
    registration backend.
    
    """
    username = forms.RegexField(regex=r'^[\w.@+-]+$',
                                max_length=30,
                                widget=forms.TextInput(attrs=attrs_dict),
                                label=_("Username"),
                                error_messages={'invalid': _("This value may contain only letters, numbers and @/./+/-/_ characters.")})
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=75)),
                             label=_("E-mail"))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_("Password (again)"))
    
    tos = forms.BooleanField(widget=forms.CheckboxInput(attrs=attrs_dict),
                             label=_(u'I have read and agree to the Terms of Service'),
                             error_messages={'required': _("You must agree to the terms to register")})
                             
    captcha = ReCaptchaField(attrs={'theme': 'clean',
                                    'tabindex': 5},
                             error_messages = {'required': _("You must enter the correct ReCaptcha characters")})
    
    def clean_username(self):
        """
        Validate that the username is alphanumeric and is not already
        in use.
        
        """
        existing = User.objects.filter(username__iexact=self.cleaned_data['username'])
        if existing.exists():
            raise forms.ValidationError(_("A user with that username already exists."))
        else:
            return self.cleaned_data['username']

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.
        
        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_("The two password fields didn't match."))
        return self.cleaned_data

    
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
