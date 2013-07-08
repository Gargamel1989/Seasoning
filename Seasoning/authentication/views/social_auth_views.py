import base64
from authentication.backends import SocialUserBackend, RegistrationBackend
from django.contrib.auth import authenticate as django_auth, login as django_login
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
from authentication.forms import SocialNetworkConnectionForm

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
            user = django_auth(**{'network_id': user_info['id'], 
                                          'network':SocialUserBackend.FACEBOOK})
            if user:
                django_login(request, user)
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
        form = SocialNetworkConnectionForm(request.POST)   
        if form.is_valid():
            user = form.user()
            user.facebook_id = form.social_id()
            user.save()
            django_login(request, user)
            return redirect(home)
    form = SocialNetworkConnectionForm()
    return render(request, 'authentication/social/facebook_connect.html', {'form': form})

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
            user = django_auth(**{'network_id': user.facebook_id, 
                                  'network': SocialUserBackend.FACEBOOK})
            django_login(request, user)
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