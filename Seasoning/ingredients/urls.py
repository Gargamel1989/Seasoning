from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^(\d*)/$', 'ingredients.views.view_ingredient', name='ingredient'),
    
    # Add Ingredients Toolchain
    url(r'^edit/$', 'ingredients.views.edit_ingredient', name='add_ingredient'),
    url(r'^edit/(\d*)/$', 'ingredients.views.edit_ingredient', name='edit_ingredient'),
    url(r'^edit/units/(\d*)/$', 'ingredients.views.edit_ingredient_units'),
)
