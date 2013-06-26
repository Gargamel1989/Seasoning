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

def home(request):
    return render(request, 'seasoning/homepage.html')

def contact(request):
    return render(request, 'seasoning/contact.html')

def motifs(request):
    return render(request, 'seasoning/motifs.html')

def privacypolicy(request):
    return render(request, 'seasoning/privacypolicy.html')

def sitemap(request):
    return render(request, 'seasoning/sitemap.html')

def support(request):
    return render(request, 'seasoning/support.html')

def terms(request):
    return render(request, 'seasoning/terms.html')

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