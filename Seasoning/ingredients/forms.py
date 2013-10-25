from django import forms
from ingredients.fields import AutoCompleteSelectIngredientField

class SearchIngredientForm(forms.Form):
    
    name = AutoCompleteSelectIngredientField(ingredient_must_exist=False)