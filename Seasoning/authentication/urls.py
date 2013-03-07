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
    url(r'^password_reset/$', 'django.contrib.auth.views.password_reset', 
        {'template_name'='authentication/password_reset_form.html',
         'email_template_name'='authentication/password_reset_email.html',
         'subject_template_name'='authentication/password_reset_subject.txt'},
        name='password_reset'),
    url(r'^password_reset/done/$', 'django.contrib.auth.views.password_reset_done', 
        {'template_name'='authentication/password_reset_done.html'},
        name='password_reset_done'),
    url(r'^password_reset/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        'django.contrib.auth.views.password_reset_confirm',
        {'template_name'='authentication/password_reset_confirm.html'},
        name='password_reset_confirm'),
    url(r'^password_reset/complete/$', 'django.contrib.auth.views.password_reset_complete', 
        {'template_name'='authentication/password_reset_complete.html'},
        name='password_reset_complete'),
    
    # Profile urls
    url(r'^profile/account/$', 'authentication.views.account_settings'),
    url(r'^password_change/$', 'django.contrib.auth.views.password_change', 
        {'template_name'='authentication/password_change_form.html'},
        name='password_change'),
    url(r'^password_change/done/$', 'django.contrib.auth.views.password_change_done', 
        {'template_name'='authentication/password_change_done.html'},
        name='password_change_done'),
)
