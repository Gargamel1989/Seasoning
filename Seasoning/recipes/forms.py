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
from django import forms
from recipes.models import Recipe, UsesIngredient, Cuisine
from recipes.fields import AutoCompleteSelectIngredientField
from ingredients.models import CanUseUnit
import recipes
from django.forms.widgets import RadioSelect

class AddRecipeForm(forms.ModelForm):
    
    class Meta:
        model = Recipe
        exclude = ['author', 'time_added',
                   'rating', 'number_of_votes',
                   'thumbnail', 'accepted']
        
    def save(self, *args, **kwargs):
        author = kwargs.pop('author', None)
        kwargs['commit'] = False
        recipe = super(AddRecipeForm, self).save(*args, **kwargs)
        recipe.author = author
        return recipe.save()

class UsesIngredientForm(forms.ModelForm):

    ingredient = AutoCompleteSelectIngredientField()
    
    class Meta:
        model = UsesIngredient

#     def clean(self):
#         cleaned_data = super(UsesIngredientForm, self).clean()
#         ingredient_obj = cleaned_data.get('ingredient')
#         unit_obj = cleaned_data.get('unit')
# 
#         if not CanUseUnit.objects.filter(ingredient=ingredient_obj, unit=unit_obj).exists():
#             self._errors['unit'] = self.error_class(['Deze eenheid kan niet gebruikt worden voor het gekozen ingredient...'])
#             del cleaned_data['unit']
#         return cleaned_data

class SearchRecipeForm(forms.Form):
    
    SORT_CHOICES = (('name', 'Naam'), ('footprint', 'Voetafdruk'),
                    ('active_time', 'Actieve Kooktijd'), ('tot_time', 'Totale Kooktijd'))
    SORT_ORDER_CHOICES = (('', 'Van Laag naar Hoog'), ('-', 'Van Hoog naar Laag'))
    OPERATOR_CHOICES = (('and', 'Allemaal'), ('or', 'Minstens 1'))
    
    search_string = forms.CharField(required=False, label='Zoektermen')
    
    sort_field = forms.ChoiceField(choices=SORT_CHOICES)
    sort_order = forms.ChoiceField(widget=RadioSelect, choices=SORT_ORDER_CHOICES, required=False)
    
    ven = forms.BooleanField(initial=True, required=False, label='Veganistisch')
    veg = forms.BooleanField(initial=True, required=False, label='Vegetarisch')
    nveg = forms.BooleanField(initial=True, required=False, label='Niet-Vegetarisch')
    
    cuisine = forms.ModelMultipleChoiceField(queryset=Cuisine.objects.all(), required=False, label='Keuken')
    
    course = forms.ChoiceField(required=False, choices=(((u'', u'Maakt niet uit'),) + recipes.models.Recipe.COURSES), label='Maaltijd')
    
    include_ingredients_operator = forms.ChoiceField(widget=RadioSelect, choices=OPERATOR_CHOICES, label='', initial=OPERATOR_CHOICES[1][0])

class IngredientInRecipeSearchForm(forms.Form):
    
    name = forms.CharField()
    
    

