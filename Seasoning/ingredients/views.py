
from django.shortcuts import render, redirect
from ingredients.models import Ingredient, Synonym, CanUseUnit
from ingredients.forms import IngredientForm, CanUseUnitFormset
from django.forms.models import inlineformset_factory

def view_ingredient(request, ingredient_id):
    ingredient = Ingredient.objects.all_info(ingredient_id)

    return render(request, 'ingredients/view_ingredient.html', {'ingredient': ingredient})

def edit_ingredient(request, ingredient_id=None):
    
    if ingredient_id:
        ingredient = Ingredient.objects.get(pk=ingredient_id)
    else:
        ingredient = Ingredient()
    
    SynonymInlineFormSet = inlineformset_factory(Ingredient, Synonym, extra=1)
    
    if request.method == 'POST':
        ingredient_form = IngredientForm(request.POST, request.FILES, instance=ingredient)
        synonym_formset = SynonymInlineFormSet(request.POST, instance=ingredient)
        
        if ingredient_form.is_valid() and synonym_formset.is_valid():
            ingredient_form.save()
            synonym_formset.save()
            
            return redirect('/ingredients/edit/units/%i/' % ingredient.id)
        
    else:
        ingredient_form = IngredientForm(instance=ingredient)
        synonym_formset = SynonymInlineFormSet(instance=ingredient)
        
    return render(request, 'ingredients/edit_ingredient.html', {'ingredient_form': ingredient_form,
                                                                'synonym_formset': synonym_formset})

def edit_ingredient_units(request, ingredient_id):
    
    ingredient = Ingredient.objects.get(pk=ingredient_id)
    
    CanUseUnitInlineFormset = inlineformset_factory(Ingredient, CanUseUnit, formset=CanUseUnitFormset, extra=1)
    
    if request.method == 'POST':
        canuseunit_formset = CanUseUnitInlineFormset(request.POST, instance=ingredient)
        
        if canuseunit_formset.is_valid():
            canuseunit_formset.save()
            
            if ingredient.primary_unit:
                # Primary Unit field has not been broken because of canuseunit changes
                return redirect('/ingredients/edit/next/%i/' % ingredient.id)
            else:
                # Primary Unit field is null, we must set this to a valid canuseunit object
                # before continuing
                return redirect('/ingredients/edit/primaryunit/%i/' % ingredient.id)
    else:
        canuseunit_formset = CanUseUnitInlineFormset(instance=ingredient)
    
    return render(request, 'ingredients/edit_ingredient_units.html', {'units_form': canuseunit_formset})
