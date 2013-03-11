from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'Seasoning.ingredients.views.list_ingredients', name='ingredients_list'),
    url(r'^(\d*)/$', 'Seasoning.ingredients.views.view_ingredient', name='ingredient'),
)
