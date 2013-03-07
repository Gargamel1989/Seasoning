from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from captcha.fields import ReCaptchaField
from django.contrib.auth.forms import AuthenticationForm


attrs_dict = {'class': 'required'}

class EmailUserCreationForm(forms.Form):
    """
    Form for registering a new user account.
    
    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.
    
    Enforces uniqueness of email adresses and adds a ReCaptcha field 
    and a required checkbox for agreeing to the site's Terms of Service. 
    
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
        existing = get_user_model().objects.filter(username__iexact=self.cleaned_data['username'])
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
                             error_messages = {'invalid': _("Please enter a valid email address"),
                                               'required': _("Please enter a valid email address")})
    
    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            user = get_user_model().objects.get(email=email)
            profiles = user.registrationprofile_set.all()
            
            if len(profiles) <= 0 or user.is_active:
                raise forms.ValidationError(_("The account corresponding to this email address has already been activated"))
            
            if profiles[0].activation_key_expired():
                raise forms.ValidationError(_("The account corresponding to this email address has expired due to prolonged inactivity"))
            
            return profiles[0]
        
        except get_user_model().DoesNotExist:
            raise forms.ValidationError(_("The given email address was not found"))
    

class CheckActiveAuthenticationForm(AuthenticationForm):
    
    def __init__(self, *args, **kwargs):
        super(CheckActiveAuthenticationForm, self).__init__(*args, **kwargs)
        self.error_messages['inactive'] = mark_safe(_("This account has not been activated yet, so you may not log in at \
            this time. If you haven't received an activation email for 15 minutes after registering, you can use \
            <a href=\"/activate/resend/\">this form</a> to resend an activation email."))
