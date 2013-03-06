from django.conf.urls.defaults import patterns, url, include
from authentication.forms import EmailAuthenticationForm

urlpatterns = patterns('',
                       
    url(r'^login/$', 'django.contrib.auth.views.login', {'authentication_form': EmailAuthenticationForm}),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
    url(r'^register/$', 'authentication.views.register', {'backend': 'registration.backends.default.DefaultBackend'}),
    url(r'^activate/resend/$', 'authentication.views.resend_activation_email'),
    url(r'^', include('registration.urls')),
    url(r'^profile/account/$', 'authentication.views.account_settings'),
)
