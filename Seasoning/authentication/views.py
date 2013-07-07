"""
Copyright 2012, 2013 Driesen Joep

This file is part of Seasoning.

Seasoning is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Seasoning is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Seasoning.  If not, see <http://www.gnu.org/licenses/>.
    
"""
from django.template.response import TemplateResponse
from django.contrib.sites.models import RequestSite, get_current_site
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, render_to_response
from django.template.context import RequestContext
from authentication.forms import ResendActivationEmailForm, AccountSettingsForm,\
    DeleteAccountForm, CheckActiveAuthenticationForm
from django.contrib.auth import get_user_model, logout, authenticate, login
from django.utils.translation import ugettext_lazy as _
from authentication.models import NewEmail, User
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import Http404
from general.views import home
from django.contrib import messages
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.forms import PasswordChangeForm
import datetime
from django.http.response import HttpResponse
import urllib2
from django.utils import simplejson
from urllib2 import HTTPError
from authentication.backends import SocialUserBackend, RegistrationBackend
from django.contrib.auth.views import login as django_login
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from encodings.base64_codec import base64_decode
import base64
import hmac
import hashlib


def register(request, backend, success_url=None, form_class=None,
             disallowed_url='registration_disallowed',
             template_name='authentication/registration_form.html',
             extra_context=None):
    """
    Allow a new user to register an account.

    The actual registration of the account will be delegated to the
    backend specified by the ``backend`` keyword argument (see below);
    it will be used as follows:

    1. The backend's ``registration_allowed()`` method will be called,
       passing the ``HttpRequest``, to determine whether registration
       of an account is to be allowed; if not, a redirect is issued to
       the view corresponding to the named URL pattern
       ``registration_disallowed``. To override this, see the list of
       optional arguments for this view (below).

    2. The form to use for account registration will be obtained by
       calling the backend's ``get_form_class()`` method, passing the
       ``HttpRequest``. To override this, see the list of optional
       arguments for this view (below).

    3. If valid, the form's ``cleaned_data`` will be passed (as
       keyword arguments, and along with the ``HttpRequest``) to the
       backend's ``register()`` method, which should return the new
       ``User`` object.

    4. Upon successful registration, the backend's
       ``post_registration_redirect()`` method will be called, passing
       the ``HttpRequest`` and the new ``User``, to determine the URL
       to redirect the user to. To override this, see the list of
       optional arguments for this view (below).
    
    **Required arguments**
    
    None.
    
    **Optional arguments**

    ``backend``
        The backend class to use.

    ``disallowed_url``
        URL to redirect to if registration is not permitted for the
        current ``HttpRequest``. Must be a value which can legally be
        passed to ``django.shortcuts.redirect``. If not supplied, this
        will be whatever URL corresponds to the named URL pattern
        ``registration_disallowed``.
    
    ``form_class``
        The form class to use for registration. If not supplied, this
        will be retrieved from the registration backend.
    
    ``extra_context``
        A dictionary of variables to add to the template context. Any
        callable object in this dictionary will be called to produce
        the end result which appears in the context.

    ``success_url``
        URL to redirect to after successful registration. Must be a
        value which can legally be passed to
        ``django.shortcuts.redirect``. If not supplied, this will be
        retrieved from the registration backend.
    
    ``template_name``
        A custom template to use. If not supplied, this will default
        to ``authentication/registration_form.html``.
    
    **Context:**
    
    ``form``
        The registration form.
    
    Any extra variables supplied in the ``extra_context`` argument
    (see above).
    
    **Template:**
    
    authentication/registration_form.html or ``template_name`` keyword
    argument.
    
    """
    backend = backend()
    if not backend.registration_allowed(request):
        return redirect(disallowed_url)
    if form_class is None:
        form_class = backend.get_form_class(request)
    
    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_user = backend.register(request, **form.cleaned_data)
            if success_url is None:
                to, args, kwargs = backend.post_registration_redirect(request, new_user)
                return redirect(to, *args, **kwargs)
            else:
                return redirect(success_url)
    else:
        form = form_class()
        
    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value
    
    return render_to_response(template_name,
                              {'form': form},
                              context_instance=context)

def registration_closed(request):
    return render(request, 'authentication/registration_closed.html')
    
def registration_complete(request):
    return render(request, 'authentication/registration_complete.html')
    

def resend_activation_email(request):
    """
    Allow a registered, non-activated user to resend an activation email.
    
    The user will be required to provide the non-activated email address. After
    checking if this email address indeed corresponds to a non-activated account,
    an email will be sent to it. 
    
    """
    if request.method == "POST":
        
        form = ResendActivationEmailForm(data=request.POST)
        
        if form.is_valid():
            site = RequestSite(request)
            
            # Send an activation email to the registration profile corresponding to the
            # given email
            form.cleaned_data['email'].send_activation_email(site)
            
            messages.add_message(request, messages.INFO, _('A new activation email has been sent to %s. This email should '
                                                           'arrive within 15 minutes. Please be sure to check your Spam/Junk '
                                                           'folder.'))
            return redirect(home)
        
    else:
        form = ResendActivationEmailForm()
        
    return render(request, 'authentication/resend_activation_email.html', {'form': form})


def activate(request, backend, **kwargs):
    """
    Activate a user's account.

    The actual activation of the account will be delegated to the
    backend specified by the ``backend`` keyword argument (see below);
    the backend's ``activate()`` method will be called, passing any
    keyword arguments captured from the URL, and will be assumed to
    return a ``User`` if activation was successful, or a value which
    evaluates to ``False`` in boolean context if not.

    Upon successful activation, the user will be redirected to the home
    page and displayed a message that the activation was succesfull.

    **Arguments**

    ``backend``
        The backend class to use. Required.

    ``**kwargs``
        Any keyword arguments captured from the URL, such as an
        activation key, which will be passed to the backend's
        ``activate()`` method.
    
    """
    backend = backend()
    account = backend.activate(request, **kwargs)

    if account:
        messages.add_message(request, messages.INFO, _('Your account has been successfully activated. Have fun!'))            
        return redirect(home)
    raise Http404

@login_required
def account_settings(request):
    """
    Allow a user to change his account settings
    
    If the user has changed his email address, an activation email will be sent to this new
    address. The new address will not be activated until the link in this email has been
    clicked.
    
    If the user has an alternate email that should be activated, this will also be displayed
    on this page.
    
    """
    context = {}
    if request.method == "POST":
        user = get_user_model().objects.get(id=request.user.id)
        form = AccountSettingsForm(request.POST, request.FILES, instance=user)
        
        if form.is_valid():
            if form.new_email:
                # Send an activation email to the new email
                NewEmail.objects.create_inactive_email(user, form.new_email, RequestSite(request))
                messages.add_message(request, messages.INFO, _('An email has been sent to the new email address provided by you. Please follow the instructions '
                                                               'in this email to complete the changing of your email address.'))
            # New email address has been replaced by old email address in the form, so it will not be saved until activated
            form.save()
    else:
        form = AccountSettingsForm(instance=request.user)
    
    try:
        new_email = NewEmail.objects.get(user=request.user)
        context['new_email'] = new_email.email
    except ObjectDoesNotExist:
        pass
    
    context['form'] = form
    return render(request, 'authentication/account_settings.html', context)

@login_required
def change_email(request, activation_key):
    """
    This checks if the given activation key belongs to the current users new,
    inactive email address. If so, this new email address is activated, and
    the users old email address is deleted.
    
    """
    activated = NewEmail.objects.activate_email(request.user, activation_key)
    if activated:
        messages.add_message(request, messages.INFO, _('Your email address has been successfully changed.'))
        return redirect(account_settings)
    raise Http404

@sensitive_post_parameters()
@login_required
def change_password(request,
                    template_name='authentication/password_change_form.html',
                    password_change_form=PasswordChangeForm,
                    current_app=None, extra_context=None):
    """
    Provides a form where the users password can be changed.
    
    """
    if request.method == "POST":
        form = password_change_form(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.INFO, _('Your password has been successfully changed.'))
            return redirect(account_settings)
    
    form = password_change_form(user=request.user)
    context = {
        'form': form,
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)

@login_required
def account_delete(request):
    """
    Provides a method for deleting the users account
    
    """
    # TODO: test
    if request.method == 'POST':
        form = DeleteAccountForm(request.POST)
        if form.is_valid():
            user = User.objects.get(pk=request.user.id)
            logout(request)
            user.delete()
            return redirect('/')
    else:
        form = DeleteAccountForm()
    return render(request, 'authentication/account_delete.html', {'form': form})

def login(request):
    redirect_to = request.REQUEST.get('next', None)
    
    if redirect_to:
        next_string = '&next=' + redirect_to
    else:
        next_string = ''
    return django_login(request, template_name='authentication/login.html', 
                        authentication_form=CheckActiveAuthenticationForm,
                        extra_context={'next_string': next_string})

def base64_url_decode(inp):
    padding_factor = len(inp) % 4
    inp += "="*padding_factor
    return base64.b64decode(unicode(inp).translate(dict(zip(map(ord, u'-_'), u'+/'))))

def facebook_authentication(request):
    code = request.GET.get('code', None)
    access_token = request.GET.get('accessToken', None)
    redirect_to = request.REQUEST.get('next', '')
    
    backend = SocialUserBackend()
    if not access_token and code:
        access_token = backend.get_facebook_access_token(request, code)
    if access_token:
        user_info = backend.check_facebook_access_token(access_token)
        if user_info:
            # The id can be trusted: try to log the user in
            user = authenticate(**{'network_id': user_info['id'], 
                    
                                   'network':SocialUserBackend.FACEBOOK})
            if user:
                login(request, user)
                return redirect(redirect_to)
            try:
                # Check if a user with this email has already been registered
                user = User.objects.get(email=user_info['email'])
                return redirect('/auth/fb/connect/')
            except User.DoesNotExist:
                pass
            messages.add_message(request, messages.INFO, _('Your social network account has not been connected to Seasoning yet. Please take a minute to register.'))
            return redirect('/auth/fb/register/')
    messages.add_message(request, messages.INFO, _('An error occurred while checking your identity with Facebook. Please try again.'))
    return redirect('/login/')

def facebook_connect(request):
    if request.method == 'POST':
        try:
            access_token = request.POST['access_token']
        except KeyError:
            raise PermissionDenied    
        backend = SocialUserBackend()
        user_info = backend.check_facebook_access_token(access_token)
        try:
            user = User.objects.get(email=user_info['email'])
            user.facebook_id = user_info['uid']
            user.save()
            login(request, user)
            return redirect(home)
        except User.DoesNotExist:
            messages.add_message(request, messages.INFO, _('Your social network account has not been connected to Seasoning yet. Please take a minute to register.'))
            return redirect('/auth/fb/register/')
    return render(request, 'authentication/social/facebook_connect.html')

@csrf_exempt
def facebook_registration(request, disallowed_url='registration_disallowed'):
    if request.method == 'POST':
        signed_request = request.POST.get('signed_request', None)
        if signed_request:
            encoded_sig, payload = signed_request.split('.', 1)
            sig = base64_url_decode(str(encoded_sig))
            data = simplejson.loads(base64_url_decode(str(payload)))
            if data.get('algorithm').upper() != 'HMAC-SHA256':
                messages.add_message(request, messages.INFO, _('Something went wrong. Please try again or contact the administrator.'))
                return redirect('/auth/fb/register/')
            else:
                expected_sig = hmac.new(settings.FACEBOOK_SECRET, msg=payload, digestmod=hashlib.sha256).digest()
                 
            if sig != expected_sig:
                raise PermissionDenied
                # TODO: csrf validation, test
            user_data = data['registration']
            print user_data
            try:
                User.objects.get(email=user_data['email'])
                messages.add_message(request, messages.INFO, _('A user has already registered with that email. If this is your account, would you like to connect it to your Social Network account?'))
                return redirect('/auth/fb/connect/')
            except User.DoesNotExist:
                pass
            backend = RegistrationBackend()
            if not backend.registration_allowed(request):
                return redirect(disallowed_url)
            user = backend.social_register(request, user_data['givenname'], user_data['surname'], user_data['email'], user_data['gender'], datetime.datetime.strptime('%M/%D/%Y', user_data['birthday']).date, data['user_id'], SocialUserBackend.FACEBOOK)
            user = authenticate(**{'network_id': user.facebook_id, 
                                   'network': SocialUserBackend.FACEBOOK})
            login(request, user)
            messages.add_message(request, messages.INFO, _('You have successfully registered your Facebook account on Seasoning. Have fun!'))            
            return redirect(home)            
    return render(request, 'authentication/social/facebook_register.html', {'site': get_current_site(request).domain})

def facebook_channel_file(request):
    response = HttpResponse('<script src="//connect.facebook.net/en_US/all.js"></script>')
    response['Pragma'] = 'public'
    response['Cache-Control'] = 'max-age=' + str(60*60*24*365)
    response['Expires'] = (datetime.datetime.now() + datetime.timedelta(days=365)).strftime('%a, %d %b %Y %H:%M:%S GMT')
    return response

def twitter_authentication(request):
    return render(request, 'authentication/social/twitter.html')

def google_authentication(request):
    return render(request, 'authentication/social/google.html')

def openid_authentication(request):
    return render(request, 'authentication/social/openid.html')