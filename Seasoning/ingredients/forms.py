from django import forms
from ingredients.fields import AutoCompleteSelectIngredientField

class SearchIngredientForm(forms.Form):
    
    name = AutoCompleteSelectIngredientField()