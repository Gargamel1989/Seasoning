from django.contrib import admin
from recipes.models import Recipe, Cuisine, UsesIngredient

class UsesIngredientInline(admin.TabularInline):
    model = UsesIngredient

class RecipeAdmin(admin.ModelAdmin):
    inlines = [ UsesIngredientInline, ]
    
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Cuisine)