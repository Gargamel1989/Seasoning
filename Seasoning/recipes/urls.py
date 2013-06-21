from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^search/$', 'recipes.views.search_recipes', name='recipe_search'),
    url(r'^(\d*)/$', 'recipes.views.view_recipe', name='recipe_view'),
    url(r'^(\d*)/portions/(\d*)/$', 'recipes.views.view_recipe'),
    url(r'^vote/(\d*)/(\d*)/$', 'recipes.views.vote'),
    url(r'^removevote/(\d*)/$', 'recipes.views.remove_vote'),
    
    url(r'^add/$', 'recipes.views.edit_recipe'),
    url(r'^edit/(\d*)/$', 'recipes.views.edit_recipe')
)
