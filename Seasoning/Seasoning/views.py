from django.shortcuts import render

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