
from django.shortcuts import render
from ingredients.models import Ingredient

def view_ingredient(request, ingredient_id):
    ingredient = Ingredient.objects.all_info(pk=ingredient_id)

    return render(request, 'ingredients/view_ingredient.html', {'ingredient': ingredient})
