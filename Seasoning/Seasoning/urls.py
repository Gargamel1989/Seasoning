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

    # Core pages
    url(r'^ingredients/', include('ingredients.urls')),
    url(r'^recipes/', include('recipes.urls')),
    
    # Registration pages
    url(r'^', include('authentication.urls')),
    
     # Comments
    (r'^comments/', include('django.contrib.comments.urls')),
    
)

from django.conf import settings
## debug stuff to serve static media
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', 
            {'document_root': settings.MEDIA_ROOT}),
   )
