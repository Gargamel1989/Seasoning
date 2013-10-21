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
from django.shortcuts import render
from ingredients.models import Ingredient, CanUseUnit
from django.core.exceptions import PermissionDenied
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
        useable_units = list(CanUseUnit.objects.all_useable_units(ingredient_id=ingredient_id))
        primary_unit = ingredient.primary_unit
        try:
            available_ins = ingredient.get_available_ins().select_related()
        except Ingredient.BasicIngredientException:
            available_ins = []
    except Ingredient.DoesNotExist:
        raise Http404    
    return render(request, 'ingredients/view_ingredient.html', {'ingredient': ingredient,
                                                                'useable_units': useable_units,
                                                                'primary_unit': primary_unit,
                                                                'available_ins': available_ins})



"""
Ajax calls
"""

def ajax_ingredient_name_list(request):
    """
    An ajax call that returns a json list with every ingredient 
    name or synonym containing the given search query
    
    """    
    if request.is_ajax() and 'term' in request.GET:
        query = request.GET['term']
        
        # Query the database for ingredients with a name of synonym like the query
        cursor = connection.cursor()
        cursor.execute('SELECT name '
                       'FROM ingredient '
                       'WHERE name LIKE %s '
                       'UNION '
                       'SELECT name '
                       'FROM synonym '
                       'WHERE name LIKE %s '
                       'ORDER BY name', ['%%%s%%' % query, '%%%s%%' % query])
        
        # Convert results to dict
        result = [dict(zip(['value', 'label'], [row[0], row[0]])) for row in cursor.fetchall()]
        
        # Serialize to json
        ingredients_json = json.dumps(result)
  
        # Return the response
        return HttpResponse(ingredients_json, mimetype='application/javascript')
    
    # If this is not an ajax request, permission is denied
    raise PermissionDenied

def ajax_ingredients_page(request):
    """
    An ajax call that returns a certain page of the ingredient
    list resulting from a given query string filter.
    
    """
    if request.is_ajax() and request.method == 'POST':
        query = request.POST.get('query', '')
        name = Q(name__icontains=query)
        synonym = Q(synonym__name__icontains=query)
        ingredient_list = Ingredient.objects.filter(name | synonym).order_by('name')
        paginator = Paginator(ingredient_list, 25)
        
        page = request.POST.get('page', 1)
        try:
            ingredients = paginator.page(page)
        except PageNotAnInteger:
            ingredients = paginator.page(1)
        except EmptyPage:
            ingredients = paginator.page(paginator.num_pages)
        
        # FIXME: send ingredients page to template and send template to client instead of ing list
        ingredients_json = json.dumps(ingredients.object_list)
        return HttpResponse(ingredients_json, mimetype='application/javascript')
    
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
   
    ingredients = Ingredient.objects.all().order_by('accepted', 'name').prefetch_related('canuseunit_set__unit', 'useable_units', 'available_in_country', 'available_in_sea')
    perc_done = int(len(ingredients)/7)
    
    return render(request, 'admin/list_ingredients.html', {'ingredients': ingredients,
                                                           'perc_done': perc_done})