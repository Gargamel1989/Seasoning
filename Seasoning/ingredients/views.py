from django.shortcuts import render, redirect
from ingredients.models import Ingredient, Synonym, CanUseUnit,\
    VegetalIngredient, AvailableInCountry, AvailableInSea, Unit
from django.forms.models import inlineformset_factory, modelform_factory,\
    ModelForm
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.utils.safestring import mark_safe
from django.forms.widgets import Select, Widget
import calendar
from django.db import connection
import json
from django.http.response import HttpResponse

def ajax_ingredient_name_list(request, query=""):
    """
    An ajax call that returns a json list with every ingredient 
    name or synonym containing the given search query
    
    """    
    if request.is_ajax(): 
        
        # Query the database for ingredients with a name of synonym like the query
        cursor = connection.cursor()
        cursor.execute('SELECT name '
                       'FROM ingredient '
                       'WHERE name LIKE %s '
                       'UNION '
                       'SELECT name '
                       'FROM synonym '
                       'WHERE name LIKE %s', ['%%%s%%' % query, '%%%s%%' % query])
        ingredients = [x[0] for x in cursor.fetchall()]
        
        # Serialize ingredient list to json
        ingredients_json = json.dumps(ingredients)
  
        # Return the response  
        return HttpResponse(ingredients_json, mimetype='application/javascript')
    
    # If this is not an ajax request, deny permission to anyone
    raise PermissionDenied 
    
"""
Administrative Functions only below this comment
"""
    
def list_ingredients(request):
    """
    Displays a list of all ingredients currently in the database.
    
    """    
    if not request.user.is_superuser:
        raise PermissionDenied
   
    ingredients = Ingredient.objects.all().order_by('accepted', 'name')
    perc_done = int(len(ingredients)/5)
    
    return render(request, 'ingredients/list_ingredients.html', {'ingredients': ingredients,
                                                                 'perc_done': perc_done})

def edit_ingredient(request, ingredient_id=None):
    """
    Edit an ingredient
    
    """
    if not request.user.is_superuser:
        raise PermissionDenied
    
    
    # This is temporary because it makes ingredient input easier
    class MonthWidget(Widget):
        
        month_field = '%s_month'
        
        def render(self, name, value, attrs=None):
            try:
                month_val = value.month
            except AttributeError:
                month_val = None
            
            output = []

            if 'id' in self.attrs:
                id_ = self.attrs['id']
            else:
                id_ = 'id_%s' % name
    
            month_choices = ((0, '---'),
                             (1, 'Januari'), (2, 'Februari'), (3, 'Maart'), (4, 'April'), (5, 'Mei'), (6, 'Juni'),
                             (7, 'Juli'), (8, 'Augustus'), (9, 'September'), (10, 'Oktober'), (11, 'November'), (12, 'December'))
            local_attrs = self.build_attrs(id=self.month_field % id_)
            s = Select(choices=month_choices)
            select_html = s.render(self.month_field % name, month_val, local_attrs)
            output.append(select_html)
            
            return mark_safe(u'\n'.join(output))
    
        def id_for_label(self, id_):
            return '%s_month' % id_
        id_for_label = classmethod(id_for_label)
    
        def value_from_datadict(self, data, files, name):
            m = data.get(self.month_field % name)
            if m == "0":
                return None
            if m:
                return '%s-%s-%s' % (2000, m, 1)
            return data.get(name, None)
    
    class LastOfMonthWidget(MonthWidget):
        def value_from_datadict(self, data, files, name):
            m = data.get(self.month_field % name)
            if m == "0":
                return None
            if m:
                return '%s-%s-%s' % (2000, m, calendar.monthrange(2000, int(m))[1])
            return data.get(name, None)
    
    class AvailableInCountryForm(ModelForm):
        class Meta:
            model = AvailableInCountry
            widgets= {'date_from': MonthWidget,
                      'date_until': LastOfMonthWidget}
    
    class AvailableInSeaForm(ModelForm):
        class Meta:
            model = AvailableInSea
            widgets= {'date_from': MonthWidget,
                      'date_until': LastOfMonthWidget}
        
    #############################################################
        
    
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
    # FIXME: remove form argument when no longer needed
    AvailableInCountryInlineFormset = inlineformset_factory(Ingredient, AvailableInCountry, extra=1,
                                                            form=AvailableInCountryForm)
    
    AvailableInSeaInlineFormset = inlineformset_factory(Ingredient, AvailableInSea, extra=1,
                                                        form=AvailableInSeaForm)
    
    if request.method == 'POST':
        ingredient_form = IngredientForm(request.POST, request.FILES, instance=ingredient)
        synonym_formset = SynonymInlineFormSet(request.POST, instance=ingredient)
        canuseunit_formset = CanUseUnitInlineFormset(request.POST, instance=ingredient)
        
        veg_ingredient_form = VegetalIngredientForm(request.POST, instance=veg_ingredient)
        availinc_formset = AvailableInCountryInlineFormset(request.POST, instance=ingredient)
        
        availins_formset = AvailableInSeaInlineFormset(request.POST, instance=ingredient)
            
        models_valid = ingredient_form.is_valid() and synonym_formset.is_valid() and canuseunit_formset.is_valid()
        
        if models_valid and ingredient_form.cleaned_data['type'] == Ingredient.SEASONAL:
            models_valid = models_valid and veg_ingredient_form.is_valid() and availinc_formset.is_valid()
            veg_ingredient_form.ingredient = ingredient
        
        if models_valid and ingredient_form.cleaned_data['type'] == Ingredient.SEASONAL_SEA:
            models_valid = models_valid and availins_formset.is_valid()
        
        if models_valid:
            ingredient_form.save()
            synonym_formset.save()
            canuseunit_formset.save()
            if ingredient_form.cleaned_data['type'] == Ingredient.SEASONAL:
                veg_ing_temp = veg_ingredient_form.save(commit=False)
                veg_ing_temp.ingredient = ingredient
                veg_ing_temp.save()
                availinc_formset.save()
            if ingredient_form.cleaned_data['type'] == Ingredient.SEASONAL_SEA:
                availins_formset.save()
            
            return redirect(list_ingredients)
        
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

def list_units(request):
    """
    Displays a list with all available units in the database
    
    """
    if not request.user.is_superuser:
        raise PermissionDenied
    
    units = Unit.objects.all()
    
    return render(request, 'ingredients/list_units.html', {'units': units})

def edit_unit(request, unit_id=None):
    """
    Edit unit objects
    
    """
    if not request.user.is_superuser:
        raise PermissionDenied
    
    if unit_id:
        unit = Unit.objects.get(pk=unit_id)
    else:
        unit = Unit()
    
    UnitForm = modelform_factory(Unit)
    
    if request.method == 'POST':
        unit_form = UnitForm(request.POST, instance=unit)
        
        if unit_form.is_valid():
            unit_form.save()
            return redirect(list_units)
    else:
        unit_form = UnitForm(instance=unit)
    
    return render(request, 'ingredients/edit_unit.html', {'unit_form': unit_form})
