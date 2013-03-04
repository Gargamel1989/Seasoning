from django.conf.urls import patterns, url, include

urlpatterns = patterns('',
    # General Pages
    url(r'^$', 'Seasoning.views.home', name='home'),
    url(r'^contact/$', 'Seasoning.views.contact'),
    url(r'^motifs/$', 'Seasoning.views.motifs'),
    url(r'^privacypolicy/$', 'Seasoning.views.privacypolicy'),
    url(r'^sitemap/$', 'Seasoning.views.sitemap'),
    url(r'^support/$', 'Seasoning.views.support'),
    url(r'^terms/$', 'Seasoning.views.terms'),
    
    # Registration pages
    url(r'^', include('authentication.urls')),

)
