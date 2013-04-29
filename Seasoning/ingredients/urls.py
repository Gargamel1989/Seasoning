from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^(\d*)/$', 'ingredients.views.view_ingredient', name='ingredient'),
)
