from django.conf.urls.defaults import patterns, url, include
from authentication.forms import EmailAuthenticationForm
from authentication.views import registration_complete, registration_closed,\
    activation_complete, resend_activation_email, register, activate
from authentication.backends import DefaultBackend

urlpatterns = patterns('',
                       
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'authentication/login.html',
                                                         'authentication_form': EmailAuthenticationForm}),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
    url(r'^register/$', register, {'backend': DefaultBackend}),
    url(r'^activate/resend/$', resend_activation_email),
    url(r'^activate/complete/$', activation_complete, 
        name='registration_activation_complete'),
    # Activation keys get matched by \w+ instead of the more specific
    # [a-fA-F0-9]{40} because a bad activation key should still get to the view;
    # that way it can return a sensible "invalid key" message instead of a
    # confusing 404.
    url(r'^activate/(?P<activation_key>\w+)/$',
                           activate,
                           {'backend': DefaultBackend},
                           name='registration_activate'),
    url(r'^register/complete/$', registration_complete,
        name='registration_complete'),
    url(r'^register/closed/$', registration_closed,
        name='registration_disallowed'),
    url(r'^profile/account/$', 'authentication.views.account_settings'),
    url(r'', include('registration.auth_urls')),
)
