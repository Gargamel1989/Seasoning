from django.shortcuts import render

def search_recipes(request):
    return render(request, 'recipes/search_recipes.html')

def view_recipe(request, recipe_id):
    return render(request, 'recipes/view_recipe.html')