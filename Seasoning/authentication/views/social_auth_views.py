import base64
from authentication.backends import GoogleAuthBackend, FacebookAuthBackend, SocialUserBackend, RegistrationBackend
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
from authentication.forms import SocialUserCheckForm

BACKENDS = {'google': GoogleAuthBackend,
            'fb': FacebookAuthBackend}

def base64_url_decode(inp):
    padding_factor = len(inp) % 4
    inp += "="*padding_factor
    return base64.b64decode(unicode(inp).translate(dict(zip(map(ord, u'-_'), u'+/'))))

def social_auth(request, backend):
    backend = BACKENDS[backend]
    backend = backend()
    
    code = request.GET.get('code', None)
    state = request.GET.get('state', None)
    next_page = state or request.REQUEST.get('next', None)
    
    redirect_uri = 'http://' + str(get_current_site(request)) + '/auth/' + backend.NAME + '/'
    if code is None:
        # User has just click the 'Login with ...' button to start a social authentication.
        # Redirect him to the social network, so we may get an authorization code.
        return redirect(backend.get_auth_code_url(redirect_uri=redirect_uri, 
                                                  next_page=next_page))
    else:
        # User has been redirected to the social network, and has come back with a code
        # We now need to exchange this code for an access token in our backend
        access_token = backend.get_access_token(code,
                                                redirect_uri=redirect_uri)
    
        if access_token:
            # We now have an access token
            user_info = backend.get_user_info(access_token)
            
            if user_info:
                # We received a valid access token, and were able to exchange it for the necessary
                # user information. 
                # Lets try to authenticate the user
                user = authenticate(**{backend.ID_FIELD: user_info['id']})
                
                if user:
                    # User was successfully authenticated, so log him in
                    auth_login(request, user)
                    return redirect(next_page or home)
                # A user with the this id whas not found in the database. Check if we can find a
                # Seasoning account with the social users email
                try:
                    user = User.objects.get(email=user_info['email'])
                    # A user with the given email has been found. Prompt the user to
                    # connect his social network account to his Seasoning account
                    messages.add_message(request, messages.INFO, _('The email corresponding to your ' + backend.name() + ' account is already in use on Seasoning. '
                                                                   'If this account belongs to you, please log in to connect it to your ' + backend.name() + ' account, '
                                                                   'otherwise, please contact an administrator.'))
                    # The user is probably not logged in at this point, so he will be asked to log
                    # in first before connecting his social network account to his Seasoning account.
                    return redirect('/auth/' + backend.NAME + '/connect/')
                except User.DoesNotExist:
                    # A user with the given email was not found. Prompt the user to register
                    # at Seasoning using his social network account
                    messages.add_message(request, messages.INFO, _('Your ' + backend.name() + ' account has not been connected to Seasoning yet. Please take a minute to register.'))
                    return redirect('/auth/' + backend.NAME + '/register/')
    
    # The code or access token was not correct or we were unable to connect to the social network. Please try again later
    messages.add_message(request, messages.INFO, _('An error occurred while checking your identity with ' + backend.name() + '. Please try again.'))
    return redirect('/login/')

@login_required
def social_connect(request, backend):
    backend = BACKENDS[backend]
    backend = backend()
    
    if request.method == 'POST':
        # The user has posted his intent to connect his social network id with
        # his Seasoning account
        if 'Cancel' in request.POST:
            # User didn't want to connect
            return redirect(home)
        
        access_token = request.POST.get('access-token', '')
        if access_token:
            # Check the access token and get the users Facebook info
            user_info = backend.get_user_info(access_token)
            if user_info:
                # Access token was valid and we have received the users' info
                # Check if this user is already connected to a Seasoning account
                user = authenticate(**{backend.ID_FIELD: user_info['id']})
                if user:
                    # User already has an account on Seasoning, so we can't connect it to another one
                    messages.add_message(request, messages.INFO, _('This ' + backend.name() + ' account is already connected to another account.'))
                else:
                    backend.connect_user(request.user, user_info['id'])
                    messages.add_message(request, messages.INFO, _('Your ' + backend.name() + ' account has been successfully connected to your Seasoning account!'))
                    return redirect(home)
            else:
                # Invalid access token or something else went wrong
                messages.add_message(request, messages.INFO, _('An error occurred while checking your identity with ' + backend.name() + '. Please try again.'))
    
    # User wants to connect his social account to his Seasoning account. Get the neccessary information
    # He either did something wrong while posting his response, or has not had the change to post it yet.
    code = request.GET.get('code', None)
    access_token = request.GET.get('accessToken', None)
    next_page = request.REQUEST.get('next', None)
    
    redirect_uri = 'http://' + str(get_current_site(request)) + '/auth/' + backend.NAME + '/connect/'
    if code is None:
        # Redirect User to the social network, so we may get an authorization code.
        return redirect(backend.get_auth_code_url(redirect_uri=redirect_uri, 
                                                  next_page=next_page))
    else:
        # User has been redirected to the social network, and has come back with a code
        # We now need to exchange this code for an access token in our backend
        access_token = backend.get_access_token(code,
                                                redirect_uri=redirect_uri)
    
        if access_token:
            # We now have an access token
            user_info = backend.get_user_info(access_token)
            
            if user_info:
                # We received a valid access token, and were able to exchange it for the necessary
                # user information.
                context = {'access_token': access_token}
                context.update(user_info)
                return render(request, 'authentication/social/' + backend.NAME + '_connect.html', context)
        
        messages.add_message(request, messages.INFO, _('An error occurred while checking your identity with ' + backend.name() + '. Please try again.'))
        return redirect('/account/settings/')
    
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
                user.facebook_id = social_user_info['id'] 
                user.save()
                messages.add_message(request, messages.INFO, _('Your social network account has been successfully connected to your Seasoning account!'))
            # If the user pressed cancel, return him to the home page
            return redirect(home)
    except PermissionDenied:
        pass
    # Show the connect account form
    return render(request, 'authentication/social/facebook_connect.html', {'app_id': settings.FACEBOOK_APP_ID})

@login_required
def facebook_disconnect(request):
    if request.user.password == '!':
        messages.add_message(request, messages.INFO, _('You can only disconnect social accounts if your password has been set.'))
    else:
        request.user.facebook_id = None
        request.user.save()
        messages.add_message(request, messages.INFO, _('Your Seasoning account has been disconnected from your Facebook account.'))
    return redirect('/account/settings/')

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
                # Check if a user with this Facebook id already exists
                User.objects.get(facebook_id=data['user_id'])
                messages.add_message(request, messages.INFO, _('A user has already registered with your Facebook account. If this is you, please log in, otherwise, contact an administrator'))
                return redirect('/login/')
            except User.DoesNotExist:
                pass
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

def google_authentication(request):
    error = request.GET.get('error', None)
    code = request.GET.get('code', None)
    state = request.GET.get('state', None)
    redirect_to = state or request.GET.get('next', '/')
    
    if error is None and code is None:
        # User is just starting to try to authenticate using google, redirect him to google
        # servers to fetch us an authorization code
        return redirect('https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=' + settings.GOOGLE_APP_ID + \
                    '&redirect_uri=http://' + str(get_current_site(request)) + '/auth/google/' + \
                    '&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email+https://www.googleapis.com/auth/userinfo.profile' + \
                    '&state=' + redirect_to)
    
    if code:
        # The user has been redirected by google and given a code
        backend = SocialUserBackend()
        access_token = backend.get_google_access_token(request, code, '/auth/google/')
        if access_token:
            # We received an access token from google for our code
            user_info = backend.check_google_access_token(access_token)
            if user_info:
                # Valid access token, we now trust the user because Google says so
                # Check if a user is available with the returned Google ID
                user = authenticate(**{'network_id': user_info['id'], 
                                       'network':SocialUserBackend.GOOGLE})
                if user:
                    # A user with the given Google ID has been found, log the user in
                    auth_login(request, user)
                    return redirect(redirect_to)
                # A user with the given Google ID was not found in the Seasoning DB, check
                # if a user with the given Google email is registered
                try:
                    user = User.objects.get(email=user_info['email'])
                    # A user with the given Google email has been found. Prompt the user to
                    # connect his social network account to his Seasoning account
                    messages.add_message(request, messages.INFO, _('The email corresponding to your social network account is already in use on Seasoning. '
                                                                   'If this account belongs to you, please log in to connect it to your Google account, '
                                                                   'otherwise, please contact an administrator.'))
                    # The user is probably not logged in at this point, so he will be asked to log
                    # in first before connecting his Google account to his Seasoning account.
                    return redirect('/auth/google/connect/?access_token=' + access_token)
                except User.DoesNotExist:
                    # A user with the given Facebook email was not found. Prompt the user to register
                    # at Seasoning using his Facebook account
                    messages.add_message(request, messages.INFO, _('Your Google account has not been connected to Seasoning yet. Please take a minute to register.'))
                    return redirect('/auth/google/register/')
        messages.add_message(request, messages.INFO, _('An error occurred while checking your identity with Google. Please try again.'))
        return redirect('/login/')

@login_required
def google_connect(request):
    # The currently logged in user will try to connect his Seasoning account to his
    # Google account.
    try:
        if request.method == 'POST':
            # User has just decided to connect his current google account to his seasoning account
            if not 'Cancel' in request.POST:
                # The user actually wants to connect his accounts
                backend = SocialUserBackend()
                access_token = request.POST.get('access-token', '')
                # Check the access token and get the users Facebook info
                social_user_info = backend.check_google_access_token(access_token)
                if not social_user_info:
                    # Access token was invalid or we were unable to connect to Facebook
                    messages.add_message(request, messages.INFO, _('An error occurred while checking your identity with Google. Please try again.'))
                    raise PermissionDenied
                user = request.user
                user.google_id = social_user_info['id'] 
                user.save()
                messages.add_message(request, messages.INFO, _('Your Google account has been successfully connected to your Seasoning account!'))
            # If the user pressed cancel, return him to the home page
            return redirect(home)
    except PermissionDenied:
        pass
    
    # User wants to connect his google account to his seasoning account
    error = request.GET.get('error', None)
    code = request.GET.get('code', None)
    access_token = request.GET.get('access_token', None)
    
    if access_token is None and error is None and code is None:
        # User wants to connect his google account to his seasoning account. First we need to get
        # an authorization code
        return redirect('https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=' + settings.GOOGLE_APP_ID + \
                        '&redirect_uri=http://' + str(get_current_site(request)) + '/auth/google/connect/' + \
                        '&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email+https://www.googleapis.com/auth/userinfo.profile')
    
    backend = SocialUserBackend()
    if access_token is None and code:
        # User was redirected from google, so fetch an access token for the received code
        access_token = backend.get_google_access_token(request, code, '/auth/google/connect/')
    
    if access_token:
        # We now have an acces code that was either fetched from google, or given to us in the url get params.
        # Doesn't matter, now we can show te connect form to the user
        user_info = backend.check_google_access_token(access_token)
        if user_info:
            return render(request, 'authentication/social/google_connect.html', {'app_id': settings.GOOGLE_APP_ID,
                                                                                 'access_token': access_token,
                                                                                 'id': user_info['id'],
                                                                                 'name': user_info['name'],
                                                                                 'email': user_info['email']})
    # If we're here, something above must have gone wrong...
    messages.add_message(request, messages.INFO, _('An error occurred while checking your identity with Google. Please try again.'))
    return redirect(home)

@login_required
def google_disconnect(request):
    if request.user.password == '!':
        messages.add_message(request, messages.INFO, _('You can only disconnect social accounts if your password has been set.'))
    else:
        request.user.google_id = None
        request.user.save()
        messages.add_message(request, messages.INFO, _('Your Seasoning account has been disconnected from your Google account.'))
    return redirect('/account/settings/')
    

def google_register(request, disallowed_url='registration_disallowed'):
    form = None
    backend = SocialUserBackend()
    if request.method == 'POST':
        access_token = request.POST.get('access_token', '')
        # User has registered using his google account
        form = SocialUserCheckForm(request.POST)
        if form.is_valid():
            user_info = backend.check_google_access_token(access_token)
            if user_info:
                try:
                    # Check if a user with this Google id already exists
                    User.objects.get(google_id=user_info['id'])
                    messages.add_message(request, messages.INFO, _('A user has already registered with your Google account. If this is you, please log in, otherwise, contact an administrator'))
                    return redirect('/login/')
                except User.DoesNotExist:
                    pass
                try:
                    # Check if a user with this Facebook email is already registered
                    User.objects.get(email=user_info['email'])
                    messages.add_message(request, messages.INFO, _('A user has already registered with that email. If this is your account, would you like to connect it to your Social Network account?'))
                    return redirect('/auth/fb/connect/')
                except User.DoesNotExist:
                    # A user with this Google email does not exist, so we will register a new one
                    pass
                backend = RegistrationBackend()
                # Check if registration is allowed
                if not backend.registration_allowed(request):
                    return redirect(disallowed_url)
                # Register the user
                try:
                    date_of_birth = date_of_birth=datetime.datetime.strptime(user_info['birthday'], '%m/%d/%Y').date()
                except ValueError:
                    date_of_birth = datetime.date.today()
                password = form.cleaned_data['password'] or None
                user = backend.social_register(request, social_id=user_info['id'], social_network=SocialUserBackend.GOOGLE,
                                               givenname=user_info['given_name'], surname=user_info['family_name'], email=user_info['email'], 
                                               date_of_birth=date_of_birth, password=password)
                # And log him in, because we don't need to validate his information
                user = authenticate(**{'network_id': user.facebook_id, 
                                       'network': SocialUserBackend.GOOGLE})
                auth_login(request, user)
                messages.add_message(request, messages.INFO, _('You have successfully registered your Google account on Seasoning. Have fun!'))            
                return redirect(home)
            # Invalid access token...
            access_token = None
    else:
        # User wants to register using his google account
        error = request.GET.get('error', None)
        code = request.GET.get('code', None)
        
        if error is None and code is None:
            # User wants to register using his google account. First we need to get
            # an authorization code
            return redirect('https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=' + settings.GOOGLE_APP_ID + \
                            '&redirect_uri=http://' + str(get_current_site(request)) + '/auth/google/register/' + \
                            '&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email+https://www.googleapis.com/auth/userinfo.profile')
            
        if code:
            # User was redirected from google, so fetch an access token for the received code
            access_token = backend.get_google_access_token(request, code, '/auth/google/register/')
            
    if access_token:
        # We now have an acces code that was either fetched from google, or given to us in the url get params.
        # Doesn't matter, now we can show te connect form to the user
        user_info = backend.check_google_access_token(access_token)
        if user_info:
            if not form:
                form = SocialUserCheckForm()
            return render(request, 'authentication/social/google_register.html', {'form': form,
                                                                                  'givenname': user_info['given_name'],
                                                                                  'surname': user_info['family_name'],
                                                                                  'email': user_info['email'],
                                                                                  'date_of_birth': user_info['birthday'],
                                                                                  'image': 'http://profiles.google.com/s2/photos/profile/' + user_info['id'] + '?sz=100',
                                                                                  'access_token': access_token})
                
    # If we're here, something above must have gone wrong...
    messages.add_message(request, messages.INFO, _('An error occurred while checking your identity with Google. Please try again.'))
    return redirect(home)

def twitter_authentication(request):
    redirect_to = request.GET.get('next', None)
    callback_url = 'http://' + str(get_current_site(request)) + '/auth/twitter/'
    if redirect_to is not None:
        callback_url += '?next=' + redirect_to
    
    return render(request, 'authentication/social/twitter.html', {'callback_url': callback_url})

def openid_authentication(request):
    return render(request, 'authentication/social/openid.html')