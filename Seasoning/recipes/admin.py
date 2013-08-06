from django.contrib import admin
from recipes.models import Recipe, Cuisine

admin.site.register(Recipe)
admin.site.register(Cuisine)