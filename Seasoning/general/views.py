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
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
import time
import os
from authentication.models import User
from ingredients.models import Ingredient
from recipes.models import Recipe
from django.template.loaders.app_directories import Loader
from django.core.exceptions import PermissionDenied

def home(request):
    return render(request, 'homepage.html')

def contact(request):
    return render(request, 'static_page.html', {'title': 'Contact',
                                                'static_page': 'seasoning/contact.html'})

def motifs(request):
    return render(request, 'static_page.html', {'title': 'Motivering',
                                                'static_page': 'seasoning/motifs.html'})

def privacypolicy(request):
    return render(request, 'static_page.html', {'title': 'Privacybeleid',
                                                'static_page': 'seasoning/privacypolicy.html'})

def sitemap(request):
    return render(request, 'static_page.html', {'title': 'Sitemap',
                                                'static_page': 'seasoning/sitemap.html'})

def support(request):
    return render(request, 'static_page.html', {'title': 'Ondersteuning',
                                                'static_page': 'seasoning/support.html'})

def terms(request):
    return render(request, 'static_page.html', {'title': 'Voorwaarden',
                                                'static_page': 'seasoning/terms.html'})

def admin(request):
    if not request.user.is_superuser:
        raise PermissionDenied
   
    users = len(User.objects.all())
    ingredients = len(Ingredient.objects.all())
    accepted_ingredients = len(Ingredient.objects.filter(accepted=True))
    recipes = len(Recipe.objects.all())
    return render(request, 'admin/main.html', {'users': users,
                                               'ingredients': ingredients,
                                               'accepted_ingredients': accepted_ingredients,
                                               'recipes': recipes})

def edit_static_pages(request, page_name=None):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    context = {}
    if page_name:
        page = 'seasoning/' + page_name + '.html'
        searcher = Loader().get_template_sources(page)
        while True:
            try:
                path = searcher.next()
                f = open(path, 'r')
                f.close()
                break
            except IOError:
                continue
            
    if request.method == 'POST':
        f = open(path, 'w+')
        f.write(request.POST['content'])
        f.close()
    
    if page_name:
        f = open(path, 'r+')
        contents = f.read()
        f.close()
        context['page_name'] = page_name
        context['page'] = page
        context['contents'] = contents
        
    return render(request, 'admin/edit_static_pages.html', context)

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