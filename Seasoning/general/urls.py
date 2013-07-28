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
from django.conf.urls import patterns, url

urlpatterns = patterns('',
    # Home Page
    url(r'^$', 'general.views.home', name='home'),
    
    # Static Pages
    url(r'^contact/$', 'general.views.contact'),
    url(r'^motifs/$', 'general.views.motifs'),
    url(r'^privacypolicy/$', 'general.views.privacypolicy'),
    url(r'^sitemap/$', 'general.views.sitemap'),
    url(r'^support/$', 'general.views.support'),
    url(r'^terms/$', 'general.views.terms'),
    url(r'^information/$', 'general.views.information'),
    url(r'^news/$', 'general.views.news'),
    url(r'^about/$', 'general.views.about'),
    
    # Admin Pages
    url(r'^admin/$', 'general.views.admin'),
    url(r'^admin/static/$', 'general.views.edit_static_pages'),
    url(r'^admin/static/(.*)/$', 'general.views.edit_static_pages'),

    # Backup Database
    url(r'^backup/$', 'general.views.backup_db'),
    
)
