from django.conf.urls.defaults import patterns, url, include
from authentication.forms import EmailAuthenticationForm
from authentication.views import registration_complete, registration_closed,\
    activation_complete, resend_activation_email, register, activate
from authentication.backends import DefaultBackend

urlpatterns = patterns('',
    
    # Registration urls                   
    url(r'^register/$', register, {'backend': DefaultBackend},
        name='registration'),
    url(r'^register/closed/$', registration_closed,
        name='registration_disallowed'),
    url(r'^register/complete/$', registration_complete,
        name='registration_complete'),
    
    # Activation urls
    url(r'^activate/resend/$', resend_activation_email,
        name='resend_activation_email'),
    url(r'^activate/complete/$', activation_complete, 
        name='activation_complete'),
    url(r'^activate/(?P<activation_key>\w+)/$', activate, {'backend': DefaultBackend},
        name='registration_activate'),
    
    # Login urls
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'authentication/login.html',
                                                         'authentication_form': EmailAuthenticationForm}),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
    
    # Profile urls
    url(r'^profile/account/$', 'authentication.views.account_settings'),
    
    # Misc urls
    url(r'', include('django.contrib.auth.urls')),
)
