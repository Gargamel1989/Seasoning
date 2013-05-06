from django.forms import ModelForm
from ingredients.models import Ingredient

class IngredientForm(ModelForm):
    
    class Meta:
        model = Ingredient