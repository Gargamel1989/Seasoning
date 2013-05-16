from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'ingredients.views.list_ingredients', name='list_ingredients'),
    url(r'^(\d*)/$', 'ingredients.views.view_ingredient', name='ingredient'),
    url(r'^edit/(\d*)/$', 'ingredients.views.edit_ingredient'),
    url(r'^add/$', 'ingredients.views.edit_ingredient', name='add_ingredient'),
    
    url(r'^units/$', 'ingredients.views.list_units'),
    url(r'^units/(\d*)/$', 'ingredients.views.edit_unit'),
    url(r'^units/add/$', 'ingredients.views.edit_unit'),
)
