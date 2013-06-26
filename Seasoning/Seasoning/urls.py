"""
Copyright 2012, 2013 Driesen Joep

This file is part of Seasoning.

Seasoning is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Seasoning is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Seasoning.  If not, see <http://www.gnu.org/licenses/>.
    
"""
from django.conf.urls import patterns, include, url
from general.views import home, contact, motifs, privacypolicy, sitemap, support, terms, backup_db

urlpatterns = patterns('',
    # General Pages
    url(r'^$', home, name='home'),
    url(r'^contact/$', contact),
    url(r'^motifs/$', motifs),
    url(r'^privacypolicy/$', privacypolicy),
    url(r'^sitemap/$', sitemap),
    url(r'^support/$', support),
    url(r'^terms/$', terms),

    # Core pages
    (r'^ingredients/', include('ingredients.urls')),
    (r'^recipes/', include('recipes.urls')),
    
    # Registration pages
    (r'^', include('authentication.urls')),
    
     # Comments
    (r'^comments/', include('django.contrib.comments.urls')),
    
    # Backup Database
    (r'^backup/$', backup_db),
    
)

from django.conf import settings
# debug stuff to serve static media
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', 
            {'document_root': settings.MEDIA_ROOT}),
   )
