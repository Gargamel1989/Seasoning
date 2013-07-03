"""
Copyright 2012, 2013 Driesen Joep

This file is part of Seasoning.

Seasoning is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Seasoning is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Seasoning.  If not, see <http://www.gnu.org/licenses/>.
    
"""
from django.shortcuts import render, redirect, get_object_or_404
from ingredients.models import Ingredient, Synonym, CanUseUnit,\
    AvailableInCountry, AvailableInSea, Unit
from django.forms.models import inlineformset_factory, modelform_factory,\
    ModelForm
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.forms.widgets import Select, Widget
import calendar
from django.db import connection
import json
from django.http.response import HttpResponse, Http404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from ingredients.forms import SearchIngredientForm

def view_ingredients(request):
    search_form = SearchIngredientForm()
    return render(request, 'ingredients/view_ingredients.html', {'form': search_form})
    
def view_ingredient(request, ingredient_id):
    try:
        ingredient = Ingredient.objects.get(pk=ingredient_id)
        useable_units = CanUseUnit.objects.all_useable_units(ingredient_id=ingredient_id)
    except Ingredient.DoesNotExist:
        raise Http404    
    return render(request, 'ingredients/view_ingredient.html', {'ingredient': ingredient,
                                                                'useable_units': useable_units})



"""
Ajax calls
"""

def ajax_ingredient_name_list(request, query=""):
    """
    An ajax call that returns a json list with every ingredient 
    name or synonym containing the given search query
    
    """    
    if request.is_ajax(): 
        # Query the database for ingredients with a name of synonym like the query
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM ('
                       '    (SELECT id, name '
                       '     FROM ingredient '
                       '     WHERE name LIKE %s) '
                       'UNION '
                       '    (SELECT ingredient, name '
                       '     FROM synonym '
                       '     WHERE name LIKE %s)) '
                       'ORDER BY name', ['%%%s%%' % query, '%%%s%%' % query])
        
        # Serialize to json
        ingredients_json = json.dumps(cursor.fetchall())
  
        # Return the response  
        return HttpResponse(ingredients_json, mimetype='application/javascript')
    
    # If this is not an ajax request, 404
    raise Http404

def ajax_ingredients_page(request):
    """
    An ajax call that returns a certain page of the ingredient
    list resulting from a given query string filter.
    
    """
    if request.is_ajax() and request.method == 'POST':
        query = request.POST.get('query', '')
        name = Q(name__icontains=query)
        synonym = Q(synonym__icontains=query)
        ingredient_list = Ingredient.objects.filter(name | synonym).order_by('name')
        paginator = Paginator(ingredient_list, 25)
        
        page = request.POST.get('page', 1)
        try:
            ingredients = paginator.page(page)
        except PageNotAnInteger:
            ingredients = paginator.page(1)
        except EmptyPage:
            ingredients = paginator.page(paginator.num_pages)
        
        ingredients_json = json.dumps(ingredients)
        return HttpResponse(ingredients_json, mimetype='application/javascript')
    
    raise Http404



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
    
    IngredientForm = modelform_factory(Ingredient)
    SynonymInlineFormSet = inlineformset_factory(Ingredient, Synonym, extra=1)
    CanUseUnitInlineFormset = inlineformset_factory(Ingredient, CanUseUnit, extra=1)
    
    AvailableInCountryInlineFormset = inlineformset_factory(Ingredient, AvailableInCountry, extra=1,
                                                            form=AvailableInCountryForm)
    
    AvailableInSeaInlineFormset = inlineformset_factory(Ingredient, AvailableInSea, extra=1,
                                                        form=AvailableInSeaForm)
    
    if request.method == 'POST':
        ingredient_form = IngredientForm(request.POST, request.FILES, instance=ingredient)
        synonym_formset = SynonymInlineFormSet(request.POST, instance=ingredient)
        canuseunit_formset = CanUseUnitInlineFormset(request.POST, instance=ingredient)
        
        availinc_formset = AvailableInCountryInlineFormset(request.POST, instance=ingredient)
        
        availins_formset = AvailableInSeaInlineFormset(request.POST, instance=ingredient)
            
        models_valid = ingredient_form.is_valid() and synonym_formset.is_valid() and canuseunit_formset.is_valid()
        
        if models_valid and ingredient_form.cleaned_data['type'] == Ingredient.SEASONAL:
            models_valid = models_valid and availinc_formset.is_valid()
        
        if models_valid and ingredient_form.cleaned_data['type'] == Ingredient.SEASONAL_SEA:
            models_valid = models_valid and availins_formset.is_valid()
        
        if models_valid:
            ingredient_form.save()
            synonym_formset.save()
            canuseunit_formset.save()
            if ingredient_form.cleaned_data['type'] == Ingredient.SEASONAL:
                availinc_formset.save()
            if ingredient_form.cleaned_data['type'] == Ingredient.SEASONAL_SEA:
                availins_formset.save()
            
            return redirect(list_ingredients)
        
    else:
        ingredient_form = IngredientForm(instance=ingredient)
        synonym_formset = SynonymInlineFormSet(instance=ingredient)
        canuseunit_formset = CanUseUnitInlineFormset(instance=ingredient)
        
        availinc_formset = AvailableInCountryInlineFormset(instance=ingredient)
        
        availins_formset = AvailableInSeaInlineFormset(instance=ingredient)
    
        
        
    return render(request, 'ingredients/edit_ingredient.html', {'new': new,
                                                                'ingredient_form': ingredient_form,
                                                                'synonym_formset': synonym_formset,
                                                                'canuseunit_formset': canuseunit_formset,
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
