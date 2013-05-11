from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'ingredients.views.list_ingredients', name='list_ingredients'),
    url(r'^(\d*)/$', 'ingredients.views.edit_ingredient', name='ingredient'),
    
    # Add Ingredients Toolchain
    url(r'^add/$', 'ingredients.views.edit_ingredient', name='add_ingredient'),
)
