from django.shortcuts import render
from recipes.models import Recipe
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

def search_recipes(request):
    recipes_list = Recipe.objects.all()
    paginator = Paginator(recipes_list, 10)
    
    page = request.GET.get('page')
    try:
        recipes = paginator.page(page)
    except PageNotAnInteger:
        recipes = paginator.page(1)
    except EmptyPage:
        recipes = paginator.page(paginator.num_pages)
        
    return render(request, 'recipes/search_recipes.html', {'recipes': recipes})

def view_recipe(request, recipe_id):
    recipe = Recipe.objects.get_everything(recipe_id=recipe_id)
    
    try:
        portions = int(request.GET.get('portions', recipe.portions))
    except ValueError:
        portions = recipe.portions
    recipe.recalculate_footprints(portions)
    
    
    return render(request, 'recipes/view_recipe.html', {'recipe': recipe})