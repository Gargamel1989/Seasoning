from django.conf.urls.defaults import patterns, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^search/$', 'recipes.views.search_recipes', name='recipe_search'),
    url(r'^(\d*)/$', 'recipes.views.view_recipe', name='recipe_view'),
    url(r'^vote/(\d*)/(\d*)/$', 'recipes.views.vote'),
    url(r'^removevote/(\d*)/$', 'recipes.views.remove_vote'),
)
