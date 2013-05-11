
from django.shortcuts import render
from ingredients.models import Ingredient, Synonym, CanUseUnit,\
    VegetalIngredient, AvailableInCountry, AvailableInSea
from django.forms.models import inlineformset_factory, modelform_factory
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import permission_required

def view_ingredient(request, ingredient_id):
    ingredient = Ingredient.objects.all_info(ingredient_id)

    return render(request, 'ingredients/view_ingredient.html', {'ingredient': ingredient})

@permission_required('is_superuser')
def edit_ingredient(request, ingredient_id=None):
    
    if ingredient_id:
        ingredient = Ingredient.objects.get(pk=ingredient_id)
        new = False
    else:
        new =True
        ingredient = Ingredient()
    
    try:
        veg_ingredient = VegetalIngredient.objects.get(ingredient=ingredient)
    except ObjectDoesNotExist:
        veg_ingredient = VegetalIngredient()
        veg_ingredient.ingredient = ingredient
    
    IngredientForm = modelform_factory(Ingredient)
    SynonymInlineFormSet = inlineformset_factory(Ingredient, Synonym, extra=1)
    CanUseUnitInlineFormset = inlineformset_factory(Ingredient, CanUseUnit, extra=1)
    
    VegetalIngredientForm = modelform_factory(VegetalIngredient, exclude=("ingredient"))
    AvailableInCountryInlineFormset = inlineformset_factory(Ingredient, AvailableInCountry, extra=1)
    
    AvailableInSeaInlineFormset = inlineformset_factory(Ingredient, AvailableInSea, extra=1)
    
    if request.method == 'POST':
        ingredient_form = IngredientForm(request.POST, request.FILES, instance=ingredient)
        synonym_formset = SynonymInlineFormSet(request.POST, instance=ingredient)
        canuseunit_formset = CanUseUnitInlineFormset(request.POST, instance=ingredient)
        
        veg_ingredient_form = VegetalIngredientForm(request.POST, instance=veg_ingredient)
        availinc_formset = AvailableInCountryInlineFormset(request.POST, instance=ingredient)
        
        availins_formset = AvailableInSeaInlineFormset(request.POST, instance=ingredient)
            
        models_valid = ingredient_form.is_valid() and synonym_formset.is_valid() and canuseunit_formset.is_valid()
        
        if models_valid and ingredient_form.cleaned_data['type'] == 'VE':
            models_valid = models_valid and veg_ingredient_form.is_valid() and availinc_formset.is_valid()
        
        if models_valid and ingredient_form.cleaned_data['type'] == 'FI':
            models_valid = models_valid and availins_formset.is_valid()
        
        if models_valid:
            ingredient_form.save()
            synonym_formset.save()
            canuseunit_formset.save()
            if ingredient_form.cleaned_data['type'] == 'VE':
                veg_ingredient_form.save()
                availinc_formset.save()
            if ingredient_form.cleaned_data['type'] == 'FI':
                availins_formset.save()
        
    else:
        ingredient_form = IngredientForm(instance=ingredient)
        synonym_formset = SynonymInlineFormSet(instance=ingredient)
        canuseunit_formset = CanUseUnitInlineFormset(instance=ingredient)
        
        veg_ingredient_form = VegetalIngredientForm(instance=veg_ingredient)
        availinc_formset = AvailableInCountryInlineFormset(instance=ingredient)
        
        availins_formset = AvailableInSeaInlineFormset(instance=ingredient)
    
        
        
    return render(request, 'ingredients/edit_ingredient.html', {'new': new,
                                                                'ingredient_form': ingredient_form,
                                                                'synonym_formset': synonym_formset,
                                                                'canuseunit_formset': canuseunit_formset,
                                                                'vegingredient_form': veg_ingredient_form,
                                                                'availinc_formset': availinc_formset,
                                                                'availins_formset': availins_formset})