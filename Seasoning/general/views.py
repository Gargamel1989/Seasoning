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
from django import forms
from django.http.response import Http404

def home(request):
    try:
        recipe_otw = Recipe.objects.get(pk=1)
    except Recipe.DoesNotExist:
        recipe_otw = None
    return render(request, 'homepage.html', {'recipe_otw': recipe_otw})

def contribute(request):
    return render(request, 'contribute.html')

def static_page(request, url):
    static_page = get_object_or_404(StaticPage, url=url)
    return render(request, 'static_page.html', {'page_info': static_page})
    
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

@staff_member_required
def upload_static_image(request):
    """
    Upload a picture into the static folder
    
    """
    class UploadStaticImageForm(forms.Form):
        image = forms.FileField()
    
    static_img_dir = '%s/img/static' % settings.STATIC_ROOT
    
    def handle_uploaded_file(f):
        with open('%s/%s' % (static_img_dir, f.name), 'wb+') as destination:
            for chunck in f.chunks():
                destination.write(chunck)
    
    if request.method == 'POST':
        form = UploadStaticImageForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(request.FILES['image'])
            return redirect('/admin/')
    else:
        form = UploadStaticImageForm()
        
    images = os.listdir(static_img_dir)
    
    return render(request, 'admin/upload_image.html', {'form': form,
                                                       'images': images})
    
    
# TEST VIEWS FOR TEMPLATE INSPECTION
def test_500(request):
    if not request.user.is_staff:
        raise Http404
    return 1/0