
from django.shortcuts import render
from ingredients.models import Ingredient, Synonym
from ingredients.forms import IngredientForm
from django.forms.models import inlineformset_factory

def view_ingredient(request, ingredient_id):
    ingredient = Ingredient.objects.all_info(ingredient_id)

    return render(request, 'ingredients/view_ingredient.html', {'ingredient': ingredient})

def add_ingredient(request):
    
    SynonymInlineFormSet = inlineformset_factory(Ingredient, Synonym, extra=0)
    if request.method == 'POST':
        pass
    else:
        form = IngredientForm()
        synonym_formset = SynonymInlineFormSet()
        
        return render(request, 'ingredients/add_ingredient.html', {'form': form,
                                                                   'synonym_formset': synonym_formset})
