from django.conf.urls import patterns, url

urlpatterns = patterns('',
    # General Pages
    url(r'^$', 'Seasoning.views.home', name='home'),

)
