from django.conf.urls.defaults import patterns, url, include
from registration.views import activate
from authentication.forms import CustomPasswordResetForm, CustomSetPasswordForm

urlpatterns = patterns('',
                       
    url(r'^login/$', 'authentication.views.login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
    url(r'^register/$', 'authentication.views.register', {'backend': 'registration.backends.default.DefaultBackend'}),
    url(r'^activate/(?P<activation_key>\w+)/$',
                           activate,
                           {'backend': 'registration.backends.default.DefaultBackend'},
                           name='registration_activate'),
#    url(r'^password/reset/$', 'django.contrib.auth.views.password_reset', {'password_reset_form': CustomPasswordResetForm}),
#    url(r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
#        'django.contrib.auth.views.password_reset_confirm', {'set_password_form': CustomSetPasswordForm}),
    url(r'^activate/resend/$', 'authentication.views.resend_activation_email'),                       
    url(r'^', include('registration.urls')),
)