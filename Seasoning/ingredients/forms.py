from django import forms
from ingredients.models import Ingredient
from django.forms.models import BaseInlineFormSet

class IngredientForm(forms.ModelForm):
    
    class Meta:
        model = Ingredient




class CanUseUnitFormset(BaseInlineFormSet):
    
    def __init__(self, *args, **kwargs):
        super(CanUseUnitFormset, self).__init__(*args, **kwargs)
        self.forms[0].empty_permitted = False
    
    # TODO: Override save method to check if at least one canuseunit
    # object is left