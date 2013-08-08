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
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
import time
import os
from general.models import StaticPage
from recipes.models import Recipe

def home(request):
    recipe_otw = Recipe.objects.get(pk=1)
    return render(request, 'homepage.html', {'recipe_otw': recipe_otw})

def static_page(request, url):
    static_page = get_object_or_404(StaticPage, url=url)
    return render(request, 'static_page.html', {'title': static_page.name,
                                                'body_html': static_page.body_html})
    
@staff_member_required
def backup_db(request):
    '''
    Backup the Seasoning Database to disk
    '''
    db = settings.DATABASES['default']
    filename = "/backups/mysql/%s-%s.sql" % (db['NAME'], time.strftime('%Y-%m-%d'))
    cmd = 'mysqldump --opt -u %s -p%s -e -c %s | bzip2 -c > %s' % (db['USER'], db['PASSWORD'], db['NAME'], filename)
    os.popen(cmd)
    
    return redirect(home)
