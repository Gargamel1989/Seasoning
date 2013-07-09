import base64
from authentication.backends import SocialUserBackend, RegistrationBackend
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import redirect, render
from authentication.models import User
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from general.views import home
from django.views.decorators.csrf import csrf_exempt
from django.utils import simplejson
import hmac
from django.conf import settings
import hashlib
import datetime
from django.contrib.sites.models import get_current_site
from django.http.response import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required

def base64_url_decode(inp):
    padding_factor = len(inp) % 4
    inp += "="*padding_factor
    return base64.b64decode(unicode(inp).translate(dict(zip(map(ord, u'-_'), u'+/'))))


def facebook_authentication(request):
    code = request.GET.get('code', None)
    access_token = request.GET.get('accessToken', None)
    redirect_to = request.REQUEST.get('next', home)
    
    if code is None and access_token is None:
        # The user wants to log in using his Facebook account, but no
        # contact with facebook has been made yet
        return render(request, 'authentication/social/facebook.html', {'app_id': settings.FACEBOOK_APP_ID,
                                                                       'site': get_current_site(request),
                                                                       'next': redirect_to})
    
    backend = SocialUserBackend()
    if code is not None:
        # The user has just logged in to his Facebook account, and we have received
        # a precious Facebook code. We need to get the corresponding access token
        # from Facebook
        access_token = backend.get_facebook_access_token(request, code)
    if access_token is not None:
        # The user is logged in to Facebook, and has been given an access
        # token to log in to Seasoning
        # Validate the access token and fetch the users Facebook info
        user_info = backend.check_facebook_access_token(access_token)
        if user_info:
            # Valid access token, we now trust the user because Facebook says so
            # Check if a user is available with the return Facebook ID
            user = authenticate(**{'network_id': user_info['id'], 
                                   'network':SocialUserBackend.FACEBOOK})
            if user:
                # A user with the given Faceboook ID has been found, log the user in
                auth_login(request, user)
                return redirect(redirect_to)
            # A user with the given Facebook ID was not found in the Seasoning DB, check
            # if a user with the given Facebook email is registered
            try:
                user = User.objects.get(email=user_info['email'])
                # A user with the given Facebook email has been found. Prompt the user to
                # connect his social network account to his Seasoning account
                messages.add_message(request, messages.INFO, _('The email corresponding to your social network account is already in use on Seasoning. '
                                                               'If this account belongs to you, please log in to connect it to your Facebook account, '
                                                               'otherwise, please contact an administrator.'))
                # The user is probably not logged in at this point, so he will be asked to log
                # in first before connecting his Facebook account to his Seasoning account.
                return redirect('/auth/fb/connect/')
            except User.DoesNotExist:
                # A user with the given Facebook email was not found. Prompt the user to register
                # at Seasoning using his Facebook account
                messages.add_message(request, messages.INFO, _('Your social network account has not been connected to Seasoning yet. Please take a minute to register.'))
                return redirect('/auth/fb/register/')
    # The code or access token was not correct or we were unable to connect to Facebook. Please try again later
    messages.add_message(request, messages.INFO, _('An error occurred while checking your identity with Facebook. Please try again.'))
    return redirect('/login/')
    

@login_required
def facebook_connect(request):
    # The currently logged in user will try to connect his Seasoning account to his
    # Facebook account.
    try:
        if request.method == 'POST':
            if not 'Cancel' in request.POST:
                # The user actually wants to connect his accounts
                backend = SocialUserBackend()
                access_token = request.POST.get('access-token', '')
                # Check the access token and get the users Facebook info
                social_user_info = backend.check_facebook_access_token(access_token)
                if not social_user_info:
                    # Access token was invalid or we were unable to connect to Facebook
                    messages.add_message(request, messages.INFO, _('An error occurred while checking your identity with Facebook. Please try again.'))
                    raise PermissionDenied
                user = request.user
                if not user.email == social_user_info['email']:
                    messages.add_message(request, messages.INFO, _('The email of your Seasoning account did not match that of your Facebook account.'))
                    raise PermissionDenied
                user.facebook_id = social_user_info['id'] 
                user.save()
                messages.add_message(request, messages.INFO, _('Your social network account has successfully connected to your Seasoning account!'))
            # If the user pressed cancel, return him to the home page
            return redirect(home)
    except PermissionDenied:
        pass
    # Show the connect account form
    return render(request, 'authentication/social/facebook_connect.html')

@csrf_exempt
def facebook_registration(request, disallowed_url='registration_disallowed'):
    if request.method == 'POST':
        # The user has posted a registration request through facebook
        signed_request = request.POST.get('signed_request', None)
        if signed_request:
            # Decode the signed request
            encoded_sig, payload = signed_request.split('.', 1)
            sig = base64_url_decode(str(encoded_sig))
            data = simplejson.loads(base64_url_decode(str(payload)))
            if data.get('algorithm').upper() != 'HMAC-SHA256':
                # We can't decode this kind of request
                messages.add_message(request, messages.INFO, _('Something went wrong. Please try again or contact the administrator.'))
                return redirect('/auth/fb/register/')
            # Get the signature we would except from this Facebook data and our secret
            expected_sig = hmac.new(settings.FACEBOOK_SECRET, msg=payload, digestmod=hashlib.sha256).digest()
            
            # Check if the signature in the request corresponds with our own generated signature
            if sig != expected_sig:
                # Someone tampered with the request
                raise PermissionDenied
            # This is now trusted data, extract the users info from the data
            user_data = data['registration']
            try:
                # Check if a user with this Facebook email is already registered
                User.objects.get(email=user_data['email'])
                messages.add_message(request, messages.INFO, _('A user has already registered with that email. If this is your account, would you like to connect it to your Social Network account?'))
                return redirect('/auth/fb/connect/')
            except User.DoesNotExist:
                # A user with this Facebook email does not exist, so we will register a new one
                pass
            backend = RegistrationBackend()
            # Check if registration is allowed
            if not backend.registration_allowed(request):
                return redirect(disallowed_url)
            # Register the user
            user = backend.social_register(request, social_id=data['user_id'], social_network=SocialUserBackend.FACEBOOK,
                                           givenname=user_data['first_name'], surname=user_data['last_name'], email=user_data['email'], 
                                           date_of_birth=datetime.datetime.strptime(user_data['birthday'], '%m/%d/%Y').date(), password=user_data['password'])
            # And log him in, because we don't need to validate his information
            user = authenticate(**{'network_id': user.facebook_id, 
                                   'network': SocialUserBackend.FACEBOOK})
            auth_login(request, user)
            messages.add_message(request, messages.INFO, _('You have successfully registered your Facebook account on Seasoning. Have fun!'))            
            return redirect(home)            
    return render(request, 'authentication/social/facebook_register.html', {'app_id': settings.FACEBOOK_APP_ID,
                                                                            'site': get_current_site(request)})

def facebook_channel_file(request):
    """
    This provides a cached channel file used by facebook
    
    """
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