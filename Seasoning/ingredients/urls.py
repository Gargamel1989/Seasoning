from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^(\d*)/$', 'ingredients.views.view_ingredient', name='ingredient'),
    url(r'^add/$', 'ingredients.views.add_ingredient', name='add_ingredient'),
)
