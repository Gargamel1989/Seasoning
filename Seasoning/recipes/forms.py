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
import recipes
from django.forms.widgets import RadioSelect, CheckboxSelectMultiple
from ingredients.fields import AutoCompleteSelectIngredientField
from ingredients.models import Ingredient, Unit
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError
from general.widgets import WMDWidget

class AddRecipeForm(forms.ModelForm):
    
    class Meta:
        model = Recipe
        exclude = ['author', 'time_added',
                   'rating', 'number_of_votes',
                   'thumbnail', 'accepted']
    
    class Media:
        css = {
            'all': ('css/forms.css',)
        }
        
#    instructions = forms.CharField(widget=WMDWidget())
    
    def save(self, author, commit=True):
        recipe = super(AddRecipeForm, self).save(commit=False)
        recipe.author = author
        return recipe.save()

class UsesIngredientForm(forms.ModelForm):    
    class Meta:
        model = UsesIngredient

    ingredient = AutoCompleteSelectIngredientField()
    group = forms.CharField(max_length=100, required=False, widget=forms.HiddenInput(attrs={'class': 'group'}))
    amount = forms.FloatField(widget=forms.TextInput(attrs={'class': 'amount'}))

    def _get_changed_data(self, *args, **kwargs):
        super(UsesIngredientForm, self)._get_changed_data(*args, **kwargs)
        # If group is in changed_data, but no other fields are filled in, remove group so
        # the form will not be validated or saved
        if 'group' in self._changed_data and len(self._changed_data) == 1:
            contains_data = False
            for name in ['ingredient', 'amount', 'unit']:
                field = self.fields[name]
                prefixed_name = self.add_prefix(name)
                data_value = field.widget.value_from_datadict(self.data, self.files, prefixed_name)
                if data_value:
                    contains_data = True
                    break
            if not contains_data:
                self._changed_data.remove('group')
        return self._changed_data
    changed_data = property(_get_changed_data)
        
    def is_valid_after_ingrequest(self):
        """
        Check if this form would be valid if a known ingredient was used
        
        """
        if super(UsesIngredientForm, self).is_valid():
            # Check if the form is valid anyway
            return True
        if not 'amount' in self.cleaned_data or not 'unit' in self.cleaned_data:
            # Check if any fields except ingredient are invalid, if so, the form would be invalid anyway
            return False
        if not self['ingredient'].value() or len(self['ingredient'].value()) > 50:
            # Check if anything else is wrong with the ingredient field
            return False
        return True
            
    
    def uses_existing_ingredient(self):
        try:
            if self['ingredient'].value():
                Ingredient.objects.get(name__iexact=self['ingredient'].value())
            return True
        except Ingredient.DoesNotExist:
            pass
        return False

class RequireOneFormSet(BaseInlineFormSet):
    
    def __init__(self, *args, **kwargs):
        return super(RequireOneFormSet, self).__init__(*args, **kwargs)
    """
    Require at least one form in the formset to be completed.
    
    """
    def clean(self):
        # Check that at least one form has been completed.
        super(RequireOneFormSet, self).clean()
        for error in self.errors:
            if error:
                return
        completed = 0
        for cleaned_data in self.cleaned_data:
            # form has data and we aren't deleting it.
            if cleaned_data and not cleaned_data.get('DELETE', False):
                completed += 1

        if completed < 1:
            raise forms.ValidationError("At least one %s is required." %
                self.model._meta.object_name.lower())

            

class SearchRecipeForm(forms.Form):
    
    SORT_CHOICES = (('name', 'Naam'), ('footprint', 'Voetafdruk'),
                    ('active_time', 'Actieve Kooktijd'), ('tot_time', 'Totale Kooktijd'))
    SORT_ORDER_CHOICES = (('', 'Van Laag naar Hoog'), ('-', 'Van Hoog naar Laag'))
    OPERATOR_CHOICES = (('and', 'Allemaal'), ('or', 'Minstens 1'))
    
    search_string = forms.CharField(required=False, label='Zoektermen',
                                    widget=forms.TextInput(attrs={'placeholder': 'Zoek Recepten', 'class': 'keywords-searchbar'}))
    
    advanced_search = forms.BooleanField(initial=True, required=False)
    
    sort_field = forms.ChoiceField(choices=SORT_CHOICES)
    sort_order = forms.ChoiceField(widget=RadioSelect, choices=SORT_ORDER_CHOICES, required=False)
    
    ven = forms.BooleanField(initial=True, required=False, label='Veganistisch')
    veg = forms.BooleanField(initial=True, required=False, label='Vegetarisch')
    nveg = forms.BooleanField(initial=True, required=False, label='Niet-Vegetarisch')
    
    cuisine = forms.ModelMultipleChoiceField(queryset=Cuisine.objects.all(), required=False, label='Keuken',
                                             widget=CheckboxSelectMultiple())
    
    course = forms.MultipleChoiceField(required=False, choices=recipes.models.Recipe.COURSES, label='Maaltijd',
                                       widget=CheckboxSelectMultiple())
    
    include_ingredients_operator = forms.ChoiceField(widget=RadioSelect, choices=OPERATOR_CHOICES, label='', initial=OPERATOR_CHOICES[1][0])

class IngredientInRecipeSearchForm(forms.Form):
    
    name = forms.CharField()
    
    

