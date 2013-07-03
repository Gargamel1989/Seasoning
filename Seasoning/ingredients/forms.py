from django import forms

class SearchIngredientForm(forms.Form):
    
    name = forms.CharField()