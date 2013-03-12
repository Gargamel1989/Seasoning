from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^(\d*)/$', 'ingredients.views.view_ingredient', name='ingredient'),
)
