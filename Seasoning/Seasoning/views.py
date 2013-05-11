from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
import subprocess
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
    db = settings.DATABASES['default']
    filename = "/backups/mysql/%s-%s.sql" % (db['NAME'], time.strftime('%Y-%m-%d'))
    cmd = 'mysqldump --opt -u %s -p%s -e -c %s | bzip2 -c > %s' % (db['USER'], db['PASSWORD'], db['NAME'], filename)
    os.popen(cmd)
    
    return render(request, 'seasoning/homepage.html')
