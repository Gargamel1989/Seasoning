
from django.shortcuts import render
from ingredients.models import Ingredient

def view_ingredient(request, ingredient_id):
    ingredient = Ingredient.objects.get(pk=ingredient_id)

    return render(request, 'ingredients/view_ingredient.html', {'ingredient': ingredient})# Create your views here.
